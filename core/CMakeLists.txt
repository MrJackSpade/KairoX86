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
# The frontend, and its view of the hardware 86Box offers for the machine settings (Kairo#143).
set(KAIRO_FRONTEND "${CMAKE_CURRENT_LIST_DIR}/kairo/frontend.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/hardware.c"
    "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_scanout.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_frame.c"
    "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_voodoo.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_virge.c"
    "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_mach64.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_powervr.c"
    "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_seg.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_seg_run.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_mach64_2d.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_p9100.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_et4000w32.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_cl54xx.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_chips69000.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_tgui.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_xga.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_s3.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_ibm8514.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_mga.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_virge2d.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_banshee2d.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_wd90c3x.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_pgc.c" "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_gxm.c"
    "${CMAKE_CURRENT_LIST_DIR}/kairo/gpu_pages.c")
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
# Android's x86_64 headers (time.h, unistd.h) reach signal.h and with it the kernel's
# asm/sigcontext.h and sys/ucontext.h, whose field and register names 86Box takes for its own macros
# (cpu.h's segments cs, ds, es, ss, fs, gs; the x86-64 recompiler's REG_RAX ...), so the x86_64 build
# for the test emulator did not compile (KairoX86#212). Each source reads signal.h first, before any
# of 86Box's macros exist. The arm64 headers include no such structs.
if(ANDROID AND ANDROID_ABI STREQUAL "x86_64")
    add_compile_options("SHELL:-include signal.h")
endif()
# Profile-guided optimization (KairoX86#123): the device's arm64 core is built with the profile of
# the RG DS running the exactness standard's machines (core/pgo, recorded by tools/pgo-train.ps1). A
# function whose code no longer matches the profile is a build error, so a change to the core
# records it again. -DKAIRO_PGO=OFF builds without it; KAIROX86_PGO_GENERATE builds the core that
# records it. Set before 86Box is added, so every target here and below is built with it.
if(ANDROID AND ANDROID_ABI STREQUAL "arm64-v8a")
    set(KAIROX86_PGO_DEFAULT ON)
else()
    set(KAIROX86_PGO_DEFAULT OFF)
endif()
option(KAIRO_PGO "Build the core with its recorded profile (core/pgo)" ${KAIROX86_PGO_DEFAULT})
option(KAIROX86_PGO_GENERATE "Build the core that records a profile (tools/pgo-train.ps1)" OFF)
if(KAIRO_PGO)
    if(KAIROX86_PGO_GENERATE)
        message(FATAL_ERROR "The recorded profile is for the ordinary core: add -DKAIRO_PGO=OFF to a KAIROX86_PGO_GENERATE build")
    endif()
    include("${KAIROX86_ROOT}/shared/cmake/KairoPgo.cmake")
    kairo_use_profile("${CMAKE_CURRENT_LIST_DIR}/pgo/arm64.proftext" "${CMAKE_CURRENT_LIST_DIR}/pgo/profile.json"
        "${KAIROX86_ROOT}")
endif()
if(KAIROX86_PGO_GENERATE)
    add_compile_options(-fprofile-generate)
    add_link_options(-fprofile-generate)
endif()
# The core's diagnostic counters (K9X_DIAG in 86Box's sources), reported by game_profile over its
# measured frames (KairoX86#214). Never in a build that ships; needs -DKAIRO_PGO=OFF, as the
# counters change the profiled code.
option(K9X_DIAG "Build the core with its diagnostic counters" OFF)
if(K9X_DIAG)
    if(KAIRO_PGO)
        message(FATAL_ERROR "The counters change the profiled code: add -DKAIRO_PGO=OFF to a K9X_DIAG build")
    endif()
    add_compile_definitions(K9X_DIAG)
    set(CMAKE_C_VISIBILITY_PRESET default)
    set(CMAKE_CXX_VISIBILITY_PRESET default)
endif()
# KairoX86#239: the Rage 128's own GPU backend (vid_ati_rage128_gpu.c), on the core's Vulkan, built against the
# pinned headers (its CMake looks for vulkan/vulkan.h through this variable)
set(R128_VULKAN_INCLUDE_DIR "${KAIROX86_THIRD_PARTY}/vulkan-headers/include" CACHE PATH "" FORCE)
add_subdirectory("${KAIROX86_THIRD_PARTY}/86box" 86box)

set_target_properties(86Box PROPERTIES OUTPUT_NAME kairox86_86box C_VISIBILITY_PRESET hidden CXX_VISIBILITY_PRESET hidden)
if(K9X_DIAG)
    # game_profile reads the counters from the library (KairoMachine.cmake hides every symbol of its parts)
    set_target_properties(86Box PROPERTIES C_VISIBILITY_PRESET default CXX_VISIBILITY_PRESET default)
