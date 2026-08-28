cmake_minimum_required(VERSION 3.10)
project(frosty_wos_ai LANGUAGES CXX)

set(BINARY_NAME "frosty_wos_ai")
set(APPLICATION_ID "com.statecraft.frosty_wos_ai")

cmake_policy(SET CMP0079 NEW)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTK REQUIRED IMPORTED_TARGET gtk+-3.0)

add_subdirectory("flutter")

add_executable(${BINARY_NAME}
  "main.cc"
  "my_application.cc"
)

apply_standard_settings(${BINARY_NAME})

target_include_directories(${BINARY_NAME} PRIVATE
  "${CMAKE_SOURCE_DIR}"
)

target_link_libraries(${BINARY_NAME} PRIVATE
  flutter
  PkgConfig::GTK
)
