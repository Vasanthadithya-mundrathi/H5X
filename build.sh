#!/bin/bash

# H5X Advanced Obfuscation Engine - Professional Build Script
# Version 1.0.0

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="H5X Advanced Obfuscation Engine"
VERSION="1.0.0"
BUILD_DIR="build"
INSTALL_PREFIX="/usr/local"
CMAKE_BUILD_TYPE="Release"
PARALLEL_JOBS=$(nproc 2>/dev/null || echo 4)

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "  $PROJECT_NAME - Build System v$VERSION"
    echo "=================================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_step "Checking build dependencies..."

    local missing_deps=()

    # Check for required tools
    command -v cmake >/dev/null 2>&1 || missing_deps+=("cmake")
    command -v make >/dev/null 2>&1 || missing_deps+=("make")
    command -v g++ >/dev/null 2>&1 || missing_deps+=("g++")
    command -v pkg-config >/dev/null 2>&1 || missing_deps+=("pkg-config")

    # Check for optional but recommended tools
    command -v ninja >/dev/null 2>&1 && USE_NINJA=1 || USE_NINJA=0
    command -v ccache >/dev/null 2>&1 && USE_CCACHE=1 || USE_CCACHE=0

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo "Please install them using your package manager:"
        echo "  Ubuntu/Debian: sudo apt install ${missing_deps[*]}"
        echo "  CentOS/RHEL:   sudo yum install ${missing_deps[*]}"
        echo "  Arch Linux:    sudo pacman -S ${missing_deps[*]}"
        exit 1
    fi

    print_success "All required dependencies found"

    if [ $USE_NINJA -eq 1 ]; then
        print_success "Ninja build system available - will use for faster builds"
        CMAKE_GENERATOR="-G Ninja"
    else
        CMAKE_GENERATOR=""
        print_warning "Ninja not found - using default Make (consider installing ninja for faster builds)"
    fi

    if [ $USE_CCACHE -eq 1 ]; then
        print_success "ccache available - will use for faster rebuilds"
        export CMAKE_C_COMPILER_LAUNCHER=ccache
        export CMAKE_CXX_COMPILER_LAUNCHER=ccache
    fi
}

detect_llvm() {
    print_step "Detecting LLVM installation..."

    # Try to find LLVM in common locations
    LLVM_VERSIONS=("18" "17" "16" "15" "14")
    LLVM_FOUND=0

    for version in "${LLVM_VERSIONS[@]}"; do
        if command -v "llvm-config-$version" >/dev/null 2>&1; then
            LLVM_VERSION=$version
            LLVM_CONFIG="llvm-config-$version"
            LLVM_FOUND=1
            break
        elif command -v "llvm-config" >/dev/null 2>&1; then
            LLVM_VERSION=$(llvm-config --version | cut -d. -f1)
            LLVM_CONFIG="llvm-config"
            LLVM_FOUND=1
            break
        fi
    done

    if [ $LLVM_FOUND -eq 1 ]; then
        LLVM_PREFIX=$($LLVM_CONFIG --prefix)
        print_success "Found LLVM $LLVM_VERSION at $LLVM_PREFIX"
        CMAKE_ARGS="$CMAKE_ARGS -DLLVM_DIR=$LLVM_PREFIX/lib/cmake/llvm"
    else
        print_warning "LLVM not found - will build with mock implementation"
        print_warning "For full functionality, install LLVM development packages:"
        echo "  Ubuntu/Debian: sudo apt install llvm-17-dev clang-17"
        echo "  CentOS/RHEL:   sudo yum install llvm-devel clang-devel"
    fi
}

setup_build_directory() {
    print_step "Setting up build directory..."

    if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
        if [ -d "$BUILD_DIR" ]; then
            print_step "Cleaning existing build directory..."
            rm -rf "$BUILD_DIR"
        fi
    fi

    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    print_success "Build directory ready: $(pwd)"
}

configure_cmake() {
    print_step "Configuring CMake..."

    CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE"
    CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX"

    if [ "$CMAKE_BUILD_TYPE" = "Debug" ]; then
        CMAKE_ARGS="$CMAKE_ARGS -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
        print_step "Debug build - enabling compile commands export"
    fi

    echo "CMake command: cmake $CMAKE_GENERATOR $CMAKE_ARGS .."

    if cmake $CMAKE_GENERATOR $CMAKE_ARGS ..; then
        print_success "CMake configuration completed"
    else
        print_error "CMake configuration failed"
        exit 1
    fi
}

