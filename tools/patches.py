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

# KairoX86#287: on a Voodoo Banshee or Voodoo3 the 3D engine draws in the memory the 2D display shows, and
# the display redraws only the pages marked changed: every 3D colour write (triangle spans, fast fills,
# LFB writes) marks its pages, as the blitter's writes do. The Voodoo Graphics and Voodoo2 have no such
# map (changedvram NULL).
KAIROX86_VOODOO_CHANGED_PAGES = [
    ('86box/src/include/86box/vid_voodoo_render.h',
     'void voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params);\n',
     "void voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params);\n/* KairoX86#287: marks the desktop's pages under pixels x0 to x1 of a 16-bit colour row (at byte offset row,\n   tiled or not) changed, on the cards whose display redraws by page (changedvram set) */\nvoid voodoo_mark_changed(voodoo_t *voodoo, uint32_t row, int tiled, int x0, int x1);\n"),
    ('86box/src/video/vid_voodoo_render.c',
     '\nvoid\nvoodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n',
     '\n/* KairoX86#287 */\nvoid\nvoodoo_mark_changed(voodoo_t *voodoo, uint32_t row, int tiled, int x0, int x1)\n{\n    if (voodoo->changedvram == NULL)\n        return;\n    if (x0 > x1) {\n        const int t = x0;\n        x0          = x1;\n        x1          = t;\n    }\n    if (tiled) {\n        /* 64 pixels across, 32 rows down: each tile column is one page */\n        for (int tile = x0 >> 6; tile <= (x1 >> 6); tile++)\n            voodoo->changedvram[((row + (uint32_t) tile * 4096) & voodoo->fb_mask) >> 12] = changeframecount;\n    } else {\n        const uint32_t last = row + (uint32_t) x1 * 2;\n        for (uint32_t addr = (row + (uint32_t) x0 * 2) & ~0xfffu; addr <= last; addr += 4096)\n            voodoo->changedvram[(addr & voodoo->fb_mask) >> 12] = changeframecount;\n    }\n}\n\nvoid\nvoodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '        span_end_x         = x2;\n',
     '        span_end_x         = x2;\n        const int span_start_x = x; /* KairoX86#287 */\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '        if (voodoo->params.draw_offset == voodoo->params.front_offset && !SLI_ENABLED) {\n            if (real_y < 2048)\n                voodoo->dirty_line[real_y] = 1;\n        }\n',
     "        if (voodoo->params.draw_offset == voodoo->params.front_offset && !SLI_ENABLED) {\n            if (real_y < 2048)\n                voodoo->dirty_line[real_y] = 1;\n        }\n        /* KairoX86#287: the span's pages on the desktop */\n        if (!SLI_ENABLED && (params->fbzMode & FBZ_RGB_WMASK))\n            voodoo_mark_changed(voodoo, params->draw_offset + (params->col_tiled ? ((real_y >> 5) * params->row_width + (real_y & 31) * 128) : (real_y * params->row_width)),\n                                params->col_tiled, span_start_x, span_end_x);\n"),
    ('86box/src/video/vid_voodoo_blitter.c',
     '                /* Mark line dirty for single buffer mode */\n                if (params->draw_offset == params->front_offset && y < 2048)\n                    voodoo->dirty_line[y] = 1;\n',
     "                /* Mark line dirty for single buffer mode */\n                if (params->draw_offset == params->front_offset && y < 2048)\n                    voodoo->dirty_line[y] = 1;\n                /* KairoX86#287: the row's pages on the desktop */\n                if (params->clipRight > params->clipLeft)\n                    voodoo_mark_changed(voodoo, params->draw_offset + (voodoo->col_tiled ? ((y >> 5) * voodoo->row_width + (y & 31) * 128) : (y * voodoo->row_width)),\n                                        voodoo->col_tiled, params->clipLeft, params->clipRight - 1);\n"),
    ('86box/src/video/vid_voodoo_fb.c',
     '        x = lfb_addr & 0xffe;\n        y = (lfb_addr >> 12) & 0x3ff;\n    } else {\n        x = lfb_addr & 0x7fe;\n        y = (lfb_addr >> 11) & 0x3ff;\n    }\n\n    y = lfb_y_origin_flip(voodoo, y);\n    if (y < 0)\n        return;\n\n    if (SLI_ENABLED) {\n        if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(y & 1)))\n            return;\n        y >>= 1;\n    }\n\n    if (voodoo->fb_write_offset == voodoo->params.front_offset && y < 2048)\n        voodoo->dirty_line[y] = 1;\n',
     "        x = lfb_addr & 0xffe;\n        y = (lfb_addr >> 12) & 0x3ff;\n    } else {\n        x = lfb_addr & 0x7fe;\n        y = (lfb_addr >> 11) & 0x3ff;\n    }\n\n    y = lfb_y_origin_flip(voodoo, y);\n    if (y < 0)\n        return;\n\n    if (SLI_ENABLED) {\n        if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(y & 1)))\n            return;\n        y >>= 1;\n    }\n\n    if (voodoo->fb_write_offset == voodoo->params.front_offset && y < 2048)\n        voodoo->dirty_line[y] = 1;\n    /* KairoX86#287: the pixels' pages on the desktop */\n    voodoo_mark_changed(voodoo, voodoo->fb_write_offset + (voodoo->col_tiled ? ((y & 31) * 128 + (y >> 5) * voodoo->row_width) : (y * voodoo->row_width)),\n                        voodoo->col_tiled, x >> 1, (x >> 1) + 1 - 1);\n"),
    ('86box/src/video/vid_voodoo_fb.c',
     '        x = addr & 0xffe;\n        y = (addr >> 12) & 0x3ff;\n    } else {\n        x = addr & 0x7fe;\n        y = (addr >> 11) & 0x3ff;\n    }\n\n    y = lfb_y_origin_flip(voodoo, y);\n    if (y < 0)\n        return;\n\n    if (SLI_ENABLED) {\n        if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(y & 1)))\n            return;\n        y >>= 1;\n    }\n\n    if (voodoo->fb_write_offset == voodoo->params.front_offset && y < 2048)\n        voodoo->dirty_line[y] = 1;\n',
     "        x = addr & 0xffe;\n        y = (addr >> 12) & 0x3ff;\n    } else {\n        x = addr & 0x7fe;\n        y = (addr >> 11) & 0x3ff;\n    }\n\n    y = lfb_y_origin_flip(voodoo, y);\n    if (y < 0)\n        return;\n\n    if (SLI_ENABLED) {\n        if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(y & 1)))\n            return;\n        y >>= 1;\n    }\n\n    if (voodoo->fb_write_offset == voodoo->params.front_offset && y < 2048)\n        voodoo->dirty_line[y] = 1;\n    /* KairoX86#287: the pixels' pages on the desktop */\n    voodoo_mark_changed(voodoo, voodoo->fb_write_offset + (voodoo->col_tiled ? ((y & 31) * 128 + (y >> 5) * voodoo->row_width) : (y * voodoo->row_width)),\n                        voodoo->col_tiled, x >> 1, (x >> 1) + count - 1);\n"),
]

# KairoX86#277, #278: the Voodoo's triangles on the GPU (86box/kairo_gpu_voodoo.h, core/kairo/gpu_voodoo.c).
# With Hardware acceleration on, video memory (svga_init's), the Voodoo Graphics/Voodoo2 frame buffer and
# every card's texture caches are memory the GPU shares; triangles are recorded instead of going to the
# render threads, and drawn where 86Box waits for those threads. Where the processor reads or writes card
# memory with no such wait (the linear aperture, the 2D engine, the 3D LFB's reads, texture downloads
# and decodes, the display) it touches it first, which draws the recorded triangles if they draw there;
# the counter registers draw them all first. Off, nothing changes.
KAIROX86_GPU_VOODOO = [
    ('86box/src/include/86box/vid_voodoo_common.h',
     '    ATOMIC_INT k_fifo_state;\n',
     "    ATOMIC_INT k_fifo_state;\n    /* KairoX86#278: its triangles' GPU state (kairo_gpu_voodoo.h), NULL in software */\n    void *k_gpu;\n"),
    ('86box/src/include/86box/vid_voodoo_render.h',
     '#ifndef VIDEO_VOODOO_RENDER_H\n#define VIDEO_VOODOO_RENDER_H\n',
     '#ifndef VIDEO_VOODOO_RENDER_H\n#define VIDEO_VOODOO_RENDER_H\n\n#include <86box/kairo_gpu_voodoo.h> /* KairoX86#278 */\n'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'voodoo_wait_for_render_thread_idle(voodoo_t *voodoo)\n{\n',
     'voodoo_wait_for_render_thread_idle(voodoo_t *voodoo)\n{\n    /* KairoX86#278: on the GPU, the recorded triangles drawn */\n    if (voodoo->k_gpu != NULL) {\n        kairo_voodoo_gpu_drain(voodoo);\n        return;\n    }\n'),
    ('86box/src/video/vid_voodoo_render.c',
     'voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n{\n',
     'voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n{\n    /* KairoX86#278: on the GPU, recorded for its kernel */\n    if (voodoo->k_gpu != NULL) {\n        voodoo_use_texture(voodoo, params, 0);\n        if (voodoo->dual_tmus)\n            voodoo_use_texture(voodoo, params, 1);\n        kairo_voodoo_gpu_queue(voodoo, params);\n        return;\n    }\n'),
    ('86box/src/video/vid_svga.c',
     '    svga->vram              = calloc(memsize + 4096, 1);\n',
     '    /* KairoX86#278: with the GPU on, memory it shares */\n    svga->vram              = kairo_gpu_on ? kairo_gpu_alloc(memsize + 4096) : calloc(memsize + 4096, 1);\n'),
    ('86box/src/video/vid_svga.c',
     '    free(svga->changedvram);\n    free(svga->vram);\n',
     '    free(svga->changedvram);\n    if (kairo_gpu_on) /* KairoX86#278 */\n        kairo_gpu_free(svga->vram);\n    else\n        free(svga->vram);\n'),
    ('86box/src/video/vid_voodoo.c',
     '#include <86box/config.h> /* KairoX86#228: config_kairo_int() */\n',
     "#include <86box/config.h> /* KairoX86#228: config_kairo_int() */\n#include <86box/kairo_gpu.h> /* KairoX86#278 */\n\n/* KairoX86#278: a TMU's texture cache entry, and the caches: with the GPU on, one block of memory it\n   shares per TMU */\n#define VOODOO_TEXTURE_ENTRY_BYTES ((256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2) * 4)\n\nstatic void\nvoodoo_alloc_texture_caches(voodoo_t *voodoo)\n{\n    for (int tmu = 0; tmu < (voodoo->dual_tmus ? 2 : 1); tmu++) {\n        uint8_t *block = kairo_gpu_on ? kairo_gpu_alloc((size_t) VOODOO_TEXTURE_ENTRY_BYTES * TEX_CACHE_MAX) : NULL;\n\n        for (int c = 0; c < TEX_CACHE_MAX; c++) {\n            voodoo->texture_cache[tmu][c].data     = kairo_gpu_on ? (uint32_t *) (block + (size_t) VOODOO_TEXTURE_ENTRY_BYTES * c)\n                                                                  : calloc(1, VOODOO_TEXTURE_ENTRY_BYTES);\n            voodoo->texture_cache[tmu][c].base     = -1; /*invalid*/\n            voodoo->texture_cache[tmu][c].refcount = 0;\n        }\n    }\n}\n\nstatic void\nvoodoo_free_texture_caches(voodoo_t *voodoo)\n{\n    for (int tmu = 0; tmu < (voodoo->dual_tmus ? 2 : 1); tmu++) {\n        if (kairo_gpu_on)\n            kairo_gpu_free(voodoo->texture_cache[tmu][0].data);\n        else\n            for (int c = 0; c < TEX_CACHE_MAX; c++)\n                free(voodoo->texture_cache[tmu][c].data);\n    }\n}\n"),
    ('86box/src/video/vid_voodoo.c',
     '    voodoo->fb_mem     = calloc(1, 4 * 1024 * 1024);\n',
     '    voodoo->fb_mem     = kairo_gpu_on ? kairo_gpu_alloc(4 * 1024 * 1024) : calloc(1, 4 * 1024 * 1024); /* KairoX86#278 */\n'),
    ('86box/src/video/vid_voodoo.c',
     '    voodoo->tex_mem_w[1] = (uint16_t *) voodoo->tex_mem[1];\n\n    for (c = 0; c < TEX_CACHE_MAX; c++) {\n        voodoo->texture_cache[0][c].data     = calloc(1, (256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2) * 4);\n        voodoo->texture_cache[0][c].base     = -1; /*invalid*/\n        voodoo->texture_cache[0][c].refcount = 0;\n        if (voodoo->dual_tmus) {\n            voodoo->texture_cache[1][c].data     = calloc(1, (256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2) * 4);\n            voodoo->texture_cache[1][c].base     = -1; /*invalid*/\n            voodoo->texture_cache[1][c].refcount = 0;\n        }\n    }\n',
     '    voodoo->tex_mem_w[1] = (uint16_t *) voodoo->tex_mem[1];\n\n    voodoo_alloc_texture_caches(voodoo); /* KairoX86#278 */\n    if (kairo_gpu_on)\n        voodoo->k_gpu = kairo_voodoo_gpu_open(voodoo);\n'),
    ('86box/src/video/vid_voodoo.c',
     '    voodoo_generate_filter_v2(voodoo);\n\n    for (c = 0; c < TEX_CACHE_MAX; c++) {\n        voodoo->texture_cache[0][c].data     = calloc(1, (256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2) * 4);\n        voodoo->texture_cache[0][c].base     = -1; /*invalid*/\n        voodoo->texture_cache[0][c].refcount = 0;\n        if (voodoo->dual_tmus) {\n            voodoo->texture_cache[1][c].data     = calloc(1, (256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2) * 4);\n            voodoo->texture_cache[1][c].base     = -1; /*invalid*/\n            voodoo->texture_cache[1][c].refcount = 0;\n        }\n    }\n',
     '    voodoo_generate_filter_v2(voodoo);\n\n    voodoo_alloc_texture_caches(voodoo); /* KairoX86#278: its GPU state once the Banshee gives it memory */\n'),
    ('86box/src/video/vid_voodoo.c',
     '    for (uint8_t c = 0; c < TEX_CACHE_MAX; c++) {\n        if (voodoo->dual_tmus)\n            free(voodoo->texture_cache[1][c].data);\n        free(voodoo->texture_cache[0][c].data);\n    }\n',
     '    kairo_voodoo_gpu_close(voodoo); /* KairoX86#278 */\n    voodoo_free_texture_caches(voodoo);\n'),
    ('86box/src/video/vid_voodoo.c',
     '    if (voodoo->type < VOODOO_BANSHEE && voodoo->fb_mem) {\n        free(voodoo->fb_mem);\n',
     '    if (voodoo->type < VOODOO_BANSHEE && voodoo->fb_mem) {\n        if (kairo_gpu_on) /* KairoX86#278 */\n            kairo_gpu_free(voodoo->fb_mem);\n        else\n            free(voodoo->fb_mem);\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '#include <86box/vid_voodoo_render.h>\n',
     '#include <86box/vid_voodoo_render.h>\n#include <86box/kairo_gpu.h> /* KairoX86#278 */\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    banshee->voodoo->texture_mask = banshee->svga.vram_mask;\n',
     '    banshee->voodoo->texture_mask = banshee->svga.vram_mask;\n    if (kairo_gpu_on) /* KairoX86#278 */\n        banshee->voodoo->k_gpu = kairo_voodoo_gpu_open(banshee->voodoo);\n'),
    ('86box/src/video/vid_voodoo.c',
     '            case SST_fbiPixelsIn:\n                temp = voodoo->fbiPixelsIn & 0xffffff;\n                break;\n            case SST_fbiChromaFail:\n                temp = voodoo->fbiChromaFail & 0xffffff;\n                break;\n            case SST_fbiZFuncFail:\n                temp = voodoo->fbiZFuncFail & 0xffffff;\n                break;\n            case SST_fbiAFuncFail:\n                temp = voodoo->fbiAFuncFail & 0xffffff;\n                break;\n            case SST_fbiPixelsOut:\n                temp = voodoo->fbiPixelsOut & 0xffffff;\n                break;\n',
     '            case SST_fbiPixelsIn:\n                if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                    kairo_voodoo_gpu_drain(voodoo);\n                temp = voodoo->fbiPixelsIn & 0xffffff;\n                break;\n            case SST_fbiChromaFail:\n                if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                    kairo_voodoo_gpu_drain(voodoo);\n                temp = voodoo->fbiChromaFail & 0xffffff;\n                break;\n            case SST_fbiZFuncFail:\n                if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                    kairo_voodoo_gpu_drain(voodoo);\n                temp = voodoo->fbiZFuncFail & 0xffffff;\n                break;\n            case SST_fbiAFuncFail:\n                if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                    kairo_voodoo_gpu_drain(voodoo);\n                temp = voodoo->fbiAFuncFail & 0xffffff;\n                break;\n            case SST_fbiPixelsOut:\n                if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                    kairo_voodoo_gpu_drain(voodoo);\n                temp = voodoo->fbiPixelsOut & 0xffffff;\n                break;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '                case SST_fbiPixelsIn:\n                    ret = voodoo->fbiPixelsIn & 0xffffff;\n                    break;\n                case SST_fbiChromaFail:\n                    ret = voodoo->fbiChromaFail & 0xffffff;\n                    break;\n                case SST_fbiZFuncFail:\n                    ret = voodoo->fbiZFuncFail & 0xffffff;\n                    break;\n                case SST_fbiAFuncFail:\n                    ret = voodoo->fbiAFuncFail & 0xffffff;\n                    break;\n                case SST_fbiPixelsOut:\n                    ret = voodoo->fbiPixelsOut & 0xffffff;\n                    break;\n',
     '                case SST_fbiPixelsIn:\n                    if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                        kairo_voodoo_gpu_drain(voodoo);\n                    ret = voodoo->fbiPixelsIn & 0xffffff;\n                    break;\n                case SST_fbiChromaFail:\n                    if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                        kairo_voodoo_gpu_drain(voodoo);\n                    ret = voodoo->fbiChromaFail & 0xffffff;\n                    break;\n                case SST_fbiZFuncFail:\n                    if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                        kairo_voodoo_gpu_drain(voodoo);\n                    ret = voodoo->fbiZFuncFail & 0xffffff;\n                    break;\n                case SST_fbiAFuncFail:\n                    if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                        kairo_voodoo_gpu_drain(voodoo);\n                    ret = voodoo->fbiAFuncFail & 0xffffff;\n                    break;\n                case SST_fbiPixelsOut:\n                    if (voodoo->k_gpu != NULL) /* KairoX86#278: what the GPU has to draw, counted */\n                        kairo_voodoo_gpu_drain(voodoo);\n                    ret = voodoo->fbiPixelsOut & 0xffffff;\n                    break;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_read_b;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 1);\n    cycles -= svga->monitor->mon_video_timing_read_b;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_read_w;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 2);\n    cycles -= svga->monitor->mon_video_timing_read_w;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_read_l;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 4);\n    cycles -= svga->monitor->mon_video_timing_read_l;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_write_b;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 1);\n    cycles -= svga->monitor->mon_video_timing_write_b;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_write_w;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 2);\n    cycles -= svga->monitor->mon_video_timing_write_w;\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    cycles -= svga->monitor->mon_video_timing_write_l;\n',
     '    /* KairoX86#278: what the GPU draws there, drawn first */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_touch((voodoo_t *) voodoo, addr & svga->vram_mask, 4);\n    cycles -= svga->monitor->mon_video_timing_write_l;\n'),
    ('86box/src/video/vid_voodoo_banshee_blitter.c',
     'banshee_do_2d_blit(voodoo_t *voodoo, int count, uint32_t data)\n{\n',
     'banshee_do_2d_blit(voodoo_t *voodoo, int count, uint32_t data)\n{\n    /* KairoX86#278: the 2D engine works on memory the GPU may still draw on */\n    if (voodoo->k_gpu != NULL)\n        kairo_voodoo_gpu_drain(voodoo);\n'),
    ('86box/src/video/vid_voodoo_fb.c',
     '    if (read_addr > voodoo->fb_mask)\n        return 0xffff;\n',
     '    if (read_addr > voodoo->fb_mask)\n        return 0xffff;\n    if (voodoo->k_gpu != NULL) /* KairoX86#278 */\n        kairo_voodoo_gpu_touch(voodoo, read_addr & ~3, 4);\n'),
    ('86box/src/video/vid_voodoo_fb.c',
     '    if (read_addr > voodoo->fb_mask)\n        return 0xffffffff;\n',
     '    if (read_addr > voodoo->fb_mask)\n        return 0xffffffff;\n    if (voodoo->k_gpu != NULL) /* KairoX86#278 */\n        kairo_voodoo_gpu_touch(voodoo, read_addr & ~3, 4);\n'),
    ('86box/src/video/vid_voodoo_texture.c',
     '        uint32_t      tex_addr = params->tex_base[tmu][lod] & texture_mask;\n',
     "        uint32_t      tex_addr = params->tex_base[tmu][lod] & texture_mask;\n        /* KairoX86#278: a Banshee's textures are in the memory the GPU draws on */\n        if ((voodoo->k_gpu != NULL) && (voodoo->type >= VOODOO_BANSHEE))\n            kairo_voodoo_gpu_touch(voodoo, tex_addr, params->tex_end[tmu][lod] - params->tex_base[tmu][lod]);\n"),
    ('86box/src/video/vid_voodoo_texture.c',
     '    *(uint32_t *) (&voodoo->tex_mem[tmu][addr & texture_mask]) = val;\n}\n',
     '    if ((voodoo->k_gpu != NULL) && (voodoo->type >= VOODOO_BANSHEE)) /* KairoX86#278 */\n        kairo_voodoo_gpu_touch(voodoo, addr & texture_mask, 4);\n    *(uint32_t *) (&voodoo->tex_mem[tmu][addr & texture_mask]) = val;\n}\n'),
    ('86box/src/video/vid_voodoo_display.c',
     '                uint16_t *src = (uint16_t *) &draw_voodoo->fb_mem[draw_voodoo->front_offset + draw_line * draw_voodoo->row_width];\n',
     '                if (draw_voodoo->k_gpu != NULL) /* KairoX86#278: the line, drawn */\n                    kairo_voodoo_gpu_touch(draw_voodoo, draw_voodoo->front_offset + draw_line * draw_voodoo->row_width, draw_voodoo->row_width);\n                uint16_t *src = (uint16_t *) &draw_voodoo->fb_mem[draw_voodoo->front_offset + draw_line * draw_voodoo->row_width];\n'),
    ('86box/src/video/vid_voodoo_fifo.c',
     '        voodoo_wake_fifo_thread_now(voodoo);\n        plat_delay_ms(0);\n    }\n    voodoo_wait_for_render_thread_idle(voodoo);\n',
     '        voodoo_wake_fifo_thread_now(voodoo);\n        plat_delay_ms(0);\n    }\n    /* KairoX86#278: on the GPU, the caller touches what the line shows instead */\n    if (voodoo->k_gpu == NULL)\n        voodoo_wait_for_render_thread_idle(voodoo);\n'),
    ('86box/src/video/vid_voodoo_banshee.c',
     '    if (banshee->voodoo != NULL)\n        voodoo_settle(banshee->voodoo);\n',
     '    if (banshee->voodoo != NULL)\n        voodoo_settle(banshee->voodoo);\n    /* KairoX86#278: the desktop and the overlay as shown, drawn first where the GPU draws on them */\n    if ((banshee->voodoo != NULL) && (banshee->voodoo->k_gpu != NULL)) {\n        const uint32_t rows = (uint32_t) svga->vtotal + 1;\n        const uint32_t desktop = (banshee->vidProcCfg & VIDPROCCFG_DESKTOP_TILE)\n                                     ? banshee->desktop_stride_tiled * ((rows + 31) / 32)\n                                     : (banshee->vidDesktopOverlayStride & 0x3fff) * rows;\n        kairo_voodoo_gpu_touch(banshee->voodoo, banshee->vidDesktopStartAddr & svga->vram_mask, desktop);\n        if (banshee->vidProcCfg & VIDPROCCFG_OVERLAY_ENABLE)\n            kairo_voodoo_gpu_touch(banshee->voodoo, svga->overlay_latch.addr & svga->vram_mask, svga->overlay_latch.pitch * rows);\n    }\n'),
]

# KairoX86#288: the Voodoo's rotating stipple as DOSBox-X (and MAME) has it: the register turns left,
# unsigned, once for every pixel that reaches the test, in raster order, from one triangle to the next.
# A triangle takes the register as it is queued and moves it on by its pixels (its spans after clipping,
# from its edges: voodoo_triangle_pixels); each line of it starts from that turned by the lines before
# it, whichever render thread draws it. Both recompilers turn it left too.
KAIROX86_VOODOO_STIPPLE = [
    ('86box/src/video/vid_voodoo_render.c',
     '    int stipple;\n} voodoo_state_t;\n',
     '    uint32_t stipple; /* KairoX86#288: unsigned, so it turns (it sign-filled as an int) */\n} voodoo_state_t;\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '\nstatic void\nvoodoo_half_triangle(voodoo_t *voodoo, voodoo_params_t *params, voodoo_state_t *state, int ystart, int yend, int odd_even)\n',
     "\n/* The triangle's vertices (12.4, sign extended) and its edges' slopes, from its parameters */\nstatic void\nvoodoo_triangle_edges(const voodoo_params_t *params, voodoo_state_t *state)\n{\n    state->vertexAy = params->vertexAy & ~0xffff0000;\n    if (state->vertexAy & 0x8000)\n        state->vertexAy |= 0xffff0000;\n    state->vertexBy = params->vertexBy & ~0xffff0000;\n    if (state->vertexBy & 0x8000)\n        state->vertexBy |= 0xffff0000;\n    state->vertexCy = params->vertexCy & ~0xffff0000;\n    if (state->vertexCy & 0x8000)\n        state->vertexCy |= 0xffff0000;\n\n    state->vertexAx = params->vertexAx & ~0xffff0000;\n    if (state->vertexAx & 0x8000)\n        state->vertexAx |= 0xffff0000;\n    state->vertexBx = params->vertexBx & ~0xffff0000;\n    if (state->vertexBx & 0x8000)\n        state->vertexBx |= 0xffff0000;\n    state->vertexCx = params->vertexCx & ~0xffff0000;\n    if (state->vertexCx & 0x8000)\n        state->vertexCx |= 0xffff0000;\n\n    if (state->vertexBy - state->vertexAy)\n        state->dxAB = (int) ((((int64_t) state->vertexBx << 12) - ((int64_t) state->vertexAx << 12)) << 4) / (state->vertexBy - state->vertexAy);\n    else\n        state->dxAB = 0;\n    if (state->vertexCy - state->vertexAy)\n        state->dxAC = (int) ((((int64_t) state->vertexCx << 12) - ((int64_t) state->vertexAx << 12)) << 4) / (state->vertexCy - state->vertexAy);\n    else\n        state->dxAC = 0;\n    if (state->vertexCy - state->vertexBy)\n        state->dxBC = (int) ((((int64_t) state->vertexCx << 12) - ((int64_t) state->vertexBx << 12)) << 4) / (state->vertexCy - state->vertexBy);\n    else\n        state->dxBC = 0;\n    state->xdir = params->sign ? -1 : 1;\n}\n\n/* KairoX86#288: the pixels line y of the triangle draws: its span after clipping, as\n   voodoo_half_triangle finds it */\nstatic int\nvoodoo_span_pixels(const voodoo_params_t *params, const voodoo_state_t *state, int y)\n{\n    const int real_y = (y << 4) + 8;\n    int       x      = (state->vertexAx << 12) + ((state->dxAC * (real_y - state->vertexAy)) >> 4);\n    int       x2;\n\n    if (real_y < state->vertexBy)\n        x2 = (state->vertexAx << 12) + ((state->dxAB * (real_y - state->vertexAy)) >> 4);\n    else\n        x2 = (state->vertexBx << 12) + ((state->dxBC * (real_y - state->vertexBy)) >> 4);\n    if (state->xdir > 0)\n        x2 -= (1 << 16);\n    else\n        x -= (1 << 16);\n    x  = (x + 0x7000) >> 16;\n    x2 = (x2 + 0x7000) >> 16;\n    if (params->fbzMode & 1) {\n        if (state->xdir > 0) {\n            if (x < params->clipLeft)\n                x = params->clipLeft;\n            if (x2 >= params->clipRight)\n                x2 = params->clipRight - 1;\n        } else {\n            if (x >= params->clipRight)\n                x = params->clipRight - 1;\n            if (x2 < params->clipLeft)\n                x2 = params->clipLeft;\n        }\n    }\n    if ((x2 < x && state->xdir > 0) || (x2 > x && state->xdir < 0))\n        return 0;\n    return ((x2 > x) ? (x2 - x) : (x - x2)) + 1;\n}\n\n/* KairoX86#288: every pixel the triangle draws on this card, as voodoo_half_triangle walks its lines */\nuint32_t\nvoodoo_triangle_pixels(voodoo_t *voodoo, const voodoo_params_t *params)\n{\n    voodoo_state_t state  = { 0 };\n    const int      y_diff = SLI_ENABLED ? 2 : 1;\n    uint32_t       pixels = 0;\n    int            y;\n    int            yend;\n\n    voodoo_triangle_edges(params, &state);\n    y    = (state.vertexAy + 7) >> 4;\n    yend = (state.vertexCy + 7) >> 4;\n    if ((params->fbzMode & 1) && (y < params->clipLowY))\n        y = params->clipLowY;\n    if ((params->fbzMode & 1) && (yend >= params->clipHighY))\n        yend = params->clipHighY;\n    if (SLI_ENABLED) {\n        const int y_origin = (voodoo->type >= VOODOO_BANSHEE) ? voodoo->y_origin_swap : (voodoo->v_disp - 1);\n        const int test_y   = (params->fbzMode & (1 << 17)) ? (y_origin - y) : y;\n\n        if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (test_y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(test_y & 1)))\n            y++;\n    }\n    for (; y < yend; y += y_diff)\n        pixels += (uint32_t) voodoo_span_pixels(params, &state, y);\n    return pixels;\n}\n\nstatic void\nvoodoo_half_triangle(voodoo_t *voodoo, voodoo_params_t *params, voodoo_state_t *state, int ystart, int yend, int odd_even)\n"),
    ('86box/src/video/vid_voodoo_render.c',
     '    state.vertexAy = params->vertexAy & ~0xffff0000;\n    if (state.vertexAy & 0x8000)\n        state.vertexAy |= 0xffff0000;\n    state.vertexBy = params->vertexBy & ~0xffff0000;\n    if (state.vertexBy & 0x8000)\n        state.vertexBy |= 0xffff0000;\n    state.vertexCy = params->vertexCy & ~0xffff0000;\n    if (state.vertexCy & 0x8000)\n        state.vertexCy |= 0xffff0000;\n\n    state.vertexAx = params->vertexAx & ~0xffff0000;\n    if (state.vertexAx & 0x8000)\n        state.vertexAx |= 0xffff0000;\n    state.vertexBx = params->vertexBx & ~0xffff0000;\n    if (state.vertexBx & 0x8000)\n        state.vertexBx |= 0xffff0000;\n    state.vertexCx = params->vertexCx & ~0xffff0000;\n    if (state.vertexCx & 0x8000)\n        state.vertexCx |= 0xffff0000;\n\n    vertexAy_adjusted = (state.vertexAy + 7) >> 4;\n    vertexCy_adjusted = (state.vertexCy + 7) >> 4;\n\n    if (state.vertexBy - state.vertexAy)\n        state.dxAB = (int) ((((int64_t) state.vertexBx << 12) - ((int64_t) state.vertexAx << 12)) << 4) / (state.vertexBy - state.vertexAy);\n    else\n        state.dxAB = 0;\n    if (state.vertexCy - state.vertexAy)\n        state.dxAC = (int) ((((int64_t) state.vertexCx << 12) - ((int64_t) state.vertexAx << 12)) << 4) / (state.vertexCy - state.vertexAy);\n    else\n        state.dxAC = 0;\n    if (state.vertexCy - state.vertexBy)\n        state.dxBC = (int) ((((int64_t) state.vertexCx << 12) - ((int64_t) state.vertexBx << 12)) << 4) / (state.vertexCy - state.vertexBy);\n    else\n        state.dxBC = 0;\n',
     '    voodoo_triangle_edges(params, &state); /* KairoX86#288: shared with voodoo_triangle_pixels */\n\n    vertexAy_adjusted = (state.vertexAy + 7) >> 4;\n    vertexCy_adjusted = (state.vertexCy + 7) >> 4;\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '    state.xstart = state.xend = state.vertexAx << 8;\n    state.xdir                = params->sign ? -1 : 1;\n',
     '    state.xstart = state.xend = state.vertexAx << 8;\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '    for (; state->y < yend; state->y += y_diff) {\n',
     "    /* KairoX86#288: the rotating stipple's turns before each line */\n    const int stipple_rotating = (params->fbzMode & (FBZ_STIPPLE | FBZ_STIPPLE_PATT)) == FBZ_STIPPLE;\n    uint32_t  stipple_pixels   = 0;\n\n    for (; state->y < yend; state->y += y_diff) {\n        if (stipple_rotating) {\n            const uint32_t turns = stipple_pixels & 31;\n\n            state->stipple = turns ? ((params->stipple << turns) | (params->stipple >> (32 - turns))) : params->stipple;\n            stipple_pixels += (uint32_t) voodoo_span_pixels(params, state, state->y);\n        }\n"),
    ('86box/src/video/vid_voodoo_render.c',
     'voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n{\n',
     "voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params)\n{\n    /* KairoX86#288: the rotating stipple's register, turned on by the triangle's pixels once it is queued */\n    const int stipple_rotating = (params->fbzMode & (FBZ_STIPPLE | FBZ_STIPPLE_PATT)) == FBZ_STIPPLE;\n    uint32_t  stipple_next     = params->stipple;\n\n    if (stipple_rotating) {\n        const uint32_t turns = voodoo_triangle_pixels(voodoo, params) & 31;\n\n        if (turns)\n            stipple_next = (params->stipple << turns) | (params->stipple >> (32 - turns));\n    }\n\n"),
    ('86box/src/video/vid_voodoo_render.c',
     '        kairo_voodoo_gpu_queue(voodoo, params);\n        return;\n    }\n',
     '        kairo_voodoo_gpu_queue(voodoo, params);\n        if (stipple_rotating)\n            voodoo->params.stipple = stipple_next;\n        return;\n    }\n'),
    ('86box/src/video/vid_voodoo_render.c',
     '    memcpy(params_new, params, sizeof(voodoo_params_t));\n',
     '    memcpy(params_new, params, sizeof(voodoo_params_t));\n    if (stipple_rotating)\n        voodoo->params.stipple = stipple_next;\n'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'void voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params);\n',
     'void voodoo_queue_triangle(voodoo_t *voodoo, voodoo_params_t *params);\n/* KairoX86#288: the pixels a triangle draws on this card (its spans after clipping) */\nuint32_t voodoo_triangle_pixels(voodoo_t *voodoo, const voodoo_params_t *params);\n'),
    ('86box/src/include/86box/vid_voodoo_codegen_x86-64.h',
     '            addbyte(0xd1); /* ROR state->stipple[EDI], 1*/\n            addbyte(0x8f);\n',
     '            addbyte(0xd1); /* ROL state->stipple[EDI], 1 (KairoX86#288: left, as the C code and DOSBox-X turn it) */\n            addbyte(0x87);\n'),
    ('86box/src/include/86box/vid_voodoo_codegen_arm64.h',
     '            addlong(ARM64_ROR_IMM(4, 4, 1));\n',
     '            addlong(ARM64_ROR_IMM(4, 4, 31)); /* KairoX86#288: right by 31, left by 1, as the C code turns it */\n'),
]

# KairoX86#290: DEPTH_TEST pasted its argument into each comparison unparenthesised, so the depth source
# zaColor (a conditional argument) turned the test into "zaColor's low 16 bits are not zero". Each
# comparison parenthesises it, so zaColor is compared against the depth buffer, as DOSBox-X does.
KAIROX86_VOODOO_DEPTH_SOURCE = [
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth < old_depth)) {',
     'if (!((comp_depth) < old_depth)) {'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth == old_depth)) {',
     'if (!((comp_depth) == old_depth)) {'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth <= old_depth)) {',
     'if (!((comp_depth) <= old_depth)) {'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth > old_depth)) {',
     'if (!((comp_depth) > old_depth)) {'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth != old_depth)) {',
     'if (!((comp_depth) != old_depth)) {'),
    ('86box/src/include/86box/vid_voodoo_render.h',
     'if (!(comp_depth >= old_depth)) {',
     'if (!((comp_depth) >= old_depth)) {'),
]

# KairoX86#291: the Voodoo Graphics/Voodoo2 display drew each line as the host's FIFO and render threads
# had got with it, so a line scanned while a triangle on it was half drawn showed part of it, and could
# stay so. Before it reads a line it settles the card that draws it (voodoo_settle, KairoX86#222), as the
# Banshee's display does: every write the guest queued before that point is in the line.
KAIROX86_VOODOO_DISPLAY_SETTLE = [
    ('86box/src/video/vid_voodoo_display.c',
     '#include <86box/vid_voodoo_display.h>\n',
     '#include <86box/vid_voodoo_display.h>\n#include <86box/vid_voodoo_fifo.h> /* KairoX86#291: voodoo_settle() */\n'),
    ('86box/src/video/vid_voodoo_display.c',
     '            if (draw_voodoo->dirty_line[draw_line]) {\n',
     '            /* KairoX86#291: the line with every write queued before it drawn */\n            voodoo_settle(draw_voodoo);\n            if (draw_voodoo->dirty_line[draw_line]) {\n'),
]

