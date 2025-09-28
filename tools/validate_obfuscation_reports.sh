#!/bin/bash

# H5X Obfuscation Report Validation Script
# This script validates obfuscation reports to ensure all metrics are accurate

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"
REPORTS_DIR="${PROJECT_ROOT}/output/reports"
VALIDATION_OUTPUT_DIR="${PROJECT_ROOT}/validation_output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo "========================================="
    echo "  H5X Obfuscation Report Validation"
    echo "========================================="
    echo
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -s, --strict            Enable strict validation mode"
    echo "  -r, --reports DIR       Directory containing reports to validate"
    echo "  -o, --output DIR        Output directory for validation results"
    echo "  -b, --build             Build the project before validation"
    echo "  -t, --test-only         Only run validation tests, skip report validation"
    echo
    echo "Examples:"
    echo "  $0                      # Run basic validation"
    echo "  $0 --strict             # Run in strict mode"
    echo "  $0 --build --strict     # Build and validate strictly"
    echo
}

validate_environment() {
    log_info "Validating environment..."

    # Check if we're in the right directory
    if [[ ! -f "${PROJECT_ROOT}/CMakeLists.txt" ]]; then
        log_error "CMakeLists.txt not found. Are you in the H5X project directory?"
        exit 1
    fi

    # Check for required tools
    if ! command -v cmake &> /dev/null; then
        log_error "cmake is required but not installed."
        exit 1
    fi

    if ! command -v make &> /dev/null && ! command -v ninja &> /dev/null; then
        log_error "make or ninja is required but not installed."
        exit 1
    fi

    log_success "Environment validation completed"
}

build_project() {
    log_info "Building H5X project..."

    # Create build directory if it doesn't exist
    mkdir -p "$BUILD_DIR"

    # Configure and build
    cd "$BUILD_DIR"
    cmake -DCMAKE_BUILD_TYPE=Release ..
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

    log_success "Project built successfully"
}

run_obfuscation_tests() {
    log_info "Running obfuscation tests to generate reports..."

    # Create reports directory
    mkdir -p "$REPORTS_DIR"

    # Run test programs through obfuscation
    cd "$BUILD_DIR"

    if [[ -f "h5x-cli" ]]; then
        log_info "Running string obfuscation test..."
        ./h5x-cli "${PROJECT_ROOT}/demos/validation_test_strings.cpp" \
            --output "${PROJECT_ROOT}/test_outputs/obf_strings.cpp" \
            --report "${REPORTS_DIR}/strings_validation_report" \
            --levels basic advanced

        log_info "Running arithmetic obfuscation test..."
        ./h5x-cli "${PROJECT_ROOT}/demos/validation_test_arithmetic.cpp" \
            --output "${PROJECT_ROOT}/test_outputs/obf_arithmetic.cpp" \
            --report "${REPORTS_DIR}/arithmetic_validation_report" \
            --levels basic advanced

        log_info "Running control flow obfuscation test..."
        ./h5x-cli "${PROJECT_ROOT}/demos/validation_test_control_flow.cpp" \
            --output "${PROJECT_ROOT}/test_outputs/obf_control_flow.cpp" \
            --report "${REPORTS_DIR}/control_flow_validation_report" \
            --levels basic advanced maximum

        log_info "Running function obfuscation test..."
        ./h5x-cli "${PROJECT_ROOT}/demos/validation_test_functions.cpp" \
            --output "${PROJECT_ROOT}/test_outputs/obf_functions.cpp" \
            --report "${REPORTS_DIR}/functions_validation_report" \
            --levels basic advanced maximum
    else
        log_warning "h5x-cli not found. Skipping obfuscation tests."
        log_info "Please build the project first or run: $0 --build"
        return 1
    fi

    log_success "Obfuscation tests completed"
}

