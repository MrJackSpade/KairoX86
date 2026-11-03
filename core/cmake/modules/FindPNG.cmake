# KairoX86: 86Box's find_package(PNG) finds the shared frontend's libpng (kairo_png,
# shared/cmake/KairoLibraries.cmake), which core/CMakeLists.txt builds before 86Box.
if(NOT TARGET kairo_png)
    message(FATAL_ERROR "FindPNG: kairo_png is not built; include shared/cmake/KairoLibraries.cmake first")
endif()
get_target_property(PNG_INCLUDE_DIRS kairo_png INTERFACE_INCLUDE_DIRECTORIES)
set(PNG_INCLUDE_DIR "${PNG_INCLUDE_DIRS}")
set(PNG_LIBRARIES kairo_png)
set(PNG_FOUND TRUE)
if(NOT TARGET PNG::PNG)
    add_library(PNG::PNG INTERFACE IMPORTED GLOBAL)
    target_link_libraries(PNG::PNG INTERFACE kairo_png)
endif()
