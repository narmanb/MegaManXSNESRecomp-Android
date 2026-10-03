#!/usr/bin/env bash
# Fetch the SDL2 release used by the working SuperMetroidRecomp Android port.
# The native sources and org.libsdl.app Java glue must come from the same tag.
set -euo pipefail

SDL_VERSION="2.32.8"
SDL_SHA256="0ca83e9c9b31e18288c7ec811108e58bac1f1bb5ec6577ad386830eac51c787e"

cd "$(dirname "$0")"
if [ -f "app/jni/SDL/include/SDL_version.h" ] &&
   grep -q "SDL_PATCHLEVEL 8" app/jni/SDL/include/SDL_version.h; then
    echo "fetch_sdl: SDL ${SDL_VERSION} already present"
    exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -sL -o "$tmp/SDL2.tar.gz"     "https://github.com/libsdl-org/SDL/releases/download/release-${SDL_VERSION}/SDL2-${SDL_VERSION}.tar.gz"
echo "${SDL_SHA256}  $tmp/SDL2.tar.gz" | shasum -a 256 -c -
tar xzf "$tmp/SDL2.tar.gz" -C "$tmp"

rm -rf app/jni/SDL
mv "$tmp/SDL2-${SDL_VERSION}" app/jni/SDL
rm -rf app/src/main/java/org
mkdir -p app/src/main/java
cp -R app/jni/SDL/android-project/app/src/main/java/org app/src/main/java/
echo "fetch_sdl: SDL ${SDL_VERSION} ready"
