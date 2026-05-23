# Porting Utinni Addresses to a Different SWG Client

How to find the equivalents of Utinni's 272 hardcoded SWG client addresses (catalogued in `ADDRESSES.md`) in a different SWG client build — e.g. Bellum Gero at `C:\Dev-BG\SWGEmu.exe`.

## Why addresses shift between SWG builds

Addresses drift because the linker lays code out differently across compilations. Function bodies move; static data moves; the PE image layout changes. But **string literals, imports, and call-graph structure survive recompilation almost intact**. The porting workflow is built around finding those stable anchors.

## Tool

**Ghidra** — free, open source, from the NSA. The standard for SWG modding work. Download: https://ghidra-sre.org. Requires JDK 21+. Run `ghidraRun.bat`.

Alternatives:
- **IDA Pro** — commercial, the gold standard, $$$.
- **x32dbg** — free runtime debugger. Useful complement once you have candidate addresses: attach to `SWGEmu.exe`, set a breakpoint, verify the function behaves as Utinni's typedef expects. For pure address discovery, Ghidra alone is enough.

## General workflow

1. **Import `SWGEmu.exe` into Ghidra** → File → Import File → accept defaults (PE/x86 32-bit) → Auto-analyze with default analyzers. Takes 5–15 min for a 22 MB binary.
2. **For each target address**, pick an anchor type (in order of reliability):
   - **PE entrypoint** — free, Ghidra labels it `entry` automatically.
   - **Unique string** — Search → For Strings → filter → right-click match → References → Show References to Address.
   - **Distinctive import** (`MiniDumpWriteDump`, `DirectInput8Create`, `RegisterClassExA`, etc.) — Symbol Tree → Imports → right-click → References.
   - **Call-graph from a known anchor** — once you've found one address in a compilation unit, neighbors typically live in the same `.text` region.
3. **Verify** the candidate's signature matches Utinni's typedef: calling convention (`__cdecl`/`__thiscall`), arg count and types, return type.
4. **Record** the new address in your port.

## Walkthrough — priority addresses

Ordered easiest-first so you can confirm Ghidra is working before tackling harder ones.

### 1. `Client::clientMain` @ `0x00401050` (client.cpp:41) — PE entrypoint

This is the PE entrypoint, free for the taking.

- Ghidra: **Symbol Tree → Functions → `entry`**. Double-click.
- Verify: signature is `int(HINSTANCE, int, int)`; prologue calls `GetModuleHandle` and/or `GetCommandLine` early.
- Expected BG address: probably very close to `0x00401050`, possibly identical — entrypoints sit at the start of `.text` regardless of build.

### 2. `Client::writeMiniDump` @ `0x00A8A170` (client.cpp:46) — import anchor

Proves the import-anchor technique on something easy.

- **Symbol Tree → Imports → `dbghelp.dll` → `MiniDumpWriteDump`**. Right-click → References → Show References to.
- You'll get a short list, usually 1–2 callers.
- The caller whose signature is `bool __cdecl(const char* filename, void* unk)` is `writeMiniDump`. Record its entry.

### 3. `Client::writeCrashLog` @ `0x00A9F640` (client.cpp:45)

- Registered via `SetUnhandledExceptionFilter`. **Imports → `kernel32.dll` → `SetUnhandledExceptionFilter`** → References. The argument to that call is the address of the exception handler, which calls `writeCrashLog`.
- Alternatively: search Defined Strings for `"swg_client"`, `"crash"`, or `"logs/"` — `writeCrashLog` references log filename strings.

### 4. SWG `WndProc` @ `0x00AA0970` (client.cpp:43)

- **Imports → `user32.dll` → `RegisterClassExA`** (or `RegisterClassA`) → References. Find the function that builds the `WNDCLASSEX` struct.
- In that function, look for `mov [...+lpfnWndProc], offset XXXXXXXX`. That immediate is the WndProc address.
- Confirm: the WndProc has a distinctive `switch(Message)` on `WM_PAINT`, `WM_DESTROY`, `WM_KEYDOWN`, etc.

### 5. `Client::setupStartDataInstall` @ `0x00A9F970` (client.cpp:40)

- Takes a `StartupData*` and reads fields like `createOwnWindow`, `hInstance`, `windowHandle`, `processMessagePump`, `lostFocusCallback`. Those struct field reads at fixed offsets are a fingerprint.
- Easier path: it's called from `clientMain` (already located). Step through `clientMain`'s call list — `setupStartDataInstall` is one of the first non-trivial calls, before the message loop.

