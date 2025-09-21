#!/usr/bin/env python3
"""
H5X Advanced Obfuscation Engine - Professional Build Script
Python version for cross-platform compatibility
"""

import os
import sys
import subprocess
import shutil
import argparse
import multiprocessing
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.PURPLE = cls.CYAN = cls.NC = ''

def print_step(msg):
    print(f"{Colors.CYAN}[STEP]{Colors.NC} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def print_header():
    print(f"{Colors.BLUE}")
    print("==================================================================")
    print("  H5X Advanced Obfuscation Engine - Build System v1.0.0")
    print("==================================================================")
    print(f"{Colors.NC}")

def check_command(cmd):
    """Check if a command exists"""
    return shutil.which(cmd) is not None

def run_command(cmd, cwd=None, check=True):
    """Run a command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_dependencies():
    print_step("Checking build dependencies...")

    required = ['cmake', 'make', 'g++', 'pkg-config']
    missing = [cmd for cmd in required if not check_command(cmd)]

    if missing:
        print_error(f"Missing required dependencies: {', '.join(missing)}")
        print("Please install them using your package manager:")
        if sys.platform.startswith('linux'):
            print(f"  Ubuntu/Debian: sudo apt install {' '.join(missing)}")
            print(f"  CentOS/RHEL:   sudo yum install {' '.join(missing)}")
            print(f"  Arch Linux:    sudo pacman -S {' '.join(missing)}")
        elif sys.platform == 'darwin':
            print(f"  macOS: brew install {' '.join(missing)}")
        elif sys.platform.startswith('win'):
            print("  Windows: Install using vcpkg or MSYS2")
        return False

    print_success("All required dependencies found")

    # Check optional tools
    if check_command('ninja'):
        print_success("Ninja build system available - will use for faster builds")
        return True, 'ninja'
    else:
        print_warning("Ninja not found - using default Make")
        return True, 'make'

def detect_llvm():
    print_step("Detecting LLVM installation...")

    versions = ['18', '17', '16', '15', '14']

    for version in versions:
        if check_command(f'llvm-config-{version}'):
            success, output, _ = run_command(f'llvm-config-{version} --prefix')
            if success:
                print_success(f"Found LLVM {version} at {output.strip()}")
                return True, version, output.strip()

    # Try generic llvm-config
    if check_command('llvm-config'):
        success, output, _ = run_command('llvm-config --version')
        if success:
            version = output.strip().split('.')[0]
            success, prefix, _ = run_command('llvm-config --prefix')
            if success:
                print_success(f"Found LLVM {version} at {prefix.strip()}")
                return True, version, prefix.strip()

    print_warning("LLVM not found - will build with mock implementation")
    return False, None, None

def build_h5x(args):
    """Main build function"""

    print_header()

    print("Build Configuration:")
    print(f"  Build Type: {args.build_type}")
    print(f"  Parallel Jobs: {args.jobs}")
    print(f"  Install Prefix: {args.prefix}")
    print()

    # Check dependencies
    deps_ok, build_system = check_dependencies()
    if not deps_ok:
        return False

    # Detect LLVM
    llvm_found, llvm_version, llvm_prefix = detect_llvm()

    # Setup build directory
    print_step("Setting up build directory...")
    build_dir = Path("build")

    if args.clean and build_dir.exists():
        print_step("Cleaning existing build directory...")
        shutil.rmtree(build_dir)

    build_dir.mkdir(exist_ok=True)
    print_success(f"Build directory ready: {build_dir.absolute()}")

    # Configure CMake
    print_step("Configuring CMake...")

    cmake_args = [
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        f"-DCMAKE_INSTALL_PREFIX={args.prefix}"
    ]

    if build_system == 'ninja':
        cmake_args.append("-G Ninja")

    if llvm_found:
        cmake_args.append(f"-DLLVM_DIR={llvm_prefix}/lib/cmake/llvm")

    if args.build_type == 'Debug':
        cmake_args.append("-DCMAKE_EXPORT_COMPILE_COMMANDS=ON")

    cmake_cmd = f"cmake {' '.join(cmake_args)} .."
    print(f"CMake command: {cmake_cmd}")

    success, stdout, stderr = run_command(cmake_cmd, cwd=build_dir)
    if not success:
        print_error("CMake configuration failed")
        print(stderr)
        return False

    print_success("CMake configuration completed")

    # Build project
    print_step(f"Building project with {args.jobs} parallel jobs...")

    if build_system == 'ninja':
        build_cmd = f"ninja -j{args.jobs}"
    else:
        build_cmd = f"make -j{args.jobs}"

    print(f"Build command: {build_cmd}")

    success, stdout, stderr = run_command(build_cmd, cwd=build_dir)
    if not success:
        print_error("Build failed")
        print(stderr)
        return False

    print_success("Build completed successfully")

    # Run tests
    if not args.skip_tests:
        print_step("Running tests...")
        if check_command('ctest'):
            success, stdout, stderr = run_command("ctest --output-on-failure", cwd=build_dir)
            if success:
                print_success("All tests passed")
            else:
                print_warning("Some tests failed - check output above")
        else:
            print_warning("CTest not available - skipping tests")

    # Install
    if not args.no_install:
        print_step("Installing project...")

        if build_system == 'ninja':
            install_cmd = "ninja install"
        else:
            install_cmd = "make install"

        # Add sudo for system directories on Unix
        if (sys.platform != 'win32' and 
            args.prefix.startswith('/usr') and 
            os.geteuid() != 0):
            install_cmd = f"sudo {install_cmd}"
            print_warning("Installing to system directory requires sudo")

        success, stdout, stderr = run_command(install_cmd, cwd=build_dir)
        if success:
            print_success("Installation completed")
            print(f"H5X installed to: {args.prefix}")
            print(f"CLI tool: {args.prefix}/bin/h5x-cli")
            print(f"Libraries: {args.prefix}/lib/")
            print(f"Headers: {args.prefix}/include/h5x/")
        else:
            print_error("Installation failed")
            print(stderr)
            return False

    # Create package
    if args.package:
        print_step("Creating distribution package...")
        if check_command('cpack'):
            success, stdout, stderr = run_command("cpack", cwd=build_dir)
            if success:
                print_success("Package created successfully")
            else:
                print_warning("Package creation failed")
        else:
            print_warning("CPack not available - skipping package creation")

    print()
    print_success("Build process completed successfully!")
    print()
    print("Next steps:")
    print("  1. Test the CLI: h5x-cli --version")
    print("  2. Start the dashboard: cd tools/h5x-dashboard && python3 app.py")
    print("  3. Read the documentation: docs/USER_MANUAL.md")
    print()

    return True

def main():
    parser = argparse.ArgumentParser(description='H5X Build System')

    # Build options
    parser.add_argument('--clean', '-c', action='store_true',
                       help='Clean build directory before building')
    parser.add_argument('--debug', action='store_true',
                       help='Build in debug mode')
    parser.add_argument('--release', action='store_true',
                       help='Build in release mode (default)')
    parser.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count(),
                       help='Number of parallel jobs')

    # Installation options
    parser.add_argument('--prefix', default='/usr/local',
                       help='Installation prefix')
    parser.add_argument('--no-install', action='store_true',
                       help='Skip installation step')

    # Other options
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--package', action='store_true',
                       help='Create distribution package')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')

    args = parser.parse_args()

    # Handle color output
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Determine build type
    if args.debug:
        args.build_type = 'Debug'
    else:
        args.build_type = 'Release'

    # On Windows, adjust default prefix
    if sys.platform.startswith('win'):
        if args.prefix == '/usr/local':
            args.prefix = 'C:/Program Files/H5X'

    # Run build
    success = build_h5x(args)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
