# Mega Man X Recompiled — Android build

This directory is the ARM64 Android shell for the native Mega Man X recomp.
It follows the Android architecture already proven by SuperMetroidRecomp:
SDL2 + SDLActivity + CMake/NDK, with the game exported as `libmain.so`.

## Current milestone

The initial Android path targets:
- arm64-v8a only
- Android API 28+
- landscape/fullscreen
- SDL2 controller input
- OpenGL ES through recomp-ui
- the USA Mega Man X Rev 1 build

Netplay and desktop-only shader-preset support are intentionally deferred until the native runtime boots reliably. The APK now packages the launcher assets and built-in mod metadata, and first launch uses Android's system file picker to copy and SHA-256-verify the user's own USA Rev 1 ROM.

## Required generated game code

The upstream project intentionally does not commit `src/gen/`. It is produced
from your legally obtained **Mega Man X (USA) (Rev 1)** ROM.

From the repository root:

```bash
git submodule update --init --recursive
cp "/path/to/Mega Man X (USA Rev 1).sfc" mmx.sfc
bash tools/regen.sh usa --no-tests
```

The ROM and generated outputs remain ignored by Git.

## Android dependencies

Install Android SDK 34, NDK `26.3.11579264`, CMake, Python 3 and a Java 17+
runtime. Then fetch the pinned SDL2 source and matching Java glue:

```bash
cd android
bash fetch_sdl.sh
```

Build with Gradle 8.1.1:

```bash
gradle assembleDebug
```

The APK is produced under `android/app/build/outputs/apk/debug/`.

The Android shell now includes ROM verification, fullscreen SDL startup, launcher assets and the built-in mod catalog. It is still not a verified playable release until the native library is built with regenerated game code and tested on hardware.
