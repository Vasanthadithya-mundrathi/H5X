cmake_minimum_required(VERSION 3.20)
project(H5X_Advanced_Obfuscation_Engine VERSION 1.0.0)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -DDEBUG")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native")

# Add LLVM compile flags if available
if(LLVM_CXXFLAGS)
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} ${LLVM_CXXFLAGS}")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} ${LLVM_CXXFLAGS}")
endif()

# Find required packages
find_package(PkgConfig REQUIRED)

# LLVM Configuration - Use llvm-config for proper linking
set(LLVM_ROOT "/opt/homebrew/Cellar/llvm@18/18.1.8")
set(LLVM_CONFIG "${LLVM_ROOT}/bin/llvm-config")

# Check if LLVM exists and get proper linking flags
if(EXISTS "${LLVM_CONFIG}")
    message(STATUS "Found LLVM at ${LLVM_ROOT}")

    # Get LLVM include directories
    execute_process(
        COMMAND ${LLVM_CONFIG} --includedir
        OUTPUT_VARIABLE LLVM_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get LLVM library directories
    execute_process(
        COMMAND ${LLVM_CONFIG} --libdir
        OUTPUT_VARIABLE LLVM_LIBRARY_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get required LLVM libraries for our use case
    execute_process(
        COMMAND ${LLVM_CONFIG} --libs core irreader bitwriter target aarch64codegen aarch64asmparser passes transformutils analysis support
        OUTPUT_VARIABLE LLVM_LIBS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get LLVM system libraries
    execute_process(
        COMMAND ${LLVM_CONFIG} --system-libs
        OUTPUT_VARIABLE LLVM_SYSTEM_LIBS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get LLVM compile flags
    execute_process(
        COMMAND ${LLVM_CONFIG} --cxxflags
        OUTPUT_VARIABLE LLVM_CXXFLAGS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Clean up the library flags (remove -l prefix and separate)
    string(REPLACE "-l" "" LLVM_LIBS "${LLVM_LIBS}")
    string(REPLACE " " ";" LLVM_LIBS "${LLVM_LIBS}")

    # Add full paths to LLVM libraries
    set(LLVM_FULL_LIBS "")
    foreach(lib ${LLVM_LIBS})
        if(EXISTS "${LLVM_LIBRARY_DIRS}/lib${lib}.dylib")
            list(APPEND LLVM_FULL_LIBS "${LLVM_LIBRARY_DIRS}/lib${lib}.dylib")
        elseif(EXISTS "${LLVM_LIBRARY_DIRS}/lib${lib}.a")
            list(APPEND LLVM_FULL_LIBS "${LLVM_LIBRARY_DIRS}/lib${lib}.a")
        endif()
    endforeach()

    include_directories(${LLVM_INCLUDE_DIRS})

    # Add LLVM compile definitions
    add_definitions(-DHAVE_LLVM=1)

    message(STATUS "LLVM includes: ${LLVM_INCLUDE_DIRS}")
    message(STATUS "LLVM libraries: ${LLVM_FULL_LIBS}")
    message(STATUS "LLVM system libs: ${LLVM_SYSTEM_LIBS}")
else()
    message(WARNING "LLVM config not found at ${LLVM_CONFIG}, using mock implementation")
    set(LLVM_FULL_LIBS "")
    set(USE_MOCK_LLVM ON)
    add_definitions(-DUSE_MOCK_LLVM)
endif()

# Find OpenSSL for cryptographic functions
find_package(OpenSSL REQUIRED)

# Find CURL for HTTP/RPC communication (blockchain)
find_package(CURL REQUIRED)

# Find jsoncpp for JSON handling
find_package(PkgConfig REQUIRED)
pkg_check_modules(JSONCPP jsoncpp)

# Try to find system jsoncpp, fallback to bundled if not found
if(NOT JSONCPP_FOUND)
    message(STATUS "System jsoncpp not found, will use fallback implementation")
    set(JSONCPP_LIBRARIES "")
    add_definitions(-DUSE_FALLBACK_JSON)
endif()

if(NOT JSONCPP_FOUND)
    message(WARNING "jsoncpp not found, using header-only JSON library")
    set(USE_HEADER_ONLY_JSON ON)
    add_definitions(-DUSE_HEADER_ONLY_JSON)
endif()

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/third_party
)

# Source files
set(CORE_SOURCES
    src/core/H5XObfuscationEngine.cpp
    src/core/ObfuscationManager.cpp
    src/core/ObfuscationReporter.cpp
    src/core/ReportValidator.cpp
    src/core/ReportGenerator.cpp
    src/core/SecurityAnalyzer.cpp
    src/core/CrossPlatformBuilder.cpp
)

set(UTILS_SOURCES
    src/utils/Logger.cpp
    src/utils/ConfigParser.cpp
    src/utils/FileUtils.cpp
)

set(AI_SOURCES
    src/ai/GeneticOptimizer.cpp
)

set(BLOCKCHAIN_SOURCES
    src/blockchain/BlockchainVerifier.cpp
)

set(PASSES_SOURCES
    src/passes/InstructionSubstitution.cpp
    src/passes/ControlFlowFlattening.cpp
    src/passes/BogusControlFlow.cpp
    src/passes/StringObfuscation.cpp
    src/passes/AntiAnalysisPass.cpp
    src/passes/JunkCodeInsertion.cpp
)

set(ALL_SOURCES
    ${CORE_SOURCES}
    ${UTILS_SOURCES}
    ${AI_SOURCES}
    ${BLOCKCHAIN_SOURCES}
    ${PASSES_SOURCES}
)

# Create H5X core library
add_library(h5x_core ${ALL_SOURCES})

# Link libraries to core
target_link_libraries(h5x_core
    ${LLVM_FULL_LIBS}
    ${LLVM_SYSTEM_LIBS}
    OpenSSL::SSL
    OpenSSL::Crypto
    CURL::libcurl
)

if(JSONCPP_FOUND)
    target_link_libraries(h5x_core ${JSONCPP_LDFLAGS})
    target_include_directories(h5x_core PRIVATE ${JSONCPP_INCLUDE_DIRS})
endif()

# Set library properties
set_target_properties(h5x_core PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    PUBLIC_HEADER "src/core/H5XObfuscationEngine.hpp"
)

# CLI executable
add_executable(h5x-cli tools/h5x-cli/main.cpp)
target_link_libraries(h5x-cli h5x_core)

# Link jsoncpp to CLI if available
if(JSONCPP_FOUND)
    target_link_libraries(h5x-cli ${JSONCPP_LDFLAGS})
    target_include_directories(h5x-cli PRIVATE ${JSONCPP_INCLUDE_DIRS})
endif()

# Install targets
install(TARGETS h5x_core h5x-cli
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    PUBLIC_HEADER DESTINATION include/h5x
)

# Testing
enable_testing()

# Add test subdirectory if it exists
if(EXISTS "${CMAKE_SOURCE_DIR}/tests")
    add_subdirectory(tests)
endif()

# Print configuration summary
message(STATUS "")
message(STATUS "H5X Configuration Summary:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  LLVM Version: ${LLVM_PACKAGE_VERSION}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
