cmake_minimum_required(VERSION 3.20)

project(MegaManXSNESRecompAndroid LANGUAGES C CXX)

# android/fetch_sdl.sh installs the pinned SDL2 source tree here. Building it
# from source keeps the C library and org.libsdl.app Java glue version-matched.
add_subdirectory(SDL)

# The repo-root project produces libmain.so on Android. SDLActivity loads that
# library and resolves SDL_main, while desktop builds remain normal executables.
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../.. mmx)
