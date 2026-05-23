# Utinni Hook Patterns

The five techniques Utinni uses to interop with the SWG client. Important for porting work because each technique has a different fragility profile when the underlying binary changes.

## Fragility ranking (most stable → most fragile)

| Pattern | Address type | Stable across rebuilds? |
|---|---|---|
| Function pointer typedef + cast | Function entry | **Yes** — entry addresses move per build but the *shape* of the function survives |
| `Detour::Create` (DetourXS) | Function entry | **Yes** — needs 5+ stable bytes at entry, almost always true |
| `memory::read<T>` / `memory::write<T>` | Static data ptr | **Mostly** — addresses shift, but data layout & types persist; re-derive via reader functions |
| `memory::nopAddress` | Specific instruction | **Fragile** — instruction-level offset; re-derive per build |
| `memory::createJMP` + `__declspec(naked)` handler | Specific instruction | **Most fragile** — needs both jmp site AND return-target re-derived; surrounding instructions must be re-validated |

When porting to a new SWG build, the first two patterns "just work" once you find the new function entry. The bottom three need careful per-build re-derivation — every patch site is suspect.

---

## Pattern 1 — Function pointer typedef + cast

**Used for:** calling an SWG function unmodified.

```cpp
// UtinniCore/swg/game/game.cpp
namespace swg::game
{
    using pInstall = void(__cdecl*)(int applicationType);
    pInstall install = (pInstall)0x00422E80;
}

// Usage elsewhere:
swg::game::install(application);
```

**Notes:**
- Calling convention must match SWG's (`__cdecl`, `__thiscall`, `__stdcall`). Wrong convention = stack corruption.
- `__thiscall` is the default for non-static class methods in MSVC; pass `this` in `ecx`.
- Returns and args must match exactly — Utinni uses `swgptr` (= `uintptr_t`) for opaque SWG pointers.

---

## Pattern 2 — Full function detour via DetourXS

**Used for:** intercepting an SWG function at entry to inject custom logic, then optionally calling the original.

```cpp
// UtinniCore/swg/game/game.cpp
void __cdecl hkMainLoop(bool presentToWindow, HWND hwnd, int width, int height)
{
    for (const auto& func : preMainLoopCallbacks) { func(); }
    swg::game::mainLoop(presentToWindow, hwnd, width, height);  // call original
    for (const auto& func : mainLoopCallbacks) { func(); }
}

void Game::detour()
{
    swg::game::mainLoop = (swg::game::pMainLoop)Detour::Create(
        swg::game::mainLoop, hkMainLoop, DETOUR_TYPE_PUSH_RET);
}
```

**Notes:**
- `Detour::Create` from `external/DetourXS`. Returns a trampoline pointer Utinni reassigns to the original variable — so subsequent calls via `swg::game::mainLoop(...)` go to the *trampoline* (which calls the real original).
- `DETOUR_TYPE_PUSH_RET` is the standard 6-byte `push <addr>; ret` style. Other types exist for tighter constraints.
- The hooked function must have at least 5 bytes of stable prologue (almost always true for `__cdecl`/`__thiscall` functions in release builds).
- Hook function signature MUST match the original byte-for-byte (calling convention + args).

---

## Pattern 3 — Static data read/write

**Used for:** reading/writing SWG global state (game flags, counters, pointers into runtime structures).

```cpp
// UtinniCore/swg/game/game.cpp
int getMainLoopCount()
{
    return memory::read<int>(0x1908830);   // Ptr to the main loop count
}

bool Game::isSafeToUse()
{
    return memory::read<bool>(0x01908858) || memory::read<bool>(0x01919410);
}

// UtinniCore/swg/scene/world_snapshot.cpp
bool WorldSnapshot::getPreloadSnapshot()
{
    return memory::read<bool>(0x191113C);
}

void WorldSnapshot::setPreloadSnapshot(bool preloadSnapshot)
{
    memory::write<bool>(0x191113C, preloadSnapshot);
}
```

**Notes:**
- These addresses live in `.data` (`0x019xxxxx`–`0x01Axxxxx`), not `.text`.
- Can't be discovered by function-search techniques — derive them from the disassembly of functions that *use* them (see `PORTING_GUIDE.md` section 9).
- Type must match SWG's: a `bool` (1 byte), `int` (4 bytes), and `swgptr` (4 bytes) are not interchangeable.