# KairoX86#233: the remaining core renderers' lines on the GPU: the S3's 2bpp (lowres and highres, one
# loop for both address forms), the Headland's 2bpp and Tseng's 4bpp (their 8-pixel groups' nibbles)
# as KAIRO_SCAN_BITS lines, and the ATI 28800's KSC5601 text as text cells. Each loop either draws its
# pixels or gathers what the GPU line needs; the CPU's drawing is the same as before.
KAIROX86_GPU_SCANOUT_REST = [
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_null(svga_t *svga)\n',
     "/* KairoX86#233: a line the renderer's loop reads byte by byte, `pixels` pixels of `bits` bits a pixel,\n   most significant first, through `colours` (KAIRO_SCAN_BITS), each drawn twice across when wide, to the\n   GPU when eligible (the installed renderer is the one asking): returns where its bytes go, in the order\n   the loop reads them (NULL: the CPU draws the line). The caller commits the queue. */\nstatic uint8_t *\nrender_gpu_bits(svga_t *svga, uint32_t *p, uint32_t bits, uint32_t pixels, bool wide, const uint32_t *colours, uint32_t n,\n                bool eligible)\n{\n    if (!kairo_gpu_on || !eligible || !svga->render_async || (pixels == 0) || (pixels > 4096))\n        return NULL;\n    const uint32_t words = (pixels * bits + 31) / 32;\n    uint32_t      *line  = render_gpu_line(svga, p, KAIRO_SCAN_BITS, pixels * (wide ? 2 : 1), words, colours, n, bits,\n                                           wide ? KAIRO_SCAN_WIDE : 0);\n    memset(line, 0, words * 4);\n    return (uint8_t *) line;\n}\n\nvoid\nsvga_render_null(svga_t *svga)\n"),
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_text_80_ksc5601(svga_t *svga)\n{\n    uint32_t *p;\n    int       xx;\n    int       drawcursor;\n    int       xinc;\n    uint8_t   chr;\n    uint8_t   attr;\n    uint8_t   dat;\n    uint8_t   nextchr;\n    uint32_t  charaddr;\n    uint32_t  fg;\n    uint32_t  bg;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->firstline_draw == 2000)\n        svga->firstline_draw = svga->displine;\n    svga->lastline_draw = svga->displine;\n\n    if (svga->fullchange) {\n        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n        xinc = (svga->seqregs[1] & 1) ? 8 : 9;\n\n        for (int x = 0; x < (svga->hdisp + svga->scrollcache); x += xinc) {\n            uint32_t addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;\n            drawcursor    = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);\n            chr           = svga->vram[addr];\n            nextchr       = svga->vram[addr + 8];\n            attr          = svga->vram[addr + 1];\n\n            if (drawcursor) {\n                bg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];\n                fg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];\n            } else {\n                fg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];\n                bg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];\n                if (attr & 0x80 && svga->attrregs[0x10] & 8) {\n                    bg = svga->pallook[svga->egapal[((attr >> 4) & 7) & svga->plane_mask] & svga->dac_mask];\n                    if (svga->blink & 16)\n                        fg = bg;\n                }\n            }\n\n            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {\n                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))\n                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline];\n                else if (nextchr & 0x80) {\n                    if (svga->ksc5601_swap_mode == 1 && (nextchr > 0xa0 && nextchr < 0xff)) {\n                        if (chr >= 0x80 && chr < 0x99)\n                            chr += 0x30;\n                        else if (chr >= 0xB0 && chr < 0xC9)\n                            chr -= 0x30;\n                    }\n                    dat = fontdatksc5601[((chr & 0x7F) << 7) | (nextchr & 0x7F)].chr[svga->scanline];\n                } else\n                    dat = 0xff;\n            } else {\n                if (attr & 8)\n                    charaddr = svga->charsetb + (chr * 128);\n                else\n                    charaddr = svga->charseta + (chr * 128);\n\n                if ((svga->ksc5601_english_font_type >> 8) == 1)\n                    dat = fontdatksc5601[((svga->ksc5601_english_font_type & 0x7F) << 7) | (chr >> 1)].chr[((chr & 1) << 4) | svga->scanline];\n                else\n                    dat = svga->vram[charaddr + (svga->scanline << 2)];\n            }\n\n            if (svga->seqregs[1] & 1) {\n                for (xx = 0; xx < 8; xx++)\n                    p[xx] = (dat & (0x80 >> xx)) ? fg : bg;\n            } else {\n                for (xx = 0; xx < 8; xx++)\n                    p[xx] = (dat & (0x80 >> xx)) ? fg : bg;\n                if (((chr & ~0x1f) != 0xc0) || !(svga->attrregs[0x10] & 4))\n                    p[8] = bg;\n                else\n                    p[8] = (dat & 1) ? fg : bg;\n            }\n            svga->memaddr += 4;\n            p += xinc;\n\n            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {\n                attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];\n\n                if (drawcursor) {\n                    bg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];\n                    fg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];\n                } else {\n                    fg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];\n                    bg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];\n                    if (attr & 0x80 && svga->attrregs[0x10] & 8) {\n                        bg = svga->pallook[svga->egapal[((attr >> 4) & 7) & svga->plane_mask] & svga->dac_mask];\n                        if (svga->blink & 16)\n                            fg = bg;\n                    }\n                }\n\n                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))\n                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline + 16];\n                else if (nextchr & 0x80)\n                    dat = fontdatksc5601[((chr & 0x7f) << 7) | (nextchr & 0x7F)].chr[svga->scanline + 16];\n                else\n                    dat = 0xff;\n\n                if (svga->seqregs[1] & 1) {\n                    for (xx = 0; xx < 8; xx++)\n                        p[xx] = (dat & (0x80 >> xx)) ? fg : bg;\n                } else {\n                    for (xx = 0; xx < 8; xx++)\n                        p[xx] = (dat & (0x80 >> xx)) ? fg : bg;\n                    if (((chr & ~0x1f) != 0xc0) || !(svga->attrregs[0x10] & 4))\n                        p[8] = bg;\n                    else\n                        p[8] = (dat & 1) ? fg : bg;\n                }\n\n                svga->memaddr += 4;\n                p += xinc;\n                x += xinc;\n            }\n        }\n        svga->memaddr &= svga->vram_display_mask;\n    }\n}\n\n',
     "/* KairoX86#233: one cell of a KSC5601 text line: its 8 dots (and the ninth, a line drawing character's\n   bit 0 where the attribute controller extends them, else the background) drawn at *p, or its word for\n   the GPU at *gpu */\nstatic void\nksc5601_cell(const svga_t *svga, uint32_t **p, uint32_t **gpu, int xinc, uint8_t chr, uint8_t dat, const uint32_t *colours,\n             uint32_t fi, uint32_t bi)\n{\n    const int ninth = (xinc == 9) && ((chr & ~0x1f) == 0xc0) && (svga->attrregs[0x10] & 4) && (dat & 1);\n\n    if (*gpu != NULL) {\n        *(*gpu)++ = dat | (fi << 8) | (bi << 16) | (ninth ? (1u << 24) : 0);\n        return;\n    }\n    for (int xx = 0; xx < 8; xx++)\n        (*p)[xx] = (dat & (0x80 >> xx)) ? colours[fi] : colours[bi];\n    if (xinc == 9)\n        (*p)[8] = ninth ? colours[fi] : colours[bi];\n    *p += xinc;\n}\n\n/* KairoX86#233: a text cell's colour indexes (the dot, the background), as the attribute gives them */\nstatic void\nksc5601_cell_colours(const svga_t *svga, uint8_t attr, int drawcursor, uint32_t *fi, uint32_t *bi)\n{\n    if (drawcursor) {\n        *bi = attr & 15;\n        *fi = attr >> 4;\n    } else {\n        *fi = attr & 15;\n        *bi = attr >> 4;\n        if (attr & 0x80 && svga->attrregs[0x10] & 8) {\n            *bi = (attr >> 4) & 7;\n            if (svga->blink & 16)\n                *fi = *bi;\n        }\n    }\n}\n\nvoid\nsvga_render_text_80_ksc5601(svga_t *svga)\n{\n    uint32_t *p;\n    int       drawcursor;\n    int       xinc;\n    uint8_t   chr;\n    uint8_t   attr;\n    uint8_t   dat;\n    uint8_t   nextchr;\n    uint32_t  charaddr;\n    uint32_t  fi;\n    uint32_t  bi;\n    uint32_t  colours[16];\n    uint32_t *gpu = NULL; /* KairoX86#233: the cells' words, when the GPU draws the line */\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->firstline_draw == 2000)\n        svga->firstline_draw = svga->displine;\n    svga->lastline_draw = svga->displine;\n\n    if (svga->fullchange) {\n        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n        xinc = (svga->seqregs[1] & 1) ? 8 : 9;\n        for (int i = 0; i < 16; i++)\n            colours[i] = svga->pallook[svga->egapal[i & svga->plane_mask] & svga->dac_mask];\n\n        /* KairoX86#233: one cell every xinc dots up to the line's end (a double-byte character's two\n           halves are two cells), each with its font byte and colours resolved here */\n        const int end = svga->hdisp + svga->scrollcache;\n        if (kairo_gpu_on && svga->render_async && (end > 0) && (svga->render == svga_render_text_80_ksc5601)) {\n            const uint32_t cells = (uint32_t) (end + xinc - 1) / (uint32_t) xinc;\n            gpu = render_gpu_line(svga, p, KAIRO_SCAN_TEXT, cells * (uint32_t) xinc, cells, colours, 16, (uint32_t) xinc, 0);\n        }\n\n        for (int x = 0; x < (svga->hdisp + svga->scrollcache); x += xinc) {\n            uint32_t addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;\n            drawcursor    = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);\n            chr           = svga->vram[addr];\n            nextchr       = svga->vram[addr + 8];\n            attr          = svga->vram[addr + 1];\n\n            ksc5601_cell_colours(svga, attr, drawcursor, &fi, &bi);\n\n            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {\n                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))\n                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline];\n                else if (nextchr & 0x80) {\n                    if (svga->ksc5601_swap_mode == 1 && (nextchr > 0xa0 && nextchr < 0xff)) {\n                        if (chr >= 0x80 && chr < 0x99)\n                            chr += 0x30;\n                        else if (chr >= 0xB0 && chr < 0xC9)\n                            chr -= 0x30;\n                    }\n                    dat = fontdatksc5601[((chr & 0x7F) << 7) | (nextchr & 0x7F)].chr[svga->scanline];\n                } else\n                    dat = 0xff;\n            } else {\n                if (attr & 8)\n                    charaddr = svga->charsetb + (chr * 128);\n                else\n                    charaddr = svga->charseta + (chr * 128);\n\n                if ((svga->ksc5601_english_font_type >> 8) == 1)\n                    dat = fontdatksc5601[((svga->ksc5601_english_font_type & 0x7F) << 7) | (chr >> 1)].chr[((chr & 1) << 4) | svga->scanline];\n                else\n                    dat = svga->vram[charaddr + (svga->scanline << 2)];\n            }\n\n            ksc5601_cell(svga, &p, &gpu, xinc, chr, dat, colours, fi, bi);\n            svga->memaddr += 4;\n\n            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {\n                attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];\n\n                ksc5601_cell_colours(svga, attr, drawcursor, &fi, &bi);\n\n                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))\n                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline + 16];\n                else if (nextchr & 0x80)\n                    dat = fontdatksc5601[((chr & 0x7f) << 7) | (nextchr & 0x7F)].chr[svga->scanline + 16];\n                else\n                    dat = 0xff;\n\n                ksc5601_cell(svga, &p, &gpu, xinc, chr, dat, colours, fi, bi);\n                svga->memaddr += 4;\n                x += xinc;\n            }\n        }\n        svga->memaddr &= svga->vram_display_mask;\n        if (gpu != NULL)\n            kairo_gpu_scan_commit();\n    }\n}\n\n"),
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_2bpp_s3_lowres(svga_t *svga)\n{\n    int       changed_offset;\n    int       x;\n    uint8_t   dat[2];\n    uint32_t  addr;\n    uint32_t *p;\n    uint32_t  changed_addr;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->force_old_addr) {\n        changed_offset = ((svga->memaddr << 1) + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;\n\n        if (svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 16) {\n                addr = svga->memaddr;\n\n                if (!(svga->crtc[0x17] & 0x40)) {\n                    addr = (addr << 1) & svga->vram_mask;\n                    addr &= ~7;\n\n                    if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))\n                        addr |= 4;\n\n                    if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))\n                        addr |= 4;\n                }\n\n                if (!(svga->crtc[0x17] & 0x01))\n                    addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);\n\n                if (!(svga->crtc[0x17] & 0x02))\n                    addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);\n\n                dat[0] = svga->vram[addr];\n                dat[1] = svga->vram[addr | 0x1];\n                if (svga->seqregs[1] & 4)\n                    svga->memaddr += 2;\n                else\n                    svga->memaddr += 4;\n                svga->memaddr &= svga->vram_mask;\n                p[0] = p[1] = svga->pallook[svga->egapal[(dat[0] >> 6) & 3] & svga->dac_mask];\n                p[2] = p[3] = svga->pallook[svga->egapal[(dat[0] >> 4) & 3] & svga->dac_mask];\n                p[4] = p[5] = svga->pallook[svga->egapal[(dat[0] >> 2) & 3] & svga->dac_mask];\n                p[6] = p[7] = svga->pallook[svga->egapal[dat[0] & 3] & svga->dac_mask];\n                p[8] = p[9] = svga->pallook[svga->egapal[(dat[1] >> 6) & 3] & svga->dac_mask];\n                p[10] = p[11] = svga->pallook[svga->egapal[(dat[1] >> 4) & 3] & svga->dac_mask];\n                p[12] = p[13] = svga->pallook[svga->egapal[(dat[1] >> 2) & 3] & svga->dac_mask];\n                p[14] = p[15] = svga->pallook[svga->egapal[dat[1] & 3] & svga->dac_mask];\n                p += 16;\n            }\n        }\n    } else {\n        changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 16) {\n                addr = svga->remap_func(svga, svga->memaddr);\n\n                dat[0] = svga->vram[addr];\n                dat[1] = svga->vram[addr | 0x1];\n                if (svga->seqregs[1] & 4)\n                    svga->memaddr += 2;\n                else\n                    svga->memaddr += 4;\n\n                svga->memaddr &= svga->vram_mask;\n\n                p[0] = p[1] = svga->pallook[svga->egapal[(dat[0] >> 6) & 3] & svga->dac_mask];\n                p[2] = p[3] = svga->pallook[svga->egapal[(dat[0] >> 4) & 3] & svga->dac_mask];\n                p[4] = p[5] = svga->pallook[svga->egapal[(dat[0] >> 2) & 3] & svga->dac_mask];\n                p[6] = p[7] = svga->pallook[svga->egapal[dat[0] & 3] & svga->dac_mask];\n                p[8] = p[9] = svga->pallook[svga->egapal[(dat[1] >> 6) & 3] & svga->dac_mask];\n                p[10] = p[11] = svga->pallook[svga->egapal[(dat[1] >> 4) & 3] & svga->dac_mask];\n                p[12] = p[13] = svga->pallook[svga->egapal[(dat[1] >> 2) & 3] & svga->dac_mask];\n                p[14] = p[15] = svga->pallook[svga->egapal[dat[1] & 3] & svga->dac_mask];\n\n                p += 16;\n            }\n        }\n    }\n}\n\nvoid\nsvga_render_2bpp_s3_highres(svga_t *svga)\n{\n    int       changed_offset;\n    int       x;\n    uint8_t   dat[2];\n    uint32_t  addr;\n    uint32_t *p;\n    uint32_t  changed_addr;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->force_old_addr) {\n        changed_offset = ((svga->memaddr << 1) + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;\n\n        if (svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                addr = svga->memaddr;\n\n                if (!(svga->crtc[0x17] & 0x40)) {\n                    addr = (addr << 1) & svga->vram_mask;\n                    addr &= ~7;\n\n                    if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))\n                        addr |= 4;\n\n                    if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))\n                        addr |= 4;\n                }\n\n                if (!(svga->crtc[0x17] & 0x01))\n                    addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);\n\n                if (!(svga->crtc[0x17] & 0x02))\n                    addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);\n\n                dat[0] = svga->vram[addr];\n                dat[1] = svga->vram[addr | 0x1];\n                if (svga->seqregs[1] & 4)\n                    svga->memaddr += 2;\n                else\n                    svga->memaddr += 4;\n                svga->memaddr &= svga->vram_mask;\n                p[0] = svga->pallook[svga->egapal[(dat[0] >> 6) & 3] & svga->dac_mask];\n                p[1] = svga->pallook[svga->egapal[(dat[0] >> 4) & 3] & svga->dac_mask];\n                p[2] = svga->pallook[svga->egapal[(dat[0] >> 2) & 3] & svga->dac_mask];\n                p[3] = svga->pallook[svga->egapal[dat[0] & 3] & svga->dac_mask];\n                p[4] = svga->pallook[svga->egapal[(dat[1] >> 6) & 3] & svga->dac_mask];\n                p[5] = svga->pallook[svga->egapal[(dat[1] >> 4) & 3] & svga->dac_mask];\n                p[6] = svga->pallook[svga->egapal[(dat[1] >> 2) & 3] & svga->dac_mask];\n                p[7] = svga->pallook[svga->egapal[dat[1] & 3] & svga->dac_mask];\n                p += 8;\n            }\n        }\n    } else {\n        changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                addr = svga->remap_func(svga, svga->memaddr);\n\n                dat[0] = svga->vram[addr];\n                dat[1] = svga->vram[addr | 0x1];\n                if (svga->seqregs[1] & 4)\n                    svga->memaddr += 2;\n                else\n                    svga->memaddr += 4;\n\n                svga->memaddr &= svga->vram_mask;\n\n                p[0] = svga->pallook[svga->egapal[(dat[0] >> 6) & 3] & svga->dac_mask];\n                p[1] = svga->pallook[svga->egapal[(dat[0] >> 4) & 3] & svga->dac_mask];\n                p[2] = svga->pallook[svga->egapal[(dat[0] >> 2) & 3] & svga->dac_mask];\n                p[3] = svga->pallook[svga->egapal[dat[0] & 3] & svga->dac_mask];\n                p[4] = svga->pallook[svga->egapal[(dat[1] >> 6) & 3] & svga->dac_mask];\n                p[5] = svga->pallook[svga->egapal[(dat[1] >> 4) & 3] & svga->dac_mask];\n                p[6] = svga->pallook[svga->egapal[(dat[1] >> 2) & 3] & svga->dac_mask];\n                p[7] = svga->pallook[svga->egapal[dat[1] & 3] & svga->dac_mask];\n\n                p += 8;\n            }\n        }\n    }\n}\n\n',
     "/* KairoX86#233: svga_render_2bpp_s3_lowres and _highres in one: the line's 2-bit pixels, two bytes each 8,\n   through the palette, each drawn twice across when wide; or, with the GPU on, the bytes to the GPU */\nstatic void\nrender_2bpp_s3(svga_t *svga, bool wide)\n{\n    uint32_t  colours[4];\n    bool      changed;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->force_old_addr) {\n        const int changed_offset = ((svga->memaddr << 1) + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;\n\n        changed = svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange;\n    } else {\n        const uint32_t changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        changed = svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange;\n    }\n    if (!changed)\n        return;\n\n    uint32_t *p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n    if (svga->firstline_draw == 2000)\n        svga->firstline_draw = svga->displine;\n    svga->lastline_draw = svga->displine;\n\n    for (int v = 0; v < 4; v++)\n        colours[v] = svga->pallook[svga->egapal[v] & svga->dac_mask];\n    const int step = wide ? 16 : 8;\n    const int end  = svga->hdisp + svga->scrollcache;\n    uint8_t  *gpu  = (end >= 0) ? render_gpu_bits(svga, p, 2, (uint32_t) (end / step + 1) * 8, wide, colours, 4,\n                                                  svga->render == (wide ? svga_render_2bpp_s3_lowres : svga_render_2bpp_s3_highres))\n                                : NULL;\n\n    for (int x = 0; x <= end; x += step) {\n        uint32_t addr;\n\n        if (svga->force_old_addr) {\n            addr = svga->memaddr;\n\n            if (!(svga->crtc[0x17] & 0x40)) {\n                addr = (addr << 1) & svga->vram_mask;\n                addr &= ~7;\n\n                if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))\n                    addr |= 4;\n\n                if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))\n                    addr |= 4;\n            }\n\n            if (!(svga->crtc[0x17] & 0x01))\n                addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);\n\n            if (!(svga->crtc[0x17] & 0x02))\n                addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);\n        } else\n            addr = svga->remap_func(svga, svga->memaddr);\n\n        const uint8_t dat[2] = { svga->vram[addr], svga->vram[addr | 0x1] };\n        if (svga->seqregs[1] & 4)\n            svga->memaddr += 2;\n        else\n            svga->memaddr += 4;\n        svga->memaddr &= svga->vram_mask;\n\n        if (gpu != NULL) {\n            *gpu++ = dat[0];\n            *gpu++ = dat[1];\n            continue;\n        }\n        for (int i = 0; i < 8; i++) {\n            const uint32_t c = colours[(dat[i >> 2] >> (6 - 2 * (i & 3))) & 3];\n\n            if (wide) {\n                p[0] = p[1] = c;\n                p += 2;\n            } else\n                *p++ = c;\n        }\n    }\n    if (gpu != NULL)\n        kairo_gpu_scan_commit();\n}\n\nvoid\nsvga_render_2bpp_s3_lowres(svga_t *svga)\n{\n    render_2bpp_s3(svga, true);\n}\n\nvoid\nsvga_render_2bpp_s3_highres(svga_t *svga)\n{\n    render_2bpp_s3(svga, false);\n}\n\n"),
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_2bpp_headland_highres(svga_t *svga)\n{\n    int       oddeven;\n    uint32_t  addr;\n    uint32_t *p;\n    uint8_t   edat[4];\n    uint8_t   dat;\n    uint32_t  changed_addr;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    changed_addr = svga->remap_func(svga, svga->memaddr);\n\n    if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n        if (svga->firstline_draw == 2000)\n            svga->firstline_draw = svga->displine;\n        svga->lastline_draw = svga->displine;\n\n        for (int x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n            addr    = svga->remap_func(svga, svga->memaddr);\n            oddeven = 0;\n\n            if (svga->seqregs[1] & 4) {\n                oddeven = (addr & 4) ? 1 : 0;\n                edat[0] = svga->vram[addr | oddeven];\n                edat[2] = svga->vram[addr | oddeven | 0x2];\n                edat[1] = edat[3] = 0;\n            } else {\n                *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);\n            }\n            svga->memaddr += 4;\n            svga->memaddr &= svga->vram_mask;\n\n            dat  = edatlookup[edat[0] >> 6][edat[1] >> 6] | (edatlookup[edat[2] >> 6][edat[3] >> 6] << 2);\n            p[0] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask] & svga->dac_mask];\n            p[1] = svga->pallook[svga->egapal[dat & svga->plane_mask] & svga->dac_mask];\n            dat  = edatlookup[(edat[0] >> 4) & 3][(edat[1] >> 4) & 3] | (edatlookup[(edat[2] >> 4) & 3][(edat[3] >> 4) & 3] << 2);\n            p[2] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask] & svga->dac_mask];\n            p[3] = svga->pallook[svga->egapal[dat & svga->plane_mask] & svga->dac_mask];\n            dat  = edatlookup[(edat[0] >> 2) & 3][(edat[1] >> 2) & 3] | (edatlookup[(edat[2] >> 2) & 3][(edat[3] >> 2) & 3] << 2);\n            p[4] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask] & svga->dac_mask];\n            p[5] = svga->pallook[svga->egapal[dat & svga->plane_mask] & svga->dac_mask];\n            dat  = edatlookup[edat[0] & 3][edat[1] & 3] | (edatlookup[edat[2] & 3][edat[3] & 3] << 2);\n            p[6] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask] & svga->dac_mask];\n            p[7] = svga->pallook[svga->egapal[dat & svga->plane_mask] & svga->dac_mask];\n\n            p += 8;\n        }\n    }\n}\n',
     "/* KairoX86#233: the 8 pixels of four plane bytes (edat), as the plane mask leaves them (the second of each\n   pair keeps the high nibble's bits a mask above 0x0f lets through): drawn at *p through the attribute\n   palette and the DAC's (its index masked with dac), or packed two a byte (the first in the high nibble)\n   at *gpu, which only takes lines whose mask is within 0x0f */\nstatic void\nrender_edat_pixels(const svga_t *svga, const uint8_t *edat, uint32_t dac, uint32_t **p, uint8_t **gpu)\n{\n    for (int i = 0; i < 4; i++) {\n        const int     s   = 6 - 2 * i;\n        const uint8_t dat = edatlookup[(edat[0] >> s) & 3][(edat[1] >> s) & 3] | (edatlookup[(edat[2] >> s) & 3][(edat[3] >> s) & 3] << 2);\n        const int     hi  = (dat >> 4) & svga->plane_mask;\n        const int     lo  = dat & svga->plane_mask;\n\n        if (*gpu != NULL)\n            *(*gpu)++ = (uint8_t) ((hi << 4) | (lo & 0x0f));\n        else {\n            (*p)[0] = svga->pallook[svga->egapal[hi] & dac];\n            (*p)[1] = svga->pallook[svga->egapal[lo] & dac];\n            *p += 2;\n        }\n    }\n}\n\nvoid\nsvga_render_2bpp_headland_highres(svga_t *svga)\n{\n    uint32_t  addr;\n    uint32_t *p;\n    uint8_t   edat[4];\n    uint32_t  changed_addr;\n    uint32_t  colours[16];\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    changed_addr = svga->remap_func(svga, svga->memaddr);\n\n    if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n        if (svga->firstline_draw == 2000)\n            svga->firstline_draw = svga->displine;\n        svga->lastline_draw = svga->displine;\n\n        for (int v = 0; v < 16; v++)\n            colours[v] = svga->pallook[svga->egapal[v] & svga->dac_mask];\n        const int end = svga->hdisp + svga->scrollcache;\n        /* KairoX86#233: each 8 pixels' nibbles to the GPU, when it draws the line (the plane mask within\n           4 bits: its pixels index the 16 colours) */\n        uint8_t *gpu = ((end >= 0) && !(svga->plane_mask & ~0x0f))\n                           ? render_gpu_bits(svga, p, 4, (uint32_t) (end / 8 + 1) * 8, false, colours, 16,\n                                             svga->render == svga_render_2bpp_headland_highres)\n                           : NULL;\n\n        for (int x = 0; x <= end; x += 8) {\n            addr = svga->remap_func(svga, svga->memaddr);\n\n            if (svga->seqregs[1] & 4) {\n                const int oddeven = (addr & 4) ? 1 : 0;\n                edat[0]           = svga->vram[addr | oddeven];\n                edat[2]           = svga->vram[addr | oddeven | 0x2];\n                edat[1] = edat[3] = 0;\n            } else {\n                *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);\n            }\n            svga->memaddr += 4;\n            svga->memaddr &= svga->vram_mask;\n\n            render_edat_pixels(svga, edat, svga->dac_mask, &p, &gpu);\n        }\n        if (gpu != NULL)\n            kairo_gpu_scan_commit();\n    }\n}\n"),
    ('86box/src/video/vid_svga_render.c',
     'void\nsvga_render_4bpp_tseng_highres(svga_t *svga)\n{\n    int       changed_offset;\n    int       x;\n    int       oddeven;\n    uint32_t  addr;\n    uint32_t *p;\n    uint8_t   edat[4];\n    uint8_t   dat;\n    uint32_t  changed_addr;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->force_old_addr) {\n        changed_offset = (svga->memaddr + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;\n\n        if (svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                addr    = svga->memaddr;\n                oddeven = 0;\n\n                if (!(svga->crtc[0x17] & 0x40)) {\n                    addr = (addr << 1) & svga->vram_mask;\n\n                    if (svga->seqregs[1] & 4)\n                        oddeven = (addr & 4) ? 1 : 0;\n\n                    addr &= ~7;\n\n                    if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))\n                        addr |= 4;\n                    if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))\n                        addr |= 4;\n                }\n\n                if (!(svga->crtc[0x17] & 0x01))\n                    addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);\n                if (!(svga->crtc[0x17] & 0x02))\n                    addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);\n\n                if (svga->seqregs[1] & 4) {\n                    edat[0] = svga->vram[addr | oddeven];\n                    edat[2] = svga->vram[addr | oddeven | 0x2];\n                    edat[1] = edat[3] = 0;\n                    svga->memaddr += 2;\n                } else {\n                    *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);\n                    svga->memaddr += 4;\n                }\n                svga->memaddr &= svga->vram_mask;\n\n                dat  = edatlookup[edat[0] >> 6][edat[1] >> 6] | (edatlookup[edat[2] >> 6][edat[3] >> 6] << 2);\n                p[0] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[1] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[(edat[0] >> 4) & 3][(edat[1] >> 4) & 3] | (edatlookup[(edat[2] >> 4) & 3][(edat[3] >> 4) & 3] << 2);\n                p[2] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[3] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[(edat[0] >> 2) & 3][(edat[1] >> 2) & 3] | (edatlookup[(edat[2] >> 2) & 3][(edat[3] >> 2) & 3] << 2);\n                p[4] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[5] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[edat[0] & 3][edat[1] & 3] | (edatlookup[edat[2] & 3][edat[3] & 3] << 2);\n                p[6] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[7] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n\n                p += 8;\n            }\n        }\n    } else {\n        changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {\n            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n            if (svga->firstline_draw == 2000)\n                svga->firstline_draw = svga->displine;\n            svga->lastline_draw = svga->displine;\n\n            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {\n                addr    = svga->remap_func(svga, svga->memaddr);\n                oddeven = 0;\n\n                if (svga->seqregs[1] & 4) {\n                    oddeven = (addr & 4) ? 1 : 0;\n                    edat[0] = svga->vram[addr | oddeven];\n                    edat[2] = svga->vram[addr | oddeven | 0x2];\n                    edat[1] = edat[3] = 0;\n                    svga->memaddr += 2;\n                } else {\n                    *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);\n                    svga->memaddr += 4;\n                }\n                svga->memaddr &= svga->vram_mask;\n\n                dat  = edatlookup[edat[0] >> 6][edat[1] >> 6] | (edatlookup[edat[2] >> 6][edat[3] >> 6] << 2);\n                p[0] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[1] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[(edat[0] >> 4) & 3][(edat[1] >> 4) & 3] | (edatlookup[(edat[2] >> 4) & 3][(edat[3] >> 4) & 3] << 2);\n                p[2] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[3] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[(edat[0] >> 2) & 3][(edat[1] >> 2) & 3] | (edatlookup[(edat[2] >> 2) & 3][(edat[3] >> 2) & 3] << 2);\n                p[4] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[5] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n                dat  = edatlookup[edat[0] & 3][edat[1] & 3] | (edatlookup[edat[2] & 3][edat[3] & 3] << 2);\n                p[6] = svga->pallook[svga->egapal[(dat >> 4) & svga->plane_mask]];\n                p[7] = svga->pallook[svga->egapal[dat & svga->plane_mask]];\n\n                p += 8;\n            }\n        }\n    }\n}\n\n',
     "void\nsvga_render_4bpp_tseng_highres(svga_t *svga)\n{\n    uint32_t  addr;\n    uint8_t   edat[4];\n    uint32_t  colours[16];\n    bool      changed;\n\n    if (((svga->displine + svga->y_add) < 0) ||\n        (svga->monitor->target_buffer == NULL) ||\n        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))\n        return;\n\n    if (svga->force_old_addr) {\n        const int changed_offset = (svga->memaddr + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;\n\n        changed = svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange;\n    } else {\n        const uint32_t changed_addr = svga->remap_func(svga, svga->memaddr);\n\n        changed = svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange;\n    }\n    if (!changed)\n        return;\n\n    uint32_t *p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];\n\n    if (svga->firstline_draw == 2000)\n        svga->firstline_draw = svga->displine;\n    svga->lastline_draw = svga->displine;\n\n    for (int v = 0; v < 16; v++)\n        colours[v] = svga->pallook[svga->egapal[v]];\n    const int end = svga->hdisp + svga->scrollcache;\n    /* KairoX86#233: each 8 pixels' nibbles to the GPU, when it draws the line (the plane mask within 4 bits) */\n    uint8_t *gpu = ((end >= 0) && !(svga->plane_mask & ~0x0f))\n                       ? render_gpu_bits(svga, p, 4, (uint32_t) (end / 8 + 1) * 8, false, colours, 16,\n                                         svga->render == svga_render_4bpp_tseng_highres)\n                       : NULL;\n\n    for (int x = 0; x <= end; x += 8) {\n        int oddeven = 0;\n\n        if (svga->force_old_addr) {\n            addr = svga->memaddr;\n\n            if (!(svga->crtc[0x17] & 0x40)) {\n                addr = (addr << 1) & svga->vram_mask;\n\n                if (svga->seqregs[1] & 4)\n                    oddeven = (addr & 4) ? 1 : 0;\n\n                addr &= ~7;\n\n                if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))\n                    addr |= 4;\n                if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))\n                    addr |= 4;\n            }\n\n            if (!(svga->crtc[0x17] & 0x01))\n                addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);\n            if (!(svga->crtc[0x17] & 0x02))\n                addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);\n        } else {\n            addr = svga->remap_func(svga, svga->memaddr);\n            if (svga->seqregs[1] & 4)\n                oddeven = (addr & 4) ? 1 : 0;\n        }\n\n        if (svga->seqregs[1] & 4) {\n            edat[0] = svga->vram[addr | oddeven];\n            edat[2] = svga->vram[addr | oddeven | 0x2];\n            edat[1] = edat[3] = 0;\n            svga->memaddr += 2;\n        } else {\n            *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);\n            svga->memaddr += 4;\n        }\n        svga->memaddr &= svga->vram_mask;\n\n        render_edat_pixels(svga, edat, 0xff, &p, &gpu);\n    }\n    if (gpu != NULL)\n        kairo_gpu_scan_commit();\n}\n\n"),
]

# KairoX86#292: a ViRGE triangle half starting below the hard clip rectangle skipped its clipped lines
# but moved the destination and depth rows up by one row only, drawing the rest of the half diff_y - 1
# rows low; they move by diff_y rows.
# KairoX86#293: the ViRGE's picture followed host timing (its 3D engine draws on render threads, its
# commands run on the FIFO thread). Before each line (render_sync) it waits for the FIFO to empty and
# the 3D engine to go idle, as the Voodoos' displays settle (KairoX86#222, #291); the reset's wait for
# the 3D engine is the same function.
KAIROX86_VIRGE_CLIP_AND_SETTLE = [
    ('86box/src/video/vid_s3_virge.c',
     '            state->y -= diff_y;\n            dest_offset -= s3d_tri->dest_str;\n            z_offset -= s3d_tri->z_str;\n',
     '            state->y -= diff_y;\n            /* KairoX86#292: the rows move with the lines skipped */\n            dest_offset -= s3d_tri->dest_str * diff_y;\n            z_offset -= s3d_tri->z_str * diff_y;\n'),
    ('86box/src/video/vid_s3_virge.c',
     'static uint8_t\ns3_virge_mmio_read(uint32_t addr, void *priv)\n{\n',
     '/* KairoX86#293: waits until the 3D engine has drawn every triangle queued to it */\nstatic void\ns3_virge_wait_3d_idle(virge_t *virge)\n{\n    while (s3d_engine_busy(virge)) {\n        thread_reset_event(virge->not_full_event);\n        wake_render_threads(virge);\n        if (s3d_engine_busy(virge))\n            thread_wait_event(virge->not_full_event, 1);\n    }\n}\n\n/* KairoX86#293: each line drawn with every write the guest queued before it applied */\nstatic void\ns3_virge_render_sync(svga_t *svga)\n{\n    virge_t *virge = (virge_t *) svga->priv;\n\n    s3_virge_wait_fifo_idle(virge);\n    s3_virge_wait_3d_idle(virge);\n}\n\nstatic uint8_t\ns3_virge_mmio_read(uint32_t addr, void *priv)\n{\n'),
    ('86box/src/video/vid_s3_virge.c',
     '        s3_virge_wait_fifo_idle(dev);\n        while (s3d_engine_busy(dev)) {\n            thread_reset_event(dev->not_full_event);\n            wake_render_threads(dev);\n            if (s3d_engine_busy(dev))\n                thread_wait_event(dev->not_full_event, 1);\n        }\n',
     '        s3_virge_wait_fifo_idle(dev);\n        s3_virge_wait_3d_idle(dev); /* KairoX86#293 */\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    virge->svga.hwcursor.cur_ysize = 64;\n    virge->svga.conv_16to32        = tvp3026_conv_16to32;\n',
     '    virge->svga.hwcursor.cur_ysize = 64;\n    virge->svga.conv_16to32        = tvp3026_conv_16to32;\n    virge->svga.render_sync        = s3_virge_render_sync; /* KairoX86#293 */\n'),
]

