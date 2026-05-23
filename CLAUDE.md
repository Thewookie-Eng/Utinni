# Utinni — Project Context

## What this is

Utinni is a DLL-injection modding/editor framework for the **Star Wars Galaxies** client. It injects a DLL into the running SWG process, hooks engine functions at hardcoded addresses, and exposes a callback API for plugins (both native C++ and managed C#).

License: MIT, originally by Philip Klatt (2020).

## Solution layout

`Utinni.sln` (Visual Studio) — five projects:

| Project | Role |
|---|---|
| **`Launcher/`** | Win32 EXE. Launches the SWG client process and injects `UtinniCore.dll`. Entry: `Launcher/main.cpp`. |
| **`UtINI/`** | Static lib wrapping LeksysINI. Defines the canonical Utinni settings schema in `utini.cpp`. |
| **`UtinniCore/`** | The injected DLL. Contains all SWG-client hooks under `swg/` (camera, graphics, game, object, scene, ui, misc, etc.) plus the plugin framework. **This is where 99% of the hardcoded addresses live.** |
| **`UtinniCore-Symbols/`** | Symbol-export project for the SDK. |
| **`UtinniCoreDotNet/`** | C# managed wrapper. Exposes UtinniCore via P/Invoke so .NET plugins can hook the same callbacks. The CLR is hosted from UtinniCore (`UtinniCore/clr.cpp`). |
| **`sdk/`** | Plugin templates (`UtinniCppPluginTemplate`, `UtinniPluginTemplates`). |

## The address-hook pattern

Almost every SWG client function is wrapped using the same idiom:

```cpp
namespace swg::<subsystem> {
    using pFoo = ReturnType(__callconv*)(ArgTypes);
    pFoo foo = (pFoo)0x00XXXXXX;   // hardcoded SWG client address
}
```

Then either called directly through `swg::<subsystem>::foo(...)`, or detoured via `Detour::Create(...)` from `external/DetourXS`. Mid-function patches use `memory::createJMP(...)` to write a 5-byte trampoline, with a `__declspec(naked)` handler and a return-target address back into SWG.

Static data is read with `memory::read<T>(0x019xxxxx)`.

**See `ADDRESSES.md` for the full catalog of 272 hardcoded addresses, grouped by subsystem, with file:line and purpose annotations.**

## Active work — Bellum Gero port

The hardcoded addresses in this repo target the **original SWG client** that Utinni was written against. Active effort: porting Utinni to work with the **Bellum Gero** client at `C:\Dev-BG\SWGEmu.exe` (22 MB, different build, addresses will shift).

Toolchain for porting: **Ghidra** on the BG binary, anchored by string literals / imports / PE entrypoint.

**See `PORTING_GUIDE.md` for the step-by-step methodology** — tool setup, anchor types, worked walkthroughs for the priority addresses (`clientMain`, `writeMiniDump`, `WndProc`, `Game::install`, `Game::mainLoop`, etc.), suggested order of attack, and verification techniques.

## Build

Open `Utinni.sln` in Visual Studio. Configurations include the usual Debug/Release plus a `RELDBG` variant referenced in `Launcher/main.cpp` (debugger-attach path, currently commented out).

## Reference files

- **`ADDRESSES.md`** — full address catalog
- **`PORTING_GUIDE.md`** — how to find equivalent addresses in a different SWG build
- **`HOOK_PATTERNS.md`** — the five hook techniques (typedef-cast, Detour::Create, memory::read/write, nopAddress, createJMP+naked) with fragility ranking for porting