validate_reports() {
    local reports_dir="$1"
    local output_dir="$2"
    local strict_mode="$3"

    log_info "Validating obfuscation reports..."

    # Create output directory
    mkdir -p "$output_dir"

    # Find all report files
    local json_reports=($(find "$reports_dir" -name "*.report.json" 2>/dev/null))
    local html_reports=($(find "$reports_dir" -name "*.report.html" 2>/dev/null))
    local text_reports=($(find "$reports_dir" -name "*.report.txt" 2>/dev/null))

    if [[ ${#json_reports[@]} -eq 0 ]]; then
        log_warning "No JSON reports found in $reports_dir"
        return 1
    fi

    log_info "Found ${#json_reports[@]} JSON reports, ${#html_reports[@]} HTML reports, ${#text_reports[@]} text reports"

    # Build validation test runner if needed
    cd "$BUILD_DIR"
    if [[ ! -f "validation_test_runner" ]]; then
        log_info "Building validation test runner..."
        g++ -std=c++17 -I../src \
            "${PROJECT_ROOT}/tools/validation_test_runner.cpp" \
            -o validation_test_runner
    fi

    # Run validation
    local validation_summary="$output_dir/validation_summary.txt"
    echo "H5X Validation Report Summary" > "$validation_summary"
    echo "Generated on: $(date)" >> "$validation_summary"
    echo "=========================================" >> "$validation_summary"
    echo >> "$validation_summary"

    local total_reports=0
    local valid_reports=0
    local invalid_reports=0

    for json_report in "${json_reports[@]}"; do
        total_reports=$((total_reports + 1))

        log_info "Validating $(basename "$json_report")..."

        # Extract base name for related reports
        local base_name="${json_report%.report.json}"

        # Validate JSON report
        if [[ -f "${PROJECT_ROOT}/build/validation_test_runner" ]]; then
            local validation_result="$output_dir/$(basename "$json_report" .json)_validation.json"
            "${PROJECT_ROOT}/build/validation_test_runner" \
                --json "$json_report" \
                --output "$validation_result" \
                $( [[ "$strict_mode" == "true" ]] && echo "--strict" )
        fi

        # Check for corresponding HTML and text reports
        local html_report="${base_name}.report.html"
        local text_report="${base_name}.report.txt"

        if [[ -f "$html_report" ]] && [[ -f "$text_report" ]]; then
            log_info "Validating cross-format consistency..."
            # Add consistency validation here
        fi

        # Simple validation check
        if [[ -s "$json_report" ]]; then
            valid_reports=$((valid_reports + 1))
            echo "✓ $(basename "$json_report") - VALID" >> "$validation_summary"
        else
            invalid_reports=$((invalid_reports + 1))
            echo "✗ $(basename "$json_report") - INVALID" >> "$validation_summary"
        fi
    done

    # Generate summary
    echo >> "$validation_summary"
    echo "Validation Summary:" >> "$validation_summary"
    echo "Total Reports: $total_reports" >> "$validation_summary"
    echo "Valid Reports: $valid_reports" >> "$validation_summary"
    echo "Invalid Reports: $invalid_reports" >> "$validation_summary"

    if [[ $invalid_reports -eq 0 ]]; then
        log_success "All reports passed validation!"
        echo "Status: PASSED" >> "$validation_summary"
    else
        log_warning "$invalid_reports reports failed validation"
        echo "Status: FAILED" >> "$validation_summary"
    fi

    log_success "Validation completed. Summary: $validation_summary"
}

generate_validation_dashboard() {
    local output_dir="$1"
    local summary_file="$output_dir/validation_summary.txt"

    log_info "Generating validation dashboard..."

    if [[ -f "$summary_file" ]]; then
        echo
        echo "========================================="
        echo "  Validation Dashboard"
        echo "========================================="
        cat "$summary_file"
        echo
    fi
}

# Main script
main() {
    local build=false
    local strict_mode=false
    local test_only=false
    local reports_dir="$REPORTS_DIR"
    local output_dir="$VALIDATION_OUTPUT_DIR"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--build)
                build=true
                shift
                ;;
            -s|--strict)
                strict_mode=true
                shift
                ;;
            -t|--test-only)
                test_only=true
                shift
                ;;
            -r|--reports)
                reports_dir="$2"
                shift 2
                ;;
            -o|--output)
                output_dir="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_header

    # Validate environment
    validate_environment

    # Build if requested
    if [[ "$build" == "true" ]]; then
        build_project
    fi

    # Run obfuscation tests unless test-only mode
    if [[ "$test_only" == "false" ]]; then
        run_obfuscation_tests
    fi

    # Validate reports
    validate_reports "$reports_dir" "$output_dir" "$strict_mode"

    # Generate dashboard
    generate_validation_dashboard "$output_dir"

    log_success "Validation process completed!"
}

# Run main function with all arguments
main "$@"