---

## Pattern 4 — Instruction NOP-out

**Used for:** disabling a specific original behavior without redirecting flow.

```cpp
// UtinniCore/swg/scene/world_snapshot.cpp
void WorldSnapshot::load(const std::string& name)
{
    if (name.empty()) return;

    memory::nopAddress(0x0059C3F3, 6);  // Remove grabbing of current .trn name
                                         // to allow loading of any .ws
    swg::worldsnapshot::load(name.c_str());
}
```

**Notes:**
- Writes `0x90` (NOP) over the specified number of bytes at the given address.
- Size MUST match a whole instruction (or sequence). NOPping a partial instruction will crash.
- The comment explains *why* the original behavior is undesired — preserve these comments on port.
- **Fragile**: this is an instruction-level patch. The new build may have the equivalent logic at a different offset, with different instruction length, or inlined into the caller.

---

## Pattern 5 — Mid-function inline hook via JMP + naked asm

**Used for:** injecting logic into the middle of an SWG function (not at entry), often to read/modify arguments or local state before continuing.

```cpp
// UtinniCore/swg/client/client.cpp
std::string fn_MidCrashLogWrite;
swgptr fnInput_MidCrashLogWrite;
swgptr fnModified_MidCrashLogWrite;
static constexpr swgptr start_MidCrashLogWrite  = 0x00A9F766;
static constexpr swgptr return_MidCrashLogWrite = 0x00A9F76B;

__declspec(naked) void midCrashLogWrite()
{
    __asm {
        mov fnInput_MidCrashLogWrite, 0x0193C268   // capture SWG's filename ptr
        pushad
        pushfd
    }

    fn_MidCrashLogWrite  = logDir;
    fn_MidCrashLogWrite += (const char*)fnInput_MidCrashLogWrite;
    fnModified_MidCrashLogWrite = (swgptr)(fn_MidCrashLogWrite).c_str();

    __asm {
        popfd
        popad
        push fnModified_MidCrashLogWrite
        jmp [return_MidCrashLogWrite]               // resume original execution
    }
}

// Install:
memory::createJMP(start_MidCrashLogWrite, (swgptr)midCrashLogWrite, 5);
```

**Notes:**
- **Naked function** = no compiler-generated prologue/epilogue. You control every instruction.
- `pushad`/`pushfd` save all GP registers + flags before C++ code runs; `popfd`/`popad` restore before jumping back. **Required** — C++ code clobbers registers SWG expects intact.
- `start_*` = where the 5-byte JMP is written. `return_*` = the instruction *after* the JMP's overwritten bytes. The JMP must overwrite a whole-instruction boundary.
- **Most fragile pattern**: both the JMP site and the return target need re-derivation per build. Worse, the surrounding logic that the hook depends on (here: how SWG passes the filename ptr) may have changed too.
- When porting, treat this as "re-write" not "re-address" — verify the equivalent SWG logic still exists at the new build's offsets before patching.

---

## Where each pattern is used in Utinni

Looking at the address catalog in `ADDRESSES.md`:

- **Pattern 1 (typedef-cast)**: ~95% of all addresses. Every `fn` entry.
- **Pattern 2 (Detour::Create)**: ~10 hooks total. Concentrated in `Game::detour()` (game.cpp), `Client::detour()` (client.cpp), `Graphics::detour()`, `CuiHud::detour()`, `DirectInput::detour()`.
- **Pattern 3 (memory::read/write)**: every `data` entry. Game state flags, static pointers, config strings.
- **Pattern 4 (nopAddress)**: rare — `world_snapshot.cpp:410`, `cui_misc.cpp` patch sites, `cui_chat_window.cpp` patch sites.
- **Pattern 5 (createJMP + naked)**: ~4–5 hooks. `client.cpp` crash log, `cui_hud.cpp` mid-update, `cui_chat_window.cpp` ctor hook, `shader.cpp` cell pop.

When porting, do Pattern 1 first (mechanical address swap), then Pattern 3 (data ptrs from reader xrefs), then Pattern 2 (re-detour against the new entries), and treat Patterns 4 & 5 as case-by-case rewrites.
