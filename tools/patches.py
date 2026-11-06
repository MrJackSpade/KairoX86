"""KairoX86's local changes to the third-party snapshots in third_party/, which
shared/tools/local_patches.py applies and checks. docs/source-import.md describes each change.

The KAIRO9X_* groups are the 86Box changes made in the Kairo9X proof of concept, where this core
began (KairoX86#183): the headless Android build and the exact speed fixes of docs/core-performance.md,
each gated against the no-link reference."""

KAIRO9X_BUILD = [
    ('86box/CMakeLists.txt',
     '    LANGUAGES C CXX)\n\n',
     '    LANGUAGES C CXX)\n\nif(POC_PREFIX)\n    include_directories(BEFORE "${POC_PREFIX}/include" "${POC_PREFIX}/include/freetype2")\nendif()\n\n# POC headless builds (Android, and the Windows install/reference build) have\n# no host audio output: the sound devices are still emulated.\nif(ANDROID)\n    set(K9X_NULL_AUDIO ON)\nendif()\nif(K9X_NULL_AUDIO)\n    add_compile_definitions(K9X_NULL_AUDIO)\nendif()\n\n'),
    ('86box/cmake/CompilerFlags.cmake',
     '        add_compile_options("$<$<NOT:$<CONFIG:Optimized>>:-march=armv8.5-a+simd>")\n    else()\n',
     '        add_compile_options("$<$<NOT:$<CONFIG:Optimized>>:-march=armv8.5-a+simd>")\n    elseif(K9X_MCPU)\n        add_compile_options("-mcpu=${K9X_MCPU}")\n    else()\n'),
    ('86box/cmake/CompilerFlags.cmake',
     '\n# Configuration-specific flags.\n',
     '\nif(K9X_LTO)\n    add_compile_options(-flto=thin)\n    add_link_options(-flto=thin)\nendif()\n\n# Configuration-specific flags.\n'),
    ('86box/src/cdrom/CMakeLists.txt',
     '\nfind_package(PkgConfig REQUIRED)\n\npkg_check_modules(SNDFILE REQUIRED IMPORTED_TARGET sndfile)\n\n',
     '\nfind_package(SndFile CONFIG REQUIRED)\nadd_library(PkgConfig::SNDFILE ALIAS SndFile::sndfile)\n\n'),
    ('86box/src/network/CMakeLists.txt',
     '    net_pcap.c\n    net_slirp.c\n    net_switch.c\n',
     '    net_pcap.c\n    net_switch.c\n'),
    ('86box/src/network/CMakeLists.txt',
     '\nfind_package(PkgConfig REQUIRED)\npkg_check_modules(SLIRP REQUIRED IMPORTED_TARGET slirp)\ntarget_link_libraries(86Box PkgConfig::SLIRP)\n\nif(WIN32)\n    target_link_libraries(PkgConfig::SLIRP INTERFACE wsock32 ws2_32 iphlpapi)\n',
     '\nlist(APPEND net_sources net_slirp_stub.c)\nif(FALSE)\n    target_link_libraries(PkgConfig::SLIRP INTERFACE wsock32 ws2_32 iphlpapi)\n'),
    ('86box/src/printer/CMakeLists.txt',
     '\nfind_package(PkgConfig REQUIRED)\npkg_check_modules(FREETYPE REQUIRED IMPORTED_TARGET freetype2)\ntarget_link_libraries(86Box PkgConfig::FREETYPE)\nif(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")\n',
     '\n\nif(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")\n'),
    ('86box/src/printer/CMakeLists.txt',
     '    target_link_libraries(86Box -static ${FREETYPE_STATIC_LIBRARIES})\nendif()\n',
     '    target_link_libraries(86Box -static ${FREETYPE_STATIC_LIBRARIES})\nendif()\n\nif(K9X_NULL_AUDIO)\n    find_package(Freetype REQUIRED)\n    target_link_libraries(86Box Freetype::Freetype)\nendif()\n'),
    ('86box/src/sound/CMakeLists.txt',
     '    include_directories(${SNDIO_INCLUDE_DIRS})\nelseif(OPENAL)\n',
     '    include_directories(${SNDIO_INCLUDE_DIRS})\nelseif(K9X_NULL_AUDIO)\n    target_sources(snd PRIVATE null_audio.c)\nelseif(OPENAL)\n'),
    ('86box/src/unix/CMakeLists.txt',
     '#\n# 86Box    A hypervisor and IBM PC system emulator that specializes in\n#          running old operating systems and software designed for IBM\n#          PC systems and compatibles from 1981 through fairly recent\n#          system designs based on the PCI bus.\n#\n#          This file is part of the 86Box distribution.\n#\n#          CMake build script.\n#\n# Authors: Cacodemon345\n#          David Hrdlička, <hrdlickadavid@outlook.com>\n#          Jasmine Iwanek, <jriwanek@gmail.com>\n#\n#          Copyright 2021      Cacodemon345.\n#          Copyright 2021      David Hrdlička.\n#          Copyright 2021      Andreas J. Reichel.\n#          Copyright 2021-2024 Jasmine Iwanek.\n#\n\n',
     '# POC: headless frontend (automation socket only).\n\n'),
    ('86box/src/unix/CMakeLists.txt',
     'add_library(plat OBJECT\n    sdl_main.c\n    sdl_plat.c\n',
     'add_library(plat OBJECT\n    headless_main.c\n    sdl_plat.c\n'),
    ('86box/src/unix/CMakeLists.txt',
     '    sdl_plat.c\n    ../qt/sdl_joystick.c\n)\n',
     '    sdl_plat.c\n)\n'),
    ('86box/src/unix/CMakeLists.txt',
     '    sdl_plat.c\n)\n\nif(WIN32)\n',
     '    sdl_plat.c\n)\ntarget_include_directories(plat PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/headless_sdl)\n\nif(WIN32)\n'),
    ('86box/src/unix/CMakeLists.txt',
     '    target_sources(plat PRIVATE\n        ../qt/win_netsocket.c\n',
     '    target_sources(plat PRIVATE\n        sdl_plat_win.c\n        ../qt/win_netsocket.c\n'),
    ('86box/src/unix/CMakeLists.txt',
     '        ../qt/win_dynld.c\n        sdl_plat_win.c\n    )\n',
     '        ../qt/win_dynld.c\n        ../qt/win_cdrom_ioctl.c\n        dummy_floppy_ioctl.c\n    )\n'),
    ('86box/src/unix/CMakeLists.txt',
     '        unix_dynld.c\n    )\n',
     '        unix_dynld.c\n        dummy_cdrom_ioctl.c\n        dummy_floppy_ioctl.c\n    )\n'),
    ('86box/src/unix/CMakeLists.txt',
     '\nif (NOT CPPTHREADS)\n    if (NOT WIN32)\n        set(THREADS_PREFER_PTHREAD_FLAG TRUE)\n    endif()\n    find_package(Threads REQUIRED)\n    target_link_libraries(86Box Threads::Threads)\n\n    if (WIN32)\n        target_sources(plat PRIVATE ../qt/win_thread.c)\n    else()\n        target_sources(plat PRIVATE unix_thread.c)\n    endif()\nendif()\n\nif(SDL2)\n    find_package(SDL2 REQUIRED)\n    add_compile_definitions(USE_SDL2_LIB)\n    include_directories(${SDL2_INCLUDE_DIRS})\n    if(STATIC_BUILD AND TARGET SDL2::SDL2-static)\n        target_link_libraries(86Box SDL2::SDL2-static)\n    elseif(TARGET SDL3::SDL3)\n        target_link_libraries(86Box SDL2::SDL2)\n    else()\n        target_link_libraries(86Box ${SDL2_LIBRARIES})\n    endif()\nelse()\n    find_package(SDL3 REQUIRED)\n    include_directories(${SDL3_INCLUDE_DIRS})\n    target_link_libraries(86Box SDL3::Headers)\n    if(STATIC_BUILD AND TARGET SDL3::SDL3-static)\n        target_link_libraries(86Box SDL3::SDL3-static)\n    elseif(TARGET SDL3::SDL3)\n        target_link_libraries(86Box SDL3::SDL3)\n    else()\n        target_link_libraries(86Box ${SDL3_LIBRARIES})\n    endif()\nendif()\n\noption(USE_SDL_SHADER "Build SDL GLES2 shader pipeline" OFF)\n\nadd_library(ui OBJECT\n',
     '\nadd_library(ui OBJECT\n'),
    ('86box/src/unix/CMakeLists.txt',
     'add_library(ui OBJECT\n    sdl_render.c\n    sdl_cdrom.c\n',
     'add_library(ui OBJECT\n    sdl_cdrom.c\n'),
    ('86box/src/unix/CMakeLists.txt',
     '    sdl_cdrom.c\n    sdl_monitor.c\n    sdl_ui.c\n)\n',
     '    sdl_cdrom.c\n)\n'),
    ('86box/src/unix/CMakeLists.txt',
     '\nif(USE_SDL_SHADER)\n    target_compile_definitions(ui PRIVATE USE_SDL_SHADER_PIPELINE)\n\n    find_library(GLESV2_LIBRARY GLESv2)\n    find_path(GLESV2_INCLUDE_DIR GLES2/gl2.h)\n\n    if(NOT GLESV2_LIBRARY OR NOT GLESV2_INCLUDE_DIR)\n        message(FATAL_ERROR "USE_SDL_SHADER=ON requires GLESv2 and GLES2/gl2.h; use -DUSE_SDL_SHADER=OFF to build without the shader pipeline")\n    endif()\n\n    target_sources(ui PRIVATE sdl_shader.c)\n\n    target_link_libraries(86Box ${GLESV2_LIBRARY})\n    target_include_directories(ui PRIVATE ${GLESV2_INCLUDE_DIR})\nendif()\n\ntarget_sources(ui PRIVATE sdl_osd.cpp)\n\n# Build the SDL ImGui backend separately so AUTOMOC skips it.\nset(OSD_DIR ${CMAKE_SOURCE_DIR}/src/osd)\nif(SDL2)\n    add_library(osd_backend OBJECT\n        ${OSD_DIR}/imgui/imgui_impl_sdl2.cpp\n    )\nelse()\n    add_library(osd_backend OBJECT\n        ${OSD_DIR}/imgui/imgui_impl_sdl3.cpp\n    )\nendif()\n\nif(USE_SDL_SHADER)\n    target_sources(osd_backend PRIVATE ${OSD_DIR}/imgui/imgui_impl_opengl3.cpp)\n    target_compile_definitions(osd_backend PRIVATE IMGUI_IMPL_OPENGL_ES2)\nelse()\n    if(SDL2)\n        target_sources(osd_backend PRIVATE ${OSD_DIR}/imgui/imgui_impl_sdlrenderer2.cpp)\n    else()\n        target_sources(osd_backend PRIVATE ${OSD_DIR}/imgui/imgui_impl_sdlrenderer3.cpp)\n    endif()\nendif()\n\ntarget_include_directories(osd_backend PRIVATE ${OSD_DIR}/imgui)\ntarget_link_libraries(86Box osd_backend)\n\ntarget_include_directories(ui PRIVATE ${OSD_DIR} ${OSD_DIR}/imgui)\n\nif(CMAKE_SYSTEM_NAME STREQUAL "Linux")\n    target_sources(plat PRIVATE linux_cdrom_ioctl.c)\n    target_sources(plat PRIVATE dummy_floppy_ioctl.c)\nelseif(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD" OR CMAKE_SYSTEM_NAME STREQUAL "Darwin")\n    target_sources(plat PRIVATE dummy_cdrom_ioctl.c)\n    target_sources(plat PRIVATE unix_floppy_ioctl.c)\nelseif(WIN32)\n    target_sources(plat PRIVATE ../qt/win_cdrom_ioctl.c)\n    target_sources(plat PRIVATE dummy_floppy_ioctl.c)\nelse()\n    target_sources(plat PRIVATE dummy_cdrom_ioctl.c)\n    target_sources(plat PRIVATE dummy_floppy_ioctl.c)\nendif()\n\n',
     '\nfind_package(Threads REQUIRED)\ntarget_link_libraries(86Box Threads::Threads)\n\n'),
    ('86box/src/unix/CMakeLists.txt',
     'target_link_libraries(plat ${CMAKE_DL_LIBS})\n\nif(APPLE)\n    target_sources(plat PRIVATE macOSXGlue.m)\nendif()\n\nif(WIN32)\n    enable_language(RC)\n    target_sources(86Box PUBLIC ../qt/86Box-qt.rc)\n\n    # CMake 3.22 messed this up for clang/clang++\n    # See https://gitlab.kitware.com/cmake/cmake/-/issues/22611\n    if(MSVC OR (NOT MINGW AND CMAKE_VERSION VERSION_GREATER_EQUAL 3.22))\n        # MSVC linker adds its own manifest to the executable, which fails if\n        # we include ours in 86Box.rc. We therefore need to pass the manifest\n        # directly as as a source file, so the linker can use that instead.\n        set_property(SOURCE ../qt/86Box-qt.rc DIRECTORY .. PROPERTY COMPILE_DEFINITIONS NO_INCLUDE_MANIFEST)\n        target_sources(86Box PRIVATE ../qt/86Box.manifest)\n    endif()\n\n    if (MINGW)\n        add_compile_definitions(NTDDI_VERSION=0x06010000)\n    endif()\nendif()\n',
     'target_link_libraries(plat ${CMAKE_DL_LIBS})\n'),
]

KAIRO9X_PLATFORM = [
    ('86box/src/unix/sdl_plat_unix.c',
     '#include <stdlib.h>\n',
     '#include <errno.h>\n#include <inttypes.h>\n#include <stdlib.h>\n'),
    ('86box/src/unix/sdl_plat_unix.c',
     '        *large = 0;\n#    if defined __APPLE__ && defined MAP_JIT\n',
     '        *large = 0;\n#    if defined(__ANDROID__) && defined(__aarch64__)\n    /* The recompiler\'s pool right after the program, so its code reaches the\n       program\'s functions with BL and its data with ADRP\n       (codegen_backend_arm64_ops.c). */\n    if (executable) {\n        extern char     _end[];\n        const uintptr_t align = (uintptr_t) 2 << 20;\n        const uintptr_t at    = ((uintptr_t) _end + (16 << 20) + align - 1) & ~(align - 1);\n        void           *pool  = mmap((void *) at, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANON | MAP_PRIVATE | MAP_FIXED_NOREPLACE, -1, 0);\n\n        if (pool == MAP_FAILED)\n            fatal("plat_mmap: no room for the recompiler at %p after the program: %s\\n", (void *) at, strerror(errno));\n        return pool;\n    }\n#    endif\n#    if defined __APPLE__ && defined MAP_JIT\n'),
]

KAIRO9X_CPU = [
    ('86box/src/codegen/codegen_allocator.c',
     'static mem_block_t mem_blocks[MEM_BLOCK_NR];\nstatic uint32_t    mem_block_free_list;\n',
     'static mem_block_t mem_blocks[MEM_BLOCK_NR];\n\nstatic uint32_t    mem_block_free_list;\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '#    include <86box/plat.h>\n\n#    include "codegen.h"\n',
     '#    include <86box/plat.h>\n#    include <86box/k9x_hot.h>\n#    include "codegen.h"\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\ncodegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS];\n#    endif\n',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\ncodegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS][CODEGEN_LINK_WAYS];\n#    endif\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n/*ea_rule: take the direct load whenever the address is at most 0xffc into\n',
     '\n#    ifdef K9X_DIAG\n/*Event counts for the cost model (diagnostic builds only): *counter += add.\n  X16/X17 are free wherever this is emitted.*/\nuint64_t k9x_cnt_ins;\nuint64_t k9x_cnt_exits;\nuint64_t k9x_cnt_mem;\nstatic void\nk9x_diag_count(codeblock_t *block, uint64_t *counter, int add)\n{\n    codegen_alloc(block, 28);\n    host_arm64_MOVX_IMM(block, REG_X16, (uint64_t) (uintptr_t) counter);\n    host_arm64_LDR_IMM_X(block, REG_X17, REG_X16, 0);\n    host_arm64_ADDX_IMM(block, REG_X17, REG_X17, add);\n    host_arm64_STR_IMM_Q(block, REG_X17, REG_X16, 0);\n}\n#    endif\n\n/*The memory routines\' C paths leave the block themselves when the access\n  aborted (W1 = abrt): the block flushed its registers before the call (an\n  ordered access), as for the exit it would otherwise take right after it,\n  and their frame is gone again, so codegen_exit_rout runs on the block\'s.\n  Their callers do not check. Patched once codegen_exit_rout exists.*/\n#    define STUB_ABORTS_MAX 32\nstatic uint32_t *stub_aborts[STUB_ABORTS_MAX];\nstatic int       nr_stub_aborts;\n\nstatic void\nstub_abort_exit(codeblock_t *block)\n{\n    uint32_t *done = host_arm64_CBZ_SHORT_(block, REG_W1);\n\n    if (nr_stub_aborts == STUB_ABORTS_MAX)\n        fatal("stub_abort_exit - too many routines\\n");\n    stub_aborts[nr_stub_aborts++] = host_arm64_B_placeholder(block);\n    host_arm64_short_branch_set_offset(done, &block_write_data[block_pos]);\n}\n\n/*ea_rule: take the direct load whenever the address is at most 0xffc into\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    /*In - W0 = address\n',
     '\n#    ifdef K9X_DIAG\n    k9x_diag_count(block, &k9x_cnt_mem, 1);\n#    endif\n    /*In - W0 = address\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    */\n    codegen_alloc(block, 80);\n    host_arm64_MOV_REG_LSR(block, REG_W1, REG_W0, 12);\n',
     '    */\n    codegen_alloc(block, ((size == 2) && !is_float && !ea_rule) ? 260 : 80);\n    host_arm64_MOV_REG_LSR(block, REG_W1, REG_W0, 12);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_RET(block, REG_X30);\n\n    host_arm64_branch_set_offset(branch_offset, &block_write_data[block_pos]);\n    if (size != 1)\n',
     '    host_arm64_RET(block, REG_X30);\n\n    if ((size == 2) && !is_float && !ea_rule) {\n        uint32_t *page_end;\n        uint32_t *not_ram;\n        uint32_t *intel;\n        uint32_t *aligned;\n\n        /*A misaligned word inside one page that readlookup2 has: what\n          readmemwl() does there, without the call (addr64a[] is left alone:\n          every user fills it before reading it)*/\n        host_arm64_branch_set_offset(misaligned_offset, &block_write_data[block_pos]);\n        host_arm64_AND_IMM(block, REG_W2, REG_W0, 0xfff);\n        host_arm64_CMP_IMM(block, REG_W2, 0xfff);\n        page_end = host_arm64_BEQ_(block);\n        host_arm64_CMPX_IMM(block, REG_X1, -1);\n        not_ram = host_arm64_BEQ_(block);\n        host_arm64_MOVX_IMM(block, REG_X2, (uint64_t) &mem_logical_addr);\n        host_arm64_STR_IMM_W(block, REG_W0, REG_X2, 0);\n        host_arm64_MOVX_IMM(block, REG_X2, (uint64_t) &high_page);\n        host_arm64_STRB_IMM(block, REG_WZR, REG_X2, 0);\n        /*timing_misaligned, unless a Cyrix part aligns this one*/\n        host_arm64_MOVX_IMM(block, REG_X2, (uint64_t) &cpu_cyrix_alignment);\n        host_arm64_LDR_IMM_W(block, REG_W2, REG_X2, 0);\n        host_arm64_CMP_IMM(block, REG_W2, 0);\n        intel = host_arm64_BEQ_(block);\n        host_arm64_AND_IMM(block, REG_W3, REG_W0, 7);\n        host_arm64_CMP_IMM(block, REG_W3, 7);\n        aligned = host_arm64_BNE_(block);\n        host_arm64_branch_set_offset(intel, &block_write_data[block_pos]);\n        host_arm64_MOVX_IMM(block, REG_X2, (uint64_t) &timing_misaligned);\n        host_arm64_LDR_IMM_W(block, REG_W2, REG_X2, 0);\n        host_arm64_LDR_IMM_W(block, REG_W3, REG_CPUSTATE, (int) ((uintptr_t) &cpu_state._cycles - (uintptr_t) &cpu_state));\n        host_arm64_SUB_REG(block, REG_W3, REG_W3, REG_W2, 0);\n        host_arm64_STR_IMM_W(block, REG_W3, REG_CPUSTATE, (int) ((uintptr_t) &cpu_state._cycles - (uintptr_t) &cpu_state));\n        host_arm64_branch_set_offset(aligned, &block_write_data[block_pos]);\n        host_arm64_LDRH_REG(block, REG_W0, REG_W1, REG_W0);\n        host_arm64_MOVZ_IMM(block, REG_W1, 0);\n        host_arm64_RET(block, REG_X30);\n        misaligned_offset = page_end;\n        host_arm64_branch_set_offset(not_ram, &block_write_data[block_pos]);\n    }\n\n    host_arm64_branch_set_offset(branch_offset, &block_write_data[block_pos]);\n    if (size != 1)\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '        host_arm64_FMOV_D_Q(block, REG_V_TEMP, REG_X0);\n    host_arm64_LDP_POSTIDX_X(block, REG_X29, REG_X30, REG_XSP, 16);\n    host_arm64_RET(block, REG_X30);\n}\n',
     '        host_arm64_FMOV_D_Q(block, REG_V_TEMP, REG_X0);\n    host_arm64_LDP_POSTIDX_X(block, REG_X29, REG_X30, REG_XSP, 16);\n    stub_abort_exit(block);\n    host_arm64_RET(block, REG_X30);\n}\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     "#    if !defined(USE_GDBSTUB)\n/*An aligned dword store to a RAM page whose writes are tracked (page_lookup):\n  what writememll() and mem_write_raml_page() do, without the two calls. The\n  dword never reaches the next 64-byte chunk, so only one dirty bit and one\n  byte-mask word change. writememll()'s addr64a[] is left alone: every user\n  fills it before reading it. Anything else returns through to_c[] to the C\n  path.\n  In - W0 = address, W1 = data. Returns the number of to_c[] branches.*/\n",
     '#    if !defined(USE_GDBSTUB)\n/*An aligned byte, word or dword store to a RAM page whose writes are\n  tracked (page_lookup): what writemem*l() and mem_write_ram*_page() do,\n  without the two calls. It never reaches the next 64-byte chunk, so only one\n  dirty bit and one byte-mask word change. addr64a[] is left alone: every\n  user fills it before reading it. Anything else returns through to_c[] to\n  the C path.\n  In - W0 = address, W1 = data. Returns the number of to_c[] branches.*/\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     'static int\nbuild_store_long_tracked(codeblock_t *block, uint32_t **to_c)\n{\n',
     'static int\nbuild_store_tracked(codeblock_t *block, int size, uint32_t **to_c)\n{\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '{\n    uint32_t *done[3];\n',
     "{\n    const uint32_t bytes = (1 << size) - 1; /*the store's bytes in the byte mask*/\n    uint32_t *done[3];\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    to_c[nr_to_c++] = host_arm64_BEQ_(block);\n    host_arm64_LDR_IMM_X(block, REG_X5, REG_X4, offsetof(page_t, write_l));\n    host_arm64_MOVX_IMM(block, REG_X6, (uint64_t) mem_write_raml_page);\n    host_arm64_CMPX_REG(block, REG_X5, REG_X6);\n',
     '    to_c[nr_to_c++] = host_arm64_BEQ_(block);\n    if (size == 1) {\n        host_arm64_LDR_IMM_X(block, REG_X5, REG_X4, offsetof(page_t, write_b));\n        host_arm64_MOVX_IMM(block, REG_X6, (uint64_t) mem_write_ramb_page);\n    } else if (size == 2) {\n        host_arm64_LDR_IMM_X(block, REG_X5, REG_X4, offsetof(page_t, write_w));\n        host_arm64_MOVX_IMM(block, REG_X6, (uint64_t) mem_write_ramw_page);\n    } else {\n        host_arm64_LDR_IMM_X(block, REG_X5, REG_X4, offsetof(page_t, write_l));\n        host_arm64_MOVX_IMM(block, REG_X6, (uint64_t) mem_write_raml_page);\n    }\n    host_arm64_CMPX_REG(block, REG_X5, REG_X6);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    /*Unchanged data: no store and no dirty bits*/\n    host_arm64_AND_IMM(block, REG_W6, REG_W0, 0xfff);\n',
     '\n    /*Unchanged data: no store and no dirty bits (only the low byte or word\n      of W1 is the data)*/\n    host_arm64_AND_IMM(block, REG_W6, REG_W0, 0xfff);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_AND_IMM(block, REG_W6, REG_W0, 0xfff);\n    host_arm64_LDR_REG(block, REG_W7, REG_X5, REG_X6);\n    host_arm64_CMP_REG(block, REG_W7, REG_W1);\n',
     '    host_arm64_AND_IMM(block, REG_W6, REG_W0, 0xfff);\n    if (size == 1) {\n        host_arm64_AND_IMM(block, REG_W1, REG_W1, 0xff);\n        host_arm64_LDRB_REG(block, REG_W7, REG_X5, REG_X6);\n    } else if (size == 2) {\n        host_arm64_AND_IMM(block, REG_W1, REG_W1, 0xffff);\n        host_arm64_LDRH_REG(block, REG_W7, REG_X5, REG_X6);\n    } else\n        host_arm64_LDR_REG(block, REG_W7, REG_X5, REG_X6);\n    host_arm64_CMP_REG(block, REG_W7, REG_W1);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    done[0] = host_arm64_BEQ_(block);\n    host_arm64_STR_REG(block, REG_W1, REG_X5, REG_X6);\n\n',
     '    done[0] = host_arm64_BEQ_(block);\n    if (size == 1)\n        host_arm64_STRB_REG(block, REG_X1, REG_X5, REG_X6);\n    else if (size == 2)\n        host_arm64_STRH_REG(block, REG_X1, REG_X5, REG_X6);\n    else\n        host_arm64_STR_REG(block, REG_W1, REG_X5, REG_X6);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_AND_IMM(block, REG_W9, REG_W0, 63);\n    host_arm64_MOVZ_IMM(block, REG_X10, 0xf);\n    host_arm64_LSLX(block, REG_X10, REG_X10, REG_X9);\n',
     '    host_arm64_AND_IMM(block, REG_W9, REG_W0, 63);\n    host_arm64_MOVZ_IMM(block, REG_X10, bytes);\n    host_arm64_LSLX(block, REG_X10, REG_X10, REG_X9);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LSRX(block, REG_X12, REG_X12, REG_X9);\n    host_arm64_TST_IMM(block, REG_W12, 0xf);\n    done[2] = host_arm64_BEQ_(block);\n',
     '    host_arm64_LSRX(block, REG_X12, REG_X12, REG_X9);\n    host_arm64_TST_IMM(block, REG_W12, bytes);\n    done[2] = host_arm64_BEQ_(block);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    /*In - R0 = address, R1 = data\n',
     '\n#    ifdef K9X_DIAG\n    k9x_diag_count(block, &k9x_cnt_mem, 1);\n#    endif\n    /*In - R0 = address, R1 = data\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '#    if !defined(USE_GDBSTUB)\n    if (size == 4 && !is_float) {\n        uint32_t *to_c[6];\n',
     '#    if !defined(USE_GDBSTUB)\n    if (size <= 4 && !is_float) {\n        uint32_t *to_c[6];\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '        uint32_t *to_c[6];\n        int       nr_to_c = build_store_long_tracked(block, to_c);\n\n',
     '        uint32_t *to_c[6];\n        int       nr_to_c = build_store_tracked(block, size, to_c);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    codegen_direct_read_8(block, REG_W1, &cpu_state.abrt);\n    host_arm64_LDP_POSTIDX_X(block, REG_X29, REG_X30, REG_XSP, 16);\n    host_arm64_RET(block, REG_X30);\n}\n',
     '    codegen_direct_read_8(block, REG_W1, &cpu_state.abrt);\n    host_arm64_LDP_POSTIDX_X(block, REG_X29, REG_X30, REG_XSP, 16);\n    stub_abort_exit(block);\n    host_arm64_RET(block, REG_X30);\n}\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n/*Literal pool entries, in the pairs the routine loads together with LDP*/\nenum {\n',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n/*Literal pool: the base of the k9xhot section, where every global the\n  routine reads or writes lives (k9x_hot.h), and the readlookup2 table.*/\nenum {\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     'enum {\n    LINK_LIT_WAS_RESET,\n    LINK_LIT_FLUSH_PENDING,\n    LINK_LIT_CPU_INIT,\n    LINK_LIT_NEW_NE,\n    LINK_LIT_NMI_ENABLE,\n    LINK_LIT_FORCE_INTERPRETER,\n    LINK_LIT_OVERRIDE_DYNAREC,\n    LINK_LIT_NMI,\n    LINK_LIT_PIC,\n    LINK_LIT_CUR_STATUS,\n    LINK_LIT_TSC,\n    LINK_LIT_TSC_OLD,\n    LINK_LIT_CYCLES_OLD,\n    LINK_LIT_TIMER_TARGET,\n    LINK_LIT_GET_PHYS_VIRT,\n    LINK_LIT_GET_PHYS_PHYS,\n    LINK_LIT_OLDCS,\n    LINK_LIT_OLDCPL,\n    LINK_LIT_FETCH_DEVICE,\n    LINK_LIT_CPU_HALTED,\n    LINK_LIT_NMI_MASK,\n    LINK_LIT_RAMMASK,\n    LINK_LIT_READLOOKUP2,\n',
     'enum {\n    LINK_LIT_HOT,\n    LINK_LIT_READLOOKUP2,\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    LINK_LIT_READLOOKUP2,\n    LINK_LIT_RAM,\n    LINK_LIT_DR_ARMED,\n    LINK_LIT_IOAPIC_PATH,\n    LINK_LIT_LAPIC_EXTINT,\n    LINK_LIT_LAPIC_IRR,\n\n',
     '    LINK_LIT_READLOOKUP2,\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n#        define LINK_SLOT(field) ((int) offsetof(codegen_link_slot_t, field))\n',
     '\n#        ifndef K9X_HAS_HOT\n#            error "the ARM64 link routine needs the k9xhot section"\n#        endif\n\n#        define LINK_SLOT(field) ((int) offsetof(codegen_link_slot_t, field))\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '#        define LINK_LIT(nr)     ((nr) * 8)\n#        define LINK_MAX_MISS    32\n\n',
     '#        define LINK_LIT(nr)     ((nr) * 8)\n#        define LINK_MAX_MISS    40\n/*Offset of a k9xhot global from X16, which holds __start_k9xhot*/\n#        define HOT(var)         ((int) ((uintptr_t) &(var) - (uintptr_t) __start_k9xhot))\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '               "exit_pc/exit_cs and entry are loaded as one pair");\n_Static_assert(offsetof(codegen_link_slot_t, status) == offsetof(codegen_link_slot_t, gen) + 4\n                   && offsetof(codegen_link_slot_t, npxc) == offsetof(codegen_link_slot_t, gen) + 6,\n               "gen and status/npxc are loaded as one pair");\n_Static_assert(offsetof(codegen_link_slot_t, phys_page) == offsetof(codegen_link_slot_t, cr0_bits) + 8\n                   && !(offsetof(codegen_link_slot_t, cr0_bits) & 7),\n               "cr0_bits and phys_page are the low halves of one pair");\n_Static_assert(offsetof(codegen_link_slot_t, xlat_val) == offsetof(codegen_link_slot_t, xlat) + 8\n',
     '               "exit_pc/exit_cs and entry are loaded as one pair");\n_Static_assert(offsetof(codegen_link_slot_t, npxc) == offsetof(codegen_link_slot_t, status) + 2\n                   && !(offsetof(codegen_link_slot_t, status) & 3),\n               "status and npxc are loaded as one word");\n_Static_assert(offsetof(codegen_link_slot_t, phys_page) == offsetof(codegen_link_slot_t, cr0_bits) + 4\n                   && !(offsetof(codegen_link_slot_t, cr0_bits) & 3),\n               "cr0_bits and phys_page are loaded as one pair");\n_Static_assert(offsetof(codegen_link_slot_t, dirty_mask) + sizeof(uint64_t *) <= 64 && _Alignof(codegen_link_slot_t) == 64,\n               "a hit reads one cache line of the slot");\n_Static_assert(sizeof(codegen_link_slot_t) == 128, "a slot is two cache lines");\n_Static_assert(offsetof(codegen_link_slot_t, xlat_val) == offsetof(codegen_link_slot_t, xlat) + 8\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '_Static_assert(T_FLAG == (1 << 8) && I_FLAG == (1 << 9) && CODEBLOCK_BYTE_MASK == (1 << 5), "flag bits tested by number");\n_Static_assert(BLOCK_SIZE <= 0x10000, "block numbers and codeblock_hash entries are compared as 16 bits");\n',
     '_Static_assert(T_FLAG == (1 << 8) && I_FLAG == (1 << 9) && CODEBLOCK_BYTE_MASK == (1 << 5), "flag bits tested by number");\n_Static_assert(offsetof(codeblock_t, reused) == offsetof(codeblock_t, used) + 1 && !(offsetof(codeblock_t, used) & 1),\n               "used and reused are set with one halfword store");\n_Static_assert(BLOCK_SIZE <= 0x10000, "block numbers and codeblock_hash entries are compared as 16 bits");\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     "\n/*Entered by a branch from the end of a block, with X0 = the block's slot\n  pair and X29 = &cpu_state. Repeats what exec386_dynarec() and\n  exec386_dynarec_dyn() do between that block and the next one, assuming\n",
     "\n/*Entered by a branch from the end of a block, with X0 = the exit's first\n  slot way and X29 = &cpu_state. Repeats what exec386_dynarec() and\n  exec386_dynarec_dyn() do between that block and the next one, assuming\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     "  nothing in that stretch has anything to do: if any check fails it returns\n  to C exactly as the block's own epilogue did, before any store. On a hit\n  it does the stores the C loop would have done and jumps to the next\n",
     "  nothing in that stretch has anything to do: if any check fails it returns\n  to C exactly as the block's own epilogue did, before any store, or, once\n  it has run timers or get_phys() itself, with k9x_post_done telling the C\n  loop how far it got. On a hit\n  it does the stores the C loop would have done and jumps to the next\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '  Global addresses come from a literal pool placed just before the routine,\n  so the routine and the pool must share one allocator block. Loads are\n  paired wherever the layout allows, since on a hit the routine is limited\n',
     "  Global addresses come from a literal pool placed just before the routine,\n  so the routine's hit path and the pool share one allocator block; the\n  paths a hit rarely takes sit in the next one. Loads are\n  paired wherever the layout allows, since on a hit the routine is limited\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    uint8_t  *start_data;\n    uint32_t *miss[LINK_MAX_MISS];\n',
     '    uint8_t  *start_data;\n    uint8_t  *cold_data;\n    uint32_t *miss[LINK_MAX_MISS];\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    uint32_t *es_flat;\n    uint32_t *uncached;\n',
     '    uint32_t *es_flat;\n    uint32_t *slice_ok;\n    uint32_t *no_slice;\n    uint32_t *timer_due;\n    uint32_t *plain_miss;\n    uint32_t *xlat_same;\n    uint32_t *other_way;\n    uint32_t *way_match[CODEGEN_LINK_WAYS];\n    uint8_t  *way_found;\n    uint32_t *walk_no_slice;\n    uint8_t  *timer_done;\n    uint32_t *uncached;\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    lit[LINK_LIT_WAS_RESET]         = (uint64_t) (uintptr_t) &x86_was_reset;\n    lit[LINK_LIT_FLUSH_PENDING]     = (uint64_t) (uintptr_t) &cpu_flush_pending;\n    lit[LINK_LIT_CPU_INIT]          = (uint64_t) (uintptr_t) &cpu_init;\n    lit[LINK_LIT_NEW_NE]            = (uint64_t) (uintptr_t) &new_ne;\n    lit[LINK_LIT_CPU_HALTED]        = (uint64_t) (uintptr_t) &cpu_halted;\n    lit[LINK_LIT_FORCE_INTERPRETER] = (uint64_t) (uintptr_t) &cpu_force_interpreter;\n    lit[LINK_LIT_OVERRIDE_DYNAREC]  = (uint64_t) (uintptr_t) &cpu_override_dynarec;\n    lit[LINK_LIT_NMI]               = (uint64_t) (uintptr_t) &nmi;\n    lit[LINK_LIT_PIC]               = (uint64_t) (uintptr_t) &pic;\n    lit[LINK_LIT_CUR_STATUS]        = (uint64_t) (uintptr_t) &cpu_cur_status;\n    lit[LINK_LIT_TSC]               = (uint64_t) (uintptr_t) &tsc;\n    lit[LINK_LIT_TSC_OLD]           = (uint64_t) (uintptr_t) &tsc_old;\n    lit[LINK_LIT_CYCLES_OLD]        = (uint64_t) (uintptr_t) &cycles_old;\n    lit[LINK_LIT_TIMER_TARGET]      = (uint64_t) (uintptr_t) &timer_target;\n    lit[LINK_LIT_GET_PHYS_VIRT]     = (uint64_t) (uintptr_t) &get_phys_virt;\n    lit[LINK_LIT_GET_PHYS_PHYS]     = (uint64_t) (uintptr_t) &get_phys_phys;\n    lit[LINK_LIT_OLDCS]             = (uint64_t) (uintptr_t) &oldcs;\n    lit[LINK_LIT_OLDCPL]            = (uint64_t) (uintptr_t) &oldcpl;\n    lit[LINK_LIT_FETCH_DEVICE]      = (uint64_t) (uintptr_t) &cpu_fetch_device;\n    lit[LINK_LIT_NMI_ENABLE]        = (uint64_t) (uintptr_t) &nmi_enable;\n    lit[LINK_LIT_NMI_MASK]          = (uint64_t) (uintptr_t) &nmi_mask;\n    lit[LINK_LIT_RAMMASK]           = (uint64_t) (uintptr_t) &rammask;\n    lit[LINK_LIT_READLOOKUP2]       = (uint64_t) (uintptr_t) readlookup2;\n    lit[LINK_LIT_RAM]               = (uint64_t) (uintptr_t) &ram;\n    lit[LINK_LIT_DR_ARMED]          = (uint64_t) (uintptr_t) &cpu_dr_armed;\n    lit[LINK_LIT_IOAPIC_PATH]       = (uint64_t) (uintptr_t) &ioapic_irq_path_active;\n    lit[LINK_LIT_LAPIC_EXTINT]      = (uint64_t) (uintptr_t) &cpu_lapic_extint_live[0];\n    lit[LINK_LIT_LAPIC_IRR]         = (uint64_t) (uintptr_t) &cpu_lapic_irr_live;\n\n',
     '\n    lit[LINK_LIT_HOT]         = (uint64_t) (uintptr_t) __start_k9xhot;\n    lit[LINK_LIT_READLOOKUP2] = (uint64_t) (uintptr_t) readlookup2;\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     "\n    /*X17 = the literal pool. X1 = the exit's slot, whose exit_pc and exit_cs\n      must match cpu_state.pc and the CS base and whose entry must be set;\n      X15 = its entry; W2 = cs + pc*/\n    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n",
     "\n    /*X17 = the literal pool, X16 = __start_k9xhot. X1 = the exit's slot way\n      whose exit_pc and exit_cs match cpu_state.pc and the CS base and\n      whose entry must be set; X15 = its entry; W2 = cs + pc*/\n    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n    host_arm64_LDR_IMM_W(block, REG_W2, REG_CPUSTATE, rep_state_offset(&cpu_state.pc));\n',
     "    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X17, LINK_LIT(LINK_LIT_HOT));\n    host_arm64_MOVZ_IMM(block, REG_W22, 0);\n    /*W26 = 1 once the routine has run this block's timers itself*/\n    host_arm64_MOVZ_IMM(block, REG_W26, 0);\n    host_arm64_LDR_IMM_W(block, REG_W2, REG_CPUSTATE, rep_state_offset(&cpu_state.pc));\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDP_IMM_X(block, REG_X5, REG_X15, REG_X0, LINK_SLOT(exit_pc));\n    host_arm64_ORRX_REG(block, REG_X4, REG_X2, REG_X3, 32);\n',
     "    host_arm64_LDP_IMM_X(block, REG_X5, REG_X15, REG_X0, LINK_SLOT(exit_pc));\n    /*Start the cache miss a check below waits on: the target's page's dirty\n      mask. PRFM never faults, so an empty slot's NULL pointer is harmless;\n      X12 is reloaded before it is used again.*/\n    host_arm64_LDR_IMM_X(block, REG_X12, REG_X0, LINK_SLOT(dirty_mask));\n    host_arm64_PRFM_IMM(block, REG_X12, 0);\n    host_arm64_ORRX_REG(block, REG_X4, REG_X2, REG_X3, 32);\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_CMPX_REG(block, REG_X5, REG_X4);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X15);\n',
     '    host_arm64_CMPX_REG(block, REG_X5, REG_X4);\n    other_way       = host_arm64_BNE_SHORT_(block);\n    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X15);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X15);\n\n',
     '    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X15);\n    way_found       = &block_write_data[block_pos];\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     "\n    /*Target not freed or changed since the slot was filled. W6 = the slot's\n      status | npxc << 16*/\n    host_arm64_LDR_IMM_X(block, REG_X4, REG_X1, LINK_SLOT(block));\n    host_arm64_LDP_IMM_W(block, REG_W5, REG_W6, REG_X1, LINK_SLOT(gen));\n    host_arm64_LDR_IMM_W(block, REG_W4, REG_X4, offsetof(codeblock_t, link_gen));\n    host_arm64_CMP_REG(block, REG_W4, REG_W5);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n\n",
     "\n    /*The target is unchanged since the slot was filled: a change empties\n      every slot that links to it (codegen_link_block_changed()), so the\n      entry check above covers it. W6 = the slot's status | npxc << 16*/\n    host_arm64_LDR_IMM_W(block, REG_W6, REG_X1, LINK_SLOT(status));\n\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '      check (dr_blocks_cache()). W7 = abrt and smi_line in its top half,\n      W14 = cycles, X12 = &nmi*/\n    host_arm64_LDP_IMM_W(block, REG_W7, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state.abrt) - 2);\n',
     '      check (dr_blocks_cache()). W7 = abrt and smi_line in its top half,\n      W14 = cycles*/\n    host_arm64_LDP_IMM_W(block, REG_W7, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state.abrt) - 2);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDP_IMM_W(block, REG_W7, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state.abrt) - 2);\n    host_arm64_LDR_IMM_X(block, REG_X13, REG_X17, LINK_LIT(LINK_LIT_DR_ARMED));\n    host_arm64_LDP_IMM_X(block, REG_X3, REG_X4, REG_X17, LINK_LIT(LINK_LIT_WAS_RESET));\n    host_arm64_LDP_IMM_X(block, REG_X5, REG_X8, REG_X17, LINK_LIT(LINK_LIT_CPU_INIT));\n    /*X9 = &nmi_enable, loaded only as the pair of the next entry*/\n    host_arm64_LDP_IMM_X(block, REG_X9, REG_X10, REG_X17, LINK_LIT(LINK_LIT_NMI_ENABLE));\n    host_arm64_LDP_IMM_X(block, REG_X11, REG_X12, REG_X17, LINK_LIT(LINK_LIT_OVERRIDE_DYNAREC));\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X3, 0);\n    host_arm64_LDR_IMM_W(block, REG_W4, REG_X4, 0);\n    host_arm64_LDR_IMM_W(block, REG_W5, REG_X5, 0);\n    host_arm64_LDR_IMM_W(block, REG_W8, REG_X8, 0);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X10, 0);\n    host_arm64_LDR_IMM_W(block, REG_W11, REG_X11, 0);\n    host_arm64_LDR_IMM_W(block, REG_W13, REG_X13, 0);\n    host_arm64_AND_IMM(block, REG_W7, REG_W7, 0xffff0000);\n    host_arm64_ORR_REG(block, REG_W3, REG_W3, REG_W4, 0);\n    host_arm64_ORR_REG(block, REG_W5, REG_W5, REG_W8, 0);\n    host_arm64_ORR_REG(block, REG_W7, REG_W7, REG_W11, 0);\n    host_arm64_ORR_REG(block, REG_W3, REG_W3, REG_W5, 0);\n    host_arm64_ORR_REG(block, REG_W7, REG_W7, REG_W10, 0);\n    host_arm64_ORR_REG(block, REG_W5, REG_W5, REG_W13, 0);\n    host_arm64_ORR_REG(block, REG_W3, REG_W3, REG_W7, 0);\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W3);\n\n',
     '    host_arm64_LDP_IMM_W(block, REG_W7, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state.abrt) - 2);\n    {\n        /*The flags, two to a load where they sit side by side in an aligned\n          pair (386_common.c places them so), ORed into X7*/\n        static const int regs[] = { REG_X3, REG_X4, REG_X5, REG_X8, REG_X10, REG_X11, REG_X13 };\n        int              offs[] = { HOT(x86_was_reset), HOT(cpu_flush_pending), HOT(cpu_init), HOT(new_ne),\n                                    HOT(cpu_force_interpreter), HOT(cpu_override_dynarec), HOT(cpu_dr_armed) };\n        const int        nr_offs = (int) (sizeof(offs) / sizeof(offs[0]));\n        int              nr_regs = 0;\n\n        for (int c = 1; c < nr_offs; c++)\n            for (int d = c; (d > 0) && (offs[d - 1] > offs[d]); d--) {\n                const int t = offs[d];\n                offs[d]     = offs[d - 1];\n                offs[d - 1] = t;\n            }\n        for (int c = 0; c < nr_offs; c++) {\n            if (!(offs[c] & 7) && ((c + 1) < nr_offs) && (offs[c + 1] == (offs[c] + 4))) {\n                host_arm64_LDR_IMM_X(block, regs[nr_regs++], REG_X16, offs[c]);\n                c++;\n            } else\n                host_arm64_LDR_IMM_W(block, regs[nr_regs++], REG_X16, offs[c]);\n        }\n        host_arm64_LDR_IMM_W(block, REG_W12, REG_X16, HOT(nmi));\n        host_arm64_AND_IMM(block, REG_W7, REG_W7, 0xffff0000);\n        for (int c = 0; c < nr_regs; c++)\n            host_arm64_ORRX_REG(block, REG_X7, REG_X7, regs[c], 0);\n    }\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_X7);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '      rest is out of line, with W12 = nmi*/\n    host_arm64_LDR_IMM_W(block, REG_W12, REG_X12, 0);\n    nmi_set  = host_arm64_CBNZ_SHORT_(block, REG_W12);\n',
     '      rest is out of line, with W12 = nmi*/\n    nmi_set  = host_arm64_CBNZ_SHORT_(block, REG_W12);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDR_IMM_X(block, REG_X13, REG_CPUSTATE, rep_state_offset(&cpu_state.CR0.l));\n    host_arm64_LDP_IMM_X(block, REG_X3, REG_X4, REG_X17, LINK_LIT(LINK_LIT_PIC));\n    miss[nr_miss++] = host_arm64_TBNZ_SHORT_(block, REG_X13, 32 + 8);\n',
     '    host_arm64_LDR_IMM_X(block, REG_X13, REG_CPUSTATE, rep_state_offset(&cpu_state.CR0.l));\n    miss[nr_miss++] = host_arm64_TBNZ_SHORT_(block, REG_X13, 32 + 8);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    irq_ok          = host_arm64_TBZ_SHORT_(block, REG_X13, 32 + 9);\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X3, offsetof(pic_t, int_pending));\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n',
     '    irq_ok          = host_arm64_TBZ_SHORT_(block, REG_X13, 32 + 9);\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X16, HOT(pic) + (int) offsetof(pic_t, int_pending));\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '      miss, and the C loop works out whether it is deliverable*/\n    host_arm64_LDR_IMM_X(block, REG_X5, REG_X17, LINK_LIT(LINK_LIT_IOAPIC_PATH));\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X5, 0);\n    irq_ok_2 = host_arm64_CBZ_SHORT_(block, REG_W5);\n',
     '      miss, and the C loop works out whether it is deliverable*/\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X16, HOT(ioapic_irq_path_active));\n    irq_ok_2 = host_arm64_CBZ_SHORT_(block, REG_W5);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    irq_ok_2 = host_arm64_CBZ_SHORT_(block, REG_W5);\n    host_arm64_LDR_IMM_X(block, REG_X5, REG_X17, LINK_LIT(LINK_LIT_LAPIC_EXTINT));\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X5, 0);\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n',
     '    irq_ok_2 = host_arm64_CBZ_SHORT_(block, REG_W5);\n    host_arm64_LDRB_IMM_W(block, REG_W5, REG_X16, HOT(cpu_lapic_extint_live[0]));\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n    host_arm64_LDR_IMM_X(block, REG_X5, REG_X17, LINK_LIT(LINK_LIT_LAPIC_IRR));\n    host_arm64_LDR_IMM_W(block, REG_W5, REG_X5, 0);\n    miss[nr_miss++] = host_arm64_TBNZ_SHORT_(block, REG_W5, 0);\n',
     '    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W5);\n    host_arm64_LDR_IMM_W(block, REG_W5, REG_X16, HOT(cpu_lapic_irr_live));\n    miss[nr_miss++] = host_arm64_TBNZ_SHORT_(block, REG_W5, 0);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '      it is worked out again here from ES itself: W8 = 0 if ES is flat.*/\n    host_arm64_LDRH_IMM(block, REG_W4, REG_X4, 0);\n    host_arm64_AND_IMM(block, REG_W4, REG_W4, ~(uint32_t) CPU_STATUS_NOTFLATES);\n',
     '      it is worked out again here from ES itself: W8 = 0 if ES is flat.*/\n    host_arm64_LDRH_IMM(block, REG_W4, REG_X16, HOT(cpu_cur_status));\n#    ifdef K9X_NO_ES_RECOMPUTE /* measurement only: the most dropping this could save (not exact) */\n    (void) es_flat;\n#    else\n    host_arm64_AND_IMM(block, REG_W4, REG_W4, ~(uint32_t) CPU_STATUS_NOTFLATES);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_short_branch_set_offset(es_flat, &block_write_data[block_pos]);\n    host_arm64_LDRH_IMM(block, REG_W5, REG_CPUSTATE, rep_state_offset(&cpu_state.npxc));\n',
     '    host_arm64_short_branch_set_offset(es_flat, &block_write_data[block_pos]);\n#    endif\n    host_arm64_LDRH_IMM(block, REG_W5, REG_CPUSTATE, rep_state_offset(&cpu_state.npxc));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    /*The TSC. If it moved, update_tsc() ran inside the block and the C loop\n      does the rest of that arithmetic. X3 = &tsc, X11 = new tsc,\n      X4 = &tsc_old, X5 = &cycles_old*/\n    host_arm64_LDP_IMM_X(block, REG_X3, REG_X4, REG_X17, LINK_LIT(LINK_LIT_TSC));\n    host_arm64_LDP_IMM_X(block, REG_X5, REG_X6, REG_X17, LINK_LIT(LINK_LIT_CYCLES_OLD));\n    host_arm64_LDR_IMM_X(block, REG_X11, REG_X3, 0);\n    host_arm64_LDR_IMM_X(block, REG_X7, REG_X4, 0);\n    host_arm64_CMPX_REG(block, REG_X11, REG_X7);\n',
     '    /*The TSC. If it moved, update_tsc() ran inside the block and the C loop\n      does the rest of that arithmetic. X11 = new tsc*/\n    host_arm64_LDR_IMM_X(block, REG_X11, REG_X16, HOT(tsc));\n    host_arm64_LDR_IMM_X(block, REG_X7, REG_X16, HOT(tsc_old));\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X16, HOT(cycles_old));\n    host_arm64_LDR_IMM_X(block, REG_X4, REG_X16, HOT(timer_target));\n    host_arm64_CMPX_REG(block, REG_X11, REG_X7);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    host_arm64_LDR_IMM_W(block, REG_W7, REG_X5, 0);\n    host_arm64_SUB_REG(block, REG_W7, REG_W7, REG_W14, 0);\n    host_arm64_CMP_IMM(block, REG_W7, 0);\n',
     '    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    host_arm64_SUB_REG(block, REG_W7, REG_W3, REG_W14, 0);\n    host_arm64_CMP_IMM(block, REG_W7, 0);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    /*No timer due at the new TSC*/\n    host_arm64_LDR_IMM_X(block, REG_X7, REG_X6, 0);\n    host_arm64_SUBX_REG(block, REG_X7, REG_X7, REG_X11);\n    host_arm64_CMPX_IMM(block, REG_X7, 0);\n',
     '    /*No timer due at the new TSC*/\n    host_arm64_SUBX_REG(block, REG_X7, REG_X4, REG_X11);\n    host_arm64_CMPX_IMM(block, REG_X7, 0);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_CMPX_IMM(block, REG_X7, 0);\n    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n',
     '    host_arm64_CMPX_IMM(block, REG_X7, 0);\n    timer_due  = host_arm64_BLE_SHORT_(block);\n    timer_done = &block_write_data[block_pos];\n    /*Slice used up: what exec386_dynarec() does at the end of a 5 us slice,\n      when the quantum has more to run: cycles_main -= cycles_start - cycles,\n      cycles += cyc_period, cycles_start = cycles. Its loop does nothing else\n      between the two slices. The end of the quantum is a miss.*/\n    host_arm64_CMP_IMM(block, REG_W14, 0);\n#    ifdef K9X_NO_LINK_SLICE\n    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n    /*Slice not used up*/\n    host_arm64_CMP_IMM(block, REG_W14, 0);\n',
     '    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n    slice_ok        = NULL;\n#    else\n    slice_ok = host_arm64_BGT_SHORT_(block);\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X16, HOT(cycles_start));\n    host_arm64_LDR_IMM_W(block, REG_W4, REG_X16, HOT(cycles_main));\n    host_arm64_LDR_IMM_W(block, REG_W5, REG_X16, HOT(cyc_period));\n    host_arm64_SUB_REG(block, REG_W3, REG_W3, REG_W14, 0);\n    host_arm64_SUB_REG(block, REG_W4, REG_W4, REG_W3, 0);\n    host_arm64_CMP_IMM(block, REG_W4, 0);\n    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n    /*A block that overran its slice by more than a slice leaves cycles <= 0\n      even after one more period: the loop then adds periods without running\n      anything until cycles is positive. Leave that to it.*/\n    host_arm64_ADD_REG(block, REG_W14, REG_W14, REG_W5, 0);\n    host_arm64_CMP_IMM(block, REG_W14, 0);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n\n',
     '    miss[nr_miss++] = host_arm64_BLE_SHORT_(block);\n    /*Nothing is stored yet: a miss further on must leave the slice exactly\n      as the loop expects to find it. W22 = 1: the hit stores below commit\n      W20 = cycles_main and W14 = cycles (also the new cycles_start).\n      X19-X28 are free here: the blocks reload the guest registers they\n      use, and a miss restores them from the frame.*/\n    host_arm64_MOV_REG(block, REG_W20, REG_W4, 0);\n    host_arm64_MOVZ_IMM(block, REG_W22, 1);\n    host_arm64_short_branch_set_offset(slice_ok, &block_write_data[block_pos]);\n#    endif\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    /*Paging and cache-disable bits as when the slot was filled. W9 = them,\n      W12 = phys_page (the upper halves hold virt and rammask)*/\n    host_arm64_LDP_IMM_X(block, REG_X9, REG_X12, REG_X1, LINK_SLOT(cr0_bits));\n    host_arm64_AND_IMM(block, REG_W10, REG_W13, 0xc0000000);\n',
     '    /*Paging and cache-disable bits as when the slot was filled. W9 = them,\n      W12 = phys_page*/\n    host_arm64_LDP_IMM_W(block, REG_W9, REG_W12, REG_X1, LINK_SLOT(cr0_bits));\n    host_arm64_AND_IMM(block, REG_W10, REG_W13, 0xc0000000);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    /*get_phys(cs + pc) gives phys_page. X6 = &get_phys_virt,\n      X7 = &get_phys_phys, W8 = nonzero if get_phys() would miss its cache*/\n    host_arm64_LDP_IMM_X(block, REG_X6, REG_X7, REG_X17, LINK_LIT(LINK_LIT_GET_PHYS_VIRT));\n    host_arm64_LDR_IMM_W(block, REG_W8, REG_X6, 0);\n    host_arm64_EOR_REG(block, REG_W8, REG_W8, REG_W2, 0);\n',
     '\n    /*get_phys(cs + pc) gives phys_page. W8 = nonzero if get_phys() would\n      miss its cache*/\n    host_arm64_LDR_IMM_W(block, REG_W8, REG_X16, HOT(get_phys_virt));\n    host_arm64_EOR_REG(block, REG_W8, REG_W8, REG_W2, 0);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    uncached = host_arm64_BNE_SHORT_(block);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X7, 0);\n    host_arm64_CMP_REG(block, REG_W10, REG_W12);\n',
     '    uncached = host_arm64_BNE_SHORT_(block);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X16, HOT(get_phys_phys));\n    host_arm64_CMP_REG(block, REG_W10, REG_W12);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    xlat_done = &block_write_data[block_pos];\n    host_arm64_LDP_IMM_X(block, REG_X10, REG_X13, REG_X1, LINK_SLOT(mem_exec));\n    host_arm64_LDR_IMM_X(block, REG_X10, REG_X10, 0);\n    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X10);\n\n',
     '    xlat_done = &block_write_data[block_pos];\n    /*_mem_exec[] as when the slot was filled, when the page had code to run\n      (the map has not been rebuilt since). The hash entry needs no check:\n      whatever takes it from the target gives the target a new link_gen.*/\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X1, LINK_SLOT(map_gen));\n    host_arm64_LDR_IMM_W(block, REG_W13, REG_X16, HOT(mem_mapping_gen));\n    host_arm64_CMP_REG(block, REG_W10, REG_W13);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDR_IMM_X(block, REG_X9, REG_X1, LINK_SLOT(block_nr));\n    host_arm64_LDRH_IMM(block, REG_W10, REG_X13, 0);\n    host_arm64_EOR_REG(block, REG_W10, REG_W10, REG_W9, 0);\n    host_arm64_TST_IMM(block, REG_W10, 0xffff);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    host_arm64_LDP_IMM_X(block, REG_X10, REG_X13, REG_X1, LINK_SLOT(page_mask));\n',
     '    host_arm64_LDR_IMM_X(block, REG_X9, REG_X1, LINK_SLOT(block_nr));\n    host_arm64_LDP_IMM_X(block, REG_X10, REG_X13, REG_X1, LINK_SLOT(page_mask));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '      CS access | selector << 16*/\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X3, 0);\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X4, 0);\n    host_arm64_STR_IMM_W(block, REG_W14, REG_X5, 0);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_CPUSTATE, rep_state_offset(&cpu_state.seg_cs.access));\n',
     '      CS access | selector << 16*/\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X16, HOT(tsc));\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X16, HOT(tsc_old));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_X16, HOT(cycles_old));\n    /*A slice crossed above, committed now that every check has passed*/\n    no_slice = host_arm64_CBZ_SHORT_(block, REG_W22);\n    host_arm64_STR_IMM_W(block, REG_W20, REG_X16, HOT(cycles_main));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_X16, HOT(cycles_start));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state._cycles));\n    host_arm64_short_branch_set_offset(no_slice, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_CPUSTATE, rep_state_offset(&cpu_state.seg_cs.access));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDR_IMM_W(block, REG_W10, REG_CPUSTATE, rep_state_offset(&cpu_state.seg_cs.access));\n    host_arm64_LDP_IMM_X(block, REG_X3, REG_X4, REG_X17, LINK_LIT(LINK_LIT_OLDCS));\n    host_arm64_UBFX(block, REG_W13, REG_W10, 16, 16);\n',
     '    host_arm64_LDR_IMM_W(block, REG_W10, REG_CPUSTATE, rep_state_offset(&cpu_state.seg_cs.access));\n    host_arm64_UBFX(block, REG_W13, REG_W10, 16, 16);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_UBFX(block, REG_W13, REG_W10, 16, 16);\n    host_arm64_STRH_IMM(block, REG_W13, REG_X3, 0);\n    host_arm64_UBFX(block, REG_W10, REG_W10, 5, 2);\n',
     '    host_arm64_UBFX(block, REG_W13, REG_W10, 16, 16);\n    host_arm64_STRH_IMM(block, REG_W13, REG_X16, HOT(oldcs));\n    host_arm64_UBFX(block, REG_W10, REG_W10, 5, 2);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_UBFX(block, REG_W10, REG_W10, 5, 2);\n    host_arm64_STR_IMM_W(block, REG_W10, REG_X4, 0);\n    /*get_phys() only writes its cache when it misses*/\n',
     '    host_arm64_UBFX(block, REG_W10, REG_W10, 5, 2);\n    host_arm64_STR_IMM_W(block, REG_W10, REG_X16, HOT(oldcpl));\n    /*get_phys() only writes its cache when it misses*/\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    cached = host_arm64_CBZ_SHORT_(block, REG_W8);\n    host_arm64_STR_IMM_W(block, REG_W2, REG_X6, 0);\n    host_arm64_STR_IMM_W(block, REG_W12, REG_X7, 0);\n    host_arm64_short_branch_set_offset(cached, &block_write_data[block_pos]);\n',
     '    cached = host_arm64_CBZ_SHORT_(block, REG_W8);\n    host_arm64_STR_IMM_W(block, REG_W2, REG_X16, HOT(get_phys_virt));\n    host_arm64_STR_IMM_W(block, REG_W12, REG_X16, HOT(get_phys_phys));\n    host_arm64_short_branch_set_offset(cached, &block_write_data[block_pos]);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    /*cpu_fetch_device and cpu_halted, cleared as the C loop does*/\n    host_arm64_LDP_IMM_X(block, REG_X3, REG_X4, REG_X17, LINK_LIT(LINK_LIT_FETCH_DEVICE));\n    host_arm64_STR_IMM_W(block, REG_WZR, REG_X3, 0);\n    host_arm64_STR_IMM_W(block, REG_WZR, REG_X4, 0);\n    /*The block is about to run: the eviction sweep passes it over once*/\n    host_arm64_LDR_IMM_X(block, REG_X3, REG_X1, LINK_SLOT(block));\n',
     '    /*cpu_fetch_device and cpu_halted, cleared as the C loop does*/\n    host_arm64_STR_IMM_W(block, REG_WZR, REG_X16, HOT(cpu_fetch_device));\n    host_arm64_STR_IMM_W(block, REG_WZR, REG_X16, HOT(cpu_halted));\n    /*The block is about to run: the eviction sweep passes it over once, and\n      it was reached through block->data, so compiling it paid off (reused,\n      which the SMC strike count in invalidate_block() reads), exactly as\n      when exec386_dynarec_dyn() runs it*/\n    host_arm64_LDR_IMM_X(block, REG_X3, REG_X1, LINK_SLOT(block));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDR_IMM_X(block, REG_X3, REG_X1, LINK_SLOT(block));\n    host_arm64_MOVZ_IMM(block, REG_W4, 1);\n    host_arm64_STRB_IMM(block, REG_W4, REG_X3, offsetof(codeblock_t, used));\n    host_arm64_BR(block, REG_X15);\n',
     '    host_arm64_LDR_IMM_X(block, REG_X3, REG_X1, LINK_SLOT(block));\n    host_arm64_MOVZ_IMM(block, REG_W4, 0x0101);\n    host_arm64_STRH_IMM(block, REG_W4, REG_X3, offsetof(codeblock_t, used));\n    host_arm64_BR(block, REG_X15);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss_dest = &block_write_data[block_pos];\n    host_arm64_B(block, codegen_link_miss_rout);\n',
     '    miss_dest = &block_write_data[block_pos];\n    plain_miss = host_arm64_CBZ_SHORT_(block, REG_W26);\n    host_arm64_STR_IMM_W(block, REG_W26, REG_X16, HOT(k9x_post_done));\n    host_arm64_short_branch_set_offset(plain_miss, &block_write_data[block_pos]);\n    host_arm64_B(block, codegen_link_miss_rout);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    /*nmi set: miss only if nmi_enable is too, and nmi_mask or an NMI from\n',
     '\n    if (block_write_data != start_data)\n        fatal("build_link_routine - hot path does not fit in one allocator block\\n");\n\n    /*Out of line: the paths a hit rarely takes, in an allocator block of\n      their own. It is the next one handed out, and every short branch\n      between the two checks its range.*/\n    codegen_alloc(block, BLOCK_MAX);\n    cold_data = block_write_data;\n\n    /*A timer is due at the new TSC: run the timers as exec386_dynarec() does\n      at the end of a block, then carry on with the checks it makes before\n      the next one. Its interrupt and event checks for this block came before\n      its timers, as they did here, so they are not repeated; a miss from\n      here on tells the loop not to repeat any of it (W26). The C call keeps\n      X19-X28; X0, X16, X17 and the values a callback may have changed (TSC,\n      cycles, CR0 and flags) are reloaded.*/\n    host_arm64_short_branch_set_offset(timer_due, &block_write_data[block_pos]);\n    host_arm64_MOVX_REG(block, REG_X19, REG_X1, 0);\n    host_arm64_MOVX_REG(block, REG_X21, REG_X2, 0);\n    host_arm64_MOVX_REG(block, REG_X25, REG_X15, 0);\n    host_arm64_MOVX_REG(block, REG_X0, REG_X11, 0);\n    host_arm64_call(block, (void *) k9x_link_timer);\n    /*X0 is the slots again: a miss from here returns it to the C loop*/\n    host_arm64_MOVX_REG(block, REG_X0, REG_X19, 0);\n    host_arm64_MOVX_REG(block, REG_X1, REG_X19, 0);\n    host_arm64_MOVX_REG(block, REG_X2, REG_X21, 0);\n    host_arm64_MOVX_REG(block, REG_X15, REG_X25, 0);\n    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X17, LINK_LIT(LINK_LIT_HOT));\n    host_arm64_MOVZ_IMM(block, REG_W26, 1);\n    host_arm64_LDR_IMM_X(block, REG_X11, REG_X16, HOT(tsc));\n    host_arm64_LDR_IMM_W(block, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state._cycles));\n    host_arm64_LDR_IMM_X(block, REG_X13, REG_CPUSTATE, rep_state_offset(&cpu_state.CR0.l));\n    /*The loop\'s choice of how to run the next block*/\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X16, HOT(cpu_force_interpreter));\n    host_arm64_LDR_IMM_W(block, REG_W4, REG_X16, HOT(cpu_override_dynarec));\n    host_arm64_LDR_IMM_W(block, REG_W5, REG_X16, HOT(cpu_flush_pending));\n    host_arm64_ORR_REG(block, REG_W3, REG_W3, REG_W4, 0);\n    host_arm64_ORR_REG(block, REG_W3, REG_W3, REG_W5, 0);\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W3);\n    host_arm64_B(block, timer_done);\n\n    /*The first way links to another target: the others in turn, X1 = the\n      one that matches*/\n    host_arm64_short_branch_set_offset(other_way, &block_write_data[block_pos]);\n    for (int w = 1; w < CODEGEN_LINK_WAYS; w++) {\n        host_arm64_ADDX_IMM(block, REG_X1, REG_X0, w * sizeof(codegen_link_slot_t));\n        host_arm64_LDP_IMM_X(block, REG_X5, REG_X15, REG_X1, LINK_SLOT(exit_pc));\n        host_arm64_CMPX_REG(block, REG_X5, REG_X4);\n        if (w < (CODEGEN_LINK_WAYS - 1))\n            way_match[w] = host_arm64_BEQ_SHORT_(block);\n        else\n            miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    }\n    for (int w = 1; w < (CODEGEN_LINK_WAYS - 1); w++)\n        host_arm64_short_branch_set_offset(way_match[w], &block_write_data[block_pos]);\n    miss[nr_miss++] = host_arm64_CBZ_SHORT_(block, REG_X15);\n    host_arm64_B(block, way_found);\n\n    /*nmi set: miss only if nmi_enable is too, and nmi_mask or an NMI from\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_short_branch_set_offset(nmi_set, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_X(block, REG_X3, REG_X17, LINK_LIT(LINK_LIT_NMI_ENABLE));\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X3, 0);\n    nmi_ok = host_arm64_CBZ_SHORT_(block, REG_W3);\n',
     '    host_arm64_short_branch_set_offset(nmi_set, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X16, HOT(nmi_enable));\n    nmi_ok = host_arm64_CBZ_SHORT_(block, REG_W3);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_short_branch_set_offset(nmi_ok, nmi_done);\n    host_arm64_LDR_IMM_X(block, REG_X3, REG_X17, LINK_LIT(LINK_LIT_NMI_MASK));\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X3, 0);\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W3);\n',
     '    host_arm64_short_branch_set_offset(nmi_ok, nmi_done);\n    host_arm64_LDR_IMM_W(block, REG_W3, REG_X16, HOT(nmi_mask));\n    miss[nr_miss++] = host_arm64_CBNZ_SHORT_(block, REG_W3);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_CMPX_REG(block, REG_X10, REG_X13);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n',
     '    host_arm64_CMPX_REG(block, REG_X10, REG_X13);\n    xlat_same = host_arm64_BEQ_SHORT_(block);\n    host_arm64_short_branch_set_offset(xlat_same, xlat_done);\n    /*Any other translation there is another page*/\n    host_arm64_CMN_IMM(block, REG_W10, 1);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_CMN_IMM(block, REG_W10, 1);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    host_arm64_B(block, xlat_done);\n    host_arm64_short_branch_set_offset(no_paging, &block_write_data[block_pos]);\n',
     "    host_arm64_CMN_IMM(block, REG_W10, 1);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n\n    /*Not in readlookup2: get_phys() walks the page tables, which the guest\n      can see (accessed bits, and the readlookup2 fill and the cycles it\n      costs), so it is called here, as exec386_dynarec_dyn() calls it first\n      thing. What the C loop does before that is done first: the loop-top\n      stores, a crossed slice committed. From here on a miss re-enters\n      exec386_dynarec_dyn() directly (W26 = 2), and its get_phys() finds\n      this result in its one-entry cache. Another page or a fault is a miss.\n      The hit path's stores after this repeat the same values, except\n      cycles (get_phys() may have charged it), which is not stored again\n      (W22 = 0); get_phys() kept its own cache (W8 = 0).*/\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X16, HOT(tsc));\n    host_arm64_STR_IMM_Q(block, REG_X11, REG_X16, HOT(tsc_old));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_X16, HOT(cycles_old));\n    walk_no_slice = host_arm64_CBZ_SHORT_(block, REG_W22);\n    host_arm64_STR_IMM_W(block, REG_W20, REG_X16, HOT(cycles_main));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_X16, HOT(cycles_start));\n    host_arm64_STR_IMM_W(block, REG_W14, REG_CPUSTATE, rep_state_offset(&cpu_state._cycles));\n    host_arm64_short_branch_set_offset(walk_no_slice, &block_write_data[block_pos]);\n    host_arm64_MOVZ_IMM(block, REG_W22, 0);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_CPUSTATE, rep_state_offset(&cpu_state.seg_cs.access));\n    host_arm64_UBFX(block, REG_W13, REG_W10, 16, 16);\n    host_arm64_STRH_IMM(block, REG_W13, REG_X16, HOT(oldcs));\n    host_arm64_UBFX(block, REG_W10, REG_W10, 5, 2);\n    host_arm64_STR_IMM_W(block, REG_W10, REG_X16, HOT(oldcpl));\n    host_arm64_STR_IMM_W(block, REG_WZR, REG_X16, HOT(cpu_halted));\n    host_arm64_MOVZ_IMM(block, REG_W26, 2);\n    host_arm64_MOVX_REG(block, REG_X19, REG_X1, 0);\n    host_arm64_MOVX_REG(block, REG_X21, REG_X2, 0);\n    host_arm64_MOVX_REG(block, REG_X23, REG_X11, 0);\n    host_arm64_MOVX_REG(block, REG_X24, REG_X12, 0);\n    host_arm64_MOVX_REG(block, REG_X25, REG_X15, 0);\n    host_arm64_MOVX_REG(block, REG_X27, REG_X14, 0);\n    host_arm64_MOV_REG(block, REG_W0, REG_W2, 0);\n    host_arm64_call(block, (void *) k9x_link_phys);\n    host_arm64_CMP_REG(block, REG_W0, REG_W24);\n    host_arm64_MOVX_REG(block, REG_X0, REG_X19, 0);\n    host_arm64_MOVX_REG(block, REG_X1, REG_X19, 0);\n    host_arm64_MOVX_REG(block, REG_X2, REG_X21, 0);\n    host_arm64_MOVX_REG(block, REG_X11, REG_X23, 0);\n    host_arm64_MOVX_REG(block, REG_X12, REG_X24, 0);\n    host_arm64_MOVX_REG(block, REG_X14, REG_X27, 0);\n    host_arm64_MOVX_REG(block, REG_X15, REG_X25, 0);\n    host_arm64_ADR(block, REG_X17, (int) ((uintptr_t) lit - (uintptr_t) &block_write_data[block_pos]));\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X17, LINK_LIT(LINK_LIT_HOT));\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n    host_arm64_MOVZ_IMM(block, REG_W8, 0);\n    host_arm64_B(block, xlat_done);\n    host_arm64_short_branch_set_offset(no_paging, &block_write_data[block_pos]);\n"),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_short_branch_set_offset(no_paging, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_X(block, REG_X10, REG_X17, LINK_LIT(LINK_LIT_RAMMASK));\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X10, 0);\n    host_arm64_LDR_IMM_W(block, REG_W13, REG_X1, LINK_SLOT(rammask));\n',
     '    host_arm64_short_branch_set_offset(no_paging, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_W(block, REG_W10, REG_X16, HOT(rammask));\n    host_arm64_LDR_IMM_W(block, REG_W13, REG_X1, LINK_SLOT(rammask));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    no_paging_2 = host_arm64_TBZ_SHORT_(block, REG_W13, 31);\n    host_arm64_LDR_IMM_X(block, REG_X13, REG_X17, LINK_LIT(LINK_LIT_READLOOKUP2));\n',
     '    no_paging_2 = host_arm64_TBZ_SHORT_(block, REG_W13, 31);\n    /*X16 stays __start_k9xhot here: X7 is the scratch register (only\n      instructions with encodable immediates follow, which never use it)*/\n    host_arm64_LDR_IMM_X(block, REG_X13, REG_X17, LINK_LIT(LINK_LIT_READLOOKUP2));\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_LDR_IMM_X(block, REG_X13, REG_X17, LINK_LIT(LINK_LIT_READLOOKUP2));\n    host_arm64_UBFX(block, REG_W16, REG_W10, 12, 20);\n    host_arm64_LDRX_REG_LSL3(block, REG_X13, REG_X13, REG_X16);\n    host_arm64_CMN_IMM(block, REG_W13, 1);\n',
     '    host_arm64_LDR_IMM_X(block, REG_X13, REG_X17, LINK_LIT(LINK_LIT_READLOOKUP2));\n    host_arm64_UBFX(block, REG_W7, REG_W10, 12, 20);\n    host_arm64_LDRX_REG_LSL3(block, REG_X13, REG_X13, REG_X7);\n    host_arm64_CMN_IMM(block, REG_W13, 1);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    miss[nr_miss++] = host_arm64_BEQ_SHORT_(block);\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X17, LINK_LIT(LINK_LIT_RAM));\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X16, 0);\n    host_arm64_ADDX_REG_UXTW(block, REG_X13, REG_X13, REG_W10);\n',
     '    miss[nr_miss++] = host_arm64_BEQ_SHORT_(block);\n    host_arm64_LDR_IMM_X(block, REG_X7, REG_X16, HOT(ram));\n    host_arm64_ADDX_REG_UXTW(block, REG_X13, REG_X13, REG_W10);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_ADDX_REG_UXTW(block, REG_X13, REG_X13, REG_W10);\n    host_arm64_SUBX_REG(block, REG_X13, REG_X13, REG_X16);\n    xlat_2_done = &block_write_data[block_pos];\n',
     '    host_arm64_ADDX_REG_UXTW(block, REG_X13, REG_X13, REG_W10);\n    host_arm64_SUBX_REG(block, REG_X13, REG_X13, REG_X7);\n    xlat_2_done = &block_write_data[block_pos];\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    xlat_2_done = &block_write_data[block_pos];\n    host_arm64_LDR_IMM_W(block, REG_W16, REG_X9, offsetof(codeblock_t, phys_2));\n    host_arm64_EOR_REG(block, REG_W16, REG_W16, REG_W13, 0);\n    host_arm64_TST_IMM(block, REG_W16, 0xfffff000);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n',
     '    xlat_2_done = &block_write_data[block_pos];\n    host_arm64_LDR_IMM_W(block, REG_W7, REG_X9, offsetof(codeblock_t, phys_2));\n    host_arm64_EOR_REG(block, REG_W7, REG_W7, REG_W13, 0);\n    host_arm64_TST_IMM(block, REG_W7, 0xfffff000);\n    miss[nr_miss++] = host_arm64_BNE_SHORT_(block);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    host_arm64_short_branch_set_offset(no_paging_2, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_X(block, REG_X16, REG_X17, LINK_LIT(LINK_LIT_RAMMASK));\n    host_arm64_LDR_IMM_W(block, REG_W16, REG_X16, 0);\n    host_arm64_AND_REG(block, REG_W13, REG_W10, REG_W16, 0);\n    host_arm64_B(block, xlat_2_done);\n',
     '    host_arm64_short_branch_set_offset(no_paging_2, &block_write_data[block_pos]);\n    host_arm64_LDR_IMM_W(block, REG_W7, REG_X16, HOT(rammask));\n    host_arm64_AND_REG(block, REG_W13, REG_W10, REG_W7, 0);\n    host_arm64_B(block, xlat_2_done);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '        fatal("build_link_routine - too many miss branches\\n");\n    if (block_write_data != start_data)\n        fatal("build_link_routine - routine does not fit in one allocator block\\n");\n    for (int c = 0; c < nr_miss; c++)\n',
     '        fatal("build_link_routine - too many miss branches\\n");\n    if (block_write_data != cold_data)\n        fatal("build_link_routine - out-of-line paths do not fit in one allocator block\\n");\n    for (int c = 0; c < nr_miss; c++)\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    block_write_data      = block->data;\n    build_loadstore_routines(block);\n',
     '    block_write_data      = block->data;\n    nr_stub_aborts = 0;\n    build_loadstore_routines(block);\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    codegen_exit_rout = &block_write_data[block_pos];\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n',
     '    codegen_exit_rout = &block_write_data[block_pos];\n    for (int c = 0; c < nr_stub_aborts; c++)\n        host_arm64_B_patch(stub_aborts[c], codegen_exit_rout);\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '    link_site = 0;\n#    endif\n\n    if (block->flags & CODEBLOCK_HAS_FPU) {\n',
     '    link_site = 0;\n#    endif\n    codegen_imm_store_forget();\n\n    if (block->flags & CODEBLOCK_HAS_FPU) {\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '{\n    codegen_link_slot_t *slot = &codegen_link_slots[get_block_nr(block)][link_site++ % CODEGEN_LINK_SLOTS];\n\n',
     '{\n    codegen_link_slot_t *slot = &codegen_link_slots[get_block_nr(block)][link_site++ % CODEGEN_LINK_SLOTS][0];\n\n'),
    ('86box/src/codegen/codegen_backend_arm64.c',
     '\n    codegen_alloc(block, 20);\n',
     '\n#    ifdef K9X_DIAG\n    /*Instructions up to this exit, and the exit itself*/\n    k9x_diag_count(block, &k9x_cnt_ins, block->ins ? block->ins : 1);\n    k9x_diag_count(block, &k9x_cnt_exits, 1);\n#    endif\n    codegen_alloc(block, 20);\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     'uint32_t *\nhost_arm64_CBZ_SHORT_(codeblock_t *block, int reg)\n',
     'uint32_t *\nhost_arm64_BGT_SHORT_(codeblock_t *block)\n{\n    codegen_addlong(block, OPCODE_BCOND | COND_GT);\n    return (uint32_t *) &block_write_data[block_pos - 4];\n}\nuint32_t *\nhost_arm64_CBZ_SHORT_(codeblock_t *block, int reg)\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '}\n\nvoid\nhost_arm64_LDR_REG(codeblock_t *block, int dest_reg, int base_reg, int offset_reg)\n',
     '}\n\n/*PRFM PLDL1KEEP, [base, #offset]: never faults, whatever the address*/\nvoid\nhost_arm64_PRFM_IMM(codeblock_t *block, int base_reg, int offset)\n{\n    if (!in_range12_q(offset))\n        fatal("host_arm64_PRFM_IMM out of range12 %i\\n", offset);\n    codegen_addlong(block, (0x3e6 << 22) | OFFSET12_Q(offset) | Rn(base_reg) | Rt(0));\n}\n\nvoid\nhost_arm64_LDR_REG(codeblock_t *block, int dest_reg, int base_reg, int offset_reg)\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '{\n    codegen_addlong(block, OPCODE_MOVZ_X | MOV_WIDE_HW(0) | IMM16(imm_data & 0xffff) | Rd(reg));\n',
     '{\n    /* A value within 4 GiB of the code (an address in the program: the pool\n       sits next to it, plat_mmap()) that would take three or four moves:\n       ADRP and ADD instead. The code never moves once written. */\n    if (((imm_data >> 32) & 0xffff) && ((imm_data >> 16) & 0xffff)) {\n        codegen_alloc(block, 8);\n        const uint64_t pc    = (uint64_t) (uintptr_t) &block_write_data[block_pos];\n        const int64_t  pages = (int64_t) ((imm_data & ~(uint64_t) 0xfff) - (pc & ~(uint64_t) 0xfff)) >> 12;\n\n        if ((pages >= -(1 << 20)) && (pages < (1 << 20))) {\n            codegen_addlong(block, 0x90000000u | ((uint32_t) (pages & 3) << 29) | ((uint32_t) ((pages >> 2) & 0x7ffff) << 5) | Rd(reg));\n            if (imm_data & 0xfff)\n                codegen_addlong(block, 0x91000000u | ((uint32_t) (imm_data & 0xfff) << 10) | Rn(reg) | Rd(reg));\n            return;\n        }\n    }\n    codegen_addlong(block, OPCODE_MOVZ_X | MOV_WIDE_HW(0) | IMM16(imm_data & 0xffff) | Rd(reg));\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '}\n\nvoid\nhost_arm64_STP_PREIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n',
     '}\n\n/*B to a place not built yet: host_arm64_B_patch() sets where*/\nuint32_t *\nhost_arm64_B_placeholder(codeblock_t *block)\n{\n    codegen_alloc(block, 4);\n    codegen_addlong(block, OPCODE_B);\n    return (uint32_t *) &block_write_data[block_pos - 4];\n}\nvoid\nhost_arm64_B_patch(uint32_t *site, void *dest)\n{\n    const intptr_t offset = (intptr_t) ((uint8_t *) dest - (uint8_t *) site);\n\n    if (!offset_is_26bit(offset))\n        fatal("host_arm64_B_patch - offset out of range %" PRIiPTR "\\n", offset);\n    *site = OPCODE_B | OFFSET26(offset);\n}\n\n/*STP Wt1, Wt2, [Xn, #offset], as a word to write over another instruction*/\nint\nhost_arm64_STP_W_fits(int offset)\n{\n    return !(offset & 3) && (offset >= -256) && (offset <= 252);\n}\nuint32_t\nhost_arm64_STP_W_word(int src_reg1, int src_reg2, int base_reg, int offset)\n{\n    return 0x29000000u | ((uint32_t) ((offset >> 2) & 0x7f) << 15) | Rn(base_reg) | Rt(src_reg1) | Rt2(src_reg2);\n}\n\nvoid\nhost_arm64_STP_PREIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '{\n    uint8_t *branch_src;\n    int      is_local;\n\n    /* Prefer direct BL for local in-range JIT targets; otherwise preserve\n',
     '{\n    uint8_t *branch_src;\n\n    /* Prefer direct BL for local in-range JIT targets; otherwise preserve\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '\n    /* Prefer direct BL for local in-range JIT targets; otherwise preserve\n       existing absolute MOVX+BLR fallback for correctness. */\n    codegen_alloc(block, 4);\n',
     '\n    /* A direct BL to anything in range (the pool sits next to the program,\n       plat_mmap()); otherwise an absolute MOVX+BLR. */\n    codegen_alloc(block, 4);\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '    branch_src = &block_write_data[block_pos];\n    is_local   = codegen_allocator_contains_host_ptr(dst_addr);\n    if (is_local && codegen_allocator_can_branch_imm26(branch_src, dst_addr)) {\n        intptr_t offset = (intptr_t) ((uint8_t *) dst_addr - branch_src);\n        codegen_addlong(block, OPCODE_BL | OFFSET26(offset));\n        return;\n    }\n',
     '    branch_src = &block_write_data[block_pos];\n    if (codegen_allocator_can_branch_imm26(branch_src, dst_addr))\n        codegen_addlong(block, OPCODE_BL | OFFSET26((intptr_t) ((uint8_t *) dst_addr - branch_src)));\n    else {\n        host_arm64_MOVX_IMM(block, REG_X16, (uint64_t) dst_addr);\n        host_arm64_BLR(block, REG_X16);\n    }\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '        host_arm64_BLR(block, REG_X16);\n    }\n\n    host_arm64_MOVX_IMM(block, REG_X16, (uint64_t) dst_addr);\n    host_arm64_BLR(block, REG_X16);\n}\n\n',
     '        host_arm64_BLR(block, REG_X16);\n    }\n}\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '    void    *dst_ptr = (void *) dst_addr;\n    int      is_local;\n\n',
     '    void    *dst_ptr = (void *) dst_addr;\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '\n    /* Prefer direct B for local in-range JIT targets; otherwise preserve\n       existing absolute MOVX+BR fallback for correctness. */\n    codegen_alloc(block, 4);\n',
     '\n    /* A direct B to anything in range; otherwise an absolute MOVX+BR. */\n    codegen_alloc(block, 4);\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.c',
     '    branch_src = &block_write_data[block_pos];\n    is_local   = codegen_allocator_contains_host_ptr(dst_ptr);\n    if (is_local && codegen_allocator_can_branch_imm26(branch_src, dst_ptr)) {\n        intptr_t offset = (intptr_t) ((uint8_t *) dst_ptr - branch_src);\n',
     '    branch_src = &block_write_data[block_pos];\n    if (codegen_allocator_can_branch_imm26(branch_src, dst_ptr)) {\n        intptr_t offset = (intptr_t) ((uint8_t *) dst_ptr - branch_src);\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.h',
     'uint32_t *host_arm64_BLE_SHORT_(codeblock_t *block);\nuint32_t *host_arm64_CBZ_SHORT_(codeblock_t *block, int reg);\n',
     'uint32_t *host_arm64_BLE_SHORT_(codeblock_t *block);\nuint32_t *host_arm64_BGT_SHORT_(codeblock_t *block);\nuint32_t *host_arm64_CBZ_SHORT_(codeblock_t *block, int reg);\n'),
    ('86box/src/codegen/codegen_backend_arm64_ops.h',
     'void host_arm64_LDR_IMM_X(codeblock_t *block, int dest_reg, int base_reg, int offset);\nvoid host_arm64_LDR_REG(codeblock_t *block, int dest_reg, int base_reg, int offset_reg);\n',
     'void host_arm64_LDR_IMM_X(codeblock_t *block, int dest_reg, int base_reg, int offset);\nvoid host_arm64_PRFM_IMM(codeblock_t *block, int base_reg, int offset);\nuint32_t *host_arm64_B_placeholder(codeblock_t *block);\nvoid      host_arm64_B_patch(uint32_t *site, void *dest);\nint      host_arm64_STP_W_fits(int offset);\nuint32_t host_arm64_STP_W_word(int src_reg1, int src_reg2, int base_reg, int offset);\n/*codegen_direct_write_32_imm() forgets the store it may build on*/\nvoid codegen_imm_store_forget(void);\nvoid host_arm64_LDR_REG(codeblock_t *block, int dest_reg, int base_reg, int offset_reg);\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("MEM_LOAD_ABS - %02x\\n", uop->dest_reg_a_real);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n    if (REG_IS_B(dest_size)) {\n',
     '        fatal("MEM_LOAD_ABS - %02x\\n", uop->dest_reg_a_real);\n    if (REG_IS_B(dest_size)) {\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("MEM_LOAD_REG_EA - %02x\\n", uop->dest_reg_a_real);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n    if (REG_IS_W(dest_size))\n',
     '        fatal("MEM_LOAD_REG_EA - %02x\\n", uop->dest_reg_a_real);\n    if (REG_IS_W(dest_size))\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("MEM_LOAD_REG - %02x\\n", uop->dest_reg_a_real);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n    if (REG_IS_B(dest_size)) {\n',
     '        fatal("MEM_LOAD_REG - %02x\\n", uop->dest_reg_a_real);\n    if (REG_IS_B(dest_size)) {\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_load_double);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n    host_arm64_FMOV_D_D(block, dest_reg, REG_V_TEMP);\n',
     '    host_arm64_call(block, codegen_mem_load_double);\n    host_arm64_FMOV_D_D(block, dest_reg, REG_V_TEMP);\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_load_single);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n    host_arm64_FCVT_D_S(block, dest_reg, REG_V_TEMP);\n',
     '    host_arm64_call(block, codegen_mem_load_single);\n    host_arm64_FCVT_D_S(block, dest_reg, REG_V_TEMP);\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("MEM_STORE_ABS - %02x\\n", uop->dest_reg_a_real);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '        fatal("MEM_STORE_ABS - %02x\\n", uop->dest_reg_a_real);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("MEM_STORE_REG - %02x\\n", uop->src_reg_c_real);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '        fatal("MEM_STORE_REG - %02x\\n", uop->src_reg_c_real);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_store_byte);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '    host_arm64_call(block, codegen_mem_store_byte);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_store_word);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '    host_arm64_call(block, codegen_mem_store_word);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_store_long);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '    host_arm64_call(block, codegen_mem_store_long);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_store_single);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '    host_arm64_call(block, codegen_mem_store_single);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_call(block, codegen_mem_store_double);\n    host_arm64_CBNZ(block, REG_X1, (uintptr_t) codegen_exit_rout);\n\n',
     '    host_arm64_call(block, codegen_mem_store_double);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '}\n\nvoid\ncodegen_set_jump_dest(codeblock_t *block, void *p)\n',
     '}\n\n/*The last 32-bit immediate stored to cpu_state: where the store ended, the\n  value (still in W16) and its offset. A store of the same value right after\n  it, with nothing emitted between, reuses W16, and one to the next word\n  turns the two into an STP. Nothing may branch to a point between them:\n  a jump destination or a new block forgets it.*/\nstatic uint8_t *imm_store_data;\nstatic int      imm_store_end = -1;\nstatic uint32_t imm_store_val;\nstatic int      imm_store_off;\n\nvoid\ncodegen_imm_store_forget(void)\n{\n    imm_store_end = -1;\n}\n\nvoid\ncodegen_set_jump_dest(codeblock_t *block, void *p)\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    host_arm64_branch_set_offset(p, &block_write_data[block_pos]);\n}\n',
     '    host_arm64_branch_set_offset(p, &block_write_data[block_pos]);\n    codegen_imm_store_forget();\n}\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '    /* 32-bit immediate store fast path used by generic emitters. */\n    host_arm64_mov_imm(block, REG_W16, imm_data);\n\n',
     '    /* 32-bit immediate store fast path used by generic emitters. */\n    const int off = (int) ((uintptr_t) p - (uintptr_t) &cpu_state);\n\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '\n    if (in_range12_w((uintptr_t) p - (uintptr_t) &cpu_state))\n        host_arm64_STR_IMM_W(block, REG_W16, REG_CPUSTATE, (uintptr_t) p - (uintptr_t) &cpu_state);\n    else\n        fatal("codegen_direct_write_32_imm - not in range\\n");\n',
     '\n    if (!in_range12_w(off))\n        fatal("codegen_direct_write_32_imm - not in range\\n");\n'),
    ('86box/src/codegen/codegen_backend_arm64_uops.c',
     '        fatal("codegen_direct_write_32_imm - not in range\\n");\n}\n',
     '        fatal("codegen_direct_write_32_imm - not in range\\n");\n    if ((block_write_data == imm_store_data) && (block_pos == imm_store_end) && (imm_data == imm_store_val)) {\n        if ((off == (imm_store_off + 4)) && host_arm64_STP_W_fits(imm_store_off)) {\n            /*The STR just before becomes an STP of W16 to both words*/\n            *(uint32_t *) &block_write_data[block_pos - 4] = host_arm64_STP_W_word(REG_W16, REG_W16, REG_CPUSTATE, imm_store_off);\n            imm_store_end = -1;\n            return;\n        }\n        host_arm64_STR_IMM_W(block, REG_W16, REG_CPUSTATE, off);\n    } else {\n        host_arm64_mov_imm(block, REG_W16, imm_data);\n        host_arm64_STR_IMM_W(block, REG_W16, REG_CPUSTATE, off);\n    }\n    imm_store_data = block_write_data;\n    imm_store_end  = block_pos;\n    imm_store_val  = imm_data;\n    imm_store_off  = off;\n}\n'),
    ('86box/src/codegen/codegen_backend_x86-64.c',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\ncodegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS];\n\n',
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\ncodegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS][CODEGEN_LINK_WAYS];\n\n'),
    ('86box/src/codegen/codegen_backend_x86-64.c',
     '    if (codegen_block_link) {\n        uintptr_t slot = (uintptr_t) &codegen_link_slots[get_block_nr(block)][0];\n\n',
     '    if (codegen_block_link) {\n        uintptr_t slot = (uintptr_t) &codegen_link_slots[get_block_nr(block)][0][0];\n\n'),
    ('86box/src/codegen/codegen_backend_x86-64.c',
     '{\n    codegen_link_slot_t *slot = &codegen_link_slots[get_block_nr(block)][link_site++ % CODEGEN_LINK_SLOTS];\n\n',
     '{\n    codegen_link_slot_t *slot = &codegen_link_slots[get_block_nr(block)][link_site++ % CODEGEN_LINK_SLOTS][0];\n\n'),
    ('86box/src/codegen/codegen_block.c',
     'static uint32_t link_gen_last = 0;\n\nvoid\ncodegen_link_reset(void)\n',
     'static uint32_t link_gen_last = 0;\n\n/*The slots that link to each block, as a list through the slots, so a\n  change to the block can empty them and the link routine need not read the\n  block to know it is unchanged. A slot is on the list of the block it links\n  to, and on no list while empty.*/\nstatic codegen_link_slot_t *link_in_head[BLOCK_SIZE];\n\nvoid\ncodegen_link_reset(void)\n'),
    ('86box/src/codegen/codegen_block.c',
     '    memset(codegen_link_slots, 0, sizeof(codegen_link_slots));\n}\n',
     '    memset(codegen_link_slots, 0, sizeof(codegen_link_slots));\n    memset(link_in_head, 0, sizeof(link_in_head));\n}\n'),
    ('86box/src/codegen/codegen_block.c',
     '}\n\nvoid\ncodegen_link_block_changed(codeblock_t *block)\n',
     '}\n\nstatic void\nlink_in_remove(codegen_link_slot_t *slot)\n{\n    if (!slot->in_listed)\n        return;\n    if (slot->in_prev != NULL)\n        slot->in_prev->in_next = slot->in_next;\n    else\n        link_in_head[slot->in_nr] = slot->in_next;\n    if (slot->in_next != NULL)\n        slot->in_next->in_prev = slot->in_prev;\n    slot->in_next   = NULL;\n    slot->in_prev   = NULL;\n    slot->in_listed = 0;\n}\n\nstatic void\nlink_in_insert(codeblock_t *block, codegen_link_slot_t *slot)\n{\n    const uint16_t nr = get_block_nr(block);\n\n    slot->in_nr     = nr;\n    slot->in_listed = 1;\n    slot->in_prev   = NULL;\n    slot->in_next   = link_in_head[nr];\n    if (slot->in_next != NULL)\n        slot->in_next->in_prev = slot;\n    link_in_head[nr] = slot;\n}\n\n#ifdef K9X_DIAG\nuint64_t k9x_cnt_changed; /* link_gen bumps, for the cost model */\n#endif\nvoid\ncodegen_link_block_changed(codeblock_t *block)\n'),
    ('86box/src/codegen/codegen_block.c',
     '{\n    if (!codegen_block_link)\n',
     '{\n#ifdef K9X_DIAG\n    k9x_cnt_changed++;\n#endif\n    if (!codegen_block_link)\n'),
    ('86box/src/codegen/codegen_block.c',
     '    block->link_gen = link_gen_last;\n}\n',
     '    block->link_gen = link_gen_last;\n\n    /*Empty every slot that links to it*/\n    codegen_link_slot_t *slot = link_in_head[get_block_nr(block)];\n\n    while (slot != NULL) {\n        codegen_link_slot_t *next = slot->in_next;\n\n        slot->entry     = NULL;\n        slot->in_next   = NULL;\n        slot->in_prev   = NULL;\n        slot->in_listed = 0;\n        slot            = next;\n    }\n    link_in_head[get_block_nr(block)] = NULL;\n}\n'),
    ('86box/src/codegen/codegen_block.c',
     '{\n    memset(codegen_link_slots[get_block_nr(block)], 0, sizeof(codegen_link_slots[0]));\n',
     '{\n    for (int c = 0; c < CODEGEN_LINK_SLOTS; c++)\n        for (int w = 0; w < CODEGEN_LINK_WAYS; w++)\n            link_in_remove(&codegen_link_slots[get_block_nr(block)][c][w]);\n    memset(codegen_link_slots[get_block_nr(block)], 0, sizeof(codegen_link_slots[0]));\n'),
    ('86box/src/codegen/codegen_block.c',
     '}\n\nvoid\ncodegen_link_patch(codegen_link_slot_t *from, codeblock_t *block, uint32_t phys)\n',
     '}\n\n/*exec386_dynarec_dyn() interprets a page in SMC cooldown, which the link\n  routine does not check: cut every link to a block that starts on it. None\n  is made again before the cooldown ends, as the C loop only fills a slot\n  when it runs the target block compiled.*/\nstatic void\nlink_page_blocks_changed(page_t *page)\n{\n    for (uint32_t block_nr = page->block; block_nr; block_nr = codeblock[block_nr].next)\n        codegen_link_block_changed(&codeblock[block_nr]);\n}\n\nvoid\ncodegen_link_patch(codegen_link_slot_t *from, codeblock_t *block, uint32_t phys)\n'),
    ('86box/src/codegen/codegen_block.c',
     "\n    /*The exit's own slot, whatever it held*/\n    slot = from;\n\n",
     "\n    /*The exit's way that already has this target, or else an empty one, or\n      else the ways take turns*/\n    slot = NULL;\n    for (int w = 0; (w < CODEGEN_LINK_WAYS) && (slot == NULL); w++)\n        if ((from[w].block != NULL) && (from[w].exit_pc == cpu_state.pc) && (from[w].exit_cs == cs))\n            slot = &from[w];\n    for (int w = 0; (w < CODEGEN_LINK_WAYS) && (slot == NULL); w++)\n        if (from[w].entry == NULL)\n            slot = &from[w];\n    if (slot == NULL) {\n        slot         = &from[from->victim];\n        from->victim = (from->victim + 1) % CODEGEN_LINK_WAYS;\n    }\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_link_patches, k9x_patch_first, k9x_patch_same, k9x_patch_retarget;\n        k9x_link_patches++;\n        if (slot->block == NULL)\n            k9x_patch_first++;\n        else if ((slot->exit_pc == cpu_state.pc) && (slot->exit_cs == cs))\n            k9x_patch_same++;\n        else\n            k9x_patch_retarget++;\n    }\n#endif\n\n"),
    ('86box/src/codegen/codegen_block.c',
     '    slot->mem_exec   = &_mem_exec[phys >> MEM_GRANULARITY_BITS];\n    slot->hash       = &codeblock_hash[HASH(phys)];\n',
     '    slot->mem_exec   = &_mem_exec[phys >> MEM_GRANULARITY_BITS];\n    slot->map_gen    = mem_mapping_gen;\n    slot->hash       = &codeblock_hash[HASH(phys)];\n'),
    ('86box/src/codegen/codegen_block.c',
     '    slot->dirty_mask = block->dirty_mask;\n    slot->entry      = &block->data[BLOCK_START + CODEGEN_LINK_ENTRY_OFFSET];\n}\n',
     '    slot->dirty_mask = block->dirty_mask;\n    link_in_remove(slot);\n    link_in_insert(block, slot);\n    slot->entry = &block->data[BLOCK_START + CODEGEN_LINK_ENTRY_OFFSET];\n}\n'),
    ('86box/src/codegen/codegen_block.c',
     '            page->smc_strikes++;\n        if (page->smc_strikes >= SMC_THRASH_STRIKE_THRESHOLD)\n            page->smc_cooldown_until = tsc + ((uint64_t) SMC_THRASH_BASE_COOLDOWN << (page->smc_strikes - SMC_THRASH_STRIKE_THRESHOLD));\n',
     '            page->smc_strikes++;\n        if (page->smc_strikes >= SMC_THRASH_STRIKE_THRESHOLD) {\n            page->smc_cooldown_until = tsc + ((uint64_t) SMC_THRASH_BASE_COOLDOWN << (page->smc_strikes - SMC_THRASH_STRIKE_THRESHOLD));\n'),
    ('86box/src/codegen/codegen_block.c',
     '            page->smc_cooldown_until = tsc + ((uint64_t) SMC_THRASH_BASE_COOLDOWN << (page->smc_strikes - SMC_THRASH_STRIKE_THRESHOLD));\n    } else\n',
     '            page->smc_cooldown_until = tsc + ((uint64_t) SMC_THRASH_BASE_COOLDOWN << (page->smc_strikes - SMC_THRASH_STRIKE_THRESHOLD));\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n            link_page_blocks_changed(page);\n#endif\n        }\n    } else\n'),
    ('86box/src/codegen/codegen_block.c',
     '    block_num                 = HASH(phys_addr);\n    codeblock_hash[block_num] = block_current;\n',
     '    block_num                 = HASH(phys_addr);\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    /*Links to the block the hash held stop: the link routine counts on the\n      hash pointing at its target*/\n    if (codeblock_hash[block_num] != block_current)\n        codegen_link_block_changed(&codeblock[codeblock_hash[block_num]]);\n#endif\n    codeblock_hash[block_num] = block_current;\n'),
    ('86box/src/codegen/codegen_ir.c',
     '            if (uop->type & UOP_TYPE_ORDER_BARRIER)\n                codegen_reg_flush(ir, block);\n\n',
     '            if (uop->type & UOP_TYPE_ORDER_BARRIER)\n                codegen_reg_flush_ex(ir, block, uop_is_mem_access(uop->type));\n\n'),
    ('86box/src/codegen/codegen_ir_defs.h',
     '#define UOP_MEM_LOAD_REG_EA (UOP_TYPE_PARAMS_REGS | UOP_TYPE_PARAMS_IMM | 0x4e | UOP_TYPE_ORDER_BARRIER)\n\n',
     '#define UOP_MEM_LOAD_REG_EA (UOP_TYPE_PARAMS_REGS | UOP_TYPE_PARAMS_IMM | 0x4e | UOP_TYPE_ORDER_BARRIER)\n\n\n'),
    ('86box/src/codegen/codegen_ir_defs.h',
     '#define UOP_MASK    0xffff\n\n',
     '#define UOP_MASK    0xffff\n\n/*A guest memory access through the memory routines (the CMP_J* among them\n  are branches, not accesses)*/\nstatic inline int\nuop_is_mem_access(uint32_t type)\n{\n    switch (type & UOP_MASK) {\n        case UOP_MEM_LOAD_ABS & UOP_MASK:\n        case UOP_MEM_LOAD_REG & UOP_MASK:\n        case UOP_MEM_STORE_ABS & UOP_MASK:\n        case UOP_MEM_STORE_REG & UOP_MASK:\n        case UOP_MEM_STORE_IMM_8 & UOP_MASK:\n        case UOP_MEM_STORE_IMM_16 & UOP_MASK:\n        case UOP_MEM_STORE_IMM_32 & UOP_MASK:\n        case UOP_MEM_LOAD_SINGLE & UOP_MASK:\n        case UOP_MEM_LOAD_DOUBLE & UOP_MASK:\n        case UOP_MEM_STORE_SINGLE & UOP_MASK:\n        case UOP_MEM_STORE_DOUBLE & UOP_MASK:\n        case UOP_MEM_LOAD_REG_EA & UOP_MASK:\n            return 1;\n        default:\n            return 0;\n    }\n}\n\n'),
    ('86box/src/codegen/codegen_link.h',
     '\ntypedef struct codegen_link_slot_t {\n',
     '\n/*Everything a hit reads is in the first 64 bytes, one cache line (slots are\n  64-byte aligned); the rest is only read off the hit path.*/\ntypedef struct codegen_link_slot_t {\n'),
    ('86box/src/codegen/codegen_link.h',
     '    codeblock_t *block;       /*Target block*/\n    uint32_t     gen;         /*block->link_gen when the slot was filled*/\n    uint16_t     status;      /*cpu_cur_status after the FPU refresh*/\n',
     '    codeblock_t *block;       /*Target block*/\n    uint16_t     status;      /*cpu_cur_status after the FPU refresh*/\n'),
    ('86box/src/codegen/codegen_link.h',
     '    uint16_t     npxc;        /*cpu_state.npxc & 0x0f00*/\n    uint32_t     cr0_bits;    /*cr0 & 0xc0000000 (CD can only be clear here)*/\n',
     '    uint16_t     npxc;        /*cpu_state.npxc & 0x0f00*/\n    uint32_t     map_gen;     /*mem_mapping_gen: _mem_exec[] is as it was*/\n    uint32_t     cr0_bits;    /*cr0 & 0xc0000000 (CD can only be clear here)*/\n'),
    ('86box/src/codegen/codegen_link.h',
     '    uint32_t     cr0_bits;    /*cr0 & 0xc0000000 (CD can only be clear here)*/\n    uint32_t     virt;        /*exit_cs + exit_pc*/\n    uint32_t     phys_page;   /*get_phys(virt) & ~0xfff*/\n',
     '    uint32_t     cr0_bits;    /*cr0 & 0xc0000000 (CD can only be clear here)*/\n    uint32_t     phys_page;   /*get_phys(virt) & ~0xfff*/\n'),
    ('86box/src/codegen/codegen_link.h',
     '    uint32_t     phys_page;   /*get_phys(virt) & ~0xfff*/\n    uint32_t     rammask;     /*rammask, compared when paging is off*/\n    uintptr_t   *xlat;        /*&readlookup2[virt >> 12], compared when paging is on*/\n    uintptr_t    xlat_val;    /*readlookup2[virt >> 12], never (int)-1*/\n    uint8_t    **mem_exec;    /*&_mem_exec[phys >> MEM_GRANULARITY_BITS]*/\n    uint32_t    *hash;        /*&codeblock_hash[HASH(phys)]*/\n#if defined(__aarch64__) || defined(_M_ARM64)\n',
     '    uint32_t     phys_page;   /*get_phys(virt) & ~0xfff*/\n#if defined(__aarch64__) || defined(_M_ARM64)\n'),
    ('86box/src/codegen/codegen_link.h',
     '    uint64_t    *dirty_mask;  /*block->dirty_mask*/\n} codegen_link_slot_t;\n\n',
     '    uint64_t    *dirty_mask;  /*block->dirty_mask*/\n    /*Off the hit path*/\n    uint32_t     gen;         /*block->link_gen when the slot was filled*/\n    uint32_t     virt;        /*exit_cs + exit_pc*/\n    uint32_t     rammask;     /*rammask, compared when paging is off*/\n    uint16_t     in_nr;       /*the block whose list of linking slots it is on*/\n    uint8_t      in_listed;   /*on that list (codegen_block.c)*/\n    uint8_t      victim;      /*way 0 only: the way the next new target takes*/\n    uintptr_t   *xlat;        /*&readlookup2[virt >> 12], compared when paging is on*/\n    uintptr_t    xlat_val;    /*readlookup2[virt >> 12], never (int)-1*/\n    uint8_t    **mem_exec;    /*&_mem_exec[phys >> MEM_GRANULARITY_BITS]*/\n    uint32_t    *hash;        /*&codeblock_hash[HASH(phys)]*/\n    /*Neighbours on that list*/\n    struct codegen_link_slot_t *in_next;\n    struct codegen_link_slot_t *in_prev;\n} __attribute__((aligned(64))) codegen_link_slot_t;\n\n'),
    ('86box/src/codegen/codegen_link.h',
     'extern uint64_t tsc_old;\n\n',
     'extern uint64_t tsc_old;\n/*Slice state of exec386_dynarec(), which the link routine moves on itself*/\nextern int32_t cycles_main;\nextern int32_t cycles_start;\nextern int32_t cyc_period;\n/*Timers run by the link routine at the end of a block (see exec386_dynarec())*/\nextern int  k9x_post_done;\nextern void k9x_link_timer(uint64_t new_tsc);\n/*get_phys() run by the link routine for the next block (see exec386_dynarec_dyn())*/\nextern uint32_t k9x_link_phys(uint32_t virt);\n\n/*Several per exit: an exit passes its first, and when that holds another\n  target the routine tries the others, which follow it in memory. An exit\n  that goes to a few targets (a return to a few callers) links to each.*/\n#define CODEGEN_LINK_WAYS 4\n\n'),
    ('86box/src/codegen/codegen_link.h',
     '/*Indexed by the number of the block whose exit uses them.*/\nextern codegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS];\n\n',
     '/*Indexed by the number of the block whose exit uses them.*/\nextern codegen_link_slot_t codegen_link_slots[BLOCK_SIZE][CODEGEN_LINK_SLOTS][CODEGEN_LINK_WAYS];\n\n'),
    ('86box/src/codegen/codegen_reg.c',
     'void\ncodegen_reg_flush(UNUSED(ir_data_t *ir), codeblock_t *block)\n{\n',
     "void\ncodegen_reg_flush(ir_data_t *ir, codeblock_t *block)\n{\n    codegen_reg_flush_ex(ir, block, 0);\n}\n\n/*mem_access: before a guest memory access (UOP_MEM_*). Nothing that runs\n  there reads cpu_state.eaaddr (the memory routines, their C paths, an\n  abort's exception delivery; fpu_postamble() and the interpreted\n  instructions read it, behind full barriers), so it stays in its\n  register, still to be written back, unless the register is volatile.*/\nvoid\ncodegen_reg_flush_ex(UNUSED(ir_data_t *ir), codeblock_t *block, int mem_access)\n{\n"),
    ('86box/src/codegen/codegen_reg.c',
     "    reg_set = &host_reg_set;\n    for (c = 0; c < reg_set->nr_regs; c++) {\n        if (!ir_reg_is_invalid(reg_set->regs[c]) && reg_set->dirty[c]) {\n            codegen_reg_writeback(reg_set, block, c, 0);\n        }\n        /*The C code behind an ordered access (a memory access's slow path,\n",
     "    reg_set = &host_reg_set;\n    for (c = 0; c < reg_set->nr_regs; c++) {\n        if (!ir_reg_is_invalid(reg_set->regs[c]) && reg_set->dirty[c]) {\n            if (mem_access && (IREG_GET_REG(reg_set->regs[c].reg) == IREG_eaaddr) &&\n                !(reg_set->reg_list[c].flags & HOST_REG_FLAG_VOLATILE))\n                continue;\n            codegen_reg_writeback(reg_set, block, c, 0);\n        }\n        /*The C code behind an ordered access (a memory access's slow path,\n"),
    ('86box/src/codegen/codegen_reg.h',
     'void codegen_reg_flush(struct ir_data_t *ir, codeblock_t *block);\n/*Write back and evict all registers*/\n',
     'void codegen_reg_flush(struct ir_data_t *ir, codeblock_t *block);\nvoid codegen_reg_flush_ex(struct ir_data_t *ir, codeblock_t *block, int mem_access);\n/*Write back and evict all registers*/\n'),
    ('86box/src/cpu/386_common.c',
     '#include <86box/plat_unused.h>\n\n',
     '#include <86box/plat_unused.h>\n#include <86box/k9x_hot.h>\n\n'),
    ('86box/src/cpu/386_common.c',
     'int cpu_debug_regs_486 = 0;\nint cpu_dr_armed       = 0;\n\n',
     'int cpu_debug_regs_486 = 0;\n\n/* What the block link routine finds 0 before it lets one block follow\n   another without the dispatch loop, side by side so it loads them in pairs\n   (build_link_routine()). */\nK9X_HOT __attribute__((aligned(8))) int x86_was_reset = 0;\nK9X_HOT int cpu_flush_pending     = 0;\nK9X_HOT int cpu_init              = 0;\nK9X_HOT int new_ne                = 0;\nK9X_HOT int cpu_force_interpreter = 0;\nK9X_HOT int cpu_override_dynarec  = 0;\nK9X_HOT int cpu_dr_armed          = 0;\n\n'),
    ('86box/src/cpu/386_common.c',
     '\nint      cpu_init = 0;\n\nuint32_t *eal_r;\n',
     '\nuint32_t *eal_r;\n'),
    ('86box/src/cpu/386_common.c',
     '\nint nmi_enable = 1;\n\n',
     '\nK9X_HOT int nmi_enable = 1;\n\n'),
    ('86box/src/cpu/386_common.c',
     '\nuint16_t cpu_cur_status = 0;\n\n',
     '\nK9X_HOT uint16_t cpu_cur_status = 0;\n\n'),
    ('86box/src/cpu/386_common.c',
     '\nint      new_ne            = 0;\nint      in_sys            = 0;\n',
     '\nint      in_sys            = 0;\n'),
    ('86box/src/cpu/386_common.c',
     'int smi_block   = 0;\nint cpu_halted  = 0;\n\n',
     'int smi_block   = 0;\nK9X_HOT int cpu_halted  = 0;\n\n'),
    ('86box/src/cpu/386_common.c',
     'int tempc;\nint oldcpl;\nint optype;\n',
     'int tempc;\nK9X_HOT int oldcpl;\nint optype;\n'),
    ('86box/src/cpu/386_common.c',
     '\nuint16_t oldcs;\n\n',
     '\nK9X_HOT uint16_t oldcs;\n\n'),
    ('86box/src/cpu/386_dynarec.c',
     '#include <86box/gdbstub.h>\n#ifdef USE_DYNAREC\n',
     '#include <86box/gdbstub.h>\n#include <86box/k9x_hot.h>\n#ifdef USE_DYNAREC\n'),
    ('86box/src/cpu/386_dynarec.c',
     '\nint cpu_force_interpreter   = 0;\nint cpu_override_dynarec    = 0;\nint inrecomp                = 0;\n',
     '\n#ifdef K9X_DIAG\nuint64_t k9x_c_dispatch;   /* compiled blocks entered from the C loop */\nuint64_t k9x_c_interp;     /* blocks interpreted by the C loop */\nuint64_t k9x_link_patches; /* link slots filled */\nuint64_t k9x_patch_first, k9x_patch_same, k9x_patch_retarget;\nuint64_t k9x_c_dispatch_nofrom; /* compiled blocks entered from the C loop not after a block exit */\n/* Link misses: target, gen, tsc moved, slice used up, timer due, irq, status, other */\nuint64_t k9x_miss[8];\nuint64_t k9x_miss2[12];\nuint64_t k9x_lines_skip, k9x_lines_vram, k9x_lines_full;\nuint64_t k9x_lines_fast, k9x_lines_slow, k9x_slow_why[8];\nuint64_t k9x_cmem[24];\nvoid    *k9x_timer_cb[32];\nuint64_t k9x_timer_n[32];\n#endif\nint inrecomp                = 0;\n'),
    ('86box/src/cpu/386_dynarec.c',
     '#ifdef USE_DYNAREC\nint32_t         cycles_main = 0;\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n',
     "#ifdef USE_DYNAREC\nK9X_HOT int32_t cycles_main  = 0;\n/* Set by the block link routine when it missed after doing part of this\n   loop's work itself, so the loop does not do it again: 1 = it ran the\n   timers due after a block (go on to the next block), 2 = it also did the\n   loop-top work and called get_phys() for the next block (go straight back\n   into exec386_dynarec_dyn()). */\nK9X_HOT int k9x_post_done = 0;\n\n/* Called by the block link routine with the TSC at the end of a block, when a\n   timer is due: what the loop below does at the end of that block. */\nvoid\nk9x_link_timer(uint64_t new_tsc)\n{\n    tsc = new_tsc;\n    timer_process();\n}\n\n/* Called by the block link routine with the next block's linear address, as\n   exec386_dynarec_dyn() calls get_phys() first thing: its page, or 1 (never a\n   page) if the translation faulted. */\nuint32_t\nk9x_link_phys(uint32_t virt)\n{\n    const uint32_t phys = get_phys(virt);\n\n    return cpu_state.abrt ? 1 : (phys & ~0xfff);\n}\nK9X_HOT int32_t cycles_start = 0; /* cycles at the start of the current slice */\nK9X_HOT int32_t cyc_period   = 0; /* cycles per slice */\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n"),
    ('86box/src/cpu/386_dynarec.c',
     '/* The block link routine does the loop-top stores itself. */\nint32_t  cycles_old = 0;\nuint64_t tsc_old    = 0;\n#    else\n',
     '/* The block link routine does the loop-top stores itself. */\nK9X_HOT int32_t  cycles_old = 0;\nK9X_HOT uint64_t tsc_old    = 0;\n#    else\n'),
    ('86box/src/cpu/386_dynarec.c',
     'exec386_dynarec_int(void)\n{\n    if (UNLIKELY(cpu_debug_regs_486))\n        exec386_dynarec_int_dbg();\n',
     'exec386_dynarec_int(void)\n{\n#ifdef K9X_DIAG\n    k9x_c_interp++;\n#endif\n    if (UNLIKELY(cpu_debug_regs_486))\n        exec386_dynarec_int_dbg();\n'),
    ('86box/src/cpu/386_dynarec.c',
     '                    if (valid_block) {\n                        block = new_block;\n',
     '                    if (valid_block) {\n#        ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n                        /* Links to the block the hash held stop: the link\n                           routine counts on the hash pointing at its target. */\n                        if (block != new_block)\n                            codegen_link_block_changed(block);\n#        endif\n                        block = new_block;\n'),
    ('86box/src/cpu/386_dynarec.c',
     '        block->reused = 1; /* reached via block->data: compiling it paid off */\n        inrecomp = 1;\n',
     '        block->reused = 1; /* reached via block->data: compiling it paid off */\n#    ifdef K9X_DIAG\n        k9x_c_dispatch++;\n        if (from == NULL)\n            k9x_c_dispatch_nofrom++;\n#    endif\n        inrecomp = 1;\n'),
    ('86box/src/cpu/386_dynarec.c',
     '            code();\n#    else\n',
     "            code();\n#        ifdef K9X_DIAG\n        /* Why the exit's link was not taken, as far as it can be told now. */\n        if (link_from != NULL) {\n            codegen_link_slot_t *s = link_from;\n            if ((s->entry == NULL) || (s->exit_pc != cpu_state.pc) || (s->exit_cs != cs))\n                k9x_miss[0]++;\n            else if (s->gen != s->block->link_gen)\n                k9x_miss[1]++;\n            else if (tsc != tsc_old)\n                k9x_miss[2]++;\n            else if (cycles <= 0)\n                k9x_miss[3]++;\n            else if ((int64_t) (timer_target - (tsc + (uint64_t) (cycles_old - cycles))) <= 0)\n                k9x_miss[4]++;\n            else if ((cpu_state.flags & I_FLAG) && pic.int_pending)\n                k9x_miss[5]++;\n            else if ((s->status & ~(CPU_STATUS_NOTFLATES | CPU_STATUS_FPU_PC24 | CPU_STATUS_FPU_RC_NZ)) !=\n                     (cpu_cur_status & ~(CPU_STATUS_NOTFLATES | CPU_STATUS_FPU_PC24 | CPU_STATUS_FPU_RC_NZ)))\n                k9x_miss[6]++;\n            else {\n                /* The routine's remaining checks, in its order */\n                const uint32_t virt = cs + cpu_state.pc;\n                k9x_miss[7]++;\n                if ((cpu_state.flags & T_FLAG) || (cpu_state.abrt & 0xffff0000) || x86_was_reset || cpu_flush_pending ||\n                    cpu_init || new_ne || cpu_force_interpreter || cpu_override_dynarec || cpu_dr_armed || nmi)\n                    k9x_miss2[0]++;\n                else if ((s->status ^ cpu_cur_status) & ~(CPU_STATUS_FPU_PC24 | CPU_STATUS_FPU_RC_NZ))\n                    k9x_miss2[1]++;\n                else if (s->npxc != (cpu_state.npxc & 0x0f00))\n                    k9x_miss2[2]++;\n                else if (s->cr0_bits != (cr0 & 0xc0000000))\n                    k9x_miss2[3]++;\n                else if (((get_phys_virt ^ virt) & 0xfffff000) ? ((cr0 >> 31) ? (*s->xlat != s->xlat_val) : (s->rammask != rammask))\n                                                                 : (get_phys_phys != s->phys_page))\n                    k9x_miss2[4]++;\n                else if (*s->mem_exec == NULL)\n                    k9x_miss2[5]++;\n                else if ((uint16_t) *s->hash != s->block_nr)\n                    k9x_miss2[6]++;\n                else if (*s->dirty_mask & s->page_mask)\n                    k9x_miss2[7]++;\n                else if ((cpu_state.TOP & s->top_mask) != s->top)\n                    k9x_miss2[8]++;\n                else if (s->two_page)\n                    k9x_miss2[9]++;\n                else\n                    k9x_miss2[10]++;\n            }\n        }\n#        endif\n#    else\n"),
    ('86box/src/cpu/386_dynarec.c',
     '\n    int32_t cyc_period = cycs / (force_10ms ? 2000 : 200); /*5us*/\n\n',
     '\n    /* 5 us slices. The block link routine crosses a slice boundary itself\n       when nothing else needs this loop, with this same arithmetic, so the\n       slice state is global. */\n    cyc_period = cycs / (force_10ms ? 2000 : 200);\n\n'),
    ('86box/src/cpu/386_dynarec.c',
     '    while (cycles_main > 0) {\n        int32_t cycles_start;\n\n        cycles += cyc_period;\n',
     '    while (cycles_main > 0) {\n        cycles += cyc_period;\n'),
    ('86box/src/cpu/386_dynarec.c',
     '            } else {\n                exec386_dynarec_dyn();\n',
     '            } else {\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\nk9x_dyn_again:\n#    endif\n                exec386_dynarec_dyn();\n'),
    ('86box/src/cpu/386_dynarec.c',
     '                    cpu_flush_pending++;\n            }\n',
     '                    cpu_flush_pending++;\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n                /* The link routine already did everything below for the last\n                   block, its timers included, before it missed: go straight on\n                   to the next block, as this loop would have. */\n                if (k9x_post_done) {\n                    const int resume = k9x_post_done;\n\n                    k9x_post_done = 0;\n                    if (resume == 2)\n                        goto k9x_dyn_again;\n                    goto post_block_done;\n                }\n#    endif\n            }\n'),
    ('86box/src/cpu/386_dynarec.c',
     '            }\n\n            cycdiff = oldcyc - cycles;\n            delta   = tsc - oldtsc;\n',
     '            }\n\n#    ifdef K9X_TRACE\n            {\n                static uint64_t lo, hi;\n                if (!hi) {\n                    const char *e;\n                    lo = (e = getenv("K9X_TRACE_LO")) ? strtoull(e, NULL, 0) : 0;\n                    hi = (e = getenv("K9X_TRACE_HI")) ? strtoull(e, NULL, 0) : 1;\n                }\n                if ((tsc >= lo) && (tsc < hi))\n                    fprintf(stderr, "[trace] loop tsc=%llu cyc=%d cyc_old=%d cs=%04x pc=%08x eax=%08x start=%d main=%d\\n",\n                            (unsigned long long) tsc, cycles, cycles_old, CS, cpu_state.pc, EAX, cycles_start, cycles_main);\n            }\n#    endif\n            cycdiff = oldcyc - cycles;\n            delta   = tsc - oldtsc;\n'),
    ('86box/src/cpu/386_dynarec.c',
     '\n#    ifdef USE_GDBSTUB\n',
     '\n#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\npost_block_done:\n#    endif\n#    ifdef USE_GDBSTUB\n'),
    ('86box/src/cpu/386_dynarec.c',
     '#    endif\n        }\n',
     '#    endif\n            ;\n        }\n'),
    ('86box/src/cpu/cpu.c',
     '#include <86box/plat_unused.h>\n\n',
     '#include <86box/plat_unused.h>\n#include <86box/k9x_hot.h>\n\n'),
    ('86box/src/cpu/cpu.c',
     'int cpu_cache_ext_enabled;\nint cpu_flush_pending;\nint cpu_old_paging;\n',
     'int cpu_cache_ext_enabled;\nint cpu_old_paging;\n'),
    ('86box/src/cpu/cpu.c',
     '\nuint64_t tsc = 0;\n\n',
     '\nK9X_HOT uint64_t tsc = 0;\n\n'),
    ('86box/src/cpu/cpu_lapic.c',
     '#include <86box/video.h> /* cpuclock */\n#include "../lapic_policy.h"\n',
     '#include <86box/video.h> /* cpuclock */\n#include <86box/k9x_hot.h>\n#include "../lapic_policy.h"\n'),
    ('86box/src/cpu/cpu_lapic.c',
     '   cpu_lapic_irr_live_sync(). */\nuint32_t                     cpu_lapic_irr_live;\nuint8_t                      cpu_lapic_extint_live[IOAPIC_STATE_MAX_LAPICS];\nstatic uint32_t              cpu_lapic_isrs[IOAPIC_STATE_MAX_LAPICS][IOAPIC_STATE_LAPIC_BIT_WORDS];\n',
     '   cpu_lapic_irr_live_sync(). */\nK9X_HOT uint32_t                     cpu_lapic_irr_live;\nK9X_HOT uint8_t                      cpu_lapic_extint_live[IOAPIC_STATE_MAX_LAPICS];\nstatic uint32_t              cpu_lapic_isrs[IOAPIC_STATE_MAX_LAPICS][IOAPIC_STATE_LAPIC_BIT_WORDS];\n'),
    ('86box/src/cpu/x86.c',
     '#include <86box/vid_svga.h>\n\n',
     '#include <86box/vid_svga.h>\n#include <86box/k9x_hot.h>\n\n'),
    ('86box/src/cpu/x86.c',
     '/* Variables for handling the non-maskable interrupts. */\nint nmi            = 0;\nint nmi_auto_clear = 0;\n',
     '/* Variables for handling the non-maskable interrupts. */\nK9X_HOT int nmi            = 0;\nint nmi_auto_clear = 0;\n'),
    ('86box/src/cpu/x86.c',
     '\n/* Was the CPU ever reset? */\nint x86_was_reset  = 0;\nint soft_reset_pci = 0;\n',
     '\n/* Was the CPU ever reset? x86_was_reset is in 386_common.c. */\nint soft_reset_pci = 0;\n'),
]

KAIRO9X_MACHINE = [
    ('86box/src/automation.c',
     'static uint64_t  frame_count;\n\n',
     'static uint64_t  frame_count;\nstatic int       frame_x;\nstatic int       frame_y;\nstatic int       frame_pending; /* frame_x/y/w/h describe a frame not yet copied */\n\n/* Copy the latest frame from the target buffer into frame_buf. Called with\n   frame_mutex held, on the emulation thread. */\nstatic void\nframe_take(void)\n{\n    const bitmap_t *target = monitors[0].target_buffer;\n\n    if (!frame_pending || !target)\n        return;\n    if ((frame_w * frame_h) > frame_alloc) {\n        frame_alloc = frame_w * frame_h;\n        frame_buf   = realloc(frame_buf, frame_alloc * sizeof(uint32_t));\n    }\n    for (int row = 0; row < frame_h; row++)\n        memcpy(&frame_buf[row * frame_w], &target->line[frame_y + row][frame_x], frame_w * sizeof(uint32_t));\n    frame_pending = 0;\n}\n\n'),
    ('86box/src/automation.c',
     '    thread_wait_mutex(frame_mutex);\n    if ((w * h) > frame_alloc) {\n        frame_alloc = w * h;\n        frame_buf   = realloc(frame_buf, frame_alloc * sizeof(uint32_t));\n    }\n    for (int row = 0; row < h; row++)\n        memcpy(&frame_buf[row * w], &target->line[y + row][x], w * sizeof(uint32_t));\n    frame_w = w;\n',
     '    thread_wait_mutex(frame_mutex);\n    frame_x = x;\n    frame_y = y;\n    frame_w = w;\n'),
    ('86box/src/automation.c',
     '    frame_count++;\n    record_frame();\n    thread_release_mutex(frame_mutex);\n',
     '    frame_count++;\n    /* Copy the frame only when something will look at it: a recording\n       takes every frame, a screenshot takes the latest one when asked\n       (frame_take()). The emulation thread does not pay for a copy nobody\n       reads; a real frontend copies on its own display thread. */\n    frame_pending = 1;\n    if (rec_interval) {\n        frame_take();\n        record_frame();\n    }\n    thread_release_mutex(frame_mutex);\n'),
    ('86box/src/automation.c',
     '        thread_wait_mutex(frame_mutex);\n        ok       = (argc >= 2) ? write_png(rest[1]) : encode_png(&png_out);\n',
     '        thread_wait_mutex(frame_mutex);\n        frame_take();\n        ok       = (argc >= 2) ? write_png(rest[1]) : encode_png(&png_out);\n'),
    ('86box/src/automation.c',
     '            thread_wait_mutex(frame_mutex);\n            rec_interval = 0;\n',
     '            thread_wait_mutex(frame_mutex);\n        frame_take();\n            rec_interval = 0;\n'),
    ('86box/src/automation.c',
     '            thread_wait_mutex(frame_mutex);\n            snprintf(rec_dir, sizeof(rec_dir), "%s", (argc >= 4) ? rest[3] : "");\n',
     '            thread_wait_mutex(frame_mutex);\n        frame_take();\n            snprintf(rec_dir, sizeof(rec_dir), "%s", (argc >= 4) ? rest[3] : "");\n'),
    ('86box/src/automation.c',
     '            thread_wait_mutex(frame_mutex);\n            if (n > rec_q_len)\n',
     '            thread_wait_mutex(frame_mutex);\n        frame_take();\n            if (n > rec_q_len)\n'),
    ('86box/src/automation.c',
     '            respond_error("usage: record start <interval_ms> [<dir>] | record stop | record pull [<max_frames>]");\n    } else if (!strcmp(argv[0], "info")) {\n',
     '            respond_error("usage: record start <interval_ms> [<dir>] | record stop | record pull [<max_frames>]");\n    } else if (!strcmp(argv[0], "ramhash")) {\n        /* ramhash [chunk]: FNV-1a over all of guest RAM, for comparing runs;\n           with a chunk size, also a hash per chunk, listing the chunks\n           whose hash differs from "empty" is left to the client. */\n        const uint64_t len   = (uint64_t) mem_size << 10;\n        const uint64_t chunk = (argc >= 2) ? strtoull(argv[1], NULL, 0) : 0;\n        uint64_t       h     = 0xcbf29ce484222325ULL;\n        for (uint64_t i = 0; i < len; i++)\n            h = (h ^ ram[i]) * 0x100000001b3ULL;\n        resp.len = 0;\n        sb_printf(&resp, "{\\"ok\\":true,\\"ramhash\\":\\"%016llx\\",\\"bytes\\":%llu", (unsigned long long) h, (unsigned long long) len);\n        if (chunk) {\n            sb_printf(&resp, ",\\"chunks\\":[");\n            for (uint64_t c = 0; c < len; c += chunk) {\n                uint64_t ch = 0xcbf29ce484222325ULL;\n                for (uint64_t i = c; (i < c + chunk) && (i < len); i++)\n                    ch = (ch ^ ram[i]) * 0x100000001b3ULL;\n                sb_printf(&resp, "%s\\"%016llx\\"", c ? "," : "", (unsigned long long) ch);\n            }\n            sb_printf(&resp, "]");\n        }\n        sb_printf(&resp, "}");\n    } else if (!strcmp(argv[0], "info")) {\n'),
    ('86box/src/chipset/wd76c10.c',
     '            _mem_exec[i >> 12] = exec;\n\n',
     '            _mem_exec[i >> 12] = exec;\n    /* _mem_exec[] changed outside mem_mapping_recalc() */\n    mem_mapping_gen++;\n\n'),
    ('86box/src/disk/hdc_ide.c',
     '    if ((state->thread == NULL) || state->pending || (count == 0))\n        return;\n\n    state->sector  = sector;\n',
     '    if ((state->thread == NULL) || state->pending || (count == 0))\n        return;\n#ifdef K9X_NO_IDE_ASYNC\n    return;\n#endif\n\n    state->sector  = sector;\n'),
    ('86box/src/ioapic.c',
     '#include <86box/plat_unused.h>\n#include "cpu.h"\n',
     '#include <86box/plat_unused.h>\n#include <86box/k9x_hot.h>\n#include "cpu.h"\n'),
    ('86box/src/ioapic.c',
     '   the 8259 exactly as they did before any APIC existed. */\nuint8_t ioapic_irq_path_active = 0;\n\n',
     '   the 8259 exactly as they did before any APIC existed. */\nK9X_HOT uint8_t ioapic_irq_path_active = 0;\n\n'),
    ('86box/src/mem/mem.c',
     '#include <86box/gdbstub.h>\n#ifdef USE_DYNAREC\n',
     '#include <86box/gdbstub.h>\n#include <86box/k9x_hot.h>\n#ifdef USE_DYNAREC\n'),
    ('86box/src/mem/mem.c',
     '\nuint8_t *ram;  /* the virtual RAM */\nuint8_t  page_ff[4096];\n',
     '\nK9X_HOT uint8_t *ram;  /* the virtual RAM */\nuint8_t  page_ff[4096];\n'),
    ('86box/src/mem/mem.c',
     'uint8_t  page_ff[4096];\nuint32_t rammask;\n\n',
     'uint8_t  page_ff[4096];\nK9X_HOT uint32_t rammask;\n\n'),
    ('86box/src/mem/mem.c',
     'uint8_t *pccache2;\nint      cpu_fetch_device;\n\n',
     'uint8_t *pccache2;\nK9X_HOT int      cpu_fetch_device;\n\n'),
    ('86box/src/mem/mem.c',
     '\nuint32_t get_phys_virt;\nuint32_t get_phys_phys;\n\n',
     '\nK9X_HOT uint32_t get_phys_virt;\nK9X_HOT uint32_t get_phys_phys;\n\n'),
    ('86box/src/mem/mem.c',
     '   while it is unchanged. */\nuint32_t mem_mapping_gen;\n\n',
     '   while it is unchanged. */\nK9X_HOT uint32_t mem_mapping_gen;\n\n'),
    ('86box/src/mem/mem.c',
     '}\n\nuint64_t\nmmutranslatereal(uint32_t addr, int rw)\n',
     '}\n\n#ifdef K9X_DIAG\nuint64_t k9x_cnt_walk; /* page-table walks, for the cost model */\n#endif\nuint64_t\nmmutranslatereal(uint32_t addr, int rw)\n'),
    ('86box/src/mem/mem.c',
     'mmutranslatereal(uint32_t addr, int rw)\n{\n    /* Fast path to return invalid without any call if an exception has occurred beforehand. */\n    if (cpu_state.abrt)\n',
     'mmutranslatereal(uint32_t addr, int rw)\n{\n#ifdef K9X_DIAG\n    k9x_cnt_walk++;\n#endif\n    /* Fast path to return invalid without any call if an exception has occurred beforehand. */\n    if (cpu_state.abrt)\n'),
    ('86box/src/mem/mem.c',
     'writemembl(uint32_t addr, uint8_t val)\n{\n    mem_mapping_t *map;\n    uint64_t       a;\n',
     'writemembl(uint32_t addr, uint8_t val)\n{\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_cmem[24];\n        if (0)\n            k9x_cmem[16]++;\n        else if (page_lookup[addr >> 12] != NULL)\n            k9x_cmem[17]++;\n        else if (writelookup2[addr >> 12] == (uintptr_t) LOOKUP_INV)\n            k9x_cmem[18]++;\n        else\n            k9x_cmem[19]++;\n    }\n#endif\n    mem_mapping_t *map;\n    uint64_t       a;\n'),
    ('86box/src/mem/mem.c',
     'readmemwl(uint32_t addr)\n{\n    mem_mapping_t *map;\n    uint64_t       a;\n',
     'readmemwl(uint32_t addr)\n{\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_cmem[24];\n        if (addr & 1)\n            k9x_cmem[4]++;\n        else if (readlookup2[addr >> 12] == (uintptr_t) LOOKUP_INV)\n            k9x_cmem[5]++;\n        else\n            k9x_cmem[6]++;\n    }\n#endif\n    mem_mapping_t *map;\n    uint64_t       a;\n'),
    ('86box/src/mem/mem.c',
     'writememwl(uint32_t addr, uint16_t val)\n{\n    mem_mapping_t *map;\n    uint64_t       a;\n',
     'writememwl(uint32_t addr, uint16_t val)\n{\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_cmem[24];\n        if ((addr & 1))\n            k9x_cmem[12]++;\n        else if (page_lookup[addr >> 12] != NULL)\n            k9x_cmem[13]++;\n        else if (writelookup2[addr >> 12] == (uintptr_t) LOOKUP_INV)\n            k9x_cmem[14]++;\n        else\n            k9x_cmem[15]++;\n    }\n#endif\n    mem_mapping_t *map;\n    uint64_t       a;\n'),
    ('86box/src/mem/mem.c',
     'readmemll(uint32_t addr)\n{\n    mem_mapping_t *map;\n    int            i;\n',
     'readmemll(uint32_t addr)\n{\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_cmem[24];\n        if (addr & 3)\n            k9x_cmem[0]++;\n        else if (readlookup2[addr >> 12] == (uintptr_t) LOOKUP_INV)\n            k9x_cmem[1]++;\n        else\n            k9x_cmem[2]++;\n    }\n#endif\n    mem_mapping_t *map;\n    int            i;\n'),
    ('86box/src/mem/mem.c',
     'writememll(uint32_t addr, uint32_t val)\n{\n    mem_mapping_t *map;\n    int            i;\n',
     'writememll(uint32_t addr, uint32_t val)\n{\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_cmem[24];\n        if ((addr & 3))\n            k9x_cmem[8]++;\n        else if (page_lookup[addr >> 12] != NULL)\n            k9x_cmem[9]++;\n        else if (writelookup2[addr >> 12] == (uintptr_t) LOOKUP_INV)\n            k9x_cmem[10]++;\n        else\n            k9x_cmem[11]++;\n    }\n#endif\n    mem_mapping_t *map;\n    int            i;\n'),
    ('86box/src/nmi.c',
     '#include <86box/plat_unused.h>\n\n',
     '#include <86box/plat_unused.h>\n#include <86box/k9x_hot.h>\n\n'),
    ('86box/src/nmi.c',
     '\nint nmi_mask;\nvoid (*nmi_mask_changed)(void) = NULL;\n',
     '\nK9X_HOT int nmi_mask;\nvoid (*nmi_mask_changed)(void) = NULL;\n'),
    ('86box/src/pic.c',
     '#include <86box/plat_unused.h>\n#ifdef USE_VFIO\n',
     '#include <86box/plat_unused.h>\n#include <86box/k9x_hot.h>\n#ifdef USE_VFIO\n'),
    ('86box/src/pic.c',
     '\npic_t pic;\npic_t pic2;\n',
     '\nK9X_HOT pic_t pic;\npic_t pic2;\n'),
    ('86box/src/timer.c',
     '#include <86box/nv/vid_nv_rivatimer.h>\n\n',
     '#include <86box/nv/vid_nv_rivatimer.h>\n#include <86box/k9x_hot.h>\n\n'),
    ('86box/src/timer.c',
     'uint64_t TIMER_USEC;\nuint64_t timer_target;\n\n',
     'uint64_t TIMER_USEC;\nK9X_HOT uint64_t timer_target;\n\n'),
    ('86box/src/timer.c',
     'pc_timer_t *timer_head = NULL;\n\n',
     'pc_timer_t *timer_head = NULL;\n/* The last timer in the list, so one due after every other is added\n   without walking it. */\nstatic pc_timer_t *timer_tail = NULL;\n\n'),
    ('86box/src/timer.c',
     '    if (!timer_head) {\n        timer_head = timer;\n        timer->next = timer->prev = NULL;\n',
     '    if (!timer_head) {\n        timer_head = timer_tail = timer;\n        timer->next = timer->prev = NULL;\n'),
    ('86box/src/timer.c',
     '\n    timer_node = timer_head;\n',
     '\n    /* Due after the last one: the walk below would end there too. */\n    if (!TIMER_LESS_THAN(timer, timer_tail)) {\n        timer_tail->next = timer;\n        timer->prev      = timer_tail;\n        timer_tail       = timer;\n        return;\n    }\n\n    timer_node = timer_head;\n'),
    ('86box/src/timer.c',
     '            timer->prev = timer_node;\n            return;\n',
     '            timer->prev = timer_node;\n            timer_tail  = timer;\n            return;\n'),
    ('86box/src/timer.c',
     '        timer->next->prev = timer->prev;\n    timer->prev = timer->next = NULL;\n',
     '        timer->next->prev = timer->prev;\n    else\n        timer_tail = timer->prev;\n    timer->prev = timer->next = NULL;\n'),
    ('86box/src/timer.c',
     '        timer_head = timer->next;\n        timer_head->prev = NULL;\n        timer->next = timer->prev = NULL;\n',
     '        timer_head = timer->next;\n        if (timer_head == NULL)\n            timer_tail = NULL;\n        else\n            timer_head->prev = NULL;\n        timer->next = timer->prev = NULL;\n'),
    ('86box/src/timer.c',
     '            break;\n\n',
     '            break;\n#ifdef K9X_TRACE\n        {\n            static uint64_t lo, hi;\n            if (!hi) {\n                const char *e;\n                lo = (e = getenv("K9X_TRACE_LO")) ? strtoull(e, NULL, 0) : 0;\n                hi = (e = getenv("K9X_TRACE_HI")) ? strtoull(e, NULL, 0) : 1;\n            }\n            if ((tsc >= lo) && (tsc < hi))\n                fprintf(stderr, "[trace] timer tsc=%llu ts=%llu cb=%p\\n", (unsigned long long) tsc,\n                        (unsigned long long) timer->ts_integer, (void *) timer->callback);\n        }\n#endif\n\n'),
    ('86box/src/timer.c',
     '            timer->in_callback = 1;\n            timer->callback(timer->priv);\n',
     '            timer->in_callback = 1;\n#ifdef K9X_DIAG\n            {\n                /* Count callbacks per function, for finding the busy timers. */\n                extern void *k9x_timer_cb[32];\n                extern uint64_t k9x_timer_n[32];\n                int i;\n                for (i = 0; (i < 32) && k9x_timer_cb[i] && (k9x_timer_cb[i] != (void *) timer->callback); i++)\n                    ;\n                if (i < 32) {\n                    k9x_timer_cb[i] = (void *) timer->callback;\n                    k9x_timer_n[i]++;\n                }\n            }\n#endif\n            timer->callback(timer->priv);\n'),
    ('86box/src/timer.c',
     '    timer_head   = NULL;\n    timer_target = 0;\n',
     '    timer_head   = NULL;\n    timer_tail   = NULL;\n    timer_target = 0;\n'),
]

KAIRO9X_VIDEO = [
    ('86box/src/include/86box/vid_svga.h',
     '\n    void (*write)(uint32_t addr, uint8_t val, void *priv);\n',
     '\n    /* Called before each line is rendered, so a card whose accelerator runs\n       on another thread can finish the work queued so far. */\n    void (*render_sync)(struct svga_t *svga);\n\n    void (*write)(uint32_t addr, uint8_t val, void *priv);\n'),
    ('86box/src/include/86box/vid_svga.h',
     '    uint8_t dpms;\n    uint8_t color_2bpp;\n',
     '    uint8_t dpms;\n    /* The line may be drawn on the drawing thread (vid_svga_render.c) */\n    uint8_t render_async;\n    uint8_t color_2bpp;\n'),
    ('86box/src/include/86box/vid_svga_render.h',
     'extern void svga_render_null(svga_t *svga);\nextern void svga_render_blank(svga_t *svga);\n',
     'extern void svga_render_null(svga_t *svga);\n/* Wait until every queued line is drawn (vid_svga_render.c) */\nextern void svga_render_drain(void);\nextern void svga_render_blank(svga_t *svga);\n'),
    ('86box/src/video/vid_s3.c',
     '\n    uint8_t subsys_cntl, subsys_stat;\n',
     '\n    /* The FIFO thread does the work; everything the guest can see of it is\n       decided on the emulation thread, at emulated times. fifo_emp_pending:\n       commands were queued since INT_FIFO_EMP was last raised. */\n    uint8_t    fifo_emp_pending;\n    pc_timer_t fifo_emp_timer;\n\n    uint8_t subsys_cntl, subsys_stat;\n'),
    ('86box/src/video/vid_s3.c',
     '\n    if (FIFO_ENTRIES > 0xe000 || FIFO_ENTRIES < 8)\n',
     '\n    /* INT_FIFO_EMP is raised on the emulation thread, a fixed emulated time\n       after the queue last went from idle to busy (s3_fifo_emp_timer). */\n    s3->fifo_emp_pending = 1;\n    if (!timer_is_enabled(&s3->fifo_emp_timer))\n        timer_set_delay_u64(&s3->fifo_emp_timer, 20 * TIMER_USEC);\n\n    if (FIFO_ENTRIES > 0xe000 || FIFO_ENTRIES < 8)\n'),
    ('86box/src/video/vid_s3.c',
     '        pci_clear_irq(s3->pci_slot, PCI_INTA, &s3->irq_state);\n}\n',
     "        pci_clear_irq(s3->pci_slot, PCI_INTA, &s3->irq_state);\n}\n\n/* Bring the accelerator up to date before the guest observes it: finish\n   everything queued, then raise INT_FIFO_EMP if work was queued since it was\n   last raised. The guest then sees the same state on every run, whatever the\n   FIFO thread's host scheduling. Called only on the emulation thread. */\nstatic void\ns3_fifo_sync(s3_t *s3)\n{\n    if (!FIFO_EMPTY)\n        s3_wait_fifo_idle(s3);\n\n    if (s3->fifo_emp_pending) {\n        s3->fifo_emp_pending = 0;\n        s3->subsys_stat |= INT_FIFO_EMP;\n        s3_update_irqs(s3);\n    }\n}\n\n/* Linear framebuffer: as the banked window, after the queued blits. */\n#define S3_LFB_SYNC(s3)            \\\n    if (!FIFO_EMPTY)               \\\n        s3_wait_fifo_idle(s3)\n\nstatic uint8_t\ns3_lfb_read(uint32_t addr, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    return svga_read_linear(addr, &s3->svga);\n}\n\nstatic uint16_t\ns3_lfb_readw(uint32_t addr, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    return svga_readw_linear(addr, &s3->svga);\n}\n\nstatic uint32_t\ns3_lfb_readl(uint32_t addr, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    return svga_readl_linear(addr, &s3->svga);\n}\n\nstatic void\ns3_lfb_write(uint32_t addr, uint8_t val, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    svga_write_linear(addr, val, &s3->svga);\n}\n\nstatic void\ns3_lfb_writew(uint32_t addr, uint16_t val, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    svga_writew_linear(addr, val, &s3->svga);\n}\n\nstatic void\ns3_lfb_writel(uint32_t addr, uint32_t val, void *priv)\n{\n    s3_t *s3 = (s3_t *) priv;\n    S3_LFB_SYNC(s3);\n    svga_writel_linear(addr, val, &s3->svga);\n}\n\nstatic void\ns3_fifo_emp_timer(void *priv)\n{\n    s3_fifo_sync((s3_t *) priv);\n}\n\nstatic void\ns3_render_sync(svga_t *svga)\n{\n    s3_t *s3 = (s3_t *) svga->priv;\n\n    if (!FIFO_EMPTY)\n        s3_wait_fifo_idle(s3);\n}\n"),
    ('86box/src/video/vid_s3.c',
     '    int memory_map_mode = (svga->gdcreg[6] >> 2) & 3;\n\n',
     '    int memory_map_mode = (svga->gdcreg[6] >> 2) & 3;\n    s3_t *s3            = (s3_t *) svga->priv;\n\n    /* The CPU reaches video memory only after the blits queued before it. */\n    if (!FIFO_EMPTY)\n        s3_wait_fifo_idle(s3);\n\n'),
    ('86box/src/video/vid_s3.c',
     '        case 0x42e8:\n            return s3->subsys_stat | (enhanced_8bpp_modes ? 0x80 : 0x00);\n',
     '        case 0x42e8:\n            s3_fifo_sync(s3);\n            return s3->subsys_stat | (enhanced_8bpp_modes ? 0x80 : 0x00);\n'),
    ('86box/src/video/vid_s3.c',
     '            if (s3_enable_fifo(s3)) {\n                if (!s3->blitter_busy)\n                    wake_fifo_thread(s3);\n                if (FIFO_FULL)\n',
     '            if (s3_enable_fifo(s3)) {\n                s3_fifo_sync(s3);\n                if (FIFO_FULL)\n'),
    ('86box/src/video/vid_s3.c',
     '            if (s3_enable_fifo(s3)) {\n                if (!s3->blitter_busy)\n                    wake_fifo_thread(s3);\n\n',
     '            if (s3_enable_fifo(s3)) {\n                s3_fifo_sync(s3);\n\n'),
    ('86box/src/video/vid_s3.c',
     '            case 0x8504:\n                return s3->subsys_stat;\n',
     '            case 0x8504:\n                s3_fifo_sync(s3);\n                return s3->subsys_stat;\n'),
    ('86box/src/video/vid_s3.c',
     '        s3->blitter_busy = 0;\n        s3->subsys_stat |= INT_FIFO_EMP;\n        s3_update_irqs(s3);\n    }\n',
     '        s3->blitter_busy = 0;\n    }\n'),
    ('86box/src/video/vid_s3.c',
     "    mem_mapping_add(&s3->linear_mapping, 0, 0,\n                    svga_read_linear, svga_readw_linear, svga_readl_linear,\n                    svga_write_linear, svga_writew_linear, svga_writel_linear,\n                    NULL, MEM_MAPPING_EXTERNAL, &s3->svga);\n    /*It's hardcoded to 0xa0000 before the Trio64V+ and expects so*/\n",
     "    mem_mapping_add(&s3->linear_mapping, 0, 0,\n                    s3_lfb_read, s3_lfb_readw, s3_lfb_readl,\n                    s3_lfb_write, s3_lfb_writew, s3_lfb_writel,\n                    NULL, MEM_MAPPING_EXTERNAL, s3);\n    /*It's hardcoded to 0xa0000 before the Trio64V+ and expects so*/\n"),
    ('86box/src/video/vid_s3.c',
     '\n    *reset_state = *s3;\n',
     '\n    timer_add(&s3->fifo_emp_timer, s3_fifo_emp_timer, s3, 0);\n    svga->render_sync = s3_render_sync;\n\n    *reset_state = *s3;\n'),
    ('86box/src/video/vid_svga.c',
     '{\n    ibm8514_t       *dev = (ibm8514_t *) svga->dev8514;\n',
     '{\n    svga_render_drain();\n    ibm8514_t       *dev = (ibm8514_t *) svga->dev8514;\n'),
    ('86box/src/video/vid_svga.c',
     '        svga->render_line_offset = svga->start_retrace_latch - svga->crtc[0x4];\n        svga->render(svga);\n',
     '        svga->render_line_offset = svga->start_retrace_latch - svga->crtc[0x4];\n        if (svga->render_sync)\n            svga->render_sync(svga);\n        /* A line the cursors or the overlay draw on next is drawn in place */\n        svga->render_async = !svga->overlay_on && !svga->dac_hwcursor_on && !svga->hwcursor_on;\n#ifndef K9X_NO_RENDER /* measurement only: the cost of rendering on this thread */\n        svga->render(svga);\n'),
    ('86box/src/video/vid_svga.c',
     '        svga->render(svga);\n    }\n',
     '        svga->render(svga);\n#endif\n        svga->render_async = 0;\n    }\n'),
    ('86box/src/video/vid_svga.c',
     '{\n    free(svga->changedvram);\n',
     '{\n    svga_render_drain();\n    free(svga->changedvram);\n'),
    ('86box/src/video/vid_svga.c',
     '{\n    int       y_add;\n',
     '{\n    svga_render_drain();\n    int       y_add;\n'),
    ('86box/src/video/vid_svga_render.c',
     '#include <86box/vid_svga_render.h>\n#include <86box/vid_svga_render_remap.h>\n',
     '#include <86box/vid_svga_render.h>\n#include <stdatomic.h>\n#include <86box/thread.h>\n#include <86box/plat_unused.h>\n#include <86box/vid_svga_render_remap.h>\n'),
    ('86box/src/video/vid_svga_render.c',
     '\nstatic void\n',
     '\n/* Lines of packed 8bpp drawn on a thread of their own. The emulation thread\n   works out each line (svga->memaddr moves on just as drawing would move it)\n   and queues the part of it left of hdisp; the rest, which the right overscan\n   then partly covers, it draws itself, so the frame comes out the same.\n   Drawing writes nothing but the frame buffer, so the guest sees nothing of\n   it; a queued line shows the VRAM of a moment later. svga_render_drain()\n   waits for the queue to empty: before a frame is shown, before the buffer\n   can change size, and on close. A line something else draws on (cursors,\n   overlay) is drawn in place (svga->render_async). */\ntypedef struct render_job_t {\n    uint32_t       *p;\n    const uint8_t  *vram;\n    const uint32_t *map8;\n    uint32_t        memaddr;\n    uint32_t        mask;\n    uint32_t        dac;\n    int             dwords;\n} render_job_t;\n\n#define RENDER_JOBS 4096 /* a power of 2, more lines than a frame has */\n\nstatic render_job_t render_jobs[RENDER_JOBS];\nstatic atomic_uint  render_head; /* next job queued, emulation thread */\nstatic atomic_uint  render_tail; /* next job drawn, drawing thread */\nstatic thread_t    *render_thread;\nstatic event_t     *render_wake;\nstatic event_t     *render_idle;\n\nstatic void\nrender_8bpp_dwords(const render_job_t *job)\n{\n    uint32_t *p       = job->p;\n    uint32_t  memaddr = job->memaddr;\n\n    for (int c = 0; c < job->dwords; c++) {\n        const uint32_t dat = *(const uint32_t *) &job->vram[memaddr & job->mask];\n\n        memaddr = (memaddr + 4) & job->mask;\n        p[0]    = job->map8[dat & job->dac];\n        p[1]    = job->map8[(dat >> 8) & job->dac];\n        p[2]    = job->map8[(dat >> 16) & job->dac];\n        p[3]    = job->map8[(dat >> 24) & job->dac];\n        p += 4;\n    }\n}\n\nstatic void\nrender_thread_func(UNUSED(void *priv))\n{\n    for (;;) {\n        thread_wait_event(render_wake, -1);\n        thread_reset_event(render_wake);\n        for (;;) {\n            const unsigned tail = atomic_load_explicit(&render_tail, memory_order_relaxed);\n\n            if (tail == atomic_load_explicit(&render_head, memory_order_acquire))\n                break;\n            render_8bpp_dwords(&render_jobs[tail & (RENDER_JOBS - 1)]);\n            atomic_store_explicit(&render_tail, tail + 1, memory_order_release);\n        }\n        thread_set_event(render_idle);\n    }\n}\n\nvoid\nsvga_render_drain(void)\n{\n    if (render_thread == NULL)\n        return;\n    while (atomic_load_explicit(&render_tail, memory_order_acquire) != atomic_load_explicit(&render_head, memory_order_relaxed)) {\n        thread_reset_event(render_idle);\n        if (atomic_load_explicit(&render_tail, memory_order_acquire) == atomic_load_explicit(&render_head, memory_order_relaxed))\n            break;\n        thread_set_event(render_wake);\n        thread_wait_event(render_idle, -1);\n    }\n}\n\nstatic void\nrender_queue(const render_job_t *job)\n{\n    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);\n\n    if (render_thread == NULL) {\n        render_wake   = thread_create_event();\n        render_idle   = thread_create_event();\n        render_thread = thread_create(render_thread_func, NULL);\n    }\n    if ((head - atomic_load_explicit(&render_tail, memory_order_acquire)) == RENDER_JOBS)\n        svga_render_drain();\n    /* A thread still drawing finds the job itself; one that found the queue\n       empty is woken */\n    const int was_empty = (head == atomic_load_explicit(&render_tail, memory_order_acquire));\n    render_jobs[head & (RENDER_JOBS - 1)] = *job;\n    atomic_store_explicit(&render_head, head + 1, memory_order_release);\n    if (was_empty)\n        thread_set_event(render_wake);\n}\n\n\nstatic void\n'),
    ('86box/src/video/vid_svga_render.c',
     '\n    if (!(svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange))\n',
     '\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_lines_skip, k9x_lines_vram, k9x_lines_full;\n        if (!(svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange))\n            k9x_lines_skip++;\n        else if (svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1])\n            k9x_lines_vram++;\n        else\n            k9x_lines_full++;\n    }\n#endif\n    if (!(svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange))\n'),
    ('86box/src/video/vid_svga_render.c',
     '    static uint32_t col2         = 0;\n    for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += charwidth) {\n',
     '    static uint32_t col2         = 0;\n\n    /* Packed 8bpp, a dot per pixel, nothing remapped, masked or blinking:\n       what the loop below comes to (each VRAM byte in order through map8),\n       with the fields it reads held here, as the pixel stores could alias\n       them as far as the compiler knows (-fno-strict-aliasing). With\n       force_old_addr the address is memaddr & ~3 (forcepacked makes\n       incbypow2 0) unless CRTC 17h bits 0/1 bring in scanline bits, so it is\n       the same for a dword-aligned memaddr with both bits set. */\n    if (combine8bits && highres && !svga->packed_4bpp && !svga->half_pixel && !svga->ati_4color &&\n        (!svga->force_old_addr || (((svga->crtc[0x17] & 3) == 3) && !(svga->memaddr & 3) && !incbypow2)) &&\n        !svga->remap_required && (loadevery == 1) && (incevery == 1) &&\n        (planemask == 0xffffffff) && !blinkmask && shift4bit) {\n        const uint8_t  *vram    = svga->vram;\n        const uint32_t *map8    = svga->map8;\n        const uint32_t  mask    = svga->vram_display_mask;\n        const uint32_t  dac     = svga->dac_mask;\n        const int       end     = svga->hdisp + svga->scrollcache;\n        uint32_t        memaddr = svga->memaddr;\n\n#ifdef K9X_DIAG\n        {\n            extern uint64_t k9x_lines_fast;\n            k9x_lines_fast++;\n        }\n#endif\n        /* The dwords wholly left of hdisp to the drawing thread */\n        x = 0;\n        if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8)) {\n            const render_job_t job = { p, vram, map8, memaddr, mask, dac, svga->hdisp / 4 };\n\n            render_queue(&job);\n            memaddr = (memaddr + (4 * job.dwords)) & mask;\n            p += 4 * job.dwords;\n            x = 4 * job.dwords;\n        }\n\n        for (; x <= end; x += 4) {\n            const uint32_t dat = *(const uint32_t *) &vram[memaddr & mask];\n\n            memaddr = (memaddr + 4) & mask;\n            p[0]    = map8[dat & dac];\n            p[1]    = map8[(dat >> 8) & dac];\n            p[2]    = map8[(dat >> 16) & dac];\n            p[3]    = map8[(dat >> 24) & dac];\n            col     = p[3];\n            p += 4;\n        }\n        svga->memaddr = memaddr;\n    } else {\n#ifdef K9X_DIAG\n    {\n        extern uint64_t k9x_lines_slow, k9x_slow_why[8];\n        k9x_lines_slow++;\n        k9x_slow_why[0] += !(combine8bits && highres);\n        k9x_slow_why[1] += !!(svga->packed_4bpp || svga->half_pixel || svga->ati_4color);\n        k9x_slow_why[2] += !!svga->force_old_addr;\n        k9x_slow_why[3] += !!svga->remap_required;\n        k9x_slow_why[4] += (loadevery != 1) || (incevery != 1);\n        k9x_slow_why[5] += (planemask != 0xffffffff);\n        k9x_slow_why[6] += !!blinkmask;\n        k9x_slow_why[7] += !shift4bit;\n    }\n#endif\n    for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += charwidth) {\n'),
    ('86box/src/video/vid_svga_render.c',
     '            p += charwidth;\n    }\n',
     '            p += charwidth;\n    }\n    }\n'),
]

KAIRO9X_SOUND = [
    ('86box/src/include/86box/filters.h',
     '#define NCoef 2\n\n/* fc=350Hz */\nstatic inline double\n',
     "#define NCoef 2\n\n/* One channel of one of the 2-pole IIR filters below: its last inputs and\n   outputs. The *_s() forms take the caller's; the others keep 6 x 2 of their\n   own, shared by every card that passes the same c and i. */\ntypedef struct iir2_t {\n    double x[NCoef + 1];\n    double y[NCoef + 1];\n} iir2_t;\n\nstatic inline double\niir2_step(iir2_t *f, const double *ACoef, const double *BCoef, double NewSample)\n{\n    int n;\n\n    /* shift the old samples */\n    for (n = NCoef; n > 0; n--) {\n        f->x[n] = f->x[n - 1];\n        f->y[n] = f->y[n - 1];\n    }\n\n    /* Calculate the new output */\n    f->x[0] = NewSample;\n    f->y[0] = ACoef[0] * f->x[0];\n    for (n = 1; n <= NCoef; n++)\n        f->y[0] += ACoef[n] * f->x[n] - BCoef[n] * f->y[n];\n\n    return f->y[0];\n}\n\n/* fc=350Hz */\nstatic inline double\n"),
    ('86box/src/include/86box/filters.h',
     '\n/* fc=350Hz */\nstatic inline double\nlow_iir(int c, int i, double NewSample)\n',
     '\n/* fc=350Hz */\nstatic const double low_iir_a[NCoef + 1] = {\n    0.00049713569693400649,\n    0.00099427139386801299,\n    0.00049713569693400649\n};\nstatic const double low_iir_b[NCoef + 1] = {\n    1.00000000000000000000,\n    -1.93522955470669530000,\n    0.93726236021404663000\n};\n\nstatic inline double\nlow_iir_s(iir2_t *f, double NewSample)\n{\n    return iir2_step(f, low_iir_a, low_iir_b, NewSample);\n}\n\nstatic inline double\nlow_iir(int c, int i, double NewSample)\n'),
    ('86box/src/include/86box/filters.h',
     '{\n    double ACoef[NCoef + 1] = {\n        0.00049713569693400649,\n        0.00099427139386801299,\n        0.00049713569693400649\n    };\n\n',
     '{\n    static iir2_t f[6][2];\n\n'),
    ('86box/src/include/86box/filters.h',
     '\n    double BCoef[NCoef + 1] = {\n        1.00000000000000000000,\n        -1.93522955470669530000,\n        0.93726236021404663000\n    };\n\n    static double y[6][2][NCoef + 1]; /* output samples */\n    static double x[6][2][NCoef + 1]; /* input samples */\n    int           n;\n\n    /* shift the old samples */\n    for (n = NCoef; n > 0; n--) {\n        x[c][i][n] = x[c][i][n - 1];\n        y[c][i][n] = y[c][i][n - 1];\n    }\n\n    /* Calculate the new output */\n    x[c][i][0] = NewSample;\n    y[c][i][0] = ACoef[0] * x[c][i][0];\n    for (n = 1; n <= NCoef; n++)\n        y[c][i][0] += ACoef[n] * x[c][i][n] - BCoef[n] * y[c][i][n];\n\n    return y[c][i][0];\n}\n',
     '\n    return low_iir_s(&f[c][i], NewSample);\n}\n'),
    ('86box/src/include/86box/filters.h',
     '/* fc=350Hz */\nstatic inline double\n',
     '/* fc=350Hz */\nstatic const double low_cut_iir_a[NCoef + 1] = {\n    0.96839970114733542000,\n    -1.93679940229467080000,\n    0.96839970114733542000\n};\nstatic const double low_cut_iir_b[NCoef + 1] = {\n    1.00000000000000000000,\n    -1.93522955471202770000,\n    0.93726236021916731000\n};\n\nstatic inline double\nlow_cut_iir_s(iir2_t *f, double NewSample)\n{\n    return iir2_step(f, low_cut_iir_a, low_cut_iir_b, NewSample);\n}\n\nstatic inline double\n'),
    ('86box/src/include/86box/filters.h',
     'low_cut_iir(int c, int i, double NewSample)\n{\n    double ACoef[NCoef + 1] = {\n        0.96839970114733542000,\n        -1.93679940229467080000,\n        0.96839970114733542000\n    };\n\n    double BCoef[NCoef + 1] = {\n',
     'low_cut_iir(int c, int i, double NewSample)\n{\n    static iir2_t f[6][2];\n\n    double BCoef[NCoef + 1] = {\n'),
    ('86box/src/include/86box/filters.h',
     '\n    double BCoef[NCoef + 1] = {\n        1.00000000000000000000,\n        -1.93522955471202770000,\n        0.93726236021916731000\n    };\n\n    static double y[6][2][NCoef + 1]; /* output samples */\n    static double x[6][2][NCoef + 1]; /* input samples */\n    int           n;\n\n    /* shift the old samples */\n    for (n = NCoef; n > 0; n--) {\n        x[c][i][n] = x[c][i][n - 1];\n        y[c][i][n] = y[c][i][n - 1];\n    }\n\n    /* Calculate the new output */\n    x[c][i][0] = NewSample;\n    y[c][i][0] = ACoef[0] * x[c][i][0];\n    for (n = 1; n <= NCoef; n++)\n        y[c][i][0] += ACoef[n] * x[c][i][n] - BCoef[n] * y[c][i][n];\n\n    return y[c][i][0];\n}\n',
     '\n    return low_cut_iir_s(&f[c][i], NewSample);\n}\n'),
    ('86box/src/include/86box/filters.h',
     '\n/* fc=3.5kHz */\nstatic inline double\nhigh_iir(int c, int i, double NewSample)\n',
     '\n/* fc=3.5kHz */\nstatic const double high_iir_a[NCoef + 1] = {\n    0.72248704753064896000,\n    -1.44497409506129790000,\n    0.72248704753064896000\n};\nstatic const double high_iir_b[NCoef + 1] = {\n    1.00000000000000000000,\n    -1.36640781670578510000,\n    0.52352474706139873000\n};\n\nstatic inline double\nhigh_iir_s(iir2_t *f, double NewSample)\n{\n    return iir2_step(f, high_iir_a, high_iir_b, NewSample);\n}\n\nstatic inline double\nhigh_iir(int c, int i, double NewSample)\n'),
    ('86box/src/include/86box/filters.h',
     'high_iir(int c, int i, double NewSample)\n{\n    double ACoef[NCoef + 1] = {\n        0.72248704753064896000,\n        -1.44497409506129790000,\n        0.72248704753064896000\n    };\n\n    double BCoef[NCoef + 1] = {\n',
     'high_iir(int c, int i, double NewSample)\n{\n    static iir2_t f[6][2];\n\n    double BCoef[NCoef + 1] = {\n'),
    ('86box/src/include/86box/filters.h',
     '\n    double BCoef[NCoef + 1] = {\n        1.00000000000000000000,\n        -1.36640781670578510000,\n        0.52352474706139873000\n    };\n    static double y[6][2][NCoef + 1]; /* output samples */\n    static double x[6][2][NCoef + 1]; /* input samples */\n    int           n;\n\n    /* shift the old samples */\n    for (n = NCoef; n > 0; n--) {\n        x[c][i][n] = x[c][i][n - 1];\n        y[c][i][n] = y[c][i][n - 1];\n    }\n\n    /* Calculate the new output */\n    x[c][i][0] = NewSample;\n    y[c][i][0] = ACoef[0] * x[c][i][0];\n    for (n = 1; n <= NCoef; n++)\n        y[c][i][0] += ACoef[n] * x[c][i][n] - BCoef[n] * y[c][i][n];\n\n    return y[c][i][0];\n}\n',
     '\n    return high_iir_s(&f[c][i], NewSample);\n}\n'),
    ('86box/src/include/86box/filters.h',
     '/* fc=3.5kHz */\nstatic inline double\n',
     '/* fc=3.5kHz */\nstatic const double high_cut_iir_a[NCoef + 1] = {\n    0.03927726802250377400,\n    0.07855453604500754700,\n    0.03927726802250377400\n};\nstatic const double high_cut_iir_b[NCoef + 1] = {\n    1.00000000000000000000,\n    -1.36640781666419950000,\n    0.52352474703279628000\n};\n\nstatic inline double\nhigh_cut_iir_s(iir2_t *f, double NewSample)\n{\n    return iir2_step(f, high_cut_iir_a, high_cut_iir_b, NewSample);\n}\n\nstatic inline double\n'),
    ('86box/src/include/86box/filters.h',
     'high_cut_iir(int c, int i, double NewSample)\n{\n    double ACoef[NCoef + 1] = {\n        0.03927726802250377400,\n        0.07855453604500754700,\n        0.03927726802250377400\n    };\n\n    double BCoef[NCoef + 1] = {\n',
     'high_cut_iir(int c, int i, double NewSample)\n{\n    static iir2_t f[6][2];\n\n    double BCoef[NCoef + 1] = {\n'),
    ('86box/src/include/86box/filters.h',
     '\n    double BCoef[NCoef + 1] = {\n        1.00000000000000000000,\n        -1.36640781666419950000,\n        0.52352474703279628000\n    };\n    static double y[6][2][NCoef + 1]; /* output samples */\n    static double x[6][2][NCoef + 1]; /* input samples */\n    int           n;\n\n    /* shift the old samples */\n    for (n = NCoef; n > 0; n--) {\n        x[c][i][n] = x[c][i][n - 1];\n        y[c][i][n] = y[c][i][n - 1];\n    }\n\n    /* Calculate the new output */\n    x[c][i][0] = NewSample;\n    y[c][i][0] = ACoef[0] * x[c][i][0];\n    for (n = 1; n <= NCoef; n++)\n        y[c][i][0] += ACoef[n] * x[c][i][n] - BCoef[n] * y[c][i][n];\n\n    return y[c][i][0];\n}\n',
     '\n    return high_cut_iir_s(&f[c][i], NewSample);\n}\n'),
    ('86box/src/include/86box/filters.h',
     'extern double low_fir_sb16_coef[SB16_NCoef];\n\nstatic inline double\nlow_fir_sb16(int i, double NewSample)\n',
     "extern double low_fir_sb16_coef[SB16_NCoef];\n\n/* The SB16 output filter's state: both channels' last inputs. The *_s()\n   form takes the caller's; low_fir_sb16() keeps one of its own. */\ntypedef struct sb16_fir_t {\n    double x[2][SB16_NCoef + 1]; // input samples\n    int    pos;\n} sb16_fir_t;\n\nstatic inline double\nlow_fir_sb16_s(sb16_fir_t *f, int i, double NewSample)\n{\n    double out = 0.0;\n    int    n;\n\n    /* Calculate the new output */\n    f->x[i][f->pos] = NewSample;\n\n    for (n = 0; n < ((SB16_NCoef + 1) - f->pos) && n < SB16_NCoef; n++)\n        out += low_fir_sb16_coef[n] * f->x[i][n + f->pos];\n    for (; n < SB16_NCoef; n++)\n        out += low_fir_sb16_coef[n] * f->x[i][(n + f->pos) - (SB16_NCoef + 1)];\n\n    if (i == 1) {\n        f->pos++;\n        if (f->pos > SB16_NCoef)\n            f->pos = 0;\n    }\n\n    return out;\n}\n\nstatic inline double\nlow_fir_sb16(int i, double NewSample)\n"),
    ('86box/src/include/86box/filters.h',
     'low_fir_sb16(int i, double NewSample)\n{\n    static double x[2][SB16_NCoef + 1]; // input samples\n    static int    pos    = 0;\n    double        out    = 0.0;\n    int           n;\n\n    /* Calculate the new output */\n',
     'low_fir_sb16(int i, double NewSample)\n{\n    static sb16_fir_t f;\n\n    /* Calculate the new output */\n'),
    ('86box/src/include/86box/filters.h',
     '\n    /* Calculate the new output */\n    x[i][pos] = NewSample;\n\n    for (n = 0; n < ((SB16_NCoef + 1) - pos) && n < SB16_NCoef; n++)\n        out += low_fir_sb16_coef[n] * x[i][n + pos];\n    for (; n < SB16_NCoef; n++)\n        out += low_fir_sb16_coef[n] * x[i][(n + pos) - (SB16_NCoef + 1)];\n\n    if (i == 1) {\n        pos++;\n        if (pos > SB16_NCoef)\n            pos = 0;\n    }\n\n    return out;\n}\n',
     '\n    return low_fir_sb16_s(&f, i, NewSample);\n}\n'),
    ('86box/src/include/86box/snd_sb.h',
     '\n    /* Output gain required for the Pro Sonic 16 so PCM sounds are volume adjusted\n',
     '\n    /* SB16 output mixing thread (snd_sb.c), made on first use */\n    void *mix16;\n\n    /* Output gain required for the Pro Sonic 16 so PCM sounds are volume adjusted\n'),
    ('86box/src/sound/snd_backend.c',
     '#endif\n#if !defined(AUDIO4) && !defined(SNDIO)\n    { &sound_backend_openal                },\n',
     '#endif\n#if !defined(AUDIO4) && !defined(SNDIO) && !defined(K9X_NULL_AUDIO)\n    { &sound_backend_openal                },\n'),
    ('86box/src/sound/snd_backend.c',
     '#endif\n#if !defined(AUDIO4) && !defined(SNDIO)\n    { &sound_backend_xaudio2               },\n',
     '#endif\n#if !defined(AUDIO4) && !defined(SNDIO) && !defined(K9X_NULL_AUDIO)\n    { &sound_backend_xaudio2               },\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '#include <cstring>\n#include "ymfm/ymfm_ssg.h"\n',
     '#include <cstring>\n#include <condition_variable>\n#include <mutex>\n#include <thread>\n#include <vector>\n#include "ymfm/ymfm_ssg.h"\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    virtual uint8_t  read(uint16_t addr)                                     = 0;\n    virtual void     set_clock(uint32_t clock)                               = 0;\n',
     '    virtual uint8_t  read(uint16_t addr)                                     = 0;\n    /*Bring the samples up to now before a register access, unless another\n      thread makes them*/\n    virtual void     catch_up()                                              = 0;\n    virtual void     set_clock(uint32_t clock)                               = 0;\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '\ntemplate <typename ChipType>\n',
     "\n/*The interface of the copy of a chip that a synthesis thread runs: no\n  timers, busy or interrupts (the emulation thread's copy has those and\n  answers the guest), timer expiries replayed at the sample they came at, and\n  the OPL4's sample ROM.*/\nclass YMFMSynthIntf : public ymfm::ymfm_interface {\npublic:\n    const uint8_t *m_rom = nullptr;\n\n    void timer_expired(uint32_t tnum) { m_engine->engine_timer_expired(tnum); }\n\n    virtual uint8_t ymfm_external_read(ymfm::access_class type, uint32_t address) override\n    {\n        if ((m_rom != nullptr) && (type == ymfm::access_class::ACCESS_PCM) && (address < 0x200000))\n            return m_rom[address];\n        return 0xFF;\n    }\n};\n\n/*Samples are made on a thread of their own, one buffer behind: the\n  emulation thread's chip takes the writes, runs the timers and answers reads,\n  and logs each write, timer expiry and clock change with the sample it came\n  at. When the buffer is due (update()), that log goes to the synthesis\n  thread, whose own copy of the chip makes the buffer from it exactly as the\n  emulation thread would have, and the buffer it finished last time is handed\n  over. The guest sees nothing of it; the sound comes out one buffer later.\n  A chip whose samples are taken with generate() (midi_opl4.c) makes them\n  itself, as before.*/\ntemplate <typename ChipType>\n"),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        , m_chip(*this)\n        , m_clock(clock)\n',
     '        , m_chip(*this)\n        , m_synth(m_sintf)\n        , m_clock(clock)\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        timer_add(&m_timers[1], YMFMChip::timer2, this, 0);\n    }\n',
     '        timer_add(&m_timers[1], YMFMChip::timer2, this, 0);\n\n        m_sintf.m_rom = m_yrw801;\n        m_synth_rateratio = m_rateratio;\n        if (m_buf_pos_global == &sound_pos_global)\n            m_buf_len = SOUNDBUFLEN;\n        else if (m_buf_pos_global == &ym2151_pos_global)\n            m_buf_len = YM2151BUFLEN;\n        else if (m_buf_pos_global == &music_pos_global)\n            m_buf_len = MUSICBUFLEN;\n        else\n            m_buf_len = WTBUFLEN;\n        memset(m_done, 0, sizeof(m_done));\n        m_thread = std::thread(&YMFMChip::synth_thread, this);\n    }\n\n    virtual ~YMFMChip()\n    {\n        {\n            std::lock_guard<std::mutex> lock(m_mutex);\n            m_quit = true;\n        }\n        m_cv.notify_all();\n        m_thread.join();\n    }\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        m_rateratio = (m_samplerate << RSM_FRAC) / m_chip.sample_rate(m_clock);\n\n',
     '        m_rateratio = (m_samplerate << RSM_FRAC) / m_chip.sample_rate(m_clock);\n        log_event(EV_CLOCK, 0, clock);\n\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    virtual void generate(int32_t *data, uint32_t num_samples) override\n    {\n        for (uint32_t i = 0; i < num_samples; i++) {\n            m_chip.generate(&m_output);\n',
     '    virtual void generate(int32_t *data, uint32_t num_samples) override\n    {\n        m_threaded = false;\n        generate_on(m_chip, data, num_samples);\n    }\n\n    virtual void generate_resampled(int32_t *data, uint32_t num_samples) override\n    {\n        m_threaded = false;\n        generate_resampled_on(m_chip, m_rateratio, data, num_samples);\n    }\n\n    void generate_on(ChipType &chip, int32_t *data, uint32_t num_samples)\n    {\n        for (uint32_t i = 0; i < num_samples; i++) {\n            m_chip.generate(&m_output);\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        for (uint32_t i = 0; i < num_samples; i++) {\n            m_chip.generate(&m_output);\n            if ((m_type == FM_YMF278B) && (sizeof(m_output.data) > (4 * sizeof(int32_t)))) {\n',
     '        for (uint32_t i = 0; i < num_samples; i++) {\n            chip.generate(&m_output);\n            if ((m_type == FM_YMF278B) && (sizeof(m_output.data) > (4 * sizeof(int32_t)))) {\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    }\n\n    virtual void generate_resampled(int32_t *data, uint32_t num_samples) override\n    {\n        for (uint32_t i = 0; i < num_samples; i++) {\n',
     '    }\n\n    void generate_resampled_on(ChipType &chip, int32_t rateratio, int32_t *data, uint32_t num_samples)\n    {\n        for (uint32_t i = 0; i < num_samples; i++) {\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        for (uint32_t i = 0; i < num_samples; i++) {\n            while (m_samplecnt >= m_rateratio) {\n                m_oldsamples[0] = m_samples[0];\n',
     '        for (uint32_t i = 0; i < num_samples; i++) {\n            while (m_samplecnt >= rateratio) {\n                m_oldsamples[0] = m_samples[0];\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '                m_oldsamples[1] = m_samples[1];\n                m_chip.generate(&m_output);\n                if ((m_type == FM_YMF278B) && (sizeof(m_output.data) > (4 * sizeof(int32_t)))) {\n',
     '                m_oldsamples[1] = m_samples[1];\n                chip.generate(&m_output);\n                if ((m_type == FM_YMF278B) && (sizeof(m_output.data) > (4 * sizeof(int32_t)))) {\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '                }\n                m_samplecnt -= m_rateratio;\n            }\n',
     '                }\n                m_samplecnt -= rateratio;\n            }\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '\n            *data++ = ((int32_t) ((m_oldsamples[0] * (m_rateratio - m_samplecnt)\n                                   + m_samples[0] * m_samplecnt)\n',
     '\n            *data++ = ((int32_t) ((m_oldsamples[0] * (rateratio - m_samplecnt)\n                                   + m_samples[0] * m_samplecnt)\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '                                   + m_samples[0] * m_samplecnt)\n                                  / m_rateratio));\n            *data++ = ((int32_t) ((m_oldsamples[1] * (m_rateratio - m_samplecnt)\n                                   + m_samples[1] * m_samplecnt)\n',
     '                                   + m_samples[0] * m_samplecnt)\n                                  / rateratio));\n            *data++ = ((int32_t) ((m_oldsamples[1] * (rateratio - m_samplecnt)\n                                   + m_samples[1] * m_samplecnt)\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '                                   + m_samples[1] * m_samplecnt)\n                                  / m_rateratio));\n\n',
     '                                   + m_samples[1] * m_samplecnt)\n                                  / rateratio));\n\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    {\n        if (m_buf_pos >= *m_buf_pos_global)\n',
     '    {\n        if (m_threaded) {\n            /*Only a full buffer is handed over; a register access on the way\n              (catch_up()) has nothing to do*/\n            if (*m_buf_pos_global == (int) m_buf_len)\n                hand_over();\n            return m_buffer;\n        }\n        if (m_buf_pos >= *m_buf_pos_global)\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        m_chip.write(addr, data);\n    }\n',
     '        m_chip.write(addr, data);\n        log_event(EV_WRITE, addr, data);\n    }\n\n    virtual void catch_up() override\n    {\n        if (!m_threaded)\n            update();\n    }\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        drv->m_engine->engine_timer_expired(0);\n    }\n',
     '        drv->m_engine->engine_timer_expired(0);\n        drv->log_event(EV_TIMER, 0, 0);\n    }\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '        drv->m_engine->engine_timer_expired(1);\n    }\n',
     '        drv->m_engine->engine_timer_expired(1);\n        drv->log_event(EV_TIMER, 1, 0);\n    }\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     'private:\n    ChipType                       m_chip;\n',
     'private:\n    enum { EV_WRITE, EV_TIMER, EV_CLOCK };\n    struct event_t {\n        uint32_t pos;  /*sample in the buffer it came at*/\n        uint8_t  kind;\n        uint16_t addr; /*register, or timer number*/\n        uint32_t data; /*value, or clock*/\n    };\n\n    void log_event(uint8_t kind, uint16_t addr, uint32_t data)\n    {\n        if (m_threaded)\n            m_events.push_back({ (uint32_t) *m_buf_pos_global, kind, addr, data });\n    }\n\n    /*The buffer is full: the synthesis thread gets its log, and the buffer\n      it finished last becomes this one*/\n    void hand_over()\n    {\n        std::unique_lock<std::mutex> lock(m_mutex);\n        m_cv.wait(lock, [this] { return !m_job_pending; });\n        memcpy(m_buffer, m_done, m_buf_len * 2 * sizeof(int32_t));\n        m_job.swap(m_events);\n        m_events.clear();\n        m_job_pending = true;\n        lock.unlock();\n        m_cv.notify_all();\n        m_buf_pos = m_buf_len;\n    }\n\n    void synth_samples(uint32_t from, uint32_t to)\n    {\n        if (to <= from)\n            return;\n        if (m_48k)\n            generate_resampled_on(m_synth, m_synth_rateratio, &m_done[from * 2], to - from);\n        else\n            generate_on(m_synth, &m_done[from * 2], to - from);\n    }\n\n    void synth_thread()\n    {\n        for (;;) {\n            std::unique_lock<std::mutex> lock(m_mutex);\n            m_cv.wait(lock, [this] { return m_job_pending || m_quit; });\n            if (m_quit)\n                return;\n            lock.unlock();\n\n            uint32_t pos = 0;\n            for (const event_t &ev : m_job) {\n                synth_samples(pos, ev.pos);\n                if (ev.pos > pos)\n                    pos = ev.pos;\n                if (ev.kind == EV_WRITE)\n                    m_synth.write(ev.addr, (uint8_t) ev.data);\n                else if (ev.kind == EV_TIMER)\n                    m_sintf.timer_expired(ev.addr);\n                else\n                    m_synth_rateratio = (m_samplerate << RSM_FRAC) / m_synth.sample_rate(ev.data);\n            }\n            synth_samples(pos, m_buf_len);\n            for (uint32_t c = 0; c < m_buf_len * 2; c++)\n                m_done[c] /= 2;\n\n            lock.lock();\n            m_job_pending = false;\n            lock.unlock();\n            m_cv.notify_all();\n        }\n    }\n\n    YMFMSynthIntf                  m_sintf;\n    ChipType                       m_chip;\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    double                         m_subtract[2];\n    typename ChipType::output_data m_output;\n',
     '    double                         m_subtract[2];\n    ChipType                       m_synth;\n    typename ChipType::output_data m_output;\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    int                            m_cs;\n};\n',
     '    int                            m_cs;\n\n    /*The synthesis thread, its log and its finished buffer*/\n    bool                    m_threaded        = true;\n    uint32_t                m_buf_len         = 0;\n    int32_t                 m_synth_rateratio = 0;\n    std::vector<event_t>    m_events;\n    std::vector<event_t>    m_job;\n    int32_t                 m_done[MUSICBUFLEN * 2];\n    bool                    m_job_pending     = false;\n    bool                    m_quit            = false;\n    std::mutex              m_mutex;\n    std::condition_variable m_cv;\n    std::thread             m_thread;\n};\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    uint8_t ret = drv->read(port);\n    drv->update();\n\n',
     '    uint8_t ret = drv->read(port);\n    drv->catch_up();\n\n'),
    ('86box/src/sound/snd_opl_ymfm.cpp',
     '    drv->write(port, val);\n    drv->update();\n}\n',
     '    drv->write(port, val);\n    drv->catch_up();\n}\n'),
    ('86box/src/sound/snd_sb.c',
     '#include <86box/plat_unused.h>\n#include <86box/snd_azt2316a.h>\n',
     '#include <86box/plat_unused.h>\n#include <86box/thread.h>\n#include <86box/snd_azt2316a.h>\n'),
    ('86box/src/sound/snd_sb.c',
     '}\n\nstatic void\nsb_get_buffer_sb16_awe32(int32_t *buffer, uint16_t len, void *priv)\n',
     "}\n\n/* The SB16's output mixing (filter, volumes, bass and treble: nothing the\n   guest sees) runs on a thread of its own, one buffer behind: when a buffer is\n   due its DSP samples and the mixer settings go to the thread, and the buffer\n   it mixed last time is added in. The filters' state is its own. */\ntypedef struct sb16_mix_t {\n    thread_t         *thread;\n    event_t          *start;\n    event_t          *done;\n    int               quit;\n    sb_ct1745_mixer_t mixer;\n    uint16_t          len;\n    int16_t           dsp[SOUNDBUFLEN * 2];\n    int32_t           out[SOUNDBUFLEN * 2];\n    sb16_fir_t        fir;\n    iir2_t            bass[2];\n    iir2_t            treble[2];\n} sb16_mix_t;\n\nstatic void\nsb_get_buffer_sb16_awe32(int32_t *buffer, uint16_t len, void *priv)\n"),
    ('86box/src/sound/snd_sb.c',
     'static void\nsb_get_buffer_sb16_awe32(int32_t *buffer, uint16_t len, void *priv)\n{\n',
     'static void\nsb16_mix(sb16_mix_t *mix)\n{\n'),
    ('86box/src/sound/snd_sb.c',
     'sb16_mix(sb16_mix_t *mix)\n{\n    sb_t                    *sb    = (sb_t *) priv;\n    const sb_ct1745_mixer_t *mixer = &sb->mixer_sb16;\n    double                   bass_treble;\n\n',
     'sb16_mix(sb16_mix_t *mix)\n{\n    const sb_ct1745_mixer_t *mixer = &mix->mixer;\n    double                   bass_treble;\n\n'),
    ('86box/src/sound/snd_sb.c',
     '    double                   bass_treble;\n\n    sb_dsp_update(&sb->dsp);\n\n    for (uint16_t c = 0; c < len * 2; c += 2) {\n        double out_l = 0.0;\n        double out_r = 0.0;\n',
     '    double                   bass_treble;\n\n    for (uint16_t c = 0; c < mix->len * 2; c += 2) {\n        double out_l = 0.0;\n        double out_r = 0.0;\n'),
    ('86box/src/sound/snd_sb.c',
     '            /* We divide by 3 to get the volume down to normal. */\n            out_l += (low_fir_sb16(0, (double) sb->dsp.buffer[c]) * mixer->voice_l) / 3.0;\n            out_r += (low_fir_sb16(1, (double) sb->dsp.buffer[c + 1]) * mixer->voice_r) / 3.0;\n        } else {\n',
     '            /* We divide by 3 to get the volume down to normal. */\n            out_l += (low_fir_sb16_s(&mix->fir, 0, (double) mix->dsp[c]) * mixer->voice_l) / 3.0;\n            out_r += (low_fir_sb16_s(&mix->fir, 1, (double) mix->dsp[c + 1]) * mixer->voice_r) / 3.0;\n        } else {\n'),
    ('86box/src/sound/snd_sb.c',
     '        } else {\n            out_l += (((double) sb->dsp.buffer[c]) * mixer->voice_l) / 3.0;\n            out_r += (((double) sb->dsp.buffer[c + 1]) * mixer->voice_r) / 3.0;\n        }\n',
     '        } else {\n            out_l += (((double) mix->dsp[c]) * mixer->voice_l) / 3.0;\n            out_r += (((double) mix->dsp[c + 1]) * mixer->voice_r) / 3.0;\n        }\n'),
    ('86box/src/sound/snd_sb.c',
     '            if (mixer->bass_l > 8)\n                out_l += (low_iir(0, 0, out_l) * bass_treble);\n            else\n',
     '            if (mixer->bass_l > 8)\n                out_l += (low_iir_s(&mix->bass[0], out_l) * bass_treble);\n            else\n'),
    ('86box/src/sound/snd_sb.c',
     '            else\n                out_l = (out_l *bass_treble + low_cut_iir(0, 0, out_l) * (1.0 - bass_treble));\n        }\n',
     '            else\n                out_l = (out_l *bass_treble + low_cut_iir_s(&mix->bass[0], out_l) * (1.0 - bass_treble));\n        }\n'),
    ('86box/src/sound/snd_sb.c',
     '            if (mixer->bass_r > 8)\n                out_r += (low_iir(0, 1, out_r) * bass_treble);\n            else\n',
     '            if (mixer->bass_r > 8)\n                out_r += (low_iir_s(&mix->bass[1], out_r) * bass_treble);\n            else\n'),
    ('86box/src/sound/snd_sb.c',
     '            else\n                out_r = (out_r *bass_treble + low_cut_iir(0, 1, out_r) * (1.0 - bass_treble));\n        }\n',
     '            else\n                out_r = (out_r *bass_treble + low_cut_iir_s(&mix->bass[1], out_r) * (1.0 - bass_treble));\n        }\n'),
    ('86box/src/sound/snd_sb.c',
     '            if (mixer->treble_l > 8)\n                out_l += (high_iir(0, 0, out_l) * bass_treble);\n            else\n',
     '            if (mixer->treble_l > 8)\n                out_l += (high_iir_s(&mix->treble[0], out_l) * bass_treble);\n            else\n'),
    ('86box/src/sound/snd_sb.c',
     '            else\n                out_l = (out_l *bass_treble + high_cut_iir(0, 0, out_l) * (1.0 - bass_treble));\n        }\n',
     '            else\n                out_l = (out_l *bass_treble + high_cut_iir_s(&mix->treble[0], out_l) * (1.0 - bass_treble));\n        }\n'),
    ('86box/src/sound/snd_sb.c',
     '            if (mixer->treble_r > 8)\n                out_r += (high_iir(0, 1, out_r) * bass_treble);\n            else\n',
     '            if (mixer->treble_r > 8)\n                out_r += (high_iir_s(&mix->treble[1], out_r) * bass_treble);\n            else\n'),
    ('86box/src/sound/snd_sb.c',
     '            else\n                out_r = (out_r *bass_treble + high_cut_iir(0, 1, out_r) * (1.0 - bass_treble));\n        }\n',
     '            else\n                out_r = (out_r *bass_treble + high_cut_iir_s(&mix->treble[1], out_r) * (1.0 - bass_treble));\n        }\n'),
    ('86box/src/sound/snd_sb.c',
     '                out_r = (out_r *bass_treble + high_cut_iir_s(&mix->treble[1], out_r) * (1.0 - bass_treble));\n        }\n\n        buffer[c] += (int32_t) (out_l * mixer->output_gain_L);\n        buffer[c + 1] += (int32_t) (out_r * mixer->output_gain_R);\n    }\n\n    sb->dsp.pos = 0;\n',
     '                out_r = (out_r *bass_treble + high_cut_iir_s(&mix->treble[1], out_r) * (1.0 - bass_treble));\n        }\n\n        mix->out[c]     = (int32_t) (out_l * mixer->output_gain_L);\n        mix->out[c + 1] = (int32_t) (out_r * mixer->output_gain_R);\n    }\n\n    sb->dsp.pos = 0;\n'),
    ('86box/src/sound/snd_sb.c',
     '        mix->out[c + 1] = (int32_t) (out_r * mixer->output_gain_R);\n    }\n\n    sb->dsp.pos = 0;\n',
     "        mix->out[c + 1] = (int32_t) (out_r * mixer->output_gain_R);\n    }\n}\n\nstatic void\nsb16_mix_thread(void *priv)\n{\n    sb16_mix_t *mix = (sb16_mix_t *) priv;\n\n    for (;;) {\n        thread_wait_event(mix->start, -1);\n        thread_reset_event(mix->start);\n        if (mix->quit)\n            return;\n        sb16_mix(mix);\n        thread_set_event(mix->done);\n    }\n}\n\nstatic void\nsb16_mix_close(sb_t *sb)\n{\n    sb16_mix_t *mix = (sb16_mix_t *) sb->mix16;\n\n    if (mix == NULL)\n        return;\n    thread_wait_event(mix->done, -1);\n    mix->quit = 1;\n    thread_set_event(mix->start);\n    thread_wait(mix->thread);\n    thread_destroy_event(mix->start);\n    thread_destroy_event(mix->done);\n    free(mix);\n    sb->mix16 = NULL;\n}\n\nstatic void\nsb_get_buffer_sb16_awe32(int32_t *buffer, uint16_t len, void *priv)\n{\n    sb_t       *sb  = (sb_t *) priv;\n    sb16_mix_t *mix = (sb16_mix_t *) sb->mix16;\n\n    sb_dsp_update(&sb->dsp);\n\n    if (mix == NULL) {\n        mix         = (sb16_mix_t *) calloc(1, sizeof(sb16_mix_t));\n        mix->start  = thread_create_event();\n        mix->done   = thread_create_event();\n        mix->len    = len;\n        thread_set_event(mix->done);\n        mix->thread = thread_create(sb16_mix_thread, mix);\n        sb->mix16   = mix;\n    }\n\n    /* The buffer mixed last time; then this one's samples and settings go */\n    thread_wait_event(mix->done, -1);\n    thread_reset_event(mix->done);\n    for (uint16_t c = 0; c < mix->len * 2; c++)\n        buffer[c] += mix->out[c];\n    mix->mixer = sb->mixer_sb16;\n    mix->len   = len;\n    memcpy(mix->dsp, sb->dsp.buffer, len * 2 * sizeof(int16_t));\n    thread_set_event(mix->start);\n\n    sb->dsp.pos = 0;\n"),
    ('86box/src/sound/snd_sb.c',
     '    sb_t *sb = (sb_t *) priv;\n    sb_dsp_close(&sb->dsp);\n',
     '    sb_t *sb = (sb_t *) priv;\n    sb16_mix_close(sb);\n    sb_dsp_close(&sb->dsp);\n'),
    ('86box/src/sound/sound.c',
     '        memset(outbuffer, 0x00, sound_buf_len * 2 * sizeof(int32_t));\n\n        for (uint8_t c = 0; c < handler_count; c++)\n            if (sound_handlers[c].get_buffer != NULL)\n',
     '        memset(outbuffer, 0x00, sound_buf_len * 2 * sizeof(int32_t));\n\n#ifndef K9X_NO_SYNTH /* measurement only: the cost of synthesis on this thread */\n        for (uint8_t c = 0; c < handler_count; c++)\n            if (sound_handlers[c].get_buffer != NULL)\n'),
    ('86box/src/sound/sound.c',
     '                sound_handlers[c].get_buffer(outbuffer, sound_buf_len, sound_handlers[c].priv);\n\n',
     '                sound_handlers[c].get_buffer(outbuffer, sound_buf_len, sound_handlers[c].priv);\n#endif\n\n'),
    ('86box/src/sound/sound.c',
     '        memset(outbuffer_m, 0x00, MUSICBUFLEN * 2 * sizeof(int32_t));\n\n        for (uint8_t c = 0; c < handler_count; c++)\n            if (music_handlers[c].get_buffer != NULL)\n',
     '        memset(outbuffer_m, 0x00, MUSICBUFLEN * 2 * sizeof(int32_t));\n\n#ifndef K9X_NO_SYNTH\n        for (uint8_t c = 0; c < handler_count; c++)\n            if (music_handlers[c].get_buffer != NULL)\n'),
    ('86box/src/sound/sound.c',
     '                music_handlers[c].get_buffer(outbuffer_m, MUSICBUFLEN, music_handlers[c].priv);\n\n',
     '                music_handlers[c].get_buffer(outbuffer_m, MUSICBUFLEN, music_handlers[c].priv);\n#endif\n\n'),
]

# KairoX86#1: every file that included PCE's GPL-2.0-only cassette.h includes KairoX86's own header,
# which has the same calls; the device builds KairoX86's kairo_cassette.c; VDE networking is left out.
_CASSETTE_USERS = ['config.c', 'device/kbc_xt.c', 'device/keyboard_xt.c', 'machine/machine.c',
                   'machine/m_pcjr.c', 'machine/m_pcjx.c', 'machine_status.cpp', 'pit.c', 'pit_fast.c',
                   'unix/sdl_cdrom.c']
_NL = chr(10)
KAIROX86_LICENSE = [
    ('86box/src/' + user, '#include <86box/cassette.h>' + _NL,
     '#include <86box/kairo_cassette.h> /* KairoX86 */' + _NL) for user in _CASSETTE_USERS
] + [
    ('86box/src/device/CMakeLists.txt', '    cassette.c' + _NL, '    kairo_cassette.c' + _NL),
    ('86box/src/network/CMakeLists.txt', '    if(HAS_VDE)' + _NL,
     '    set(HAS_VDE OFF) # KairoX86: net_vde.c (GPL-2.0-only) is left out' + _NL + '    if(HAS_VDE)' + _NL),
]

# KairoX86's build of the core (core/CMakeLists.txt): 86Box as a library its host loads afresh for
# each machine (KAIRO_LIBRARY), with KairoX86's frontend in place of the headless program and its
# null audio (KAIRO_FRONTEND, core/kairo/), and the CHD reader of the shared frontend, which every
# Kairo app that reads CHDs uses (KAIRO_LIBCHDR, shared cmake/KairoChd.cmake).
KAIROX86_LIBRARY = [
    ('86box/src/CMakeLists.txt',
     'add_executable(86Box' + _NL,
     '# KairoX86: the core as a library its host loads, a fresh copy per machine.' + _NL
     + 'macro(kairo_86box_target name)' + _NL
     + '    if(KAIRO_LIBRARY)' + _NL
     + '        add_library(${name} SHARED ${ARGN})' + _NL
     + '    else()' + _NL
     + '        add_executable(${name} ${ARGN})' + _NL
     + '    endif()' + _NL
     + 'endmacro()' + _NL
     + 'kairo_86box_target(86Box' + _NL),
    ('86box/src/cdrom/CMakeLists.txt',
     'add_subdirectory(libchdr)' + _NL,
     '# KairoX86: KAIRO_LIBCHDR names a chdr-static the build already has (the shared frontend\'s).' + _NL
     + 'if(NOT KAIRO_LIBCHDR)' + _NL
     + '    add_subdirectory(libchdr)' + _NL
     + 'endif()' + _NL),
    ('86box/src/cdrom/CMakeLists.txt',
     'add_library(PkgConfig::SNDFILE ALIAS SndFile::sndfile)' + _NL,
     '# KairoX86: an interface over SndFile::sndfile, which may itself be an alias (libsndfile built' + _NL
     + '# from source names it one), and an alias of an alias is not allowed.' + _NL
     + 'add_library(PkgConfig::SNDFILE INTERFACE IMPORTED)' + _NL
     + 'target_link_libraries(PkgConfig::SNDFILE INTERFACE SndFile::sndfile)' + _NL),
    ('86box/src/cdrom/CMakeLists.txt',
     'target_link_libraries(cdrom chdr-static)' + _NL,
     'target_link_libraries(cdrom chdr-static)' + _NL
     + '# KairoX86: the CD image reader includes sndfile.h, which libsndfile built from source writes' + _NL
     + '# into its build folder; linking it gives the reader its headers and builds it first.' + _NL
     + 'target_link_libraries(cdrom PkgConfig::SNDFILE)' + _NL),
    # The version header names 86Box's own project (PROJECT_*), not the top-level one
    # (CMAKE_PROJECT_*), which is KairoX86's core when 86Box is built inside it.
    ('86box/CMakeLists.txt',
     'if(NOT CMAKE_PROJECT_VERSION_PATCH)' + _NL + '    set(CMAKE_PROJECT_VERSION_PATCH 0)' + _NL,
     'if(NOT PROJECT_VERSION_PATCH)' + _NL + '    set(PROJECT_VERSION_PATCH 0)' + _NL),
    # The recompiler's pool near the core's code (docs/core-performance.md #47), which as a library
    # loaded among others is not the program: the nearest free place after or before the library,
    # within ADRP's 4 GiB, instead of one fixed address past it. The code generator takes BL/ADRP
    # only for what is in reach, so where the pool lands does not change the guest.
    ('86box/src/unix/sdl_plat_unix.c',
     '        extern char     _end[];' + _NL
     + '        const uintptr_t align = (uintptr_t) 2 << 20;' + _NL
     + '        const uintptr_t at    = ((uintptr_t) _end + (16 << 20) + align - 1) & ~(align - 1);' + _NL
     + '        void           *pool  = mmap((void *) at, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANON | MAP_PRIVATE | MAP_FIXED_NOREPLACE, -1, 0);' + _NL
     + _NL
     + '        if (pool == MAP_FAILED)' + _NL
     + '            fatal("plat_mmap: no room for the recompiler at %p after the program: %s\\n", (void *) at, strerror(errno));' + _NL,
     '        extern char     __ehdr_start[];' + _NL
     + '        extern char     _end[];' + _NL
     + '        const uintptr_t align = (uintptr_t) 2 << 20;' + _NL
     + '        const uintptr_t reach = (uintptr_t) 4 << 30;' + _NL
     + '        const uintptr_t above = ((uintptr_t) _end + align - 1) & ~(align - 1);' + _NL
     + '        const uintptr_t below = ((uintptr_t) __ehdr_start - size) & ~(align - 1);' + _NL
     + '        void           *pool  = MAP_FAILED;' + _NL
     + _NL
     + '        /* KairoX86: the nearest free place to the core, after it and before it in turn. */' + _NL
     + '        for (uintptr_t step = 0; (pool == MAP_FAILED) && (step < reach); step += align) {' + _NL
     + '            const uintptr_t places[2] = { above + step, (below > step) ? (below - step) : 0 };' + _NL
     + '            for (int i = 0; (i < 2) && (pool == MAP_FAILED); i++) {' + _NL
     + '                if (!places[i])' + _NL
     + '                    continue;' + _NL
     + '                pool = mmap((void *) places[i], size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANON | MAP_PRIVATE | MAP_FIXED_NOREPLACE, -1, 0);' + _NL
     + '                if ((pool == MAP_FAILED) && (errno != EEXIST))' + _NL
     + '                    fatal("plat_mmap: the recompiler\'s pool at %p: %s\\n", (void *) places[i], strerror(errno));' + _NL
     + '                /* A kernel without MAP_FIXED_NOREPLACE takes the place as a hint: elsewhere is taken. */' + _NL
     + '                if ((pool != MAP_FAILED) && ((uintptr_t) pool != places[i])) {' + _NL
     + '                    munmap(pool, size);' + _NL
     + '                    pool = MAP_FAILED;' + _NL
     + '                }' + _NL
     + '            }' + _NL
     + '        }' + _NL
     + '        if (pool == MAP_FAILED)' + _NL
     + '            fatal("plat_mmap: no room for the recompiler within 4 GiB of the program\\n");' + _NL),
    # The 8bpp drawing thread (docs/core-performance.md #42) ran until the process ended. A host that runs
    # machine after machine in one process, unloading each one's copy of the core, must find no thread
    # of it left: svga_render_close (from video_close) drains the queue and joins the thread.
    ('86box/src/video/vid_svga_render.c',
     'static event_t     *render_idle;' + _NL,
     'static event_t     *render_idle;' + _NL
     + 'static atomic_int   render_quit; /* KairoX86: svga_render_close ends the drawing thread */' + _NL),
    ('86box/src/video/vid_svga_render.c',
     '        thread_wait_event(render_wake, -1);' + _NL + '        thread_reset_event(render_wake);' + _NL,
     '        thread_wait_event(render_wake, -1);' + _NL + '        thread_reset_event(render_wake);' + _NL
     + '        if (atomic_load_explicit(&render_quit, memory_order_acquire))' + _NL
     + '            return; /* KairoX86: svga_render_close, after the queue was drained */' + _NL),
    ('86box/src/video/vid_svga_render.c',
     'static void' + _NL + 'render_queue(const render_job_t *job)' + _NL,
     '/* KairoX86: ends the drawing thread, its queue drawn, so nothing of it outlives the machine. */' + _NL
     + 'void' + _NL + 'svga_render_close(void)' + _NL + '{' + _NL
     + '    if (render_thread == NULL)' + _NL + '        return;' + _NL
     + '    svga_render_drain();' + _NL
     + '    atomic_store_explicit(&render_quit, 1, memory_order_release);' + _NL
     + '    thread_set_event(render_wake);' + _NL
     + '    thread_wait(render_thread);' + _NL
     + '    thread_destroy_event(render_wake);' + _NL
     + '    thread_destroy_event(render_idle);' + _NL
     + '    render_thread = NULL;' + _NL + '    render_wake   = NULL;' + _NL + '    render_idle   = NULL;' + _NL
     + '    atomic_store_explicit(&render_quit, 0, memory_order_relaxed);' + _NL
     + '}' + _NL + _NL
     + 'static void' + _NL + 'render_queue(const render_job_t *job)' + _NL),
    ('86box/src/include/86box/vid_svga_render.h',
     'extern void svga_render_drain(void);' + _NL,
     'extern void svga_render_drain(void);' + _NL
     + 'extern void svga_render_close(void); /* KairoX86: ends the drawing thread */' + _NL),
    ('86box/src/video/video.c',
     'video_close(void)' + _NL + '{' + _NL + '    video_monitor_close(0);' + _NL,
     'video_close(void)' + _NL + '{' + _NL
     + '    svga_render_close(); /* KairoX86: the 8bpp drawing thread ends with the machine */' + _NL
     + '    video_monitor_close(0);' + _NL),
    ('86box/src/video/video.c',
     '#include <86box/vid_svga.h>' + _NL,
     '#include <86box/vid_svga.h>' + _NL + '#include <86box/vid_svga_render.h> /* KairoX86 */' + _NL),
    # The floppy and hard disk drive sound threads start with the machine (pc_init_modules) but
    # nothing ended them: pc_close ends them too, so a closed machine leaves no thread behind.
    ('86box/src/86box.c',
     '    sound_cd_thread_end();' + _NL,
     '    sound_cd_thread_end();' + _NL
     + '    /* KairoX86: the drive sound threads end with the machine too. */' + _NL
     + '    fdd_audio_close();' + _NL + '    sound_hdd_thread_end();' + _NL + '    hdd_audio_close();' + _NL),
    # timespec_get is in Android's C library from API 29 only, and the app runs from Android 8 (26):
    # clock_gettime gives the same clock (TIME_UTC is CLOCK_REALTIME) on every version.
    ('86box/src/video/vid_powervr_pcx.c',
     '    timespec_get(&ts, TIME_UTC);' + _NL,
     '    clock_gettime(CLOCK_REALTIME, &ts); /* KairoX86: timespec_get needs Android API 29 */' + _NL),
    # An Android app runs no host programs (the serial port's "run a command" mode opens a terminal
    # on a desktop): the command fails, which its caller reports, and posix_spawn (API 28) is not built.
    ('86box/src/unix/sdl_plat_unix.c',
     '    /* Execute command under a terminal emulator if requested. */' + _NL,
     '#ifdef __ANDROID__' + _NL
     + '    /* KairoX86: an Android app runs no host programs; the command fails, as its caller reports. */' + _NL
     + '    (void) cmd;' + _NL + '    (void) title;' + _NL + '    int ret = 0;' + _NL
     + '#else' + _NL
     + '    /* Execute command under a terminal emulator if requested. */' + _NL),
    ('86box/src/unix/sdl_plat_unix.c',
     '    if (new_env)' + _NL + '        free(new_env);' + _NL + '    return ret;' + _NL,
     '#endif' + _NL + '    if (new_env)' + _NL + '        free(new_env);' + _NL + '    return ret;' + _NL),
] + [
    ('86box/src/include/86box/version.h.in', line + _NL, line.replace('@CMAKE_PROJECT_', '@PROJECT_') + _NL)
    for line in (
        '#define EMU_NAME    "@CMAKE_PROJECT_NAME@"',
        '#define EMU_VERSION       "@CMAKE_PROJECT_VERSION@"',
        '#define EMU_VERSION_MAJ   @CMAKE_PROJECT_VERSION_MAJOR@',
        '#define EMU_VERSION_MIN   @CMAKE_PROJECT_VERSION_MINOR@',
        '#define EMU_VERSION_PATCH @CMAKE_PROJECT_VERSION_PATCH@',
        '# define EMU_ROMS_URL  "https://github.com/@CMAKE_PROJECT_NAME@/roms/releases/v@CMAKE_PROJECT_VERSION_MAJOR@'
        '.@CMAKE_PROJECT_VERSION_MINOR@" EMU_VERSION_ROMS_SUFFIX',
        '# define EMU_DOCS_URL  "https://86box.readthedocs.io/en/v@CMAKE_PROJECT_VERSION_MAJOR@'
        '.@CMAKE_PROJECT_VERSION_MINOR@/"',
        '# define EMU_ROMS_URL  "https://github.com/@CMAKE_PROJECT_NAME@/roms/releases/latest"',
    )
] + [
    ('86box/src/sound/CMakeLists.txt',
     'elseif(K9X_NULL_AUDIO)' + _NL + '    target_sources(snd PRIVATE null_audio.c)' + _NL,
     'elseif(KAIRO_FRONTEND)' + _NL + '    # KairoX86: its frontend takes the sound (core/kairo/).' + _NL
     + 'elseif(K9X_NULL_AUDIO)' + _NL + '    target_sources(snd PRIVATE null_audio.c)' + _NL),
    ('86box/src/unix/CMakeLists.txt',
     'add_library(plat OBJECT' + _NL + '    headless_main.c' + _NL + '    sdl_plat.c' + _NL + ')' + _NL,
     'add_library(plat OBJECT' + _NL + '    sdl_plat.c' + _NL + ')' + _NL
     + '# KairoX86: KAIRO_FRONTEND is the frontend in place of the headless program (core/kairo/).' + _NL
     + 'if(KAIRO_FRONTEND)' + _NL
     + '    target_sources(plat PRIVATE ${KAIRO_FRONTEND})' + _NL
     + 'else()' + _NL
     + '    target_sources(plat PRIVATE headless_main.c)' + _NL
     + 'endif()' + _NL),
]

# KairoX86#34: a machine that stops ends the game with its reason. Every CPU core's HLT that stays
# halted notes where (CPU_NOTE_HALT), so the frontend can tell a processor stopped with interrupts
# off (core/kairo/frontend.c) from one that is only waiting for its next interrupt.
KAIROX86_STOP = [
    ('86box/src/cpu/386_common.c',
     'K9X_HOT int cpu_halted  = 0;' + _NL,
     'K9X_HOT int cpu_halted  = 0;' + _NL
     + '/* KairoX86: the CS:IP of the last HLT any CPU core stayed halted on (CPU_NOTE_HALT). */' + _NL
     + 'uint16_t cpu_halt_cs   = 0;' + _NL
     + 'uint32_t cpu_halt_pc   = 0;' + _NL
     + 'int      cpu_halt_seen = 0;' + _NL),
    ('86box/src/cpu/cpu.h',
     'extern int cpu_halted;' + _NL,
     'extern int cpu_halted;' + _NL
     + '/* KairoX86: where a core\'s HLT stayed halted (386_common.c). A frontend reads it with the' + _NL
     + '   flags: a processor still on that HLT with interrupts off has stopped. */' + _NL
     + 'extern uint16_t cpu_halt_cs;' + _NL
     + 'extern uint32_t cpu_halt_pc;' + _NL
     + 'extern int      cpu_halt_seen;' + _NL
     + '#define CPU_NOTE_HALT()               \\' + _NL
     + '    do {                              \\' + _NL
     + '        cpu_halt_cs   = CS;           \\' + _NL
     + '        cpu_halt_pc   = cpu_state.pc; \\' + _NL
     + '        cpu_halt_seen = 1;            \\' + _NL
     + '    } while (0)' + _NL),
    ('86box/src/cpu/x86_ops_misc.h',
     '            cpu_halted = 1; /* an interrupt taken here returns past the HLT */' + _NL,
     '            cpu_halted = 1; /* an interrupt taken here returns past the HLT */' + _NL
     + '            CPU_NOTE_HALT(); /* KairoX86 */' + _NL),
    ('86box/src/cpu/808x.c',
     '                } else {' + _NL
     + '                    repeating = 1;' + _NL
     + '                    completed = 0;' + _NL
     + '                    clock_end();' + _NL
     + '                }' + _NL
     + '                break;' + _NL
     + '            case 0xf5:             /* CMC */' + _NL,
     '                } else {' + _NL
     + '                    repeating = 1;' + _NL
     + '                    completed = 0;' + _NL
     + '                    CPU_NOTE_HALT(); /* KairoX86 */' + _NL
     + '                    clock_end();' + _NL
     + '                }' + _NL
     + '                break;' + _NL
     + '            case 0xf5:             /* CMC */' + _NL),
    ('86box/src/cpu/vx0.c',
     '                halted    = 1;' + _NL
     + '            }' + _NL,
     '                halted    = 1;' + _NL
     + '                CPU_NOTE_HALT(); /* KairoX86 */' + _NL
     + '            }' + _NL),
    ('86box/src/cpu/808x_marty_86box.c',
     '    pfq_pos = (int) queue_effective_len(&icpu->biu.queue);' + _NL + '}' + _NL,
     '    pfq_pos = (int) queue_effective_len(&icpu->biu.queue);' + _NL
     + '    if (icpu->halted)' + _NL
     + '        CPU_NOTE_HALT(); /* KairoX86 */' + _NL
     + '}' + _NL),
]

# KairoX86#36: a seeded run repeats. The SN76489 (the PCjr's and Tandy's sound) seeded the C library's
# random numbers from the host's clock as it started, which also undid the run's seed for every other
# rand() (random_seed seeds both); its noise counters' start values now come from 86Box's own random
# numbers, as random as before in a normal run.
KAIROX86_REPEATABLE = [
    ('86box/src/sound/snd_sn76489.c',
     '#include <86box/plat_unused.h>' + _NL,
     '#include <86box/plat_unused.h>' + _NL
     + '#include <86box/random.h> /* KairoX86 */' + _NL),
    ('86box/src/sound/snd_sn76489.c',
     '    srand(time(NULL));' + _NL
     + '    sn76489->count[0] = 0;' + _NL
     + '    sn76489->count[1] = (rand() & 0x3FF) << 6;' + _NL
     + '    sn76489->count[2] = (rand() & 0x3FF) << 6;' + _NL
     + '    sn76489->count[3] = (rand() & 0x3FF) << 6;' + _NL,
     '    sn76489->count[0] = 0;' + _NL
     + '    for (int c = 1; c < 4; c++) /* KairoX86: 86Box\'s random numbers, seeded in a repeatable run */' + _NL
     + '        sn76489->count[c] = (((random_generate() << 8) | random_generate()) & 0x3FF) << 6;' + _NL),
]

# KairoX86#38: a build that draws every line in place (KAIROX86_SYNC_RENDER, tests only), to compare
# the threaded 8bpp renderer's pictures against.
KAIROX86_SYNC_RENDER = [
    ('86box/src/video/vid_svga.c',
     '        svga->render_async = !svga->overlay_on && !svga->dac_hwcursor_on && !svga->hwcursor_on;' + _NL,
     '#ifdef KAIROX86_SYNC_RENDER /* KairoX86#38: every line drawn in place, to compare against */' + _NL
     + '        svga->render_async = 0;' + _NL
     + '#else' + _NL
     + '        svga->render_async = !svga->overlay_on && !svga->dac_hwcursor_on && !svga->hwcursor_on;' + _NL
     + '#endif' + _NL),
]

# KairoX86#38: a frame's picture does not depend on how its drawing is split. The threaded 8bpp
# renderer (kairo9x-video) drew a queued line later from VRAM and the live palette, so a line showed
# what the guest wrote after it was scanned: palette changes and VRAM written behind the beam (the
# raster test, core/test/display) came out unlike drawing each line in place. A job now holds the
# line's VRAM bytes and the palette, taken as the guest scans the line; the drawing thread reads
# only those.
_F = '86box/src/video/vid_svga_render.c'
KAIROX86_RASTER = [
    (_F,
     'typedef struct render_job_t {' + _NL
     + '    uint32_t       *p;' + _NL
     + '    const uint8_t  *vram;' + _NL
     + '    const uint32_t *map8;' + _NL
     + '    uint32_t        memaddr;' + _NL
     + '    uint32_t        mask;' + _NL
     + '    uint32_t        dac;' + _NL
     + '    int             dwords;' + _NL
     + '} render_job_t;' + _NL
     + _NL
     + '#define RENDER_JOBS 4096 /* a power of 2, more lines than a frame has */' + _NL,
     '/* KairoX86#38: a job holds what its line reads, taken as the guest scans the line: the line\'s' + _NL
     + '   VRAM and the palette. Wider lines than RENDER_LINE_BYTES are drawn in place. */' + _NL
     + '#define RENDER_LINE_BYTES 2048' + _NL
     + _NL
     + 'typedef struct render_job_t {' + _NL
     + '    uint32_t *p;' + _NL
     + '    uint32_t  dac;' + _NL
     + '    int       dwords;' + _NL
     + '    uint32_t  map8[256];' + _NL
     + '    uint8_t   line[RENDER_LINE_BYTES];' + _NL
     + '} render_job_t;' + _NL
     + _NL
     + '#define RENDER_JOBS 2048 /* a power of 2, more lines than a frame has */' + _NL),
    (_F,
     '    uint32_t *p       = job->p;' + _NL
     + '    uint32_t  memaddr = job->memaddr;' + _NL
     + _NL
     + '    for (int c = 0; c < job->dwords; c++) {' + _NL
     + '        const uint32_t dat = *(const uint32_t *) &job->vram[memaddr & job->mask];' + _NL
     + _NL
     + '        memaddr = (memaddr + 4) & job->mask;' + _NL
     + '        p[0]    = job->map8[dat & job->dac];' + _NL,
     '    uint32_t *p = job->p;' + _NL
     + _NL
     + '    for (int c = 0; c < job->dwords; c++) {' + _NL
     + '        uint32_t dat;' + _NL
     + _NL
     + '        memcpy(&dat, &job->line[4 * c], 4);' + _NL
     + '        p[0]    = job->map8[dat & job->dac];' + _NL),
    (_F,
     'static void' + _NL
     + 'render_queue(const render_job_t *job)' + _NL
     + '{' + _NL
     + '    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);' + _NL,
     '/* The next job\'s slot, which the emulation thread fills before render_commit(). */' + _NL
     + 'static render_job_t *' + _NL
     + 'render_slot(void)' + _NL
     + '{' + _NL
     + '    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);' + _NL),
    (_F,
     '    if ((head - atomic_load_explicit(&render_tail, memory_order_acquire)) == RENDER_JOBS)' + _NL
     + '        svga_render_drain();' + _NL
     + '    /* A thread still drawing finds the job itself; one that found the queue' + _NL
     + '       empty is woken */' + _NL
     + '    const int was_empty = (head == atomic_load_explicit(&render_tail, memory_order_acquire));' + _NL
     + '    render_jobs[head & (RENDER_JOBS - 1)] = *job;' + _NL
     + '    atomic_store_explicit(&render_head, head + 1, memory_order_release);' + _NL,
     '    if ((head - atomic_load_explicit(&render_tail, memory_order_acquire)) == RENDER_JOBS)' + _NL
     + '        svga_render_drain();' + _NL
     + '    return &render_jobs[head & (RENDER_JOBS - 1)];' + _NL
     + '}' + _NL
     + _NL
     + '/* Queues the job render_slot() gave. */' + _NL
     + 'static void' + _NL
     + 'render_commit(void)' + _NL
     + '{' + _NL
     + '    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);' + _NL
     + '    /* A thread still drawing finds the job itself; one that found the queue' + _NL
     + '       empty is woken */' + _NL
     + '    const int was_empty = (head == atomic_load_explicit(&render_tail, memory_order_acquire));' + _NL
     + '    atomic_store_explicit(&render_head, head + 1, memory_order_release);' + _NL),
    (_F,
     '        if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8)) {' + _NL
     + '            const render_job_t job = { p, vram, map8, memaddr, mask, dac, svga->hdisp / 4 };' + _NL
     + _NL
     + '            render_queue(&job);' + _NL
     + '            memaddr = (memaddr + (4 * job.dwords)) & mask;' + _NL
     + '            p += 4 * job.dwords;' + _NL
     + '            x = 4 * job.dwords;' + _NL
     + '        }' + _NL,
     '        if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8) &&' + _NL
     + '            (svga->hdisp <= RENDER_LINE_BYTES)) {' + _NL
     + '            render_job_t *job    = render_slot();' + _NL
     + '            const int     dwords = svga->hdisp / 4;' + _NL
     + _NL
     + '            job->p      = p;' + _NL
     + '            job->dac    = dac;' + _NL
     + '            job->dwords = dwords;' + _NL
     + '            memcpy(job->map8, map8, sizeof(job->map8));' + _NL
     + '            for (int c = 0; c < dwords; c++) {' + _NL
     + '                memcpy(&job->line[4 * c], &vram[memaddr & mask], 4);' + _NL
     + '                memaddr = (memaddr + 4) & mask;' + _NL
     + '            }' + _NL
     + '            render_commit();' + _NL
     + '            p += 4 * dwords;' + _NL
     + '            x = 4 * dwords;' + _NL
     + '        }' + _NL),
]

# KairoX86#43: every INT n the guest runs goes past the frontend (kairo_observe_int, core/kairo/
# frontend.c), which counts the BIOS keyboard and mouse driver calls the Auto touch mode reads. One
# call in each processor's INT decoder: the 386 and later interpreters (the recompiler runs INT
# through them), the 8088, the cycle-exact 8088 and the NEC V20/V30.
KAIROX86_GUEST_INPUT = [
    ('86box/src/cpu/cpu.h',
     'extern void x86_int_sw(int num);' + _NL,
     'extern void x86_int_sw(int num);' + _NL
     + '/* KairoX86#43, #44, #46: the guest runs INT num from code at linear code_base, with DS at data_base; the frontend may change' + _NL
     + '   the call through its registers (core/kairo/frontend.c). */' + _NL
     + 'extern void kairo_observe_int(uint8_t num, uint16_t *ax, uint16_t *bx, uint16_t *cx, uint16_t *dx, uint32_t code_base, uint32_t data_base);' + _NL),
    ('86box/src/cpu/x86_ops_int.h',
     '    uint8_t temp = getbytef();' + _NL,
     '    uint8_t temp = getbytef();' + _NL
     + '    kairo_observe_int(temp, &AX, &BX, &CX, &DX, cpu_state.seg_cs.base, cpu_state.seg_ds.base); /* KairoX86#43 */' + _NL),
    ('86box/src/cpu/808x.c',
     '                interrupt(pfq_fetchb());' + _NL,
     '                temp = pfq_fetchb();' + _NL
     + '                kairo_observe_int(temp, &AX, &BX, &CX, &DX, cpu_state.seg_cs.base, cpu_state.seg_ds.base); /* KairoX86#43 */' + _NL
     + '                interrupt(temp);' + _NL),
    ('86box/src/cpu/808x_marty_86box.c',
     '            const uint8_t vector = queue_read(icpu, false);' + _NL
     + '            software_interrupt(icpu, vector);' + _NL,
     '            const uint8_t vector = queue_read(icpu, false);' + _NL
     + '            kairo_observe_int(vector, &AX, &BX, &CX, &DX, (uint32_t) icpu->segs[SEG_CS] << 4, (uint32_t) icpu->segs[SEG_DS] << 4); /* KairoX86#43 */' + _NL
     + '            software_interrupt(icpu, vector);' + _NL),
    ('86box/src/cpu/vx0.c',
     '            temp = biu_pfq_fetchb();' + _NL
     + '            do_cycle_i();' + _NL
     + '            sw_int(temp);' + _NL,
     '            temp = biu_pfq_fetchb();' + _NL
     + '            kairo_observe_int(temp, &AX, &BX, &CX, &DX, cpu_state.seg_cs.base, cpu_state.seg_ds.base); /* KairoX86#43 */' + _NL
     + '            do_cycle_i();' + _NL
     + '            sw_int(temp);' + _NL),
]

# KairoX86#37: the core hands the host the machine's own pixels: a card that draws each pixel twice
# across (VGA's 320-wide and 40-column modes, CGA's) or each line twice (CGA's line doubling for a
# 400-line window) says so on its monitor, and the frontend keeps one of each.
KAIROX86_NATIVE_SIZE = [
    ('86box/src/include/86box/video.h',
     '    int                      mon_bpp;' + _NL,
     '    int                      mon_bpp;' + _NL
     + '    /* KairoX86#37: the last frame repeats each pixel this many times across, and each line this' + _NL
     + '       many times down (0 or 1: once); the frontend keeps one of each. */' + _NL
     + '    int                      mon_kairo_x_div;' + _NL
     + '    int                      mon_kairo_y_div;' + _NL
     + '    uintptr_t                mon_kairo_render; /* the renderer at the end of the last frame (vid_svga.c) */' + _NL),
    ('86box/src/video/vid_svga.c',
     '    video_blit_memtoscreen_monitor(x_start, y_start, svga->monitor->mon_xsize + x_add, svga->monitor->mon_ysize + y_add, svga->monitor_index);' + _NL
     + _NL
     + '    if (svga->vertical_linedbl)' + _NL,
     '    /* KairoX86#37: the renderers that draw each pixel twice across, unless a cursor, overlay or' + _NL
     + '       accelerator draws over them at full width this frame, or the frame began with another renderer' + _NL
     + '       (a mode set during it: the same renderer must have ended the last frame too). */' + _NL
     + '    svga->monitor->mon_kairo_x_div = (!svga->override && (svga->monitor->mon_kairo_render == (uintptr_t) svga->render) && !svga->hwcursor_on && !svga->dac_hwcursor_on && !svga->overlay_on' + _NL
     + '                                      && ((svga->render == svga_render_text_40) || (svga->render == svga_render_2bpp_lowres)' + _NL
     + '                                          || (svga->render == svga_render_4bpp_lowres) || (svga->render == svga_render_8bpp_lowres)' + _NL
     + '                                          || (svga->render == svga_render_15bpp_lowres) || (svga->render == svga_render_15bpp_mix_lowres)' + _NL
     + '                                          || (svga->render == svga_render_16bpp_lowres) || (svga->render == svga_render_24bpp_lowres)' + _NL
     + '                                          || (svga->render == svga_render_32bpp_lowres)' + _NL
     + '                                          || (svga->render == svga_render_2bpp_s3_lowres) || (svga->render == svga_render_8bpp_tseng_lowres))) ? 2 : 1;' + _NL
     + '    svga->monitor->mon_kairo_y_div = 1;' + _NL
     + '    svga->monitor->mon_kairo_render = (uintptr_t) svga->render;' + _NL
     + '    video_blit_memtoscreen_monitor(x_start, y_start, svga->monitor->mon_xsize + x_add, svga->monitor->mon_ysize + y_add, svga->monitor_index);' + _NL
     + _NL
     + '    if (svga->vertical_linedbl)' + _NL),
    ('86box/src/video/vid_cga.c',
     '                        cga_do_blit(xsize, cga->firstline, cga->lastline, cga->double_type);' + _NL,
     '                        /* KairoX86#37: 40-column text and the 320-wide graphics draw each pixel twice across' + _NL
     + '                           (composite colour is worked out per dot, so it stays whole), and line doubling draws' + _NL
     + '                           each line twice, the second interpolated or not: the even lines are the card\'s. */' + _NL
     + '                        monitors[monitor_index_global].mon_kairo_x_div = (!cga->composite && (!(cga->cgamode & CGA_MODE_FLAG_GRAPHICS)' + _NL
     + '                            ? !(cga->cgamode & CGA_MODE_FLAG_HIGHRES) : !(cga->cgamode & CGA_MODE_FLAG_HIGHRES_GRAPHICS))) ? 2 : 1;' + _NL
     + '                        monitors[monitor_index_global].mon_kairo_y_div = (cga->double_type > DOUBLE_NONE) ? 2 : 1;' + _NL
     + '                        cga_do_blit(xsize, cga->firstline, cga->lastline, cga->double_type);' + _NL),
]

# KairoX86#186: a machine owns what it maps. The platform files' mappings become plat_mmap_os and
# plat_munmap_os, which the frontend's plat_mmap and plat_munmap call, recording each mapping; the
# machine's close releases what 86Box left mapped (the recompiler's pool and tables among it).
KAIROX86_OWN_MEMORY = [
    ('86box/src/unix/sdl_plat_unix.c',
     'void *' + _NL + 'plat_mmap(size_t size, uint8_t executable, uint8_t* large)' + _NL,
     '/* KairoX86#186: the frontend\'s plat_mmap records the mapping (core/kairo/frontend.c). */' + _NL
     + 'void *' + _NL + 'plat_mmap_os(size_t size, uint8_t executable, uint8_t* large)' + _NL),
    ('86box/src/unix/sdl_plat_unix.c',
     'void' + _NL + 'plat_munmap(void *ptr, size_t size)' + _NL,
     'void' + _NL + 'plat_munmap_os(void *ptr, size_t size)' + _NL),
    ('86box/src/unix/sdl_plat_win.c',
     'void *' + _NL + 'plat_mmap(size_t size, uint8_t executable, uint8_t* large)' + _NL,
     '/* KairoX86#186: the frontend\'s plat_mmap records the mapping (core/kairo/frontend.c). */' + _NL
     + 'void *' + _NL + 'plat_mmap_os(size_t size, uint8_t executable, uint8_t* large)' + _NL),
    ('86box/src/unix/sdl_plat_win.c',
     'void' + _NL + 'plat_munmap(void *ptr, UNUSED(size_t size))' + _NL,
     'void' + _NL + 'plat_munmap_os(void *ptr, UNUSED(size_t size))' + _NL),
]

# KairoX86#192: add_path (src/mem/rom.c) appends a relative ROM folder to the working folder in place,
# with the same buffer as destination and first part: path_append_filename copies it only when they differ.
KAIROX86_PATH_APPEND = [
    ('86box/src/unix/sdl_plat.c',
     'path_append_filename(char *dest, const char *s1, const char *s2)' + _NL + '{' + _NL + '    strcpy(dest, s1);' + _NL,
     'path_append_filename(char *dest, const char *s1, const char *s2)' + _NL + '{' + _NL
     + '    if (dest != s1) /* KairoX86#192: a copy onto itself is undefined */' + _NL
     + '        strcpy(dest, s1);' + _NL),
]

# KairoX86#190: the PS/2, serial and bus mice tell the frontend when the guest turns their reports on
# or off, so it can tell a protected-mode driver (Windows) setting the mouse up from a DOS driver.
KAIROX86_MOUSE_ENABLE = [
    ('86box/src/include/86box/mouse.h',
     'extern void            mouse_reset(void);\n',
     "extern void            mouse_reset(void);\n/* KairoX86#190: the guest turned the mouse's reports on (1) or off (0); the frontend notes whether a\n   protected-mode driver did it (core/kairo/frontend.c). */\nextern void            kairo_observe_mouse_enable(int enabled);\n"),
    ('86box/src/device/mouse_ps2.c',
     '                mouse_ps2_log("%s: Enable\\n", dev->name);\n                mouse_scan = 1;\n',
     '                mouse_ps2_log("%s: Enable\\n", dev->name);\n                mouse_scan = 1;\n                kairo_observe_mouse_enable(1); /* KairoX86#190 */\n'),
    ('86box/src/device/mouse_ps2.c',
     '                mouse_ps2_log("%s: Disable\\n", dev->name);\n                mouse_scan = 0;\n',
     '                mouse_ps2_log("%s: Disable\\n", dev->name);\n                mouse_scan = 0;\n                kairo_observe_mouse_enable(0); /* KairoX86#190 */\n'),
    ('86box/src/device/mouse_ps2.c',
     '                mouse_ps2_log("%s: Reset\\n", dev->name);\n                kbc_at_dev_reset(dev, 1);\n',
     '                mouse_ps2_log("%s: Reset\\n", dev->name);\n                kbc_at_dev_reset(dev, 1);\n                kairo_observe_mouse_enable(0); /* KairoX86#190: a reset mouse reports nothing until enabled */\n'),
    ('86box/src/device/mouse_serial.c',
     '    sermouse_reset(dev, 1);\n\n    memcpy(dev->buf, dev->id, dev->id_len);\n',
     '    sermouse_reset(dev, 1);\n    kairo_observe_mouse_enable(1); /* KairoX86#190: a driver powers the mouse up by RTS */\n\n    memcpy(dev->buf, dev->id, dev->id_len);\n'),
    ('86box/src/device/mouse_bus.c',
     '            if (!(val & DISABLE_IRQ))\n                dev->flags |= FLAG_TIMER_INT;\n            else\n                dev->flags &= ~FLAG_TIMER_INT;\n',
     '            if (!(val & DISABLE_IRQ))\n                dev->flags |= FLAG_TIMER_INT;\n            else\n                dev->flags &= ~FLAG_TIMER_INT;\n            kairo_observe_mouse_enable(!(val & DISABLE_IRQ)); /* KairoX86#190 */\n'),
    ('86box/src/device/mouse_bus.c',
     '                    if (val & INP_ENABLE_DATA_IRQ)\n                        dev->flags |= FLAG_DATA_INT;\n                    else\n                        dev->flags &= ~FLAG_DATA_INT;\n',
     '                    if (val & INP_ENABLE_DATA_IRQ)\n                        dev->flags |= FLAG_DATA_INT;\n                    else\n                        dev->flags &= ~FLAG_DATA_INT;\n                    kairo_observe_mouse_enable((val & (INP_ENABLE_TIMER_IRQ | INP_ENABLE_DATA_IRQ)) != 0); /* KairoX86#190 */\n'),
]

# KairoX86#200: the recompiler's free list is built lazily: blocks are handed out in the order the
# whole list gave them, each with the link generation adding it gave it, so starting a machine and
# resetting it touch only the blocks that were used.
KAIROX86_LAZY_BLOCKS = [
    ('86box/src/codegen/codegen_block.c',
     'static uint32_t block_free_list;\n',
     'static uint32_t block_free_list;\n/*KairoX86#200: building the free list touched every block and its link slots, though most are\n  never used. Blocks 1..block_fresh_top have not been handed out since the list was last built and\n  hold what adding them left: zeroes, and the link generation block_fresh_gen + their number when\n  block_fresh_gen_set. They are handed out from the top down once the blocks freed since are used\n  up, as the list would have given them. Below block_touched_low no block was ever written.*/\nstatic uint32_t block_fresh_top;\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\nstatic uint32_t block_fresh_gen;\nstatic int      block_fresh_gen_set;\n#endif\nstatic uint32_t block_touched_low = BLOCK_SIZE;\n'),
    ('86box/src/codegen/codegen_block.c',
     'void\ncodegen_link_reset(void)\n{\n    memset(codegen_link_slots, 0, sizeof(codegen_link_slots));\n    memset(link_in_head, 0, sizeof(link_in_head));\n}\n',
     "void\ncodegen_link_reset(void)\n{\n    memset(codegen_link_slots, 0, sizeof(codegen_link_slots));\n    memset(link_in_head, 0, sizeof(link_in_head));\n}\n\n/*codegen_link_reset for the blocks ever used (block 0 and block_touched_low up, KairoX86#200): the\n  others' slots were never written.*/\nstatic void\ncodegen_link_reset_used(void)\n{\n    memset(codegen_link_slots[0], 0, sizeof(codegen_link_slots[0]));\n    if (block_touched_low < BLOCK_SIZE)\n        memset(codegen_link_slots[block_touched_low], 0, (BLOCK_SIZE - block_touched_low) * sizeof(codegen_link_slots[0]));\n    memset(link_in_head, 0, sizeof(link_in_head));\n}\n"),
    ('86box/src/codegen/codegen_block.c',
     '        codegen_link_reset();\n        for (int c = 0; c < BLOCK_SIZE; c++)\n            codeblock[c].link_gen = ++link_gen_last;\n',
     '        codegen_link_reset();\n        for (int c = 0; c < BLOCK_SIZE; c++)\n            codeblock[c].link_gen = ++link_gen_last;\n        /*KairoX86#200: the blocks not handed out keep these numbers, and every block was written.*/\n        block_fresh_gen_set = 0;\n        block_touched_low   = 1;\n'),
    ('86box/src/codegen/codegen_block.c',
     'static void\nblock_dirty_list_add(codeblock_t *block)\n',
     "/*The free list of blocks 1 up, after block 0 was added (which leaves the list empty: its 0 is the\n  list's end), as adding each in turn would make it (KairoX86#200): the blocks are handed out as\n  taken, and get the link generation adding them would have given them then.*/\nstatic void\nblock_free_list_build(void)\n{\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    if (codegen_block_link && (link_gen_last > UINT32_MAX - BLOCK_SIZE)) {\n        /*The generations would wrap while adding them: add every block, the wrap with it.*/\n        block_fresh_top = 0;\n        for (uint32_t c = 1; c < BLOCK_SIZE; c++)\n            block_free_list_add(&codeblock[c]);\n        return;\n    }\n    block_fresh_gen_set = codegen_block_link;\n    block_fresh_gen     = link_gen_last;\n    if (codegen_block_link)\n        link_gen_last += BLOCK_SIZE - 1;\n#endif\n    block_fresh_top = BLOCK_SIZE - 1;\n}\n\nstatic void\nblock_dirty_list_add(codeblock_t *block)\n"),
    ('86box/src/codegen/codegen_block.c',
     '    codeblock_t *block = NULL;\n\n    while (!block_free_list) {\n',
     '    codeblock_t *block = NULL;\n\n    if (!block_free_list && block_fresh_top) {\n        const uint32_t c = block_fresh_top--;\n\n        if (c < block_touched_low)\n            block_touched_low = c;\n        block = &codeblock[c];\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n        if (block_fresh_gen_set)\n            block->link_gen = block_fresh_gen + c;\n#endif\n        return block;\n    }\n    while (!block_free_list) {\n'),
    ('86box/src/codegen/codegen_block.c',
     '    block_free_list = 0;\n    for (uint32_t c = 0; c < BLOCK_SIZE; c++)\n        block_free_list_add(&codeblock[c]);\n    block_dirty_list_head = block_dirty_list_tail = 0;\n    dirty_list_size                               = 0;\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    codegen_link_reset();\n#endif\n',
     '    block_free_list = 0;\n    block_free_list_add(&codeblock[0]);\n    block_free_list_build();\n    block_dirty_list_head = block_dirty_list_tail = 0;\n    dirty_list_size                               = 0;\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    codegen_link_reset_used();\n#endif\n'),
    ('86box/src/codegen/codegen_block.c',
     '    for (c = 1; c < BLOCK_SIZE; c++) {\n        codeblock_t *block = &codeblock[c];\n\n        if (block->valid) {\n            block->phys   = 0;\n            block->phys_2 = 0;\n            delete_block(block);\n        }\n    }\n\n    memset(codeblock, 0, BLOCK_SIZE * sizeof(codeblock_t));\n    memset(codeblock_hash, 0, HASH_SIZE * sizeof(uint32_t));\n    mem_reset_page_blocks();\n\n    block_free_list = 0;\n    for (c = 0; c < BLOCK_SIZE; c++) {\n        codeblock[c].valid = 0;\n        block_free_list_add(&codeblock[c]);\n    }\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    codegen_link_reset();\n',
     '    /*Only blocks ever handed out were written (KairoX86#200): block 0 and block_touched_low up.*/\n    const uint32_t low = block_touched_low;\n\n    for (c = (low > 1) ? low : 1; c < BLOCK_SIZE; c++) {\n        codeblock_t *block = &codeblock[c];\n\n        if (block->valid) {\n            block->phys   = 0;\n            block->phys_2 = 0;\n            delete_block(block);\n        }\n    }\n\n    memset(&codeblock[0], 0, sizeof(codeblock_t));\n    if (low < BLOCK_SIZE)\n        memset(&codeblock[low], 0, (BLOCK_SIZE - low) * sizeof(codeblock_t));\n    memset(codeblock_hash, 0, HASH_SIZE * sizeof(uint32_t));\n    mem_reset_page_blocks();\n\n    block_free_list = 0;\n    block_free_list_add(&codeblock[0]);\n    /*What adding the blocks ever used did for their versions, in the same order; the others have none.*/\n    for (c = (low > 1) ? low : 1; c < BLOCK_SIZE; c++)\n        block_versions_free_all(c);\n    block_free_list_build();\n#ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n    codegen_link_reset_used();\n'),
]

# KairoX86#200: mem_reset_page_blocks skips writing a page table that is as it would leave it (just
# filled by mem_reset and untouched since): a 386's table covers 4 GB, and every start wrote it twice.
KAIROX86_PAGES_AS_RESET = [
    ('86box/src/include/86box/mem.h',
     'extern void mem_reset_page_blocks(void);\n',
     "extern void mem_reset_page_blocks(void);\n/* KairoX86#200: whether every page's write handlers and code blocks are as mem_reset_page_blocks\n   leaves them, so it need not write them again. */\nextern int  mem_pages_as_reset;\n"),
    ('86box/src/mem/mem.c',
     'page_t  *pages;       /* RAM page table */\n',
     'page_t  *pages;       /* RAM page table */\nint      mem_pages_as_reset = 0;\n'),
    ('86box/src/mem/mem.c',
     '        pages[c].byte_code_present_mask = &byte_code_present_mask[c * 64];\n    }\n\n    memset(_mem_exec, 0x00, sizeof(_mem_exec));\n',
     '        pages[c].byte_code_present_mask = &byte_code_present_mask[c * 64];\n    }\n    /* KairoX86#200: as mem_reset_page_blocks leaves them: the RAM handlers, no blocks (calloc). */\n    mem_pages_as_reset = 1;\n\n    memset(_mem_exec, 0x00, sizeof(_mem_exec));\n'),
    ('86box/src/mem/mem.c',
     'mem_reset_page_blocks(void)\n{\n    if (pages == NULL)\n        return;\n\n',
     "mem_reset_page_blocks(void)\n{\n    if (pages == NULL)\n        return;\n    /* KairoX86#200: a 386's table covers 4 GB; writing it again when it is already so faulted in\n       and cleared its 100 MB a second time on every start. */\n    if (mem_pages_as_reset)\n        return;\n\n"),
    ('86box/src/mem/mem.c',
     '        pages[c].head    = BLOCK_INVALID;\n    }\n}\n',
     '        pages[c].head    = BLOCK_INVALID;\n    }\n    mem_pages_as_reset = 1;\n}\n'),
    ('86box/src/mem/mem.c',
     '    for (c = ((start * 1024) >> 12); c < (((start + size) * 1024) >> 12); c++) {\n',
     '    mem_pages_as_reset = 0; /* KairoX86#200 */\n    for (c = ((start * 1024) >> 12); c < (((start + size) * 1024) >> 12); c++) {\n'),
    ('86box/src/mem/mem.c',
     '    for (c = 0xa0; c < 0xf0; c++) {\n        if ((c >= 0xc0) && (c <= 0xcf))\n            continue;\n',
     '    mem_pages_as_reset = 0; /* KairoX86#200 */\n    for (c = 0xa0; c < 0xf0; c++) {\n        if ((c >= 0xc0) && (c <= 0xcf))\n            continue;\n'),
    ('86box/src/machine/m_ps2_mca.c',
     '    for (c = (start >> 12); c < ((start + (size << 10)) >> 12); c++) {\n        const uint32_t offset = c - (start >> 12);\n',
     '    mem_pages_as_reset = 0; /* KairoX86#200 */\n    for (c = (start >> 12); c < ((start + (size << 10)) >> 12); c++) {\n        const uint32_t offset = c - (start >> 12);\n'),
    ('86box/src/codegen/codegen_block.c',
     '    codeblock_t *block = NULL;\n\n    if (!block_free_list && block_fresh_top) {\n',
     '    codeblock_t *block = NULL;\n\n    /*A block taken is put on its pages (KairoX86#200).*/\n    mem_pages_as_reset = 0;\n    if (!block_free_list && block_fresh_top) {\n'),
]

KAIROX86_LAZY_PIT = [
    ('86box/src/include/86box/pit.h',
     '    uint64_t   pit_const;\n',
     '    uint64_t   pit_const;\n\n    /* KairoX86#199: the halves the timer skips to its next edge that is more than a count down\n       (0: the next half), the clock before them, and how each counter counts on them (pit.c). */\n    uint32_t   skip_halves;\n    int        skip_clock;\n    uint8_t    skip_kind[NUM_COUNTERS];\n'),
    ('86box/src/pit.c',
     'void\nctr_clock(void *data, int counter_id)\n{\n    pit_t *pit = (pit_t *) data;\n',
     "/* KairoX86#199: the timer runs the counters a half clock at a time, about 2.4 million calls a\n   second on a PC, though between the edges where a counter's output or state changes its edges\n   only count down. pit_schedule sends the timer straight to the first edge any counter does more\n   on (dev->skip_halves halves on), and the edges in between are counted down at once: there\n   (pit_timer_over), or as far as the CPU has run (pit_catch_up) before anything reads or changes\n   a counter. 86Box runs every timer whose time is at or before tsc as tsc moves (the 808x's\n   clock_end), so the edges counted are the ones it would have run by then, edge for edge. */\n#define PIT_PLAIN_MAX  0x10000u\n#define PIT_PLAIN_NONE 0 /* the edge leaves the counter as it is */\n#define PIT_PLAIN_DEC  1 /* ctr_decrease_count, binary */\n#define PIT_PLAIN_DEC2 2 /* the square wave's count by two */\n\n/* How many of the counter's next falling edges only count it down, as [kind]: ctr_tick's cases,\n   each as long as it neither changes the output or state nor reaches the count that does. */\nstatic uint32_t\nctr_plain_ticks(const ctr_t *ctr, uint8_t *kind)\n{\n    *kind = PIT_PLAIN_NONE;\n    if (ctr->clock_div > 1)\n        return 0;\n    /* The timer only sets the clock of a counter it does not drive. */\n    if (!ctr->using_timer)\n        return PIT_PLAIN_MAX;\n    if (ctr->latch || ctr->bcd || ((ctr->state & 0x03) == 0x01))\n        return 0;\n\n    switch (ctr->m & 0x07) {\n        case 0:\n            if ((ctr->state == 2) && ctr->gate && (ctr->count >= 1)) {\n                *kind = PIT_PLAIN_DEC;\n                return (uint32_t) (ctr->count - 1);\n            }\n            if (ctr->state == 3)\n                *kind = PIT_PLAIN_DEC;\n            return PIT_PLAIN_MAX;\n        case 1:\n            if ((ctr->state == 2) && (ctr->count >= 1)) {\n                *kind = PIT_PLAIN_DEC;\n                return (uint32_t) (ctr->count - 1);\n            }\n            if ((ctr->state == 3) || (ctr->state == 6))\n                *kind = PIT_PLAIN_DEC;\n            return PIT_PLAIN_MAX;\n        case 2:\n        case 6:\n            if (ctr->state == 3)\n                return 0;\n            if ((ctr->state == 2) && ctr->gate && (ctr->count >= 2)) {\n                *kind = PIT_PLAIN_DEC;\n                return (uint32_t) (ctr->count - 2);\n            }\n            return PIT_PLAIN_MAX;\n        case 3:\n        case 7:\n            if (((ctr->state != 2) && (ctr->state != 3)) || !ctr->gate || (ctr->count < 0))\n                return PIT_PLAIN_MAX;\n            /* The first count after a load, and an odd count, take their own edges. */\n            if (ctr->newcount || (ctr->count & 1) || (ctr->count == 0))\n                return 0;\n            *kind = PIT_PLAIN_DEC2;\n            return (uint32_t) (ctr->count / 2 - 1);\n        case 4:\n        case 5:\n            if ((ctr->gate == 0) && (ctr->m == 4))\n                return PIT_PLAIN_MAX;\n            switch (ctr->state) {\n                case 0:\n                    if (!ctr->null_count)\n                        *kind = PIT_PLAIN_DEC;\n                    return PIT_PLAIN_MAX;\n                case 6:\n                    *kind = PIT_PLAIN_DEC;\n                    return PIT_PLAIN_MAX;\n                case 2:\n                    if (ctr->count >= 1) {\n                        *kind = PIT_PLAIN_DEC;\n                        return (uint32_t) (ctr->count - 1);\n                    }\n                    return PIT_PLAIN_MAX;\n                case 3:\n                    return 0;\n                default:\n                    return PIT_PLAIN_MAX;\n            }\n        default:\n            return PIT_PLAIN_MAX;\n    }\n}\n\n/* The first [halves] edges of the skip: each counter counted down by the falling edges among them,\n   and every clock where the last of them left it. */\nstatic void\npit_skip_apply(pit_t *dev, uint32_t halves)\n{\n    const int32_t falls = (int32_t) (dev->skip_clock ? ((halves + 1) >> 1) : (halves >> 1));\n    const int     clock = dev->skip_clock ^ (int) (halves & 1);\n\n    for (uint8_t i = 0; i < NUM_COUNTERS; i++) {\n        ctr_t *ctr = &dev->counters[i];\n\n        if (dev->skip_kind[i] == PIT_PLAIN_DEC)\n            ctr->count = (ctr->count - falls) & 0xffff;\n        else if (dev->skip_kind[i] == PIT_PLAIN_DEC2)\n            ctr->count -= 2 * falls;\n        ctr->clock = clock;\n    }\n    dev->clock = clock;\n}\n\n/* The timer's next edge, after the one it ran: half a clock on, or the first edge past every\n   counter's plain ones. */\nstatic void\npit_schedule(pit_t *dev)\n{\n    const uint64_t half  = dev->pit_const >> 1ULL;\n    uint32_t       falls = PIT_PLAIN_MAX;\n    uint8_t        kind[NUM_COUNTERS];\n\n    for (uint8_t i = 0; i < NUM_COUNTERS; i++) {\n        const uint32_t plain = ctr_plain_ticks(&dev->counters[i], &kind[i]);\n        if (plain < falls)\n            falls = plain;\n    }\n\n    if (falls < 2) {\n        timer_advance_u64(&dev->callback_timer, half);\n        return;\n    }\n\n    /* After a rising edge the next is a falling one: the skip ends on the falling edge after the\n       plain ones, which pit_timer_over runs as it would. */\n    dev->skip_halves = 2 * falls + (dev->clock ? 1 : 2);\n    dev->skip_clock  = dev->clock;\n    for (uint8_t i = 0; i < NUM_COUNTERS; i++)\n        dev->skip_kind[i] = kind[i];\n    timer_advance_u64(&dev->callback_timer, half * dev->skip_halves);\n}\n\n/* The skipped edges up to tsc, counted down, and the timer back on the next edge, before anything\n   reads or changes a counter. */\nstatic void\npit_catch_up(pit_t *dev)\n{\n    if (!dev->skip_halves)\n        return;\n\n    pc_timer_t       *timer   = &dev->callback_timer;\n    const uint64_t    half    = dev->pit_const >> 1ULL;\n    const uint32_t    halves  = dev->skip_halves;\n    const __uint128_t landing = ((__uint128_t) timer->ts_integer << 32) | timer->ts_frac;\n    const __uint128_t due     = (__uint128_t) ((uint64_t) tsc + 1ULL) << 32;\n    uint32_t          done;\n\n    /* Edge h is at landing - (halves - h) * half; it has run once its whole part is at or before tsc. */\n    if (landing < due)\n        done = halves - 1;\n    else {\n        const __uint128_t ahead = (landing - due) / half;\n        done = (ahead + 1 >= halves) ? 0 : (uint32_t) (halves - 1 - ahead);\n    }\n\n    pit_skip_apply(dev, done);\n    dev->skip_halves = 0;\n\n    const __uint128_t next = landing - (__uint128_t) (halves - done - 1) * half;\n    timer_disable(timer);\n    timer->ts_integer = (uint64_t) (next >> 32);\n    timer->ts_frac    = (uint32_t) next;\n    timer_enable(timer);\n}\n\nvoid\nctr_clock(void *data, int counter_id)\n{\n    pit_t *pit = (pit_t *) data;\n"),
    ('86box/src/pit.c',
     '    pit_t *pit = (pit_t *) data;\n    ctr_t *ctr = &pit->counters[counter_id];\n\n    int     old  = ctr->gate;\n',
     '    pit_t *pit = (pit_t *) data;\n    pit_catch_up(pit);\n    ctr_t *ctr = &pit->counters[counter_id];\n\n    int     old  = ctr->gate;\n'),
    ('86box/src/pit.c',
     "        } else if (old && !ctr->clock)\n            ctr_tick(ctr, pit);\n    }\n}\n\nvoid\npit_ctr_set_clock(ctr_t *ctr, int clock, void *priv)\n{\n    pit_ctr_set_clock_common(ctr, clock, priv);\n}\n\nvoid\npit_ctr_set_using_timer(void *data, int counter_id, int using_timer)\n{\n    if (tsc > 0)\n        timer_process();\n    pit_t *pit       = (pit_t *) data;\n    ctr_t *ctr       = &pit->counters[counter_id];\n    ctr->using_timer = using_timer;\n}\n\nstatic void\npit_timer_over(void *priv)\n{\n    pit_t *dev = (pit_t *) priv;\n\n    dev->clock ^= 1;\n\n    for (uint8_t i = 0; i < NUM_COUNTERS; i++) {\n        ctr_t *ctr = &dev->counters[i];\n\n        /* A divided counter sees one edge in every clock_div of the\n           timer's, and so a clock clock_div times slower. */\n        if (ctr->clock_div > 1) {\n            if (++ctr->clock_phase < ctr->clock_div)\n                continue;\n            ctr->clock_phase = 0;\n            pit_ctr_set_clock_common(ctr, !ctr->clock, dev);\n        } else\n            pit_ctr_set_clock_common(ctr, dev->clock, dev);\n    }\n\n    timer_advance_u64(&dev->callback_timer, dev->pit_const >> 1ULL);\n}\n",
     "        } else if (old && !ctr->clock)\n            ctr_tick(ctr, pit);\n    }\n}\n\nvoid\npit_ctr_set_clock(ctr_t *ctr, int clock, void *priv)\n{\n    pit_catch_up((pit_t *) priv);\n    pit_ctr_set_clock_common(ctr, clock, priv);\n}\n\nvoid\npit_ctr_set_using_timer(void *data, int counter_id, int using_timer)\n{\n    if (tsc > 0)\n        timer_process();\n    pit_t *pit       = (pit_t *) data;\n    pit_catch_up(pit);\n    ctr_t *ctr       = &pit->counters[counter_id];\n    ctr->using_timer = using_timer;\n}\n\nstatic void\npit_timer_over(void *priv)\n{\n    pit_t *dev = (pit_t *) priv;\n\n    /* The skip's plain edges, before the one it ends on. */\n    if (dev->skip_halves) {\n        pit_skip_apply(dev, dev->skip_halves - 1);\n        dev->skip_halves = 0;\n    }\n\n    dev->clock ^= 1;\n\n    for (uint8_t i = 0; i < NUM_COUNTERS; i++) {\n        ctr_t *ctr = &dev->counters[i];\n\n        /* A divided counter sees one edge in every clock_div of the\n           timer's, and so a clock clock_div times slower. */\n        if (ctr->clock_div > 1) {\n            if (++ctr->clock_phase < ctr->clock_div)\n                continue;\n            ctr->clock_phase = 0;\n            pit_ctr_set_clock_common(ctr, !ctr->clock, dev);\n        } else\n            pit_ctr_set_clock_common(ctr, dev->clock, dev);\n    }\n\n    pit_schedule(dev);\n}\n"),
    ('86box/src/pit.c',
     'static void\npit_write(uint16_t addr, uint8_t val, void *priv)\n{\n    pit_t *dev = (pit_t *) priv;\n    int    t   = (addr & 3);\n    ctr_t *ctr;\n',
     'static void\npit_write(uint16_t addr, uint8_t val, void *priv)\n{\n    pit_t *dev = (pit_t *) priv;\n    int    t   = (addr & 3);\n    ctr_t *ctr;\n\n    pit_catch_up(dev);\n'),
    ('86box/src/pit.c',
     'pit_read(uint16_t addr, void *priv)\n{\n    pit_t  *dev = (pit_t *) priv;\n    uint8_t ret = 0xff;\n    int     count;\n    int     t = (addr & 3);\n    ctr_t  *ctr;\n',
     'pit_read(uint16_t addr, void *priv)\n{\n    pit_t  *dev = (pit_t *) priv;\n    uint8_t ret = 0xff;\n    int     count;\n    int     t = (addr & 3);\n    ctr_t  *ctr;\n\n    pit_catch_up(dev);\n'),
    ('86box/src/pit.c',
     'pit_device_reset(pit_t *dev)\n{\n    dev->clock = 0;\n\n',
     'pit_device_reset(pit_t *dev)\n{\n    pit_catch_up(dev);\n    dev->clock = 0;\n\n'),
    ('86box/src/pit.c',
     '    dev->counters[2].gate = 0;\n}\n\nvoid\npit_handler(int set, uint16_t base, int size, void *priv)\n{\n    io_handler(set, base, size, pit_read, NULL, NULL, pit_write, NULL, NULL, priv);\n}\n\nvoid\npit_set_pit_const(void *data, uint64_t pit_const)\n{\n    pit_t *pit = (pit_t *) data;\n\n',
     '    dev->counters[2].gate = 0;\n}\n\nvoid\npit_handler(int set, uint16_t base, int size, void *priv)\n{\n    io_handler(set, base, size, pit_read, NULL, NULL, pit_write, NULL, NULL, priv);\n}\n\nvoid\npit_set_pit_const(void *data, uint64_t pit_const)\n{\n    pit_t *pit = (pit_t *) data;\n\n    pit_catch_up(pit);\n'),
]

KAIROX86_VIDEO_HOIST = [
    ('86box/src/video/video.c',
     'video_process_8_monitor(int x, int y, int monitor_index)\n{\n    for (int xx = 0; xx < x; xx++) {\n        if (monitors[monitor_index].target_buffer->line[y][xx] <= 0xff)\n            monitors[monitor_index].target_buffer->line[y][xx] = monitors[monitor_index].mon_pal_lookup[monitors[monitor_index].target_buffer->line[y][xx]];\n        else\n            monitors[monitor_index].target_buffer->line[y][xx] = 0x00000000;\n    }\n}\n',
     'video_process_8_monitor(int x, int y, int monitor_index)\n{\n    /* KairoX86#199: the line and the palette read once. 86Box builds without strict aliasing, so\n       read through the monitor at each pixel they were read again after every store. */\n    uint32_t       *pixels  = monitors[monitor_index].target_buffer->line[y];\n    const uint32_t *palette = monitors[monitor_index].mon_pal_lookup;\n\n    for (int xx = 0; xx < x; xx++) {\n        const uint32_t index = pixels[xx];\n        pixels[xx] = (index <= 0xff) ? palette[index] : 0x00000000;\n    }\n}\n'),
    ('86box/src/video/vid_cga.c',
     'cga_render(cga_t *cga, int line)\n{\n    uint16_t cursoraddr  = (cga->crtc[CGA_CRTC_CURSOR_ADDR_LOW] | (cga->crtc[CGA_CRTC_CURSOR_ADDR_HIGH] << 8)) & DEVICE_VRAM_MASK;\n    int      drawcursor;\n    int      x;\n    int      column;\n    uint8_t  chr;\n    uint8_t  attr;\n    uint16_t dat;\n    int      cols[4];\n    int      col;\n\n    int32_t  highres_graphics_flag = (CGA_MODE_FLAG_HIGHRES_GRAPHICS | CGA_MODE_FLAG_GRAPHICS);\n    bool     overlay_flag          = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag);\n\n    for (column = 0; column < 8; ++column) {\n        buffer32->line[line][column] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n        if (cga->cgamode & CGA_MODE_FLAG_HIGHRES)\n            buffer32->line[line][column + (cga->crtc[CGA_CRTC_HDISP] * 8) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n        else\n            buffer32->line[line][column + (cga->crtc[CGA_CRTC_HDISP] * 16) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n    }\n\n    if (cga->cgamode & CGA_MODE_FLAG_HIGHRES) { /* 80-column text */\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) {\n                chr  = cga->charbuffer[x << 1];\n                attr = cga->charbuffer[(x << 1) + 1];\n            } else\n                chr = attr = 0;\n            drawcursor = ((cga->memaddr == cursoraddr) && cga->cursorvisible && cga->cursoron);\n            cols[1]    = (attr & 15) + 16;\n            if (cga->cgamode & CGA_MODE_FLAG_BLINK) {\n                cols[0] = ((attr >> 4) & 7) + 16;\n                if ((cga->cgablink & 8) && (attr & 0x80) && !cga->drawcursor)\n                    cols[1] = cols[0];\n            } else\n                cols[0] = (attr >> 4) + 16;\n\n            for (column = 0; column < 8; column++) {\n                buffer32->line[line][(x * 8) + column + 8]\n                    = cols[(fontdat[chr + cga->fontbase][cga->scanline & 7] & (1 << (column ^ 7))) ? 1 : 0] ^ (drawcursor ? 0b1111 : 0);\n                \n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && cga_is_in_lightpen(cga, (x * 8) + column + 8, line)) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 8) + column + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n\n            cga->memaddr++;\n        }\n    } else if (!(cga->cgamode & CGA_MODE_FLAG_GRAPHICS)) {\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) {\n                chr  = cga->vram[(cga->memaddr << 1) & DEVICE_VRAM_MASK];\n                attr = cga->vram[((cga->memaddr << 1) + 1) & DEVICE_VRAM_MASK];\n            } else\n                chr = attr = 0;\n            drawcursor = ((cga->memaddr == cursoraddr) && cga->cursorvisible && cga->cursoron);\n            cols[1]    = (attr & 15) + 16;\n            if (cga->cgamode & CGA_MODE_FLAG_BLINK) {\n                cols[0] = ((attr >> 4) & 7) + 16;\n                if ((cga->cgablink & 8) && (attr & 0x80))\n                    cols[1] = cols[0];\n            } else\n                cols[0] = (attr >> 4) + 16;\n\n            for (column = 0; column < 8; column++) {\n                buffer32->line[line][(x * 16) + (column << 1) + 8]\n                    = buffer32->line[line][(x * 16) + (column << 1) + 8 + 1]\n                    = (cols[(fontdat[chr + cga->fontbase][cga->scanline & 7] & (1 << (column ^ 7))) ? 1 : 0] ^ (drawcursor ? 0b1111 : 0));\n\n                \n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && (cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8, line) || cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8 + 1, line))) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + (column << 1) + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n\n            cga->memaddr++;\n        }\n    } else if (!(cga->cgamode & CGA_MODE_FLAG_HIGHRES_GRAPHICS)) { /* not hi-res (but graphics) => 4-color mode (2bpp) */\n        cols[0] = (cga->cgacol & 15) | 16;\n        col     = (cga->cgacol & 16) ? 24 : 16;\n        if (cga->cgamode & CGA_MODE_FLAG_BW) {\n            cols[1] = col | 3; /* Cyan */\n            cols[2] = col | 4; /* Red */\n            cols[3] = col | 7; /* White */\n        } else if (cga->cgacol & 32) {\n            cols[1] = col | 3; /* Cyan */\n            cols[2] = col | 5; /* Magenta */\n            cols[3] = col | 7; /* White */\n        } else {\n            cols[1] = col | 2; /* Green */\n            cols[2] = col | 4; /* Red */\n            cols[3] = col | 6; /* Yellow */\n        }\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE)\n                dat = (cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000)] << 8) |\n                      cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000) + 1];\n            else\n                dat = 0;\n            for (column = 0; column < 8; column++) {\n                buffer32->line[line][(x * 16) + (column << 1) + 8]\n                    = buffer32->line[line][(x * 16) + (column << 1) + 8 + 1]\n                    = cols[dat >> 14];\n\n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && (cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8, line) || cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8 + 1, line))) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + (column << 1) + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n\n                dat <<= 2;\n            }\n            cga->memaddr++;\n        }\n    } else { /* 2-color hi-res graphics mode (1bpp) */\n        cols[0] = 0;\n        cols[1] = (cga->cgacol & 15) + 16;\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE)\n                dat = (cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000)] << 8) |\n                      cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000) + 1];\n            else\n                dat = 0;\n            for (column = 0; column < 16; column++) {\n                buffer32->line[line][(x * 16) + column + 8] = cols[dat >> 15];\n                dat <<= 1;\n\n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && cga_is_in_lightpen(cga, (x * 16) + column + 8, line)) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + column + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n            cga->memaddr++;\n        }\n    }\n}\n\nstatic void\n',
     "cga_render(cga_t *cga, int line)\n{\n    /* KairoX86#199: the line read once, not again after each pixel's store (no strict aliasing). */\n    uint32_t *pixels     = buffer32->line[line];\n    uint16_t cursoraddr  = (cga->crtc[CGA_CRTC_CURSOR_ADDR_LOW] | (cga->crtc[CGA_CRTC_CURSOR_ADDR_HIGH] << 8)) & DEVICE_VRAM_MASK;\n    int      drawcursor;\n    int      x;\n    int      column;\n    uint8_t  chr;\n    uint8_t  attr;\n    uint16_t dat;\n    int      cols[4];\n    int      col;\n\n    int32_t  highres_graphics_flag = (CGA_MODE_FLAG_HIGHRES_GRAPHICS | CGA_MODE_FLAG_GRAPHICS);\n    bool     overlay_flag          = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag);\n\n    for (column = 0; column < 8; ++column) {\n        pixels[column] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n        if (cga->cgamode & CGA_MODE_FLAG_HIGHRES)\n            pixels[column + (cga->crtc[CGA_CRTC_HDISP] * 8) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n        else\n            pixels[column + (cga->crtc[CGA_CRTC_HDISP] * 16) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n    }\n\n    if (cga->cgamode & CGA_MODE_FLAG_HIGHRES) { /* 80-column text */\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) {\n                chr  = cga->charbuffer[x << 1];\n                attr = cga->charbuffer[(x << 1) + 1];\n            } else\n                chr = attr = 0;\n            drawcursor = ((cga->memaddr == cursoraddr) && cga->cursorvisible && cga->cursoron);\n            cols[1]    = (attr & 15) + 16;\n            if (cga->cgamode & CGA_MODE_FLAG_BLINK) {\n                cols[0] = ((attr >> 4) & 7) + 16;\n                if ((cga->cgablink & 8) && (attr & 0x80) && !cga->drawcursor)\n                    cols[1] = cols[0];\n            } else\n                cols[0] = (attr >> 4) + 16;\n\n            for (column = 0; column < 8; column++) {\n                pixels[(x * 8) + column + 8]\n                    = cols[(fontdat[chr + cga->fontbase][cga->scanline & 7] & (1 << (column ^ 7))) ? 1 : 0] ^ (drawcursor ? 0b1111 : 0);\n                \n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && cga_is_in_lightpen(cga, (x * 8) + column + 8, line)) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 8) + column + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n\n            cga->memaddr++;\n        }\n    } else if (!(cga->cgamode & CGA_MODE_FLAG_GRAPHICS)) {\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) {\n                chr  = cga->vram[(cga->memaddr << 1) & DEVICE_VRAM_MASK];\n                attr = cga->vram[((cga->memaddr << 1) + 1) & DEVICE_VRAM_MASK];\n            } else\n                chr = attr = 0;\n            drawcursor = ((cga->memaddr == cursoraddr) && cga->cursorvisible && cga->cursoron);\n            cols[1]    = (attr & 15) + 16;\n            if (cga->cgamode & CGA_MODE_FLAG_BLINK) {\n                cols[0] = ((attr >> 4) & 7) + 16;\n                if ((cga->cgablink & 8) && (attr & 0x80))\n                    cols[1] = cols[0];\n            } else\n                cols[0] = (attr >> 4) + 16;\n\n            for (column = 0; column < 8; column++) {\n                pixels[(x * 16) + (column << 1) + 8]\n                    = pixels[(x * 16) + (column << 1) + 8 + 1]\n                    = (cols[(fontdat[chr + cga->fontbase][cga->scanline & 7] & (1 << (column ^ 7))) ? 1 : 0] ^ (drawcursor ? 0b1111 : 0));\n\n                \n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && (cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8, line) || cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8 + 1, line))) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + (column << 1) + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n\n            cga->memaddr++;\n        }\n    } else if (!(cga->cgamode & CGA_MODE_FLAG_HIGHRES_GRAPHICS)) { /* not hi-res (but graphics) => 4-color mode (2bpp) */\n        cols[0] = (cga->cgacol & 15) | 16;\n        col     = (cga->cgacol & 16) ? 24 : 16;\n        if (cga->cgamode & CGA_MODE_FLAG_BW) {\n            cols[1] = col | 3; /* Cyan */\n            cols[2] = col | 4; /* Red */\n            cols[3] = col | 7; /* White */\n        } else if (cga->cgacol & 32) {\n            cols[1] = col | 3; /* Cyan */\n            cols[2] = col | 5; /* Magenta */\n            cols[3] = col | 7; /* White */\n        } else {\n            cols[1] = col | 2; /* Green */\n            cols[2] = col | 4; /* Red */\n            cols[3] = col | 6; /* Yellow */\n        }\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE)\n                dat = (cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000)] << 8) |\n                      cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000) + 1];\n            else\n                dat = 0;\n            for (column = 0; column < 8; column++) {\n                pixels[(x * 16) + (column << 1) + 8]\n                    = pixels[(x * 16) + (column << 1) + 8 + 1]\n                    = cols[dat >> 14];\n\n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && (cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8, line) || cga_is_in_lightpen(cga, (x * 16) + (column << 1) + 8 + 1, line))) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + (column << 1) + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n\n                dat <<= 2;\n            }\n            cga->memaddr++;\n        }\n    } else { /* 2-color hi-res graphics mode (1bpp) */\n        cols[0] = 0;\n        cols[1] = (cga->cgacol & 15) + 16;\n        for (x = 0; x < cga->crtc[CGA_CRTC_HDISP]; x++) {\n            if (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE)\n                dat = (cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000)] << 8) |\n                      cga->vram[((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000) + 1];\n            else\n                dat = 0;\n            for (column = 0; column < 16; column++) {\n                pixels[(x * 16) + column + 8] = cols[dat >> 15];\n                dat <<= 1;\n\n                if (cga_lightpen_enabled && !cga->lp_latch_found && mouse_tablet_in_proximity > 0 && cga_is_in_lightpen(cga, (x * 16) + column + 8, line)) {\n                    cga->lp_latch_found_y = line;\n                    cga->lp_latch_found_x = (x * 16) + column + 8;\n                    cga->lp_latch_found_memaddr = cga->memaddr;\n                    cga->lp_latch_found   = true;\n                }\n            }\n            cga->memaddr++;\n        }\n    }\n}\n\nstatic void\n"),
]

KAIROX86_HALT_SKIP = [
    ('86box/src/cpu/808x.c',
     'static void\ncheck_interrupts(int nec_hlt)\n',
     "/* KairoX86#199: the cycles a halted 8088 spends before the next timer is due, at once. A halted\n   cycle (HLT repeating, nothing to interrupt it) only counts: one cycle off, the bus interface's\n   cycle on (the queue is empty and not prefetching, so pfq_add writes nothing), and tsc on by the\n   multiplier. Nothing can end the halt but a timer (every device raises its interrupts and DMA\n   from one), so every cycle before the one where the next timer is due goes by at once; that cycle,\n   and the last of the slice, still run one at a time. A memory refresh to do, a queue that fetches,\n   a held clock or the newer bus interface take every cycle as before. */\nstatic void\nhalt_skip(void)\n{\n    const uint64_t multi = (uint64_t) xt_cpu_multi >> 32ULL;\n    const int64_t  ahead = (int64_t) (timer_target - (uint64_t) tsc);\n\n    if ((refresh > 0) || is_new_biu || (is80c88 && cpu_clock_gated) || (multi == 0) || (ahead <= 0))\n        return;\n    if ((pfq_pos < pfq_size) && prefetching)\n        return;\n\n    /* The cycle that makes tsc reach the timer's time is the first to run its callbacks. */\n    const uint64_t due  = ((uint64_t) ahead + multi - 1) / multi;\n    int64_t        skip = (int64_t) due - 1;\n\n    if (skip > (int64_t) cycles - 1)\n        skip = (int64_t) cycles - 1;\n    if (skip <= 0)\n        return;\n\n    cycles -= (int) skip;\n    if (pfq_pos < pfq_size)\n        biu_cycles = (int) ((biu_cycles + skip) & 0x03);\n    tsc += (uint64_t) skip * multi;\n    cycdiff = cycles;\n}\n\nstatic void\ncheck_interrupts(int nec_hlt)\n"),
    ('86box/src/cpu/808x.c',
     '                    repeating = 1;\n                    completed = 0;\n                    CPU_NOTE_HALT(); /* KairoX86 */\n                    clock_end();\n',
     '                    repeating = 1;\n                    completed = 0;\n                    CPU_NOTE_HALT(); /* KairoX86 */\n                    clock_end();\n                    halt_skip(); /* KairoX86#199 */\n'),
]

KAIROX86_HALT_SKIP_VX0 = [
    ('86box/src/cpu/vx0_biu.c',
     '    cycles_ex++;\n}\n',
     "    cycles_ex++;\n}\n\n/* KairoX86#205: the passes a halted V20/V30 (HLT repeating, nothing to interrupt it) spends before\n   the next timer is due, at once, as kairox86-halt-skip does for the 8088 (KairoX86#199). With the\n   bus interface idle or suspended and staying so, no DMA cycle and no wait states, a cycle only\n   counts: biu_cycle runs no bus access, run_dma_cycle and biu_do_cycle change nothing, and\n   cycles_forward takes a cycle off and moves tsc on. Only a timer can end the halt, so every pass of\n   [pass_cycles] before the one where the next timer is due goes by at once; that pass, and the\n   slice's last, still run cycle by cycle. */\nvoid\nbiu_halt_skip(int pass_cycles)\n{\n    if (((biu_state != BIU_STATE_IDLE) && (biu_state != BIU_STATE_SUSP)) || (biu_next_state != biu_state) ||\n        (dma_state != DMA_STATE_IDLE) || (wait_states != 0) || (dma_wait_states != 0) || is286 || (pass_cycles <= 0))\n        return;\n\n    const uint64_t multi = (uint64_t) xt_cpu_multi >> 32ULL;\n    const int64_t  ahead = (int64_t) (timer_target - (uint64_t) tsc);\n\n    if ((multi == 0) || (ahead <= 0))\n        return;\n\n    /* Every skipped cycle leaves tsc before the timer's time, and the slice a pass to run. */\n    int64_t       passes = (int64_t) (((uint64_t) ahead - 1) / multi) / pass_cycles;\n    const int64_t room   = ((int64_t) cycles - 1) / pass_cycles;\n\n    if (passes > room)\n        passes = room;\n    if (passes <= 0)\n        return;\n\n    const int64_t skip = passes * pass_cycles;\n    cycles -= (int) skip;\n    tsc += (uint64_t) skip * multi;\n    cycles_ex += (int) skip;\n}\n"),
    ('86box/src/cpu/vx0_biu.h',
     'extern void        biu_suspend_fetch(void);\n',
     'extern void        biu_suspend_fetch(void);\nextern void        biu_halt_skip(int pass_cycles);\n'),
    ('86box/src/cpu/vx0.c',
     '                halted    = 1;\n                CPU_NOTE_HALT(); /* KairoX86 */\n',
     "                halted    = 1;\n                CPU_NOTE_HALT(); /* KairoX86 */\n                /* KairoX86#205: a pass is execute_instruction's cycle when no ModR/M is loaded and\n                   the three above. */\n                if (!nx && !group_delay && !in_0f && !(is_nec && !(cpu_state.flags & MD_FLAG)))\n                    biu_halt_skip((modrm_loaded ? 0 : 1) + 3);\n"),
]

KAIROX86_DENSEL_ONCE = [
    ('86box/src/floppy/fdd.c',
     'fdd_type_invert_densel(int type)\n{\n    int ret;\n\n    if (drive_types[type].flags & FLAG_PS2) {\n        /* The Model 25/30 planar also belongs to the 7690, whose display\n           name does not contain "PS/2". Its drive wiring is unchanged. */\n        ret = (machines[machine].init == machine_ps2_8086_init) ||\n              (!!strstr(machine_getname(machine), "PS/1")) ||\n              (!!strstr(machine_getname(machine), "PS/2")) ||\n              (!!strstr(machine_getname(machine), "PS/55"));\n    } else\n',
     'fdd_type_invert_densel(int type)\n{\n    /* KairoX86#206: whether the machine is a PS/1, PS/2 or PS/55, worked out once for each machine:\n       the floppy poll asks for every bit, and the name search was a fortieth of a 486\'s time. */\n    static int ps_machine = -1;\n    static int ps_answer  = 0;\n    int ret;\n\n    if (drive_types[type].flags & FLAG_PS2) {\n        if (ps_machine != machine) {\n            /* The Model 25/30 planar also belongs to the 7690, whose display\n               name does not contain "PS/2". Its drive wiring is unchanged. */\n            ps_answer  = (machines[machine].init == machine_ps2_8086_init) ||\n                         (!!strstr(machine_getname(machine), "PS/1")) ||\n                         (!!strstr(machine_getname(machine), "PS/2")) ||\n                         (!!strstr(machine_getname(machine), "PS/55"));\n            ps_machine = machine;\n        }\n        ret = ps_answer;\n    } else\n'),
]

# KairoX86#214: 320-wide packed 8bpp (VGA mode 13h and its unchained form, DOOM's) took the generic
# renderer's slow loop on the emulation thread, a seventh of DOOM's time. The fast path and the drawing
# thread (kairo9x-video, kairox86-raster) took only lines of a dot per pixel. A lowres line is the same
# line with each pixel drawn twice across, so they take it too: each VRAM byte through map8 into two
# pixels, a dword to eight, the dwords wholly left of hdisp on the drawing thread.
_F = '86box/src/video/vid_svga_render.c'
KAIROX86_LOWRES_8BPP = [
    (_F,
     '    int       dwords;\n    uint32_t  map8[256];\n',
     '    int       dwords;\n    int       wide; /* KairoX86#214: each pixel drawn twice across */\n    uint32_t  map8[256];\n'),
    (_F,
     '        memcpy(&dat, &job->line[4 * c], 4);\n'
     '        p[0]    = job->map8[dat & job->dac];\n'
     '        p[1]    = job->map8[(dat >> 8) & job->dac];\n'
     '        p[2]    = job->map8[(dat >> 16) & job->dac];\n'
     '        p[3]    = job->map8[(dat >> 24) & job->dac];\n'
     '        p += 4;\n',
     '        memcpy(&dat, &job->line[4 * c], 4);\n'
     '        if (job->wide) {\n'
     '            p[0] = p[1] = job->map8[dat & job->dac];\n'
     '            p[2] = p[3] = job->map8[(dat >> 8) & job->dac];\n'
     '            p[4] = p[5] = job->map8[(dat >> 16) & job->dac];\n'
     '            p[6] = p[7] = job->map8[(dat >> 24) & job->dac];\n'
     '            p += 8;\n'
     '            continue;\n'
     '        }\n'
     '        p[0]    = job->map8[dat & job->dac];\n'
     '        p[1]    = job->map8[(dat >> 8) & job->dac];\n'
     '        p[2]    = job->map8[(dat >> 16) & job->dac];\n'
     '        p[3]    = job->map8[(dat >> 24) & job->dac];\n'
     '        p += 4;\n'),
    (_F,
     '    if (combine8bits && highres && !svga->packed_4bpp && !svga->half_pixel && !svga->ati_4color &&\n',
     '    /* KairoX86#214: lowres too, each pixel twice across (dotwidth 2, a dword to eight pixels) */\n'
     '    if (combine8bits && !svga->packed_4bpp && !svga->half_pixel && !svga->ati_4color &&\n'),
    (_F,
     '            render_job_t *job    = render_slot();\n'
     '            const int     dwords = svga->hdisp / 4;\n'
     '\n'
     '            job->p      = p;\n'
     '            job->dac    = dac;\n'
     '            job->dwords = dwords;\n',
     '            render_job_t *job    = render_slot();\n'
     '            const int     dwords = svga->hdisp / (highres ? 4 : 8);\n'
     '\n'
     '            job->p      = p;\n'
     '            job->dac    = dac;\n'
     '            job->dwords = dwords;\n'
     '            job->wide   = !highres;\n'),
    (_F,
     '            render_commit();\n'
     '            p += 4 * dwords;\n'
     '            x = 4 * dwords;\n'
     '        }\n'
     '\n'
     '        for (; x <= end; x += 4) {\n',
     '            render_commit();\n'
     '            p += (highres ? 4 : 8) * dwords;\n'
     '            x = (highres ? 4 : 8) * dwords;\n'
     '        }\n'
     '\n'
     '        for (; !highres && (x <= end); x += 8) {\n'
     '            const uint32_t dat = *(const uint32_t *) &vram[memaddr & mask];\n'
     '\n'
     '            memaddr = (memaddr + 4) & mask;\n'
     '            p[0] = p[1] = map8[dat & dac];\n'
     '            p[2] = p[3] = map8[(dat >> 8) & dac];\n'
     '            p[4] = p[5] = map8[(dat >> 16) & dac];\n'
     '            p[6] = p[7] = map8[(dat >> 24) & dac];\n'
     '            col = p[7];\n'
     '            p += 8;\n'
     '        }\n'
     '        for (; highres && (x <= end); x += 4) {\n'),
    # The thread drew each line before the next was queued, so it slept again and every line woke it:
    # a futex wake per line, a twentieth of the emulation thread's time in DOOM. A job holds its line's
    # bytes and palette (kairox86-raster), so when it is drawn changes nothing; svga_render_drain still
    # draws every one before a frame is shown. The thread is woken once RENDER_BATCH lines wait.
    (_F,
     '    /* A thread still drawing finds the job itself; one that found the queue\n'
     '       empty is woken */\n'
     '    const int was_empty = (head == atomic_load_explicit(&render_tail, memory_order_acquire));\n'
     '    atomic_store_explicit(&render_head, head + 1, memory_order_release);\n'
     '    if (was_empty)\n'
     '        thread_set_event(render_wake);\n',
     '    /* KairoX86#214: a thread still drawing finds the job itself; a sleeping one is woken once\n'
     '       RENDER_BATCH lines wait (while it sleeps nothing is drawn, so the count reaches it), and\n'
     '       svga_render_drain() wakes it for the rest */\n'
     '    const unsigned waiting = head + 1 - atomic_load_explicit(&render_tail, memory_order_acquire);\n'
     '    atomic_store_explicit(&render_head, head + 1, memory_order_release);\n'
     '    if (waiting == RENDER_BATCH)\n'
     '        thread_set_event(render_wake);\n'),
    (_F,
     '#define RENDER_JOBS 2048 /* a power of 2, more lines than a frame has */\n',
     '#define RENDER_JOBS 2048 /* a power of 2, more lines than a frame has */\n'
     '#define RENDER_BATCH 32 /* KairoX86#214: lines queued before a sleeping drawing thread is woken */\n'),
]

# KairoX86#214: Nuked OPL3's synthesis on a thread of its own, exact and without delay. 86Box's default
# FM driver generated on the emulation thread, catching up on every register access (4.5% of DOOM's
# time); kairo9x-sound's synthesis thread is ymfm's only. Nothing the guest reads comes from the
# samples (status and timers are the driver's), so the emulation thread queues each write with its
# sample position and the thread generates up to it before applying it, as the catch-up did. The one
# exception is the address write's choice of bank, which reads the chip's newm: once every queued
# 0x105 write is applied, that is the last value written, and while one is still in the chip's write
# buffer the emulation thread waits for the thread to reach the present and reads the chip itself.
# update() waits for the thread to reach the buffer's end, so every sample is where it was.
_F = '86box/src/sound/snd_opl3_nuked.c'
_H = '86box/src/include/86box/snd_opl3_nuked.h'
KAIROX86_OPL3_THREAD = [
    (_H,
     '    opl3_writebuf writebuf[OPL3_WRITEBUF_SIZE];\n};\n',
     '    opl3_writebuf writebuf[OPL3_WRITEBUF_SIZE];\n'
     '    uint32_t      k_applied105; /* KairoX86#214: 0x105 writes the chip has applied */\n'
     '};\n'),
    (_H,
     '    int32_t *(*update)(void *priv);\n} nuked_opl3_drv_t;\n',
     '    int32_t *(*update)(void *priv);\n'
     '\n'
     '    /* KairoX86#214: the synthesis thread (snd_opl3_nuked.c), and what newm is once every 0x105\n'
     '       write queued to it (sent105 of them) is applied */\n'
     '    void    *synth;\n'
     '    uint32_t sent105;\n'
     '    uint8_t  newm;\n'
     '} nuked_opl3_drv_t;\n'),
    (_F,
     '#include <86box/snd_opl3_nuked.h>\n',
     '#include <86box/snd_opl3_nuked.h>\n'
     '#include <86box/thread.h>\n'
     '#include <stdatomic.h>\n'),
    (_F,
     '                    case 0x05:\n'
     '                        chip->newm = val & 0x01;\n',
     '                    case 0x05:\n'
     '                        chip->k_applied105++; /* KairoX86#214 */\n'
     '                        chip->newm = val & 0x01;\n'),
    (_F,
     'static int32_t *\n'
     'nuked_opl3_drv_update(void *priv)\n'
     '{\n'
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    if (dev->pos >= music_pos_global)\n'
     '        return dev->buffer;\n'
     '\n'
     '    OPL3_GenerateStream(&dev->opl,\n'
     '                        &dev->buffer[dev->pos * 2],\n'
     '                        music_pos_global - dev->pos);\n'
     '\n'
     '    for (; dev->pos < music_pos_global; dev->pos++) {\n'
     '        dev->buffer[dev->pos * 2] /= 2;\n'
     '        dev->buffer[(dev->pos * 2) + 1] /= 2;\n'
     '    }\n'
     '\n'
     '    return dev->buffer;\n'
     '}\n'
     '\n'
     'static int32_t *\n'
     'nuked_opl3_drv_update_48k(void *priv)\n'
     '{\n'
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    if (dev->pos >= sound_pos_global)\n'
     '        return dev->buffer;\n'
     '\n'
     '    OPL3_GenerateResampledStream(&dev->opl,\n'
     '                                 &dev->buffer[dev->pos * 2],\n'
     '                                 sound_pos_global - dev->pos);\n'
     '\n'
     '    for (; dev->pos < sound_pos_global; dev->pos++) {\n'
     '        dev->buffer[dev->pos * 2] /= 2;\n'
     '        dev->buffer[(dev->pos * 2) + 1] /= 2;\n'
     '    }\n'
     '\n'
     '    return dev->buffer;\n'
     '}\n',
     '/* KairoX86#214: the synthesis thread. The emulation thread queues what the chip is told, each at\n'
     '   the sample it happens at; the thread generates up to that sample, then applies it. */\n'
     '#define SYNTH_OPS   4096 /* a power of 2 */\n'
     '#define SYNTH_BATCH 16   /* operations queued before a sleeping thread is woken */\n'
     '\n'
     'enum { SYNTH_ADVANCE, SYNTH_WRITE, SYNTH_NEWM, SYNTH_RESET };\n'
     '\n'
     'typedef struct synth_op_t {\n'
     '    int      pos;\n'
     '    uint16_t kind;\n'
     '    uint16_t reg;\n'
     '    uint8_t  val;\n'
     '} synth_op_t;\n'
     '\n'
     'typedef struct nuked_synth_t {\n'
     '    thread_t   *thread;\n'
     '    event_t    *wake;\n'
     '    event_t    *idle;\n'
     '    atomic_uint head;       /* next operation queued, emulation thread */\n'
     '    atomic_uint tail;       /* next operation applied, synthesis thread */\n'
     '    atomic_uint applied105; /* the chip\'s k_applied105 as of tail */\n'
     '    atomic_int  quit;\n'
     '    int         pos;        /* the next sample of the buffer to generate, synthesis thread */\n'
     '    synth_op_t  ops[SYNTH_OPS];\n'
     '} nuked_synth_t;\n'
     '\n'
     '/* The samples up to [to], as the catch-up generated them. */\n'
     'static void\n'
     'nuked_opl3_generate(nuked_opl3_drv_t *dev, int *pos, int to)\n'
     '{\n'
     '    if (*pos >= to)\n'
     '        return;\n'
     '    if (dev->is_48k)\n'
     '        OPL3_GenerateResampledStream(&dev->opl, &dev->buffer[*pos * 2], to - *pos);\n'
     '    else\n'
     '        OPL3_GenerateStream(&dev->opl, &dev->buffer[*pos * 2], to - *pos);\n'
     '    for (; *pos < to; (*pos)++) {\n'
     '        dev->buffer[*pos * 2] /= 2;\n'
     '        dev->buffer[(*pos * 2) + 1] /= 2;\n'
     '    }\n'
     '}\n'
     '\n'
     'static void\n'
     'nuked_synth_thread(void *priv)\n'
     '{\n'
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '    nuked_synth_t    *s   = (nuked_synth_t *) dev->synth;\n'
     '\n'
     '    for (;;) {\n'
     '        thread_wait_event(s->wake, -1);\n'
     '        thread_reset_event(s->wake);\n'
     '        for (;;) {\n'
     '            const unsigned tail = atomic_load_explicit(&s->tail, memory_order_relaxed);\n'
     '\n'
     '            if (tail == atomic_load_explicit(&s->head, memory_order_acquire))\n'
     '                break;\n'
     '            const synth_op_t *op = &s->ops[tail & (SYNTH_OPS - 1)];\n'
     '            switch (op->kind) {\n'
     '                case SYNTH_RESET:\n'
     '                    s->pos = 0;\n'
     '                    break;\n'
     '                case SYNTH_WRITE:\n'
     '                    nuked_opl3_generate(dev, &s->pos, op->pos);\n'
     '                    OPL3_WriteRegBuffered(&dev->opl, op->reg, op->val);\n'
     '                    break;\n'
     '                case SYNTH_NEWM:\n'
     '                    nuked_opl3_generate(dev, &s->pos, op->pos);\n'
     '                    dev->opl.newm = op->val;\n'
     '                    break;\n'
     '                default:\n'
     '                    nuked_opl3_generate(dev, &s->pos, op->pos);\n'
     '                    break;\n'
     '            }\n'
     '            atomic_store_explicit(&s->applied105, dev->opl.k_applied105, memory_order_relaxed);\n'
     '            atomic_store_explicit(&s->tail, tail + 1, memory_order_release);\n'
     '        }\n'
     '        thread_set_event(s->idle);\n'
     '        if (atomic_load_explicit(&s->quit, memory_order_acquire))\n'
     '            return;\n'
     '    }\n'
     '}\n'
     '\n'
     '/* Waits until the thread has applied everything queued: then the chip and the buffer are as the\n'
     '   catch-up would have left them now. */\n'
     'static void\n'
     'nuked_synth_wait(nuked_synth_t *s)\n'
     '{\n'
     '    while (atomic_load_explicit(&s->tail, memory_order_acquire) != atomic_load_explicit(&s->head, memory_order_relaxed)) {\n'
     '        thread_reset_event(s->idle);\n'
     '        if (atomic_load_explicit(&s->tail, memory_order_acquire) == atomic_load_explicit(&s->head, memory_order_relaxed))\n'
     '            break;\n'
     '        thread_set_event(s->wake);\n'
     '        thread_wait_event(s->idle, -1);\n'
     '    }\n'
     '}\n'
     '\n'
     'static void\n'
     'nuked_synth_push(nuked_opl3_drv_t *dev, uint16_t kind, uint16_t reg, uint8_t val)\n'
     '{\n'
     '    nuked_synth_t *s    = (nuked_synth_t *) dev->synth;\n'
     '    const unsigned head = atomic_load_explicit(&s->head, memory_order_relaxed);\n'
     '\n'
     '    if ((head - atomic_load_explicit(&s->tail, memory_order_acquire)) == SYNTH_OPS)\n'
     '        nuked_synth_wait(s);\n'
     '    synth_op_t *op = &s->ops[head & (SYNTH_OPS - 1)];\n'
     '    op->pos  = dev->is_48k ? sound_pos_global : music_pos_global;\n'
     '    op->kind = kind;\n'
     '    op->reg  = reg;\n'
     '    op->val  = val;\n'
     '    /* A thread still working finds it itself; a sleeping one is woken once SYNTH_BATCH wait\n'
     '       (while it sleeps nothing is taken, so the count reaches it), and by nuked_synth_wait() */\n'
     '    const unsigned waiting = head + 1 - atomic_load_explicit(&s->tail, memory_order_acquire);\n'
     '    atomic_store_explicit(&s->head, head + 1, memory_order_release);\n'
     '    if (waiting == SYNTH_BATCH)\n'
     '        thread_set_event(s->wake);\n'
     '}\n'
     '\n'
     '/* The buffer up to the present: the thread generates the rest of it. */\n'
     'static int32_t *\n'
     'nuked_opl3_drv_update(void *priv)\n'
     '{\n'
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    nuked_synth_push(dev, SYNTH_ADVANCE, 0, 0);\n'
     '    nuked_synth_wait((nuked_synth_t *) dev->synth);\n'
     '    return dev->buffer;\n'
     '}\n'
     '\n'
     'static int32_t *\n'
     'nuked_opl3_drv_update_48k(void *priv)\n'
     '{\n'
     '    return nuked_opl3_drv_update(priv);\n'
     '}\n'
     '\n'
     '/* The register an address write selects. The bank depends on the chip\'s newm: the last 0x105\n'
     '   value written once the chip has applied every 0x105 write, and the chip\'s own, read at the\n'
     '   present, while one is still in its write buffer. */\n'
     'static uint16_t\n'
     'nuked_opl3_drv_addr(nuked_opl3_drv_t *dev, uint16_t port, uint8_t val)\n'
     '{\n'
     '    nuked_synth_t *s    = (nuked_synth_t *) dev->synth;\n'
     '    uint16_t       addr = val;\n'
     '\n'
     '    if (atomic_load_explicit(&s->applied105, memory_order_acquire) != dev->sent105) {\n'
     '        nuked_synth_push(dev, SYNTH_ADVANCE, 0, 0);\n'
     '        nuked_synth_wait(s);\n'
     '        return nuked_opl3_write_addr(&dev->opl, port, val);\n'
     '    }\n'
     '    if ((port & 0x0002) && ((addr == 0x0005) || dev->newm))\n'
     '        addr |= 0x0100;\n'
     '    return addr;\n'
     '}\n'),
    (_F,
     '        cycles -= ((int) (isa_timing * 8));\n'
     '\n'
     '    dev->update(dev);\n'
     '\n'
     '    uint8_t ret = 0xff;\n',
     '        cycles -= ((int) (isa_timing * 8));\n'
     '\n'
     '    /* KairoX86#214: what a read returns is the driver\'s, not the samples\': no catch-up */\n'
     '    uint8_t ret = 0xff;\n'),
    (_F,
     '    dev->update(dev);\n'
     '\n'
     '    if ((port & 0x0001) == 0x0001) {\n'
     '        OPL3_WriteRegBuffered(&dev->opl, dev->port, val);\n',
     '    if ((port & 0x0001) == 0x0001) {\n'
     '        nuked_synth_push(dev, SYNTH_WRITE, dev->port, val); /* KairoX86#214 */\n'
     '        if (dev->port == 0x105) {\n'
     '            dev->sent105++;\n'
     '            dev->newm = val & 0x01;\n'
     '        }\n'),
    (_F,
     '            case 0x105:\n'
     '                dev->opl.newm = val & 0x01;\n',
     '            case 0x105:\n'
     '                nuked_synth_push(dev, SYNTH_NEWM, 0, val & 0x01); /* KairoX86#214 */\n'),
    (_F,
     '        dev->port = nuked_opl3_write_addr(&dev->opl, port, val) & 0x01ff;\n',
     '        dev->port = nuked_opl3_drv_addr(dev, port, val) & 0x01ff; /* KairoX86#214 */\n'),
    (_F,
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    dev->pos = 0;\n',
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    nuked_synth_push(dev, SYNTH_RESET, 0, 0); /* KairoX86#214 */\n'),
    (_F,
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '\n'
     '    free(dev);\n',
     '    nuked_opl3_drv_t *dev = (nuked_opl3_drv_t *) priv;\n'
     '    nuked_synth_t    *s   = (nuked_synth_t *) dev->synth;\n'
     '\n'
     '    /* KairoX86#214: the thread ends with the chip, everything queued applied */\n'
     '    nuked_synth_wait(s);\n'
     '    atomic_store_explicit(&s->quit, 1, memory_order_release);\n'
     '    thread_set_event(s->wake);\n'
     '    thread_wait(s->thread);\n'
     '    thread_destroy_event(s->wake);\n'
     '    thread_destroy_event(s->idle);\n'
     '    free(s);\n'
     '    free(dev);\n'),
    (_F,
     '    timer_add(&dev->timers[0], nuked_opl3_timer_1, dev, 0);\n'
     '    timer_add(&dev->timers[1], nuked_opl3_timer_2, dev, 0);\n'
     '\n'
     '    return dev;\n',
     '    timer_add(&dev->timers[0], nuked_opl3_timer_1, dev, 0);\n'
     '    timer_add(&dev->timers[1], nuked_opl3_timer_2, dev, 0);\n'
     '\n'
     '    /* KairoX86#214: the synthesis thread */\n'
     '    nuked_synth_t *s = (nuked_synth_t *) calloc(1, sizeof(nuked_synth_t));\n'
     '    s->wake    = thread_create_event();\n'
     '    s->idle    = thread_create_event();\n'
     '    dev->synth = s;\n'
     '    s->thread  = thread_create(nuked_synth_thread, dev);\n'
     '    nuked_synth_register(dev, 1);\n'
     '\n'
     '    return dev;\n'),
    # The thread generates while the machine runs, not only at a write or the buffer's end: every
    # SYNTH_STEP samples sound.c's own per-sample poll (no new timer) tells each chip the present.
    (_F,
     '/* The buffer up to the present: the thread generates the rest of it. */\n',
     '#define SYNTH_CHIPS 4   /* chips at once */\n'
     '#define SYNTH_STEP  128 /* samples between the present told to the thread, a power of 2 */\n'
     '\n'
     'static nuked_opl3_drv_t *synth_chips[SYNTH_CHIPS];\n'
     '\n'
     'static void\n'
     'nuked_synth_register(nuked_opl3_drv_t *dev, int on)\n'
     '{\n'
     '    for (int c = 0; c < SYNTH_CHIPS; c++) {\n'
     '        if (on ? (synth_chips[c] == NULL) : (synth_chips[c] == dev)) {\n'
     '            synth_chips[c] = on ? dev : NULL;\n'
     '            return;\n'
     '        }\n'
     '    }\n'
     '    if (on)\n'
     '        fatal("Nuked OPL3: more than %i chips\\n", SYNTH_CHIPS);\n'
     '}\n'
     '\n'
     '/* sound.c: the sample count [pos] of the 48 kHz stream ([is_48k]) or the music stream moved on. */\n'
     'void\n'
     'kairo_nuked_advance(int is_48k, int pos)\n'
     '{\n'
     '    if (pos & (SYNTH_STEP - 1))\n'
     '        return;\n'
     '    for (int c = 0; c < SYNTH_CHIPS; c++) {\n'
     '        nuked_opl3_drv_t *dev = synth_chips[c];\n'
     '\n'
     '        if ((dev != NULL) && (dev->is_48k == !!is_48k)) {\n'
     '            nuked_synth_push(dev, SYNTH_ADVANCE, 0, 0);\n'
     '            thread_set_event(((nuked_synth_t *) dev->synth)->wake);\n'
     '        }\n'
     '    }\n'
     '}\n'
     '\n'
     '/* The buffer up to the present: the thread generates the rest of it. */\n'),
    (_F,
     '    /* KairoX86#214: the thread ends with the chip, everything queued applied */\n'
     '    nuked_synth_wait(s);\n',
     '    /* KairoX86#214: the thread ends with the chip, everything queued applied */\n'
     '    nuked_synth_register(dev, 0);\n'
     '    nuked_synth_wait(s);\n'),
    ('86box/src/sound/sound.c',
     '    music_pos_global++;\n'
     '    if (music_pos_global == MUSICBUFLEN) {\n',
     '    music_pos_global++;\n'
     '    kairo_nuked_advance(0, music_pos_global); /* KairoX86#214 */\n'
     '    if (music_pos_global == MUSICBUFLEN) {\n'),
    ('86box/src/sound/sound.c',
     '    sound_pos_global++;\n'
     '    if (sound_pos_global == sound_buf_len) {\n',
     '    sound_pos_global++;\n'
     '    kairo_nuked_advance(1, sound_pos_global); /* KairoX86#214 */\n'
     '    if (sound_pos_global == sound_buf_len) {\n'),
    ('86box/src/sound/sound.c',
     'int  music_pos_global                   = 0;\n',
     'int  music_pos_global                   = 0;\n'
     '/* KairoX86#214: Nuked OPL3\'s synthesis thread is told the present (snd_opl3_nuked.c) */\n'
     'extern void kairo_nuked_advance(int is_48k, int pos);\n'),
]

# KairoX86#214: the planar byte write a card that decodes its own addresses makes (the S3's, in
# DOOM's unchained 256-colour mode) in its plainest form: write mode 0, every bit taken, no logic
# operation, no set/reset, plain planar addressing. svga_write_common's general path worked out the
# planes with clz/ctz and tested its flags for each one; this does the same steps in the same order:
# the timing, fullchange, a zero write mask's return, the address, the changed page, the rotation, and
# the planes the mask names.
KAIROX86_PLAIN_PLANAR_WRITE = [
    ('86box/src/video/vid_svga.c',
     '        writemask2 = svga->seqregs[2];\n'
     '\n'
     '    cycles -= svga->monitor->mon_video_timing_write_b;\n',
     '        writemask2 = svga->seqregs[2];\n'
     '\n'
     '    cycles -= svga->monitor->mon_video_timing_write_b;\n'
     '\n'
     '    /* KairoX86#214: the plain planar write, as the general path below makes it */\n'
     '    if (linear && !(svga->adv_flags & (FLAG_ADDR_BY8 | FLAG_ADDR_BY16 | FLAG_LATCH8 | FLAG_EXT_WRITE)) &&\n'
     '        (svga->writemode == 0) && !svga->chain4 && !svga->chain2_write && !svga->fb_only &&\n'
     '        (svga->gdcreg[8] == 0xff) && !(svga->gdcreg[3] & 0x18) && (!svga->gdcreg[1] || svga->set_reset_disabled) &&\n'
     '        (svga->translate_address == NULL)) {\n'
     '        if (!(svga->gdcreg[6] & 1))\n'
     '            svga->fullchange = 2;\n'
     '        if (!writemask2)\n'
     '            return;\n'
     '        addr = (addr << 2) & svga->decode_mask;\n'
     '        if (addr >= svga->vram_max)\n'
     '            return;\n'
     '        addr &= svga->vram_mask;\n'
     '        svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n'
     '        val = ((val >> (svga->gdcreg[3] & 7)) | (val << (8 - (svga->gdcreg[3] & 7))));\n'
     '        if (writemask2 & 1)\n'
     '            svga->vram[addr] = val;\n'
     '        if (writemask2 & 2)\n'
     '            svga->vram[addr | 1] = val;\n'
     '        if (writemask2 & 4)\n'
     '            svga->vram[addr | 2] = val;\n'
     '        if (writemask2 & 8)\n'
     '            svga->vram[addr | 3] = val;\n'
     '        return;\n'
     '    }\n'),
]

# The arm64 recompiler's guest FPU registers are V8-V15 (codegen_host_fp_reg_list), whose low halves
# (d8-d15) AAPCS64 makes callee-saved, but a block's prologue saved only X19-X30. A block with FPU
# code (x87, as Windows 9x games run) clobbered the floating-point values its C callers kept in
# d8-d15 across the call: the emulation thread's own C code and the frontend above it. Found by
# game_profile on Daytona USA (eXoWin9x, Pentium Pro), whose frame statistics and screenshot headers
# came out as doubles of the guest's. The prologue now saves d8-d15 under X19/X20 (the locals' offsets
# from SP are unchanged), and both ways back to C restore them.
_F = '86box/src/codegen/codegen_backend_arm64.c'
_O = '86box/src/codegen/codegen_backend_arm64_ops.c'
KAIROX86_ARM64_FP_CALLEE_SAVED = [
    (_O,
     '#    define OPCODE_STP_PREIDX_X       (0x2a6 << 22)\n',
     '#    define OPCODE_STP_PREIDX_X       (0x2a6 << 22)\n'
     '#    define OPCODE_STP_PREIDX_D       (0x1b6 << 22) /* KairoX86: STP Dt, Dt2, [Xn, #imm]! */\n'
     '#    define OPCODE_LDP_POSTIDX_D      (0x1b3 << 22) /* KairoX86: LDP Dt, Dt2, [Xn], #imm */\n'),
    (_O,
     'void\n'
     'host_arm64_STP_POSTIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n',
     '/* KairoX86: the callee-saved d8-d15, around a block\'s frame */\n'
     'void\n'
     'host_arm64_STP_PREIDX_D(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n'
     '{\n'
     '    if (!in_range7_x(offset))\n'
     '        fatal("host_arm64_STP_PREIDX_D out of range7 %i\\n", offset);\n'
     '    codegen_addlong(block, OPCODE_STP_PREIDX_D | IMM7_X(offset) | Rn(base_reg) | Rt(src_reg1) | Rt2(src_reg2));\n'
     '}\n'
     'void\n'
     'host_arm64_LDP_POSTIDX_D(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n'
     '{\n'
     '    if (!in_range7_x(offset))\n'
     '        fatal("host_arm64_LDP_POSTIDX_D out of range7 %i\\n", offset);\n'
     '    codegen_addlong(block, OPCODE_LDP_POSTIDX_D | IMM7_X(offset) | Rn(base_reg) | Rt(src_reg1) | Rt2(src_reg2));\n'
     '}\n'
     'void\n'
     'host_arm64_STP_POSTIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset)\n'),
    ('86box/src/codegen/codegen_backend_arm64.h',
     'void host_arm64_LDP_POSTIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset);\n',
     'void host_arm64_LDP_POSTIDX_X(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset);\n'
     'void host_arm64_STP_PREIDX_D(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset);\n'
     'void host_arm64_LDP_POSTIDX_D(codeblock_t *block, int src_reg1, int src_reg2, int base_reg, int offset);\n'),
    (_F,
     '    host_arm64_STP_PREIDX_X(block, REG_X21, REG_X22, REG_XSP, -16);\n'
     '    host_arm64_STP_PREIDX_X(block, REG_X19, REG_X20, REG_XSP, -64);\n',
     '    host_arm64_STP_PREIDX_X(block, REG_X21, REG_X22, REG_XSP, -16);\n'
     '    /* KairoX86: d8-d15 are callee-saved, and the guest FPU registers are V8-V15 */\n'
     '    host_arm64_STP_PREIDX_D(block, REG_V8, REG_V9, REG_XSP, -16);\n'
     '    host_arm64_STP_PREIDX_D(block, REG_V10, REG_V11, REG_XSP, -16);\n'
     '    host_arm64_STP_PREIDX_D(block, REG_V12, REG_V13, REG_XSP, -16);\n'
     '    host_arm64_STP_PREIDX_D(block, REG_V14, REG_V15, REG_XSP, -16);\n'
     '    host_arm64_STP_PREIDX_X(block, REG_X19, REG_X20, REG_XSP, -64);\n'
     '#    ifdef CODEGEN_BACKEND_HAS_BLOCK_LINK\n'
     '    /* KairoX86: links enter here, past the saves (codegen_link.h), as the x86-64 backend checks */\n'
     '    if (block_pos != BLOCK_START + CODEGEN_LINK_ENTRY_OFFSET)\n'
     '        fatal("codegen_backend_prologue: the link entry is at %i, not %i\\n", block_pos - BLOCK_START, CODEGEN_LINK_ENTRY_OFFSET);\n'
     '#    endif\n'),
    ('86box/src/codegen/codegen_link.h',
     '#if defined(__aarch64__) || defined(_M_ARM64)\n'
     '#    define CODEGEN_LINK_ENTRY_OFFSET 24\n',
     '#if defined(__aarch64__) || defined(_M_ARM64)\n'
     '/*Ten pairs: X19-X30 and, KairoX86, d8-d15*/\n'
     '#    define CODEGEN_LINK_ENTRY_OFFSET 40\n'),
    (_F,
     '    codegen_link_miss_rout = &block_write_data[block_pos];\n'
     '#    endif\n'
     '    host_arm64_LDP_POSTIDX_X(block, REG_X19, REG_X20, REG_XSP, 64);\n',
     '    codegen_link_miss_rout = &block_write_data[block_pos];\n'
     '#    endif\n'
     '    host_arm64_LDP_POSTIDX_X(block, REG_X19, REG_X20, REG_XSP, 64);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V14, REG_V15, REG_XSP, 16); /* KairoX86 */\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V12, REG_V13, REG_XSP, 16);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V10, REG_V11, REG_XSP, 16);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V8, REG_V9, REG_XSP, 16);\n'),
    (_F,
     '        return;\n'
     '    }\n'
     '#    endif\n'
     '    host_arm64_LDP_POSTIDX_X(block, REG_X19, REG_X20, REG_XSP, 64);\n',
     '        return;\n'
     '    }\n'
     '#    endif\n'
     '    host_arm64_LDP_POSTIDX_X(block, REG_X19, REG_X20, REG_XSP, 64);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V14, REG_V15, REG_XSP, 16); /* KairoX86 */\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V12, REG_V13, REG_XSP, 16);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V10, REG_V11, REG_XSP, 16);\n'
     '    host_arm64_LDP_POSTIDX_D(block, REG_V8, REG_V9, REG_XSP, 16);\n'),
]

# KairoX86#214: flags_rebuild_zpna (the P, A, Z and N flags of the last operation, before a rotate,
# which sets only C and O) asked PF_SET, AF_SET, ZF_SET and NF_SET in turn, each a switch of its own
# on flags_op, AF_SET not even inlined: about 8% of Daytona USA's emulation thread. One switch now
# gives what they gave: Z and P from the result as every result-keeping operation has them, N from
# its sign bit at the operation's size, A as each kind of operation has it, the rotates and
# FLAGS_UNKNOWN the flags as they are (so nothing changes), and any other operation nothing.
KAIROX86_FLAGS_ZPNA_ONCE = [
    ('86box/src/cpu/x86_flags.h',
     'static __inline void\n'
     'flags_rebuild_zpna(void)\n'
     '{\n'
     '    if (cpu_state.flags_op != FLAGS_UNKNOWN) {\n'
     '        uint16_t tempf = 0;\n'
     '        if (PF_SET())\n'
     '            tempf |= P_FLAG;\n'
     '        if (AF_SET())\n'
     '            tempf |= A_FLAG;\n'
     '        if (ZF_SET())\n'
     '            tempf |= Z_FLAG;\n'
     '        if (NF_SET())\n'
     '            tempf |= N_FLAG;\n'
     '        cpu_state.flags    = (cpu_state.flags & ~0xd4) | tempf;\n'
     '        cpu_state.flags_op = FLAGS_UNKNOWN;\n'
     '    }\n'
     '}\n',
     'static __inline void\n'
     'flags_rebuild_zpna(void)\n'
     '{\n'
     '    /* KairoX86#214: PF_SET(), AF_SET(), ZF_SET() and NF_SET() in one switch */\n'
     '    const uint32_t res = cpu_state.flags_res;\n'
     '    const uint32_t op1 = cpu_state.flags_op1;\n'
     '    const uint32_t op2 = cpu_state.flags_op2;\n'
     '    uint32_t       sign;\n'
     '    int            af;\n'
     '\n'
     '    switch (cpu_state.flags_op) {\n'
     '        case FLAGS_UNKNOWN:\n'
     '            return;\n'
     '        /* Each of the four is the flag as it is: the flags stay as they are */\n'
     '        case FLAGS_ROL8: case FLAGS_ROL16: case FLAGS_ROL32:\n'
     '        case FLAGS_ROR8: case FLAGS_ROR16: case FLAGS_ROR32:\n'
     '            cpu_state.flags_op = FLAGS_UNKNOWN;\n'
     '            return;\n'
     '        case FLAGS_ZN8: case FLAGS_SHL8: case FLAGS_SHR8: case FLAGS_SAR8:\n'
     '            sign = 0x80; af = 0;\n'
     '            break;\n'
     '        case FLAGS_ZN16: case FLAGS_SHL16: case FLAGS_SHR16: case FLAGS_SHRD16: case FLAGS_SAR16:\n'
     '            sign = 0x8000; af = 0;\n'
     '            break;\n'
     '        case FLAGS_ZN32: case FLAGS_SHL32: case FLAGS_SHR32: case FLAGS_SHRD32: case FLAGS_SAR32:\n'
     '            sign = 0x80000000; af = 0;\n'
     '            break;\n'
     '        case FLAGS_ADD8: case FLAGS_INC8:\n'
     '            sign = 0x80; af = ((op1 & 0xF) + (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_ADD16: case FLAGS_INC16:\n'
     '            sign = 0x8000; af = ((op1 & 0xF) + (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_ADD32: case FLAGS_INC32:\n'
     '            sign = 0x80000000; af = ((op1 & 0xF) + (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_SUB8: case FLAGS_DEC8:\n'
     '            sign = 0x80; af = ((op1 & 0xF) - (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_SUB16: case FLAGS_DEC16:\n'
     '            sign = 0x8000; af = ((op1 & 0xF) - (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_SUB32: case FLAGS_DEC32:\n'
     '            sign = 0x80000000; af = ((op1 & 0xF) - (op2 & 0xF)) & 0x10;\n'
     '            break;\n'
     '        case FLAGS_ADC8: case FLAGS_ADC16: case FLAGS_ADC32:\n'
     '            sign = (cpu_state.flags_op == FLAGS_ADC8) ? 0x80 : (cpu_state.flags_op == FLAGS_ADC16) ? 0x8000 : 0x80000000;\n'
     '            af   = ((res & 0xf) < (op1 & 0xf)) || (((res & 0xf) == (op1 & 0xf)) && ((op2 & 0xf) == 0xf));\n'
     '            break;\n'
     '        case FLAGS_SBC8: case FLAGS_SBC16: case FLAGS_SBC32:\n'
     '            sign = (cpu_state.flags_op == FLAGS_SBC8) ? 0x80 : (cpu_state.flags_op == FLAGS_SBC16) ? 0x8000 : 0x80000000;\n'
     '            af   = ((op1 & 0xf) < (op2 & 0xf)) || (((op1 & 0xf) == (op2 & 0xf)) && ((res & 0xf) != 0));\n'
     '            break;\n'
     '        /* An operation none of the four knows: each gave 0 */\n'
     '        default:\n'
     '            cpu_state.flags    = cpu_state.flags & ~0xd4;\n'
     '            cpu_state.flags_op = FLAGS_UNKNOWN;\n'
     '            return;\n'
     '    }\n'
     '    cpu_state.flags    = (cpu_state.flags & ~0xd4) | (znptable8[res & 0xff] & P_FLAG) | (af ? A_FLAG : 0) |\n'
     '                         (!res ? Z_FLAG : 0) | ((res & sign) ? N_FLAG : 0);\n'
     '    cpu_state.flags_op = FLAGS_UNKNOWN;\n'
     '}\n'),
]

# KairoX86#222: a Voodoo3/Banshee machine's picture followed host timing. The Banshee draws its
# scanlines on the emulation thread from VRAM while the FIFO thread runs the guest's queued writes,
# blits and command FIFO into it, so a line drawn while a blit was partway through showed part of it
# (Daytona USA: one frame's picture of 3,500 differed between two runs; the guest's state did not).
# Before each line (svga render_sync) the emulation thread now waits until the FIFO thread has
# settled: waiting for work with nothing queued (the FIFO empty, both command FIFOs drained and out of
# a subroutine), or waiting for a vsync swap that is still pending. Either way every entry the guest
# queued before that point has taken effect, and which ones those are follows what the guest queued.
# Then the render threads are let finish. Nothing is forced: no swap happens sooner, and the
# emulation thread takes no lock the FIFO thread holds while it waits for the vsync only the
# emulation thread brings.
_C = '86box/src/include/86box/vid_voodoo_common.h'
_F = '86box/src/video/vid_voodoo_fifo.c'
KAIROX86_VOODOO_SETTLE = [
    (_C,
     '    mutex_t  *fifo_mutex;\n',
     '    mutex_t  *fifo_mutex;\n'
     '    /* KairoX86#222: what the FIFO thread is doing (KX86_FIFO_*), for voodoo_settle() */\n'
     '    ATOMIC_INT k_fifo_state;\n'),
    (_C,
     '#define FIFO_EMPTY      (voodoo->fifo_read_idx == voodoo->fifo_write_idx)\n',
     '#define FIFO_EMPTY      (voodoo->fifo_read_idx == voodoo->fifo_write_idx)\n'
     '/* KairoX86#222: the FIFO thread running entries, waiting for work or the rest of a command\n'
     '   FIFO packet (fifo_mutex released), or waiting for a vsync swap */\n'
     '#define KX86_FIFO_WORKING   0\n'
     '#define KX86_FIFO_WAITING   1\n'
     '#define KX86_FIFO_SWAP_WAIT 2\n'),
    ('86box/src/include/86box/vid_voodoo_fifo.h',
     'void voodoo_flush(voodoo_t *voodoo);\n',
     'void voodoo_flush(voodoo_t *voodoo);\n'
     'void voodoo_settle(voodoo_t *voodoo); /* KairoX86#222 */\n'),
    (_F,
     '        /* Yield briefly while waiting for the swap to complete. */\n'
     '#ifdef _WIN32\n'
     '        /* Sleep(1) can add measurable stalls on Windows. */\n'
     '        plat_delay_ms(0);\n'
     '#else\n'
     '        plat_delay_ms(1);\n'
     '#endif\n',
     '        /* Yield briefly while waiting for the swap to complete. */\n'
     '        voodoo->k_fifo_state = KX86_FIFO_SWAP_WAIT; /* KairoX86#222 */\n'
     '#ifdef _WIN32\n'
     '        /* Sleep(1) can add measurable stalls on Windows. */\n'
     '        plat_delay_ms(0);\n'
     '#else\n'
     '        plat_delay_ms(1);\n'
     '#endif\n'
     '        voodoo->k_fifo_state = KX86_FIFO_WORKING;\n'),
    (_F,
     '        while (voodoo->fifo_thread_run && (voodoo->cmdfifo_depth_rd == voodoo->cmdfifo_depth_wr)) {\n'
     '            /* The CPU thread must be able to drain the FIFO while this\n'
     '               waits for it to write the rest of the packet. */\n'
     '            thread_release_mutex(voodoo->fifo_mutex);\n'
     '            thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '            thread_reset_event(voodoo->wake_fifo_thread);\n'
     '            thread_wait_mutex(voodoo->fifo_mutex);\n'
     '        }\n',
     '        while (voodoo->fifo_thread_run && (voodoo->cmdfifo_depth_rd == voodoo->cmdfifo_depth_wr)) {\n'
     '            /* The CPU thread must be able to drain the FIFO while this\n'
     '               waits for it to write the rest of the packet. */\n'
     '            voodoo->k_fifo_state = KX86_FIFO_WAITING; /* KairoX86#222 */\n'
     '            thread_release_mutex(voodoo->fifo_mutex);\n'
     '            thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '            thread_reset_event(voodoo->wake_fifo_thread);\n'
     '            thread_wait_mutex(voodoo->fifo_mutex);\n'
     '            voodoo->k_fifo_state = KX86_FIFO_WORKING;\n'
     '        }\n'),
    (_F,
     '        while (voodoo->fifo_thread_run && (voodoo->cmdfifo_depth_rd_2 == voodoo->cmdfifo_depth_wr_2)) {\n'
     '            /* The CPU thread must be able to drain the FIFO while this\n'
     '               waits for it to write the rest of the packet. */\n'
     '            thread_release_mutex(voodoo->fifo_mutex);\n'
     '            thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '            thread_reset_event(voodoo->wake_fifo_thread);\n'
     '            thread_wait_mutex(voodoo->fifo_mutex);\n'
     '        }\n',
     '        while (voodoo->fifo_thread_run && (voodoo->cmdfifo_depth_rd_2 == voodoo->cmdfifo_depth_wr_2)) {\n'
     '            /* The CPU thread must be able to drain the FIFO while this\n'
     '               waits for it to write the rest of the packet. */\n'
     '            voodoo->k_fifo_state = KX86_FIFO_WAITING; /* KairoX86#222 */\n'
     '            thread_release_mutex(voodoo->fifo_mutex);\n'
     '            thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '            thread_reset_event(voodoo->wake_fifo_thread);\n'
     '            thread_wait_mutex(voodoo->fifo_mutex);\n'
     '            voodoo->k_fifo_state = KX86_FIFO_WORKING;\n'
     '        }\n'),
    (_F,
     '    while (voodoo->fifo_thread_run) {\n'
     '        thread_set_event(voodoo->fifo_not_full_event);\n'
     '        thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '        thread_reset_event(voodoo->wake_fifo_thread);\n',
     '    while (voodoo->fifo_thread_run) {\n'
     '        thread_set_event(voodoo->fifo_not_full_event);\n'
     '        voodoo->k_fifo_state = KX86_FIFO_WAITING; /* KairoX86#222 */\n'
     '        thread_wait_event(voodoo->wake_fifo_thread, -1);\n'
     '        thread_reset_event(voodoo->wake_fifo_thread);\n'
     '        voodoo->k_fifo_state = KX86_FIFO_WORKING;\n'),
    (_F,
     'void\n'
     'voodoo_wake_fifo_threads(voodoo_set_t *set, voodoo_t *voodoo)\n',
     '/* KairoX86#222: waits until the FIFO thread has settled (see KAIROX86_VOODOO_SETTLE in\n'
     '   tools/patches.py) and the render threads are idle. The emulation thread is the only one that\n'
     '   queues entries or brings the vsync, so a settled thread stays settled while it draws a line. */\n'
     'void\n'
     'voodoo_settle(voodoo_t *voodoo)\n'
     '{\n'
     '    if (!voodoo->fifo_thread_run)\n'
     '        return;\n'
     '    for (;;) {\n'
     '        const int state = voodoo->k_fifo_state;\n'
     '\n'
     '        if ((state == KX86_FIFO_SWAP_WAIT) && voodoo->swap_pending)\n'
     '            break;\n'
     '        if ((state == KX86_FIFO_WAITING) && FIFO_EMPTY &&\n'
     '            !(voodoo->cmdfifo_enabled && ((voodoo->cmdfifo_depth_rd != voodoo->cmdfifo_depth_wr) || voodoo->cmdfifo_in_sub)) &&\n'
     '            !(voodoo->cmdfifo_enabled_2 && ((voodoo->cmdfifo_depth_rd_2 != voodoo->cmdfifo_depth_wr_2) || voodoo->cmdfifo_in_sub_2)))\n'
     '            break;\n'
     '        /* Woken at once, not by voodoo_wake_fifo_thread(): that arms the emulated-time\n'
     '           wake_timer, which never fires while the emulation thread waits here, and arming\n'
     '           it would move the timers the guest runs by */\n'
     '        voodoo_wake_fifo_thread_now(voodoo);\n'
     '        plat_delay_ms(0);\n'
     '    }\n'
     '    voodoo_wait_for_render_thread_idle(voodoo);\n'
     '}\n'
     '\n'
     'void\n'
     'voodoo_wake_fifo_threads(voodoo_set_t *set, voodoo_t *voodoo)\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     'static void *\n'
     'banshee_init_common(const device_t *info, const char *fn, const int has_sgram,\n',
     '/* KairoX86#222: each line is drawn with every write the guest queued before it applied */\n'
     'static void\n'
     'banshee_render_sync(svga_t *svga)\n'
     '{\n'
     '    const banshee_t *banshee = (banshee_t *) svga->priv;\n'
     '\n'
     '    if (banshee->voodoo != NULL)\n'
     '        voodoo_settle(banshee->voodoo);\n'
     '}\n'
     '\n'
     'static void *\n'
     'banshee_init_common(const device_t *info, const char *fn, const int has_sgram,\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    banshee->svga.vsync_callback = banshee_vsync_callback;\n',
     '    banshee->svga.vsync_callback = banshee_vsync_callback;\n'
     '    banshee->svga.render_sync    = banshee_render_sync; /* KairoX86#222 */\n'),
]

# KairoX86#214: the Banshee's tiled 16bpp desktop (Voodoo3 Windows games' screen) called
# banshee_conv_16to32() for every pixel, which, with no LUT mapping, gives video_16to32[] of it
# whatever the CLUT selection. The test is made once a tile and the table read directly.
KAIROX86_BANSHEE_16BPP = [
    ('86box/src/video/vid_voodoo_banshee.c',
     '            for (uint8_t xx = 0; xx < 64; xx++)\n'
     '                *p++ = banshee_conv_16to32(svga, *vram_p++, 16);\n',
     '            /* KairoX86#214: with no LUT mapping, the conversion is the table */\n'
     '            if (!svga->lut_map) {\n'
     '                for (uint8_t xx = 0; xx < 64; xx++)\n'
     '                    *p++ = video_16to32[*vram_p++];\n'
     '            } else {\n'
     '                for (uint8_t xx = 0; xx < 64; xx++)\n'
     '                    *p++ = banshee_conv_16to32(svga, *vram_p++, 16);\n'
     '            }\n'),
]

# KairoX86#214: a diagnostic core's code map (K9X_DIAG builds only): every code memory block in use,
# by its offset in the code memory, with the guest block it holds and that block's guest bytes, so
# profile samples in translated code can be told apart by the guest code they run.
KAIROX86_DIAG_CODE_MAP = [
    ('86box/src/codegen/codegen_allocator.c',
     'int codegen_allocator_usage = 0;\n',
     'int codegen_allocator_usage = 0;\n'
     '\n'
     '#ifdef K9X_DIAG\n'
     '/*Writes the code map to path: "base <address> <size>", then for each code memory block in use\n'
     '  "<offset> <codeblock> <pc> <cs base> <phys> <ins> <guest bytes from phys, in hex>"*/\n'
     'void\n'
     'k9x_code_map(const char *path)\n'
     '{\n'
     '    FILE *f = fopen(path, "w");\n'
     '\n'
     '    if (f == NULL)\n'
     '        fatal("k9x_code_map - cannot write %s\\n", path);\n'
     '    fprintf(f, "base %p %u\\n", (void *) mem_block_alloc, (unsigned) (MEM_BLOCK_NR * MEM_BLOCK_SIZE));\n'
     '    for (uint32_t c = 0; c < MEM_BLOCK_NR; c++) {\n'
     '        const uint32_t nr = mem_blocks[c].code_block;\n'
     '\n'
     '        if (nr == BLOCK_INVALID)\n'
     '            continue;\n'
     '        const codeblock_t *b = &codeblock[nr];\n'
     '        fprintf(f, "%x %x %x %x %x %u ", mem_blocks[c].offset, nr, b->pc, b->_cs, b->phys, (unsigned) b->ins);\n'
     '        for (uint32_t i = 0; i < 128; i++)\n'
     '            fprintf(f, "%02x", ((b->phys + i) & rammask) < (mem_size << 10) ? ram[(b->phys + i) & rammask] : 0);\n'
     '        fputc(\'\\n\', f);\n'
     '    }\n'
     '    fclose(f);\n'
     '}\n'
     '#endif\n'),
]


# KairoX86#224: PCem's Award 430VX PCI. eXo's Windows 95 image (Win95DX8.vhd) was installed under
# PCem on that board: 86Box's 430vx has its BIOS (55XWUQ0E), its Super I/O and its slots, but a
# PIIX3 where PCem had the original PIIX at device 7, so Windows meets new chipset functions and
# stops to install them. "pcem_piix = 1" in 86box.cfg's [KairoX86] section builds the board with
# PCem's PIIX. Only the machines KairoX86 makes for eXo's DOSBox-X games set it.
KAIROX86_PCEM_430VX = [
    ('86box/src/include/86box/config.h',
     'extern void config_load_global(void);\n',
     'extern void config_load_global(void);\n'
     '/* KairoX86#224: a setting of 86box.cfg\'s [KairoX86] section, def when it has none */\n'
     'extern int config_kairo_int(const char *name, int def);\n'),
    ('86box/src/config.c',
     'static ini_t    config;\n',
     'static ini_t    config;\n'
     '\n'
     '/* KairoX86#224: a setting of the [KairoX86] section, def when it has none */\n'
     'int\n'
     'config_kairo_int(const char *name, int def)\n'
     '{\n'
     '    return ini_section_get_int(ini_find_section(config, "KairoX86"), name, def);\n'
     '}\n'),
    ('86box/src/machine/m_at_socket7.c',
     '    ret = bios_load_linear("roms/machines/430vx/55XWUQ0E.BIN",\n'
     '                           0x000e0000, 131072, 0);\n'
     '\n'
     '    if (bios_only || !ret)\n'
     '        return ret;\n'
     '\n'
     '    machine_at_common_init(model);\n'
     '\n'
     '    pci_init(PCI_CONFIG_TYPE_1);\n'
     '    pci_register_slot(0x00, PCI_CARD_NORTHBRIDGE, 0, 0, 0, 0);\n'
     '    pci_register_slot(0x11, PCI_CARD_NORMAL,      2, 3, 4, 1);\n'
     '    pci_register_slot(0x12, PCI_CARD_NORMAL,      1, 2, 3, 4);\n'
     '    pci_register_slot(0x14, PCI_CARD_NORMAL,      3, 4, 1, 2);\n'
     '    pci_register_slot(0x13, PCI_CARD_NORMAL,      4, 1, 2, 3);\n'
     '    pci_register_slot(0x07, PCI_CARD_SOUTHBRIDGE, 0, 0, 0, 0);\n'
     '\n'
     '    device_add(&i430vx_device);\n'
     '    device_add(&piix3_device);\n',
     '    ret = bios_load_linear("roms/machines/430vx/55XWUQ0E.BIN",\n'
     '                           0x000e0000, 131072, 0);\n'
     '\n'
     '    if (bios_only || !ret)\n'
     '        return ret;\n'
     '\n'
     '    machine_at_common_init(model);\n'
     '\n'
     '    pci_init(PCI_CONFIG_TYPE_1);\n'
     '    pci_register_slot(0x00, PCI_CARD_NORTHBRIDGE, 0, 0, 0, 0);\n'
     '    pci_register_slot(0x11, PCI_CARD_NORMAL,      2, 3, 4, 1);\n'
     '    pci_register_slot(0x12, PCI_CARD_NORMAL,      1, 2, 3, 4);\n'
     '    pci_register_slot(0x14, PCI_CARD_NORMAL,      3, 4, 1, 2);\n'
     '    pci_register_slot(0x13, PCI_CARD_NORMAL,      4, 1, 2, 3);\n'
     '    pci_register_slot(0x07, PCI_CARD_SOUTHBRIDGE, 0, 0, 0, 0);\n'
     '\n'
     '    device_add(&i430vx_device);\n'
     '    /* KairoX86#224: PCem\'s Award 430VX PCI had the original PIIX here */\n'
     '    device_add(config_kairo_int("pcem_piix", 0) ? &piix_device : &piix3_device);\n'),
    ('86box/src/machine/m_at_socket7.c',
     '#include <86box/machine.h>\n',
     '#include <86box/machine.h>\n'
     '#include <86box/config.h> /* KairoX86#224: config_kairo_int() */\n'),
]

# KairoX86#228: DOSBox-X's PCI bus has no host bridge, so its first card answers device 0; eXo's
# Windows 95 image met its Voodoo Graphics there. pci_add_card_dev0() puts a card at device 0 of
# bus 0 for registers 00h-4Fh of function 0, before the northbridge, which keeps the rest (the
# 430VX keeps only stored values below 50h). "voodoo_pci_dev0 = 1" in 86box.cfg's [KairoX86]
# section puts the Voodoo there; only the machines KairoX86 makes for an image that knows it there set it.
KAIROX86_PCI_DEV0_CARD = [
    ('86box/src/include/86box/pci.h',
     '/* Add an instance of the PCI bridge. */\n',
     '/* KairoX86#228: a card at device 0 of bus 0, registers 00h-4Fh of function 0, before the\n   northbridge, which keeps the rest. */\nextern void        pci_add_card_dev0(uint8_t (*read)(int func, int addr, int len, void *priv),\n                                     void (*write)(int func, int addr, int len, uint8_t val, void *priv), void *priv);\n\n/* Add an instance of the PCI bridge. */\n'),
    ('86box/src/pci.c',
     'static uint8_t     pci_card_to_slot_mapping[256][PCI_CARDS_NUM];\n',
     'static uint8_t     pci_card_to_slot_mapping[256][PCI_CARDS_NUM];\n/* KairoX86#228: the card at device 0 of bus 0 below register 50h (pci_add_card_dev0) */\nstatic uint8_t (*pci_dev0_read)(int func, int addr, int len, void *priv);\nstatic void (*pci_dev0_write)(int func, int addr, int len, uint8_t val, void *priv);\nstatic void *pci_dev0_priv;\n'),
    ('86box/src/pci.c',
     '    slot = pci_card_to_slot_mapping[pci_bus_number_to_index_mapping[pci_bus]][pci_card];\n    if (slot != PCI_CARD_INVALID) {\n        if (pci_cards[slot].write)\n',
     '    /* KairoX86#228: device 0 of bus 0 below register 50h is the card there, if any */\n    if (pci_dev0_write && (pci_bus == 0) && (pci_card == 0) && (pci_func == 0) && (pci_index < 0x50)) {\n        pci_dev0_write(pci_func, pci_index | (port & 0x03), pci_access_len, val, pci_dev0_priv);\n        return;\n    }\n\n    slot = pci_card_to_slot_mapping[pci_bus_number_to_index_mapping[pci_bus]][pci_card];\n    if (slot != PCI_CARD_INVALID) {\n        if (pci_cards[slot].write)\n'),
    ('86box/src/pci.c',
     '    slot = pci_card_to_slot_mapping[pci_bus_number_to_index_mapping[pci_bus]][pci_card];\n    if (slot != PCI_CARD_INVALID) {\n        if (pci_cards[slot].read)\n',
     '    /* KairoX86#228: device 0 of bus 0 below register 50h is the card there, if any */\n    if (pci_dev0_read && (pci_bus == 0) && (pci_card == 0) && (pci_func == 0) && (pci_index < 0x50))\n        return pci_dev0_read(pci_func, pci_index | (port & 0x03), pci_access_len, pci_dev0_priv);\n\n    slot = pci_card_to_slot_mapping[pci_bus_number_to_index_mapping[pci_bus]][pci_card];\n    if (slot != PCI_CARD_INVALID) {\n        if (pci_cards[slot].read)\n'),
    ('86box/src/pci.c',
     'static void\npci_clear_card(UNUSED(int pci_card))\n',
     '/* KairoX86#228: DOSBox-X\'s PCI bus has no host bridge, so its first card answers device 0. An\n   installed Windows that met a card there (eXo\'s Windows 95 image, its Voodoo Graphics) finds it\n   there again: the card answers the header and its own registers (00h-4Fh of function 0), and\n   the northbridge keeps the registers above, which the BIOS programs. */\nvoid\npci_add_card_dev0(uint8_t (*read)(int func, int addr, int len, void *priv),\n                  void (*write)(int func, int addr, int len, uint8_t val, void *priv), void *priv)\n{\n    if (pci_dev0_read)\n        fatal("pci_add_card_dev0(): device 0 already has a card\\n");\n    pci_dev0_read  = read;\n    pci_dev0_write = write;\n    pci_dev0_priv  = priv;\n}\n\nstatic void\npci_clear_card(UNUSED(int pci_card))\n'),
    ('86box/src/pci.c',
     '    pci_bus_number_to_index_mapping[0] = 0; /* always map bus 0 to index 0 */\n}\n',
     '    pci_bus_number_to_index_mapping[0] = 0; /* always map bus 0 to index 0 */\n\n    pci_dev0_read  = NULL;\n    pci_dev0_write = NULL;\n    pci_dev0_priv  = NULL;\n}\n'),
    ('86box/src/video/vid_voodoo.c',
     '    pci_add_card(PCI_ADD_NORMAL, voodoo_pci_read, voodoo_pci_write, voodoo, &voodoo->pci_slot);\n',
     '    /* KairoX86#228: "voodoo_pci_dev0 = 1" in 86box.cfg\'s [KairoX86] section puts it at device 0,\n       where DOSBox-X\'s PCI bus has it */\n    if (config_kairo_int("voodoo_pci_dev0", 0)) {\n        voodoo->pci_slot = PCI_CARD_INVALID;\n        pci_add_card_dev0(voodoo_pci_read, voodoo_pci_write, voodoo);\n    } else\n        pci_add_card(PCI_ADD_NORMAL, voodoo_pci_read, voodoo_pci_write, voodoo, &voodoo->pci_slot);\n'),
    ('86box/src/video/vid_voodoo.c',
     '#include <86box/vid_voodoo_texture.h>\n',
     '#include <86box/vid_voodoo_texture.h>\n#include <86box/config.h> /* KairoX86#228: config_kairo_int() */\n'),
]

# KairoX86#232, #233: the scanout on the GPU. With the machine's Hardware acceleration on
# (86box/kairo_gpu.h), a bitmap's pixels live in memory the GPU shares, and the lines the renderers
# would draw are queued for the GPU (core/kairo/gpu_scanout.c) as the guest scans them, with what
# they read: the packed 8bpp lines KairoX86#38 queues for its drawing thread, the 15, 16 and 32bpp
# lines left of hdisp (15 and 16 bits only through 86Box's own colour tables) and the text lines.
# A frame handed over (video_blit_memtoscreen), the SVGA drain points and a bitmap's end draw them
# all with one kernel (core/kairo/shaders/scanout.comp), so the frame is the one the CPU draws. A
# line goes to the GPU only where the installed renderer is the core's own: a card's renderer around
# it (the Rage 128's pixel doubler) may read or redraw the line at once. Off, nothing changes.
KAIROX86_GPU_SCANOUT = [
    ('86box/src/include/86box/video.h',
     'typedef struct bitmap_t {\n    int       w;\n    int       h;\n    uint32_t *dat;\n    uint32_t *line[2112];\n} bitmap_t;\n',
     'typedef struct bitmap_t {\n    int       w;\n    int       h;\n    uint32_t *dat;\n    uint32_t *line[2112];\n    void     *kairo_gpu; /* KairoX86#232: the GPU buffer dat lives in, with Hardware acceleration on */\n} bitmap_t;\n'),
    ('86box/src/video/video.c',
     '#include <86box/86box.h>\n#include "cpu.h"\n',
     '#include <86box/86box.h>\n#include <86box/kairo_gpu.h> /* KairoX86#232 */\n#include "cpu.h"\n'),
    ('86box/src/video/video.c',
     '    video_wait_for_blit_monitor(monitor_index);\n\n    automation_frame(x, y, w, h, monitor_index);\n',
     '    video_wait_for_blit_monitor(monitor_index);\n\n    /* KairoX86#233: the lines the GPU draws, drawn before the frame is shown */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_drain();\n\n    automation_frame(x, y, w, h, monitor_index);\n'),
    ('86box/src/video/video.c',
     'destroy_bitmap(bitmap_t *b)\n{\n    if ((b != NULL) && (b->dat != NULL))\n        free(b->dat);\n',
     'destroy_bitmap(bitmap_t *b)\n{\n    if ((b != NULL) && (b->kairo_gpu != NULL)) {\n        /* KairoX86#232: the lines queued for it drawn first */\n        kairo_gpu_scan_forget(b);\n        kairo_gpu_buffer_free(b->kairo_gpu);\n    } else if ((b != NULL) && (b->dat != NULL))\n        free(b->dat);\n'),
    ('86box/src/video/video.c',
     '    bitmap_t *b = calloc(1, sizeof(bitmap_t));\n\n    b->dat = calloc((size_t) x * y, 4);\n',
     '    bitmap_t *b = calloc(1, sizeof(bitmap_t));\n\n    if (kairo_gpu_on) {\n        /* KairoX86#232: the GPU draws into it too */\n        kairo_gpu_buffer_t *gpu = kairo_gpu_buffer((size_t) x * y * 4);\n        b->kairo_gpu            = gpu;\n        b->dat                  = gpu->data;\n    } else\n        b->dat = calloc((size_t) x * y, 4);\n'),
    ('86box/src/video/video.c',
     '    memset(monitors, 0, sizeof(monitors));\n    video_monitor_init(0);\n',
     "    /* KairoX86#233: the GPU's copy of the 15 and 16-bit colour tables */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_tables(video_15to32, video_16to32);\n\n    memset(monitors, 0, sizeof(monitors));\n    video_monitor_init(0);\n"),
    ('86box/src/video/vid_svga_render.c',
     '#include <86box/vid_svga_render_remap.h>\n',
     '#include <86box/vid_svga_render_remap.h>\n#include <86box/kairo_gpu.h> /* KairoX86#233 */\n'),
    ('86box/src/video/vid_svga_render.c',
     '#define lookup_lut(val) svga_lookup_lut_ram(svga, val)\n',
     "#define lookup_lut(val) svga_lookup_lut_ram(svga, val)\n\n/* KairoX86#233: the lines the GPU draws with the machine's Hardware acceleration on (86box/kairo_gpu.h).\n   A line goes to the GPU only where nothing else draws on it (render_async: no cursor, no overlay)\n   and the installed renderer is the core's own: a card's renderer around it (the Rage 128's pixel\n   doubler) may read or redraw the line as soon as the core's returns. */\nextern uint32_t svga_conv_16to32(struct svga_t *svga, uint16_t color, uint8_t bpp);\n\nstatic bool\nrender_gpu_indexed(const svga_t *svga)\n{\n    return (svga->render == svga_render_2bpp_lowres) || (svga->render == svga_render_2bpp_highres) ||\n           (svga->render == svga_render_4bpp_lowres) || (svga->render == svga_render_4bpp_highres) ||\n           (svga->render == svga_render_8bpp_lowres) || (svga->render == svga_render_8bpp_highres);\n}\n\n/* Queues a line starting at p; returns where its words dwords go, the queue locked until\n   kairo_gpu_scan_commit() */\nstatic uint32_t *\nrender_gpu_line(svga_t *svga, uint32_t *p, uint32_t kind, uint32_t count, uint32_t words, const uint32_t *palette,\n                uint32_t colours, uint32_t a, uint32_t flags)\n{\n    bitmap_t *bitmap = svga->monitor->target_buffer;\n    return kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (p - bitmap->dat), kind, count, words, palette, colours,\n                          a, 0, flags);\n}\n\n/* The packed 8bpp line's dwords wholly left of hdisp, from *memaddr on (moved as the CPU's drawing\n   moves it), to the GPU; returns how many pixels (0: none, the CPU draws them all) */\nstatic int\nrender_gpu_packed8(svga_t *svga, uint32_t *p, bool highres, uint32_t *memaddr)\n{\n    const uint32_t mask = svga->vram_display_mask;\n\n    if (!svga->render_async || svga->render_line_offset || ((mask + 1) & mask) || (svga->hdisp < 8) ||\n        (svga->hdisp > 2048) || !render_gpu_indexed(svga))\n        return 0;\n    const uint32_t dwords = (uint32_t) svga->hdisp / (highres ? 4 : 8);\n    const uint32_t pixels = dwords * (highres ? 4 : 8);\n    uint32_t      *words  = render_gpu_line(svga, p, KAIRO_SCAN_8, pixels, dwords, svga->map8, 256, svga->dac_mask,\n                                             highres ? 0 : KAIRO_SCAN_WIDE);\n    for (uint32_t c = 0; c < dwords; c++) {\n        memcpy(&words[c], &svga->vram[*memaddr & mask], 4);\n        *memaddr = (*memaddr + 4) & mask;\n    }\n    kairo_gpu_scan_commit();\n    return (int) pixels;\n}\n\n/* The line's pixels left of hdisp (a multiple of 8) in format 15, 16 or 32 to the GPU, from\n   svga->memaddr on, when eligible (the installed renderer is this one and converts as 86Box does by\n   default); returns how many (0: the CPU draws them all) */\nstatic int\nrender_gpu_direct(svga_t *svga, uint32_t *p, uint32_t format, bool eligible)\n{\n    const uint32_t mask   = svga->vram_display_mask;\n    const int      pixels = svga->hdisp & ~7;\n\n    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (pixels <= 0) ||\n        (pixels > 2048) || ((mask + 1) & mask))\n        return 0;\n    const uint32_t words  = (uint32_t) pixels * ((format == 32) ? 4 : 2) / 4;\n    /* 0x1f15: 15 bits mixed with the palette (svga_render_15bpp_mix_*) */\n    const bool     mix    = (format == 0x1f15);\n    const bool     lut    = ((format == 32) && svga->lut_map) || mix;\n    const uint32_t kind   = mix ? KAIRO_SCAN_15MIX : (format == 15) ? KAIRO_SCAN_15 : (format == 16) ? KAIRO_SCAN_16 : KAIRO_SCAN_32;\n    uint32_t      *line   = render_gpu_line(svga, p, kind, (uint32_t) pixels, words, lut ? svga->pallook : NULL,\n                                            lut ? 256 : 0, 0, 0);\n    uint32_t       memaddr = svga->memaddr;\n    for (uint32_t w = 0; w < words; w++) {\n        memcpy(&line[w], &svga->vram[memaddr & mask], 4);\n        memaddr += 4;\n    }\n    kairo_gpu_scan_commit();\n    return pixels;\n}\n\n/* A text line (svga_render_text_80, _40: dots 8 or 9 a cell, each drawn twice when wide) to the GPU:\n   every cell read and its colours resolved as the CPU's drawing does, svga->memaddr moved as it moves\n   it, and *col (text_80's shift register, or NULL) left as its drawing leaves it. Not the 256-colour\n   text mode (attribute mode bit 6). Returns whether the GPU draws the line. */\nstatic bool\nrender_gpu_text(svga_t *svga, uint32_t *p, uint32_t dots, bool wide, uint32_t *col)\n{\n    const uint32_t step  = dots * (wide ? 2 : 1);\n    const int      end   = svga->hdisp + svga->scrollcache;\n\n    /* A plane mask above the low nibble makes a dot's colour depend on the dot before it (text_80's\n       shift register), which the cells do not carry */\n    if (!kairo_gpu_on || !svga->render_async || (svga->attrregs[0x10] & 0x40) || (end <= 0) ||\n        (svga->plane_mask & ~0x0f) || (svga->render != (wide ? svga_render_text_40 : svga_render_text_80)))\n        return false;\n    const uint32_t cells = ((uint32_t) end + step - 1) / step;\n    uint32_t       colours[16];\n    for (int i = 0; i < 16; i++)\n        colours[i] = svga->pallook[svga->egapal[i & svga->plane_mask] & svga->dac_mask];\n    uint32_t *words = render_gpu_line(svga, p, KAIRO_SCAN_TEXT, cells * step, cells, colours, 16, dots,\n                                      wide ? KAIRO_SCAN_WIDE : 0);\n    for (uint32_t c = 0; c < cells; c++) {\n        uint32_t addr = 0;\n        uint8_t  chr;\n        uint8_t  attr;\n        uint32_t fg;\n        uint32_t bg;\n        if (!svga->force_old_addr)\n            addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;\n        const bool drawcursor = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);\n        if (svga->force_old_addr) {\n            chr  = svga->vram[(svga->memaddr << 1) & svga->vram_display_mask];\n            attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];\n        } else {\n            chr  = svga->vram[addr];\n            attr = svga->vram[addr + 1];\n        }\n        const uint32_t charaddr = ((attr & 8) ? svga->charsetb : svga->charseta) + (chr * 128);\n        if (drawcursor) {\n            bg = attr & 15;\n            fg = attr >> 4;\n        } else {\n            fg = attr & 15;\n            bg = attr >> 4;\n            if (attr & 0x80 && svga->attrregs[0x10] & 8) {\n                bg = (attr >> 4) & 7;\n                if (svga->blink & 16)\n                    fg = bg;\n            }\n        }\n        const uint8_t dat   = svga->vram[charaddr + (svga->scanline << 2)];\n        const bool    ninth = ((chr & ~0x1f) == 0xc0) && (svga->attrregs[0x10] & 4) && (dat & 1);\n        words[c]            = dat | (fg << 8) | (bg << 16) | (ninth ? (1u << 24) : 0);\n        if (col != NULL) {\n            for (uint32_t d = 0; d < dots; d++)\n                *col = (*col << 4) | ((d < 8) ? ((dat & (0x80 >> d)) ? fg : bg) : (ninth ? fg : bg));\n        }\n        svga->memaddr += 4;\n    }\n    svga->memaddr &= svga->vram_display_mask;\n    kairo_gpu_scan_commit();\n    return true;\n}\n\n/* The low-resolution line's pixels left of hdisp (svga_render_15bpp_lowres, _16bpp_lowres, _32bpp_lowres:\n   each pixel drawn twice) in format 15, 16 or 32 to the GPU, from svga->memaddr on, when eligible;\n   returns the loop's x after them (0: the CPU draws them all), the line drawn 2x pixels on */\nstatic int\nrender_gpu_wide(svga_t *svga, uint32_t *p, uint32_t format, bool eligible)\n{\n    const uint32_t mask = svga->vram_display_mask;\n    const int      x    = svga->hdisp & ~7;\n\n    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||\n        (x > 2048) || ((mask + 1) & mask))\n        return 0;\n    /* 15 and 16 bits: x advances 4 for each 2 dwords; 32 bits: 1 for each dword */\n    const uint32_t words  = (format == 32) ? (uint32_t) x : (uint32_t) x / 2;\n    const bool     mix    = (format == 0x1f15);\n    const bool     lut    = ((format == 32) && svga->lut_map) || mix;\n    const uint32_t kind   = mix ? KAIRO_SCAN_15MIX : (format == 15) ? KAIRO_SCAN_15 : (format == 16) ? KAIRO_SCAN_16 : KAIRO_SCAN_32;\n    uint32_t      *line   = render_gpu_line(svga, p, kind, (uint32_t) x * 2, words, lut ? svga->pallook : NULL,\n                                            lut ? 256 : 0, 0, KAIRO_SCAN_WIDE);\n    for (uint32_t w = 0; w < words; w++)\n        memcpy(&line[w], &svga->vram[(svga->memaddr + 4 * w) & mask], 4);\n    kairo_gpu_scan_commit();\n    return x;\n}\n\n/* The 24bpp line's groups of 4 pixels left of hdisp (svga_render_24bpp_highres, _lowres: each pixel drawn\n   twice when wide) to the GPU, read as the loop reads them (3 dwords a group) and svga->memaddr moved on\n   12 a group as it moves it, when eligible; returns the loop's x after them (0: the CPU draws them all) */\nstatic int\nrender_gpu_24(svga_t *svga, uint32_t *p, bool wide, bool eligible)\n{\n    const uint32_t mask   = svga->vram_display_mask;\n    const int      x      = svga->hdisp & ~7;\n\n    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||\n        (x > 2048) || ((mask + 1) & mask))\n        return 0;\n    const uint32_t groups = (uint32_t) x / 4;\n    uint32_t      *line   = render_gpu_line(svga, p, KAIRO_SCAN_24, (uint32_t) x * (wide ? 2 : 1), groups * 3,\n                                            svga->lut_map ? svga->pallook : NULL, svga->lut_map ? 256 : 0, 0,\n                                            wide ? KAIRO_SCAN_WIDE : 0);\n    for (uint32_t g = 0; g < groups; g++) {\n        memcpy(&line[g * 3], &svga->vram[svga->memaddr & mask], 4);\n        memcpy(&line[g * 3 + 1], &svga->vram[(svga->memaddr + 4) & mask], 4);\n        memcpy(&line[g * 3 + 2], &svga->vram[(svga->memaddr + 8) & mask], 4);\n        svga->memaddr += 12;\n    }\n    kairo_gpu_scan_commit();\n    return x;\n}\n\n/* The packed 8bpp line's steps of 8 pixels left of hdisp for the renderers that read their dwords in turn\n   (svga_render_8bpp_clone_highres; svga_render_8bpp_tseng_highres and _lowres, whose attribute register\n   14h nibble the palette takes in) to the GPU, svga->memaddr moved on 4 a dword as they move it, when\n   eligible; returns the pixels drawn (the loop's x after them; 0: the CPU draws them all) */\nstatic int\nrender_gpu_seq8(svga_t *svga, uint32_t *p, int dwords_per_step, bool wide, bool tseng, bool eligible)\n{\n    const uint32_t mask  = svga->vram_display_mask;\n    const int      x     = svga->hdisp & ~7;\n\n    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||\n        (x > 2048) || ((mask + 1) & mask))\n        return 0;\n    const uint32_t words = (uint32_t) (x / 8) * (uint32_t) dwords_per_step;\n    uint32_t       colours[256];\n    for (int v = 0; v < 256; v++) {\n        int c = v;\n        if (tseng && (svga->attrregs[0x10] & 0x80))\n            c = (c & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);\n        colours[v] = svga->map8[c & svga->dac_mask & 0xff];\n    }\n    uint32_t *line = render_gpu_line(svga, p, KAIRO_SCAN_8, (uint32_t) x, words, colours, 256, 0xff, wide ? KAIRO_SCAN_WIDE : 0);\n    for (uint32_t w = 0; w < words; w++) {\n        memcpy(&line[w], &svga->vram[svga->memaddr & mask], 4);\n        svga->memaddr += 4;\n    }\n    kairo_gpu_scan_commit();\n    return x;\n}\n"),
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_drain(void)\n{\n    if (render_thread == NULL)\n        return;\n',
     'void\nsvga_render_drain(void)\n{\n    if (kairo_gpu_on) {\n        /* KairoX86#233: the lines queued for the GPU, drawn */\n        kairo_gpu_scan_drain();\n        return;\n    }\n    if (render_thread == NULL)\n        return;\n'),
    ('86box/src/video/vid_svga_render.c',
     '        x = 0;\n        if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8) &&\n            (svga->hdisp <= RENDER_LINE_BYTES)) {\n',
     '        x = 0;\n        if (kairo_gpu_on) {\n            /* KairoX86#233: the dwords wholly left of hdisp to the GPU */\n            x = render_gpu_packed8(svga, p, highres, &memaddr);\n            p += x;\n        } else if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8) &&\n                   (svga->hdisp <= RENDER_LINE_BYTES)) {\n'),
    ('86box/src/video/vid_svga_render.c',
     '        xinc = (svga->seqregs[1] & 1) ? 8 : 9;\n\n        static uint32_t col = 0x00000000;\n\n',
     '        xinc = (svga->seqregs[1] & 1) ? 8 : 9;\n\n        static uint32_t col = 0x00000000;\n\n        /* KairoX86#233 */\n        if (render_gpu_text(svga, p, (uint32_t) xinc, false, &col))\n            return;\n\n'),
    ('86box/src/video/vid_svga_render.c',
     '        xinc = (svga->seqregs[1] & 1) ? 16 : 18;\n\n',
     '        xinc = (svga->seqregs[1] & 1) ? 16 : 18;\n\n        /* KairoX86#233 */\n        if (render_gpu_text(svga, p, (uint32_t) xinc / 2, true, NULL))\n            return;\n\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x]     = svga->conv_16to32(svga, dat & 0xffff, 15);\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            x = render_gpu_direct(svga, p, 15, (svga->render == svga_render_15bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));\n            for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x]     = svga->conv_16to32(svga, dat & 0xffff, 15);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                uint32_t dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x]         = svga->conv_16to32(svga, dat & 0xffff, 16);\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            x = render_gpu_direct(svga, p, 16, (svga->render == svga_render_16bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));\n            for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                uint32_t dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x]         = svga->conv_16to32(svga, dat & 0xffff, 16);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {\n                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                p[x] = lookup_lut(dat & 0xffffff);\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            x = render_gpu_direct(svga, p, 32, svga->render == svga_render_32bpp_highres);\n            for (; x <= (svga->hdisp + svga->scrollcache); x++) {\n                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                p[x] = lookup_lut(dat & 0xffffff);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            if (!svga->remap_required) {\n                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);\n',
     '            if (!svga->remap_required) {\n                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_direct(svga, p, 15, (svga->render == svga_render_15bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));\n                p += x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            if (!svga->remap_required) {\n                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);\n',
     '            if (!svga->remap_required) {\n                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_direct(svga, p, 16, (svga->render == svga_render_16bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));\n                p += x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            if (!svga->remap_required) {\n                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                    *p++ = lookup_lut(dat & 0xffffff);\n                }\n                svga->memaddr += (x * 4);\n',
     '            if (!svga->remap_required) {\n                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_direct(svga, p, 32, svga->render == svga_render_32bpp_highres);\n                p += x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x++) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                    *p++ = lookup_lut(dat & 0xffffff);\n                }\n                svga->memaddr += (x * 4);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            x = render_gpu_wide(svga, p, 15, (svga->render == svga_render_15bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));\n            for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 15);\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_wide(svga, p, 15, (svga->render == svga_render_15bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));\n                p += 2 * x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 15);\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x << 1] = p[(x << 1) + 1] = svga->conv_16to32(svga, dat & 0xffff, 16);\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            x = render_gpu_wide(svga, p, 16, (svga->render == svga_render_16bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));\n            for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n                p[x << 1] = p[(x << 1) + 1] = svga->conv_16to32(svga, dat & 0xffff, 16);\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 16);\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_wide(svga, p, 16, (svga->render == svga_render_16bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));\n                p += 2 * x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 16);\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                    *p++ = lookup_lut(dat & 0xffffff);\n                    *p++ = lookup_lut(dat & 0xffffff);\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_wide(svga, p, 32, svga->render == svga_render_32bpp_lowres);\n                p += 2 * x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x++) {\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);\n                    *p++ = lookup_lut(dat & 0xffffff);\n                    *p++ = lookup_lut(dat & 0xffffff);\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);\n\n                    *p++ = lookup_lut(dat0 & 0xffffff);\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_24(svga, p, false, svga->render == svga_render_24bpp_highres);\n                p += x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);\n\n                    *p++ = lookup_lut(dat0 & 0xffffff);\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = lookup_lut(dat0 & 0xffffff);\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                x = render_gpu_24(svga, p, true, svga->render == svga_render_24bpp_lowres);\n                p += 2 * x;\n                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);\n\n                    p[0] = p[1] = lookup_lut(dat0 & 0xffffff);\n'),
    ('86box/src/video/vid_svga_render.c',
     '        for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n            dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n            p[x << 1] = p[(x << 1) + 1] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);\n',
     '        /* KairoX86#233: the pixels left of hdisp to the GPU */\n        x = render_gpu_wide(svga, p, 0x1f15, (svga->render == svga_render_15bpp_mix_lowres) && (svga->conv_16to32 == svga_conv_16to32));\n        for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {\n            dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n            p[x << 1] = p[(x << 1) + 1] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);\n'),
    ('86box/src/video/vid_svga_render.c',
     '        for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n            dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n            p[x] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);\n',
     '        /* KairoX86#233: the pixels left of hdisp to the GPU */\n        x = render_gpu_direct(svga, p, 0x1f15, (svga->render == svga_render_15bpp_mix_highres) && (svga->conv_16to32 == svga_conv_16to32));\n        for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n            dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);\n            p[x] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);\n'),
    ('86box/src/video/vid_svga_render.c',
     '    for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += charwidth) {\n        if (load_counter == 0) {\n',
     "    /* KairoX86#233: the character clocks to the GPU, which draws their pixels (not ATI's 4-colour mode,\n       half pixels, packed 4bpp or a line offset, whose drawing reads or moves what it drew) */\n    uint32_t *gpu_clocks = NULL;\n    uint32_t  gpu_count  = 0;\n    if (kairo_gpu_on && svga->render_async && !svga->render_line_offset && !svga->ati_4color && !svga->half_pixel &&\n        !(combine8bits && svga->packed_4bpp) && render_gpu_indexed(svga) && ((svga->hdisp + svga->scrollcache) >= 0)) {\n        const uint32_t clocks = (uint32_t) ((svga->hdisp + svga->scrollcache) / charwidth) + 1;\n        uint32_t       colours[256];\n        if (combine8bits) {\n            for (int c = 0; c < 256; c++)\n                colours[c] = svga->map8[c & svga->dac_mask];\n        } else {\n            for (int c = 0; c < 16; c++)\n                colours[c] = svga->pallook[svga->egapal[c] & svga->dac_mask];\n        }\n        gpu_clocks = render_gpu_line(svga, p, combine8bits ? KAIRO_SCAN_NIBBLES8 : KAIRO_SCAN_NIBBLES,\n                                     clocks * (uint32_t) charwidth, clocks, colours, combine8bits ? 256 : 16, shift_values,\n                                     (dotwidth == 2) ? KAIRO_SCAN_WIDE : 0);\n    }\n    for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += charwidth) {\n        if (load_counter == 0) {\n"),
    ('86box/src/video/vid_svga_render.c',
     '        out_edat = ((out_edat & planemask & ~blinkmask) | ((out_edat | ~planemask) & blinkmask & blinkval)) ^ blinkmask;\n\n',
     "        out_edat = ((out_edat & planemask & ~blinkmask) | ((out_edat | ~planemask) & blinkmask & blinkval)) ^ blinkmask;\n\n        if (gpu_clocks != NULL) {\n            /* KairoX86#233: the clock to the GPU; col left as the pixel loop's last pair leaves it */\n            gpu_clocks[gpu_count++] = out_edat;\n            const uint32_t last_c0  = (out_edat >> ((shift_values >> 18) & 0x1C)) & 0xF;\n            const uint32_t last_c1  = (out_edat >> ((shift_values >> 21) & 0x1C)) & 0xF;\n            if (combine8bits)\n                col = svga->map8[((last_c0 << 4) | last_c1) & svga->dac_mask];\n            else if ((x + 6 - svga->scrollcache) & 0x01)\n                col = last_c1 << 4;\n            else\n                col = (last_c0 << 4) | last_c1;\n            p += charwidth;\n            continue;\n        }\n\n"),
    ('86box/src/video/vid_svga_render.c',
     '            p += (charwidth << 1);\n            // p += charwidth;\n        else\n            p += charwidth;\n    }\n    }\n',
     '            p += (charwidth << 1);\n            // p += charwidth;\n        else\n            p += charwidth;\n    }\n    if (gpu_clocks != NULL)\n        kairo_gpu_scan_commit(); /* KairoX86#233 */\n    }\n'),
    ('86box/src/video/vid_svga_render.c',
     '        for (int x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n            if (svga->attrregs[0x10] & 0x80)\n',
     '        /* KairoX86#233: the pixels left of hdisp to the GPU */\n        const int gpu_x = render_gpu_seq8(svga, p, 2, false, true, svga->render == svga_render_8bpp_tseng_highres);\n        p += gpu_x;\n        for (int x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n            if (svga->attrregs[0x10] & 0x80)\n'),
    ('86box/src/video/vid_svga_render.c',
     '        for (int x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n            if (svga->attrregs[0x10] & 0x80)\n',
     '        /* KairoX86#233: the pixels left of hdisp to the GPU */\n        const int gpu_x = render_gpu_seq8(svga, p, 1, true, true, svga->render == svga_render_8bpp_tseng_lowres);\n        p += gpu_x;\n        for (int x = gpu_x; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n            if (svga->attrregs[0x10] & 0x80)\n'),
    ('86box/src/video/vid_svga_render.c',
     '            for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                svga->memaddr += 8;\n                p += 8;\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    } else {\n        changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            if (!svga->remap_required) {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 8;\n                    p += 8;\n                }\n            } else {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {\n                    addr = svga->remap_func(svga, svga->memaddr);\n                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 4;\n                    p += 4;\n                }\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    }\n}\n\n',
     '            /* KairoX86#233: the pixels left of hdisp to the GPU */\n            const int gpu_x = render_gpu_seq8(svga, p, 2, false, false, svga->render == svga_render_8bpp_clone_highres);\n            p += gpu_x;\n            for (x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                svga->memaddr += 8;\n                p += 8;\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    } else {\n        changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            if (!svga->remap_required) {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 8;\n                    p += 8;\n                }\n            } else {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {\n                    addr = svga->remap_func(svga, svga->memaddr);\n                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 4;\n                    p += 4;\n                }\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    }\n}\n\n'),
    ('86box/src/video/vid_svga_render.c',
     '                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 8;\n                    p += 8;\n                }\n            } else {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {\n                    addr = svga->remap_func(svga, svga->memaddr);\n                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 4;\n                    p += 4;\n                }\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    }\n}\n\n',
     '                /* KairoX86#233: the pixels left of hdisp to the GPU */\n                const int gpu_x = render_gpu_seq8(svga, p, 2, false, false, svga->render == svga_render_8bpp_clone_highres);\n                p += gpu_x;\n                for (x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {\n                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);\n                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 8;\n                    p += 8;\n                }\n            } else {\n                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {\n                    addr = svga->remap_func(svga, svga->memaddr);\n                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);\n                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];\n                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];\n                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];\n                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];\n\n                    svga->memaddr += 4;\n                    p += 4;\n                }\n            }\n            svga->memaddr &= svga->vram_display_mask;\n        }\n    }\n}\n\n'),
]

# KairoX86#241: the IBM CGA's display on the GPU (on #233's scanout queue). With Hardware
# acceleration on, cga_render hands each line's characters or pixel bytes, read as it reads them, to
# the queue with the colours video_process_8 gives them; the line's in-place conversion then runs
# over pixels the GPU overwrites at the drain, which comes before cga_interpolate reads the picture.
# Composite output and the light pen read the picture on the CPU, so their lines stay there.
KAIROX86_GPU_CGA = [
    ('86box/src/video/vid_cga.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <86box/kairo_gpu.h> /* KairoX86#241 */\n'),
    ('86box/src/video/vid_cga.c',
     '\nstatic void\ncga_render(cga_t *cga, int line)\n',
     "\n/* KairoX86#241: line [line]'s characters or pixels (cga_render's, read as it reads them) to the GPU's\n   scanout queue (86box/kairo_gpu.h), coloured as video_process_8 will colour them; returns whether the\n   GPU draws them. Not with composite output or the light pen, which read the picture back. */\nstatic bool\ncga_render_gpu(cga_t *cga, int line)\n{\n    if (!kairo_gpu_on || cga->composite || cga_lightpen_enabled)\n        return false;\n    bitmap_t       *bitmap     = buffer32;\n    uint32_t       *pixels     = &bitmap->line[line][8];\n    const uint32_t  out        = (uint32_t) (pixels - bitmap->dat);\n    const uint32_t *palette    = pal_lookup;\n    const int       hdisp      = cga->crtc[CGA_CRTC_HDISP];\n    const bool      enabled    = (cga->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) != 0;\n    uint16_t        cursoraddr = (cga->crtc[CGA_CRTC_CURSOR_ADDR_LOW] | (cga->crtc[CGA_CRTC_CURSOR_ADDR_HIGH] << 8)) & DEVICE_VRAM_MASK;\n\n    if (hdisp <= 0)\n        return false;\n    if (!(cga->cgamode & CGA_MODE_FLAG_GRAPHICS)) {\n        /* Text: 80 columns of 8 dots, or 40 of 8 doubled */\n        const bool highres = (cga->cgamode & CGA_MODE_FLAG_HIGHRES) != 0;\n        uint32_t  *cells   = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, (uint32_t) hdisp * (highres ? 8 : 16),\n                                            (uint32_t) hdisp, palette, 256, 8, 0, highres ? 0 : KAIRO_SCAN_WIDE);\n        for (int x = 0; x < hdisp; x++) {\n            uint8_t chr = 0;\n            uint8_t attr = 0;\n            if (enabled) {\n                if (highres) {\n                    chr  = cga->charbuffer[x << 1];\n                    attr = cga->charbuffer[(x << 1) + 1];\n                } else {\n                    chr  = cga->vram[(cga->memaddr << 1) & DEVICE_VRAM_MASK];\n                    attr = cga->vram[((cga->memaddr << 1) + 1) & DEVICE_VRAM_MASK];\n                }\n            }\n            const bool drawcursor = ((cga->memaddr == cursoraddr) && cga->cursorvisible && cga->cursoron);\n            uint32_t   fg         = (attr & 15) + 16;\n            uint32_t   bg;\n            if (cga->cgamode & CGA_MODE_FLAG_BLINK) {\n                bg = ((attr >> 4) & 7) + 16;\n                if ((cga->cgablink & 8) && (attr & 0x80) && (!highres || !cga->drawcursor))\n                    fg = bg;\n            } else\n                bg = (attr >> 4) + 16;\n            const uint32_t flip = drawcursor ? 0b1111 : 0;\n            cells[x] = fontdat[chr + cga->fontbase][cga->scanline & 7] | ((fg ^ flip) << 8) | ((bg ^ flip) << 16);\n            cga->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n\n    /* Graphics: 2 bytes a character, 8 pixels of 2 bits doubled, or 16 of 1 bit */\n    uint32_t   colours[4];\n    const bool hires = (cga->cgamode & CGA_MODE_FLAG_HIGHRES_GRAPHICS) != 0;\n    if (!hires) {\n        const int col = (cga->cgacol & 16) ? 24 : 16;\n        colours[0]    = palette[(cga->cgacol & 15) | 16];\n        if (cga->cgamode & CGA_MODE_FLAG_BW) {\n            colours[1] = palette[col | 3];\n            colours[2] = palette[col | 4];\n            colours[3] = palette[col | 7];\n        } else if (cga->cgacol & 32) {\n            colours[1] = palette[col | 3];\n            colours[2] = palette[col | 5];\n            colours[3] = palette[col | 7];\n        } else {\n            colours[1] = palette[col | 2];\n            colours[2] = palette[col | 4];\n            colours[3] = palette[col | 6];\n        }\n    } else {\n        colours[0] = palette[0];\n        colours[1] = palette[(cga->cgacol & 15) + 16];\n    }\n    uint32_t *words = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, (uint32_t) hdisp * 16,\n                                     ((uint32_t) hdisp * 2 + 3) / 4, colours, hires ? 2 : 4, hires ? 1 : 2, 0,\n                                     hires ? 0 : KAIRO_SCAN_WIDE);\n    uint8_t *bytes = (uint8_t *) words;\n    for (int x = 0; x < hdisp; x++) {\n        const uint32_t at = ((cga->memaddr << 1) & 0x1fff) + ((cga->scanline & 1) * 0x2000);\n        bytes[x * 2]       = enabled ? cga->vram[at] : 0;\n        bytes[x * 2 + 1]   = enabled ? cga->vram[at + 1] : 0;\n        cga->memaddr++;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nstatic void\ncga_render(cga_t *cga, int line)\n"),
    ('86box/src/video/vid_cga.c',
     '            pixels[column + (cga->crtc[CGA_CRTC_HDISP] * 16) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n    }\n\n',
     '            pixels[column + (cga->crtc[CGA_CRTC_HDISP] * 16) + 8] = overlay_flag ? 0 : ((cga->cgacol & 0b1111) + 16);\n    }\n\n    /* KairoX86#241: the GPU draws the line between the borders */\n    if (cga_render_gpu(cga, line))\n        return;\n\n'),
    ('86box/src/video/vid_cga.c',
     'cga_blit_memtoscreen(int x, int y, int w, int h, int double_type)\n{\n    if (double_type > DOUBLE_SIMPLE)\n',
     'cga_blit_memtoscreen(int x, int y, int w, int h, int double_type)\n{\n    /* KairoX86#241: the lines the GPU draws, drawn before the doubling reads them */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_drain();\n    if (double_type > DOUBLE_SIMPLE)\n'),
    ('86box/src/video/vid_cga.c',
     '    bool     overlay_flag          = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag);\n\n    for (column = 0; column < 8; ++column) {\n',
     '    bool     overlay_flag          = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag);\n\n    /* KairoX86#241: a line the GPU still has to draw is drawn before the CPU draws on it again */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (pixels - buffer32->dat), (uint32_t) buffer32->w);\n\n    for (column = 0; column < 8; ++column) {\n'),
    ('86box/src/video/vid_cga.c',
     '    int col = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag) ? 0 : (cga->cgacol & 15) + 16;\n\n',
     '    int col = ((cga->cgamode & highres_graphics_flag) == highres_graphics_flag) ? 0 : (cga->cgacol & 15) + 16;\n\n    /* KairoX86#241: a line the GPU still has to draw is drawn before the CPU blanks it */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[line] - buffer32->dat), (uint32_t) buffer32->w);\n\n'),
]

# KairoX86#284: a frame handed over is copied whole. video_blit_memtoscreen only woke the blit
# thread, and the emulation ran on, drawing the next frame's first lines into the bitmap the blit
# thread was copying (a CGA's BIOS screen showed a mix of two frames, and the picture depended on
# the threads' timing). The hand-over now waits until the frontend has copied the picture
# (video_blit_complete, buffer_in_use), so every frame's picture is that frame.
KAIROX86_WHOLE_FRAMES = [
    ('86box/src/video/video.c',
     '    monitors[monitor_index].mon_renderedframes++;\n\n    thread_set_event(monitors[monitor_index].mon_blit_data_ptr->wake_blit_thread);\n',
     '    monitors[monitor_index].mon_renderedframes++;\n\n    thread_set_event(monitors[monitor_index].mon_blit_data_ptr->wake_blit_thread);\n    /* KairoX86#284: nothing draws on the frame until its picture is copied */\n    video_wait_for_buffer_monitor(monitor_index);\n'),
]

# KairoX86#263: the IBM MDA's display on the GPU (#233's scanout queue). With Hardware acceleration
# on, mda_render_gpu takes each line's characters as mda_poll reads them, its colours resolved to the
# indexes it would draw (RGBI or the attribute table, underline, the ninth column, the cursor's XOR),
# and the GPU draws them with the colours video_process_8 gives them; the in-place conversion then
# runs over pixels the GPU overwrites at the drain.
KAIROX86_GPU_MDA = [
    ('86box/src/video/vid_mda.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#263 */\n'),
    ('86box/src/video/vid_mda.c',
     '\nvoid\nmda_poll(void *priv)\n',
     "\n/* KairoX86#263: the line's characters (mda_poll's, read as it reads them) to the GPU's scanout queue\n   (86box/kairo_gpu.h), as the colour indexes it would draw, coloured as video_process_8 colours them;\n   returns whether the GPU draws them, mda->memaddr moved as the drawing moves it. */\nstatic bool\nmda_render_gpu(mda_t *mda, uint16_t cursoraddr)\n{\n    const uint32_t hdisp = mda->crtc[MDA_CRTC_HDISP];\n    if (!kairo_gpu_on || (hdisp == 0))\n        return false;\n    bitmap_t      *bitmap = buffer32;\n    uint32_t      *pixels = &bitmap->line[mda->displine][0];\n    const bool     rgbi   = (mda->monitor_type == MDA_MONITOR_TYPE_RGBI) && !(mda->mode & MDA_MODE_BW);\n    uint32_t      *cells  = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (pixels - bitmap->dat), KAIRO_SCAN_TEXT,\n                                           hdisp * 9, hdisp, pal_lookup, 256, 9, 0, 0);\n    for (uint32_t x = 0; x < hdisp; x++) {\n        const uint8_t chr        = mda->vram[(mda->memaddr << 1) & 0xfff];\n        const uint8_t attr       = mda->vram[((mda->memaddr << 1) + 1) & 0xfff];\n        const bool    drawcursor = ((mda->memaddr == cursoraddr) && mda->cursorvisible && mda->cursoron);\n        const int32_t blink      = ((mda->blink & 16) && (mda->mode & MDA_MODE_BLINK) && (attr & 0x80) && !drawcursor);\n        int32_t       color_bg   = 0;\n        int32_t       color_fg   = 0;\n        if (rgbi) {\n            color_bg = (attr >> 4) & 0x0F;\n            color_fg = (attr & 0x0F);\n            if ((mda->mode & MDA_MODE_BLINK) && (color_bg & 0x8))\n                color_bg &= ~(0x8);\n            const bool special_treatment = (color_bg != 0 && color_bg != 7);\n            if (color_fg == MDA_COLOR_GREY && special_treatment)\n                color_fg = MDA_COLOR_BRIGHT_WHITE;\n            if (color_fg == 0 && special_treatment)\n                color_fg = MDA_COLOR_GREY;\n            if (color_fg == MDA_COLOR_GREY && (color_bg == MDA_COLOR_GREY || color_bg == MDA_COLOR_BLACK))\n                color_fg = MDA_COLOR_BLACK;\n        }\n        uint32_t fg = rgbi ? (uint32_t) (CGAPAL_CGA_START + color_fg) : (uint32_t) mda_attr_to_color_table[attr][blink][1];\n        uint32_t bg = rgbi ? (uint32_t) (CGAPAL_CGA_START + color_bg) : (uint32_t) mda_attr_to_color_table[attr][blink][0];\n        uint32_t dat;\n        bool     ninth;\n        if ((mda->scanline == 12) && ((attr & 7) == 1)) {\n            /* Underline: all nine dots the foreground */\n            dat   = 0xff;\n            ninth = true;\n        } else {\n            dat   = fontdatm[chr + mda->fontbase][mda->scanline];\n            ninth = ((chr & ~0x1f) == 0xc0) && (dat & 1);\n        }\n        if (drawcursor) {\n            const uint32_t flip = rgbi ? (uint32_t) (CGAPAL_CGA_START + color_fg) : (uint32_t) mda_attr_to_color_table[attr][0][1];\n            fg ^= flip;\n            bg ^= flip;\n        }\n        cells[x] = dat | ((fg & 0xff) << 8) | ((bg & 0xff) << 16) | (ninth ? (1u << 24) : 0);\n        mda->memaddr++;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nvoid\nmda_poll(void *priv)\n"),
    ('86box/src/video/vid_mda.c',
     '            mda->lastline = mda->displine;\n\n            for (uint32_t x = 0; x < mda->crtc[MDA_CRTC_HDISP]; x++) {\n',
     '            mda->lastline = mda->displine;\n\n            /* KairoX86#263: no character left for the CPU when the GPU draws them */\n            for (uint32_t x = mda_render_gpu(mda, cursoraddr) ? mda->crtc[MDA_CRTC_HDISP] : 0; x < mda->crtc[MDA_CRTC_HDISP]; x++) {\n'),
]

# KairoX86#257: the Hercules' display on the GPU (#233's scanout queue). With Hardware acceleration
# on, hercules_render_gpu takes each line as hercules_poll reads it: its text cells (the attribute
# table, underline, the ninth column, the cursor's XOR) or its graphics bytes (1 bit a pixel), and
# the GPU draws them with the colours video_process_8 gives them. Graphics with the blend option on
# stay on the CPU (video_blend mixes pixels already drawn).
KAIROX86_GPU_HERCULES = [
    ('86box/src/video/vid_hercules.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#257 */\n'),
    ('86box/src/video/vid_hercules.c',
     '            hercules_render_overscan_left(dev);\n\n            if (dev->ctrl & 0x02) {\n',
     '            hercules_render_overscan_left(dev);\n\n            if (hercules_render_gpu(dev, cursoraddr)) {\n                /* KairoX86#257: the GPU draws the line */\n            } else if (dev->ctrl & 0x02) {\n'),
    ('86box/src/video/vid_hercules.c',
     '\nstatic void\nhercules_poll(void *priv)\n',
     "\n/* KairoX86#257: the line (hercules_poll's, read as it reads it) to the GPU's scanout queue\n   (86box/kairo_gpu.h), coloured as video_process_8 colours it; returns whether the GPU draws it,\n   dev->memaddr moved as the drawing moves it. */\nstatic bool\nhercules_render_gpu(hercules_t *dev, uint16_t cursoraddr)\n{\n    const uint32_t columns = dev->crtc[1];\n    if (!kairo_gpu_on || (columns == 0) || ((dev->ctrl & 0x02) && herc_blend))\n        return false; /* the CPU draws it: hercules_render_overscan_left drew the row's queued drawing first */\n    bitmap_t      *bitmap = buffer32;\n    uint32_t      *pixels = &bitmap->line[dev->displine + 14][8];\n    const uint32_t out    = (uint32_t) (pixels - bitmap->dat);\n    if (dev->ctrl & 0x02) {\n        /* Graphics: 16 pixels of 1 bit a column, colour 7 or 0 */\n        uint32_t base = (dev->scanline & 3) * 0x2000;\n        if (dev->ctrl & 0x80)\n            base += 0x8000;\n        const uint32_t colours[2] = { pal_lookup[0], pal_lookup[7] };\n        uint8_t       *bytes      = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, columns * 16,\n                                                               (columns * 2 + 3) / 4, colours, 2, 1, 0, 0);\n        for (uint32_t x = 0; x < columns; x++) {\n            const uint32_t at = ((dev->memaddr << 1) & 0x1fff) + base;\n            bytes[x * 2]      = (dev->ctrl & 8) ? dev->vram[at] : 0;\n            bytes[x * 2 + 1]  = (dev->ctrl & 8) ? dev->vram[at + 1] : 0;\n            dev->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n    uint32_t *cells = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, columns * 9, columns, pal_lookup, 256, 9, 0, 0);\n    for (uint32_t x = 0; x < columns; x++) {\n        uint8_t chr  = 0;\n        uint8_t attr = 0;\n        if (dev->ctrl & 8) {\n            chr  = dev->charbuffer[x << 1];\n            attr = dev->charbuffer[(x << 1) + 1];\n        }\n        const bool drawcursor = ((dev->memaddr == cursoraddr) && dev->cursorvisible && dev->cursoron);\n        const int  blink      = ((dev->blink & 16) && (dev->ctrl & 0x20) && (attr & 0x80) && !drawcursor);\n        uint32_t   fg         = dev->cols[attr][blink][1];\n        uint32_t   bg         = dev->cols[attr][blink][0];\n        uint32_t   dat;\n        bool       ninth;\n        if ((dev->scanline == 12) && ((attr & 7) == 1)) {\n            dat   = 0xff;\n            ninth = true;\n        } else {\n            dat   = fontdatm[chr][dev->scanline];\n            ninth = ((chr & ~0x1f) == 0xc0) && (dat & 1);\n        }\n        if (dev->ctrl2 & 0x01)\n            dev->memaddr = (dev->memaddr + 1) & 0x3fff;\n        else\n            dev->memaddr = (dev->memaddr + 1) & 0x7ff;\n        if (drawcursor) {\n            fg ^= dev->cols[attr][0][1];\n            bg ^= dev->cols[attr][0][1];\n        }\n        cells[x] = dat | ((fg & 0xff) << 8) | ((bg & 0xff) << 16) | (ninth ? (1u << 24) : 0);\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nstatic void\nhercules_poll(void *priv)\n"),
    ('86box/src/video/vid_hercules.c',
     '    if (width == 0)\n        return;\n\n    for (uint8_t i = 0; i < 8; i++)\n        buffer32->line[dev->displine + 14][i] = 0x00000000;\n',
     '    if (width == 0)\n        return;\n\n    /* KairoX86#257: a row the GPU still has to draw is drawn before the CPU draws on it again */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[dev->displine + 14] - buffer32->dat), (uint32_t) buffer32->w);\n\n    for (uint8_t i = 0; i < 8; i++)\n        buffer32->line[dev->displine + 14][i] = 0x00000000;\n'),
    ('86box/src/video/vid_hercules.c',
     '                            p = &(buffer32->line[(dev->firstline + yy) & 0x7ff][0]);\n\n                            for (xx = 0; xx < (x + 16); xx++)\n',
     '                            p = &(buffer32->line[(dev->firstline + yy) & 0x7ff][0]);\n                            /* KairoX86#257: a queued row drawn before the CPU blanks it */\n                            if (kairo_gpu_on)\n                                kairo_gpu_scan_touch(buffer32, (uint32_t) (p - buffer32->dat), (uint32_t) (x + 16));\n\n                            for (xx = 0; xx < (x + 16); xx++)\n'),
    ('86box/src/video/vid_hercules.c',
     '                            p = &(buffer32->line[(dev->firstline + 14 + y + yy) & 0x7ff][0]);\n\n                            for (xx = 0; xx < (x + 16); xx++)\n',
     '                            p = &(buffer32->line[(dev->firstline + 14 + y + yy) & 0x7ff][0]);\n                            /* KairoX86#257: a queued row drawn before the CPU blanks it */\n                            if (kairo_gpu_on)\n                                kairo_gpu_scan_touch(buffer32, (uint32_t) (p - buffer32->dat), (uint32_t) (x + 16));\n\n                            for (xx = 0; xx < (x + 16); xx++)\n'),
]

# KairoX86#259: the Hercules Plus' display on the GPU (#233's scanout queue). With Hardware
# acceleration on, herculesplus_render_gpu takes each line as herculesplus_poll reads it: its text
# cells, resolved as draw_char_rom/_ram4/_ram48 resolve them (the font, blink, underline, the ninth
# column, the cursor), or its graphics bytes (1 bit a pixel); the GPU draws them with the colours
# video_process_8 gives them. Graphics with the blend option on stay on the CPU.
KAIROX86_GPU_HERCULES_PLUS = [
    ('86box/src/video/vid_hercules_plus.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#259 */\n'),
    ('86box/src/video/vid_hercules_plus.c',
     '\nstatic void\nherculesplus_poll(void *priv)\n',
     "\n/* KairoX86#259: a text cell's 9-dot pattern and colour indexes, as draw_char_rom, _ram4 and _ram48\n   resolve them (the font the extended mode register picks, blink, the MDA attributes, underline, the\n   ninth column) */\nstatic void\nherculesplus_cell(herculesplus_t *dev, uint8_t chr, uint8_t attr, unsigned *ifg_out, unsigned *ibg_out, unsigned *val_out)\n{\n    const int      mode = dev->crtc[HERCULESPLUS_CRTC_XMODE] & 5;\n    const uint8_t *fnt;\n    if (mode == 5) {\n        int font = (attr & 0x0F);\n        if (font >= 12)\n            font &= 7;\n        attr = (attr >> 4) ^ 0x0f;\n        fnt  = dev->vram + 0x4000 + 16 * chr + 4096 * font + dev->scanline;\n    } else if (mode == 1)\n        fnt = dev->vram + 0x4000 + 16 * chr + dev->scanline;\n    else\n        fnt = &(fontdatm[chr][dev->scanline]);\n    int blk = 0;\n    if (dev->ctrl & HERCULESPLUS_CTRL_BLINK) {\n        if (attr & 0x80)\n            blk = (dev->blink & 16);\n        attr &= 0x7f;\n    }\n    unsigned ibg = 0;\n    unsigned ifg = 7;\n    if ((attr & 0x77) == 0x70) {\n        ifg = 0;\n        ibg = 7;\n    }\n    if (attr & 8)\n        ifg |= 8;\n    if (attr & 0x80)\n        ibg |= 8;\n    if ((attr & 0x77) == 0)\n        ifg = ibg;\n    const unsigned ull = ((attr & 0x07) == 1) ? 13 : 0xffff;\n    const int      elg = (dev->crtc[HERCULESPLUS_CRTC_XMODE] & HERCULESPLUS_XMODE_90COL) ? 0 : ((chr >= 0xc0) && (chr <= 0xdf));\n    unsigned       val;\n    if (blk)\n        val = 0x000;\n    else if (dev->scanline == ull)\n        val = 0x1ff;\n    else {\n        val = fnt[0] << 1;\n        if (elg)\n            val |= (val >> 1) & 1;\n    }\n    *ifg_out = ifg;\n    *ibg_out = ibg;\n    *val_out = val;\n}\n\n/* KairoX86#259: the line (herculesplus_poll's, read as text_line or graphics_line reads it) to the GPU's\n   scanout queue (86box/kairo_gpu.h), coloured as video_process_8 colours it; returns whether the GPU\n   draws it, dev->memaddr moved as the drawing moves it. */\nstatic bool\nherculesplus_render_gpu(herculesplus_t *dev, uint16_t cursoraddr)\n{\n    const uint32_t columns  = dev->crtc[1];\n    const bool     graphics = (dev->ctrl & HERCULESPLUS_CTRL_GRAPH) && (dev->ctrl2 & HERCULESPLUS_CTRL2_GRAPH);\n    if (!kairo_gpu_on)\n        return false;\n    bitmap_t      *bitmap = buffer32;\n    const uint32_t out    = (uint32_t) (bitmap->line[dev->displine] - bitmap->dat);\n    if ((columns == 0) || (graphics && herc_blend)) {\n        /* The CPU draws the line: a queued drawing of the row (the frame restarted) first */\n        kairo_gpu_scan_touch(bitmap, out, (uint32_t) bitmap->w);\n        return false;\n    }\n    if (graphics) {\n        uint32_t base = (dev->scanline & 3) * 0x2000;\n        if ((dev->ctrl & HERCULESPLUS_CTRL_PAGE1) && (dev->ctrl2 & HERCULESPLUS_CTRL2_PAGE1))\n            base += 0x8000;\n        const uint32_t colours[2] = { pal_lookup[0], pal_lookup[7] };\n        uint8_t       *bytes      = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, columns * 16,\n                                                               (columns * 2 + 3) / 4, colours, 2, 1, 0, 0);\n        for (uint32_t x = 0; x < columns; x++) {\n            const uint32_t at = ((dev->memaddr << 1) & 0x1fff) + base;\n            bytes[x * 2]      = (dev->ctrl & 8) ? dev->vram[at] : 0;\n            bytes[x * 2 + 1]  = (dev->ctrl & 8) ? dev->vram[at + 1] : 0;\n            dev->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n    const uint32_t cw    = (uint32_t) HERCULESPLUS_CW;\n    uint32_t      *cells = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, columns * cw, columns, pal_lookup, 256, cw, 0, 0);\n    for (uint32_t x = 0; x < columns; x++) {\n        uint8_t chr  = 0;\n        uint8_t attr = 0;\n        if (dev->ctrl & 8) {\n            chr  = dev->vram[(dev->memaddr << 1) & 0x3fff];\n            attr = dev->vram[((dev->memaddr << 1) + 1) & 0x3fff];\n        }\n        const bool drawcursor = ((dev->memaddr == cursoraddr) && dev->cursorvisible && dev->cursoron);\n        unsigned   fg;\n        unsigned   bg;\n        unsigned   val;\n        herculesplus_cell(dev, chr, attr, &fg, &bg, &val);\n        if (drawcursor)\n            fg = bg = (unsigned) dev->cols[attr][0][1];\n        cells[x] = ((val >> 1) & 0xff) | ((fg & 0xff) << 8) | ((bg & 0xff) << 16) | ((val & 1) ? (1u << 24) : 0);\n        ++dev->memaddr;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nstatic void\nherculesplus_poll(void *priv)\n"),
    ('86box/src/video/vid_hercules_plus.c',
     '            dev->lastline = dev->displine;\n            if ((dev->ctrl & HERCULESPLUS_CTRL_GRAPH) && (dev->ctrl2 & HERCULESPLUS_CTRL2_GRAPH))\n                graphics_line(dev);\n',
     '            dev->lastline = dev->displine;\n            if (herculesplus_render_gpu(dev, cursoraddr)) {\n                /* KairoX86#259: the GPU draws the line */\n            } else if ((dev->ctrl & HERCULESPLUS_CTRL_GRAPH) && (dev->ctrl2 & HERCULESPLUS_CTRL2_GRAPH))\n                graphics_line(dev);\n'),
]

# KairoX86#258: the Hercules InColor's display on the GPU (#233's scanout queue). With Hardware
# acceleration on, incolor_render_gpu takes each line as incolor_poll reads it: its text cells,
# resolved as draw_char_rom/_ram4/_ram48 resolve them into four planes' dots and the masks a dot's
# colour comes from (attributes, blink, bold, underline, strike-through, the ninth column, the
# cursor), or its four graphics planes; the GPU draws them through the card's palette.
KAIROX86_GPU_INCOLOR = [
    ('86box/src/video/vid_hercules_incolor.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#258 */\n'),
    ('86box/src/video/vid_hercules_incolor.c',
     '\nstatic void\nincolor_poll(void *priv)\n',
     "\n/* KairoX86#258: a text cell as draw_char_rom, _ram4 or _ram48 resolves it: each plane's 9-dot pattern\n   (planes[]) and the masks a dot's colour takes its plane's bit from, f where the plane's dot is set,\n   b where it is not */\nstatic void\nincolor_cell(incolor_t *dev, uint8_t chr, uint8_t attr, unsigned planes[4], unsigned *f, unsigned *b)\n{\n    const int mode    = dev->crtc[INCOLOR_CRTC_XMODE] & 5;\n    const int blink   = dev->ctrl & INCOLOR_CTRL_BLINK;\n    const int altattr = dev->crtc[INCOLOR_CRTC_EXCEPT] & INCOLOR_EXCEPT_ALTATTR;\n    const int elg     = (dev->crtc[INCOLOR_CRTC_XMODE] & INCOLOR_XMODE_90COL) ? 0 : ((chr >= 0xc0) && (chr <= 0xdf));\n    if ((mode == 0) || (mode == 4) || (mode == 1)) {\n        /* draw_char_rom and draw_char_ram4 */\n        int blk = 0;\n        if (blink) {\n            if (attr & 0x80)\n                blk = (dev->blink & 16);\n            attr &= 0x7f;\n        }\n        unsigned ifg;\n        unsigned ibg;\n        unsigned ull;\n        if (altattr) {\n            ibg = 0;\n            ifg = 7;\n            if ((attr & 0x77) == 0x70) {\n                ifg = 0;\n                ibg = 7;\n            }\n            if (attr & 8)\n                ifg |= 8;\n            if (attr & 0x80)\n                ibg |= 8;\n            if ((attr & 0x77) == 0)\n                ifg = ibg;\n            ull = ((attr & 0x07) == 1) ? 13 : 0xffff;\n        } else {\n            ull = 0xffff;\n            ifg = attr & 0x0F;\n            ibg = (attr >> 4) & 0x0F;\n        }\n        for (int p = 0; p < 4; p++) {\n            unsigned val;\n            if (blk)\n                val = 0x000;\n            else if (dev->scanline == ull)\n                val = 0x1ff;\n            else {\n                const unsigned char *fnt = (mode == 1) ? (dev->vram + 0x4000 + 16 * chr + dev->scanline + 0x10000 * p)\n                                                       : &(fontdatm[chr][dev->scanline]);\n                val = fnt[0] << 1;\n                if (elg)\n                    val |= (val >> 1) & 1;\n            }\n            planes[p] = val;\n        }\n        *f = ifg;\n        *b = ibg;\n        if ((mode == 1) && altattr && ((attr & 0x77) == 0))\n            *f = *b = ibg; /* draw_char_ram4's blank attribute */\n        return;\n    }\n    /* draw_char_ram48 */\n    int font = (attr & 0x0F);\n    if (font >= 12)\n        font &= 7;\n    int blk = 0;\n    if (blink && altattr) {\n        if (attr & 0x40)\n            blk = (dev->blink & 16);\n        attr &= 0x7f;\n    }\n    unsigned ibg;\n    unsigned ifg = 0;\n    int      ul;\n    int      ol;\n    int      bld;\n    if (altattr) {\n        if (blink) {\n            ibg = (attr & 0x80) ? 8 : 0;\n            bld = 0;\n        } else {\n            bld = (attr & 0x80) ? 1 : 0;\n            ibg = (attr & 0x40) ? 0x0F : 0;\n        }\n        ol = (attr & 0x20) ? 1 : 0;\n        ul = (attr & 0x10) ? 1 : 0;\n    } else {\n        ibg = 0;\n        ifg = (attr >> 4) & 0x0F;\n        ol  = 0;\n        ul  = 0;\n        bld = 0;\n    }\n    unsigned ull = 0xFFFF;\n    unsigned ulc = 0;\n    unsigned oll = 0xFFFF;\n    unsigned olc = 0;\n    if (ul) {\n        ull = dev->crtc[INCOLOR_CRTC_UNDER] & 0x0F;\n        ulc = (dev->crtc[INCOLOR_CRTC_UNDER] >> 4) & 0x0F;\n        if (ulc == 0)\n            ulc = 7;\n    }\n    if (ol) {\n        oll = dev->crtc[INCOLOR_CRTC_OVER] & 0x0F;\n        olc = (dev->crtc[INCOLOR_CRTC_OVER] >> 4) & 0x0F;\n        if (olc == 0)\n            olc = 7;\n    }\n    const unsigned char *fnt = dev->vram + 0x4000 + 16 * chr + 4096 * font + dev->scanline;\n    for (int p = 0; p < 4; p++) {\n        unsigned val;\n        if (blk)\n            val = 0x000;\n        else if (dev->scanline == ull)\n            val = 0x1ff;\n        else {\n            val = fnt[0x10000 * p] << 1;\n            if (elg)\n                val |= (val >> 1) & 1;\n            if (bld)\n                val |= (val >> 1);\n        }\n        planes[p] = val;\n    }\n    if (dev->scanline == oll)\n        *f = *b = (olc ^ ibg) & 0x0f; /* strike-through */\n    else if (dev->scanline == ull)\n        *f = *b = (ulc ^ ibg) & 0x0f; /* underline */\n    else {\n        *f = (altattr ? ~ibg : ~ifg) & 0x0f;\n        *b = altattr ? (ibg & 0x0f) : 0;\n    }\n}\n\n/* KairoX86#258: the line (incolor_poll's, read as text_line or graphics_line reads it) to the GPU's\n   scanout queue (86box/kairo_gpu.h), through the card's palette; returns whether the GPU draws it,\n   dev->memaddr moved as the drawing moves it. */\nstatic bool\nincolor_render_gpu(incolor_t *dev, uint16_t cursoraddr)\n{\n    if (!kairo_gpu_on || (dev->crtc[1] == 0))\n        return false;\n    const uint32_t columns = dev->crtc[1];\n    bitmap_t      *bitmap  = buffer32;\n    const uint32_t out     = (uint32_t) (bitmap->line[dev->displine] - bitmap->dat);\n    uint32_t       colours[16];\n    for (int i = 0; i < 16; i++)\n        colours[i] = dev->rgb[(dev->crtc[INCOLOR_CRTC_EXCEPT] & INCOLOR_EXCEPT_PALETTE) ? dev->palette[i] : defpal[i]];\n    if ((dev->ctrl & INCOLOR_CTRL_GRAPH) && (dev->ctrl2 & INCOLOR_CTRL2_GRAPH)) {\n        uint32_t base = (dev->scanline & 3) * 0x2000;\n        if ((dev->ctrl & INCOLOR_CTRL_PAGE1) && (dev->ctrl2 & INCOLOR_CTRL2_PAGE1))\n            base += 0x8000;\n        uint32_t *words = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_PLANES, columns * 16, columns * 2, colours, 16, 0, 0, 0);\n        for (uint32_t x = 0; x < columns; x++) {\n            const uint8_t mask = dev->crtc[INCOLOR_CRTC_MASK];\n            uint32_t      hi   = 0;\n            uint32_t      lo   = 0;\n            for (int plane = 0; plane < 4; plane++)\n                if ((dev->ctrl & 8) && ((mask >> plane) & 1)) {\n                    const uint32_t at = ((dev->memaddr << 1) & 0x1fff) + base + 0x10000 * plane;\n                    hi |= (uint32_t) dev->vram[at] << (8 * plane);\n                    lo |= (uint32_t) dev->vram[at + 1] << (8 * plane);\n                }\n            words[x * 2]     = hi;\n            words[x * 2 + 1] = lo;\n            dev->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n    const uint32_t cw    = (uint32_t) INCOLOR_CW;\n    uint32_t      *cells = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT4, columns * cw, columns * 2, colours, 16, cw, 0, 0);\n    for (uint32_t x = 0; x < columns; x++) {\n        uint8_t chr  = 0;\n        uint8_t attr = 0;\n        if (dev->ctrl & 8) {\n            chr  = dev->vram[(dev->memaddr << 1) & 0x3fff];\n            attr = dev->vram[((dev->memaddr << 1) + 1) & 0x3fff];\n        }\n        const bool drawcursor = ((dev->memaddr == cursoraddr) && dev->cursorvisible && dev->cursoron);\n        unsigned   planes[4];\n        unsigned   f;\n        unsigned   b;\n        incolor_cell(dev, chr, attr, planes, &f, &b);\n        if (drawcursor) {\n            uint8_t ink = dev->crtc[INCOLOR_CRTC_EXCEPT] & INCOLOR_EXCEPT_CURSOR;\n            if (ink == 0)\n                ink = (attr & 0x08) | 7;\n            if (dev->crtc[INCOLOR_CRTC_EXCEPT] & INCOLOR_EXCEPT_ALTATTR)\n                ink = (attr & 0x08) | (ink & 7);\n            f = b = ink & 0x0f;\n        }\n        uint32_t bytes  = 0;\n        uint32_t ninths = 0;\n        for (int p = 0; p < 4; p++) {\n            bytes |= ((planes[p] >> 1) & 0xff) << (8 * p);\n            ninths |= (planes[p] & 1) << p;\n        }\n        cells[x * 2]     = bytes;\n        cells[x * 2 + 1] = (f & 0x0f) | ((b & 0x0f) << 4) | (ninths << 8);\n        ++dev->memaddr;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nstatic void\nincolor_poll(void *priv)\n"),
    ('86box/src/video/vid_hercules_incolor.c',
     '            dev->lastline = dev->displine;\n            if ((dev->ctrl & INCOLOR_CTRL_GRAPH) && (dev->ctrl2 & INCOLOR_CTRL2_GRAPH))\n                graphics_line(dev);\n',
     '            dev->lastline = dev->displine;\n            if (incolor_render_gpu(dev, cursoraddr)) {\n                /* KairoX86#258: the GPU draws the line */\n            } else if ((dev->ctrl & INCOLOR_CTRL_GRAPH) && (dev->ctrl2 & INCOLOR_CTRL2_GRAPH))\n                graphics_line(dev);\n'),
]

# KairoX86#234, #251: the EGA's display on the GPU (#233's scanout queue). With Hardware
# acceleration on, ega_render_text and ega_render_graphics hand each line, read as they read it, to
# the queue: text as cells (colours, blink, the cursor, the monochrome attributes, line characters'
# ninth dot), graphics as four planes (odd/even addressing and the CGA 2bpp remap applied as read),
# their colours through the palette, the blink and plane mask folded into it. A line with the CRTC
# in reset stays on the CPU, and the CPU's own drawing of a line (blank, the border) draws a queued
# drawing of its row first.
KAIROX86_GPU_EGA = [
    ('86box/src/video/vid_ega_render.c',
     '#include <86box/vid_ega_render_remap.h>\n',
     '#include <86box/vid_ega_render_remap.h>\n#include <86box/kairo_gpu.h> /* KairoX86#234 */\n'),
    ('86box/src/video/vid_ega_render.c',
     '\nvoid\nega_render_blank(ega_t *ega)\n',
     "\n/* KairoX86#234: the CPU is about to draw on the line: a queued drawing of its row first */\nstatic void\nega_render_gpu_touch(ega_t *ega)\n{\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[ega->displine + ega->y_add] - buffer32->dat),\n                             (uint32_t) buffer32->w);\n}\n\n/* KairoX86#234: the text line from p on (ega_render_text's, read as it reads it) to the GPU's scanout\n   queue; returns whether the GPU draws it, ega->memaddr moved as the drawing moves it */\nstatic bool\nega_render_text_gpu(ega_t *ega, uint32_t *p)\n{\n    if (!kairo_gpu_on)\n        return false;\n    const bool doublewidth   = ((ega->seqregs[1] & 8) != 0);\n    const bool attrblink     = ((ega->attrregs[0x10] & 8) != 0);\n    const bool attrlinechars = (ega->attrregs[0x10] & 4);\n    const bool monoattrs     = (ega->attrregs[0x10] & 2);\n    const bool crtcreset     = ((ega->crtc[0x17] & 0x80) == 0);\n    const bool seq9dot       = ((ega->seqregs[1] & 1) == 0);\n    const int  dots          = seq9dot ? 9 : 8;\n    const int  charwidth     = (doublewidth ? 2 : 1) * dots;\n    const bool blinked       = ega->blink & 0x10;\n    const int  end           = ega->hdisp + ega->scrollcache;\n    if (end <= 0)\n        return false;\n    const uint32_t cells = (uint32_t) ((end + charwidth - 1) / charwidth);\n    uint32_t       colours[16];\n    for (int i = 0; i < 16; i++)\n        colours[i] = ega->pallook[ega->egapal[i & ega->plane_mask]];\n    uint32_t *words = kairo_gpu_scan(buffer32, buffer32->kairo_gpu, (uint32_t) (p - buffer32->dat), KAIRO_SCAN_TEXT,\n                                     cells * (uint32_t) charwidth, cells, colours, 16, (uint32_t) dots, 0,\n                                     doublewidth ? KAIRO_SCAN_WIDE : 0);\n    for (uint32_t c = 0; c < cells; c++) {\n        const uint32_t addr       = ega->remap_func(ega, ega->memaddr) & ega->vrammask;\n        const int      drawcursor = ((ega->memaddr == ega->cursoraddr) && ega->cursorvisible && ega->cursoron);\n        uint32_t       chr        = 0;\n        uint32_t       attr       = 0;\n        if (!crtcreset) {\n            chr  = ega->vram[addr];\n            attr = ega->vram[addr + 1];\n        }\n        const uint32_t charaddr = ((attr & 8) ? ega->charsetb : ega->charseta) + (chr * 0x80);\n        uint32_t       dat      = ega->vram[charaddr + (ega->scanline << 2)];\n        bool           ninth    = ((chr & ~0x1f) == 0xc0) && attrlinechars && (dat & 1);\n        uint32_t       fg;\n        uint32_t       bg;\n        if (monoattrs) {\n            const int blink = (!drawcursor && (attr & 0x80) && attrblink && blinked);\n            fg              = ega->mda_attr_to_color_table[attr][blink][1];\n            bg              = ega->mda_attr_to_color_table[attr][blink][0];\n            if ((ega->scanline == ega->crtc[0x14]) && ((attr & 7) == 1)) {\n                dat   = 0xff;\n                ninth = true;\n            }\n            if (drawcursor) {\n                fg ^= ega->mda_attr_to_color_table[attr][0][1];\n                bg ^= ega->mda_attr_to_color_table[attr][0][1];\n            }\n            fg &= 0x0f;\n            bg &= 0x0f;\n        } else if (drawcursor) {\n            bg = attr & 0x0f;\n            fg = attr >> 4;\n        } else {\n            fg = attr & 0x0f;\n            bg = attr >> 4;\n            if ((attr & 0x80) && attrblink) {\n                bg = (attr >> 4) & 7;\n                if (blinked)\n                    fg = bg;\n            }\n        }\n        words[c] = (dat & 0xff) | (fg << 8) | (bg << 16) | (ninth ? (1u << 24) : 0);\n        ega->memaddr += 4;\n    }\n    ega->memaddr &= 0x3ffff;\n    kairo_gpu_scan_commit();\n    return true;\n}\n\n/* KairoX86#234: the graphics line from p on (ega_render_graphics', read as it reads it) to the GPU's\n   scanout queue; returns whether the GPU draws it, ega->memaddr moved as the drawing moves it. Not with\n   the CRTC in reset (the CPU draws black). */\nstatic bool\nega_render_graphics_gpu(ega_t *ega, uint32_t *p)\n{\n    const bool crtcreset = ((ega->crtc[0x17] & 0x80) == 0);\n    if (!kairo_gpu_on || crtcreset)\n        return false;\n    const bool    doublewidth = ((ega->seqregs[1] & 8) != 0);\n    const bool    cga2bpp     = ((ega->gdcreg[5] & 0x20) != 0);\n    const bool    attrblink   = ((ega->attrregs[0x10] & 8) != 0);\n    const bool    blinked     = ega->blink & 0x10;\n    const bool    seqoddeven  = ((ega->seqregs[1] & 4) != 0);\n    const uint8_t blinkmask   = (attrblink ? 0x8 : 0x0);\n    const uint8_t blinkval    = (attrblink && blinked ? 0x8 : 0x0);\n    const int     charwidth   = (doublewidth ? 2 : 1) * 8;\n    const int     end         = ega->hdisp + ega->scrollcache;\n    if (end < 0)\n        return false;\n    const uint32_t cells = (uint32_t) (end / charwidth) + 1;\n    uint32_t       colours[16];\n    for (uint32_t c = 0; c < 16; c++) {\n        const uint32_t v = ((c & ega->plane_mask & ~blinkmask) | ((c | ~ega->plane_mask) & blinkmask & blinkval)) ^ blinkmask;\n        colours[c]       = ega->pallook[ega->egapal[v]];\n    }\n    uint32_t *words      = kairo_gpu_scan(buffer32, buffer32->kairo_gpu, (uint32_t) (p - buffer32->dat), KAIRO_SCAN_PLANES,\n                                          cells * (uint32_t) charwidth, cells, colours, 16, 0, 0, doublewidth ? KAIRO_SCAN_WIDE : 0);\n    int       secondcclk = 0;\n    for (uint32_t c = 0; c < cells; c++) {\n        const uint32_t addr = ega->remap_func(ega, ega->memaddr) & ega->vrammask;\n        uint8_t        edat[4];\n        if (seqoddeven) {\n            edat[0]    = ega->vram[(addr | 0) ^ secondcclk];\n            edat[1]    = ega->vram[(addr | 1) ^ secondcclk];\n            edat[2]    = ega->vram[(addr | 2) ^ secondcclk];\n            edat[3]    = ega->vram[(addr | 3) ^ secondcclk];\n            secondcclk = (secondcclk + 1) & 1;\n            if (secondcclk == 0)\n                ega->memaddr += 4;\n        } else {\n            memcpy(edat, &ega->vram[addr], 4);\n            ega->memaddr += 4;\n        }\n        ega->memaddr &= 0x3ffff;\n        if (cga2bpp) {\n            const uint8_t dat0 = egaremap2bpp[edat[1]] | (egaremap2bpp[edat[0]] << 4);\n            const uint8_t dat1 = egaremap2bpp[edat[1] >> 1] | (egaremap2bpp[edat[0] >> 1] << 4);\n            const uint8_t dat2 = egaremap2bpp[edat[3]] | (egaremap2bpp[edat[2]] << 4);\n            const uint8_t dat3 = egaremap2bpp[edat[3] >> 1] | (egaremap2bpp[edat[2] >> 1] << 4);\n            edat[0]            = dat0;\n            edat[1]            = dat1;\n            edat[2]            = dat2;\n            edat[3]            = dat3;\n        }\n        words[c] = edat[0] | ((uint32_t) edat[1] << 8) | ((uint32_t) edat[2] << 16) | ((uint32_t) edat[3] << 24);\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nvoid\nega_render_blank(ega_t *ega)\n"),
    ('86box/src/video/vid_ega_render.c',
     '        (buffer32->line[ega->displine + ega->y_add] == NULL))\n        return;\n\n    for (int x = 0; x < (ega->hdisp + ega->scrollcache); x++) {\n',
     '        (buffer32->line[ega->displine + ega->y_add] == NULL))\n        return;\n\n    ega_render_gpu_touch(ega); /* KairoX86#234 */\n\n    for (int x = 0; x < (ega->hdisp + ega->scrollcache); x++) {\n'),
    ('86box/src/video/vid_ega_render.c',
     '    if (ega->scrblank || (ega->hdisp == 0))\n        return;\n\n    for (int i = 0; i < ega->x_add; i++)\n',
     '    if (ega->scrblank || (ega->hdisp == 0))\n        return;\n\n    ega_render_gpu_touch(ega); /* KairoX86#234 */\n\n    for (int i = 0; i < ega->x_add; i++)\n'),
    ('86box/src/video/vid_ega_render.c',
     '            p += dotwidth;\n        }\n\n        for (int x = 0; x < (ega->hdisp + ega->scrollcache); x += charwidth) {\n',
     '            p += dotwidth;\n        }\n\n        /* KairoX86#234 */\n        if (ega_render_text_gpu(ega, p))\n            return;\n\n        for (int x = 0; x < (ega->hdisp + ega->scrollcache); x += charwidth) {\n'),
    ('86box/src/video/vid_ega_render.c',
     '        p += dotwidth;\n    }\n\n    for (int x = 0; x <= (ega->hdisp + ega->scrollcache); x += charwidth) {\n',
     '        p += dotwidth;\n    }\n\n    /* KairoX86#234 */\n    if (ega_render_graphics_gpu(ega, p))\n        return;\n\n    for (int x = 0; x <= (ega->hdisp + ega->scrollcache); x += charwidth) {\n'),
]

# KairoX86#255: the Genius VHR's graphics on the GPU (#233's scanout queue). With Hardware
# acceleration on and its MDA text layer off, the CGA 640 x 200 and native 728-dot lines go to the
# queue at 1 bit a pixel, coloured as video_process_8 colours them, over the row's background, which
# the CPU fills first (a queued drawing of the row drawn before it). Its text layers, drawn over what
# is already there (its background shows the layers below, its ninth column and cursor read the
# pixels drawn), stay on the CPU.
KAIROX86_GPU_GENIUS = [
    ('86box/src/video/vid_genius.c',
     '#include <86box/plat.h>\n#include <86box/video.h>\n',
     '#include <86box/plat.h>\n#include <86box/video.h>\n#include <86box/kairo_gpu.h> /* KairoX86#255 */\n'),
    ('86box/src/video/vid_genius.c',
     '\n/* Draw a line in the CGA 640x200 mode */\nvoid\ngenius_cgaline(genius_t *genius)\n',
     "\n/* KairoX86#255: the graphics line genius_cgaline (cga) or genius_hiresline draws, to the GPU's scanout\n   queue, from vram at addr, dots of 1 bit, ink_f where set */\nstatic void\ngenius_graphics_gpu(genius_t *genius, uint32_t addr, uint32_t bytes, uint8_t ink_f, uint8_t ink_b)\n{\n    bitmap_t      *bitmap     = buffer32;\n    const uint32_t colours[2] = { pal_lookup[ink_b], pal_lookup[ink_f] };\n    uint8_t       *line       = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu,\n                                                           (uint32_t) (bitmap->line[genius->displine] - bitmap->dat), KAIRO_SCAN_BITS,\n                                                           bytes * 8, (bytes + 3) / 4, colours, 2, 1, 0, 0);\n    for (uint32_t x = 0; x < bytes; x++)\n        line[x] = genius->vram[addr + x];\n    kairo_gpu_scan_commit();\n}\n\n/* Draw a line in the CGA 640x200 mode */\nvoid\ngenius_cgaline(genius_t *genius)\n"),
    ('86box/src/video/vid_genius.c',
     '    addr = 0x18000 + 80 * ((genius->displine - 512) >> 2);\n    if ((genius->displine - 512) & 2)\n        addr += 0x2000;\n\n',
     '    addr = 0x18000 + 80 * ((genius->displine - 512) >> 2);\n    if ((genius->displine - 512) & 2)\n        addr += 0x2000;\n\n    /* KairoX86#255: the GPU draws it when no text is drawn over it */\n    if (kairo_gpu_on && !(genius->mda_ctrl & 8)) {\n        genius_graphics_gpu(genius, addr, 80, ink_f, ink_b);\n        return;\n    }\n\n'),
    ('86box/src/video/vid_genius.c',
     '    else /* The second 496 live at B8000 */\n        addr = 0x18000 + (128 * (genius->displine - 512));\n\n',
     '    else /* The second 496 live at B8000 */\n        addr = 0x18000 + (128 * (genius->displine - 512));\n\n    /* KairoX86#255: the GPU draws it when no text is drawn over it */\n    if (kairo_gpu_on && !(genius->mda_ctrl & 8)) {\n        genius_graphics_gpu(genius, addr, 91, ink_f, ink_b);\n        return;\n    }\n\n'),
    ('86box/src/video/vid_genius.c',
     '            /* Start off with a blank line */\n            for (uint16_t x = 0; x < GENIUS_XSIZE; x++)\n',
     '            /* KairoX86#255: a queued drawing of the row drawn before the CPU blanks it */\n            if (kairo_gpu_on)\n                kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[genius->displine] - buffer32->dat), GENIUS_XSIZE);\n\n            /* Start off with a blank line */\n            for (uint16_t x = 0; x < GENIUS_XSIZE; x++)\n'),
]

# KairoX86#279: the Wyse 700's display on the GPU (#233's scanout queue). With Hardware acceleration
# on, wy700_render_gpu takes each line as wy700_textline, _cgaline, _medresline or _hiresline reads
# it: text as pairs of 8-dot cells (MDA or CGA attributes, underline, the cursor, blink), graphics at
# 1 or 2 bits a pixel repeated 1, 2 or 4 times, coloured as video_process_8 colours them.
KAIROX86_GPU_WY700 = [
    ('86box/src/video/vid_wy700.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#279 */\n'),
    ('86box/src/video/vid_wy700.c',
     '\nvoid\nwy700_poll(void *priv)\n',
     "\n/* KairoX86#279: graphics bytes from vram (addr, each byte masked by mask) to the GPU's scanout queue,\n   bits a pixel, each repeated (flags), through inks (indexes) */\nstatic void\nwy700_bits_gpu(wy700_t *wy700, uint32_t addr, uint32_t mask, uint32_t bytes, uint32_t bits, uint32_t flags,\n               const uint8_t *inks, bool enabled)\n{\n    bitmap_t      *bitmap = buffer32;\n    uint32_t       colours[4];\n    const uint32_t values = 1u << bits;\n    for (uint32_t v = 0; v < values; v++)\n        colours[v] = pal_lookup[enabled ? inks[v] : 16];\n    const uint32_t repeat = ((flags & KAIRO_SCAN_WIDE) ? 2 : 1) * ((flags & KAIRO_SCAN_WIDE4) ? 4 : 1);\n    uint8_t       *line   = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (bitmap->line[wy700->displine] - bitmap->dat),\n                                                       KAIRO_SCAN_BITS, bytes * (8 / bits) * repeat, (bytes + 3) / 4, colours, values,\n                                                       bits, 0, flags);\n    for (uint32_t x = 0; x < bytes; x++)\n        line[x] = wy700->vram[(addr + x) & mask];\n    kairo_gpu_scan_commit();\n}\n\n/* KairoX86#279: the line wy700_poll's mode draws, read as its drawing reads it, to the GPU's scanout\n   queue; returns whether the GPU draws it */\nstatic bool\nwy700_render_gpu(wy700_t *wy700, int mode)\n{\n    static const uint8_t inks2[4] = { 16 + 0, 16 + 8, 16 + 7, 16 + 15 };\n    static const uint8_t inks1[2] = { 16 + 0, 16 + 15 };\n    if (!kairo_gpu_on)\n        return false;\n    switch (mode) {\n        case 0x04:\n        case 0x06: {\n            uint16_t       memaddr = (wy700->cga_crtc[13] | (wy700->cga_crtc[12] << 8)) & 0x3fff;\n            const uint32_t addr    = ((wy700->displine >> 2) & 1) * 0x2000 + (wy700->displine >> 3) * 80 + ((memaddr & ~1) << 1);\n            const bool     enabled = wy700->enabled && (wy700->cga_ctrl & 8);\n            if (wy700->wy700_mode == 6)\n                wy700_bits_gpu(wy700, addr, 0x3fff, 80, 1, KAIRO_SCAN_WIDE, inks1, enabled);\n            else\n                wy700_bits_gpu(wy700, addr, 0x3fff, 80, 2, KAIRO_SCAN_WIDE4, inks2, enabled);\n            return true;\n        }\n        case 0x80:\n        case 0x90: {\n            const uint32_t addr    = (wy700->displine >> 1) * 80 + 4 * wy700->wy700_base;\n            const bool     enabled = (wy700->wy700_mode & 8) != 0;\n            if (wy700->wy700_mode & 0x10)\n                wy700_bits_gpu(wy700, addr, 0x1ffff, 80, 2, KAIRO_SCAN_WIDE4, inks2, enabled);\n            else\n                wy700_bits_gpu(wy700, addr, 0x1ffff, 80, 1, KAIRO_SCAN_WIDE, inks1, enabled);\n            return true;\n        }\n        case 0xA0:\n        case 0xB0:\n        case 0xC0:\n        case 0xD0:\n        case 0xE0:\n        case 0xF0: {\n            uint32_t addr = (wy700->displine >> 1) * 160 + 4 * wy700->wy700_base;\n            if ((wy700->wy700_mode & 0x40) && (wy700->displine & 1))\n                addr += 0x10000;\n            const bool enabled = (wy700->wy700_mode & 8) != 0;\n            if (wy700->wy700_mode & 0x10)\n                wy700_bits_gpu(wy700, addr, 0x1ffff, 160, 2, KAIRO_SCAN_WIDE, inks2, enabled);\n            else\n                wy700_bits_gpu(wy700, addr, 0x1ffff, 160, 1, 0, inks1, enabled);\n            return true;\n        }\n        default:\n            break;\n    }\n    /* Text (wy700_textline): each 16-dot character two 8-dot cells */\n    const int      w          = (wy700->wy700_mode == 0) ? 40 : 80;\n    const int      cw         = (wy700->wy700_mode == 0) ? 32 : 16;\n    const uint8_t *fontbase   = &fontdatw[0][0] + (wy700->font ? 256 * 32 : 0);\n    uint16_t       memaddr    = (wy700->cga_crtc[13] | (wy700->cga_crtc[12] << 8)) & 0x3fff;\n    const uint16_t cursoraddr = (wy700->cga_crtc[15] | (wy700->cga_crtc[14] << 8)) & 0x3fff;\n    const int      mda        = (wy700->cga_crtc[9] == 0 || wy700->cga_crtc[9] == 13);\n    const uint16_t addr       = ((memaddr & ~1) + (wy700->displine >> 5) * w) * 2;\n    const uint8_t  scanline   = (wy700->displine >> 1) & 15;\n    memaddr += ((wy700->displine >> 5) * w);\n    int cursorline;\n    if ((wy700->real_crtc[10] & 0x60) == 0x20)\n        cursorline = 0;\n    else\n        cursorline = ((wy700->real_crtc[10] & 0x1F) <= scanline) && ((wy700->real_crtc[11] & 0x1F) >= scanline);\n    bitmap_t *bitmap = buffer32;\n    uint32_t *cells  = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (bitmap->line[wy700->displine] - bitmap->dat), KAIRO_SCAN_TEXT,\n                                      (uint32_t) (w * cw), (uint32_t) (w * 2), pal_lookup, 256, 8, 0, (w == 40) ? KAIRO_SCAN_WIDE : 0);\n    for (int x = 0; x < w; x++) {\n        const uint8_t chr        = wy700->vram[(addr + 2 * x) & 0x3FFF];\n        uint8_t       attr       = wy700->vram[(addr + 2 * x + 1) & 0x3FFF];\n        const int     drawcursor = ((memaddr == cursoraddr) && cursorline && wy700->enabled && (wy700->cga_ctrl & 8) && (wy700->blink & 16));\n        const int     blink      = ((wy700->blink & 16) && (wy700->cga_ctrl & 0x20) && (attr & 0x80) && !drawcursor);\n        if (wy700->cga_ctrl & 0x20)\n            attr &= 0x7F;\n        int(*table)[2][2] = mda ? mda_attr_to_color_table : cga_attr_to_color_table;\n        uint32_t bits0;\n        uint32_t bits1;\n        uint32_t fg;\n        uint32_t bg;\n        if ((scanline == 14) && mda && ((attr & 7) == 1)) {\n            /* Underline: no cursor, and the address does not move on (as wy700_textline) */\n            bits0 = bits1 = 0xff;\n            fg = bg = mda_attr_to_color_table[attr][blink][1];\n        } else {\n            bits0 = fontbase[chr * 32 + 2 * scanline];\n            bits1 = fontbase[chr * 32 + 2 * scanline + 1];\n            fg    = table[attr][blink][1];\n            bg    = table[attr][blink][0];\n            if (!(wy700->enabled) || !(wy700->cga_ctrl & 8))\n                fg = bg = mda_attr_to_color_table[0][0][0];\n            if (drawcursor) {\n                fg ^= table[attr][0][1];\n                bg ^= table[attr][0][1];\n            }\n            ++memaddr;\n        }\n        const uint32_t colours = ((fg & 0xff) << 8) | ((bg & 0xff) << 16);\n        cells[x * 2]           = bits0 | colours;\n        cells[x * 2 + 1]       = bits1 | colours;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nvoid\nwy700_poll(void *priv)\n"),
    ('86box/src/video/vid_wy700.c',
     '            switch (mode) {\n                default:\n                case 0x00:\n',
     '            if (wy700_render_gpu(wy700, mode)) {\n                /* KairoX86#279: the GPU draws the line */\n            } else switch (mode) {\n                default:\n                case 0x00:\n'),
]

# KairoX86#233: an SVGA line drawn again in a frame (a line-compare split, a restarted frame) after the
# GPU queued it: svga_do_render touches the line's row first, so the GPU draws the earlier drawing
# before the CPU draws on the row again (blank, borders, a CPU renderer) or queues it once more.
KAIROX86_GPU_SVGA_TOUCH = [
    ('86box/src/video/vid_svga.c',
     '#include <86box/vid_svga.h>\n',
     '#include <86box/vid_svga.h>\n#include <86box/kairo_gpu.h> /* KairoX86#233 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_do_render(svga_t *svga)\n{\n',
     "svga_do_render(svga_t *svga)\n{\n    /* KairoX86#233: the row's queued GPU drawing, if any, before it is drawn again */\n    if (kairo_gpu_on && (svga->monitor->target_buffer != NULL) && ((svga->displine + svga->y_add) >= 0)\n        && ((svga->displine + svga->y_add) < svga->monitor->target_buffer->h)) {\n        bitmap_t *bitmap = svga->monitor->target_buffer;\n        kairo_gpu_scan_touch(bitmap, (uint32_t) (bitmap->line[svga->displine + svga->y_add] - bitmap->dat), (uint32_t) bitmap->w);\n    }\n"),
    ('86box/src/video/vid_svga.c',
     '        svga->x_add = svga->left_overscan;\n        svga_render_overscan_left(svga);\n        svga_render_overscan_right(svga);\n        svga->x_add = svga->left_overscan - svga->scrollcache;\n',
     "        svga->x_add = svga->left_overscan;\n        svga_render_overscan_left(svga);\n        svga_render_overscan_right(svga);\n        /* KairoX86#233: the borders drawn over the line's ends (it was drawn scrollcache pixels further\n           left) stay: the queued line leaves those pixels */\n        if (kairo_gpu_on && !svga->scrblank && (svga->hdisp > 0) && ((svga->displine + svga->y_add) >= 0)\n            && (svga->monitor->target_buffer != NULL) && ((svga->displine + svga->y_add) < svga->monitor->target_buffer->h)) {\n            bitmap_t      *bitmap = svga->monitor->target_buffer;\n            const uint32_t row    = (uint32_t) (bitmap->line[svga->displine + svga->y_add] - bitmap->dat);\n            const int      right  = overscan_x - svga->left_overscan;\n            if (svga->x_add > 0)\n                kairo_gpu_scan_cut(bitmap, row, (uint32_t) svga->x_add);\n            if (right > 0)\n                kairo_gpu_scan_cut(bitmap, row + (uint32_t) (svga->x_add + svga->hdisp), (uint32_t) right);\n        }\n        svga->x_add = svga->left_overscan - svga->scrollcache;\n"),
]

# KairoX86#246: the Quadram Quadcolor's display on the GPU (#233's scanout queue), with its second
# plane off: quadcolor_render_gpu takes each line as quadcolor_render reads it (text cells, 2 and 1
# bit graphics, the Quadcolor's background colours and page offset), coloured as video_process_8
# colours them, and moves the second plane's position on as the drawing's get_next_qc2_pixel calls
# would. With the second plane on, its nibbles are ORed into every pixel: those lines stay on the CPU.
KAIROX86_GPU_QUADCOLOR = [
    ('86box/src/video/vid_cga_quadcolor.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#246 */\n'),
    ('86box/src/video/vid_cga_quadcolor.c',
     '\nstatic void\nquadcolor_render(quadcolor_t *quadcolor, int line)\n',
     "\n/* KairoX86#246: the second plane's position moved on as pixels get_next_qc2_pixel calls would move it */\nstatic void\nquadcolor_skip_qc2(quadcolor_t *quadcolor, uint32_t pixels)\n{\n    for (uint32_t i = 0; i < pixels; i++) {\n        quadcolor->qc2mask = ~quadcolor->qc2mask;\n        quadcolor->qc2idx += quadcolor->qc2mask >> 7;\n    }\n}\n\n/* KairoX86#246: the line (quadcolor_render's, read as it reads it) between its borders to the GPU's\n   scanout queue, coloured as video_process_8 colours it; returns whether the GPU draws it. Not with the\n   second plane on, nor with composite output, which reads the picture back. */\nstatic bool\nquadcolor_render_gpu(quadcolor_t *quadcolor, int line)\n{\n    if (!kairo_gpu_on || quadcolor->quadcolor_2_oe || quadcolor->composite)\n        return false;\n    const int hdisp = quadcolor->crtc[CGA_CRTC_HDISP];\n    if (hdisp <= 0)\n        return false;\n    bitmap_t       *bitmap     = buffer32;\n    const uint32_t  out        = (uint32_t) (&bitmap->line[line][8] - bitmap->dat);\n    const uint32_t *palette    = pal_lookup;\n    const bool      enabled    = (quadcolor->cgamode & CGA_MODE_FLAG_VIDEO_ENABLE) != 0;\n    uint16_t        cursoraddr = (quadcolor->crtc[CGA_CRTC_CURSOR_ADDR_LOW] | (quadcolor->crtc[CGA_CRTC_CURSOR_ADDR_HIGH] << 8)) & DEVICE_VRAM_MASK;\n    if (!(quadcolor->cgamode & CGA_MODE_FLAG_GRAPHICS)) {\n        const bool highres = (quadcolor->cgamode & CGA_MODE_FLAG_HIGHRES) != 0;\n        uint32_t  *cells   = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, (uint32_t) hdisp * (highres ? 8 : 16),\n                                            (uint32_t) hdisp, palette, 256, 8, 0, highres ? 0 : KAIRO_SCAN_WIDE);\n        for (int x = 0; x < hdisp; x++) {\n            uint8_t chr  = 0;\n            uint8_t attr = 0;\n            if (enabled) {\n                if (highres) {\n                    chr  = quadcolor->charbuffer[x << 1];\n                    attr = quadcolor->charbuffer[(x << 1) + 1];\n                } else {\n                    chr  = quadcolor->vram[(quadcolor->page_offset ^ (quadcolor->memaddr << 1)) & DEVICE_VRAM_MASK];\n                    attr = quadcolor->vram[(quadcolor->page_offset ^ ((quadcolor->memaddr << 1) + 1)) & DEVICE_VRAM_MASK];\n                }\n            }\n            const bool drawcursor = ((quadcolor->memaddr == cursoraddr) && quadcolor->cursorvisible && quadcolor->cursoron);\n            uint32_t   fg         = (attr & 15) + 16;\n            uint32_t   bg;\n            if (quadcolor->cgamode & CGA_MODE_FLAG_BLINK) {\n                bg = ((attr >> 4) & 7) + 16;\n                if ((quadcolor->cgablink & 8) && (attr & 0x80) && (!highres || !quadcolor->drawcursor))\n                    fg = bg;\n            } else\n                bg = (attr >> 4) + 16;\n            const uint32_t flip = drawcursor ? 15 : 0;\n            cells[x] = fontdat[chr + quadcolor->fontbase][quadcolor->scanline & 7] | ((fg ^ flip) << 8) | ((bg ^ flip) << 16);\n            quadcolor->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        quadcolor_skip_qc2(quadcolor, (uint32_t) hdisp * (highres ? 8 : 16));\n        return true;\n    }\n    uint32_t   colours[4];\n    const bool hires = (quadcolor->cgamode & CGA_MODE_FLAG_HIGHRES_GRAPHICS) != 0;\n    if (!hires) {\n        const int col = (quadcolor->cgacol & 16) ? 24 : 16;\n        colours[0]    = palette[(quadcolor->cgacol & 15) | 16];\n        if (quadcolor->cgamode & CGA_MODE_FLAG_BW) {\n            colours[1] = palette[col | 3];\n            colours[2] = palette[col | 4];\n            colours[3] = palette[col | 7];\n        } else if (quadcolor->cgacol & 32) {\n            colours[1] = palette[col | 3];\n            colours[2] = palette[col | 5];\n            colours[3] = palette[col | 7];\n        } else {\n            colours[1] = palette[col | 2];\n            colours[2] = palette[col | 4];\n            colours[3] = palette[col | 6];\n        }\n    } else {\n        colours[0] = palette[quadcolor->quadcolor_ctrl & 15];\n        colours[1] = palette[(quadcolor->cgacol & 15) + 16];\n    }\n    uint8_t *bytes = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, (uint32_t) hdisp * 16,\n                                                ((uint32_t) hdisp * 2 + 3) / 4, colours, hires ? 2 : 4, hires ? 1 : 2, 0,\n                                                hires ? 0 : KAIRO_SCAN_WIDE);\n    for (int x = 0; x < hdisp; x++) {\n        uint16_t dat;\n        if (enabled) {\n            const uint32_t at = ((quadcolor->memaddr << 1) & 0x1fff) + ((quadcolor->scanline & 1) * 0x2000);\n            dat               = (quadcolor->vram[quadcolor->page_offset ^ at] << 8) | quadcolor->vram[quadcolor->page_offset ^ (at + 1)];\n        } else\n            dat = hires ? (quadcolor->quadcolor_ctrl & 15) : 0;\n        bytes[x * 2]     = (uint8_t) (dat >> 8);\n        bytes[x * 2 + 1] = (uint8_t) dat;\n        quadcolor->memaddr++;\n    }\n    kairo_gpu_scan_commit();\n    quadcolor_skip_qc2(quadcolor, (uint32_t) hdisp * 16);\n    return true;\n}\n\nstatic void\nquadcolor_render(quadcolor_t *quadcolor, int line)\n"),
    ('86box/src/video/vid_cga_quadcolor.c',
     '            buffer32->line[line][column + (quadcolor->crtc[CGA_CRTC_HDISP] << 4) + 8] = cols[0];\n    }\n',
     '            buffer32->line[line][column + (quadcolor->crtc[CGA_CRTC_HDISP] << 4) + 8] = cols[0];\n    }\n    /* KairoX86#246: the GPU draws the line between the borders */\n    if (quadcolor_render_gpu(quadcolor, line))\n        return;\n'),
    ('86box/src/video/vid_cga_quadcolor.c',
     '    int32_t  highres_graphics_flag = (CGA_MODE_FLAG_HIGHRES_GRAPHICS | CGA_MODE_FLAG_GRAPHICS);\n\n    cols[0] = ((quadcolor->cgamode & highres_graphics_flag) == highres_graphics_flag) ? (quadcolor->quadcolor_ctrl & 15) :\n',
     '    int32_t  highres_graphics_flag = (CGA_MODE_FLAG_HIGHRES_GRAPHICS | CGA_MODE_FLAG_GRAPHICS);\n\n    /* KairoX86#246: a line the GPU still has to draw is drawn before the CPU draws on it again */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[line] - buffer32->dat), (uint32_t) buffer32->w);\n\n    cols[0] = ((quadcolor->cgamode & highres_graphics_flag) == highres_graphics_flag) ? (quadcolor->quadcolor_ctrl & 15) :\n'),
    ('86box/src/video/vid_cga_quadcolor.c',
     '    int col = ((quadcolor->cgamode & highres_graphics_flag) == highres_graphics_flag) ? (quadcolor->quadcolor_ctrl & 15) + 16 : (quadcolor->cgacol & 15) + 16;  /* TODO: Is Quadcolor bg color actually relevant, here? */\n',
     '    int col = ((quadcolor->cgamode & highres_graphics_flag) == highres_graphics_flag) ? (quadcolor->quadcolor_ctrl & 15) + 16 : (quadcolor->cgacol & 15) + 16;  /* TODO: Is Quadcolor bg color actually relevant, here? */\n\n    /* KairoX86#246: a line the GPU still has to draw is drawn before the CPU blanks it */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[line] - buffer32->dat), (uint32_t) buffer32->w);\n'),
    ('86box/src/video/vid_cga_quadcolor.c',
     'quadcolor_blit_memtoscreen(quadcolor_t *quadcolor, int x, int y, int w, int h)\n{\n    if (quadcolor->double_type > DOUBLE_SIMPLE)\n',
     'quadcolor_blit_memtoscreen(quadcolor_t *quadcolor, int x, int y, int w, int h)\n{\n    /* KairoX86#246: the lines the GPU draws, drawn before the doubling reads them */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_drain();\n    if (quadcolor->double_type > DOUBLE_SIMPLE)\n'),
]

# KairoX86#247: the Yamaha V6355D's display on the GPU (#233's scanout queue). With Hardware
# acceleration on, v6355_render_gpu takes each line as v6355_render reads it (text cells with the
# card's attribute mapping, underline and cursor, 2, 1 and 4-bit graphics), coloured as
# v6355_render_process colours them (the palette, or the card's own in its true-colour output).
# Lines its mouse pointer crosses (it masks pixels already drawn) and composite output stay on the CPU.
KAIROX86_GPU_V6355 = [
    ('86box/src/video/vid_cga_v6355.c',
     '#include <86box/plat_unused.h>\n',
     '#include <86box/plat_unused.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#247 */\n'),
    ('86box/src/video/vid_cga_v6355.c',
     '\nstatic void\nv6355_render(v6355_t *v6355, int line)\n',
     "\n/* KairoX86#247: whether the mouse pointer draws on this line (v6355_pointer's own test) */\nstatic bool\nv6355_pointer_on_line(v6355_t *v6355)\n{\n    const int     y         = v6355->displine - v6355->firstline;\n    const int     pointer_y = v6355->v6355data[0x63];\n    const uint8_t mflags    = v6355->v6355data[0x64];\n    if (!(mflags & 6) || ((v6355->cgablink & 8) && (mflags & 1)))\n        return false;\n    return (y >= (pointer_y - 16)) && (y < pointer_y);\n}\n\n/* KairoX86#247: the line (v6355_render's, read as it reads it) between its borders to the GPU's\n   scanout queue, coloured as v6355_render_process colours it; returns whether the GPU draws it */\nstatic bool\nv6355_render_gpu(v6355_t *v6355, int line)\n{\n    if (!kairo_gpu_on || (v6355->display_type == V6355_COMPOSITE) || v6355_pointer_on_line(v6355))\n        return false;\n    const int width = v6355_width(v6355);\n    if (width <= 0)\n        return false;\n    /* Colours: 0-31 the indexes the drawing makes, 32-47 a cursor cell's (index ^ 0xffffff) */\n    uint32_t   colours[48];\n    const bool truecolor = (v6355->display_type == V6355_TRUECOLOR);\n    for (int i = 0; i < 32; i++)\n        colours[i] = truecolor ? v6355->v6355pal[i & 0xf] : pal_lookup[i];\n    for (int i = 0; i < 16; i++)\n        colours[32 + i] = truecolor ? v6355->v6355pal[i] : 0x00000000;\n    bitmap_t      *bitmap = buffer32;\n    const uint32_t out    = (uint32_t) (&bitmap->line[line][8] - bitmap->dat);\n    const uint16_t ca     = (v6355->crtc[15] | (v6355->crtc[14] << 8)) & 0x3fff;\n    if ((v6355->cgamode & 1) || !(v6355->cgamode & 2)) {\n        /* Text: 80 columns (cgamode bit 0, whatever bit 1 says, as v6355_render tests it) or 40 doubled */\n        const bool highres = (v6355->cgamode & 1) != 0;\n        const int  columns = width / (highres ? 8 : 16);\n        uint32_t  *cells   = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, (uint32_t) width, (uint32_t) columns,\n                                            colours, 48, 8, 0, highres ? 0 : KAIRO_SCAN_WIDE);\n        /* v6355_line_text40 reads from the line's own start, while the copy moves ma on */\n        const uint16_t ma = v6355->ma;\n        for (int x = 0; x < columns; x++) {\n            uint8_t chr  = 0;\n            uint8_t attr = 0;\n            if (v6355->cgamode & 8) {\n                if (highres) {\n                    chr  = v6355->charbuffer[x << 1];\n                    attr = v6355->charbuffer[(x << 1) + 1];\n                } else {\n                    chr  = v6355->vram[((ma + x) << 1) & 0x3fff];\n                    attr = v6355->vram[(((ma + x) << 1) + 1) & 0x3fff];\n                }\n            }\n            uint8_t cols[2];\n            v6355_map_attrs(v6355, chr, attr, cols);\n            uint8_t data = fontdat[chr + v6355->fontbase][v6355->sc & 7];\n            if ((v6355->v6355data[0x66] & 0x80) && ((attr & 7) == 1) && ((v6355->sc & 7) == 7))\n                data = 0xff;\n            uint32_t fg = cols[1];\n            uint32_t bg = cols[0];\n            if ((v6355->ma == ca) && v6355->con && v6355->cursoron) {\n                fg = 32 + ((~fg) & 0xf);\n                bg = 32 + ((~bg) & 0xf);\n            }\n            cells[x] = data | (fg << 8) | (bg << 16);\n            v6355->ma++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n    /* Graphics: 2 bytes a character */\n    const int columns = width / 16;\n    uint32_t  bits;\n    uint32_t  flags;\n    uint32_t  pixel_colours[16];\n    uint32_t  count;\n    if (!(v6355->cgamode & 16)) {\n        if (v6355->cgamode & 0x40) {\n            /* 160 x 200 x 16: 4 bits a pixel, each four times */\n            bits  = 4;\n            flags = KAIRO_SCAN_WIDE4;\n            for (int v = 0; v < 16; v++)\n                pixel_colours[v] = colours[v | 16];\n        } else {\n            uint8_t       cols[4];\n            const uint8_t intensity = (v6355->cgacol & 16) ? 8 : 0;\n            cols[0]                 = (v6355->cgacol & 15) | 16;\n            if (v6355->cgamode & 4) {\n                cols[1] = intensity | 3;\n                cols[2] = intensity | 4;\n                cols[3] = intensity | 7;\n            } else if (v6355->cgacol & 32) {\n                cols[1] = intensity | 3;\n                cols[2] = intensity | 5;\n                cols[3] = intensity | 7;\n            } else {\n                cols[1] = intensity | 2;\n                cols[2] = intensity | 4;\n                cols[3] = intensity | 6;\n            }\n            for (int i = 1; i < 4; i++)\n                cols[i] |= 16;\n            bits  = 2;\n            flags = KAIRO_SCAN_WIDE;\n            for (int v = 0; v < 4; v++)\n                pixel_colours[v] = colours[cols[v]];\n        }\n    } else {\n        bits             = 1;\n        flags            = 0;\n        pixel_colours[0] = colours[16];\n        pixel_colours[1] = colours[(v6355->cgacol & 15) | 16];\n    }\n    count          = (uint32_t) columns * 16;\n    uint8_t *bytes = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, count, ((uint32_t) columns * 2 + 3) / 4,\n                                                pixel_colours, 1u << bits, bits, 0, flags);\n    for (int x = 0; x < columns; x++) {\n        const uint32_t at = ((v6355->ma << 1) & 0x1fff) + ((v6355->sc & 1) * 0x2000);\n        bytes[x * 2]      = (v6355->cgamode & 8) ? v6355->vram[at] : 0;\n        bytes[x * 2 + 1]  = (v6355->cgamode & 8) ? v6355->vram[at + 1] : 0;\n        v6355->ma++;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\nstatic void\nv6355_render(v6355_t *v6355, int line)\n"),
    ('86box/src/video/vid_cga_v6355.c',
     '        ((uint32_t *) buffer32->line[line])[c + width + 8] = cols[0];\n    }\n',
     '        ((uint32_t *) buffer32->line[line])[c + width + 8] = cols[0];\n    }\n\n    /* KairoX86#247: the GPU draws the line between the borders */\n    if (v6355_render_gpu(v6355, line))\n        return;\n'),
    ('86box/src/video/vid_cga_v6355.c',
     '    /* Draw border */\n    cols[0] = ((v6355->cgamode & 0x12) == 0x12) ? 0 : (v6355->cgacol & 15);\n',
     '    /* KairoX86#247: a line the GPU still has to draw is drawn before the CPU draws on it again */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[line] - buffer32->dat), (uint32_t) buffer32->w);\n\n    /* Draw border */\n    cols[0] = ((v6355->cgamode & 0x12) == 0x12) ? 0 : (v6355->cgacol & 15);\n'),
    ('86box/src/video/vid_cga_v6355.c',
     '    cols[0] = ((v6355->cgamode & 0x12) == 0x12) ? 0 : (v6355->cgacol & 15);\n    hline(buffer32, 0, line, width + 16, cols[0]);\n',
     '    cols[0] = ((v6355->cgamode & 0x12) == 0x12) ? 0 : (v6355->cgacol & 15);\n    /* KairoX86#247: a line the GPU still has to draw is drawn before the CPU blanks it */\n    if (kairo_gpu_on)\n        kairo_gpu_scan_touch(buffer32, (uint32_t) (buffer32->line[line] - buffer32->dat), (uint32_t) buffer32->w);\n    hline(buffer32, 0, line, width + 16, cols[0]);\n'),
]

# KairoX86#261, #268: the IBM PGC's display (and the ImageManager 1024's, on the same poll) on the
# GPU (#233's scanout queue). With Hardware acceleration on, pgc_poll's native lines go to the queue as
# 8 bits a pixel through the card's palette (the scan's horizontal wrap applied as read), and its CGA
# emulation's lines (pgc_cga_text, _gfx40, _gfx80) as text cells and 2 and 1-bit pixels, coloured as
# video_process_8 colours them.
KAIROX86_GPU_PGC = [
    ('86box/src/video/vid_pgc.c',
     '#include <86box/vid_pgc.h>\n',
     '#include <86box/vid_pgc.h>\n#include <stdbool.h>\n#include <86box/kairo_gpu.h> /* KairoX86#268 */\n'),
    ('86box/src/video/vid_pgc.c',
     '\n/* Draw the screen in CGA mode. */\nvoid\npgc_cga_poll(pgc_t *dev)\n',
     "\n/* KairoX86#268: a CGA emulation line (pgc_cga_poll's mode, read as pgc_cga_text, _gfx40 or _gfx80 reads\n   it) to the GPU's scanout queue, coloured as video_process_8 colours it; returns whether the GPU draws it */\nstatic bool\npgc_cga_render_gpu(pgc_t *dev)\n{\n    if (!kairo_gpu_on)\n        return false;\n    bitmap_t       *bitmap  = buffer32;\n    const uint32_t  out     = (uint32_t) (bitmap->line[dev->displine] - bitmap->dat);\n    const uint32_t *palette = pal_lookup;\n    uint16_t        memaddr = (dev->mapram[0x3ed] | (dev->mapram[0x3ec] << 8)) & 0x3fff;\n    if (dev->mapram[0x03d8] & 0x02) {\n        const bool hires = (dev->mapram[0x03d8] & 0x12) == 0x12;\n        uint32_t   colours[4];\n        if (hires) {\n            colours[0] = palette[16];\n            colours[1] = palette[(dev->mapram[0x3d9] & 15) + 16];\n        } else {\n            const int col = ((dev->mapram[0x3d9] & 16) ? 8 : 0) + 16;\n            colours[0]    = palette[(dev->mapram[0x3d9] & 15) + 16];\n            if (dev->mapram[0x3d9] & 32) {\n                colours[1] = palette[col | 3];\n                colours[2] = palette[col | 5];\n                colours[3] = palette[col | 7];\n            } else if (dev->mapram[0x3d8] & 4) {\n                colours[1] = palette[col | 3];\n                colours[2] = palette[col | 4];\n                colours[3] = palette[col | 7];\n            } else {\n                colours[1] = palette[col | 2];\n                colours[2] = palette[col | 4];\n                colours[3] = palette[col | 6];\n            }\n        }\n        uint8_t *bytes = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_BITS, 640, 20, colours,\n                                                    hires ? 2 : 4, hires ? 1 : 2, 0, hires ? 0 : KAIRO_SCAN_WIDE);\n        for (uint8_t x = 0; x < 40; x++) {\n            const uint8_t *addr = &dev->cga_vram[(memaddr + 2 * x + 80 * (dev->displine >> 2) + 0x2000 * ((dev->displine >> 1) & 1)) & 0x3fff];\n            bytes[x * 2]        = addr[0];\n            bytes[x * 2 + 1]    = addr[1];\n            dev->memaddr++;\n        }\n        kairo_gpu_scan_commit();\n        return true;\n    }\n    const int      w          = (dev->mapram[0x03d8] & 0x01) ? 80 : 40;\n    const int      pitch      = (dev->mapram[0x3e9] + 1) * 2;\n    const uint16_t scanline   = (dev->displine & 0x0f) % pitch;\n    const uint16_t cursoraddr = (dev->mapram[0x3ef] | (dev->mapram[0x3ee] << 8)) & 0x3fff;\n    const uint8_t *addr       = &dev->cga_vram[((memaddr + ((dev->displine / pitch) * w)) * 2) & 0x3ffe];\n    memaddr += (dev->displine / pitch) * w;\n    uint32_t *cells = kairo_gpu_scan(bitmap, bitmap->kairo_gpu, out, KAIRO_SCAN_TEXT, (uint32_t) w * ((w == 80) ? 8 : 16), (uint32_t) w,\n                                     palette, 256, 8, 0, (w == 80) ? 0 : KAIRO_SCAN_WIDE);\n    for (int x = 0; x < w; x++) {\n        const uint8_t chr  = *addr++;\n        const uint8_t attr = *addr++;\n        int           drawcursor;\n        if (memaddr == cursoraddr && (dev->cgablink & 8) && (dev->mapram[0x3ea] & 0x60) != 0x20)\n            drawcursor = ((dev->mapram[0x3ea] & 0x1f) <= (scanline >> 1)) && ((dev->mapram[0x3eb] & 0x1f) >= (scanline >> 1));\n        else\n            drawcursor = 0;\n        uint32_t fg = (attr & 15) + 16;\n        uint32_t bg;\n        if (dev->mapram[0x3d8] & 0x20) {\n            bg = ((attr >> 4) & 7) + 16;\n            if ((dev->cgablink & 8) && (attr & 0x80) && !drawcursor)\n                fg = bg;\n        } else\n            bg = (attr >> 4) + 16;\n        if (drawcursor) {\n            fg ^= 0x0f;\n            bg ^= 0x0f;\n        }\n        cells[x] = fontdatm[chr + dev->fontbase][scanline] | (fg << 8) | (bg << 16);\n        memaddr++;\n    }\n    kairo_gpu_scan_commit();\n    return true;\n}\n\n/* KairoX86#268: a native line (pgc_poll's, read as it reads it) to the GPU's scanout queue through the\n   card's palette */\nstatic void\npgc_render_gpu(pgc_t *dev)\n{\n    bitmap_t     *bitmap = buffer32;\n    const int32_t y      = dev->scan_top + dev->displine;\n    uint8_t      *bytes  = (uint8_t *) kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (bitmap->line[dev->displine] - bitmap->dat),\n                                                      KAIRO_SCAN_8, dev->screenw, (dev->screenw + 3) / 4, dev->palette, 256, 0xff, 0, 0);\n    for (uint32_t x = 0; x < dev->screenw; x++)\n        bytes[x] = (y >= 0 && y < (int32_t) dev->maxh) ? dev->vram[y * dev->maxw + ((uint32_t) dev->scan_left + x) % dev->maxw] : 0;\n    kairo_gpu_scan_commit();\n}\n\n/* Draw the screen in CGA mode. */\nvoid\npgc_cga_poll(pgc_t *dev)\n"),
    ('86box/src/video/vid_pgc.c',
     '            if ((dev->mapram[0x03d8] & 0x12) == 0x12)\n                pgc_cga_gfx80(dev);\n',
     '            if (pgc_cga_render_gpu(dev)) {\n                /* KairoX86#268: the GPU draws the line */\n            } else if ((dev->mapram[0x03d8] & 0x12) == 0x12)\n                pgc_cga_gfx80(dev);\n'),
    ('86box/src/video/vid_pgc.c',
     '            /* Rows outside the framebuffer are blank; columns wrap. */\n            y = dev->scan_top + dev->displine;\n            for (uint32_t x = 0; x < dev->screenw; x++) {\n',
     '            /* Rows outside the framebuffer are blank; columns wrap. */\n            y = dev->scan_top + dev->displine;\n            if (kairo_gpu_on) {\n                pgc_render_gpu(dev); /* KairoX86#268 */\n            } else for (uint32_t x = 0; x < dev->screenw; x++) {\n'),
]

PATCHES = {
    'kairo9x-build': KAIRO9X_BUILD,
    'kairo9x-platform': KAIRO9X_PLATFORM,
    'kairo9x-cpu': KAIRO9X_CPU,
    'kairo9x-machine': KAIRO9X_MACHINE,
    'kairo9x-video': KAIRO9X_VIDEO,
    'kairo9x-sound': KAIRO9X_SOUND,
    'kairox86-license': KAIROX86_LICENSE,
    'kairox86-library': KAIROX86_LIBRARY,
    'kairox86-stop': KAIROX86_STOP,
    'kairox86-repeatable': KAIROX86_REPEATABLE,
    'kairox86-sync-render': KAIROX86_SYNC_RENDER,
    'kairox86-raster': KAIROX86_RASTER,
    'kairox86-guest-input': KAIROX86_GUEST_INPUT,
    'kairox86-native-size': KAIROX86_NATIVE_SIZE,
    'kairox86-own-memory': KAIROX86_OWN_MEMORY,
    'kairox86-path-append': KAIROX86_PATH_APPEND,
    'kairox86-mouse-enable': KAIROX86_MOUSE_ENABLE,
    'kairox86-lazy-blocks': KAIROX86_LAZY_BLOCKS,
    'kairox86-pages-as-reset': KAIROX86_PAGES_AS_RESET,
    'kairox86-lazy-pit': KAIROX86_LAZY_PIT,
    'kairox86-video-hoist': KAIROX86_VIDEO_HOIST,
    'kairox86-halt-skip': KAIROX86_HALT_SKIP,
    'kairox86-halt-skip-vx0': KAIROX86_HALT_SKIP_VX0,
    'kairox86-densel-once': KAIROX86_DENSEL_ONCE,
    'kairox86-lowres-8bpp': KAIROX86_LOWRES_8BPP,
    'kairox86-opl3-thread': KAIROX86_OPL3_THREAD,
    'kairox86-plain-planar-write': KAIROX86_PLAIN_PLANAR_WRITE,
    'kairox86-arm64-fp-callee-saved': KAIROX86_ARM64_FP_CALLEE_SAVED,
    'kairox86-flags-zpna-once': KAIROX86_FLAGS_ZPNA_ONCE,
    'kairox86-voodoo-settle': KAIROX86_VOODOO_SETTLE,
    'kairox86-banshee-16bpp': KAIROX86_BANSHEE_16BPP,
    'kairox86-diag-code-map': KAIROX86_DIAG_CODE_MAP,
    'kairox86-pcem-430vx': KAIROX86_PCEM_430VX,
    'kairox86-pci-dev0-card': KAIROX86_PCI_DEV0_CARD,
    'kairox86-gpu-scanout': KAIROX86_GPU_SCANOUT,
    'kairox86-gpu-svga-touch': KAIROX86_GPU_SVGA_TOUCH,
    'kairox86-gpu-cga': KAIROX86_GPU_CGA,
    'kairox86-whole-frames': KAIROX86_WHOLE_FRAMES,
    'kairox86-gpu-mda': KAIROX86_GPU_MDA,
    'kairox86-gpu-hercules': KAIROX86_GPU_HERCULES,
    'kairox86-gpu-hercules-plus': KAIROX86_GPU_HERCULES_PLUS,
    'kairox86-gpu-incolor': KAIROX86_GPU_INCOLOR,
    'kairox86-gpu-ega': KAIROX86_GPU_EGA,
    'kairox86-gpu-genius': KAIROX86_GPU_GENIUS,
    'kairox86-gpu-wy700': KAIROX86_GPU_WY700,
    'kairox86-gpu-quadcolor': KAIROX86_GPU_QUADCOLOR,
    'kairox86-gpu-v6355': KAIROX86_GPU_V6355,
    'kairox86-gpu-pgc': KAIROX86_GPU_PGC,
}

ADDED = [
    '86box/src/device/kairo_cassette.c',
    '86box/src/include/86box/kairo_gpu.h',
    '86box/src/include/86box/kairo_cassette.h',
    '86box/src/include/86box/k9x_hot.h',
    '86box/src/network/net_slirp_stub.c',
    '86box/src/sound/null_audio.c',
    '86box/src/unix/headless_main.c',
    '86box/src/unix/headless_sdl/SDL3/SDL.h',
]

# KairoX86#1: GPL-2.0-only code cannot ship beside the GPL-3.0-only shader runtime. The cassette port
# (PCE's cassette.c and cassette.h) is replaced by KairoX86's own kairo_cassette.c/.h, with the same
# calls; VDE networking (net_vde.c, Linux hosts only) is left out.
REMOVED = [
    '86box/src/device/cassette.c',
    '86box/src/include/86box/cassette.h',
    '86box/src/network/net_vde.c',
]
