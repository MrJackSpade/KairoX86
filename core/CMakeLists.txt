# KairoX86's core: 86Box (third_party/86box, with tools/patches.py applied) built as the library
# kairox86_86box, which the machine loads afresh for each run (core/kairo/kairo_x86.h), with
# KairoX86's frontend (core/kairo/frontend.c) in place of 86Box's own.
#
# The libraries 86Box links come from pinned snapshots: zlib, libpng and libchdr from the shared
# frontend (shared/cmake/KairoLibraries.cmake, KairoChd.cmake), libsndfile and FreeType from
# third_party/. 86Box finds them through the modules and package files in core/cmake/.
cmake_minimum_required(VERSION 3.22)
project(kairox86_core C CXX)

get_filename_component(KAIROX86_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(KAIROX86_THIRD_PARTY "${KAIROX86_ROOT}/third_party")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
# 86Box was written for x86, where char is signed; ARM's is unsigned. And the core runs in real time
# only optimized, so it is optimized in every build type, Debug included (Gradle's debug builds would
# otherwise compile it at -O0).
add_compile_options(-fsigned-char -O3)

include("${KAIROX86_ROOT}/shared/cmake/KairoLibraries.cmake")
include("${KAIROX86_ROOT}/shared/cmake/KairoChd.cmake")
kairo_chd_library()

# libsndfile, for CD audio tracks: WAV and AIFF, without its external codecs.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(ENABLE_EXTERNAL_LIBS OFF CACHE BOOL "" FORCE)
set(ENABLE_MPEG OFF CACHE BOOL "" FORCE)
set(BUILD_PROGRAMS OFF CACHE BOOL "" FORCE)
set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(BUILD_REGTEST OFF CACHE BOOL "" FORCE)
set(ENABLE_CPACK OFF CACHE BOOL "" FORCE)
set(INSTALL_MANPAGES OFF CACHE BOOL "" FORCE)
set(ENABLE_PACKAGE_CONFIG OFF CACHE BOOL "" FORCE)
add_subdirectory("${KAIROX86_THIRD_PARTY}/libsndfile" libsndfile EXCLUDE_FROM_ALL)
# libsndfile's interface names a folder of headers it writes while building; 86Box takes it
# through an imported target (patch kairox86-library), whose folders must exist when CMake generates.
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/libsndfile/include")

# FreeType, for the printers' text, without its optional compression and shaping libraries.
set(FT_DISABLE_BZIP2 ON CACHE BOOL "" FORCE)
set(FT_DISABLE_HARFBUZZ ON CACHE BOOL "" FORCE)
set(FT_DISABLE_BROTLI ON CACHE BOOL "" FORCE)
set(FT_DISABLE_PNG ON CACHE BOOL "" FORCE)
set(FT_DISABLE_ZLIB ON CACHE BOOL "" FORCE)
add_subdirectory("${KAIROX86_THIRD_PARTY}/freetype" freetype EXCLUDE_FROM_ALL)

# 86Box's find_package calls resolve to the targets above.
list(PREPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake/modules")
set(SndFile_DIR "${CMAKE_CURRENT_LIST_DIR}/cmake/packages" CACHE PATH "" FORCE)

# 86Box: the library, KairoX86's frontend, the shared CHD reader, the ARM64 recompiler; none of
# its own interfaces, host audio or MIDI libraries, or the automation socket.
set(KAIRO_LIBRARY ON)
set(KAIRO_LIBCHDR ON)
set(KAIRO_FRONTEND "${CMAKE_CURRENT_LIST_DIR}/kairo/frontend.c")
set(QT OFF CACHE BOOL "" FORCE)
set(OPENAL OFF CACHE BOOL "" FORCE)
set(RTMIDI OFF CACHE BOOL "" FORCE)
set(FLUIDSYNTH OFF CACHE BOOL "" FORCE)
set(MUNT OFF CACHE BOOL "" FORCE)
set(SOUNDCANVAS OFF CACHE BOOL "" FORCE)
set(DISCORD OFF CACHE BOOL "" FORCE)
set(AUTOMATION OFF CACHE BOOL "" FORCE)
set(DYNAREC ON CACHE BOOL "" FORCE)
set(RELEASE ON CACHE BOOL "" FORCE)
set(LIBRASHADER OFF CACHE BOOL "" FORCE)
set(K9X_NULL_AUDIO ON CACHE BOOL "" FORCE)
# 86Box's portable C++ threads on every platform (its Windows threads come with its Qt front end).
set(CPPTHREADS ON CACHE BOOL "" FORCE)
# 86Box includes zlib.h without asking CMake for zlib (a system's is assumed): its sources take the
# shared frontend's pinned zlib, on Android and on the host alike.
get_target_property(KAIROX86_ZLIB_INCLUDE kairo_zlib INTERFACE_INCLUDE_DIRECTORIES)
include_directories(${KAIROX86_ZLIB_INCLUDE})
add_subdirectory("${KAIROX86_THIRD_PARTY}/86box" 86box)

set_target_properties(86Box PROPERTIES OUTPUT_NAME kairox86_86box C_VISIBILITY_PRESET hidden CXX_VISIBILITY_PRESET hidden)
target_include_directories(plat PRIVATE "${CMAKE_CURRENT_LIST_DIR}/kairo")
target_link_libraries(86Box chdr-static kairo_zlib)
if(WIN32)
    # The host loads a copy of the DLL from the program's own folder (x86_library.cpp).
    set_target_properties(86Box PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
endif()

# The machine (x86_machine.h): loads a fresh copy of kairox86_86box for each machine.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library(kairox86_core STATIC x86_machine.cpp x86_library.cpp)
target_include_directories(kairox86_core PUBLIC "${CMAKE_CURRENT_LIST_DIR}" "${CMAKE_CURRENT_LIST_DIR}/kairo")
target_compile_definitions(kairox86_core PRIVATE
    KAIROX86_86BOX_FILE="$<TARGET_FILE_NAME:86Box>")
add_dependencies(kairox86_core 86Box)
if(ANDROID)
    target_link_libraries(kairox86_core PUBLIC dl log)
endif()

# The boot test (shared/tools/test-core.ps1 on the host; built for the device too, to run over adb).
# The app's build names its own targets, so it never builds this one.
add_executable(boot_test EXCLUDE_FROM_ALL test/boot_test.cpp)
target_link_libraries(boot_test PRIVATE kairox86_core kairo_png)

# The measurement tool (KairoX86#56), likewise: host and device.
add_executable(game_profile EXCLUDE_FROM_ALL test/game_profile.cpp)
target_link_libraries(game_profile PRIVATE kairox86_core)