build_project() {
    print_step "Building project with $PARALLEL_JOBS parallel jobs..."

    if [ $USE_NINJA -eq 1 ]; then
        BUILD_COMMAND="ninja -j$PARALLEL_JOBS"
    else
        BUILD_COMMAND="make -j$PARALLEL_JOBS"
    fi

    echo "Build command: $BUILD_COMMAND"

    if $BUILD_COMMAND; then
        print_success "Build completed successfully"
    else
        print_error "Build failed"
        exit 1
    fi
}

run_tests() {
    if [ "$1" = "--skip-tests" ]; then
        print_warning "Skipping tests as requested"
        return
    fi

    print_step "Running tests..."

    if command -v ctest >/dev/null 2>&1; then
        if ctest --output-on-failure; then
            print_success "All tests passed"
        else
            print_warning "Some tests failed - check output above"
        fi
    else
        print_warning "CTest not available - skipping tests"
    fi
}

install_project() {
    if [ "$1" = "--no-install" ]; then
        print_warning "Skipping installation as requested"
        return
    fi

    print_step "Installing project..."

    if [ "$EUID" -ne 0 ] && [ "$INSTALL_PREFIX" = "/usr/local" ]; then
        print_warning "Installing to system directory requires sudo"
        INSTALL_COMMAND="sudo make install"
    else
        INSTALL_COMMAND="make install"
    fi

    if $INSTALL_COMMAND; then
        print_success "Installation completed"
        echo "H5X installed to: $INSTALL_PREFIX"
        echo "CLI tool: $INSTALL_PREFIX/bin/h5x-cli"
        echo "Libraries: $INSTALL_PREFIX/lib/"
        echo "Headers: $INSTALL_PREFIX/include/h5x/"
    else
        print_error "Installation failed"
        exit 1
    fi
}

create_package() {
    if [ "$1" = "--package" ]; then
        print_step "Creating distribution package..."

        if command -v cpack >/dev/null 2>&1; then
            if cpack; then
                print_success "Package created successfully"
                ls -la *.deb *.rpm *.tar.gz 2>/dev/null || true
            else
                print_warning "Package creation failed"
            fi
        else
            print_warning "CPack not available - skipping package creation"
        fi
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Build Options:"
    echo "  --clean, -c        Clean build directory before building"
    echo "  --debug           Build in debug mode"
    echo "  --release         Build in release mode (default)"
    echo "  --jobs N          Use N parallel jobs (default: $PARALLEL_JOBS)"
    echo ""
    echo "Installation Options:"
    echo "  --prefix PATH     Installation prefix (default: $INSTALL_PREFIX)"
    echo "  --no-install      Skip installation step"
    echo ""
    echo "Other Options:"
    echo "  --skip-tests      Skip running tests"
    echo "  --package         Create distribution package"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Standard release build"
    echo "  $0 --clean --debug           # Clean debug build"
    echo "  $0 --prefix=/opt/h5x         # Install to /opt/h5x"
    echo "  $0 --package                 # Build and create package"
}

# Main execution
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean|-c)
                CLEAN_BUILD="--clean"
                shift
                ;;
            --debug)
                CMAKE_BUILD_TYPE="Debug"
                shift
                ;;
            --release)
                CMAKE_BUILD_TYPE="Release"
                shift
                ;;
            --jobs)
                PARALLEL_JOBS="$2"
                shift 2
                ;;
            --prefix)
                INSTALL_PREFIX="$2"
                shift 2
                ;;
            --no-install)
                NO_INSTALL="--no-install"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS="--skip-tests"
                shift
                ;;
            --package)
                CREATE_PACKAGE="--package"
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Start build process
    print_header

    echo "Build Configuration:"
    echo "  Build Type: $CMAKE_BUILD_TYPE"
    echo "  Parallel Jobs: $PARALLEL_JOBS"
    echo "  Install Prefix: $INSTALL_PREFIX"
    echo ""

    check_dependencies
    detect_llvm
    setup_build_directory $CLEAN_BUILD
    configure_cmake
    build_project
    run_tests $SKIP_TESTS
    install_project $NO_INSTALL
    create_package $CREATE_PACKAGE

    echo ""
    print_success "Build process completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Test the CLI: h5x-cli --version"
    echo "  2. Start the dashboard: cd tools/h5x-dashboard && python3 app.py"
    echo "  3. Read the documentation: docs/USER_MANUAL.md"
    echo ""
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