endif()
# The GPU backend (core/kairo/gpu.c, KairoX86#232): the pinned Vulkan headers; the system's Vulkan
# library is loaded at run time.
target_include_directories(plat PRIVATE "${CMAKE_CURRENT_LIST_DIR}/kairo" "${KAIROX86_THIRD_PARTY}/vulkan-headers/include")
# Its kernels (core/kairo/shaders), compiled to SPIR-V by the NDK's glslc as the numbers the backend's
# sources include (<name>.comp.inc): the NDK the build uses, or on the PC the SDK's (ANDROID_HOME).
file(GLOB KAIROX86_GLSLC_HINTS "${ANDROID_NDK}/shader-tools/*" "$ENV{ANDROID_HOME}/ndk/*/shader-tools/*")
find_program(KAIROX86_GLSLC glslc HINTS ${KAIROX86_GLSLC_HINTS} NO_DEFAULT_PATH REQUIRED)
set(KAIROX86_SHADER_OUT "${CMAKE_CURRENT_BINARY_DIR}/kairo_shaders")
set(KAIROX86_SHADER_INCS)
# The kernels' shared parts (#include, from the shaders' folder): every kernel is rebuilt when one changes
file(GLOB KAIROX86_SHADER_PARTS "${CMAKE_CURRENT_LIST_DIR}/kairo/shaders/*.glsl")
foreach(shader scanout.comp voodoo.comp virge.comp mach64.comp powervr.comp mach64_2d.comp p9100.comp et4000w32.comp cl54xx.comp chips69000.comp tgui.comp xga.comp s3.comp ibm8514.comp mga.comp virge2d.comp banshee2d.comp wd90c3x.comp pgc.comp gxm.comp)
    set(source "${CMAKE_CURRENT_LIST_DIR}/kairo/shaders/${shader}")
    set(inc "${KAIROX86_SHADER_OUT}/${shader}.inc")
    add_custom_command(OUTPUT "${inc}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${KAIROX86_SHADER_OUT}"
        COMMAND "${KAIROX86_GLSLC}" --target-env=vulkan1.1 -O -Werror -mfmt=num -I "${CMAKE_CURRENT_LIST_DIR}/kairo/shaders"
                -o "${inc}" "${source}"
        DEPENDS "${source}" ${KAIROX86_SHADER_PARTS} VERBATIM)
    list(APPEND KAIROX86_SHADER_INCS "${inc}")
endforeach()
add_custom_target(kairox86_shaders DEPENDS ${KAIROX86_SHADER_INCS})
add_dependencies(plat kairox86_shaders)
target_include_directories(plat PRIVATE "${KAIROX86_SHADER_OUT}")
target_link_libraries(86Box chdr-static kairo_zlib)
if(ANDROID)
    # The frame slots' hardware buffers (core/kairo/gpu_frame.c, KairoX86#330)
    target_link_libraries(86Box android)
endif()
# A machine owns what it allocates (KairoX86#186): the library's malloc family goes through the
# frontend's record (core/kairo/frontend.c), which frees what is left when the machine closes.
target_link_options(86Box PRIVATE "LINKER:--wrap=malloc,--wrap=calloc,--wrap=realloc,--wrap=free")
if(WIN32)
    # The host loads a copy of the DLL from the program's own folder (x86_library.cpp).
    set_target_properties(86Box PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
endif()

# The machine (x86_machine.h): loads a fresh copy of kairox86_86box for each machine.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library(kairox86_core STATIC x86_machine.cpp x86_library.cpp x86_hardware.cpp)
target_include_directories(kairox86_core PUBLIC "${CMAKE_CURRENT_LIST_DIR}" "${CMAKE_CURRENT_LIST_DIR}/kairo"
    "${CMAKE_CURRENT_LIST_DIR}/../shared/frontend/src/main/cpp")
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
if(WIN32)
    # The process's memory in use after each machine (KairoX86#186).
    target_link_libraries(boot_test PRIVATE psapi)
endif()

# The hardware queries the machine settings make (Kairo#143), printed: host and device.
add_executable(hardware_query EXCLUDE_FROM_ALL test/hardware_query.cpp)
target_link_libraries(hardware_query PRIVATE kairox86_core)

# The measurement tool (KairoX86#56), likewise: host and device.
add_executable(game_profile EXCLUDE_FROM_ALL test/game_profile.cpp)
target_link_libraries(game_profile PRIVATE kairox86_core)
# The shared startup typer (startup_typer.h, header only), as the app runs it (KairoX86#46).
target_include_directories(game_profile PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../shared/frontend/src/main/cpp")
