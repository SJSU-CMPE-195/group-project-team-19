cmake_minimum_required(VERSION 3.20)
project(blundr
        LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS_DIR ${CMAKE_SOURCE_DIR})

if(ENABLE_WARNINGS)
    if(MSVC)
        add_compile_options(/W4)
        if(WARNINGS_AS_ERRORS)
            add_compile_options(/WX)
        endif()
    else()
        add_compile_options(
            -Wall           # Enable most warnings
            -Wextra         # Enable extra warnings
            -Wpedantic      # Enforce strict ISO C++
        )
        if(WARNINGS_AS_ERRORS)
            add_compile_options(-Werror)
        endif()
    endif()
endif()

# Optimization flags based on build type
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O3)
elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-O0 -g)
endif()

set(SOURCES
    src/main.cpp
    src/serialmanager.cpp)

set(HEADERS
    include/interlocks.hpp
    include/motioncontroller.hpp
    include/servocontroller.hpp
    include/timers.hpp
    include/trajectplanner.hpp)

set(INCLUDE_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(${PROJECT_NAME}
    ${SOURCES}
    ${HEADERS})

target_include_directories(${PROJECT_NAME}
  PRIVATE ${INCLUDE_DIRS})

target_compile_options(${PROJECT_NAME} PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-pthread>
    $<$<CXX_COMPILER_ID:Clang>:-pthread>
)
