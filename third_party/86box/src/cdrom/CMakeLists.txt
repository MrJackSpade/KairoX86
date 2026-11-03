#
# 86Box    A hypervisor and IBM PC system emulator that specializes in
#          running old operating systems and software designed for IBM
#          PC systems and compatibles from 1981 through fairly recent
#          system designs based on the PCI bus.
#
#          This file is part of the 86Box distribution.
#
#          CMake build script.
#
# Authors: David Hrdlička, <hrdlickadavid@outlook.com>
#          Jasmine Iwanek, <jriwanek@gmail.com>
#
#          Copyright 2020-2021 David Hrdlička.
#          Copyright 2024-2026 Jasmine Iwanek.
#

set(WITH_SYSTEM_ZLIB ON)
set(WITH_SYSTEM_ZSTD ON)
# KairoX86: KAIRO_LIBCHDR names a chdr-static the build already has (the shared frontend's).
if(NOT KAIRO_LIBCHDR)
    add_subdirectory(libchdr)
endif()

find_package(SndFile CONFIG REQUIRED)
# KairoX86: an interface over SndFile::sndfile, which may itself be an alias (libsndfile built
# from source names it one), and an alias of an alias is not allowed.
add_library(PkgConfig::SNDFILE INTERFACE IMPORTED)
target_link_libraries(PkgConfig::SNDFILE INTERFACE SndFile::sndfile)

add_library(cdrom OBJECT
    cdrom.c
    cdrom_aaru.c
    cdrom_image.c
    cdrom_image_viso.c
    cdrom_mitsumi.c
    cdrom_mke.c
    cdrom_hitachi.c
    cdrom_philips.c
    cdrom_sony.c
    cdrom_cm153.c
    cm100.c
    cm100_protocol.c
    cm100_datapath.c
    cm153_uart.c
    cdrom_chd.c
)
target_link_libraries(cdrom chdr-static)
# KairoX86: the CD image reader includes sndfile.h, which libsndfile built from source writes
# into its build folder; linking it gives the reader its headers and builds it first.
target_link_libraries(cdrom PkgConfig::SNDFILE)
if(NOT WIN32)
	target_include_directories(86Box PRIVATE PkgConfig::SNDFILE)
endif()
if(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")
	target_include_directories(cdrom PRIVATE /usr/local/include)
endif()
target_link_libraries(86Box PkgConfig::SNDFILE)

if (WIN32)
    # MSYS2
    target_link_libraries(86Box -static ${SNDFILE_STATIC_LIBRARIES})
endif()
