cmake_minimum_required(VERSION 3.22.1)
project(kairox86 LANGUAGES C CXX)

get_filename_component(KAIROX86_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../.." ABSOLUTE)
include("${KAIROX86_ROOT}/shared/cmake/KairoMachine.cmake")

# The IBM PC compatible on 86Box, driven one frame at a time (core/).
add_subdirectory("${KAIROX86_ROOT}/core" core)

kairo_machine_library(kairox86 x86_core.cpp)
target_link_libraries(kairox86 PRIVATE kairox86_core)