# KairoX86#272: the S3 ViRGE's triangles on the GPU (86box/kairo_gpu_virge.h, core/kairo/gpu_virge.c).
# With Hardware acceleration on, queue_triangle records each triangle (its setup as s3_virge_triangle
# and tri() start it, and the changed-page marks tri() makes line by line) instead of handing it to the
# render threads; the wait for the 3D engine draws the batch. The SVGA core gets a touch hook its memory
# handlers call before they read or write video memory (the bytes when the access is plain linear on a
# frame-buffer-only card, else all of it); the ViRGE draws its batch there where it draws on them, as at
# its 2D engine's start and at each line the display shows (its settle waits for the FIFO only).
KAIROX86_GPU_VIRGE = [
    ('86box/src/include/86box/vid_svga.h',
     '    void (*render_sync)(struct svga_t *svga);\n',
     "    void (*render_sync)(struct svga_t *svga);\n    /* KairoX86#272: before the processor reads or writes video memory, the card's GPU work there drawn\n       (addr and len: the bytes; NULL: no GPU work) */\n    void (*kairo_touch)(struct svga_t *svga, uint32_t addr, uint32_t len);\n"),
    ('86box/src/video/vid_svga.c',
     'static __inline void\nsvga_write_common(uint32_t addr, uint8_t val, uint8_t linear, void *priv)\n',
     "/* KairoX86#272: the card's GPU work drawn first where the processor reads or writes video memory: the\n   bytes when the access is plain linear (a frame-buffer-only card, no address translation), else all of it */\nstatic inline void\nsvga_kairo_touch(svga_t *svga, uint32_t addr, uint8_t linear, uint32_t len)\n{\n    if (svga->kairo_touch == NULL)\n        return;\n    if (linear && svga->fb_only && (svga->translate_address == NULL))\n        svga->kairo_touch(svga, addr & svga->decode_mask, len);\n    else\n        svga->kairo_touch(svga, 0, svga->vram_max);\n}\n\nstatic __inline void\nsvga_write_common(uint32_t addr, uint8_t val, uint8_t linear, void *priv)\n"),
    ('86box/src/video/vid_svga.c',
     'svga_write_common(uint32_t addr, uint8_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga       = (svga_t *) priv;\n',
     'svga_write_common(uint32_t addr, uint8_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga       = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 1); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_read_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t  *svga       = (svga_t *) priv;\n',
     'svga_read_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t  *svga       = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 1); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_writew_common(uint32_t addr, uint16_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n',
     'svga_writew_common(uint32_t addr, uint16_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 2); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_writel_common(uint32_t addr, uint32_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n',
     'svga_writel_common(uint32_t addr, uint32_t val, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 4); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_readw_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n',
     'svga_readw_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 2); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_svga.c',
     'svga_readl_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n',
     'svga_readl_common(uint32_t addr, uint8_t linear, void *priv)\n{\n    svga_t *svga = (svga_t *) priv;\n    svga_kairo_touch(svga, addr, linear, 4); /* KairoX86#272 */\n'),
    ('86box/src/video/vid_s3_virge.c',
     '#include <86box/vid_svga_render.h>\n',
     '#include <86box/vid_svga_render.h>\n#include <86box/kairo_gpu.h>       /* KairoX86#272 */\n#include <86box/kairo_gpu_virge.h>\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    ATOMIC_INT s3d_busy[S3D_RENDER_THREADS_MAX];\n',
     "    ATOMIC_INT s3d_busy[S3D_RENDER_THREADS_MAX];\n    /* KairoX86#272: its triangles' GPU state (kairo_gpu_virge.h), NULL in software */\n    void *k_gpu;\n"),
    ('86box/src/video/vid_s3_virge.c',
     '/* KairoX86#293: waits until the 3D engine has drawn every triangle queued to it */\nstatic void\ns3_virge_wait_3d_idle(virge_t *virge)\n{\n',
     '/* KairoX86#293: waits until the 3D engine has drawn every triangle queued to it */\nstatic void\ns3_virge_wait_3d_idle(virge_t *virge)\n{\n    /* KairoX86#272: on the GPU, the recorded triangles drawn */\n    if (virge->k_gpu != NULL) {\n        kairo_virge_gpu_drain(virge->k_gpu);\n        return;\n    }\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    virge_t *virge = (virge_t *) svga->priv;\n\n    s3_virge_wait_fifo_idle(virge);\n    s3_virge_wait_3d_idle(virge);\n}\n',
     "    virge_t *virge = (virge_t *) svga->priv;\n\n    s3_virge_wait_fifo_idle(virge);\n    /* KairoX86#272: on the GPU, what the line shows drawn (all of video memory when an overlay reads it\n       from elsewhere too) */\n    if (virge->k_gpu != NULL) {\n        if (svga->overlay_on)\n            kairo_virge_gpu_touch(virge->k_gpu, 0, virge->vram_mask + 1);\n        else\n            kairo_virge_gpu_touch(virge->k_gpu,\n                                  (svga->force_old_addr ? svga->memaddr : svga->remap_func(svga, svga->memaddr)) & svga->vram_display_mask,\n                                  (uint32_t) (svga->hdisp + svga->scrollcache + 64) * 4);\n        return;\n    }\n    s3_virge_wait_3d_idle(virge);\n}\n\n/* KairoX86#272: the processor's reads and writes of video memory (vid_svga.c's touch hook) */\nstatic void\ns3_virge_kairo_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const virge_t *virge = (virge_t *) svga->priv;\n\n    kairo_virge_gpu_touch(virge->k_gpu, addr, len);\n}\n"),
    ('86box/src/video/vid_s3_virge.c',
     's3_virge_bitblt(virge_t *virge, int count, uint32_t cpu_dat)\n{\n',
     's3_virge_bitblt(virge_t *virge, int count, uint32_t cpu_dat)\n{\n    /* KairoX86#272: the 2D engine works on memory the GPU may still draw on */\n    if (virge->k_gpu != NULL)\n        kairo_virge_gpu_drain(virge->k_gpu);\n'),
    ('86box/src/video/vid_s3_virge.c',
     'static void\nqueue_triangle(virge_t *virge)\n{\n',
     '/* KairoX86#272: s3_virge_triangle\'s setup of a triangle as the GPU kernel\'s record (kairo_gpu_virge.h), and\n   the bytes its texture reads; 0 for a triangle s3_virge_triangle draws nothing of */\nstatic int\ns3_virge_gpu_record(const s3d_t *s3d_tri, uint32_t *r, uint32_t *tex_start, uint32_t *tex_len)\n{\n    const uint32_t cmd     = s3d_tri->cmd_set;\n    const int      command = (cmd >> 27) & 0xf;\n    const int      max_d   = (cmd >> 8) & 15;\n\n    switch (command) {\n        case 0:\n        case 2:\n        case 6:\n            break;\n        case 1:\n        case 5:\n            if (((cmd >> 15) & 3) == 3)\n                return 0;\n            break;\n        default:\n            return 0;\n    }\n    if ((command != 0) && (max_d > 9))\n        fatal("ViRGE on the GPU: texture level %d\\n", max_d);\n    memset(r, 0, KV_WORDS * 4);\n    r[KV_CMD]       = cmd;\n    r[KV_CLIP_L]    = (uint32_t) s3d_tri->clip_l;\n    r[KV_CLIP_R]    = (uint32_t) s3d_tri->clip_r;\n    r[KV_CLIP_T]    = (uint32_t) s3d_tri->clip_t;\n    r[KV_CLIP_B]    = (uint32_t) s3d_tri->clip_b;\n    r[KV_DEST_BASE] = s3d_tri->dest_base;\n    r[KV_DEST_STR]  = s3d_tri->dest_str;\n    r[KV_Z_BASE]    = s3d_tri->z_base;\n    r[KV_Z_STR]     = s3d_tri->z_str;\n    uint32_t tex_base = s3d_tri->tex_base;\n    for (int c = 9; c >= 0; c--) {\n        r[KV_TEX_LEVEL + c] = tex_base;\n        if (c <= max_d)\n            tex_base += ((1 << (c * 2)) * tex_size[(cmd >> 5) & 7]) / 2;\n    }\n    *tex_start = s3d_tri->tex_base;\n    *tex_len   = (command != 0) ? (tex_base - s3d_tri->tex_base) : 0;\n    r[KV_TEX_BDR] = s3d_tri->tex_bdr_clr;\n    r[KV_TBU]     = s3d_tri->tbu << 11;\n    r[KV_TBV]     = s3d_tri->tbv << 11;\n    r[KV_FOG]     = s3d_tri->fog_b | (s3d_tri->fog_g << 8) | (s3d_tri->fog_r << 16);\n    r[KV_TYS]     = s3d_tri->tys;\n    r[KV_TY01]    = (uint32_t) s3d_tri->ty01;\n    r[KV_TY12]    = (uint32_t) s3d_tri->ty12;\n    r[KV_TLR]     = (uint32_t) s3d_tri->tlr;\n    r[KV_TXS]     = s3d_tri->txs;\n    r[KV_TXEND01] = s3d_tri->txend01;\n    r[KV_TXEND12] = s3d_tri->txend12;\n    r[KV_DX02]    = s3d_tri->TdXdY02;\n    r[KV_DX01]    = s3d_tri->TdXdY01;\n    r[KV_DX12]    = s3d_tri->TdXdY12;\n    const uint32_t start[9] = { s3d_tri->tus, s3d_tri->tvs, s3d_tri->tzs, s3d_tri->trs, s3d_tri->tgs, s3d_tri->tbs, s3d_tri->tas,\n                                s3d_tri->tds, s3d_tri->tws };\n    const int32_t  dx[9]    = { s3d_tri->TdUdX, s3d_tri->TdVdX, s3d_tri->TdZdX, s3d_tri->TdRdX, s3d_tri->TdGdX, s3d_tri->TdBdX,\n                                s3d_tri->TdAdX, s3d_tri->TdDdX, s3d_tri->TdWdX };\n    const int32_t  dy[9]    = { s3d_tri->TdUdY, s3d_tri->TdVdY, s3d_tri->TdZdY, s3d_tri->TdRdY, s3d_tri->TdGdY, s3d_tri->TdBdY,\n                                s3d_tri->TdAdY, s3d_tri->TdDdY, s3d_tri->TdWdY };\n    for (int i = 0; i < 9; i++) {\n        r[KV_START + i] = start[i];\n        r[KV_DX + i]    = (uint32_t) dx[i];\n        r[KV_DY + i]    = (uint32_t) dy[i];\n    }\n    return 1;\n}\n\n/* KairoX86#272: the changed-page marks tri() makes as it draws the triangle: each line it draws on, the\n   page its row starts in */\nstatic void\ns3_virge_gpu_mark_lines(virge_t *virge, const s3d_t *s3d_tri)\n{\n    const int x_dir = s3d_tri->tlr ? 1 : -1;\n    const int lines = s3d_tri->ty01 + s3d_tri->ty12;\n\n    for (int i = 0; i < lines; i++) {\n        const int y = (int) s3d_tri->tys - i;\n\n        if ((s3d_tri->cmd_set & CMD_SET_HC) && ((y < s3d_tri->clip_t) || (y > s3d_tri->clip_b)))\n            continue;\n        const int32_t x1 = (int32_t) (s3d_tri->txs + (uint32_t) i * s3d_tri->TdXdY02);\n        const int32_t x2 = (i < s3d_tri->ty01) ? (int32_t) (s3d_tri->txend01 + (uint32_t) i * s3d_tri->TdXdY01)\n                                               : (int32_t) (s3d_tri->txend12 + (uint32_t) (i - s3d_tri->ty01) * s3d_tri->TdXdY12);\n        int x  = (x1 + ((1 << 20) - 1)) >> 20;\n        int xe = (x2 + ((1 << 20) - 1)) >> 20;\n\n        if (x_dir < 0) {\n            x--;\n            xe--;\n        }\n        if (!((x != xe) && (((x_dir > 0) && (x < xe)) || ((x_dir < 0) && (x > xe)))))\n            continue;\n        if (s3d_tri->cmd_set & CMD_SET_HC) {\n            if ((x_dir > 0) && ((x > s3d_tri->clip_r) || (xe < s3d_tri->clip_l)))\n                continue;\n            if ((x_dir < 0) && ((x < s3d_tri->clip_l) || (xe > s3d_tri->clip_r)))\n                continue;\n        }\n        virge->svga.changedvram[((s3d_tri->dest_base + (uint32_t) y * s3d_tri->dest_str) & virge->vram_mask) >> 12] = changeframecount;\n    }\n}\n\nstatic void\nqueue_triangle(virge_t *virge)\n{\n    /* KairoX86#272: on the GPU, recorded for its kernel */\n    if (virge->k_gpu != NULL) {\n        uint32_t record[KV_WORDS];\n        uint32_t tex_start;\n        uint32_t tex_len;\n\n        if (s3_virge_gpu_record(&virge->s3d_tri, record, &tex_start, &tex_len)) {\n            const uint32_t flags = (virge->bilinear_enabled ? KAIRO_VIRGE_BILINEAR : 0) | (virge->dithering_enabled ? KAIRO_VIRGE_DITHER : 0)\n                                   | (((virge->chip == S3_VIRGEDX) || (virge->chip >= S3_VIRGEGX2)) ? KAIRO_VIRGE_PERSP_375 : 0);\n\n            s3_virge_gpu_mark_lines(virge, &virge->s3d_tri);\n            kairo_virge_gpu_queue(virge->k_gpu, record, flags, tex_start, tex_len);\n            virge->tri_count++;\n        }\n        return;\n    }\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    virge->svga.render_sync        = s3_virge_render_sync; /* KairoX86#293 */\n',
     '    virge->svga.render_sync        = s3_virge_render_sync; /* KairoX86#293 */\n    if (kairo_gpu_on) { /* KairoX86#272 */\n        virge->k_gpu            = kairo_virge_gpu_open(virge->svga.vram, (virge->memory_size << 20) - 1);\n        virge->svga.kairo_touch = s3_virge_kairo_touch;\n    }\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    for (int lane = 0; lane < virge->render_threads; lane++)\n        thread_destroy_event(virge->wake_render_thread[lane]);\n\n    svga_close(&virge->svga);\n',
     '    for (int lane = 0; lane < virge->render_threads; lane++)\n        thread_destroy_event(virge->wake_render_thread[lane]);\n\n    kairo_virge_gpu_close(virge->k_gpu); /* KairoX86#272 */\n    svga_close(&virge->svga);\n'),
]

# KairoX86#237: the display's GPU touches shared by every card with GPU work in its video memory (svga->kairo_touch):
# before a line is drawn, its memory from the start address; before the overlay, all of it (it reads from elsewhere
# too); before either cursor, a whole cursor's from its address. The ViRGE's own line touch (KairoX86#272) goes.
KAIROX86_GPU_DISPLAY_TOUCH = [
    ('86box/src/video/vid_svga.c',
     '}\n\nstatic void\nsvga_do_render(svga_t *svga)\n',
     "}\n\n/* KairoX86#237: the card's GPU work drawn first where the display reads video memory (svga->kairo_touch): the\n   line's from its start address, all of it for the overlay (it reads from elsewhere too), a whole cursor's from the\n   cursor's address (64 by 64 at 32 bits holds any card's) */\nstatic void\nsvga_kairo_touch_line(svga_t *svga)\n{\n    if (svga->kairo_touch != NULL)\n        svga->kairo_touch(svga, (svga->force_old_addr ? svga->memaddr : svga->remap_func(svga, svga->memaddr)) & svga->vram_display_mask,\n                          (uint32_t) (svga->hdisp + svga->scrollcache + 64) * 4);\n}\n\nstatic void\nsvga_kairo_touch_all(svga_t *svga)\n{\n    if (svga->kairo_touch != NULL)\n        svga->kairo_touch(svga, 0, svga->vram_max);\n}\n\nstatic void\nsvga_kairo_touch_cursor(svga_t *svga, uint32_t addr)\n{\n    if (svga->kairo_touch != NULL)\n        svga->kairo_touch(svga, addr & svga->vram_mask, 64 * 64 * 4);\n}\n\nstatic void\nsvga_do_render(svga_t *svga)\n"),
    ('86box/src/video/vid_svga.c',
     '            svga->render_sync(svga);\n        /* A line the cursors or the overlay draw on next is drawn in place */\n',
     '            svga->render_sync(svga);\n        svga_kairo_touch_line(svga); /* KairoX86#237 */\n        /* A line the cursors or the overlay draw on next is drawn in place */\n'),
    ('86box/src/video/vid_svga.c',
     '    if (svga->overlay_on) {\n        if (!svga->override && svga->overlay_draw)\n            svga->overlay_draw(svga, svga->displine + svga->y_add);\n        svga->overlay_on--;\n',
     '    if (svga->overlay_on) {\n        if (!svga->override && svga->overlay_draw) {\n            svga_kairo_touch_all(svga); /* KairoX86#237 */\n            svga->overlay_draw(svga, svga->displine + svga->y_add);\n        }\n        svga->overlay_on--;\n'),
    ('86box/src/video/vid_svga.c',
     '    if (svga->dac_hwcursor_on) {\n        if (!svga->override && svga->dac_hwcursor_draw)\n            svga->dac_hwcursor_draw(svga, (svga->displine + svga->y_add + ((svga->dac_hwcursor_latch.y >= 0) ? 0 : svga->dac_hwcursor_latch.y)) & 2047);\n        svga->dac_hwcursor_on--;\n',
     '    if (svga->dac_hwcursor_on) {\n        if (!svga->override && svga->dac_hwcursor_draw) {\n            svga_kairo_touch_cursor(svga, svga->dac_hwcursor_latch.addr); /* KairoX86#237 */\n            svga->dac_hwcursor_draw(svga, (svga->displine + svga->y_add + ((svga->dac_hwcursor_latch.y >= 0) ? 0 : svga->dac_hwcursor_latch.y)) & 2047);\n        }\n        svga->dac_hwcursor_on--;\n'),
    ('86box/src/video/vid_svga.c',
     '    if (svga->hwcursor_on) {\n        if (!svga->override && svga->hwcursor_draw)\n            svga->hwcursor_draw(svga, (svga->displine + svga->y_add + ((svga->hwcursor_latch.y >= 0) ? 0 : svga->hwcursor_latch.y)) & 2047);\n\n',
     '    if (svga->hwcursor_on) {\n        if (!svga->override && svga->hwcursor_draw) {\n            svga_kairo_touch_cursor(svga, svga->hwcursor_latch.addr); /* KairoX86#237 */\n            svga->hwcursor_draw(svga, (svga->displine + svga->y_add + ((svga->hwcursor_latch.y >= 0) ? 0 : svga->hwcursor_latch.y)) & 2047);\n        }\n\n'),
    ('86box/src/video/vid_s3_virge.c',
     '    s3_virge_wait_fifo_idle(virge);\n    /* KairoX86#272: on the GPU, what the line shows drawn (all of video memory when an overlay reads it\n       from elsewhere too) */\n    if (virge->k_gpu != NULL) {\n        if (svga->overlay_on)\n            kairo_virge_gpu_touch(virge->k_gpu, 0, virge->vram_mask + 1);\n        else\n            kairo_virge_gpu_touch(virge->k_gpu,\n                                  (svga->force_old_addr ? svga->memaddr : svga->remap_func(svga, svga->memaddr)) & svga->vram_display_mask,\n                                  (uint32_t) (svga->hdisp + svga->scrollcache + 64) * 4);\n        return;\n    }\n    s3_virge_wait_3d_idle(virge);\n',
     "    s3_virge_wait_fifo_idle(virge);\n    /* KairoX86#272: on the GPU, what the line, the overlay and the cursor show is drawn by the display's touches\n       (vid_svga.c, KairoX86#237) */\n    if (virge->k_gpu != NULL)\n        return;\n    s3_virge_wait_3d_idle(virge);\n"),
]

