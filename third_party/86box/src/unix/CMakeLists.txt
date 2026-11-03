# POC: headless frontend (automation socket only).

add_library(plat OBJECT
    headless_main.c
    sdl_plat.c
)
target_include_directories(plat PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/headless_sdl)

if(WIN32)
    target_sources(plat PRIVATE
        sdl_plat_win.c
        ../qt/win_netsocket.c
        ../qt/win_dynld.c
        ../qt/win_cdrom_ioctl.c
        dummy_floppy_ioctl.c
    )
    target_link_libraries(86Box ws2_32)
else()
    target_sources(plat PRIVATE
        sdl_plat_unix.c
        unix_netsocket.c
        unix_dynld.c
        dummy_cdrom_ioctl.c
        dummy_floppy_ioctl.c
    )
endif()

add_library(ui OBJECT
    sdl_cdrom.c
)

find_package(Threads REQUIRED)
target_link_libraries(86Box Threads::Threads)

target_compile_definitions(plat PUBLIC _FILE_OFFSET_BITS=64)
target_link_libraries(plat ${CMAKE_DL_LIBS})
