cmake_minimum_required(VERSION 3.20)

# Find Google Test (optional)
find_package(GTest)
find_package(Threads REQUIRED)

if(NOT GTest_FOUND)
    message(WARNING "Google Test not found. Tests will be disabled. Install GoogleTest to enable testing.")
    return()
endif()

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/include
    ${GTEST_INCLUDE_DIRS}
)

# Test source files
set(TEST_SOURCES
    test_main.cpp
    test_obfuscation_engine.cpp
    test_passes.cpp
    test_utils.cpp
    test_ai.cpp
    test_blockchain.cpp
)

# Create test executable
add_executable(h5x_tests ${TEST_SOURCES})

# Link libraries
target_link_libraries(h5x_tests
    h5x_core
    ${GTEST_LIBRARIES}
    ${GTEST_MAIN_LIBRARIES}
    Threads::Threads
)

# Add test target
add_test(NAME h5x_unit_tests COMMAND h5x_tests)

# Custom test targets
add_custom_target(test_verbose
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/h5x_tests --gtest_output=xml:test_results.xml
    DEPENDS h5x_tests
    COMMENT "Running tests with verbose output"
)

add_custom_target(test_quick
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/h5x_tests --gtest_filter=-*Slow*
    DEPENDS h5x_tests
    COMMENT "Running quick tests only"
)

# Code coverage (if available)
if(CMAKE_BUILD_TYPE MATCHES "Debug")
    if(CMAKE_COMPILER_IS_GNUCXX)
        target_compile_options(h5x_tests PRIVATE --coverage)
        target_link_libraries(h5x_tests --coverage)
    endif()
endif()