# KairoX86#237: the ATI 3D Rage II+'s 3D engine on the GPU (86box/kairo_gpu_mach64.h, core/kairo/gpu_mach64.c,
# core/kairo/shaders/mach64.comp). With the machine's Hardware acceleration on, mach64_3d_draw_rows records the rows
# a trapezoid or a 3D line has walked, with what their pixels read (the job, the registers and the palettes as they
# are), instead of drawing them; the GPU draws them where anything else meets the video memory they draw on or read:
# the processor (the linear aperture's handlers, the SVGA core's through svga->kairo_touch), the display (vid_svga.c
# touches each line's memory before it is drawn, the overlay's and the cursor's, shared with the ViRGE), the 2D engine
# (at each operation's start, its host data and the context load). Each recorded row marks the pages it may write
# changed, as the CPU's pixels mark theirs, so the display draws those lines again. A 3D line's pixels are rows of
# one, drawn by mach64_3d_draw_row as a trapezoid's are (its Z buffer bound kept), so the CPU and the GPU draw lines
# and trapezoids alike. The front-end scaler is split into its setup, a pixel, and on the GPU its destination lines
# recorded as rows of a scaled rectangle's record.
KAIROX86_GPU_MACH64 = [
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xff;\n\n',
     '        return 0xff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xffff;\n\n',
     '        return 0xffff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xffffffff;\n\n',
     '        return 0xffffffff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 4); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '    addr &= svga->vram_mask;\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n',
     '    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return;\n    addr &= svga->vram_mask;\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n    *(uint16_t *) &svga->vram[addr] = val;\n',
     '        return;\n    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n    *(uint16_t *) &svga->vram[addr] = val;\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '            offset_from_base <<= 1;\n            svga->vram[offset_from_base & svga->vram_mask] = (val & 0xFF);\n',
     '            offset_from_base <<= 1;\n            mach64_3d_kairo_touch(mach64, offset_from_base, 6); /* KairoX86#237 */\n            svga->vram[offset_from_base & svga->vram_mask] = (val & 0xFF);\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '            offset_from_base <<= 2;\n            if (((mach64->scaler_yuv_aper >> 4) & 0xc) == 0x8) { // U plane\n',
     '            offset_from_base <<= 2;\n            mach64_3d_kairo_touch(mach64, offset_from_base, 16); /* KairoX86#237 */\n            if (((mach64->scaler_yuv_aper >> 4) & 0xc) == 0x8) { // U plane\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return;\n    addr &= svga->vram_mask;\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n    *(uint32_t *) &svga->vram[addr] = val;\n',
     '        return;\n    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch(mach64, addr, 4); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n    *(uint32_t *) &svga->vram[addr] = val;\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '#include "vid_ati_mach64.h"\n\n',
     '#include "vid_ati_mach64.h"\n#include <86box/kairo_gpu.h>        /* KairoX86#237 */\n#include <86box/kairo_gpu_mach64.h>\n\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    uint64_t                    spin_ticks;\n};\n',
     "    uint64_t                    spin_ticks;\n\n    /* KairoX86#237: the rows' GPU state (kairo_gpu_mach64.h), NULL in software */\n    void *k_gpu;\n};\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    int                dp_constant;\n    int                nrows;\n',
     "    int                dp_constant;\n    int                line; /* a 3D line's pixels, each a row: one outside the Z buffer is not drawn */\n    int                nrows;\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '        if (draw && px->z_enabled) {\n            depth = mach64_3d_s16_12_depth(z);\n            draw  = mach64_3d_z_test(depth, mach64_3d_vram_read16(mach64, z_addr), (px->z_cntl >> Z_TEST_SHIFT) & 7);\n        }\n',
     '        if (draw && px->z_enabled) {\n            if (job->line && ((x < 0) || (x >= job->z_pitch) || (y < 0)))\n                draw = 0;\n            else {\n                depth = mach64_3d_s16_12_depth(z);\n                draw  = mach64_3d_z_test(depth, mach64_3d_vram_read16(mach64, z_addr), (px->z_cntl >> Z_TEST_SHIFT) & 7);\n            }\n        }\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     ' */\nstatic void\nmach64_3d_draw_rows(mach64_3d_t *ctx, const mach64_3d_rows_job_t *job, uint32_t pixels)\n{\n    mach64_3d_dither_t own;\n    int                threads = ctx->threads;\n\n',
     " */\n/* KairoX86#237: every page of len bytes at addr marked changed (mach64_3d_vram_changed's mark), wrapping as video\n   memory does */\nstatic void\nmach64_3d_mark_changed(const mach64_t *mach64, uint32_t addr, uint32_t len)\n{\n    const uint8_t stamp = mach64->svga.monitor->mon_changeframecount;\n\n    if (len == 0)\n        return;\n    if (len > mach64->vram_mask)\n        len = mach64->vram_mask + 1;\n    for (uint64_t page = addr >> 12; page <= (((uint64_t) addr + len - 1) >> 12); page++)\n        mach64->svga.changedvram[(((uint32_t) page << 12) & mach64->vram_mask) >> 12] = stamp;\n}\n\n/* KairoX86#237: the rows walked so far recorded for the GPU (kairo_gpu_mach64.h), with what their pixels read\n   from the job, the registers and the palettes as they are now */\nstatic void\nmach64_3d_gpu_rows(mach64_3d_t *ctx, const mach64_3d_rows_job_t *job)\n{\n    const mach64_t          *mach64 = ctx->mach64;\n    const mach64_3d_pixel_t *px     = &job->px;\n    const mach64_3d_interp_t *p     = &job->p;\n    uint32_t                 record[KM_WORDS] = { 0 };\n    uint32_t                 palettes[KAIRO_M64_PALETTE_WORDS];\n    uint32_t                 rows[MACH64_3D_ROWS * KR_WORDS];\n\n    record[KM_FLAGS] = (px->textured ? KAIRO_M64_TEXTURED : 0) | (px->z_enabled ? KAIRO_M64_Z_ENABLED : 0) |\n                       (px->z_write ? KAIRO_M64_Z_WRITE : 0) | (px->dst_compare ? KAIRO_M64_DST_COMPARE : 0) |\n                       (job->dp_constant ? KAIRO_M64_DP_CONSTANT : 0) | (job->line ? KAIRO_M64_LINE : 0) |\n                       ((job->lead_dir < 0) ? KAIRO_M64_LEAD_LEFT : 0) | ((uint32_t) px->alpha_fog << 8);\n    record[KM_CNTL]         = px->cntl;\n    record[KM_Z_CNTL]       = px->z_cntl;\n    record[KM_DST_BASE]     = job->dst.base;\n    record[KM_DST_PITCH]    = (uint32_t) job->dst.pitch;\n    record[KM_DST_FORMAT]   = (uint32_t) job->dst.format;\n    record[KM_DST_BPP]      = (uint32_t) job->dst.bpp;\n    record[KM_Z_BASE]       = job->z_base;\n    record[KM_Z_PITCH]      = (uint32_t) job->z_pitch;\n    record[KM_FOG]          = mach64->dp_frgd_clr;\n    record[KM_CLR_CMP_CNTL] = mach64->clr_cmp_cntl;\n    record[KM_CLR_CMP_CLR]  = mach64->clr_cmp_clr;\n    record[KM_CLR_CMP_MASK] = mach64->clr_cmp_mask;\n    record[KM_WRITE_MASK]   = mach64->write_mask;\n    record[KM_DP_SRC]       = mach64->dp_src;\n    record[KM_DP_BKGD_CLR]  = mach64->dp_bkgd_clr;\n    record[KM_DP_FRGD_CLR]  = mach64->dp_frgd_clr;\n    record[KM_DP_PIX_WIDTH] = mach64->dp_pix_width;\n    record[KM_RX]           = (uint32_t) p->rx;\n    record[KM_RX + 1]       = (uint32_t) p->gx;\n    record[KM_RX + 2]       = (uint32_t) p->bx;\n    record[KM_RX + 3]       = (uint32_t) p->ax;\n    record[KM_RX + 4]       = (uint32_t) p->zx;\n    record[KM_SX2]          = (uint32_t) p->sx2;\n    record[KM_SX2 + 1]      = (uint32_t) p->tx2;\n    record[KM_SX2 + 2]      = (uint32_t) p->sxy2;\n    record[KM_SX2 + 3]      = (uint32_t) p->txy2;\n    if (px->textured) {\n        const mach64_3d_texture_t *largest = &px->texture[0];\n        const int                  levels  = (px->cntl & MIP_MAP_DISABLE) ? 1 : (largest->max_lod + 1);\n\n        record[KM_TEX_FORMAT]  = (uint32_t) largest->format;\n        record[KM_TEX_BPP]     = (uint32_t) largest->bpp;\n        record[KM_TEX_DYNAMIC] = (uint32_t) largest->dynamic_range;\n        record[KM_KEY_FCN]     = largest->key_fcn;\n        record[KM_KEY]         = largest->key;\n        record[KM_KEY_MASK]    = largest->key_mask;\n        record[KM_MAX_LOD]     = (uint32_t) largest->max_lod;\n        record[KM_LEVELS]      = (uint32_t) levels;\n        for (int level = 0; level < levels; level++) {\n            const mach64_3d_texture_t *map = &px->texture[level];\n            uint32_t                  *out = &record[KM_MAPS + level * KM_MAP_WORDS];\n\n            out[KM_MAP_BASE]        = map->base;\n            out[KM_MAP_PITCH_LOG2]  = (uint32_t) map->pitch_log2;\n            out[KM_MAP_WIDTH_MASK]  = (uint32_t) map->width_mask;\n            out[KM_MAP_HEIGHT_MASK] = (uint32_t) map->height_mask;\n            out[KM_MAP_COORD_SHIFT] = (uint32_t) map->coord_shift;\n            out[KM_MAP_HEIGHT_LOG2] = (uint32_t) map->height_log2;\n        }\n    }\n\n    memcpy(palettes, ctx->texture_palette, 256 * 4);\n    memcpy(palettes + 256, mach64->svga.pallook, 256 * 4);\n\n    for (int i = 0; i < job->nrows; i++) {\n        const mach64_3d_row_t *row = &ctx->rows[i];\n        uint32_t              *out = &rows[i * KR_WORDS];\n        const int64_t          st[6] = { row->s, row->sxi, row->syi, row->t, row->txi, row->tyi };\n        const uint32_t         n     = (uint32_t) (row->end - row->first);\n\n        /* The pages it may write changed now, as the CPU's pixels mark theirs, so the display draws its lines again */\n        mach64_3d_mark_changed(mach64, job->dst.base + (row->y * job->dst.pitch + row->first) * job->dst.bpp, n * job->dst.bpp);\n        if (px->z_write)\n            mach64_3d_mark_changed(mach64, job->z_base + (row->y * job->z_pitch + row->first) * 2, n * 2);\n\n        out[KR_Y]     = (uint32_t) row->y;\n        out[KR_FIRST] = (uint32_t) row->first;\n        out[KR_END]   = (uint32_t) row->end;\n        out[KR_LEAD]  = (uint32_t) row->lead;\n        out[KR_DRAW]  = 0;\n        out[KR_R]     = (uint32_t) row->r;\n        out[KR_R + 1] = (uint32_t) row->g;\n        out[KR_R + 2] = (uint32_t) row->b;\n        out[KR_R + 3] = (uint32_t) row->a;\n        out[KR_R + 4] = (uint32_t) row->z;\n        for (int k = 0; k < 6; k++) {\n            out[KR_S + k * 2]     = (uint32_t) (uint64_t) st[k];\n            out[KR_S + k * 2 + 1] = (uint32_t) ((uint64_t) st[k] >> 32);\n        }\n    }\n    kairo_mach64_gpu_draw(ctx->k_gpu, record, palettes, rows, job->nrows);\n}\n\n/* KairoX86#237: what the GPU draws on or reads, drawn before the processor, the display or another engine\n   reads or writes len bytes at addr */\nvoid\nmach64_3d_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len)\n{\n    if ((mach64->gt3d != NULL) && (mach64->gt3d->k_gpu != NULL))\n        kairo_mach64_gpu_touch(mach64->gt3d->k_gpu, addr & mach64->vram_mask, len);\n}\n\n/* The SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\nmach64_3d_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, len);\n}\n\nvoid\nmach64_3d_kairo_drain(mach64_t *mach64)\n{\n    if ((mach64->gt3d != NULL) && (mach64->gt3d->k_gpu != NULL))\n        kairo_mach64_gpu_drain(mach64->gt3d->k_gpu);\n}\n\nstatic void\nmach64_3d_draw_rows(mach64_3d_t *ctx, const mach64_3d_rows_job_t *job, uint32_t pixels)\n{\n    mach64_3d_dither_t own;\n    int                threads = ctx->threads;\n\n    if (ctx->k_gpu != NULL) {\n        mach64_3d_gpu_rows(ctx, job);\n        return;\n    }\n\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    job.lead_dir = lead_dir;\n    mach64_3d_pixel_init(ctx, &job.dst, job.z_pitch, &job.px);\n',
     '    job.lead_dir = lead_dir;\n    job.line     = 0;\n    mach64_3d_pixel_init(ctx, &job.dst, job.z_pitch, &job.px);\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    uint32_t           z_off_pitch;\n    uint32_t           z_base;\n    int                z_pitch;\n    mach64_3d_dst_t    dst;\n    mach64_3d_pixel_t  px;\n    mach64_3d_interp_t p;\n\n',
     '    uint32_t           z_off_pitch;\n    uint32_t           batch = 0;\n    mach64_3d_rows_job_t job;\n    mach64_3d_interp_t  *p = &job.p;\n\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '        return;\n    if (!mach64_3d_dst_init(mach64, &dst))\n        return;\n\n    z_off_pitch = ctx->regs[Z_OFF_PITCH >> 2];\n    z_base      = (z_off_pitch & 0xfffff) << 3;\n    z_pitch     = ((z_off_pitch >> 22) & 0x3ff) << 3;\n    mach64_3d_pixel_init(ctx, &dst, z_pitch, &px);\n    mach64_3d_interp_load(ctx, &p);\n\n    for (int i = 0; i < len; i++) {\n        /* DST_LAST_PEL draws the last pixel. */\n        int draw = ((i < (len - 1)) || (mach64->dst_cntl & DST_LAST_PEL)) && (x >= dst.left) && (x <= dst.right) && (y >= dst.top) && (y <= dst.bottom);\n\n        if (draw) {\n            uint32_t addr   = dst.base + (y * dst.pitch + x) * dst.bpp;\n            uint32_t z_addr = 0;\n            uint16_t depth  = 0;\n            rgba_t   shade  = { mach64_3d_s8_12_color(p.r), mach64_3d_s8_12_color(p.g), mach64_3d_s8_12_color(p.b),\n                                mach64_3d_s8_12_color(p.a) };\n            rgba_t   src;\n\n            draw = mach64_3d_pixel_source(ctx, &px, shade, p.s, p.t, p.sxi, p.txi, p.syi, p.tyi, &src);\n            if (draw && px.z_enabled) {\n                if ((x < 0) || (x >= z_pitch) || (y < 0))\n                    draw = 0;\n                else {\n                    z_addr = z_base + (y * z_pitch + x) * 2;\n                    depth  = mach64_3d_s16_12_depth(p.z);\n                    draw   = mach64_3d_z_test(depth, mach64_3d_vram_read16(mach64, z_addr), (px.z_cntl >> Z_TEST_SHIFT) & 7);\n                }\n            }\n            if (draw) {\n                if (px.alpha_fog == ALPHA_FOG_BLEND)\n                    src = mach64_3d_blend(px.cntl, src, mach64_3d_read_dst(ctx, addr, dst.format));\n                if (px.dst_compare &&\n                    mach64_3d_destination_compare_inhibits(mach64->clr_cmp_cntl, mach64->clr_cmp_clr, mach64->clr_cmp_mask,\n                                                           mach64_3d_vram_read(mach64, addr, dst.bpp), px.dst_compare_mask))\n                    draw = 0;\n            }\n            if (draw) {\n                mach64_3d_write_dst(ctx, &ctx->dither, addr, dst.format, src, x, y);\n                if (px.z_write)\n                    mach64_3d_vram_write(mach64, z_addr, depth, 2);\n            }\n',
     "        return;\n    if (!mach64_3d_dst_init(mach64, &job.dst))\n        return;\n\n    /* Each pixel drawn is a row of one, its own leading edge, so its texture steps are the\n       registers' X and Y ones (KairoX86#237: drawn as a trapezoid's rows are). */\n    z_off_pitch     = ctx->regs[Z_OFF_PITCH >> 2];\n    job.z_base      = (z_off_pitch & 0xfffff) << 3;\n    job.z_pitch     = ((z_off_pitch >> 22) & 0x3ff) << 3;\n    job.nrows       = 0;\n    job.lead_dir    = 1;\n    job.line        = 1;\n    job.dp_constant = 0;\n    mach64_3d_pixel_init(ctx, &job.dst, job.z_pitch, &job.px);\n    mach64_3d_interp_load(ctx, p);\n\n    for (int i = 0; i < len; i++) {\n        /* DST_LAST_PEL draws the last pixel. */\n        if (((i < (len - 1)) || (mach64->dst_cntl & DST_LAST_PEL)) && (x >= job.dst.left) && (x <= job.dst.right) &&\n            (y >= job.dst.top) && (y <= job.dst.bottom)) {\n            mach64_3d_row_t *row = &ctx->rows[job.nrows++];\n\n            row->y     = y;\n            row->lead  = x;\n            row->first = x;\n            row->end   = x + 1;\n            row->r     = p->r;\n            row->g     = p->g;\n            row->b     = p->b;\n            row->a     = p->a;\n            row->z     = p->z;\n            row->s     = p->s;\n            row->sxi   = p->sxi;\n            row->syi   = p->syi;\n            row->t     = p->t;\n            row->txi   = p->txi;\n            row->tyi   = p->tyi;\n            batch++;\n            if (job.nrows == MACH64_3D_ROWS) {\n                mach64_3d_draw_rows(ctx, &job, batch);\n                job.nrows = 0;\n                batch     = 0;\n            }\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '            y += y_dir;\n            mach64_3d_interp_step_y(&p);\n        } else {\n            x += x_dir;\n            mach64_3d_interp_step_x(&p);\n        }\n',
     '            y += y_dir;\n            mach64_3d_interp_step_y(p);\n        } else {\n            x += x_dir;\n            mach64_3d_interp_step_x(p);\n        }\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '                x += x_dir;\n                mach64_3d_interp_step_x(&p);\n            } else {\n                y += y_dir;\n                mach64_3d_interp_step_y(&p);\n            }\n        }\n    }\n\n',
     '                x += x_dir;\n                mach64_3d_interp_step_x(p);\n            } else {\n                y += y_dir;\n                mach64_3d_interp_step_y(p);\n            }\n        }\n    }\n    if (job.nrows)\n        mach64_3d_draw_rows(ctx, &job, batch);\n\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     ' */\nstatic void\nmach64_scaler_draw(mach64_3d_t *ctx)\n{\n    mach64_t       *mach64     = ctx->mach64;\n    const uint32_t *regs       = ctx->regs;\n    int             replicate  = !!(regs[SCALE_3D_CNTL >> 2] & SCALE_PIX_REP);\n    uint32_t        src_base   = regs[SCALE_Y_OFF >> 2] & ~7;\n    int             src_width  = regs[SCALE_WIDTH >> 2] & 0x1fff;\n    int             src_height = regs[SCALE_HEIGHT >> 2] & 0x1fff;\n    uint32_t        src_pitch  = regs[SCALE_Y_PITCH >> 2] & 0x1fff;\n    uint32_t        x_inc      = regs[SCALE_X_INC >> 2] & 0x001ffff0;\n    uint32_t        xuv_inc    = regs[SCALE_XUV_INC >> 2] & 0x001ffff0;\n    uint32_t        y_inc      = regs[SCALE_Y_INC >> 2] & 0x001ffff0;\n    int32_t         h_start    = mach64_3d_sign_extend(regs[SCALE_HACC >> 2], 21);\n    int32_t         uv_start   = mach64_3d_sign_extend(regs[SCALE_UV_HACC >> 2], 21);\n    int32_t         v_start    = mach64_3d_sign_extend(regs[SCALE_VACC >> 2], 21);\n    int             src_format = mach64_3d_src_format(mach64);\n    int             dst_format = mach64_3d_dst_format(mach64);\n    int             dst_bpp    = mach64_3d_bytes_per_pixel(dst_format);\n    int             dst_pitch  = ((mach64->dst_off_pitch >> 22) & 0x3ff) << 3;\n    uint32_t        dst_base   = (mach64->dst_off_pitch & 0xfffff) << 3;\n    int             dst_x      = mach64_3d_sign_extend(mach64->dst_y_x >> 16, 13);\n    int             dst_y      = mach64_3d_sign_extend(mach64->dst_y_x, 15);\n    int             dst_width  = (mach64->dst_height_width >> 16) & 0x1fff;\n    int             dst_height = mach64->dst_height_width & 0x1fff;\n    int             x_dir      = (mach64->dst_cntl & DST_X_DIR) ? 1 : -1;\n    int             y_dir      = (mach64->dst_cntl & DST_Y_DIR) ? 1 : -1;\n    int             sc_left    = mach64_3d_sign_extend(mach64->sc_left_right, 13);\n    int             sc_right   = mach64_3d_sign_extend(mach64->sc_left_right >> 16, 13);\n    int             sc_top     = mach64_3d_sign_extend(mach64->sc_top_bottom, 15);\n    int             sc_bottom  = mach64_3d_sign_extend(mach64->sc_top_bottom >> 16, 15);\n    uint64_t        vram_size  = (uint64_t) mach64->vram_mask + 1;\n    uint32_t        vacc_advanced;\n\n    if (src_width && src_height && src_pitch && dst_width && dst_height && mach64_scaler_source_bpp(src_format) && dst_bpp &&\n        mach64_scaler_destination_supported(dst_format)) {\n        for (int dy = 0; dy < dst_height; dy++) {\n            int      y          = dst_y + dy * y_dir;\n            int32_t  v_acc      = v_start + (int32_t) (dy * y_inc);\n            int      src_y      = mach64_scaler_accum_pixel(v_acc);\n            unsigned v_fraction = mach64_scaler_accum_fraction4(v_acc);\n            int      src_y_next;\n\n            if (src_y < 0)\n                src_y = 0;\n            if (src_y >= src_height)\n                src_y = src_height - 1;\n            src_y_next = (src_y + 1 >= src_height) ? (src_height - 1) : (src_y + 1);\n\n            for (int dx = 0; dx < dst_width; dx++) {\n                int      x          = dst_x + dx * x_dir;\n                int32_t  h_acc      = h_start + (int32_t) (dx * x_inc);\n                int      src_x      = mach64_scaler_accum_pixel(h_acc);\n                unsigned h_fraction = mach64_scaler_accum_fraction4(h_acc);\n                int      src_x_next;\n                int      inhibits;\n                int64_t  addr;\n                rgba_t   src;\n\n                if ((x < 0) || (y < 0) || (x < sc_left) || (x > sc_right) || (y < sc_top) || (y > sc_bottom))\n                    continue;\n\n                if (src_x < 0)\n                    src_x = 0;\n                if (src_x >= src_width)\n                    src_x = src_width - 1;\n                src_x_next = (src_x + 1 >= src_width) ? (src_width - 1) : (src_x + 1);\n\n                inhibits = mach64_scaler_source_inhibits(ctx, src_format, src_base, src_pitch, src_x, src_x_next, src_y,\n                                                         src_y_next, h_fraction, v_fraction, replicate);\n\n                if (src_format == 11) {\n                    int      uv_width    = (src_width + 1) >> 1;\n                    int32_t  uv_acc      = uv_start + (int32_t) (dx * xuv_inc);\n                    int      uv_x        = mach64_scaler_accum_pixel(uv_acc);\n                    unsigned uv_fraction = mach64_scaler_accum_fraction4(uv_acc);\n                    int      uv_x_next;\n\n                    if (uv_x < 0)\n                        uv_x = 0;\n                    if (uv_x >= uv_width)\n                        uv_x = uv_width - 1;\n                    uv_x_next = (uv_x + 1 >= uv_width) ? (uv_width - 1) : (uv_x + 1);\n\n                    src = mach64_scaler_sample_yuyv(ctx, src_base, src_pitch, src_x, src_x_next, uv_x, uv_x_next, src_y,\n                                                    src_y_next, h_fraction, uv_fraction, v_fraction, replicate);\n                } else {\n                    src = mach64_scaler_read_source(ctx, src_format, src_base, src_pitch, src_x, src_y);\n                    if (!replicate) {\n                        rgba_t below       = mach64_scaler_read_source(ctx, src_format, src_base, src_pitch, src_x, src_y_next);\n                        rgba_t right       = mach64_scaler_read_source(ctx, src_format, src_base, src_pitch, src_x_next, src_y);\n                        rgba_t below_right = mach64_scaler_read_source(ctx, src_format, src_base, src_pitch, src_x_next,\n                                                                       src_y_next);\n\n                        src = mach64_scaler_lerp_rgba(mach64_scaler_lerp_rgba(src, below, v_fraction),\n                                                      mach64_scaler_lerp_rgba(right, below_right, v_fraction), h_fraction);\n                    }\n                }\n\n                addr = (int64_t) dst_base + ((int64_t) y * dst_pitch + x) * dst_bpp;\n                if ((addr < 0) || (((uint64_t) addr + dst_bpp) > vram_size))\n                    continue;\n                mach64_scaler_write_pixel(ctx, addr, dst_format, x, y, src, inhibits);\n            }\n        }\n    }\n\n    /* SCALE_VACC moves on by the lines drawn. */\n    vacc_advanced              = (uint32_t) ((int64_t) v_start + (int64_t) dst_height * y_inc);\n    ctx->regs[SCALE_VACC >> 2] = (ctx->regs[SCALE_VACC >> 2] & ~0x001ffff0) | (vacc_advanced & 0x001ffff0);\n',
     " */\ntypedef struct mach64_scaler_t {\n    int      replicate;\n    uint32_t src_base;\n    int      src_width;\n    int      src_height;\n    uint32_t src_pitch;\n    uint32_t x_inc;\n    uint32_t xuv_inc;\n    uint32_t y_inc;\n    int32_t  h_start;\n    int32_t  uv_start;\n    int32_t  v_start;\n    int      src_format;\n    int      dst_format;\n    int      dst_bpp;\n    int      dst_pitch;\n    uint32_t dst_base;\n    int      dst_x;\n    int      dst_y;\n    int      dst_width;\n    int      dst_height;\n    int      x_dir;\n    int      y_dir;\n    int      sc_left;\n    int      sc_right;\n    int      sc_top;\n    int      sc_bottom;\n} mach64_scaler_t;\n\n/* The rectangle from the registers; returns whether it draws */\nstatic int\nmach64_scaler_setup(mach64_3d_t *ctx, mach64_scaler_t *sc)\n{\n    const mach64_t *mach64 = ctx->mach64;\n    const uint32_t *regs   = ctx->regs;\n\n    sc->replicate  = !!(regs[SCALE_3D_CNTL >> 2] & SCALE_PIX_REP);\n    sc->src_base   = regs[SCALE_Y_OFF >> 2] & ~7;\n    sc->src_width  = regs[SCALE_WIDTH >> 2] & 0x1fff;\n    sc->src_height = regs[SCALE_HEIGHT >> 2] & 0x1fff;\n    sc->src_pitch  = regs[SCALE_Y_PITCH >> 2] & 0x1fff;\n    sc->x_inc      = regs[SCALE_X_INC >> 2] & 0x001ffff0;\n    sc->xuv_inc    = regs[SCALE_XUV_INC >> 2] & 0x001ffff0;\n    sc->y_inc      = regs[SCALE_Y_INC >> 2] & 0x001ffff0;\n    sc->h_start    = mach64_3d_sign_extend(regs[SCALE_HACC >> 2], 21);\n    sc->uv_start   = mach64_3d_sign_extend(regs[SCALE_UV_HACC >> 2], 21);\n    sc->v_start    = mach64_3d_sign_extend(regs[SCALE_VACC >> 2], 21);\n    sc->src_format = mach64_3d_src_format(mach64);\n    sc->dst_format = mach64_3d_dst_format(mach64);\n    sc->dst_bpp    = mach64_3d_bytes_per_pixel(sc->dst_format);\n    sc->dst_pitch  = ((mach64->dst_off_pitch >> 22) & 0x3ff) << 3;\n    sc->dst_base   = (mach64->dst_off_pitch & 0xfffff) << 3;\n    sc->dst_x      = mach64_3d_sign_extend(mach64->dst_y_x >> 16, 13);\n    sc->dst_y      = mach64_3d_sign_extend(mach64->dst_y_x, 15);\n    sc->dst_width  = (mach64->dst_height_width >> 16) & 0x1fff;\n    sc->dst_height = mach64->dst_height_width & 0x1fff;\n    sc->x_dir      = (mach64->dst_cntl & DST_X_DIR) ? 1 : -1;\n    sc->y_dir      = (mach64->dst_cntl & DST_Y_DIR) ? 1 : -1;\n    sc->sc_left    = mach64_3d_sign_extend(mach64->sc_left_right, 13);\n    sc->sc_right   = mach64_3d_sign_extend(mach64->sc_left_right >> 16, 13);\n    sc->sc_top     = mach64_3d_sign_extend(mach64->sc_top_bottom, 15);\n    sc->sc_bottom  = mach64_3d_sign_extend(mach64->sc_top_bottom >> 16, 15);\n    return sc->src_width && sc->src_height && sc->src_pitch && sc->dst_width && sc->dst_height &&\n           mach64_scaler_source_bpp(sc->src_format) && sc->dst_bpp && mach64_scaler_destination_supported(sc->dst_format);\n}\n\n/* The rectangle's pixel dx across and dy down, from its start */\nstatic void\nmach64_scaler_pixel(mach64_3d_t *ctx, const mach64_scaler_t *sc, int dx, int dy)\n{\n    uint64_t vram_size  = (uint64_t) ctx->mach64->vram_mask + 1;\n    int      y          = sc->dst_y + dy * sc->y_dir;\n    int32_t  v_acc      = sc->v_start + (int32_t) (dy * sc->y_inc);\n    int      src_y      = mach64_scaler_accum_pixel(v_acc);\n    unsigned v_fraction = mach64_scaler_accum_fraction4(v_acc);\n    int      src_y_next;\n    int      x          = sc->dst_x + dx * sc->x_dir;\n    int32_t  h_acc      = sc->h_start + (int32_t) (dx * sc->x_inc);\n    int      src_x      = mach64_scaler_accum_pixel(h_acc);\n    unsigned h_fraction = mach64_scaler_accum_fraction4(h_acc);\n    int      src_x_next;\n    int      inhibits;\n    int64_t  addr;\n    rgba_t   src;\n\n    if (src_y < 0)\n        src_y = 0;\n    if (src_y >= sc->src_height)\n        src_y = sc->src_height - 1;\n    src_y_next = (src_y + 1 >= sc->src_height) ? (sc->src_height - 1) : (src_y + 1);\n\n    if ((x < 0) || (y < 0) || (x < sc->sc_left) || (x > sc->sc_right) || (y < sc->sc_top) || (y > sc->sc_bottom))\n        return;\n\n    if (src_x < 0)\n        src_x = 0;\n    if (src_x >= sc->src_width)\n        src_x = sc->src_width - 1;\n    src_x_next = (src_x + 1 >= sc->src_width) ? (sc->src_width - 1) : (src_x + 1);\n\n    inhibits = mach64_scaler_source_inhibits(ctx, sc->src_format, sc->src_base, sc->src_pitch, src_x, src_x_next, src_y,\n                                             src_y_next, h_fraction, v_fraction, sc->replicate);\n\n    if (sc->src_format == 11) {\n        int      uv_width    = (sc->src_width + 1) >> 1;\n        int32_t  uv_acc      = sc->uv_start + (int32_t) (dx * sc->xuv_inc);\n        int      uv_x        = mach64_scaler_accum_pixel(uv_acc);\n        unsigned uv_fraction = mach64_scaler_accum_fraction4(uv_acc);\n        int      uv_x_next;\n\n        if (uv_x < 0)\n            uv_x = 0;\n        if (uv_x >= uv_width)\n            uv_x = uv_width - 1;\n        uv_x_next = (uv_x + 1 >= uv_width) ? (uv_width - 1) : (uv_x + 1);\n\n        src = mach64_scaler_sample_yuyv(ctx, sc->src_base, sc->src_pitch, src_x, src_x_next, uv_x, uv_x_next, src_y,\n                                        src_y_next, h_fraction, uv_fraction, v_fraction, sc->replicate);\n    } else {\n        src = mach64_scaler_read_source(ctx, sc->src_format, sc->src_base, sc->src_pitch, src_x, src_y);\n        if (!sc->replicate) {\n            rgba_t below       = mach64_scaler_read_source(ctx, sc->src_format, sc->src_base, sc->src_pitch, src_x, src_y_next);\n            rgba_t right       = mach64_scaler_read_source(ctx, sc->src_format, sc->src_base, sc->src_pitch, src_x_next, src_y);\n            rgba_t below_right = mach64_scaler_read_source(ctx, sc->src_format, sc->src_base, sc->src_pitch, src_x_next,\n                                                           src_y_next);\n\n            src = mach64_scaler_lerp_rgba(mach64_scaler_lerp_rgba(src, below, v_fraction),\n                                          mach64_scaler_lerp_rgba(right, below_right, v_fraction), h_fraction);\n        }\n    }\n\n    addr = (int64_t) sc->dst_base + ((int64_t) y * sc->dst_pitch + x) * sc->dst_bpp;\n    if ((addr < 0) || (((uint64_t) addr + sc->dst_bpp) > vram_size))\n        return;\n    mach64_scaler_write_pixel(ctx, addr, sc->dst_format, x, y, src, inhibits);\n}\n\n/* KairoX86#237: the rectangle recorded for the GPU (kairo_gpu_mach64.h): each destination line inside the scissors a\n   row of the pixels it may draw, with the registers its pixels read */\nstatic void\nmach64_scaler_gpu(mach64_3d_t *ctx, const mach64_scaler_t *sc)\n{\n    const mach64_t *mach64           = ctx->mach64;\n    const uint32_t  cntl             = ctx->regs[SCALE_3D_CNTL >> 2];\n    uint32_t        record[KM_WORDS] = { 0 };\n    uint32_t        palettes[KAIRO_M64_PALETTE_WORDS];\n    uint32_t        rows[MACH64_3D_ROWS * KR_WORDS] = { 0 };\n    int             count = 0;\n    /* The pixels of a line, the same on each: across from dst_x by x_dir, inside the scissors and right of 0 */\n    int first = (sc->x_dir > 0) ? sc->dst_x : (sc->dst_x - (sc->dst_width - 1));\n    int last  = (sc->x_dir > 0) ? (sc->dst_x + (sc->dst_width - 1)) : sc->dst_x;\n\n    if (first < 0)\n        first = 0;\n    if (first < sc->sc_left)\n        first = sc->sc_left;\n    if (last > sc->sc_right)\n        last = sc->sc_right;\n    if (first > last)\n        return;\n\n    record[KM_FLAGS] = KAIRO_M64_SCALER | ((sc->x_dir < 0) ? KAIRO_M64_LEAD_LEFT : 0) | ((sc->y_dir < 0) ? KAIRO_M64_Y_UP : 0) |\n                       (sc->replicate ? KAIRO_M64_REPLICATE : 0) | (((cntl >> ALPHA_FOG_SHIFT) & 3) << 8);\n    record[KM_CNTL]         = cntl;\n    record[KM_DST_BASE]     = sc->dst_base;\n    record[KM_DST_PITCH]    = (uint32_t) sc->dst_pitch;\n    record[KM_DST_FORMAT]   = (uint32_t) sc->dst_format;\n    record[KM_DST_BPP]      = (uint32_t) sc->dst_bpp;\n    record[KM_CLR_CMP_CNTL] = mach64->clr_cmp_cntl;\n    record[KM_CLR_CMP_CLR]  = mach64->clr_cmp_clr;\n    record[KM_CLR_CMP_MASK] = mach64->clr_cmp_mask;\n    record[KM_WRITE_MASK]   = mach64->write_mask;\n    record[KM_DP_PIX_WIDTH] = mach64->dp_pix_width;\n    record[KS_SRC_BASE]     = sc->src_base;\n    record[KS_SRC_WIDTH]    = (uint32_t) sc->src_width;\n    record[KS_SRC_HEIGHT]   = (uint32_t) sc->src_height;\n    record[KS_SRC_PITCH]    = sc->src_pitch;\n    record[KS_SRC_FORMAT]   = (uint32_t) sc->src_format;\n    record[KS_X_INC]        = sc->x_inc;\n    record[KS_XUV_INC]      = sc->xuv_inc;\n    record[KS_Y_INC]        = sc->y_inc;\n    record[KS_H_START]      = (uint32_t) sc->h_start;\n    record[KS_UV_START]     = (uint32_t) sc->uv_start;\n    record[KS_V_START]      = (uint32_t) sc->v_start;\n    record[KS_DST_X]        = (uint32_t) sc->dst_x;\n    record[KS_DST_Y]        = (uint32_t) sc->dst_y;\n    record[KS_DP_MIX]       = mach64->dp_mix;\n    memcpy(palettes, ctx->texture_palette, 256 * 4);\n    memcpy(palettes + 256, mach64->svga.pallook, 256 * 4);\n\n    for (int dy = 0; dy < sc->dst_height; dy++) {\n        const int y = sc->dst_y + dy * sc->y_dir;\n        uint32_t *row;\n\n        if ((y < 0) || (y < sc->sc_top) || (y > sc->sc_bottom))\n            continue;\n        row            = &rows[count * KR_WORDS];\n        row[KR_Y]      = (uint32_t) y;\n        row[KR_FIRST]  = (uint32_t) first;\n        row[KR_END]    = (uint32_t) (last + 1);\n        row[KR_LEAD]   = (uint32_t) sc->dst_x;\n        mach64_3d_mark_changed(mach64, sc->dst_base + (uint32_t) (y * sc->dst_pitch + first) * (uint32_t) sc->dst_bpp,\n                               (uint32_t) (last + 1 - first) * (uint32_t) sc->dst_bpp);\n        if (++count == MACH64_3D_ROWS) {\n            kairo_mach64_gpu_draw(ctx->k_gpu, record, palettes, rows, count);\n            count = 0;\n        }\n    }\n    if (count)\n        kairo_mach64_gpu_draw(ctx->k_gpu, record, palettes, rows, count);\n}\n\nstatic void\nmach64_scaler_draw(mach64_3d_t *ctx)\n{\n    mach64_scaler_t sc;\n    uint32_t        vacc_advanced;\n\n    if (mach64_scaler_setup(ctx, &sc)) {\n        if (ctx->k_gpu != NULL)\n            mach64_scaler_gpu(ctx, &sc);\n        else {\n            for (int dy = 0; dy < sc.dst_height; dy++) {\n                for (int dx = 0; dx < sc.dst_width; dx++)\n                    mach64_scaler_pixel(ctx, &sc, dx, dy);\n            }\n        }\n    }\n\n    /* SCALE_VACC moves on by the lines drawn. */\n    vacc_advanced              = (uint32_t) ((int64_t) sc.v_start + (int64_t) sc.dst_height * sc.y_inc);\n    ctx->regs[SCALE_VACC >> 2] = (ctx->regs[SCALE_VACC >> 2] & ~0x001ffff0) | (vacc_advanced & 0x001ffff0);\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    ctx->threads = ((mach64->render_threads == 2) || (mach64->render_threads == 4)) ? mach64->render_threads : 1;\n    return ctx;\n',
     '    ctx->threads = ((mach64->render_threads == 2) || (mach64->render_threads == 4)) ? mach64->render_threads : 1;\n    /* KairoX86#237: with Hardware acceleration on, the rows drawn on the GPU */\n    if (kairo_gpu_on) {\n        ctx->k_gpu              = kairo_mach64_gpu_open(mach64->svga.vram, mach64->vram_mask, (int32_t *) &ctx->dither);\n        mach64->svga.kairo_touch = mach64_3d_svga_touch;\n    }\n    return ctx;\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '{\n    mach64_3d_helpers_close(ctx);\n',
     '{\n    kairo_mach64_gpu_close(ctx->k_gpu); /* KairoX86#237 */\n    mach64_3d_helpers_close(ctx);\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '{\n    mach64->accel.dst_pix_width  = mach64->dp_pix_width & 7;\n',
     "{\n    /* KairoX86#237: the 3D engine's rows on the GPU drawn before the 2D engine reads or writes video memory */\n    mach64_3d_kairo_drain(mach64);\n\n    mach64->accel.dst_pix_width  = mach64->dp_pix_width & 7;\n"),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '        return;\n    }\n\n    if (count == -1) {\n',
     '        return;\n    }\n    mach64_3d_kairo_drain(mach64); /* KairoX86#237: rows recorded since the operation started */\n\n    if (count == -1) {\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '        [26] = 0x308, [27] = 0x330\n    };\n\n    if (cntl & (1u << 31))\n',
     '        [26] = 0x308, [27] = 0x330\n    };\n    mach64_3d_kairo_drain(mach64); /* KairoX86#237: the context is read from video memory */\n\n    if (cntl & (1u << 31))\n'),
    ('86box/src/video/vid_ati_mach64.h',
     'void             mach64_3d_close(mach64_3d_t *ctx);\nint              mach64_3d_read(mach64_t *mach64, uint32_t addr, uint32_t *val);\n',
     "void             mach64_3d_close(mach64_3d_t *ctx);\n/* KairoX86#237: the 3D engine's rows on the GPU drawn first where something else reads or writes video memory\n   (no-ops in software) */\nvoid mach64_3d_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len);\nvoid mach64_3d_kairo_drain(mach64_t *mach64);\nint              mach64_3d_read(mach64_t *mach64, uint32_t addr, uint32_t *val);\n"),
]

# KairoX86#294: the PowerVR PCX2's end of render comes at the frame's emulated render time whatever the host's speed:
# a frame the render threads have not finished is waited for there (pcx_render_wait), as the Voodoos wait for their
# render threads, instead of holding the end of render back in emulated time while the host catches up.
KAIROX86_POWERVR_RENDER_TIMING = [
    ('86box/src/video/vid_powervr_pcx.c',
     '    atomic_int     render_ready;   /* set by the render thread when the frame is drawn */\n    double         render_late_us; /* emulated time the end of render was held back */\n    int            render_discard;\n',
     '    atomic_int     render_ready;   /* set by the render thread when the frame is drawn */\n    int            render_discard;\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     '    /* Statistics. */\n    double   stat_render_ms, stat_render_max_ms, stat_wait_ms, stat_output_ms, stat_late_ms;\n    uint32_t stat_frames;\n',
     '    /* Statistics. */\n    double   stat_render_ms, stat_render_max_ms, stat_wait_ms, stat_output_ms;\n    uint32_t stat_frames;\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     '    pcx->render_discard = 0;\n    pcx->render_late_us = 0.0;\n    atomic_store(&pcx->render_ready, 0);\n',
     '    pcx->render_discard = 0;\n    atomic_store(&pcx->render_ready, 0);\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     "\n/* How often the end of render looks again for a frame the host has not\n   finished, in emulated microseconds. */\n#define PCX_RENDER_POLL_US 250.0\n\nstatic void\npcx_render_done(void *priv)\n{\n    pcx_t *pcx = (pcx_t *) priv;\n\n    /* If the host has not finished drawing the frame yet, the card is\n       simply still busy: hold the end of render back in emulated time\n       rather than stalling the emulated PC until the host catches up.\n       Stalling froze the guest's clocks, and the catch-up afterwards\n       could drop timer interrupts, so games that count them ran in slow\n       motion while reporting a normal frame rate. */\n    if (pcx->render_pending && !atomic_load(&pcx->render_ready)) {\n        pcx->render_late_us += PCX_RENDER_POLL_US;\n        timer_on_auto(&pcx->render_timer, PCX_RENDER_POLL_US);\n        return;\n    }\n\n    if (pcx->render_pending) {\n",
     "\nstatic void\npcx_render_done(void *priv)\n{\n    pcx_t *pcx = (pcx_t *) priv;\n\n    /* KairoX86#294: the end of render comes at the frame's emulated render\n       time whatever the host's speed: a frame the host has not finished is\n       waited for here (pcx_render_wait), as the Voodoos wait for their\n       render threads, so the guest sees the same moment in every run. */\n    if (pcx->render_pending) {\n"),
    ('86box/src/video/vid_powervr_pcx.c',
     '        pcx->stat_output_ms += pcx_now_ms() - t1;\n        pcx->stat_late_ms += pcx->render_late_us / 1000.0;\n        pcx->stat_render_ms += pcx->job_ms;\n',
     '        pcx->stat_output_ms += pcx_now_ms() - t1;\n        pcx->stat_render_ms += pcx->job_ms;\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     '                    "emulation waited %.1f ms and wrote output %.2f ms per frame; "\n                    "emulated render time %.1f ms + %.1f ms held back for the host\\n",\n                    pcx->frames - 99, pcx->frames, pcx->stat_render_ms / 100.0, pcx->stat_render_max_ms,\n                    pcx->n_helpers + 1, pcx->stat_wait_ms / 100.0, pcx->stat_output_ms / 100.0,\n                    pcx->render_delay_us / 1000.0, pcx->stat_late_ms / 100.0);\n            pcx->stat_frames = 0;\n            pcx->stat_render_ms = pcx->stat_render_max_ms = pcx->stat_wait_ms = pcx->stat_output_ms = pcx->stat_late_ms = 0.0;\n        }\n',
     '                    "emulation waited %.1f ms and wrote output %.2f ms per frame; "\n                    "emulated render time %.1f ms\\n",\n                    pcx->frames - 99, pcx->frames, pcx->stat_render_ms / 100.0, pcx->stat_render_max_ms,\n                    pcx->n_helpers + 1, pcx->stat_wait_ms / 100.0, pcx->stat_output_ms / 100.0,\n                    pcx->render_delay_us / 1000.0);\n            pcx->stat_frames = 0;\n            pcx->stat_render_ms = pcx->stat_render_max_ms = pcx->stat_wait_ms = pcx->stat_output_ms = 0.0;\n        }\n'),
]

# KairoX86#269: the PowerVR PCX2's tiles on the GPU (86box/kairo_gpu_powervr.h, an added file, core/kairo/gpu_powervr.c,
# core/kairo/shaders/powervr.comp). With the machine's Hardware acceleration on, the texture memory and the frame's
# RGB buffer are memory the GPU shares, and after pcxr_prepare the render thread hands pcxr_gpu_lists' lists (the
# decoded planes and objects, each span with the decoder schedule pcxr_render_tiles would give it) to the kernel
# instead of drawing the tiles on the render threads. The pack and the bus-master writes stay as they are.
KAIROX86_GPU_POWERVR = [
    ('86box/src/video/vid_powervr_pcx.c',
     '#include "vid_powervr_pcx_render.h"\n\n',
     '#include "vid_powervr_pcx_render.h"\n#include <86box/kairo_gpu.h> /* KairoX86#269 */\n#include <86box/kairo_gpu_powervr.h>\n\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     '    pcxr_job_t    *rjob;\n    volatile int   render_quit;\n',
     "    pcxr_job_t    *rjob;\n    void          *k_gpu; /* KairoX86#269: the tiles' GPU state (kairo_gpu_powervr.h), NULL in software */\n    volatile int   render_quit;\n"),
    ('86box/src/video/vid_powervr_pcx.c',
     '        memset(pcx->rgb, 0, PCXR_MAX_W * PCXR_MAX_H * sizeof(uint32_t));\n        if (pcxr_prepare(pcx->rjob, &pcx->job, &pcx->job_res) > 0)\n            pcx_run_phase(pcx, PCX_PHASE_TILES);\n        pcx_pack_area(pcx);\n',
     '        memset(pcx->rgb, 0, PCXR_MAX_W * PCXR_MAX_H * sizeof(uint32_t));\n        if (pcxr_prepare(pcx->rjob, &pcx->job, &pcx->job_res) > 0) {\n            if (pcx->k_gpu != NULL) {\n                /* KairoX86#269: the tiles drawn on the GPU */\n                kairo_pvr_lists_t lists;\n                if (pcxr_gpu_lists(pcx->rjob, &lists) < 0)\n                    fatal("PowerVR on the GPU: no memory for a frame\'s lists\\n");\n                kairo_pvr_gpu_render(pcx->k_gpu, &lists);\n            } else\n                pcx_run_phase(pcx, PCX_PHASE_TILES);\n        }\n        pcx_pack_area(pcx);\n'),
    ('86box/src/video/vid_powervr_pcx.c',
     '\n    pcx->tex_mem = calloc(1, PCX_TEXMEM_SIZE);\n    if (pcx->chip == PCX_CHIP_PCX2) {\n        pcx->isp_buf         = calloc(PCX_TLB_ENTRIES, 0x4000);\n        pcx->rgb             = calloc(PCXR_MAX_W * PCXR_MAX_H, sizeof(uint32_t));\n        pcx->out_buf         = malloc(PCXR_MAX_W * PCXR_MAX_H * 4);\n',
     "\n    /* KairoX86#269: with Hardware acceleration on, the texture memory and the frame's RGB buffer are memory the GPU\n       shares, and the tiles are drawn there */\n    pcx->tex_mem = kairo_gpu_on ? kairo_gpu_alloc(PCX_TEXMEM_SIZE) : calloc(1, PCX_TEXMEM_SIZE);\n    if (pcx->chip == PCX_CHIP_PCX2) {\n        pcx->isp_buf         = calloc(PCX_TLB_ENTRIES, 0x4000);\n        pcx->rgb             = kairo_gpu_on ? kairo_gpu_alloc(PCXR_MAX_W * PCXR_MAX_H * sizeof(uint32_t))\n                                            : calloc(PCXR_MAX_W * PCXR_MAX_H, sizeof(uint32_t));\n        if (kairo_gpu_on)\n            pcx->k_gpu = kairo_pvr_gpu_open((uint32_t *) pcx->tex_mem, PCX_TEXMEM_SIZE / 4, pcx->rgb);\n        pcx->out_buf         = malloc(PCXR_MAX_W * PCXR_MAX_H * 4);\n"),
    ('86box/src/video/vid_powervr_pcx.c',
     '    }\n    free(pcx->isp_buf);\n    free(pcx->rgb);\n    free(pcx->out_buf);\n    free(pcx->spans);\n    free(pcx->row_spans);\n    free(pcx->tex_mem);\n    free(pcx);\n',
     '    }\n    kairo_pvr_gpu_close(pcx->k_gpu); /* KairoX86#269 */\n    free(pcx->isp_buf);\n    if (kairo_gpu_on) {\n        kairo_gpu_free(pcx->rgb);\n        kairo_gpu_free(pcx->tex_mem);\n    } else {\n        free(pcx->rgb);\n        free(pcx->tex_mem);\n    }\n    free(pcx->out_buf);\n    free(pcx->spans);\n    free(pcx->row_spans);\n    free(pcx);\n'),
    ('86box/src/video/vid_powervr_pcx_render.c',
     '    uint32_t            cap_planes, cap_objects, cap_tiles;\n};\n',
     '    uint32_t            cap_planes, cap_objects, cap_tiles;\n    /* KairoX86#269: its lists for the GPU (pcxr_gpu_lists) */\n    uint32_t           *g_planes, *g_objects, *g_spans, *g_sched;\n    uint32_t            g_cap_planes, g_cap_objects, g_cap_spans, g_cap_sched;\n    uint32_t            g_frame[KF_WORDS];\n};\n'),
    ('86box/src/video/vid_powervr_pcx_render.c',
     '    free(job->tiles);\n    free(job);\n',
     '    free(job->tiles);\n    free(job->g_planes); /* KairoX86#269 */\n    free(job->g_objects);\n    free(job->g_spans);\n    free(job->g_sched);\n    free(job);\n'),
    ('86box/src/video/vid_powervr_pcx_render.c',
     '}\n\nvoid\npcxr_render(const pcxr_frame_t *f, uint32_t *rgb, pcxr_result_t *res)\n',
     "}\n\n/* KairoX86#269: the prepared frame as the GPU kernel's lists (86box/kairo_gpu_powervr.h): the decoded planes and\n   objects, and every span of every tile with the schedule its decoder state gives it, the states run from span to\n   span as pcxr_render_tiles runs them. The lists live in the job until the next call. */\nint\npcxr_gpu_lists(pcxr_job_t *job, kairo_pvr_lists_t *out)\n{\n    const pcxr_frame_t *f = job->f;\n    ctx_t               c;\n    sched_cache_t       sc;\n    uint32_t            n_spans = 0, n_sched = 0;\n\n    memset(&c, 0, sizeof(c));\n    memset(&sc, 0, sizeof(sc));\n    c.f = f;\n\n    if (grow((void **) &job->g_planes, &job->g_cap_planes, job->n_planes * KP_WORDS, 4)\n        || grow((void **) &job->g_objects, &job->g_cap_objects, job->n_objects * KO_WORDS, 4))\n        return -1;\n    for (uint32_t i = 0; i < job->n_planes; i++) {\n        const plane_t *pl = &job->planes[i];\n        uint32_t      *w  = &job->g_planes[i * KP_WORDS];\n        w[KP_A]           = (uint32_t) (uint64_t) pl->a;\n        w[KP_A + 1]       = (uint32_t) ((uint64_t) pl->a >> 32);\n        w[KP_B]           = (uint32_t) (uint64_t) pl->b;\n        w[KP_B + 1]       = (uint32_t) ((uint64_t) pl->b >> 32);\n        w[KP_C]           = (uint32_t) pl->c;\n        w[KP_INDEX]       = pl->index;\n        w[KP_INSTR]       = (uint32_t) pl->instr;\n        w[KP_INSTR + 1]   = 0;\n    }\n    for (uint32_t i = 0; i < job->n_objects; i++) {\n        uint32_t *w           = &job->g_objects[i * KO_WORDS];\n        w[KO_FIRST]           = job->objects[i].first;\n        w[KO_COUNT]           = job->objects[i].count;\n        w[KO_LAST_IN_REGION]  = (uint32_t) job->objects[i].last_in_region;\n        w[KO_LAST_IN_REGION + 1] = 0;\n    }\n\n    for (uint32_t ti = 0; ti < job->n_tiles; ti++) {\n        const tile_t *t  = &job->tiles[ti];\n        uint32_t      p0 = t->n_objects ? job->objects[t->first_object].first : 0;\n        uint32_t      np = t->n_objects ? job->objects[t->first_object + t->n_objects - 1].first\n                                         + job->objects[t->first_object + t->n_objects - 1].count - p0\n                                       : 0;\n        int           st = pcxr_state(t->prev_intern_out, t->sec_obj, t->first_obj);\n        uint32_t      sched_of_slot[32];\n\n        memset(sc.slot, -1, sizeof(sc.slot));\n        sc.used = 0;\n        for (int yline = t->ypos; yline < t->ypos + t->ysize; yline++) {\n            for (int xspan = t->xpos; xspan < t->xpos + t->xsize; xspan += NUM_CELLS) {\n                int       slot = sc.slot[st];\n                uint32_t *span;\n\n                if (slot < 0) {\n                    if ((slot = build_schedule(&c, job, t, p0, np, &sc, st)) < 0) {\n                        free(sc.buf);\n                        return -1;\n                    }\n                    /* the schedule's words, after the others */\n                    if (grow((void **) &job->g_sched, &job->g_cap_sched, n_sched + np, 4)) {\n                        free(sc.buf);\n                        return -1;\n                    }\n                    for (uint32_t k = 0; k < np; k++) {\n                        const sched_t *e = &sc.buf[(uint32_t) slot * np + k];\n                        job->g_sched[n_sched + k] = (uint32_t) e->run | ((uint32_t) e->wi.i_load << 1) | ((uint32_t) e->wi.u_load << 5)\n                                                    | ((uint32_t) e->wi.test_shad << 7) | ((uint32_t) e->wi.plane_visib << 9)\n                                                    | ((uint32_t) e->wi.delayed_clear_u_id << 10) | ((uint32_t) e->wi.plane_perp << 11)\n                                                    | ((uint32_t) e->wi.mux_sel << 12);\n                    }\n                    sched_of_slot[slot] = n_sched;\n                    n_sched += np;\n                }\n                if (grow((void **) &job->g_spans, &job->g_cap_spans, (n_spans + 1) * KN_WORDS, 4)) {\n                    free(sc.buf);\n                    return -1;\n                }\n                span                  = &job->g_spans[n_spans * KN_WORDS];\n                span[KN_FIRST_OBJECT] = t->first_object;\n                span[KN_N_OBJECTS]    = t->n_objects;\n                span[KN_X]            = (uint32_t) xspan;\n                span[KN_Y]            = (uint32_t) yline;\n                span[KN_SCHED]        = sched_of_slot[slot];\n                span[KN_P0]           = p0;\n                span[KN_P0 + 1]       = 0;\n                span[KN_P0 + 2]       = 0;\n                n_spans++;\n                st = sc.next[st];\n            }\n        }\n    }\n    free(sc.buf);\n\n    job->g_frame[KF_FOG_SHIFT]  = f->fog_shift;\n    job->g_frame[KF_FOG_COLOUR] = f->fog_colour;\n    job->g_frame[KF_CAMERA]     = f->camera;\n    job->g_frame[KF_XCLIP]      = f->xclip;\n    job->g_frame[KF_BILINEAR]   = f->bilinear;\n    job->g_frame[KF_TEX_WORDS]  = f->tex_words;\n    for (int i = 0; i < 128; i++)\n        job->g_frame[KF_FOG_TABLE + i] = f->fog_table[i];\n\n    out->planes    = job->g_planes;\n    out->objects   = job->g_objects;\n    out->spans     = job->g_spans;\n    out->sched     = job->g_sched;\n    out->frame     = job->g_frame;\n    out->n_planes  = job->n_planes;\n    out->n_objects = job->n_objects;\n    out->n_spans   = n_spans;\n    out->n_sched   = n_sched;\n    return 0;\n}\n\nvoid\npcxr_render(const pcxr_frame_t *f, uint32_t *rgb, pcxr_result_t *res)\n"),
    ('86box/src/video/vid_powervr_pcx_render.h',
     '#include <stdint.h>\n\n',
     '#include <stdint.h>\n#include <86box/kairo_gpu_powervr.h> /* KairoX86#269 */\n\n'),
    ('86box/src/video/vid_powervr_pcx_render.h',
     '\n#endif\n',
     "\n/* KairoX86#269: a prepared job's frame as the GPU kernel's lists (86box/kairo_gpu_powervr.h), valid until the next\n   call; 0, or -1 without memory */\nint pcxr_gpu_lists(pcxr_job_t *job, kairo_pvr_lists_t *out);\n\n#endif\n"),
]

