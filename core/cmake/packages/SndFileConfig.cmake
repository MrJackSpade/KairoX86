# KairoX86: 86Box's find_package(SndFile CONFIG) finds the libsndfile core/CMakeLists.txt builds
# from third_party/libsndfile before 86Box, whose own build names it SndFile::sndfile.
if(NOT TARGET SndFile::sndfile)
    message(FATAL_ERROR "SndFileConfig: SndFile::sndfile is not built; core/CMakeLists.txt adds libsndfile first")
endif()
set(SndFile_FOUND TRUE)