### 6. `Game::install` @ `0x00422E80` (game.cpp:54)

- Called by `clientMain` after `setupStartDataInstall`.
- Distinctive shape: takes one `int applicationType`, then makes ~50+ calls to `XxxxSystem::install()` style functions in sequence — the SWG subsystem init dance. Recognizable instantly.
- Anchor strings: check Defined Strings for `"Game::install"`, `"installing"`, or subsystem names.

### 7. `Game::mainLoop` @ `0x004237C0` (game.cpp:56)

- Signature: `void __cdecl(bool, HWND, int, int)`.
- Called from `clientMain`'s main loop (the loop that calls `PeekMessage` / `DispatchMessage` — `mainLoop` is invoked once per frame inside or adjacent to it).
- Likely **adjacent in memory** to `Game::install` (same `.obj`). Once you've found `install`, scroll the listing — `Game::quit` (`0x00423720`), `Game::mainLoop` (`0x004237C0`), `Game::cleanupScene` (`0x00423700`), `Game::setupScene` (`0x00424220`) all live in the same `0x00422xxx`–`0x00426xxx` neighborhood.

### 8. `Game::getPlayer` / `getPlayerCreatureObject` / `getCamera` (game.cpp:61-65)

- All `__cdecl`, no args, return a pointer. Very short — typically `mov eax, [global_ptr]; ret` or one level of indirection.
- ~4 KB further into the same module as `Game::install`. Scroll the listing.

### 9. Static data pointers (`0x01908830`, `0x01908858`, `0x01919410`)

These live in `.data`, not `.text`. They can't be found by function-search techniques — you derive them from functions that *use* them.

- `0x01908830` is the main loop count. `getMainLoopCount()` reads `*0x01908830`. In Ghidra, look at the equivalent of `getMainLoopCount` in BG (it's tiny — a one-liner called from `mainLoop`). The instruction will look like `mov eax, [019xxxxxh]` — that immediate is the new address.
- Same trick for `isSafeToUse`'s two flag reads.

## Suggested order of attack

1. **`entry` (`clientMain`)** — free win, confirms Ghidra is working.
2. **`writeMiniDump`** — proves the import-anchor technique.
3. **`WndProc`** — second easy import anchor.
4. **`Game::install`** — once located, you get the whole `0x004xxxxx` `Game::*` neighborhood for free by scrolling.
5. **`setupStartDataInstall` / `writeCrashLog`** — pulls the `0x00A9xxxx` `Client::*` neighborhood.
6. **Static data** — derive from already-located functions that read them.

After this batch, the appearance / camera / graphics / object / UI subsystems can each be approached the same way: find one anchor per `.obj`, scroll for neighbors.

## Verification before trusting an address

Before committing a new address to source, sanity-check at least one of:

- **Call site count** — Ghidra "References to" should give a count roughly matching what you'd expect (e.g. `MiniDumpWriteDump` wrapper is called from 1–2 places, not 50).
- **Function body length** — short getters (`getPlayer`) should be 10–30 bytes; install routines should be hundreds.
- **Calling convention markers** — `__thiscall` functions take `this` in `ecx`; `__cdecl` cleans stack at caller. Ghidra's auto-analysis usually labels these correctly in the function signature.
- **Run it under x32dbg** — set a breakpoint at the candidate address with Utinni built against it, see if the right thing happens (e.g. `getPlayer` returns a non-null pointer mid-game).

## Common pitfalls

- **Inlined functions** — small wrappers Utinni hooks may have been inlined in BG. If you can't find a standalone function for a tiny getter, check whether its caller has the body inlined; you may need to hook the caller instead.
- **Recompiler reorders** — same source compiled by a different MSVC version may reorder basic blocks. The function *entry* is still stable; mid-function patch addresses (e.g. the `cui_chat_window.cpp` patches at `0x00914245`–`0x009142E4`) often are NOT and need to be re-derived per-build.
- **Different SWG branch** — if BG is built from a different SWG source branch (not just rebuilt), some functions may not exist at all. Plan for this.
- **Static data without a function that reads it** — rare, but for orphan data pointers you may need to grep the disassembly for the *content* if you know what's stored there (e.g. a config string).

## When you have candidate addresses

Once you've located a batch in BG, share them and the surrounding disassembly. I can cross-check against the Utinni typedefs in source to confirm signature match before you commit.