# KairoX86#295: a Mach64 line is drawn once the FIFO has run out (svga->render_sync, mach64_wait_fifo_idle), so it
# shows every operation the guest queued before it, whatever the host's thread has got through.
KAIROX86_MACH64_DISPLAY_SETTLE = [
    ('86box/src/video/vid_ati_mach64.c',
     '}\n\nstatic void *\nmach64_common_init(const device_t *info)\n',
     "}\n\n/* KairoX86#295: each line drawn once every operation the guest queued before it has run (the 2D engine's FIFO,\n   run here on the display's thread as mach64_wait_fifo_idle runs it), as the ViRGE's and the Voodoos' displays\n   settle */\nstatic void\nmach64_render_sync(svga_t *svga)\n{\n    mach64_wait_fifo_idle((mach64_t *) svga->priv);\n}\n\nstatic void *\nmach64_common_init(const device_t *info)\n"),
    ('86box/src/video/vid_ati_mach64.c',
     '                  mach64_overlay_draw);\n\n',
     '                  mach64_overlay_draw);\n    svga->render_sync = mach64_render_sync; /* KairoX86#295 */\n\n'),
]

# KairoX86#237: the Mach64 2D engine's operations on the GPU, on the drawing engines' shared batches
# (86box/kairo_gpu_seg.h and 86box/kairo_gpu_mach64.h, added files; core/kairo/gpu_seg.c, gpu_mach64_2d.c,
# core/kairo/shaders/seg.glsl, mach64_2d.comp). The operation's draw and step are split apart
# (mach64_rect_draw/_advance, mach64_line_draws/_draw/_advance). With Hardware acceleration on, an operation's
# record and rows go into the batch where it starts, or as the host feeds them; the engine's walk stays the CPU's.
KAIROX86_GPU_MACH64_2D = [
    ('86box/src/video/vid_ati_mach64.c',
     '#include "vid_ati_mach64.h"\n\n',
     '#include "vid_ati_mach64.h"\n#include <86box/kairo_gpu.h> /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n\n',
     '        return 0xff;\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xffff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n\n',
     '        return 0xffff;\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '        return 0xffffffff;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 4); /* KairoX86#237 */\n\n',
     '        return 0xffffffff;\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, 4); /* KairoX86#237 */\n\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n',
     '    addr &= svga->vram_mask;\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, 1); /* KairoX86#237 */\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n',
     '    addr &= svga->vram_mask;\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, 2); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '            offset_from_base <<= 1;\n            mach64_3d_kairo_touch(mach64, offset_from_base, 6); /* KairoX86#237 */\n            svga->vram[offset_from_base & svga->vram_mask] = (val & 0xFF);\n',
     '            offset_from_base <<= 1;\n            mach64_kairo_touch(mach64, offset_from_base, 6); /* KairoX86#237 */\n            svga->vram[offset_from_base & svga->vram_mask] = (val & 0xFF);\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '            offset_from_base <<= 2;\n            mach64_3d_kairo_touch(mach64, offset_from_base, 16); /* KairoX86#237 */\n            if (((mach64->scaler_yuv_aper >> 4) & 0xc) == 0x8) { // U plane\n',
     '            offset_from_base <<= 2;\n            mach64_kairo_touch(mach64, offset_from_base, 16); /* KairoX86#237 */\n            if (((mach64->scaler_yuv_aper >> 4) & 0xc) == 0x8) { // U plane\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '    addr &= svga->vram_mask;\n    mach64_3d_kairo_touch(mach64, addr, 4); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n',
     '    addr &= svga->vram_mask;\n    mach64_kairo_touch(mach64, addr, 4); /* KairoX86#237 */\n    svga->changedvram[addr >> 12]   = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_ati_mach64.c',
     '}\n\nstatic void *\nmach64_common_init(const device_t *info)\n',
     "}\n\n/* KairoX86#237: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\nmach64_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    mach64_kairo_touch((mach64_t *) svga->priv, addr, len);\n}\n\nstatic void *\nmach64_common_init(const device_t *info)\n"),
    ('86box/src/video/vid_ati_mach64.c',
     '    svga->render_sync = mach64_render_sync; /* KairoX86#295 */\n\n',
     "    svga->render_sync = mach64_render_sync; /* KairoX86#295 */\n    /* KairoX86#237: with Hardware acceleration on, the 2D engine's operations drawn on the GPU, and both engines' work\n       drawn first where the SVGA core's handlers or the display meet it */\n    if (kairo_gpu_on) {\n        mach64_2d_kairo_open(mach64);\n        svga->kairo_touch = mach64_svga_touch;\n    }\n\n"),
    ('86box/src/video/vid_ati_mach64.c',
     '    thread_close_mutex(mach64->dma.lock);\n#endif\n\n    if (mach64->type == MACH64_GTB) {\n',
     '    thread_close_mutex(mach64->dma.lock);\n#endif\n    mach64_2d_kairo_close(mach64); /* KairoX86#237: after the FIFO thread, before video memory goes */\n\n    if (mach64->type == MACH64_GTB) {\n'),
    ('86box/src/video/vid_ati_mach64.h',
     '    mach64_3d_t     *gt3d;        /* 3D engine and scaler, vid_ati_mach64_3d.c */\n    mach64_timing_t *timing;      /* draw engine timing, vid_ati_mach64_accel.c */\n',
     "    mach64_3d_t     *gt3d;        /* 3D engine and scaler, vid_ati_mach64_3d.c */\n    void            *k_2d;        /* KairoX86#237: the 2D engine's GPU batch, NULL in software */\n    mach64_timing_t *timing;      /* draw engine timing, vid_ati_mach64_accel.c */\n"),
    ('86box/src/video/vid_ati_mach64.h',
     'void mach64_3d_kairo_drain(mach64_t *mach64);\nint              mach64_3d_read(mach64_t *mach64, uint32_t addr, uint32_t *val);\n',
     "void mach64_3d_kairo_drain(mach64_t *mach64);\n/* KairoX86#237: the 2D engine's batch on the GPU (vid_ati_mach64_accel.c), and both engines' touch */\nvoid mach64_2d_kairo_open(mach64_t *mach64);\nvoid mach64_2d_kairo_close(mach64_t *mach64);\nvoid mach64_2d_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len);\nvoid mach64_2d_kairo_drain(mach64_t *mach64);\nvoid mach64_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len);\nint              mach64_3d_read(mach64_t *mach64, uint32_t addr, uint32_t *val);\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '\n    record[KM_FLAGS] = (px->textured ? KAIRO_M64_TEXTURED : 0) | (px->z_enabled ? KAIRO_M64_Z_ENABLED : 0) |\n',
     "\n    /* the 2D engine's recorded work first: it ran before these rows */\n    mach64_2d_kairo_drain((mach64_t *) mach64);\n\n    record[KM_FLAGS] = (px->textured ? KAIRO_M64_TEXTURED : 0) | (px->z_enabled ? KAIRO_M64_Z_ENABLED : 0) |\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     "        kairo_mach64_gpu_touch(mach64->gt3d->k_gpu, addr & mach64->vram_mask, len);\n}\n\n/* The SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\nmach64_3d_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    mach64_3d_kairo_touch((mach64_t *) svga->priv, addr, len);\n}\n",
     '        kairo_mach64_gpu_touch(mach64->gt3d->k_gpu, addr & mach64->vram_mask, len);\n}\n'),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '\n    if (first < 0)\n',
     "\n    mach64_2d_kairo_drain((mach64_t *) mach64); /* the 2D engine's recorded work first */\n    if (first < 0)\n"),
    ('86box/src/video/vid_ati_mach64_3d.c',
     '    if (kairo_gpu_on) {\n        ctx->k_gpu              = kairo_mach64_gpu_open(mach64->svga.vram, mach64->vram_mask, (int32_t *) &ctx->dither);\n        mach64->svga.kairo_touch = mach64_3d_svga_touch;\n    }\n',
     '    if (kairo_gpu_on) {\n        ctx->k_gpu = kairo_mach64_gpu_open(mach64->svga.vram, mach64->vram_mask, (int32_t *) &ctx->dither);\n    }\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '#include "vid_ati_mach64.h"\n\n',
     '#include "vid_ati_mach64.h"\n#include <86box/kairo_gpu.h>        /* KairoX86#237 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_mach64.h>\n\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '}\n\nvoid\nmach64_start_fill(mach64_t *mach64)\n',
     '}\n\nstatic void mach64_2d_begin(mach64_t *mach64); /* KairoX86#237 */\n\nvoid\nmach64_start_fill(mach64_t *mach64)\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    if ((mach64->src_cntl & SRC_8x8x8_BRUSH) && !(mach64->src_cntl & SRC_8x8x8_BRUSH_LOADED)) {\n        for (int y = 0; y < 8; y++)\n',
     '    if ((mach64->src_cntl & SRC_8x8x8_BRUSH) && !(mach64->src_cntl & SRC_8x8x8_BRUSH_LOADED)) {\n        mach64_2d_kairo_touch(mach64, mach64->accel.src_offset & ~7, 64); /* KairoX86#237 */\n        for (int y = 0; y < 8; y++)\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '        mach64_timing_op(mach64, OP_RECT);\n}\n',
     '        mach64_timing_op(mach64, OP_RECT);\n    if (mach64->k_2d != NULL) /* KairoX86#237 */\n        mach64_2d_begin(mach64);\n}\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '        mach64_timing_op(mach64, OP_LINE);\n}\n',
     '        mach64_timing_op(mach64, OP_LINE);\n    if (mach64->k_2d != NULL) /* KairoX86#237 */\n        mach64_2d_begin(mach64);\n}\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '\n/* One destination pixel of a rectangle fill or blit. host is the host\n   pixel (colour, or the mono bit) for this pixel when the host feeds it.\n   Returns 1 when the operation has finished. */\nstatic int\nmach64_rect_pixel(mach64_t *mach64, uint32_t host)\n{\n',
     "\n/* One destination pixel of a rectangle fill or blit, at the engine's\n   position. host is the host pixel (colour, or the mono bit) for this pixel\n   when the host feeds it. */\nstatic void\nmach64_rect_draw(mach64_t *mach64, uint32_t host)\n{\n"),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    }\n\n    /* Next pixel: the source trajectory, then the destination. */\n',
     "    }\n}\n\nstatic void mach64_rect_finish(mach64_t *mach64);\n\n/* The engine's position moved on past a rectangle's pixel. Returns 1 when\n   the operation has finished. */\nstatic int\nmach64_rect_advance(mach64_t *mach64)\n{\n    /* Next pixel: the source trajectory, then the destination. */\n"),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '\n    /*Blit finished*/\n',
     "\n    mach64_rect_finish(mach64);\n    return 1;\n}\n\n/* A rectangle's end: the engine idle, and DST_Y_X moved on when tiling */\nstatic void\nmach64_rect_finish(mach64_t *mach64)\n{\n    /*Blit finished*/\n"),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    }\n    return 1;\n}\n\n/* One pixel of a Bresenham line. There is no 24 bpp line: "the line draw\n   engine does not function in 24bpp packed mode" (PRG 4-7). The source\n   is rectangular and never advances in Y; its X goes by SRC_LINE_X_DIR\n   (RRG 3-86, 3-87). Returns 1 when the line has finished. */\nstatic int\nmach64_line_pixel(mach64_t *mach64, uint32_t host)\n{\n',
     '    }\n}\n\n/* Whether a line\'s error term is positive: the minor axis moves, and a\n   polygon outline draws (DST_BRES_SIGN breaks a zero). */\nstatic int\nmach64_line_err_pos(const mach64_t *mach64)\n{\n    return (mach64->accel.err > 0) || ((mach64->accel.err == 0) && !(mach64->dst_cntl & DST_BRES_SIGN));\n}\n\n/* Whether a line draws its pixel at the engine\'s position, and where in X\n   (a polygon outline\'s pixel saturates to the left scissor). */\nstatic int\nmach64_line_draws(const mach64_t *mach64, int *dx)\n{\n    int draw = 1;\n\n    *dx = mach64->accel.dst_x;\n    /* Polygon outline: one pixel a scan line, none for horizontal lines,\n       saturated to the left scissor (RRG 3-47). */\n    if (mach64->dst_cntl & DST_POLYGON_EN) {\n        draw = (mach64->dst_cntl & DST_Y_MAJOR) || mach64_line_err_pos(mach64);\n        if (*dx < mach64->accel.sc_left)\n            *dx = mach64->accel.sc_left;\n    }\n\n    if ((mach64->accel.x_count == 1) && !(mach64->dst_cntl & DST_LAST_PEL))\n        draw = 0;\n    return draw;\n}\n\n/* One pixel of a Bresenham line, at the engine\'s position. There is no 24\n   bpp line: "the line draw engine does not function in 24bpp packed mode"\n   (PRG 4-7). The source is rectangular and never advances in Y; its X goes\n   by SRC_LINE_X_DIR (RRG 3-86, 3-87). */\nstatic void\nmach64_line_draw(mach64_t *mach64, uint32_t host)\n{\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    uint32_t old_dest_dat;\n    int      err_pos = (mach64->accel.err > 0) || ((mach64->accel.err == 0) && !(mach64->dst_cntl & DST_BRES_SIGN));\n    int      draw    = 1;\n    int      dx      = mach64->accel.dst_x;\n\n',
     '    uint32_t old_dest_dat;\n    int      dx;\n    int      draw = mach64_line_draws(mach64, &dx);\n\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '            break;\n    }\n\n    /* Polygon outline: one pixel a scan line, none for horizontal lines,\n       saturated to the left scissor (RRG 3-47). */\n    if (mach64->dst_cntl & DST_POLYGON_EN) {\n        draw = (mach64->dst_cntl & DST_Y_MAJOR) || err_pos;\n        if (dx < mach64->accel.sc_left)\n            dx = mach64->accel.sc_left;\n    }\n\n    if ((mach64->accel.x_count == 1) && !(mach64->dst_cntl & DST_LAST_PEL))\n        draw = 0;\n\n    if (draw && (dx >= mach64->accel.sc_left) && (dx <= mach64->accel.sc_right) &&\n',
     '            break;\n    }\n\n    if (draw && (dx >= mach64->accel.sc_left) && (dx <= mach64->accel.sc_right) &&\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '        WRITE(mach64->accel.dst_offset + (mach64->accel.dst_y * mach64->accel.dst_pitch) + dx, mach64->accel.dst_size);\n    }\n\n    if (--mach64->accel.x_count <= 0) {\n',
     "        WRITE(mach64->accel.dst_offset + (mach64->accel.dst_y * mach64->accel.dst_pitch) + dx, mach64->accel.dst_size);\n    }\n}\n\n/* The engine's position moved on past a line's pixel. Returns 1 when the\n   line has finished. */\nstatic int\nmach64_line_advance(mach64_t *mach64)\n{\n    const int err_pos = mach64_line_err_pos(mach64);\n\n    if (--mach64->accel.x_count <= 0) {\n"),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '{\n    if (mach64->accel.op == OP_LINE)\n        return mach64_line_pixel(mach64, host);\n    return mach64_rect_pixel(mach64, host);\n}\n',
     '{\n    if (mach64->accel.op == OP_LINE) {\n        mach64_line_draw(mach64, host);\n        return mach64_line_advance(mach64);\n    }\n    mach64_rect_draw(mach64, host);\n    return mach64_rect_advance(mach64);\n}\n\n/* ---- KairoX86#237: the 2D engine on the GPU (86box/kairo_gpu_seg.h; core/kairo/shaders/mach64_2d.comp) ----\n\n   With Hardware acceleration on, an operation is recorded where it starts (its record from the engine\'s state) and\n   its rows (a rectangle\'s) or pixels (a line\'s) as the engine walks them, instead of drawn: all of them at once\n   when nothing comes from the host, else as the host\'s data feeds them, a rectangle\'s row once complete. The\n   engine\'s walk (mach64_rect_advance, mach64_line_advance) stays the CPU\'s. A drain records the row being fed so\n   far first (mach64_2d_flush), and an operation that outlives a drain records itself again. */\n\ntypedef struct mach64_2d_gpu_t {\n    kairo_seg_t *seg;\n    mutex_t     *lock;\n    uint32_t     record[M2_WORDS];\n    uint64_t     generation; /* the batch\'s drains when the record went in */\n    int          issued;     /* the record is in the batch (for this generation) */\n    int          host;       /* a rectangle fed from the host: rows still to come */\n    int          row;        /* its row being fed */\n    int          row_done;   /* pixels of it fed */\n    int          row_flushed; /* of them recorded */\n    int          row_appended; /* of them in the stream for the record in the batch */\n    uint32_t     values[8192];\n} mach64_2d_gpu_t;\n\n/* The record in the batch, again after a drain: a rectangle\'s host data restarts at the row being fed */\nstatic void\nmach64_2d_issue(mach64_2d_gpu_t *g, int in_order)\n{\n    uint32_t *op = kairo_seg_op(g->seg, in_order);\n\n    g->generation = kairo_seg_generation(g->seg);\n    g->issued     = 1;\n    if (g->host) {\n        g->record[M2_HOST] = kairo_seg_stream(g->seg, NULL, 0) - (uint32_t) g->row * g->record[M2_WIDTH];\n        g->row_appended    = 0;\n    }\n    memcpy(op, g->record, sizeof(g->record));\n}\n\nstatic void\nmach64_2d_current(mach64_2d_gpu_t *g)\n{\n    if (!g->issued || (kairo_seg_generation(g->seg) != g->generation))\n        mach64_2d_issue(g, g->record[M2_FLAGS] >> 31);\n}\n\n/* A rectangle\'s pixels [p0, p1) of row r, inside the scissors */\nstatic void\nmach64_2d_rect_row(mach64_t *mach64, mach64_2d_gpu_t *g, int r, int p0, int p1)\n{\n    const int *rec  = (const int *) g->record;\n    const int  xinc = rec[M2_XINC];\n    const int  y    = rec[M2_DST_Y] + r * rec[M2_YINC];\n    const int  bits = mach64_pix_bits(mach64->accel.dst_size);\n    int        lo, hi;\n\n    if ((y < rec[M2_SC_TOP]) || (y > rec[M2_SC_BOTTOM]))\n        return;\n    if (xinc > 0) {\n        lo = rec[M2_SC_LEFT] - rec[M2_DST_X];\n        hi = rec[M2_SC_RIGHT] - rec[M2_DST_X] + 1;\n    } else {\n        lo = rec[M2_DST_X] - rec[M2_SC_RIGHT];\n        hi = rec[M2_DST_X] - rec[M2_SC_LEFT] + 1;\n    }\n    if (p0 < lo)\n        p0 = lo;\n    if (p1 > hi)\n        p1 = hi;\n    if (p0 >= p1)\n        return;\n    const uint32_t px = g->record[M2_DST_OFFSET] + (uint32_t) y * g->record[M2_DST_PITCH] + (uint32_t) (rec[M2_DST_X] + p0 * xinc);\n    kairo_seg_add(g->seg, (uint32_t) r, (uint32_t) p0, (uint32_t) (p1 - p0),\n                  (uint32_t) ((uint64_t) px * (uint64_t) bits) & (((mach64->vram_mask + 1) << 3) - 1), (uint32_t) bits, xinc);\n}\n\n/* A line\'s pixel at the engine\'s position, if it draws one */\nstatic void\nmach64_2d_line_pixel(mach64_t *mach64, mach64_2d_gpu_t *g, uint32_t host)\n{\n    int dx;\n\n    if (!mach64_line_draws(mach64, &dx) || (dx < mach64->accel.sc_left) || (dx > mach64->accel.sc_right) ||\n        (mach64->accel.dst_y < mach64->accel.sc_top) || (mach64->accel.dst_y > mach64->accel.sc_bottom))\n        return;\n    const uint32_t words[M2_LINE_PIXEL_WORDS] = { (uint32_t) mach64->accel.dst_x, (uint32_t) dx, (uint32_t) mach64->accel.dst_y,\n                                                  (uint32_t) mach64->accel.src_x, host };\n    const int      bits = mach64_pix_bits(mach64->accel.dst_size);\n    const uint32_t px   = mach64->accel.dst_offset + (uint32_t) mach64->accel.dst_y * mach64->accel.dst_pitch + (uint32_t) dx;\n\n    thread_wait_mutex(g->lock);\n    mach64_2d_current(g);\n    kairo_seg_add(g->seg, kairo_seg_stream(g->seg, words, M2_LINE_PIXEL_WORDS), 0, 1,\n                  (uint32_t) ((uint64_t) px * (uint64_t) bits) & (((mach64->vram_mask + 1) << 3) - 1), (uint32_t) bits, 1);\n    thread_release_mutex(g->lock);\n}\n\n/* The row being fed from the host, recorded up to its pixel p1 (the lock held) */\nstatic void\nmach64_2d_host_row(mach64_t *mach64, mach64_2d_gpu_t *g, int p1)\n{\n    mach64_2d_current(g);\n    if (p1 > g->row_appended) {\n        kairo_seg_stream(g->seg, &g->values[g->row_appended], (uint32_t) (p1 - g->row_appended));\n        g->row_appended = p1;\n    }\n    if (p1 > g->row_flushed) {\n        mach64_2d_rect_row(mach64, g, g->row, g->row_flushed, p1);\n        g->row_flushed = p1;\n    }\n}\n\n/* Before every drain of the batch: the row being fed so far */\nstatic void\nmach64_2d_flush(void *ctx)\n{\n    mach64_t        *mach64 = ctx;\n    mach64_2d_gpu_t *g      = mach64->k_2d;\n\n    thread_wait_mutex(g->lock);\n    if (g->host && (g->row_done > g->row_flushed))\n        mach64_2d_host_row(mach64, g, g->row_done);\n    thread_release_mutex(g->lock);\n}\n\n/* Bytes [lo, hi) of video memory as a pixel range [p_lo, p_hi] of a width at an offset (pixel addresses) */\nstatic void\nmach64_2d_bytes(uint32_t p_lo, uint32_t p_hi, int size, uint64_t *lo, uint64_t *hi)\n{\n    const uint64_t bits = (uint64_t) mach64_pix_bits(size);\n\n    *lo = ((uint64_t) p_lo * bits) >> 3;\n    *hi = (((uint64_t) p_hi + 1) * bits + 7) >> 3;\n}\n\nstatic int\nmach64_2d_overlap(uint64_t a_lo, uint64_t a_hi, uint64_t b_lo, uint64_t b_hi)\n{\n    return (a_lo < b_hi) && (b_lo < a_hi);\n}\n\n/* The operation the engine has just started, recorded: the record from the engine\'s state, and the memory it\n   draws on and reads. In order when it reads what it draws on or its rows run past the end of video memory; a\n   batch that draws on what it reads is drawn first. */\nstatic void\nmach64_2d_begin(mach64_t *mach64)\n{\n    mach64_2d_gpu_t *g    = mach64->k_2d;\n    uint32_t        *rec  = g->record;\n    const int        line = (mach64->accel.op == OP_LINE);\n    const int        rect_rows = line ? 0 : mach64->accel.dst_height;\n    const int        width     = line ? 0 : mach64->accel.dst_width;\n    const uint64_t   vram_size = (uint64_t) mach64->vram_mask + 1;\n    int              in_order  = 0;\n    int              reads_src = ((mach64->accel.source_fg == SRC_BLITSRC) || (mach64->accel.source_bg == SRC_BLITSRC) ||\n                                  (mach64->accel.source_mix == MONO_SRC_BLITSRC));\n    int              poly      = !line && (mach64->dst_cntl & DST_POLYGON_EN);\n    int              per       = 1;\n\n    memset(rec, 0, sizeof(g->record));\n    rec[M2_FLAGS] = (line ? M2F_LINE : 0) | ((mach64->dst_cntl & DST_24_ROT_EN) ? M2F_ROT : 0) |\n                    ((mach64->dp_pix_width & DP_BYTE_PIX_ORDER) ? M2F_PIX_ORDER : 0) |\n                    ((mach64->src_cntl & SRC_LINEAR_EN) ? M2F_LINEAR : 0) | (poly ? M2F_POLYGON : 0) |\n                    (((mach64->type >= MACH64_CT) && (mach64->dst_cntl & DST_POLYGON_RTEDGE_DIS)) ? M2F_RTEDGE : 0) |\n                    (((mach64->accel.src_size == 0) && (mach64->type == MACH64_VT3) && (mach64->src_cntl & SRC_8x8x8_BRUSH)) ? M2F_BRUSH : 0) |\n                    (((mach64->src_cntl & (SRC_PATT_ROT_EN | SRC_PATT_EN)) == (SRC_PATT_ROT_EN | SRC_PATT_EN)) ? M2F_PATT_ROT : 0) |\n                    ((mach64->src_cntl & SRC_PATT_EN) ? M2F_PATT_EN : 0) | (mach64_mem_bndry_en(mach64) ? M2F_BNDRY : 0);\n    rec[M2_DST_SIZE]    = (uint32_t) mach64->accel.dst_size;\n    rec[M2_SRC_SIZE]    = (uint32_t) mach64->accel.src_size;\n    rec[M2_DST_OFFSET]  = mach64->accel.dst_offset;\n    rec[M2_DST_PITCH]   = mach64->accel.dst_pitch;\n    rec[M2_SRC_OFFSET]  = mach64->accel.src_offset;\n    rec[M2_SRC_PITCH]   = mach64->accel.src_pitch;\n    rec[M2_POLY_OFFSET] = mach64->accel.poly_offset;\n    rec[M2_MIX_FG]      = (uint32_t) mach64->accel.mix_fg;\n    rec[M2_MIX_BG]      = (uint32_t) mach64->accel.mix_bg;\n    rec[M2_SOURCE_FG]   = (uint32_t) mach64->accel.source_fg;\n    rec[M2_SOURCE_BG]   = (uint32_t) mach64->accel.source_bg;\n    rec[M2_SOURCE_MIX]  = (uint32_t) mach64->accel.source_mix;\n    rec[M2_PAT_CNTL]    = mach64->pat_cntl;\n    for (int y = 0; y < 8; y++)\n        for (int x = 0; x < 8; x++) {\n            if (mach64->accel.pattern[y][x])\n                rec[M2_PATTERN + (y >> 2)] |= 1u << (((y & 3) << 3) + x);\n            rec[M2_CLR8X8 + ((y * 8 + x) >> 2)] |= (uint32_t) mach64->accel.pattern_clr8x8[y][x] << (((y * 8 + x) & 3) * 8);\n        }\n    for (int i = 0; i < 8; i++) {\n        rec[M2_CLR4X2 + (i >> 2)] |= (uint32_t) mach64->accel.pattern_clr4x2[i >> 2][i & 3] << ((i & 3) * 8);\n        rec[M2_CLR8X1 + (i >> 2)] |= (uint32_t) mach64->accel.pattern_clr8x1[i] << ((i & 3) * 8);\n    }\n    rec[M2_SC_LEFT]    = (uint32_t) mach64->accel.sc_left;\n    rec[M2_SC_RIGHT]   = (uint32_t) mach64->accel.sc_right;\n    rec[M2_SC_TOP]     = (uint32_t) mach64->accel.sc_top;\n    rec[M2_SC_BOTTOM]  = (uint32_t) mach64->accel.sc_bottom;\n    rec[M2_FG]         = mach64->accel.dp_frgd_clr;\n    rec[M2_BG]         = mach64->accel.dp_bkgd_clr;\n    rec[M2_WRITE_MASK] = mach64->accel.write_mask;\n    rec[M2_CMP_CLR]    = mach64->accel.clr_cmp_clr;\n    rec[M2_CMP_MASK]   = mach64->accel.clr_cmp_mask;\n    rec[M2_CMP_FN]     = (uint32_t) mach64->accel.clr_cmp_fn;\n    rec[M2_CMP_SRC]    = mach64->accel.clr_cmp_src ? 1 : 0;\n    rec[M2_XINC]       = (uint32_t) mach64->accel.xinc;\n    rec[M2_YINC]       = (uint32_t) mach64->accel.yinc;\n    rec[M2_ROT0]       = (uint32_t) mach64->accel.rot0;\n    rec[M2_DST_X]      = (uint32_t) mach64->accel.dst_x_start;\n    rec[M2_DST_Y]      = (uint32_t) mach64->accel.dst_y_start;\n    rec[M2_WIDTH]      = (uint32_t) width;\n    rec[M2_SX1]        = (uint32_t) mach64->accel.src_x_start;\n    rec[M2_SY1]        = (uint32_t) mach64->accel.src_y_start;\n    rec[M2_SX2]        = (uint32_t) mach64_sext((mach64->src_y_x_start >> 16) & 0x1fff, 13);\n    rec[M2_SY2]        = (uint32_t) mach64_sext(mach64->src_y_x_start & 0x7fff, 15);\n    rec[M2_W1]         = (uint32_t) mach64->accel.src_width1;\n    rec[M2_H1]         = (uint32_t) mach64->accel.src_height1;\n    rec[M2_W2]         = (uint32_t) mach64->accel.src_width2;\n    rec[M2_H2]         = (uint32_t) mach64->accel.src_height2;\n    rec[M2_CHAIN]      = mach64->chain_mask;\n    rec[M2_BNDRY]      = mach64_mem_bndry(mach64);\n    rec[M2_LINE_SRC_Y] = (uint32_t) mach64->accel.src_y;\n\n    /* A linear source\'s rows: the first ends where a byte-aligned 1 or 4 bpp source rounds it up to, the rest a whole\n       aligned row on (mach64_rect_advance) */\n    if (mach64->src_cntl & SRC_BYTE_ALIGN) {\n        const int sz = ((mach64->accel.source_mix == MONO_SRC_BLITSRC) || (mach64->accel.src_size == WIDTH_1BIT)) ? WIDTH_1BIT : mach64->accel.src_size;\n        per          = (sz == WIDTH_1BIT) ? 8 : (sz == WIDTH_4BIT) ? 2 : 1;\n    }\n    rec[M2_LIN_L1]   = (uint32_t) (((mach64->accel.src_offset + (uint32_t) width + (uint32_t) per - 1) & ~((uint32_t) per - 1)) - mach64->accel.src_offset);\n    rec[M2_LIN_STEP] = (uint32_t) ((width + per - 1) & ~(per - 1));\n\n    /* What it draws on: a rectangle\'s rows, a line\'s square around its start */\n    uint64_t d_lo, d_hi;\n    {\n        int y_lo = line ? (mach64->accel.dst_y - mach64->accel.x_count) : mach64->accel.dst_y_start;\n        int y_hi = line ? (mach64->accel.dst_y + mach64->accel.x_count) : (mach64->accel.dst_y_start + (rect_rows - 1) * mach64->accel.yinc);\n        int x_lo = line ? (mach64->accel.dst_x - mach64->accel.x_count) : mach64->accel.dst_x_start;\n        int x_hi = line ? (mach64->accel.dst_x + mach64->accel.x_count) : (mach64->accel.dst_x_start + (width - 1) * mach64->accel.xinc);\n        if (y_lo > y_hi) {\n            int t = y_lo;\n            y_lo  = y_hi;\n            y_hi  = t;\n        }\n        if (x_lo > x_hi) {\n            int t = x_lo;\n            x_lo  = x_hi;\n            x_hi  = t;\n        }\n        const int64_t p_lo = (int64_t) mach64->accel.dst_offset + (int64_t) y_lo * mach64->accel.dst_pitch + x_lo;\n        const int64_t p_hi = (int64_t) mach64->accel.dst_offset + (int64_t) y_hi * mach64->accel.dst_pitch + x_hi;\n        if ((p_lo < 0) || (((uint64_t) p_hi * mach64_pix_bits(mach64->accel.dst_size)) >> 3) >= vram_size)\n            in_order = 1;\n        mach64_2d_bytes((uint32_t) (p_lo < 0 ? 0 : p_lo), (uint32_t) (p_hi < 0 ? 0 : p_hi), mach64->accel.dst_size, &d_lo, &d_hi);\n    }\n\n    /* What it draws on, where the batch\'s operations read (before its own reads go in) */\n    kairo_seg_draws(g->seg, (uint32_t) d_lo, (uint32_t) (d_hi - d_lo));\n\n    /* What it reads: its source (a line\'s around its start, a rectangle\'s every row), the polygon\'s boundary */\n    for (int pass = 0; pass < 2; pass++) {\n        const int reads = pass ? poly : reads_src;\n        if (!reads)\n            continue;\n        const uint32_t base = pass ? mach64->accel.poly_offset : mach64->accel.src_offset;\n        const int      size = pass ? WIDTH_1BIT : ((mach64->accel.source_mix == MONO_SRC_BLITSRC) && (mach64->accel.source_fg != SRC_BLITSRC) && (mach64->accel.source_bg != SRC_BLITSRC)) ? WIDTH_1BIT : mach64->accel.src_size;\n        int64_t        p_lo, p_hi;\n        if (line) {\n            p_lo = (int64_t) base + (int64_t) mach64->accel.src_y * mach64->accel.src_pitch + mach64->accel.src_x - mach64->accel.x_count;\n            p_hi = p_lo + 2 * (int64_t) mach64->accel.x_count;\n        } else if (mach64->src_cntl & SRC_LINEAR_EN) {\n            /* the linear position\'s last value; the boundary of a polygon on the row its source Y stays on */\n            const int64_t end = (rect_rows > 1 ? (int64_t) rec[M2_LIN_L1] + (int64_t) (rect_rows - 2) * (int64_t) rec[M2_LIN_STEP] : 0) + width;\n            p_lo = (int64_t) base + (pass ? (int64_t) mach64->accel.src_y_start * mach64->accel.src_pitch : 0);\n            p_hi = p_lo + end;\n        } else {\n            int sy_lo = 0x7fffffff, sy_hi = -0x7fffffff, sx_lo = 0x7fffffff, sx_hi = -0x7fffffff;\n            for (int r = 0; r < rect_rows; r++) {\n                const int c1 = (mach64->src_cntl & SRC_PATT_EN) ? mach64->accel.src_height1 : 0x7fffffff;\n                int       sy;\n                if (!(mach64->src_cntl & SRC_PATT_EN) || (r < (c1 < 1 ? 1 : c1)))\n                    sy = mach64->accel.src_y_start + r * mach64->accel.yinc;\n                else {\n                    const int rot = (rec[M2_FLAGS] & M2F_PATT_ROT) != 0;\n                    const int c   = rot ? mach64->accel.src_height2 : mach64->accel.src_height1;\n                    sy = (rot ? (int) rec[M2_SY2] : mach64->accel.src_y_start) + ((r - (c1 < 1 ? 1 : c1)) % (c < 1 ? 1 : c)) * mach64->accel.yinc;\n                }\n                sy_lo = (sy < sy_lo) ? sy : sy_lo;\n                sy_hi = (sy > sy_hi) ? sy : sy_hi;\n            }\n            for (int p = 0; p < width; p++) {\n                const int c1 = (mach64->accel.src_width1 < 1) ? 1 : mach64->accel.src_width1;\n                int       sx;\n                if (p < c1)\n                    sx = mach64->accel.src_x_start + p * mach64->accel.xinc;\n                else {\n                    const int rot = (rec[M2_FLAGS] & M2F_PATT_ROT) != 0;\n                    const int c   = rot ? mach64->accel.src_width2 : mach64->accel.src_width1;\n                    sx = (rot ? (int) rec[M2_SX2] : mach64->accel.src_x_start) + ((p - c1) % (c < 1 ? 1 : c)) * mach64->accel.xinc;\n                }\n                sx_lo = (sx < sx_lo) ? sx : sx_lo;\n                sx_hi = (sx > sx_hi) ? sx : sx_hi;\n            }\n            if (rect_rows <= 0 || width <= 0)\n                continue;\n            p_lo = (int64_t) base + (int64_t) sy_lo * mach64->accel.src_pitch + sx_lo;\n            p_hi = (int64_t) base + (int64_t) sy_hi * mach64->accel.src_pitch + sx_hi;\n        }\n        uint64_t s_lo, s_hi;\n        if ((p_lo < 0) || (((uint64_t) p_hi * mach64_pix_bits(size)) >> 3) >= vram_size) {\n            s_lo = 0;\n            s_hi = vram_size;\n        } else\n            mach64_2d_bytes((uint32_t) p_lo, (uint32_t) p_hi, size, &s_lo, &s_hi);\n        if (mach64_2d_overlap(s_lo, s_hi, d_lo, d_hi))\n            in_order = 1;\n        if (kairo_seg_reads_pending(g->seg, (uint32_t) s_lo, (uint32_t) (s_hi - s_lo)))\n            kairo_seg_drain(g->seg);\n        kairo_seg_reads(g->seg, (uint32_t) s_lo, (uint32_t) (s_hi - s_lo));\n    }\n    /* The brush the VT3 took from video memory at the start (mach64_start_fill) */\n    if (in_order)\n        rec[M2_FLAGS] |= 1u << 31;\n\n    thread_wait_mutex(g->lock);\n    g->host         = !line && mach64->accel.source_host;\n    g->row          = 0;\n    g->row_done     = 0;\n    g->row_flushed  = 0;\n    g->row_appended = 0;\n    g->issued       = 0;\n    mach64_2d_current(g);\n    if (!line && !g->host) {\n        for (int r = 0; r < rect_rows; r++)\n            mach64_2d_rect_row(mach64, g, r, 0, width);\n    }\n    thread_release_mutex(g->lock);\n}\n\n/* A rectangle\'s host pixel, at the engine\'s position: recorded with its row, then the engine walks on */\nstatic int\nmach64_2d_host_pixel(mach64_t *mach64, uint32_t host)\n{\n    mach64_2d_gpu_t *g = mach64->k_2d;\n    int              finished;\n\n    thread_wait_mutex(g->lock);\n    if (g->row_done < (int) (sizeof(g->values) / sizeof(g->values[0])))\n        g->values[g->row_done] = host;\n    g->row_done++;\n    thread_release_mutex(g->lock);\n    finished = mach64_rect_advance(mach64);\n    if (mach64->accel.row_ended || finished) {\n        thread_wait_mutex(g->lock);\n        mach64_2d_host_row(mach64, g, g->row_done);\n        g->row++;\n        g->row_done     = 0;\n        g->row_flushed  = 0;\n        g->row_appended = 0;\n        if (finished)\n            g->host = 0;\n        thread_release_mutex(g->lock);\n    }\n    return finished;\n}\n\n/* The operation under way, on the GPU: as mach64_blit runs it */\nstatic void\nmach64_2d_blit(uint32_t cpu_dat, int count, mach64_t *mach64)\n{\n    uint32_t pix[32];\n    uint8_t  byte_of[32];\n    int      n;\n\n    if (count == -1) {\n        if (mach64->accel.op == OP_LINE) {\n            do\n                mach64_2d_line_pixel(mach64, mach64->k_2d, 0);\n            while (mach64->accel.busy && !mach64_line_advance(mach64));\n        } else {\n            /* every row went in at the start */\n            mach64->accel.poly_draw = 0;\n            mach64->accel.row_ended = 1;\n            mach64_rect_finish(mach64);\n        }\n        return;\n    }\n\n    n = mach64_host_pixels(mach64, cpu_dat, count, pix, byte_of);\n    for (int i = 0; (i < n) && mach64->accel.busy; i++) {\n        /* HOST_BYTE_ALIGN, as mach64_blit skips */\n        if (mach64->accel.row_ended) {\n            mach64->accel.row_ended = 0;\n            if ((mach64->host_cntl & HOST_BYTE_ALIGN) && (mach64->accel.op == OP_RECT) && (i > 0)) {\n                int w = (mach64->accel.source_mix == MONO_SRC_HOST) ? 1 : mach64_pix_bits(mach64->accel.host_size);\n\n                if (w < 8) {\n                    while ((i < n) && (byte_of[i] == byte_of[i - 1]))\n                        i++;\n                    if (i >= n)\n                        break;\n                }\n            }\n        }\n        if (mach64->accel.op == OP_LINE) {\n            mach64_2d_line_pixel(mach64, mach64->k_2d, pix[i]);\n            mach64_line_advance(mach64);\n        } else\n            mach64_2d_host_pixel(mach64, pix[i]);\n    }\n}\n\n/* KairoX86#237: the 2D engine\'s recorded work drawn first where something else meets the memory it draws on or\n   reads (no-ops in software) */\nvoid\nmach64_2d_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len)\n{\n    if (mach64->k_2d != NULL)\n        kairo_seg_touch(((mach64_2d_gpu_t *) mach64->k_2d)->seg, addr & mach64->vram_mask, len);\n}\n\n/* Both engines\' recorded work drawn first where something else meets its memory */\nvoid\nmach64_kairo_touch(mach64_t *mach64, uint32_t addr, uint32_t len)\n{\n    mach64_3d_kairo_touch(mach64, addr, len);\n    mach64_2d_kairo_touch(mach64, addr, len);\n}\n\nvoid\nmach64_2d_kairo_drain(mach64_t *mach64)\n{\n    if (mach64->k_2d != NULL)\n        kairo_seg_drain(((mach64_2d_gpu_t *) mach64->k_2d)->seg);\n}\n\nvoid\nmach64_2d_kairo_open(mach64_t *mach64)\n{\n    mach64_2d_gpu_t *g = calloc(1, sizeof(mach64_2d_gpu_t));\n\n    if (g == NULL)\n        fatal("Mach64 2D on the GPU: no memory\\n");\n    g->seg      = kairo_mach64_2d_open(mach64->svga.vram, mach64->vram_mask, mach64->svga.changedvram,\n                                       &mach64->svga.monitor->mon_changeframecount);\n    g->lock     = thread_create_mutex();\n    mach64->k_2d = g;\n    kairo_seg_set_flush(g->seg, mach64_2d_flush, mach64);\n}\n\nvoid\nmach64_2d_kairo_close(mach64_t *mach64)\n{\n    mach64_2d_gpu_t *g = mach64->k_2d;\n\n    if (g == NULL)\n        return;\n    kairo_seg_close(g->seg);\n    thread_close_mutex(g->lock);\n    free(g);\n    mach64->k_2d = NULL;\n}\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    mach64_3d_kairo_drain(mach64); /* KairoX86#237: rows recorded since the operation started */\n\n',
     '    mach64_3d_kairo_drain(mach64); /* KairoX86#237: rows recorded since the operation started */\n    if (mach64->k_2d != NULL) {\n        /* KairoX86#237: recorded for the GPU */\n        mach64_2d_blit(cpu_dat, count, mach64);\n        return;\n    }\n\n'),
    ('86box/src/video/vid_ati_mach64_accel.c',
     '    mach64_3d_kairo_drain(mach64); /* KairoX86#237: the context is read from video memory */\n\n',
     '    mach64_3d_kairo_drain(mach64); /* KairoX86#237: the context is read from video memory */\n    mach64_2d_kairo_drain(mach64);\n\n'),
]

