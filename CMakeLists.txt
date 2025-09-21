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

# Find required packages
find_package(PkgConfig REQUIRED)

# Find LLVM (attempt multiple versions)
find_package(LLVM REQUIRED CONFIG)
if(LLVM_FOUND)
    message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
    message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

    # Add LLVM definitions and include directories
    add_definitions(${LLVM_DEFINITIONS})
    include_directories(${LLVM_INCLUDE_DIRS})

    # Find LLVM libraries
    llvm_map_components_to_libnames(LLVM_LIBS
        support core irreader bitwriter target
        x86codegen x86asmparser x86info
        aarch64codegen aarch64asmparser aarch64info
        passes transformutils analysis
    )
else()
    message(WARNING "LLVM not found, using mock implementation")
    set(LLVM_LIBS "")
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
    ${LLVM_LIBS}
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

# Dashboard backend (Python Flask app - no compilation needed)
# Copy Python files to build directory
configure_file(
    ${CMAKE_SOURCE_DIR}/tools/h5x-dashboard/app.py
    ${CMAKE_BINARY_DIR}/bin/h5x-dashboard.py
    COPYONLY
)

# Install targets
install(TARGETS h5x_core h5x-cli
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    PUBLIC_HEADER DESTINATION include/h5x
)

# Install headers
install(DIRECTORY src/
    DESTINATION include/h5x
    FILES_MATCHING PATTERN "*.hpp"
)

# Install configuration files
install(DIRECTORY config/
    DESTINATION etc/h5x
    FILES_MATCHING PATTERN "*.json"
)

# Install documentation
install(DIRECTORY docs/
    DESTINATION share/doc/h5x
    FILES_MATCHING PATTERN "*.md" PATTERN "*.txt"
)

# Create package configuration
include(CMakePackageConfigHelpers)

configure_package_config_file(
    "${CMAKE_SOURCE_DIR}/cmake/H5XConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/H5XConfig.cmake"
    INSTALL_DESTINATION lib/cmake/H5X
)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/H5XConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/H5XConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/H5XConfigVersion.cmake"
    DESTINATION lib/cmake/H5X
)

# Testing
enable_testing()

# Add test subdirectory if it exists
if(EXISTS "${CMAKE_SOURCE_DIR}/tests")
    add_subdirectory(tests)
endif()

# CPack configuration for packaging
set(CPACK_PACKAGE_NAME "H5X")
set(CPACK_PACKAGE_VENDOR "H5X Project")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "H5X Advanced Multi-Layer Code Obfuscation Engine")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})

set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_SOURCE_DIR}/README.md")

# Platform-specific packaging
if(UNIX AND NOT APPLE)
    set(CPACK_GENERATOR "DEB;RPM;TGZ")
    set(CPACK_DEBIAN_PACKAGE_MAINTAINER "H5X Project Team")
    set(CPACK_DEBIAN_PACKAGE_DEPENDS "libssl-dev, llvm-17, clang-17")
    set(CPACK_RPM_PACKAGE_REQUIRES "openssl-devel, llvm17, clang17")
elseif(WIN32)
    set(CPACK_GENERATOR "NSIS;ZIP")
elseif(APPLE)
    set(CPACK_GENERATOR "DragNDrop;TGZ")
endif()

include(CPack)

# Testing already enabled above

# Print configuration summary
message(STATUS "")
message(STATUS "H5X Configuration Summary:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  LLVM Version: ${LLVM_PACKAGE_VERSION}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
