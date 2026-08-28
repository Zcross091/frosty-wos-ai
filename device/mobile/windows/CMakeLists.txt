cmake_minimum_required(VERSION 3.14)
project(frosty_wos_ai LANGUAGES CXX)

set(BINARY_NAME "frosty_wos_ai")

cmake_policy(SET CMP0079 NEW)

# Flutter Windows build configurations
set(FLUTTER_MANAGED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/flutter")

add_subdirectory(${FLUTTER_MANAGED_DIR})
add_subdirectory("runner")

# Build target
add_dependencies(${BINARY_NAME} flutter_assemble)