# KairoX86#296: the P9100's oversized quad outline steps as Bresenham does, both tests taking the error as the step
# began; testing the updated error let the walk miss its end point and loop forever.
KAIROX86_P9100_OUTLINE = [
    ('86box/src/video/vid_p9100.c',
     '            break;\n        if ((2 * err) >= dy) {\n            err += dy;\n            x0 += sx;\n        }\n        if ((2 * err) <= dx) {\n            err += dx;\n',
     '            break;\n        /* KairoX86#296: both tests take the error as the step began, or the walk can miss its end and run away */\n        const int e2 = 2 * err;\n        if (e2 >= dy) {\n            err += dy;\n            x0 += sx;\n        }\n        if (e2 <= dx) {\n            err += dx;\n'),
]

# KairoX86#266: the Weitek Power 9100's drawing engines on the GPU (86box/kairo_gpu_p9100.h, an added file,
# core/kairo/gpu_p9100.c, core/kairo/shaders/p9100.comp), on the drawing engines' shared batches (kairo_gpu_seg.h).
# With Hardware acceleration on, the native engine's quads, blits, pixel1 and pixel8 runs and the W5286 GHA's blits
# and lines are recorded where they run, their rows as runs of bytes (native) or longwords (GHA).
KAIROX86_GPU_P9100 = [
    ('86box/src/video/vid_p9100.c',
     '#include <86box/vid_svga.h>\n#include <86box/vid_svga_render.h>\n',
     '#include <86box/vid_svga.h>\n#include <86box/kairo_gpu.h>       /* KairoX86#266 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_p9100.h>\n#include <86box/vid_svga_render.h>\n'),
    ('86box/src/video/vid_p9100.c',
     '#define STATUS_QUAD_INTERSECTS 0x00000001\n\n',
     "#define STATUS_QUAD_INTERSECTS 0x00000001\n\n/* KairoX86#266: the drawing engines' batch on the GPU */\ntypedef struct p9100_gpu_t {\n    kairo_seg_t *seg;\n    uint32_t     record[P9_WORDS];\n    uint64_t     generation; /* the batch's drains when the record went in */\n    int          issued;\n    int          in_order;\n} p9100_gpu_t;\n\n"),
    ('86box/src/video/vid_p9100.c',
     '    uint32_t pattern[8];\n} p9100_t;\n',
     '    uint32_t pattern[8];\n\n    p9100_gpu_t *k_gpu; /* KairoX86#266: NULL in software */\n} p9100_t;\n'),
    ('86box/src/video/vid_p9100.c',
     '#define GHA_PACKED16 3\n\n',
     "#define GHA_PACKED16 3\n\n/* KairoX86#266: an operation in the batch: the record again only where it differs or the batch has been drawn */\nstatic void\np9100_k_op(p9100_t *p9100, const uint32_t *rec, int in_order)\n{\n    p9100_gpu_t *g = p9100->k_gpu;\n\n    kairo_seg_make_room(g->seg);\n    if (g->issued && (g->in_order == in_order) && (g->generation == kairo_seg_generation(g->seg)) && !memcmp(g->record, rec, sizeof(g->record)))\n        return;\n    memcpy(kairo_seg_op(g->seg, in_order), rec, sizeof(g->record));\n    memcpy(g->record, rec, sizeof(g->record));\n    g->generation = kairo_seg_generation(g->seg);\n    g->in_order   = in_order;\n    g->issued     = 1;\n}\n\n/* Segments of a run from addr, each a stretch video memory does not wrap in: units of size bytes (a power of 2),\n   pixel numbers first + i */\nstatic void\np9100_k_run(p9100_t *p9100, uint32_t row, int first, int count, uint32_t addr, int size, int dir)\n{\n    const uint32_t units = (p9100->vram_mask + 1) / size;\n\n    while (count > 0) {\n        const uint32_t lo = (addr & p9100->vram_mask) / size;\n        const int      n  = MIN((uint32_t) count, (dir > 0) ? (units - lo) : (lo + 1));\n\n        kairo_seg_add(p9100->k_gpu->seg, row, (uint32_t) first, (uint32_t) n, lo * size * 8, size * 8, dir);\n        first += (size == 1) ? (n * dir) : n; /* a byte run's numbers follow memory; a GHA row's count its longwords */\n        addr += (uint32_t) (n * dir * size);\n        count -= n;\n    }\n}\n\n/* Whole video memory when a range runs outside it */\nstatic void\np9100_k_range(const p9100_t *p9100, int64_t *lo, int64_t *hi)\n{\n    if ((*lo < 0) || (*hi > ((int64_t) p9100->vram_mask + 1))) {\n        *lo = 0;\n        *hi = (int64_t) p9100->vram_mask + 1;\n    }\n}\n\n/* What an operation reads and draws: a batch meeting either is drawn first */\nstatic void\np9100_k_reads(p9100_t *p9100, int64_t lo, int64_t hi)\n{\n    kairo_seg_t *seg = p9100->k_gpu->seg;\n\n    if (kairo_seg_reads_pending(seg, (uint32_t) lo, (uint32_t) (hi - lo)))\n        kairo_seg_drain(seg);\n    kairo_seg_reads(seg, (uint32_t) lo, (uint32_t) (hi - lo));\n}\n\n"),
    ('86box/src/video/vid_p9100.c',
     '\n    for (int y = 0; y < vt; y++) {\n',
     "\n    if (p9100->k_gpu != NULL) {\n        /* KairoX86#266: the record, what its rows read and draw, then its rows' places */\n        kairo_seg_t *seg = p9100->k_gpu->seg;\n        uint32_t     rec[P9_WORDS];\n        int64_t      s_lo = INT64_MAX, s_hi = INT64_MIN, d_lo = INT64_MAX, d_hi = INT64_MIN;\n        uint32_t     rs = src, rd = dst;\n\n        memset(rec, 0, sizeof(rec));\n        rec[P9_KIND]    = P9K_GHA_BLIT;\n        memcpy(&rec[P9_INS], ins, 16);\n        rec[P9_MODE]    = mode;\n        rec[P9_BG]      = bg;\n        rec[P9_HT]      = ht;\n        rec[P9_STEP]    = (uint32_t) step;\n        rec[P9_ROT]     = rotcnt;\n        rec[P9_RMASK]   = rmask;\n        rec[P9_GPMASK]  = pmask;\n        rec[P9_BITMASK] = bitmask;\n        rec[P9_EXPAND]  = expand;\n        rec[P9_PPL]     = ppl;\n        for (int y = 0; y < vt; y++) {\n            const uint32_t bits = (rs << 5) + (((ins[0x0f] >> 3) & 1) << 4);\n            const int64_t  far  = (int64_t) (ht + 1) * step;\n            int64_t        lo, hi;\n\n            if (packed_expand && (expand == 3))\n                lo = hi = rs;\n            else if (packed_expand) {\n                lo = bits >> 5;\n                hi = (bits + (ht + 1) * ppl) >> 5;\n            } else {\n                lo = (int64_t) rs;\n                hi = (int64_t) rs + far + (is_long ? step : 0);\n            }\n            s_lo = MIN(s_lo, MIN(lo, hi));\n            s_hi = MAX(s_hi, MAX(lo, hi));\n            d_lo = MIN(d_lo, MIN((int64_t) rd, (int64_t) rd + far));\n            d_hi = MAX(d_hi, MAX((int64_t) rd, (int64_t) rd + far));\n            rd = rd + (uint32_t) far + dpitch;\n            if (packed_expand && (expand == 3))\n                rs = (rs & ~0x1f) | ((rs + step) & 0x1f);\n            else if (packed_expand)\n                rs = ((bits + (ht + 1) * ppl + 31) >> 5) + spitch;\n            else\n                rs = rs + (uint32_t) far + (is_long ? step : 0) + spitch;\n        }\n        s_lo *= 4;\n        s_hi = (s_hi + 1) * 4;\n        d_lo *= 4;\n        d_hi = (d_hi + 1) * 4;\n        if (vt <= 0)\n            return;\n        p9100_k_range(p9100, &s_lo, &s_hi);\n        p9100_k_range(p9100, &d_lo, &d_hi);\n        kairo_seg_draws(seg, (uint32_t) d_lo, (uint32_t) (d_hi - d_lo));\n        p9100_k_reads(p9100, s_lo, s_hi);\n        p9100_k_op(p9100, rec, (s_lo < d_hi) && (d_lo < s_hi));\n        for (int y = 0; y < vt; y++) {\n            const uint32_t bits     = (src << 5) + (((ins[0x0f] >> 3) & 1) << 4);\n            const uint32_t words[3] = { src, bits, dst };\n            const uint32_t at       = kairo_seg_stream(seg, words, 3);\n\n            p9100_k_run(p9100, at, 0, ht + 1, dst << 2, 4, step);\n            dst = dst + (uint32_t) ((ht + 1) * step) + dpitch;\n            if (packed_expand && (expand == 3))\n                src = (src & ~0x1f) | ((src + step) & 0x1f);\n            else if (packed_expand)\n                src = ((bits + (ht + 1) * ppl + 31) >> 5) + spitch;\n            else\n                src = src + (uint32_t) ((ht + 1) * step) + (is_long ? step : 0) + spitch;\n        }\n        return;\n    }\n\n    for (int y = 0; y < vt; y++) {\n"),
    ('86box/src/video/vid_p9100.c',
     '    for (int n = 0; steep ? (n < count) : (lw <= count); n++) {\n        uint32_t old = p9100_gha_read(p9100, addr);\n        int      minor;\n\n        if (!steep && (lw == count) && !(m & ins[6]))\n            break;\n\n        p9100_gha_write(p9100, addr, p9100_gha_rop(mode, ins, src, old), p9100_gha_nmask(mode, m) & pmask);\n\n',
     '    for (int n = 0; steep ? (n < count) : (lw <= count); n++) {\n        int      minor;\n\n        if (!steep && (lw == count) && !(m & ins[6]))\n            break;\n\n        if (p9100->k_gpu != NULL) {\n            /* KairoX86#266: the point, its longword and mask */\n            kairo_seg_t   *seg      = p9100->k_gpu->seg;\n            const uint32_t off      = (addr << 2) & p9100->vram_mask;\n            const uint32_t words[2] = { addr, p9100_gha_nmask(mode, m) & pmask };\n            uint32_t       rec[P9_WORDS];\n\n            memset(rec, 0, sizeof(rec));\n            rec[P9_KIND]  = P9K_GHA_LINE;\n            rec[P9_COLOR] = src;\n            rec[P9_MODE]  = mode;\n            memcpy(&rec[P9_INS], ins, 16);\n            kairo_seg_draws(seg, off, 4);\n            p9100_k_op(p9100, rec, 0);\n            kairo_seg_add(seg, kairo_seg_stream(seg, words, 2), 0, 1, off * 8, 32, 1);\n        } else {\n            uint32_t old = p9100_gha_read(p9100, addr);\n\n            p9100_gha_write(p9100, addr, p9100_gha_rop(mode, ins, src, old), p9100_gha_nmask(mode, m) & pmask);\n        }\n\n'),
    ('86box/src/video/vid_p9100.c',
     '\n        for (int w = 0; w < 4; w++) {\n',
     '\n        /* KairoX86#266: the queue is video memory */\n        if (p9100->k_gpu != NULL)\n            kairo_seg_touch(p9100->k_gpu->seg, (base << 2) & p9100->vram_mask, 16);\n        for (int w = 0; w < 4; w++) {\n'),
    ('86box/src/video/vid_p9100.c',
     '\n/* Quads are filled scan line by scan line. In X11 mode a pixel is touched\n',
     "\n/* KairoX86#266: a native operation's record from the engine's state */\nstatic void\np9100_k_record(const p9100_t *p9100, const p9100_draw_t *d, uint32_t *rec, int kind)\n{\n    memset(rec, 0, P9_WORDS * sizeof(uint32_t));\n    rec[P9_KIND]   = kind;\n    rec[P9_RASTER] = p9100->raster;\n    rec[P9_PMASK]  = p9100->pmask;\n    rec[P9_BPP]    = d->bpp;\n    rec[P9_PITCH]  = d->pitch;\n    for (int i = 0; i < 4; i++)\n        rec[P9_COLOR + i] = p9100->color[i];\n    rec[P9_PAT_X] = p9100->pat_originx;\n    rec[P9_PAT_Y] = p9100->pat_originy;\n    for (int i = 0; i < 8; i++)\n        rec[P9_PATTERN + i] = p9100->pattern[i];\n}\n\n/* Quads are filled scan line by scan line. In X11 mode a pixel is touched\n"),
    ('86box/src/video/vid_p9100.c',
     '    }\n\n    for (int y = ymin; y <= ymax; y++) {\n        int xs = lo[y - ymin];\n',
     '    }\n\n    if (p9100->k_gpu != NULL) {\n        /* KairoX86#266 */\n        uint32_t rec[P9_WORDS];\n        int64_t  m_lo = (int64_t) ymin * d.pitch;\n        int64_t  m_hi = ((int64_t) ymax + 1) * d.pitch;\n\n        p9100_k_record(p9100, &d, rec, P9K_COLOR);\n        p9100_k_range(p9100, &m_lo, &m_hi);\n        kairo_seg_draws(p9100->k_gpu->seg, (uint32_t) m_lo, (uint32_t) (m_hi - m_lo));\n        p9100_k_op(p9100, rec, 0);\n    }\n    for (int y = ymin; y <= ymax; y++) {\n        int xs = lo[y - ymin];\n'),
    ('86box/src/video/vid_p9100.c',
     '            xe = d.xmax;\n        for (int x = xs; x <= xe; x++)\n',
     '            xe = d.xmax;\n        if (p9100->k_gpu != NULL) {\n            if (xs <= xe)\n                p9100_k_run(p9100, (uint32_t) y | (1u << 16), xs * d.bpp, (xe - xs + 1) * d.bpp, ((uint32_t) y * d.pitch) + (xs * d.bpp), 1, 1);\n            continue;\n        }\n        for (int x = xs; x <= xe; x++)\n'),
    ('86box/src/video/vid_p9100.c',
     '    cmax = MIN(w - 1, d.xmax - dx);\n\n',
     '    cmax = MIN(w - 1, d.xmax - dx);\n\n    if (p9100->k_gpu != NULL) {\n        /* KairoX86#266: the rectangles it reads and draws meet only where their lines and columns both do */\n        kairo_seg_t *seg = p9100->k_gpu->seg;\n        uint32_t     rec[P9_WORDS];\n        int64_t      s_lo, s_hi, d_lo, d_hi;\n        int          meet;\n\n        if ((rmin > rmax) || (cmin > cmax))\n            return;\n        s_lo = (((int64_t) sy + rmin) * d.pitch) + sx + cmin;\n        s_hi = (((int64_t) sy + rmax) * d.pitch) + sx + cmax + 1;\n        d_lo = (((int64_t) dy + rmin) * d.pitch) + dx + cmin;\n        d_hi = (((int64_t) dy + rmax) * d.pitch) + dx + cmax + 1;\n        meet = ((sy + rmin) <= (dy + rmax)) && ((dy + rmin) <= (sy + rmax)) && ((sx + cmin) <= (dx + cmax)) && ((dx + cmin) <= (sx + cmax));\n        /* Rectangles wider than a line, or out of video memory: only their memory can say */\n        if ((s_lo < 0) || (s_hi > ((int64_t) p9100->vram_mask + 1)) || (d_hi > ((int64_t) p9100->vram_mask + 1)) ||\n            ((uint32_t) MAX(sx + cmax, dx + cmax) >= d.pitch) || (MIN(sx + cmin, dx + cmin) < 0))\n            meet = 1;\n        p9100_k_range(p9100, &s_lo, &s_hi);\n        p9100_k_range(p9100, &d_lo, &d_hi);\n        kairo_seg_draws(seg, (uint32_t) d_lo, (uint32_t) (d_hi - d_lo));\n        p9100_k_reads(p9100, s_lo, s_hi);\n        p9100_k_record(p9100, &d, rec, P9K_BLIT);\n        rec[P9_SX]       = (uint32_t) sx;\n        rec[P9_SY]       = (uint32_t) sy;\n        rec[P9_DX]       = (uint32_t) dx;\n        rec[P9_DY]       = (uint32_t) dy;\n        rec[P9_USES_PAT] = pat;\n        p9100_k_op(p9100, rec, meet);\n        for (int r = rmin; r <= rmax; r++) {\n            int row = (ydir > 0) ? r : (rmax + rmin - r);\n            int ty  = dy + row;\n            int tx  = dx + ((xdir > 0) ? cmin : cmax);\n\n            p9100_k_run(p9100, (uint32_t) ty, tx, cmax - cmin + 1, ((uint32_t) ty * d.pitch) + tx, 1, xdir);\n        }\n        return;\n    }\n\n'),
    ('86box/src/video/vid_p9100.c',
     '\n        if (!p9100_clipped(&d, x, y) && p9100_pattern(p9100, x / d.bpp, y, &pcol))\n            p9100_write_byte(p9100, addr, p9100_reg_byte(&d, pcol, addr - i, i), val >> (24 - (b << 3)),\n',
     '\n        if (p9100->k_gpu != NULL) {\n            /* KairoX86#266 */\n            if (!p9100_clipped(&d, x, y)) {\n                uint32_t rec[P9_WORDS];\n\n                p9100_k_record(p9100, &d, rec, P9K_PIXEL8);\n                kairo_seg_draws(p9100->k_gpu->seg, addr & p9100->vram_mask, 1);\n                p9100_k_op(p9100, rec, 0);\n                p9100_k_run(p9100, (uint32_t) y | (((val >> (24 - (b << 3))) & 0xff) << 16), x, 1, addr, 1, 1);\n            }\n        } else if (!p9100_clipped(&d, x, y) && p9100_pattern(p9100, x / d.bpp, y, &pcol))\n            p9100_write_byte(p9100, addr, p9100_reg_byte(&d, pcol, addr - i, i), val >> (24 - (b << 3)),\n'),
    ('86box/src/video/vid_p9100.c',
     '        if ((bit || !(p9100->raster & RASTER_PIX1_TRANSP)) && !p9100_clipped(&d, x, y) &&\n            !p9100_clipped(&db, x * d.bpp, y) && !p9100_clipped(&db, (x * d.bpp) + d.bpp - 1, y))\n            p9100_pixel(p9100, &d, x, y, p9100->color[bit]);\n\n',
     '        if ((bit || !(p9100->raster & RASTER_PIX1_TRANSP)) && !p9100_clipped(&d, x, y) &&\n            !p9100_clipped(&db, x * d.bpp, y) && !p9100_clipped(&db, (x * d.bpp) + d.bpp - 1, y)) {\n            if (p9100->k_gpu != NULL) {\n                /* KairoX86#266 */\n                const uint32_t addr = ((uint32_t) y * d.pitch) + (x * d.bpp);\n                uint32_t       rec[P9_WORDS];\n\n                p9100_k_record(p9100, &d, rec, P9K_COLOR);\n                kairo_seg_draws(p9100->k_gpu->seg, addr & p9100->vram_mask, d.bpp);\n                p9100_k_op(p9100, rec, 0);\n                p9100_k_run(p9100, (uint32_t) y | ((uint32_t) bit << 16), x * d.bpp, d.bpp, addr, 1, 1);\n            } else\n                p9100_pixel(p9100, &d, x, y, p9100->color[bit]);\n        }\n\n'),
    ('86box/src/video/vid_p9100.c',
     '    /* An empty bank leaves the bus to the power-up pull-ups. */\n    if (off < 0)\n',
     '    /* An empty bank leaves the bus to the power-up pull-ups. */\n    if ((off >= 0) && (p9100->k_gpu != NULL))\n        kairo_seg_touch(p9100->k_gpu->seg, (uint32_t) off, 4); /* KairoX86#266 */\n    if (off < 0)\n'),
    ('86box/src/video/vid_p9100.c',
     '        return;\n    val  = p9100_bswap(p9100_swap(val, !!(p9100->sysconfig & 0x2000), !!(p9100->sysconfig & 0x1000), !!(p9100->sysconfig & 0x0800)));\n',
     '        return;\n    if (p9100->k_gpu != NULL)\n        kairo_seg_touch(p9100->k_gpu->seg, (uint32_t) off, 4); /* KairoX86#266 */\n    val  = p9100_bswap(p9100_swap(val, !!(p9100->sysconfig & 0x2000), !!(p9100->sysconfig & 0x1000), !!(p9100->sysconfig & 0x0800)));\n'),
    ('86box/src/video/vid_p9100.c',
     '\nstatic void *\n',
     "\n/* KairoX86#266: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\np9100_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const p9100_t *p9100 = (const p9100_t *) svga->priv;\n\n    kairo_seg_touch(p9100->k_gpu->seg, addr & p9100->vram_mask, len);\n}\n\nstatic void *\n"),
    ('86box/src/video/vid_p9100.c',
     '    svga->vblank_start      = p9100_vblank_start;\n\n',
     '    svga->vblank_start      = p9100_vblank_start;\n\n    /* KairoX86#266: with Hardware acceleration on, the drawing engines on the GPU */\n    if (kairo_gpu_on) {\n        p9100->k_gpu = calloc(1, sizeof(p9100_gpu_t));\n        if (p9100->k_gpu == NULL)\n            fatal("P9100 on the GPU: no memory\\n");\n        p9100->k_gpu->seg = kairo_p9100_open(svga->vram, p9100->vram_mask, svga->changedvram, &svga->monitor->mon_changeframecount);\n        svga->kairo_touch = p9100_svga_touch;\n    }\n\n'),
    ('86box/src/video/vid_p9100.c',
     '\n    svga_close(&p9100->svga);\n',
     '\n    if (p9100->k_gpu != NULL) {\n        kairo_seg_close(p9100->k_gpu->seg); /* KairoX86#266 */\n        free(p9100->k_gpu);\n    }\n    svga_close(&p9100->svga);\n'),
]

# KairoX86#254: the Tseng Labs ET4000/W32 family's accelerator on the GPU (86box/kairo_gpu_et4000w32.h, an added file,
# core/kairo/gpu_et4000w32.c, core/kairo/shaders/et4000w32.comp), on the drawing engines' shared batches. The five walks'
# per-byte draw is one helper (et4000w32_draw_byte); with Hardware acceleration on it records each run of destination
# bytes the walk draws, with every byte's pattern, source and mix, and the batch is drawn where anything meets it.
KAIROX86_GPU_ET4000W32 = [
    ('86box/src/video/vid_et4000w32.c',
     '#include <86box/vid_svga_render.h>\n\n',
     '#include <86box/vid_svga_render.h>\n#include <86box/kairo_gpu.h> /* KairoX86#254 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_et4000w32.h>\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     '    volatile int busy;\n} et4000w32p_t;\n\n',
     "    volatile int busy;\n\n    struct et4000w32_gpu_t *k_gpu; /* KairoX86#254: the accelerator's batch on the GPU, NULL in software */\n} et4000w32p_t;\n\n/* KairoX86#254: the accelerator's batch, and the run of bytes its walk is drawing (kairo_seg_run) */\ntypedef struct et4000w32_gpu_t {\n    kairo_seg_t     *seg;\n    kairo_seg_run_t *run;\n    uint32_t         record[ET_WORDS];\n    uint64_t         generation; /* the batch's drains when the record went in */\n    int              issued;\n    int              in_order;\n} et4000w32_gpu_t;\n\n"),
    ('86box/src/video/vid_et4000w32.c',
     '                if (((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) < svga->vram_max) {\n                    svga->vram[((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) & et4000->vram_mask]                = val;\n',
     '                if (((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) < svga->vram_max) {\n                    if (et4000->k_gpu != NULL) /* KairoX86#254 */\n                        kairo_seg_touch(et4000->k_gpu->seg, ((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) & et4000->vram_mask, 1);\n                    svga->vram[((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) & et4000->vram_mask]                = val;\n'),
    ('86box/src/video/vid_et4000w32.c',
     '                return 0xff;\n\n',
     '                return 0xff;\n            if (et4000->k_gpu != NULL) /* KairoX86#254 */\n                kairo_seg_touch(et4000->k_gpu->seg, ((addr & 0x1fff) + et4000->mmu.base[et4000->bank]) & et4000->vram_mask, 1);\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     '\nstatic void\net4000w32_blit(int count, int cpu_input, uint32_t src_dat, uint32_t mix_dat, et4000w32p_t *et4000)\n{\n    svga_t *svga = &et4000->svga;\n    uint8_t pattern;\n    uint8_t source;\n    uint8_t dest;\n    uint8_t rop;\n    uint8_t out = 0;\n    int     mixmap;\n\n',
     "\n/* KairoX86#254: the run's operation in the batch (kairo_seg_run): the record again only where it differs or the batch\n   has been drawn */\nstatic void\net4000w32_k_op(void *priv, bool in_order)\n{\n    et4000w32p_t    *et4000 = (et4000w32p_t *) priv;\n    et4000w32_gpu_t *g      = et4000->k_gpu;\n    uint32_t         rec[ET_WORDS] = { 0 };\n\n    rec[ET_ROP_FG] = et4000->acl.internal.rop_fg;\n    rec[ET_ROP_BG] = et4000->acl.internal.rop_bg;\n    kairo_seg_make_room(g->seg);\n    if (g->issued && (g->in_order == in_order) && (g->generation == kairo_seg_generation(g->seg)) && !memcmp(g->record, rec, sizeof(rec)))\n        return;\n    memcpy(kairo_seg_op(g->seg, in_order), rec, sizeof(rec));\n    memcpy(g->record, rec, sizeof(rec));\n    g->generation = kairo_seg_generation(g->seg);\n    g->in_order   = in_order;\n    g->issued     = 1;\n}\n\n/* One byte of an operation at the walk's place: its pattern and source (source >= 0: the host's byte) and its mix\n   (mix >= 0: the host's bit, else the mix map's at the mix address), drawn through the raster operation it selects,\n   or with Hardware acceleration on recorded for the GPU. A result routed to the processor (ctrl_routing 40h) is\n   the processor's at once. */\nstatic void\net4000w32_draw_byte(et4000w32p_t *et4000, int source, int mix)\n{\n    svga_t        *svga = &et4000->svga;\n    const uint32_t mask = et4000->vram_mask;\n    const uint32_t p_at = (et4000->acl.pattern_addr + et4000->acl.pattern_x) & mask;\n    const uint32_t s_at = (et4000->acl.source_addr + et4000->acl.source_x) & mask;\n    const uint32_t d_at = et4000->acl.dest_addr & mask;\n    uint8_t        pattern;\n    uint8_t        src;\n    uint8_t        dest;\n    uint8_t        rop;\n    uint8_t        out = 0;\n    int            mixdat;\n\n    if (et4000->k_gpu != NULL) {\n        et4000w32_gpu_t *g = et4000->k_gpu;\n\n        if (!(et4000->acl.internal.ctrl_routing & 0x40)) {\n            const uint32_t m_at                     = et4000->acl.mix_addr & ((mask << 3) | 7);\n            const uint32_t words[ET_BYTE_WORDS]     = { p_at, (source >= 0) ? (ET_IMMEDIATE | (uint32_t) source) : s_at,\n                                                        (mix >= 0) ? (ET_IMMEDIATE | (mix ? 1u : 0u)) : m_at };\n            const uint32_t reads[ET_BYTE_WORDS]     = { p_at, (source >= 0) ? KAIRO_SEG_RUN_NONE : s_at,\n                                                        (mix >= 0) ? KAIRO_SEG_RUN_NONE : (m_at >> 3) };\n\n            kairo_seg_run_pixel(g->run, d_at, words, reads);\n            return;\n        }\n        /* The processor takes the result: the batch drawn first */\n        kairo_seg_run_flush(g->run);\n        kairo_seg_drain(g->seg);\n    }\n\n    pattern = svga->vram[p_at];\n    src     = (source >= 0) ? source : svga->vram[s_at];\n    dest    = svga->vram[d_at];\n    mixdat  = (mix >= 0) ? mix : (svga->vram[(et4000->acl.mix_addr >> 3) & mask] & (1 << (et4000->acl.mix_addr & 7)));\n    rop     = mixdat ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n\n    ROPMIX(rop, dest, pattern, src, out);\n\n    if (!(et4000->acl.internal.ctrl_routing & 0x40)) {\n        svga->vram[d_at]             = out;\n        svga->changedvram[d_at >> 12] = changeframecount;\n    } else {\n        et4000->acl.cpu_dat |= ((uint64_t) out << (et4000->acl.cpu_dat_pos * 8));\n        et4000->acl.cpu_dat_pos++;\n    }\n}\n\nstatic void\net4000w32_blit_walk(int count, int cpu_input, uint32_t src_dat, uint32_t mix_dat, et4000w32p_t *et4000)\n{\n    int mixmap;\n\n"),
    ('86box/src/video/vid_et4000w32.c',
     '    if (cpu_input == 3) {\n        while (1) {\n            pattern = svga->vram[(et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask];\n            source = svga->vram[(et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask];\n\n            dest   = svga->vram[et4000->acl.dest_addr & et4000->vram_mask];\n            mixmap = mix_dat & 1;\n\n            rop = mixmap ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n\n            ROPMIX(rop, dest, pattern, source, out);\n\n            /*Write the data*/\n            svga->vram[et4000->acl.dest_addr & et4000->vram_mask]                = out;\n            svga->changedvram[(et4000->acl.dest_addr & et4000->vram_mask) >> 12] = changeframecount;\n\n            if (et4000->acl.internal.xy_dir & 1)\n',
     '    if (cpu_input == 3) {\n        while (1) {\n            mixmap = mix_dat & 1;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n            et4000w32_draw_byte(et4000, -1, mixmap);\n\n            if (et4000->acl.internal.xy_dir & 1)\n'),
    ('86box/src/video/vid_et4000w32.c',
     '    } else if (cpu_input == 4) {\n        while (1) {\n            pattern = svga->vram[(et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask];\n            source = svga->vram[(et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask];\n\n            dest   = svga->vram[et4000->acl.dest_addr & et4000->vram_mask];\n            mixmap = mix_dat & 1;\n\n            rop = mixmap ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n\n            ROPMIX(rop, dest, pattern, source, out);\n\n            /*Write the data*/\n            svga->vram[et4000->acl.dest_addr & et4000->vram_mask]                = out;\n            svga->changedvram[(et4000->acl.dest_addr & et4000->vram_mask) >> 12] = changeframecount;\n\n            if (et4000->acl.internal.xy_dir & 1)\n',
     '    } else if (cpu_input == 4) {\n        while (1) {\n            mixmap = mix_dat & 1;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n            et4000w32_draw_byte(et4000, -1, mixmap);\n\n            if (et4000->acl.internal.xy_dir & 1)\n'),
    ('86box/src/video/vid_et4000w32.c',
     '        while (count-- && (et4000->acl.y_count >= 0)) {\n            pattern = svga->vram[(et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask];\n\n            if (cpu_input == 1) {\n                source = src_dat & 0xff;\n                src_dat >>= 8;\n            } else /*The source data is from the display memory if the Control Routing register is not set to 1*/\n                source = svga->vram[(et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask];\n\n            dest   = svga->vram[et4000->acl.dest_addr & et4000->vram_mask];\n            mixmap = mix_dat & 1;\n\n            /*Now determine the Raster Operation*/\n            rop = mixmap ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n\n            ROPMIX(rop, dest, pattern, source, out);\n\n            /*Write the data*/\n            svga->vram[et4000->acl.dest_addr & et4000->vram_mask]                = out;\n            svga->changedvram[(et4000->acl.dest_addr & et4000->vram_mask) >> 12] = changeframecount;\n\n',
     '        while (count-- && (et4000->acl.y_count >= 0)) {\n            /*The source data is from the display memory if the Control Routing register is not set to 1*/\n            int source = -1;\n\n            if (cpu_input == 1) {\n                source = src_dat & 0xff;\n                src_dat >>= 8;\n            }\n            mixmap = mix_dat & 1;\n            mix_dat >>= 1;\n            mix_dat |= 0x80000000;\n            et4000w32_draw_byte(et4000, source, mixmap);\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     'static void\net4000w32p_blit(int count, uint32_t mix, uint32_t sdat, int cpu_input, et4000w32p_t *et4000)\n{\n    svga_t *svga = &et4000->svga;\n    uint8_t pattern;\n    uint8_t source;\n    uint8_t dest;\n    uint8_t out = 0;\n    uint8_t rop;\n    int     mixdat;\n\n',
     'static void\net4000w32p_blit_walk(int count, uint32_t mix, uint32_t sdat, int cpu_input, et4000w32p_t *et4000)\n{\n    int mixdat;\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     '            et4000w32_log("%i,%i : ", et4000->acl.internal.pos_x, et4000->acl.internal.pos_y);\n            pattern = svga->vram[(et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask];\n\n            et4000w32_log("%06X %06X ", (et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask, (et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask);\n            if (cpu_input == 2) {\n                source = sdat & 0xff;\n                sdat >>= 8;\n            } else\n                source  = svga->vram[(et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask];\n\n            dest = svga->vram[et4000->acl.dest_addr & et4000->vram_mask];\n            et4000w32_log("%06X   ", et4000->acl.dest_addr);\n            if ((et4000->acl.internal.ctrl_routing & 0xa) == 8) {\n                mixdat = svga->vram[(et4000->acl.mix_addr >> 3) & et4000->vram_mask] & (1 << (et4000->acl.mix_addr & 7));\n                et4000w32_log("%06X %02X  ", et4000->acl.mix_addr, svga->vram[(et4000->acl.mix_addr >> 3) & et4000->vram_mask]);\n            } else {\n                mixdat = mix & 1;\n                mix >>= 1;\n                mix |= 0x80000000;\n            }\n            et4000->acl.mix_addr++;\n            rop = mixdat ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n\n            ROPMIX(rop, dest, pattern, source, out);\n\n            et4000w32_log("%06X = %02X\\n", et4000->acl.dest_addr & et4000->vram_mask, out);\n            if (!(et4000->acl.internal.ctrl_routing & 0x40)) {\n                svga->vram[et4000->acl.dest_addr & et4000->vram_mask]                = out;\n                svga->changedvram[(et4000->acl.dest_addr & et4000->vram_mask) >> 12] = changeframecount;\n            } else {\n                et4000->acl.cpu_dat |= ((uint64_t) out << (et4000->acl.cpu_dat_pos * 8));\n                et4000->acl.cpu_dat_pos++;\n            }\n\n',
     '            et4000w32_log("%i,%i : ", et4000->acl.internal.pos_x, et4000->acl.internal.pos_y);\n            int source = -1;\n\n            if (cpu_input == 2) {\n                source = sdat & 0xff;\n                sdat >>= 8;\n            }\n            /* The mix from the mix map (-1), or the host\'s */\n            mixdat = -1;\n            if ((et4000->acl.internal.ctrl_routing & 0xa) != 8) {\n                mixdat = mix & 1;\n                mix >>= 1;\n                mix |= 0x80000000;\n            }\n            et4000w32_draw_byte(et4000, source, mixdat);\n            et4000->acl.mix_addr++;\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     '        while (count-- && (et4000->acl.y_count >= 0)) {\n            pattern = svga->vram[(et4000->acl.pattern_addr + et4000->acl.pattern_x) & et4000->vram_mask];\n\n            if (cpu_input == 2) {\n                source = sdat & 0xff;\n                sdat >>= 8;\n            } else\n                source = svga->vram[(et4000->acl.source_addr + et4000->acl.source_x) & et4000->vram_mask];\n\n            dest = svga->vram[et4000->acl.dest_addr & et4000->vram_mask];\n            if ((et4000->acl.internal.ctrl_routing & 0xa) == 8) {\n                mixdat = svga->vram[(et4000->acl.mix_addr >> 3) & et4000->vram_mask] & (1 << (et4000->acl.mix_addr & 7));\n            } else {\n                mixdat = mix & 1;\n                mix >>= 1;\n                mix |= 0x80000000;\n            }\n\n            rop = mixdat ? et4000->acl.internal.rop_fg : et4000->acl.internal.rop_bg;\n\n            ROPMIX(rop, dest, pattern, source, out);\n\n            if (!(et4000->acl.internal.ctrl_routing & 0x40)) {\n                svga->vram[et4000->acl.dest_addr & et4000->vram_mask]                = out;\n                svga->changedvram[(et4000->acl.dest_addr & et4000->vram_mask) >> 12] = changeframecount;\n            } else {\n                et4000->acl.cpu_dat |= ((uint64_t) out << (et4000->acl.cpu_dat_pos * 8));\n                et4000->acl.cpu_dat_pos++;\n            }\n\n',
     "        while (count-- && (et4000->acl.y_count >= 0)) {\n            int source = -1;\n\n            if (cpu_input == 2) {\n                source = sdat & 0xff;\n                sdat >>= 8;\n            }\n            /* The mix from the mix map (-1), or the host's */\n            mixdat = -1;\n            if ((et4000->acl.internal.ctrl_routing & 0xa) != 8) {\n                mixdat = mix & 1;\n                mix >>= 1;\n                mix |= 0x80000000;\n            }\n            et4000w32_draw_byte(et4000, source, mixdat);\n\n"),
    ('86box/src/video/vid_et4000w32.c',
     '                }\n            }\n        }\n    }\n}\n\nstatic void\net4000w32p_hwcursor_draw(svga_t *svga, int displine)\n',
     '                }\n            }\n        }\n    }\n}\n\n/* The walks, and with Hardware acceleration on the run they ended in recorded: the processor may meet it next */\nstatic void\net4000w32_blit(int count, int cpu_input, uint32_t src_dat, uint32_t mix_dat, et4000w32p_t *et4000)\n{\n    et4000w32_blit_walk(count, cpu_input, src_dat, mix_dat, et4000);\n    if (et4000->k_gpu != NULL)\n        kairo_seg_run_flush(et4000->k_gpu->run);\n}\n\nstatic void\net4000w32p_blit(int count, uint32_t mix, uint32_t sdat, int cpu_input, et4000w32p_t *et4000)\n{\n    et4000w32p_blit_walk(count, mix, sdat, cpu_input, et4000);\n    if (et4000->k_gpu != NULL)\n        kairo_seg_run_flush(et4000->k_gpu->run);\n}\n\nstatic void\net4000w32p_hwcursor_draw(svga_t *svga, int displine)\n'),
    ('86box/src/video/vid_et4000w32.c',
     '\nstatic void *\n',
     "\n/* KairoX86#254: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\net4000w32p_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const et4000w32p_t *et4000 = (const et4000w32p_t *) svga->priv;\n\n    kairo_seg_touch(et4000->k_gpu->seg, addr & et4000->vram_mask, len);\n}\n\nstatic void *\n"),
    ('86box/src/video/vid_et4000w32.c',
     '    et4000->svga.decode_mask = (et4000->vram_size << 20) - 1;\n\n',
     '    et4000->svga.decode_mask = (et4000->vram_size << 20) - 1;\n\n    /* KairoX86#254: with Hardware acceleration on, the accelerator\'s bytes drawn on the GPU */\n    if (kairo_gpu_on) {\n        et4000->k_gpu = calloc(1, sizeof(et4000w32_gpu_t));\n        if (et4000->k_gpu == NULL)\n            fatal("ET4000/W32 on the GPU: no memory\\n");\n        et4000->k_gpu->seg = kairo_et4000w32_open(et4000->svga.vram, et4000->vram_mask, et4000->svga.changedvram,\n                                                  &et4000->svga.monitor->mon_changeframecount);\n        et4000->k_gpu->run = kairo_seg_run_open(et4000->k_gpu->seg, et4000->vram_mask, 1, ET_BYTE_WORDS, 3, et4000w32_k_op, et4000);\n        et4000->svga.kairo_touch = et4000w32p_svga_touch;\n    }\n\n'),
    ('86box/src/video/vid_et4000w32.c',
     '\n    svga_close(&et4000->svga);\n',
     '\n    if (et4000->k_gpu != NULL) {\n        kairo_seg_close(et4000->k_gpu->seg); /* KairoX86#254 */\n        kairo_seg_run_close(et4000->k_gpu->run);\n        free(et4000->k_gpu);\n    }\n    svga_close(&et4000->svga);\n'),
]

# KairoX86#250: the Cirrus Logic GD54xx BitBLT engine on the GPU (86box/kairo_gpu_cl54xx.h, an added file,
# core/kairo/gpu_cl54xx.c, core/kairo/shaders/cl54xx.comp), on the drawing engines' shared batches as runs of bytes.
# The pattern copy's, system memory source's and normal blit's per-byte draw goes through one helper (gd54xx_draw_byte)
# with each byte's source, mask and bytes as descriptors; the walk stays the CPU's.
KAIROX86_GPU_CL54XX = [
    ('86box/src/video/vid_cl54xx.c',
     '#include <86box/bswap.h>\n\n',
     '#include <86box/bswap.h>\n#include <86box/kairo_gpu.h> /* KairoX86#250 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_cl54xx.h>\n\n'),
    ('86box/src/video/vid_cl54xx.c',
     '    void *ddc;\n} gd54xx_t;\n\n',
     "    void *ddc;\n\n    struct gd54xx_gpu_t *k_gpu; /* KairoX86#250: the BitBLT engine's batch on the GPU, NULL in software */\n} gd54xx_t;\n\n/* KairoX86#250: the engine's batch and the run of bytes its walk is drawing (kairo_seg_run) */\ntypedef struct gd54xx_gpu_t {\n    kairo_seg_t     *seg;\n    kairo_seg_run_t *run;\n    uint32_t         record[CL_WORDS];\n    uint64_t         generation; /* the batch's drains when the record went in */\n    int              issued;\n    int              in_order;\n    int              normal; /* the run's write rule: gd54xx_normal_blit's, else gd54xx_blit's */\n} gd54xx_gpu_t;\n\n"),
    ('86box/src/video/vid_cl54xx.c',
     '\nstatic void\ngd54xx_pattern_copy(gd54xx_t *gd54xx)\n{\n    uint8_t  target;\n    uint8_t  src;\n    uint8_t *dst;\n    int      pattern_y;\n    int      pattern_pitch;\n    uint32_t bitmask = 0;\n    uint32_t pixel;\n',
     "\n/* KairoX86#250: the run's operation in the batch: the record again only where it differs or the batch has been drawn */\nstatic void\ngd54xx_k_op(void *priv, bool in_order)\n{\n    gd54xx_t     *gd54xx        = (gd54xx_t *) priv;\n    gd54xx_gpu_t *g             = gd54xx->k_gpu;\n    const int     sysdest       = !!(gd54xx->blt.mode & CIRRUS_BLTMODE_MEMSYSDEST);\n    uint32_t      rec[CL_WORDS] = { 0 };\n\n    rec[CL_ROP] = gd54xx->blt.rop;\n    if (g->normal)\n        rec[CL_FLAGS] = CLF_RULE_NORMAL | ((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) ? CLF_TRANSP : 0);\n    else\n        rec[CL_FLAGS] = ((!sysdest && (gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP)) ? CLF_TRANSP : 0) |\n                        ((!sysdest && (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_BACKGROUNDONLY)) ? CLF_BGONLY : 0);\n    rec[CL_FLAGS] |= ((gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) ? CLF_COLOREXP : 0) |\n                     ((gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_COLOREXPINV) ? CLF_EXPINV : 0);\n    kairo_seg_make_room(g->seg);\n    if (g->issued && (g->in_order == in_order) && (g->generation == kairo_seg_generation(g->seg)) && !memcmp(g->record, rec, sizeof(rec)))\n        return;\n    memcpy(kairo_seg_op(g->seg, in_order), rec, sizeof(rec));\n    memcpy(g->record, rec, sizeof(rec));\n    g->generation = kairo_seg_generation(g->seg);\n    g->in_order   = in_order;\n    g->issued     = 1;\n}\n\n/* A colour-expansion bit, bit n (0 the leftmost) of the byte at addr: read now in software, its bit address on the GPU\n   (n 8 and on, past the byte, is 0) */\nstatic uint32_t\ngd54xx_k_ce(gd54xx_t *gd54xx, uint32_t addr, int n)\n{\n    if (n > 7)\n        return CL_IMM;\n    if (gd54xx->k_gpu == NULL)\n        return CL_IMM | ((gd54xx->svga.vram[addr & gd54xx->vram_mask] & (0x80 >> n)) ? 1 : 0);\n    return CL_CE | ((((addr & gd54xx->vram_mask) << 3) + (7 - n)) & CL_ADDR_MASK);\n}\n\n/* The fg and bg bytes colour expansion gives byte shift of a pixel (gd54xx_color_expand) */\nstatic uint32_t\ngd54xx_k_bytes(gd54xx_t *gd54xx, int shift)\n{\n    const uint32_t fg = (uint8_t) (gd54xx->blt.fg_col >> (shift << 3));\n    const uint32_t bg = (gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) ? fg : (uint8_t) (gd54xx->blt.bg_col >> (shift << 3));\n\n    return fg | (bg << 8);\n}\n\n/* A colour expansion's source and mask words from its bit */\nstatic void\ngd54xx_k_ce_words(uint32_t ce, uint32_t bytes, uint32_t *ws, uint32_t *wm)\n{\n    if (ce & CL_IMM) {\n        *ws = CL_IMM | ((ce & 1) ? (bytes & 0xff) : ((bytes >> 8) & 0xff));\n        *wm = ce;\n    } else {\n        *ws = ce;\n        *wm = 0;\n    }\n}\n\n/* One byte of a blit at d_at, from its source, mask and bytes words (86box/kairo_gpu_cl54xx.h), through gd54xx_rop and\n   the write rule: gd54xx_normal_blit's (normal), else gd54xx_blit's; with Hardware acceleration on recorded for the\n   GPU */\nstatic void\ngd54xx_draw_byte(gd54xx_t *gd54xx, uint32_t d_at, uint32_t ws, uint32_t wm, uint32_t bytes, int normal)\n{\n    svga_t  *svga = &gd54xx->svga;\n    uint8_t  src;\n    uint8_t  target;\n    uint32_t m;\n    int      skip = !!(wm & CL_SKIP);\n\n    d_at &= gd54xx->vram_mask;\n    if (gd54xx->k_gpu != NULL) {\n        /* gd54xx_blit leaves no skip to a destination in system memory */\n        if (!normal && (gd54xx->blt.mode & CIRRUS_BLTMODE_MEMSYSDEST))\n            wm &= ~CL_SKIP;\n        const uint32_t words[CL_BYTE_WORDS] = { ws, wm, bytes };\n        const uint32_t reads[2]             = { (ws & CL_IMM) ? KAIRO_SEG_RUN_NONE : (ws & CL_CE) ? ((ws & CL_ADDR_MASK) >> 3) : ws,\n                                                KAIRO_SEG_RUN_NONE };\n\n        gd54xx->k_gpu->normal = normal;\n        kairo_seg_run_pixel(gd54xx->k_gpu->run, d_at, words, reads);\n        return;\n    }\n\n    /* Software: the descriptors as the kernel reads them */\n    if (ws & CL_IMM)\n        src = ws & 0xff;\n    else\n        src = svga->vram[ws & gd54xx->vram_mask];\n    m = (wm & CL_IMM) ? (wm & 1) : 0;\n    if (wm & CL_TCOMP)\n        m = !((src ^ (bytes >> 16)) & ~(bytes >> 24) & 0xff);\n\n    target = svga->vram[d_at];\n    gd54xx_rop(gd54xx, &target, &target, &src);\n    if (!normal) {\n        gd54xx_blit(gd54xx, m, &svga->vram[d_at], target, skip);\n        return;\n    }\n    if ((gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) && (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_COLOREXPINV))\n        m = !m;\n    if ((wm & CL_NCOMP) && (src != ((bytes >> 16) & 0xff)))\n        m = 0;\n    if (!skip && !((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) && !m))\n        svga->vram[d_at] = target;\n}\n\n/* A pattern copy's byte xx of a pixel: its colour-expansion bit (ce), else its source byte at s_at */\nstatic void\ngd54xx_pattern_byte(gd54xx_t *gd54xx, uint32_t ce, uint32_t s_at, uint32_t d_at, int xx, int skip)\n{\n    uint32_t ws, wm, bytes = 0;\n\n    if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n        bytes = gd54xx_k_bytes(gd54xx, xx);\n        gd54xx_k_ce_words(ce, bytes, &ws, &wm);\n    } else {\n        ws = s_at & gd54xx->vram_mask;\n        wm = CL_IMM | 1;\n        /* gd54xx_transparent_comp */\n        if ((gd54xx->blt.pixel_width <= 2) && gd54xx_has_transp(&gd54xx->svga, 0)) {\n            wm = CL_TCOMP;\n            bytes |= (uint32_t) ((uint8_t *) &(gd54xx->blt.trans_col))[xx] << 16;\n            if (gd54xx_has_transp(&gd54xx->svga, 1))\n                bytes |= (uint32_t) ((uint8_t *) &(gd54xx->blt.trans_mask))[xx] << 24;\n        }\n    }\n    gd54xx_draw_byte(gd54xx, d_at, ws, wm | (skip ? CL_SKIP : 0), bytes, 0);\n}\n\n/* A normal blit's byte: its colour-expansion bit from the byte at ce_addr, else its source byte at s_at */\nstatic void\ngd54xx_normal_byte(gd54xx_t *gd54xx, uint32_t ce_addr, uint32_t s_at, uint32_t d_at, int skip)\n{\n    uint32_t ws, wm, bytes = 0;\n\n    if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n        bytes = gd54xx_k_bytes(gd54xx, gd54xx->blt.x_count % gd54xx->blt.pixel_width);\n        gd54xx_k_ce_words(gd54xx_k_ce(gd54xx, ce_addr, gd54xx->blt.x_count / gd54xx->blt.pixel_width), bytes, &ws, &wm);\n    } else {\n        ws = s_at & gd54xx->vram_mask;\n        wm = CL_IMM | 1;\n        /* 8 and 16 bpp transparent comparison, against the mask's low byte */\n        if ((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) &&\n            ((gd54xx->blt.mode & CIRRUS_BLTMODE_PIXELWIDTHMASK) <= CIRRUS_BLTMODE_PIXELWIDTH16)) {\n            wm |= CL_NCOMP;\n            bytes |= (gd54xx->blt.trans_mask & 0xff) << 16;\n        }\n    }\n    gd54xx_draw_byte(gd54xx, d_at, ws, wm | (skip ? CL_SKIP : 0), bytes, 1);\n}\n\nstatic void\ngd54xx_pattern_copy(gd54xx_t *gd54xx)\n{\n    int      pattern_y;\n    int      pattern_pitch;\n    uint32_t ce = CL_IMM; /* the pixel's colour-expansion bit (gd54xx_k_ce) */\n    uint32_t pixel;\n"),
    ('86box/src/video/vid_cl54xx.c',
     '        while (y <= gd54xx->blt.height) {\n            if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n                if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_SOLIDFILL)\n                    bitmask = 1;\n                else\n                    bitmask = svga->vram[srca2 & gd54xx->vram_mask] & (0x80 >> pixel);\n            }\n            while (xx < gd54xx->blt.pixel_width) {\n                if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_CLIP_RECTANGLE) {\n                    if (((gd54xx->blt.dst_x_pos + xx) >= clip_l) && ((gd54xx->blt.dst_x_pos + xx) <= clip_r) &&\n                        (gd54xx->blt.dst_y_pos >= clip_t) && (gd54xx->blt.dst_y_pos <= clip_b)) {\n                        if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)\n                            src = gd54xx_color_expand(gd54xx, bitmask, xx);\n                        else {\n                            src     = svga->vram[(srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx) & gd54xx->vram_mask];\n                            bitmask = gd54xx_transparent_comp(gd54xx, xx, src);\n                        }\n                        dst    = &(svga->vram[(dsta + gd54xx->blt.dst_x_pos + xx) & gd54xx->vram_mask]);\n                        target = *dst;\n                        gd54xx_rop(gd54xx, &target, &target, &src);\n                        if (gd54xx->blt.pixel_width == 3)\n                            gd54xx_blit(gd54xx, bitmask, dst, target, ((x + xx) < gd54xx->blt.pattern_x));\n                        else\n                            gd54xx_blit(gd54xx, bitmask, dst, target, (x < gd54xx->blt.pattern_x));\n                    }\n                } else {\n                    if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)\n                        src = gd54xx_color_expand(gd54xx, bitmask, xx);\n                    else {\n                        src     = svga->vram[(srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx) & gd54xx->vram_mask];\n                        bitmask = gd54xx_transparent_comp(gd54xx, xx, src);\n                    }\n                    dst    = &(svga->vram[(dsta + gd54xx->blt.dst_x_pos + xx) & gd54xx->vram_mask]);\n                    target = *dst;\n                    gd54xx_rop(gd54xx, &target, &target, &src);\n                    if (gd54xx->blt.pixel_width == 3)\n                        gd54xx_blit(gd54xx, bitmask, dst, target, ((x + xx) < gd54xx->blt.pattern_x));\n                    else\n                        gd54xx_blit(gd54xx, bitmask, dst, target, (x < gd54xx->blt.pattern_x));\n                }\n',
     '        while (y <= gd54xx->blt.height) {\n            if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)\n                ce = (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_SOLIDFILL) ? (CL_IMM | 1) : gd54xx_k_ce(gd54xx, srca2, pixel);\n            while (xx < gd54xx->blt.pixel_width) {\n                if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_CLIP_RECTANGLE) {\n                    if (((gd54xx->blt.dst_x_pos + xx) >= clip_l) && ((gd54xx->blt.dst_x_pos + xx) <= clip_r) &&\n                        (gd54xx->blt.dst_y_pos >= clip_t) && (gd54xx->blt.dst_y_pos <= clip_b)) {\n                        gd54xx_pattern_byte(gd54xx, ce, srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx, dsta + gd54xx->blt.dst_x_pos + xx, xx,\n                                            (gd54xx->blt.pixel_width == 3) ? ((x + xx) < gd54xx->blt.pattern_x) : (x < gd54xx->blt.pattern_x));\n                    }\n                } else {\n                    gd54xx_pattern_byte(gd54xx, ce, srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx, dsta + gd54xx->blt.dst_x_pos + xx, xx,\n                                        (gd54xx->blt.pixel_width == 3) ? ((x + xx) < gd54xx->blt.pattern_x) : (x < gd54xx->blt.pattern_x));\n                }\n'),
    ('86box/src/video/vid_cl54xx.c',
     '            for (uint16_t x = 0; x <= gd54xx->blt.width; x += gd54xx->blt.pixel_width) {\n                if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n                    if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_SOLIDFILL)\n                        bitmask = 1;\n                    else\n                        bitmask = svga->vram[srca2 & gd54xx->vram_mask] & (0x80 >> pixel);\n                }\n                for (int xx = 0; xx < gd54xx->blt.pixel_width; xx++) {\n                    if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)\n                        src = gd54xx_color_expand(gd54xx, bitmask, xx);\n                    else {\n                        src     = svga->vram[(srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx) & gd54xx->vram_mask];\n                        bitmask = gd54xx_transparent_comp(gd54xx, xx, src);\n                    }\n                    dst    = &(svga->vram[(dsta + x + xx) & gd54xx->vram_mask]);\n                    target = *dst;\n                    gd54xx_rop(gd54xx, &target, &target, &src);\n                    if (gd54xx->blt.pixel_width == 3)\n                        gd54xx_blit(gd54xx, bitmask, dst, target, ((x + xx) < gd54xx->blt.pattern_x));\n                    else\n                        gd54xx_blit(gd54xx, bitmask, dst, target, (x < gd54xx->blt.pattern_x));\n                }\n',
     '            for (uint16_t x = 0; x <= gd54xx->blt.width; x += gd54xx->blt.pixel_width) {\n                if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)\n                    ce = (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_SOLIDFILL) ? (CL_IMM | 1) : gd54xx_k_ce(gd54xx, srca2, pixel);\n                for (int xx = 0; xx < gd54xx->blt.pixel_width; xx++) {\n                    gd54xx_pattern_byte(gd54xx, ce, srca2 + (x % (gd54xx->blt.pixel_width << 3)) + xx, dsta + x + xx, xx,\n                                        (gd54xx->blt.pixel_width == 3) ? ((x + xx) < gd54xx->blt.pattern_x) : (x < gd54xx->blt.pattern_x));\n                }\n'),
    ('86box/src/video/vid_cl54xx.c',
     '{\n    uint8_t *dst = NULL;\n    uint8_t  exp;\n    uint8_t  target;\n    uint16_t clip_l = gd54xx->blt.clip_start_x * gd54xx->blt.pixel_width;\n',
     '{\n    uint8_t  exp;\n    uint16_t clip_l = gd54xx->blt.clip_start_x * gd54xx->blt.pixel_width;\n'),
    ('86box/src/video/vid_cl54xx.c',
     '                        }\n                        dst = &(svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask]);\n                        target = *dst;\n                        gd54xx_rop(gd54xx, &target, &target, &exp);\n                        if ((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND))\n                            gd54xx_blit(gd54xx, bitmask, dst, target,\n                                        ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x));\n                        else {\n                            gd54xx_blit(gd54xx, bitmask, dst, target, (gd54xx->blt.x_count < gd54xx->blt.pattern_x));\n                        }\n                        svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n',
     '                        }\n                        gd54xx_draw_byte(gd54xx, (gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos), CL_IMM | exp, CL_IMM | (bitmask ? 1 : 0) |\n                                         ((((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)) ?\n                                           ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x) :\n                                           (gd54xx->blt.x_count < gd54xx->blt.pattern_x)) ? CL_SKIP : 0), 0, 0);\n                        svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n'),
    ('86box/src/video/vid_cl54xx.c',
     '\n                    dst = &(svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask]);\n                    target = *dst;\n                    gd54xx_rop(gd54xx, &target, &target, &exp);\n                    if ((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND))\n                        gd54xx_blit(gd54xx, bitmask, dst, target,\n                                    ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x));\n                    else\n                        gd54xx_blit(gd54xx, bitmask, dst, target, (gd54xx->blt.x_count < gd54xx->blt.pattern_x));\n\n',
     '\n                    gd54xx_draw_byte(gd54xx, (gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos), CL_IMM | exp, CL_IMM | (bitmask ? 1 : 0) |\n                                     ((((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)) ?\n                                       ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x) :\n                                       (gd54xx->blt.x_count < gd54xx->blt.pattern_x)) ? CL_SKIP : 0), 0, 0);\n\n'),
    ('86box/src/video/vid_cl54xx.c',
     '\n                dst    = &(svga->vram[gd54xx->blt.dst_addr_backup & gd54xx->vram_mask]);\n                target = *dst;\n                gd54xx_rop(gd54xx, &target, &target, &exp);\n                if ((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND))\n                    gd54xx_blit(gd54xx, bitmask, dst, target,\n                                ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x));\n                else\n                    gd54xx_blit(gd54xx, bitmask, dst, target, (gd54xx->blt.x_count < gd54xx->blt.pattern_x));\n\n',
     '\n                gd54xx_draw_byte(gd54xx, gd54xx->blt.dst_addr_backup, CL_IMM | exp, CL_IMM | (bitmask ? 1 : 0) |\n                                 ((((gd54xx->blt.pixel_width == 3) && (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND)) ?\n                                   ((gd54xx->blt.x_count + gd54xx->blt.xx_count) < gd54xx->blt.pattern_x) :\n                                   (gd54xx->blt.x_count < gd54xx->blt.pattern_x)) ? CL_SKIP : 0), 0, 0);\n\n'),
    ('86box/src/video/vid_cl54xx.c',
     '{\n    uint8_t  src   = 0;\n    uint8_t  dst;\n    uint16_t width = gd54xx->blt.width;\n',
     '{\n    uint16_t width = gd54xx->blt.width;\n'),
    ('86box/src/video/vid_cl54xx.c',
     '    int      x_max = 0;\n    int      shift = 0;\n    uint32_t mask = 0;\n    uint32_t src_addr = gd54xx->blt.src_addr;\n',
     '    int      x_max = 0;\n    uint32_t src_addr = gd54xx->blt.src_addr;\n'),
    ('86box/src/video/vid_cl54xx.c',
     '        while (count--) {\n            src  = 0;\n            mask = 0;\n\n            if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_CLIP_RECTANGLE) {\n                //pclog("XY Clipping Blit: pix=%d, DSTX=%d, DSTY=%d, SRCX=%d, SRCY=%d, cl=%d, cr=%d, xcount=%d, xx=%d, width=%d, height=%d, modeext=%02x.\\n", gd54xx->blt.pixel_width, gd54xx->blt.dst_x_pos, gd54xx->blt.dst_y_pos, gd54xx->blt.src_x_pos, gd54xx->blt.src_y_pos, clip_l, clip_r, gd54xx->blt.x_count, xx, width, gd54xx->blt.height_internal, gd54xx->blt.modeext);\n                if ((gd54xx->blt.dst_x_pos >= clip_l) && (gd54xx->blt.dst_x_pos <= clip_r) &&\n                    (gd54xx->blt.dst_y_pos >= clip_t) && (gd54xx->blt.dst_y_pos <= clip_b)) {\n                    if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n                        mask  = svga->vram[src_addr & gd54xx->vram_mask] & (0x80 >> ((gd54xx->blt.x_count) / gd54xx->blt.pixel_width));\n                        shift = ((gd54xx->blt.x_count) % gd54xx->blt.pixel_width);\n                        src = gd54xx_color_expand(gd54xx, mask, shift);\n                    } else {\n                        src = svga->vram[(gd54xx->blt.src_addr_xy + gd54xx->blt.src_x_pos) & gd54xx->vram_mask];\n                        mask = 1;\n                    }\n\n                    dst = svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask];\n                    svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n                    gd54xx_rop(gd54xx, &dst, &dst, (const uint8_t *) &src);\n\n                    if ((gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) && (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_COLOREXPINV))\n                        mask = !mask;\n\n                    /* This handles 8bpp and 16bpp non-color-expanding transparent comparisons. */\n                    if ((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) &&\n                        !(gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) &&\n                        ((gd54xx->blt.mode & CIRRUS_BLTMODE_PIXELWIDTHMASK) <= CIRRUS_BLTMODE_PIXELWIDTH16) &&\n                        (src != ((gd54xx->blt.trans_mask >> (shift << 3)) & 0xff)))\n                        mask = 0;\n\n                    if ((((gd54xx->blt.width) - width) >= gd54xx->blt.pattern_x) &&\n                        !((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) && !mask))\n                        svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask] = dst;\n                }\n            } else {\n                if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n                    mask  = svga->vram[src_addr & gd54xx->vram_mask] & (0x80 >> ((gd54xx->blt.x_count) / gd54xx->blt.pixel_width));\n                    shift = (gd54xx->blt.x_count % gd54xx->blt.pixel_width);\n                    src = gd54xx_color_expand(gd54xx, mask, shift);\n                } else {\n                    src = svga->vram[(gd54xx->blt.src_addr_xy + gd54xx->blt.src_x_pos) & gd54xx->vram_mask];\n                    mask = 1;\n                }\n\n                dst = svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask];\n                svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n                gd54xx_rop(gd54xx, &dst, &dst, (const uint8_t *) &src);\n\n                if ((gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) && (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_COLOREXPINV))\n                    mask = !mask;\n\n                /* This handles 8bpp and 16bpp non-color-expanding transparent comparisons. */\n                if ((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) &&\n                    !(gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) &&\n                    ((gd54xx->blt.mode & CIRRUS_BLTMODE_PIXELWIDTHMASK) <= CIRRUS_BLTMODE_PIXELWIDTH16) &&\n                    (src != ((gd54xx->blt.trans_mask >> (shift << 3)) & 0xff)))\n                    mask = 0;\n\n                if ((((gd54xx->blt.width) - width) >= gd54xx->blt.pattern_x) &&\n                    !((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) && !mask)) {\n                    svga->vram[(gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask] = dst;\n                    //pclog("NoClipNormal: PATX=%d, ROP=%02x, DSTData=%02x, DX=%d, DY=%d, CX=%d, CY=%d, dir=%d, mode=%02x, modeext=%02x, fgcol=%08x, shift=%d.\\n", gd54xx->blt.pattern_x, gd54xx->blt.rop, dst, gd54xx->blt.dst_x_pos, gd54xx->blt.dst_y_pos, gd54xx->blt.src_x_pos, gd54xx->blt.src_y_pos, gd54xx->blt.dir, gd54xx->blt.mode, gd54xx->blt.modeext, gd54xx->blt.fg_col, shift);\n                } else\n                    ;//pclog("NoClipNormalNoWrite: PATX=%d, ROP=%02x, DSTData=%02x, DX=%d, DY=%d, CX=%d, CY=%d, dir=%d, mode=%02x, modeext=%02x, fg=%08x, shift=%d.\\n", gd54xx->blt.pattern_x, gd54xx->blt.rop, dst, gd54xx->blt.dst_x_pos, gd54xx->blt.dst_y_pos, gd54xx->blt.src_x_pos, gd54xx->blt.src_y_pos, gd54xx->blt.dir, gd54xx->blt.mode, gd54xx->blt.modeext, gd54xx->blt.fg_col, shift);\n            }\n',
     '        while (count--) {\n            if (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_CLIP_RECTANGLE) {\n                //pclog("XY Clipping Blit: pix=%d, DSTX=%d, DSTY=%d, SRCX=%d, SRCY=%d, cl=%d, cr=%d, xcount=%d, xx=%d, width=%d, height=%d, modeext=%02x.\\n", gd54xx->blt.pixel_width, gd54xx->blt.dst_x_pos, gd54xx->blt.dst_y_pos, gd54xx->blt.src_x_pos, gd54xx->blt.src_y_pos, clip_l, clip_r, gd54xx->blt.x_count, xx, width, gd54xx->blt.height_internal, gd54xx->blt.modeext);\n                if ((gd54xx->blt.dst_x_pos >= clip_l) && (gd54xx->blt.dst_x_pos <= clip_r) &&\n                    (gd54xx->blt.dst_y_pos >= clip_t) && (gd54xx->blt.dst_y_pos <= clip_b)) {\n                    svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n                    gd54xx_normal_byte(gd54xx, src_addr, gd54xx->blt.src_addr_xy + gd54xx->blt.src_x_pos, gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos,\n                                       !(((gd54xx->blt.width) - width) >= gd54xx->blt.pattern_x));\n                }\n            } else {\n                svga->changedvram[((gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos) & gd54xx->vram_mask) >> 12] = changeframecount;\n                gd54xx_normal_byte(gd54xx, src_addr, gd54xx->blt.src_addr_xy + gd54xx->blt.src_x_pos, gd54xx->blt.dst_addr_xy + gd54xx->blt.dst_x_pos,\n                                   !(((gd54xx->blt.width) - width) >= gd54xx->blt.pattern_x));\n            }\n'),
    ('86box/src/video/vid_cl54xx.c',
     '        while (count) {\n            src  = 0;\n            mask = 0;\n\n            if (gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) {\n                mask  = svga->vram[src_addr & gd54xx->vram_mask] & (0x80 >> (gd54xx->blt.x_count / gd54xx->blt.pixel_width));\n                shift = (gd54xx->blt.x_count % gd54xx->blt.pixel_width);\n                src   = gd54xx_color_expand(gd54xx, mask, shift);\n            } else {\n                src = svga->vram[src_addr & gd54xx->vram_mask];\n                src_addr += gd54xx->blt.dir;\n                mask = 1;\n            }\n            count--;\n\n            dst = svga->vram[dst_addr & gd54xx->vram_mask];\n            svga->changedvram[(dst_addr & gd54xx->vram_mask) >> 12] = changeframecount;\n\n            gd54xx_rop(gd54xx, &dst, &dst, (const uint8_t *) &src);\n\n            if ((gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) && (gd54xx->blt.modeext & CIRRUS_BLTMODEEXT_COLOREXPINV))\n                mask = !mask;\n\n            /* This handles 8bpp and 16bpp non-color-expanding transparent comparisons. */\n            if ((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) &&\n                !(gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND) &&\n                ((gd54xx->blt.mode & CIRRUS_BLTMODE_PIXELWIDTHMASK) <= CIRRUS_BLTMODE_PIXELWIDTH16) &&\n                (src != ((gd54xx->blt.trans_mask >> (shift << 3)) & 0xff)))\n                mask = 0;\n\n            if (((gd54xx->blt.width - width) >= gd54xx->blt.pattern_x) &&\n                !((gd54xx->blt.mode & CIRRUS_BLTMODE_TRANSPARENTCOMP) && !mask))\n                svga->vram[dst_addr & gd54xx->vram_mask] = dst;\n\n',
     '        while (count) {\n            /* The source byte, before the walk steps past it */\n            const uint32_t s_at = src_addr;\n\n            if (!(gd54xx->blt.mode & CIRRUS_BLTMODE_COLOREXPAND))\n                src_addr += gd54xx->blt.dir;\n            count--;\n\n            svga->changedvram[(dst_addr & gd54xx->vram_mask) >> 12] = changeframecount;\n            gd54xx_normal_byte(gd54xx, src_addr, s_at, dst_addr, !((gd54xx->blt.width - width) >= gd54xx->blt.pattern_x));\n\n'),
    ('86box/src/video/vid_cl54xx.c',
     '            gd54xx->blt.cmd_list_backup += 0x10;\n            gd54xx->blt.cmd_list_dword[0] = *(uint32_t *)&vram[gd54xx->blt.cmd_list_backup & gd54xx->vram_mask];\n',
     '            gd54xx->blt.cmd_list_backup += 0x10;\n            if (gd54xx->k_gpu != NULL) /* KairoX86#250 */\n                kairo_seg_touch(gd54xx->k_gpu->seg, gd54xx->blt.cmd_list_backup & gd54xx->vram_mask, 16);\n            gd54xx->blt.cmd_list_dword[0] = *(uint32_t *)&vram[gd54xx->blt.cmd_list_backup & gd54xx->vram_mask];\n'),
    ('86box/src/video/vid_cl54xx.c',
     '        while (gd54xx->blt.msd_buf_pos < 32) {\n            gd54xx->blt.msd_buf[gd54xx->blt.msd_buf_pos & 0x1f] = svga->vram[gd54xx->blt.src_addr_backup &\n',
     '        while (gd54xx->blt.msd_buf_pos < 32) {\n            if (gd54xx->k_gpu != NULL) /* KairoX86#250 */\n                kairo_seg_touch(gd54xx->k_gpu->seg, gd54xx->blt.src_addr_backup & gd54xx->vram_mask, 1);\n            gd54xx->blt.msd_buf[gd54xx->blt.msd_buf_pos & 0x1f] = svga->vram[gd54xx->blt.src_addr_backup &\n'),
    ('86box/src/video/vid_cl54xx.c',
     '\nstatic void\ngd54xx_start_blit(uint32_t cpu_dat, uint32_t count, gd54xx_t *gd54xx, svga_t *svga)\n{\n',
     "\nstatic void gd54xx_start_blit_walk(uint32_t cpu_dat, uint32_t count, gd54xx_t *gd54xx, svga_t *svga);\n\n/* KairoX86#250: the walk, and with Hardware acceleration on the run it ended in recorded (the next blit's state is\n   another operation) */\nstatic void\ngd54xx_start_blit(uint32_t cpu_dat, uint32_t count, gd54xx_t *gd54xx, svga_t *svga)\n{\n    gd54xx_start_blit_walk(cpu_dat, count, gd54xx, svga);\n    if (gd54xx->k_gpu != NULL)\n        kairo_seg_run_flush(gd54xx->k_gpu->run);\n}\n\nstatic void\ngd54xx_start_blit_walk(uint32_t cpu_dat, uint32_t count, gd54xx_t *gd54xx, svga_t *svga)\n{\n"),
    ('86box/src/video/vid_cl54xx.c',
     '\nstatic void *\n',
     "\n/* KairoX86#250: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\ngd54xx_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const gd54xx_t *gd54xx = (const gd54xx_t *) svga->priv;\n\n    kairo_seg_touch(gd54xx->k_gpu->seg, addr & gd54xx->vram_mask, len);\n}\n\nstatic void *\n"),
    ('86box/src/video/vid_cl54xx.c',
     '    svga->ven_write    = gd54xx_write_modes45;\n    if ((vram == 1) || (vram >= 256 && vram <= 1024))\n',
     '    svga->ven_write    = gd54xx_write_modes45;\n\n    /* KairoX86#250: with Hardware acceleration on, the BitBLT engine\'s bytes drawn on the GPU */\n    if (kairo_gpu_on) {\n        gd54xx->k_gpu = calloc(1, sizeof(gd54xx_gpu_t));\n        if (gd54xx->k_gpu == NULL)\n            fatal("GD54xx on the GPU: no memory\\n");\n        gd54xx->k_gpu->seg = kairo_cl54xx_open(svga->vram, gd54xx->vram_mask, svga->changedvram, &svga->monitor->mon_changeframecount);\n        gd54xx->k_gpu->run = kairo_seg_run_open(gd54xx->k_gpu->seg, gd54xx->vram_mask, 1, CL_BYTE_WORDS, 1, gd54xx_k_op, gd54xx);\n        svga->kairo_touch  = gd54xx_svga_touch;\n    }\n    if ((vram == 1) || (vram >= 256 && vram <= 1024))\n'),
    ('86box/src/video/vid_cl54xx.c',
     '\n    svga_close(&gd54xx->svga);\n',
     '\n    if (gd54xx->k_gpu != NULL) {\n        kairo_seg_close(gd54xx->k_gpu->seg); /* KairoX86#250 */\n        kairo_seg_run_close(gd54xx->k_gpu->run);\n        free(gd54xx->k_gpu);\n    }\n    svga_close(&gd54xx->svga);\n'),
]

# KairoX86#249: the Chips & Technologies B69000 BitBLT engine on the GPU (86box/kairo_gpu_chips69000.h, an added file,
# core/kairo/gpu_chips69000.c, core/kairo/shaders/chips69000.comp), on the drawing engines' shared batches as runs of
# pixels. With Hardware acceleration on, chips_69000_process_pixel records each pixel's source and pattern
# (chips_69000_k_pixel); the walk stays the CPU's and the software path is unchanged.
KAIROX86_GPU_CHIPS69000 = [
    ('86box/src/video/vid_chips_69000.c',
     '#include <86box/bswap.h>\n#include <assert.h>\n',
     '#include <86box/bswap.h>\n#include <86box/kairo_gpu.h> /* KairoX86#249 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_chips69000.h>\n#include <assert.h>\n'),
    ('86box/src/video/vid_chips_69000.c',
     '    } overlay;\n} chips_69000_t;\n',
     "    } overlay;\n\n    /* KairoX86#249: the BitBLT engine's batch on the GPU and its runs, one per bytes per pixel; NULL in software */\n    struct {\n        kairo_seg_t     *seg;\n        kairo_seg_run_t *run[3];\n        uint32_t         record[CH_WORDS];\n        uint64_t         generation;\n        int              issued;\n        int              in_order;\n        int              pb; /* the pixel being recorded's bytes */\n    } *k_gpu;\n} chips_69000_t;\n"),
    ('86box/src/video/vid_chips_69000.c',
     '\nvoid\nchips_69000_process_pixel(chips_69000_t* chips, uint32_t pixel)\n{\n',
     "\n/* KairoX86#249: the run's operation in the batch: the record again only where it differs or the batch has been drawn */\nstatic void\nchips_69000_k_op(void *priv, bool in_order)\n{\n    chips_69000_t *chips = (chips_69000_t *) priv;\n    uint32_t       rec[CH_WORDS] = { 0 };\n\n    rec[CH_ROP]    = chips->bitblt_running.bitblt.bitblt_control & 0xff;\n    rec[CH_CTRL]   = chips->bitblt_running.bitblt.bitblt_control;\n    rec[CH_KEY]    = chips->bitblt_running.bitblt.monochrome_source_expansion_color_reg_select ? chips->bitblt_running.bitblt.source_key_bg\n                                                                                               : chips->bitblt_running.bitblt.pattern_source_key_bg;\n    rec[CH_PAT_FG] = chips->bitblt_running.bitblt.pattern_source_key_fg;\n    rec[CH_PAT_BG] = chips->bitblt_running.bitblt.pattern_source_key_bg;\n    rec[CH_BYTES]  = chips->k_gpu->pb;\n    kairo_seg_make_room(chips->k_gpu->seg);\n    if (chips->k_gpu->issued && (chips->k_gpu->in_order == in_order) && (chips->k_gpu->generation == kairo_seg_generation(chips->k_gpu->seg)) &&\n        !memcmp(chips->k_gpu->record, rec, sizeof(rec)))\n        return;\n    memcpy(kairo_seg_op(chips->k_gpu->seg, in_order), rec, sizeof(rec));\n    memcpy(chips->k_gpu->record, rec, sizeof(rec));\n    chips->k_gpu->generation = kairo_seg_generation(chips->k_gpu->seg);\n    chips->k_gpu->in_order   = in_order;\n    chips->k_gpu->issued     = 1;\n}\n\n/* Every run into the batch: the walk has ended, the processor may meet its pixels next */\nstatic void\nchips_69000_k_flush(chips_69000_t *chips)\n{\n    if (chips->k_gpu != NULL)\n        for (int i = 0; i < 3; i++)\n            kairo_seg_run_flush(chips->k_gpu->run[i]);\n}\n\n/* A pixel of a blit recorded for the GPU: its source (src_at, the address of its first byte, or KAIRO_SEG_RUN_NONE\n   for the pixel itself) and its pattern, as chips_69000_process_pixel finds them. 0 when one of its addresses is the\n   MMIO window (readb_linear's bit 22), which the processor draws (the batch first). */\nstatic int\nchips_69000_k_pixel(chips_69000_t *chips, uint32_t pixel, uint32_t src_at, uint32_t dest_addr)\n{\n    const uint32_t ctrl  = chips->bitblt_running.bitblt.bitblt_control;\n    const int      pb    = chips->bitblt_running.bytes_per_pixel;\n    const uint32_t mask  = (1 << (8 * pb)) - 1;\n    const uint8_t  vpa   = (ctrl >> 20) & 7;\n    const uint32_t vmask = 0x1fffff & chips->svga.vram_mask;\n    uint32_t       dst   = chips->bitblt_running.bitblt.destination_addr;\n    uint32_t       pat_at = KAIRO_SEG_RUN_NONE;\n    uint32_t       wp;\n\n    if (pb == 2)\n        dst >>= 1;\n    if (ctrl & (1 << 18)) {\n        if (ctrl & (1 << 19)) {\n            /* A solid mono pattern: its bits clear */\n            if (ctrl & (1 << 17))\n                return 1;\n            wp = CH_IMM | (chips->bitblt_running.bitblt.pattern_source_key_bg & mask);\n        } else {\n            pat_at = chips->bitblt_running.bitblt.pat_addr + ((vpa + (chips->bitblt_running.y & 7)) & 7);\n            wp     = CH_MONO | ((((pat_at & vmask) << 3) + (7 - ((dst + chips->bitblt_running.x) & 7))) & CH_ADDR_MASK);\n        }\n    } else {\n        if (pb == 1)\n            pat_at = chips->bitblt_running.bitblt.pat_addr + 8 * ((vpa + chips->bitblt_running.y) & 7) + (((dst & 7) + chips->bitblt_running.x) & 7);\n        else if (pb == 2)\n            pat_at = chips->bitblt_running.bitblt.pat_addr + (2 * 8 * ((vpa + chips->bitblt_running.y) & 7)) + (2 * (((dst & 7) + chips->bitblt_running.x) & 7));\n        else\n            pat_at = chips->bitblt_running.bitblt.pat_addr + (4 * 8 * ((vpa + chips->bitblt_running.y) & 7)) +\n                     (3 * ((((chips->bitblt_running.bitblt.destination_addr / 3) & 7) + chips->bitblt_running.x) & 7));\n        wp = pat_at & vmask;\n    }\n    if (((dest_addr + pb - 1) & 0x400000) || (dest_addr & 0x400000) || ((src_at != KAIRO_SEG_RUN_NONE) && (src_at & 0x400000)) ||\n        ((pat_at != KAIRO_SEG_RUN_NONE) && (pat_at & 0x400000)))\n        return 0;\n\n    const uint32_t words[CH_PIXEL_WORDS] = { (src_at == KAIRO_SEG_RUN_NONE) ? (CH_IMM | (pixel & 0xffffff)) : (src_at & vmask), wp };\n    const uint32_t reads[2]              = { (src_at == KAIRO_SEG_RUN_NONE) ? KAIRO_SEG_RUN_NONE : (src_at & vmask),\n                                             (pat_at == KAIRO_SEG_RUN_NONE) ? KAIRO_SEG_RUN_NONE : (pat_at & vmask) };\n\n    /* A run is of one pixel size: another size's run goes in first */\n    for (int i = 0; i < 3; i++)\n        if (i != pb - 1)\n            kairo_seg_run_flush(chips->k_gpu->run[i]);\n    chips->k_gpu->pb = pb;\n    kairo_seg_run_pixel(chips->k_gpu->run[pb - 1], dest_addr & vmask, words, reads);\n    return 1;\n}\n\nstatic void\nchips_69000_process_pixel_at(chips_69000_t* chips, uint32_t pixel, uint32_t src_at);\n\nvoid\nchips_69000_process_pixel(chips_69000_t* chips, uint32_t pixel)\n{\n    chips_69000_process_pixel_at(chips, pixel, KAIRO_SEG_RUN_NONE);\n}\n\n/* KairoX86#249: src_at, with Hardware acceleration on, the address of a source pixel in video memory not yet read */\nstatic void\nchips_69000_process_pixel_at(chips_69000_t* chips, uint32_t pixel, uint32_t src_at)\n{\n"),
    ('86box/src/video/vid_chips_69000.c',
     '    uint8_t orig_dest_addr_bit = chips->bitblt_running.bitblt.destination_addr & 1;\n\n',
     "    uint8_t orig_dest_addr_bit = chips->bitblt_running.bitblt.destination_addr & 1;\n\n    if (chips->k_gpu != NULL) {\n        if (chips_69000_k_pixel(chips, pixel, src_at, dest_addr))\n            return;\n        /* The processor's: the batch first, and the source pixel now */\n        chips_69000_k_flush(chips);\n        kairo_seg_drain(chips->k_gpu->seg);\n        if (src_at != KAIRO_SEG_RUN_NONE) {\n            pixel = chips_69000_readb_linear(src_at, chips);\n            if (chips->bitblt_running.bytes_per_pixel >= 2)\n                pixel |= chips_69000_readb_linear(src_at + 1, chips) << 8;\n            if (chips->bitblt_running.bytes_per_pixel >= 3)\n                pixel |= chips_69000_readb_linear(src_at + 2, chips) << 16;\n        }\n    }\n\n"),
    ('86box/src/video/vid_chips_69000.c',
     '            uint32_t source_addr = chips->bitblt_running.bitblt.source_addr + (chips->bitblt_running.y * chips->bitblt.source_span) + (chips->bitblt_running.x * chips->bitblt_running.bytes_per_pixel);\n\n',
     '            uint32_t source_addr = chips->bitblt_running.bitblt.source_addr + (chips->bitblt_running.y * chips->bitblt.source_span) + (chips->bitblt_running.x * chips->bitblt_running.bytes_per_pixel);\n\n            /* KairoX86#249: on the GPU the source is read where the pixel is drawn */\n            if (chips->k_gpu != NULL) {\n                chips_69000_process_pixel_at(chips, 0, source_addr);\n                chips->bitblt_running.x += chips->bitblt_running.x_dir;\n                continue;\n            }\n\n'),
    ('86box/src/video/vid_chips_69000.c',
     '        chips_69000_bitblt_write(chips, val);\n        return;\n',
     '        chips_69000_bitblt_write(chips, val);\n        chips_69000_k_flush(chips); /* KairoX86#249 */\n        return;\n'),
    ('86box/src/video/vid_chips_69000.c',
     '                chips_69000_setup_bitblt(chips);\n            }\n',
     '                chips_69000_setup_bitblt(chips);\n                chips_69000_k_flush(chips); /* KairoX86#249 */\n            }\n'),
    ('86box/src/video/vid_chips_69000.c',
     '        chips_69000_bitblt_write(chips, (val >> 8) & 0xFF);\n        return;\n',
     '        chips_69000_bitblt_write(chips, (val >> 8) & 0xFF);\n        chips_69000_k_flush(chips); /* KairoX86#249 */\n        return;\n'),
    ('86box/src/video/vid_chips_69000.c',
     '        chips_69000_bitblt_write(chips, (val >> 24) & 0xFF);\n        return;\n',
     '        chips_69000_bitblt_write(chips, (val >> 24) & 0xFF);\n        chips_69000_k_flush(chips); /* KairoX86#249 */\n        return;\n'),
    ('86box/src/video/vid_chips_69000.c',
     '    if (reset_state != NULL) {\n        chips_69000_disable_handlers(chips);\n        reset_state->slot = chips->slot;\n\n        *chips = *reset_state;\n    }\n}\n',
     "    if (reset_state != NULL) {\n        if (chips->k_gpu != NULL) /* KairoX86#249: the batch drawn; the reset state holds the same one */\n            kairo_seg_drain(chips->k_gpu->seg);\n        chips_69000_disable_handlers(chips);\n        reset_state->slot = chips->slot;\n\n        *chips = *reset_state;\n    }\n}\n\n/* KairoX86#249: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\nchips_69000_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const chips_69000_t *chips = (const chips_69000_t *) svga->priv;\n\n    kairo_seg_touch(chips->k_gpu->seg, addr & chips->svga.vram_mask, len);\n}\n"),
    ('86box/src/video/vid_chips_69000.c',
     '    chips->svga.packed_chain4 = 1;\n\n',
     '    chips->svga.packed_chain4 = 1;\n\n    /* KairoX86#249: with Hardware acceleration on, the BitBLT engine\'s pixels drawn on the GPU (reset keeps the batch) */\n    if (kairo_gpu_on) {\n        chips->k_gpu = calloc(1, sizeof(*chips->k_gpu));\n        if (chips->k_gpu == NULL)\n            fatal("B69000 on the GPU: no memory\\n");\n        chips->k_gpu->seg = kairo_chips69000_open(chips->svga.vram, chips->svga.vram_mask, chips->svga.changedvram,\n                                                  &chips->svga.monitor->mon_changeframecount);\n        for (int i = 0; i < 3; i++)\n            chips->k_gpu->run[i] = kairo_seg_run_open(chips->k_gpu->seg, chips->svga.vram_mask, i + 1, CH_PIXEL_WORDS, 2, chips_69000_k_op, chips);\n        chips->svga.kairo_touch = chips_69000_svga_touch;\n    }\n\n'),
    ('86box/src/video/vid_chips_69000.c',
     '    i2c_gpio_close(chips->i2c);\n    svga_close(&chips->svga);\n',
     '    i2c_gpio_close(chips->i2c);\n    if (chips->k_gpu != NULL) {\n        kairo_seg_close(chips->k_gpu->seg); /* KairoX86#249 */\n        for (int i = 0; i < 3; i++)\n            kairo_seg_run_close(chips->k_gpu->run[i]);\n        free(chips->k_gpu);\n    }\n    svga_close(&chips->svga);\n'),
]

# KairoX86#274: the Trident TGUI graphics engine on the GPU (86box/kairo_gpu_tgui.h, an added file, core/kairo/gpu_tgui.c,
# core/kairo/shaders/tgui.comp), on the drawing engines' shared batches as runs of 1, 2 and 4-byte pixels. Every draw
# of tgui_accel_command (blits, scanlines, Bresenham lines, short vectors, fast lines) goes through one helper,
# tgui_draw_pixel; with Hardware acceleration on it records each pixel's source and pattern.
KAIROX86_GPU_TGUI = [
    ('86box/src/video/vid_tgui9440.c',
     '#include <86box/vid_svga_render.h>\n\n',
     '#include <86box/vid_svga_render.h>\n#include <86box/kairo_gpu.h> /* KairoX86#274 */\n#include <86box/kairo_gpu_seg.h>\n#include <86box/kairo_gpu_tgui.h>\n\n'),
    ('86box/src/video/vid_tgui9440.c',
     '    int has_bios;\n} tgui_t;\n',
     "    int has_bios;\n\n    /* KairoX86#274: the graphics engine's batch on the GPU and its runs, one per 1, 2 and 4 bytes a pixel; NULL in\n       software */\n    struct {\n        kairo_seg_t     *seg;\n        kairo_seg_run_t *run[3];\n        uint32_t         record[TG_WORDS];\n        uint64_t         generation;\n        int              issued;\n        int              in_order;\n        uint32_t         trans; /* the pixel being recorded's transparent colour and bytes */\n        int              pb;\n    } *k_gpu;\n} tgui_t;\n"),
    ('86box/src/video/vid_tgui9440.c',
     '    addr  = dword_remap(svga, addr);\n\n',
     "    addr  = dword_remap(svga, addr);\n    if (svga->kairo_touch != NULL) /* KairoX86#274: the latches' bytes, 0Dh apart in fours */\n        svga->kairo_touch(svga, addr, 64);\n\n"),
    ('86box/src/video/vid_tgui9440.c',
     '    addr &= (svga->gdcreg[0x10] & EXT_CTRL_LATCH_COPY) ? ~0x0f : ~0x07;\n    addr = dword_remap(svga, addr);\n\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n',
     '    addr &= (svga->gdcreg[0x10] & EXT_CTRL_LATCH_COPY) ? ~0x0f : ~0x07;\n    addr = dword_remap(svga, addr);\n    if (svga->kairo_touch != NULL) /* KairoX86#274 */\n        svga->kairo_touch(svga, addr, 16);\n\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_tgui9440.c',
     '    addr &= ~0x0f;\n    addr = dword_remap(svga, addr);\n\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n',
     '    addr &= ~0x0f;\n    addr = dword_remap(svga, addr);\n    if (svga->kairo_touch != NULL) /* KairoX86#274 */\n        svga->kairo_touch(svga, addr, 32);\n\n    svga->changedvram[addr >> 12] = svga->monitor->mon_changeframecount;\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\nstatic void\ntgui_accel_command(int count, uint32_t cpu_dat, tgui_t *tgui)\n{\n',
     "\n/* KairoX86#274: the run's operation in the batch: the record again only where it differs or the batch has been drawn */\nstatic void\ntgui_k_op(void *priv, bool in_order)\n{\n    tgui_t  *tgui          = (tgui_t *) priv;\n    uint32_t rec[TG_WORDS] = { 0 };\n\n    rec[TG_ROP]   = tgui->accel.rop;\n    rec[TG_TRANS] = tgui->k_gpu->trans;\n    rec[TG_BYTES] = tgui->k_gpu->pb;\n    kairo_seg_make_room(tgui->k_gpu->seg);\n    if (tgui->k_gpu->issued && (tgui->k_gpu->in_order == in_order) && (tgui->k_gpu->generation == kairo_seg_generation(tgui->k_gpu->seg)) &&\n        !memcmp(tgui->k_gpu->record, rec, sizeof(rec)))\n        return;\n    memcpy(kairo_seg_op(tgui->k_gpu->seg, in_order), rec, sizeof(rec));\n    memcpy(tgui->k_gpu->record, rec, sizeof(rec));\n    tgui->k_gpu->generation = kairo_seg_generation(tgui->k_gpu->seg);\n    tgui->k_gpu->in_order   = in_order;\n    tgui->k_gpu->issued     = 1;\n}\n\n#define TGUI_K_NONE 0xffffffffu\n\n/* One pixel of an operation, at pixel dst: through the raster operation with the pattern pat_dat and the source\n   src_dat, or (src_at not TGUI_K_NONE) the pixel at src_at, left where cmp and that source is trans_col. With\n   Hardware acceleration on, recorded for the GPU. */\nstatic void\ntgui_draw_pixel(tgui_t *tgui, uint32_t dst, uint32_t src_dat, uint32_t src_at, uint32_t pat_dat, int cmp, uint32_t trans_col)\n{\n    svga_t   *svga   = &tgui->svga;\n    uint16_t *vram_w = (uint16_t *) svga->vram;\n    uint32_t *vram_l = (uint32_t *) svga->vram;\n    uint32_t  dst_dat;\n    uint32_t  out;\n\n    if (tgui->k_gpu != NULL) {\n        const int      shift                 = (tgui->accel.bpp == 0) ? 0 : (tgui->accel.bpp == 1) ? 1 : 2;\n        const uint32_t pmask                 = tgui->vram_mask >> shift;\n        const uint32_t s_at                  = (src_at != TGUI_K_NONE) ? ((src_at & pmask) << shift) : KAIRO_SEG_RUN_NONE;\n        const uint32_t words[TG_PIXEL_WORDS] = { ((src_at != TGUI_K_NONE) ? TGK_ADDR : 0) | (cmp ? TGK_CMP : 0),\n                                                 (src_at != TGUI_K_NONE) ? s_at : src_dat, pat_dat };\n        const uint32_t reads[1]              = { s_at };\n\n        /* A run is of one pixel size, one transparent colour */\n        for (int i = 0; i < 3; i++)\n            if ((i != shift) || (tgui->k_gpu->trans != trans_col))\n                kairo_seg_run_flush(tgui->k_gpu->run[i]);\n        tgui->k_gpu->trans = trans_col;\n        tgui->k_gpu->pb    = 1 << shift;\n        kairo_seg_run_pixel(tgui->k_gpu->run[shift], (dst & pmask) << shift, words, reads);\n        return;\n    }\n\n    if (src_at != TGUI_K_NONE) {\n        READ(src_at, src_dat);\n    }\n    if (cmp && (src_dat == trans_col))\n        return;\n    READ(dst, dst_dat);\n    MIX();\n    WRITE(dst, out);\n}\n\n/* Every run into the batch: the command has ended, the processor may meet its pixels next */\nstatic void\ntgui_k_flush(tgui_t *tgui)\n{\n    if (tgui->k_gpu != NULL)\n        for (int i = 0; i < 3; i++)\n            kairo_seg_run_flush(tgui->k_gpu->run[i]);\n}\n\nstatic void tgui_accel_command_walk(int count, uint32_t cpu_dat, tgui_t *tgui);\n\nstatic void\ntgui_accel_command(int count, uint32_t cpu_dat, tgui_t *tgui)\n{\n    tgui_accel_command_walk(count, cpu_dat, tgui);\n    tgui_k_flush(tgui);\n}\n\nstatic void\ntgui_accel_command_walk(int count, uint32_t cpu_dat, tgui_t *tgui)\n{\n"),
    ('86box/src/video/vid_tgui9440.c',
     '                            }\n\n\n                            READ(tgui->accel.dst, dst_dat);\n\n                            pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n\n                            if (tgui->accel.bpp == 0)\n',
     '                            }\n\n\n                            pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n\n                            if (tgui->accel.bpp == 0)\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\n                            if ((((tgui->accel.flags & (TGUI_PATMONO | TGUI_TRANSENA)) == (TGUI_TRANSENA | TGUI_PATMONO)) && (pat_dat != trans_col)) || !(tgui->accel.flags & TGUI_PATMONO) || ((tgui->accel.flags & (TGUI_PATMONO | TGUI_TRANSENA)) == TGUI_PATMONO) || (tgui->accel.ger22 & 0x200)) {\n                                MIX();\n\n                                WRITE(tgui->accel.dst, out);\n                            }\n                        }\n',
     '\n                            if ((((tgui->accel.flags & (TGUI_PATMONO | TGUI_TRANSENA)) == (TGUI_TRANSENA | TGUI_PATMONO)) && (pat_dat != trans_col)) || !(tgui->accel.flags & TGUI_PATMONO) || ((tgui->accel.flags & (TGUI_PATMONO | TGUI_TRANSENA)) == TGUI_PATMONO) || (tgui->accel.ger22 & 0x200))\n                                tgui_draw_pixel(tgui, tgui->accel.dst, src_dat, TGUI_K_NONE, pat_dat, 0, trans_col);\n                        }\n'),
    ('86box/src/video/vid_tgui9440.c',
     '                                src_dat &= 0xffff;\n\n                            READ(tgui->accel.dst, dst_dat);\n\n                            pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n\n',
     '                                src_dat &= 0xffff;\n\n                            pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\n                            if (!(tgui->accel.flags & TGUI_TRANSENA) || (src_dat != trans_col)) {\n                                MIX();\n\n                                WRITE(tgui->accel.dst, out);\n                            }\n                        }\n',
     '\n                            if (!(tgui->accel.flags & TGUI_TRANSENA) || (src_dat != trans_col))\n                                tgui_draw_pixel(tgui, tgui->accel.dst, src_dat, TGUI_K_NONE, pat_dat, 0, trans_col);\n                        }\n'),
    ('86box/src/video/vid_tgui9440.c',
     '                    while (count--) {\n                        READ(tgui->accel.src, src_dat);\n                        READ(tgui->accel.dst, dst_dat);\n\n                        pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n',
     '                    while (count--) {\n                        pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\n                        if (!(tgui->accel.flags & TGUI_TRANSENA) || (src_dat != trans_col)) {\n                            MIX();\n\n                            WRITE(tgui->accel.dst, out);\n                        }\n\n',
     '\n                        tgui_draw_pixel(tgui, tgui->accel.dst, src_dat, tgui->accel.src, pat_dat, !!(tgui->accel.flags & TGUI_TRANSENA), trans_col);\n\n'),
    ('86box/src/video/vid_tgui9440.c',
     '            while (count--) {\n                READ(tgui->accel.src, src_dat);\n                READ(tgui->accel.dst, dst_dat);\n\n                pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n',
     '            while (count--) {\n                pat_dat = pattern_data[((tgui->accel.pat_y & 7) * 8) + (tgui->accel.pat_x & 7)];\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\n                if (!(tgui->accel.flags & TGUI_TRANSENA) || (src_dat != trans_col)) {\n                    MIX();\n\n                    WRITE(tgui->accel.dst, out);\n                }\n\n',
     '\n                tgui_draw_pixel(tgui, tgui->accel.dst, src_dat, tgui->accel.src, pat_dat, !!(tgui->accel.flags & TGUI_TRANSENA), trans_col);\n\n'),
    ('86box/src/video/vid_tgui9440.c',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    READ(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), dst_dat);\n\n                    pat_dat = tgui->accel.fg_col;\n\n                    MIX();\n\n                    WRITE(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), out);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                if (tgui->accel.size_x >= 0) {\n',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    tgui_draw_pixel(tgui, tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), src_dat, TGUI_K_NONE, tgui->accel.fg_col, 0, trans_col);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                if (tgui->accel.size_x >= 0) {\n'),
    ('86box/src/video/vid_tgui9440.c',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    READ(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), dst_dat);\n\n                    pat_dat = tgui->accel.fg_col;\n\n                    MIX();\n\n                    WRITE(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), out);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                switch ((tgui->accel.sv_size_y >> 8) & 0xe0) {\n',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    tgui_draw_pixel(tgui, tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), src_dat, TGUI_K_NONE, tgui->accel.fg_col, 0, trans_col);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                switch ((tgui->accel.sv_size_y >> 8) & 0xe0) {\n'),
    ('86box/src/video/vid_tgui9440.c',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    READ(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), dst_dat);\n\n                    pat_dat = tgui->accel.fg_col;\n\n                    MIX();\n\n                    WRITE(tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), out);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                switch ((tgui->accel.size_y >> 8) & 0xe0) {\n',
     '                }\n            }\n\n            while (count--) {\n                /*Note by TC1995: I suppose the x/y clipping max is always more than 0 in the TGUI 96xx, but the TGUI 9440 lacks clipping*/\n                if ((tgui->type == TGUI_9440) || ((tgui->type >= TGUI_9660) && ((tgui->accel.dx & 0xfff) >= tgui->accel.left) && ((tgui->accel.dx & 0xfff) <= tgui->accel.right) && ((tgui->accel.dy & 0xfff) >= tgui->accel.top) && ((tgui->accel.dy & 0xfff) <= tgui->accel.bottom))) {\n                    tgui_draw_pixel(tgui, tgui->accel.dx + (tgui->accel.dy * tgui->accel.pitch), src_dat, TGUI_K_NONE, tgui->accel.fg_col, 0, trans_col);\n                }\n\n                if (!tgui->accel.y)\n                    break;\n\n                switch ((tgui->accel.size_y >> 8) & 0xe0) {\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\nstatic void *\n',
     "\n/* KairoX86#274: the SVGA core's memory handlers and display (svga->kairo_touch) */\nstatic void\ntgui_svga_touch(svga_t *svga, uint32_t addr, uint32_t len)\n{\n    const tgui_t *tgui = (const tgui_t *) svga->priv;\n\n    kairo_seg_touch(tgui->k_gpu->seg, addr & tgui->vram_mask, len);\n}\n\nstatic void *\n"),
    ('86box/src/video/vid_tgui9440.c',
     '        svga->ramdac = device_add(&tkd8001_ramdac_device);\n\n',
     '        svga->ramdac = device_add(&tkd8001_ramdac_device);\n\n    /* KairoX86#274: with Hardware acceleration on, the graphics engine\'s pixels drawn on the GPU */\n    if (kairo_gpu_on) {\n        tgui->k_gpu = calloc(1, sizeof(*tgui->k_gpu));\n        if (tgui->k_gpu == NULL)\n            fatal("TGUI on the GPU: no memory\\n");\n        tgui->k_gpu->seg = kairo_tgui_open(svga->vram, tgui->vram_mask, svga->changedvram, &svga->monitor->mon_changeframecount);\n        for (int i = 0; i < 3; i++)\n            tgui->k_gpu->run[i] = kairo_seg_run_open(tgui->k_gpu->seg, tgui->vram_mask, 1 << i, TG_PIXEL_WORDS, 1, tgui_k_op, tgui);\n        svga->kairo_touch = tgui_svga_touch;\n    }\n\n'),
    ('86box/src/video/vid_tgui9440.c',
     '\n    svga_close(&tgui->svga);\n',
     '\n    if (tgui->k_gpu != NULL) {\n        kairo_seg_close(tgui->k_gpu->seg); /* KairoX86#274 */\n        for (int i = 0; i < 3; i++)\n            kairo_seg_run_close(tgui->k_gpu->run[i]);\n        free(tgui->k_gpu);\n    }\n    svga_close(&tgui->svga);\n'),
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
    'kairox86-voodoo-changed-pages': KAIROX86_VOODOO_CHANGED_PAGES,
    'kairox86-gpu-voodoo': KAIROX86_GPU_VOODOO,
    'kairox86-voodoo-stipple': KAIROX86_VOODOO_STIPPLE,
    'kairox86-voodoo-depth-source': KAIROX86_VOODOO_DEPTH_SOURCE,
    'kairox86-voodoo-display-settle': KAIROX86_VOODOO_DISPLAY_SETTLE,
    'kairox86-gpu-scanout-rest': KAIROX86_GPU_SCANOUT_REST,
    'kairox86-virge-clip-and-settle': KAIROX86_VIRGE_CLIP_AND_SETTLE,
    'kairox86-gpu-virge': KAIROX86_GPU_VIRGE,
    'kairox86-gpu-display-touch': KAIROX86_GPU_DISPLAY_TOUCH,
    'kairox86-gpu-mach64': KAIROX86_GPU_MACH64,
    'kairox86-powervr-render-timing': KAIROX86_POWERVR_RENDER_TIMING,
    'kairox86-gpu-powervr': KAIROX86_GPU_POWERVR,
    'kairox86-mach64-display-settle': KAIROX86_MACH64_DISPLAY_SETTLE,
    'kairox86-gpu-mach64-2d': KAIROX86_GPU_MACH64_2D,
    'kairox86-p9100-outline': KAIROX86_P9100_OUTLINE,
    'kairox86-gpu-p9100': KAIROX86_GPU_P9100,
    'kairox86-gpu-et4000w32': KAIROX86_GPU_ET4000W32,
    'kairox86-gpu-cl54xx': KAIROX86_GPU_CL54XX,
    'kairox86-gpu-chips69000': KAIROX86_GPU_CHIPS69000,
    'kairox86-gpu-tgui': KAIROX86_GPU_TGUI,
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
    '86box/src/include/86box/kairo_gpu_chips69000.h',
    '86box/src/include/86box/kairo_gpu_cl54xx.h',
    '86box/src/include/86box/kairo_gpu_et4000w32.h',
    '86box/src/include/86box/kairo_gpu_mach64.h',
    '86box/src/include/86box/kairo_gpu_p9100.h',
    '86box/src/include/86box/kairo_gpu_powervr.h',
    '86box/src/include/86box/kairo_gpu_seg.h',
    '86box/src/include/86box/kairo_gpu_tgui.h',
    '86box/src/include/86box/kairo_gpu_virge.h',
    '86box/src/include/86box/kairo_gpu_voodoo.h',
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
