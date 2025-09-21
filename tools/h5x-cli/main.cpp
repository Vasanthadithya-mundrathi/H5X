#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <chrono>
#include <iomanip>

#include "../src/core/H5XObfuscationEngine.hpp"
#include "../src/utils/Logger.hpp"

using namespace h5x;

// Version information
const std::string CLI_VERSION = "1.0.0";
const std::string CLI_BUILD_DATE = __DATE__;

void print_banner() {
    std::cout << "\n";
    std::cout << "██╗  ██╗███████╗██╗  ██╗    ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗\n";
    std::cout << "██║  ██║██╔════╝╚██╗██╔╝    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝\n";
    std::cout << "███████║███████╗ ╚███╔╝     █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗  \n";
    std::cout << "██╔══██║╚════██║ ██╔██╗     ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝  \n";
    std::cout << "██║  ██║███████║██╔╝ ██╗    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗\n";
    std::cout << "╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝\n";
    std::cout << "\n";
    std::cout << "🔐 H5X ENGINE - Advanced Multi-Layer Code Obfuscation System\n";
    std::cout << "Version " << CLI_VERSION << " (built " << CLI_BUILD_DATE << ")\n";
    std::cout << "Professional LLVM-based obfuscation with AI optimization and blockchain verification\n";
    std::cout << "\n";
}

void print_usage() {
    std::cout << "USAGE:\n";
    std::cout << "  h5x-cli [COMMAND] [OPTIONS]\n";
    std::cout << "\n";
    std::cout << "COMMANDS:\n";
    std::cout << "  obfuscate <input> -o <output>    Obfuscate a source file\n";
    std::cout << "  batch <input_dir> -o <output_dir> Batch obfuscate files\n";
    std::cout << "  analyze <binary>                 Analyze obfuscated binary\n";
    std::cout << "  verify <binary>                  Verify blockchain integrity\n";
    std::cout << "  config [show|set] [options]      Manage configuration\n";
    std::cout << "  version                          Show version information\n";
    std::cout << "  help                             Show this help message\n";
    std::cout << "\n";
    std::cout << "OBFUSCATION OPTIONS:\n";
    std::cout << "  --level <1-5>                    Obfuscation level (default: 3)\n";
    std::cout << "  --profile <name>                 Use predefined profile\n";
    std::cout << "  --config <file>                  Custom configuration file\n";
    std::cout << "  --ai-optimize                    Enable AI optimization\n";
    std::cout << "  --blockchain-verify              Enable blockchain verification\n";
    std::cout << "  --target <platform>              Target platform (linux/windows)\n";
    std::cout << "  --report                         Generate detailed report\n";
    std::cout << "  --verbose                        Verbose output\n";
    std::cout << "  --quiet                          Minimal output\n";
    std::cout << "\n";
    std::cout << "EXAMPLES:\n";
    std::cout << "  h5x-cli obfuscate main.cpp -o protected_main --level 4\n";
    std::cout << "  h5x-cli obfuscate app.cpp -o secure_app --ai-optimize --report\n";
    std::cout << "  h5x-cli batch src/ -o obfuscated/ --level 3 --target linux\n";
    std::cout << "  h5x-cli analyze protected_binary\n";
    std::cout << "  h5x-cli config show\n";
    std::cout << "\n";
}

void print_version() {
    std::cout << "H5X CLI Tool\n";
    std::cout << "Version: " << CLI_VERSION << "\n";
    std::cout << "Build Date: " << CLI_BUILD_DATE << "\n";
    std::cout << "Engine Version: " << H5XObfuscationEngine::get_version() << "\n";
    std::cout << "\n";
    std::cout << "Features:\n";
    std::cout << "  ✓ LLVM-based obfuscation\n";
    std::cout << "  ✓ AI genetic algorithm optimization\n";
    std::cout << "  ✓ Blockchain integrity verification\n";
    std::cout << "  ✓ Cross-platform compilation\n";
    std::cout << "  ✓ Professional reporting\n";
    std::cout << "\n";
}

void print_config() {
    std::cout << "CURRENT CONFIGURATION:\n";
    std::cout << "  Config File: config/config.json\n";
    std::cout << "  Log Level: INFO\n";
    std::cout << "  Default Level: 3\n";
    std::cout << "  AI Optimization: Enabled\n";
    std::cout << "  Blockchain: Polygon Network\n";
    std::cout << "  Output Directory: ./output\n";
    std::cout << "\n";
}

struct CLIArgs {
    std::string command;
    std::string input_file;
    std::string output_file;
    std::string config_file;
    std::string profile;
    std::vector<std::string> targets;
    int level = 3;
    bool ai_optimize = false;
    bool blockchain_verify = false;
    bool generate_report = false;
    bool verbose = false;
    bool quiet = false;
};

CLIArgs parse_arguments(int argc, char* argv[]) {
    CLIArgs args;

    if (argc < 2) {
        return args;
    }

    args.command = argv[1];

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "-o" && i + 1 < argc) {
            args.output_file = argv[++i];
        } else if (arg == "--level" && i + 1 < argc) {
            args.level = std::stoi(argv[++i]);
        } else if (arg == "--config" && i + 1 < argc) {
            args.config_file = argv[++i];
        } else if (arg == "--profile" && i + 1 < argc) {
            args.profile = argv[++i];
        } else if (arg == "--target" && i + 1 < argc) {
            args.targets.push_back(argv[++i]);
        } else if (arg == "--ai-optimize") {
            args.ai_optimize = true;
        } else if (arg == "--blockchain-verify") {
            args.blockchain_verify = true;
        } else if (arg == "--report") {
            args.generate_report = true;
        } else if (arg == "--verbose") {
            args.verbose = true;
        } else if (arg == "--quiet") {
            args.quiet = true;
        } else if (args.input_file.empty()) {
            args.input_file = arg;
        }
    }

    return args;
}

void print_progress_bar(const std::string& task, double progress) {
    const int bar_width = 40;
    int filled_width = static_cast<int>(progress * bar_width);

    std::cout << "\r" << task << " [";
    for (int i = 0; i < bar_width; ++i) {
        if (i < filled_width) {
            std::cout << "█";
        } else {
            std::cout << "░";
        }
    }
    std::cout << "] " << std::fixed << std::setprecision(1) << (progress * 100.0) << "%";
    std::cout.flush();

    if (progress >= 1.0) {
        std::cout << "\n";
    }
}

int cmd_obfuscate(const CLIArgs& args) {
    if (args.input_file.empty() || args.output_file.empty()) {
        std::cerr << "Error: Input and output files required for obfuscation\n";
        std::cerr << "Usage: h5x-cli obfuscate <input> -o <output>\n";
        return 1;
    }

    if (!std::filesystem::exists(args.input_file)) {
        std::cerr << "Error: Input file does not exist: " << args.input_file << "\n";
        return 1;
    }

    try {
        // Create H5X engine
        H5XObfuscationEngine engine;

        if (!args.quiet) {
            std::cout << "🚀 Initializing H5X Obfuscation Engine...\n";
            print_progress_bar("Initialization", 0.1);
        }

        // Initialize with config
        if (!engine.initialize(args.config_file)) {
            std::cerr << "Error: Failed to initialize H5X engine\n";
            return 1;
        }

        if (!args.quiet) {
            print_progress_bar("Initialization", 1.0);
            std::cout << "✅ Engine initialized successfully\n\n";
        }

        // Configure obfuscation settings
        ObfuscationConfig config;
        config.obfuscation_level = args.level;
        config.enable_ai_optimization = args.ai_optimize;
        config.enable_blockchain_verification = args.blockchain_verify;
        config.generate_detailed_report = args.generate_report;
        config.target_platforms = args.targets.empty() ? std::vector<std::string>{"linux"} : args.targets;

        engine.configure(config);

        if (!args.quiet) {
            std::cout << "⚙️  Configuration:";
            std::cout << " Level=" << args.level;
            if (args.ai_optimize) std::cout << " +AI";
            if (args.blockchain_verify) std::cout << " +Blockchain";
            std::cout << "\n";
            std::cout << "🎯 Target platforms: ";
            for (const auto& target : config.target_platforms) {
                std::cout << target << " ";
            }
            std::cout << "\n\n";
        }

        if (!args.quiet) {
            std::cout << "🛡️  Starting obfuscation process...\n";
            print_progress_bar("Processing", 0.2);
        }

        // Start obfuscation
        auto start_time = std::chrono::high_resolution_clock::now();

        auto result = engine.obfuscate_file(args.input_file, args.output_file);

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

        if (!args.quiet) {
            print_progress_bar("Processing", 1.0);
        }

        if (!result.success) {
            std::cerr << "❌ Obfuscation failed: " << result.error_message << "\n";
            return 1;
        }

        // Print results
        std::cout << "\n🎉 Obfuscation completed successfully!\n";
        std::cout << "\n📊 OBFUSCATION RESULTS:\n";
        std::cout << "  Input File:         " << result.input_file_path << "\n";
        std::cout << "  Output File:        " << result.output_file_path << "\n";
        std::cout << "  Original Size:      " << result.original_file_size << " bytes\n";
        std::cout << "  Obfuscated Size:    " << result.obfuscated_file_size << " bytes\n";

        double size_increase = ((double)result.obfuscated_file_size / result.original_file_size - 1.0) * 100;
        std::cout << "  Size Increase:      " << std::fixed << std::setprecision(1) << size_increase << "%\n";
        std::cout << "  Complexity Factor:  " << std::setprecision(2) << result.complexity_increase_factor << "x\n";
        std::cout << "  Security Score:     " << std::setprecision(1) << result.security_score << "/100\n";
        std::cout << "  Processing Time:    " << duration.count() << "ms\n";

        std::cout << "\n🛡️  APPLIED TECHNIQUES:\n";
        for (const auto& technique : result.applied_techniques) {
            std::cout << "  ✓ " << technique << "\n";
        }

        std::cout << "\n📈 PROTECTION METRICS:\n";
        std::cout << "  Functions Processed: " << result.functions_obfuscated << "\n";
        std::cout << "  Strings Obfuscated:  " << result.strings_obfuscated << "\n";
        std::cout << "  Bogus Blocks Added:  " << result.bogus_blocks_added << "\n";

        if (result.ai_optimization_used) {
            std::cout << "\n🧠 AI OPTIMIZATION:\n";
            std::cout << "  Genetic Algorithm:   ENABLED\n";
            std::cout << "  Fitness Score:       " << std::setprecision(2) << result.fitness_score << "\n";
            std::cout << "  Optimal Sequence:    ";
            for (size_t i = 0; i < result.optimal_pass_sequence.size() && i < 5; ++i) {
                std::cout << result.optimal_pass_sequence[i] << " ";
            }
            std::cout << "\n";
        }

        if (result.blockchain_verified) {
            std::cout << "\n⛓️  BLOCKCHAIN VERIFICATION:\n";
            std::cout << "  Status:             VERIFIED\n";
            std::cout << "  Integrity Hash:     " << result.integrity_hash.substr(0, 16) << "...\n";
            std::cout << "  Transaction ID:     " << result.blockchain_transaction_id.substr(0, 16) << "...\n";
        }

        if (args.generate_report) {
            std::string report_path = args.output_file + "_report";
            if (engine.generate_report(result, report_path)) {
                std::cout << "\n📋 DETAILED REPORT:\n";
                std::cout << "  Report generated:   " << report_path << ".json\n";
                std::cout << "  HTML version:       " << report_path << ".html\n";
                std::cout << "  Summary:            " << report_path << "_summary.txt\n";
            }
        }

        std::cout << "\n🎯 Ready for deployment! Your code is now protected.\n\n";

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "❌ Critical error: " << e.what() << "\n";
        return 1;
    }
}

int cmd_analyze(const CLIArgs& args) {
    if (args.input_file.empty()) {
        std::cerr << "Error: Binary file required for analysis\n";
        std::cerr << "Usage: h5x-cli analyze <binary>\n";
        return 1;
    }

    if (!std::filesystem::exists(args.input_file)) {
        std::cerr << "Error: Binary file does not exist: " << args.input_file << "\n";
        return 1;
    }

    try {
        H5XObfuscationEngine engine;

        if (!args.quiet) {
            std::cout << "🔍 Analyzing binary: " << args.input_file << "\n";
            print_progress_bar("Analysis", 0.3);
        }

        if (!engine.initialize()) {
            std::cerr << "Error: Failed to initialize H5X engine\n";
            return 1;
        }

        auto analysis_result = engine.analyze_obfuscation_effectiveness(args.input_file);

        if (!args.quiet) {
            print_progress_bar("Analysis", 1.0);
        }

        std::cout << "\n📊 SECURITY ANALYSIS RESULTS:\n";
        std::cout << analysis_result << "\n";

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "❌ Analysis error: " << e.what() << "\n";
        return 1;
    }
}

int cmd_verify(const CLIArgs& args) {
    if (args.input_file.empty()) {
        std::cerr << "Error: Binary file required for verification\n";
        std::cerr << "Usage: h5x-cli verify <binary>\n";
        return 1;
    }

    try {
        H5XObfuscationEngine engine;

        if (!args.quiet) {
            std::cout << "⛓️  Verifying blockchain integrity...\n";
        }

        if (!engine.initialize()) {
            std::cerr << "Error: Failed to initialize H5X engine\n";
            return 1;
        }

        auto verification_result = engine.verify_blockchain_integrity(args.input_file);

        std::cout << "\n🔐 BLOCKCHAIN VERIFICATION:\n";
        std::cout << verification_result << "\n";

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "❌ Verification error: " << e.what() << "\n";
        return 1;
    }
}

int cmd_batch(const CLIArgs& args) {
    if (args.input_file.empty() || args.output_file.empty()) {
        std::cerr << "Error: Input and output directories required\n";
        std::cerr << "Usage: h5x-cli batch <input_dir> -o <output_dir>\n";
        return 1;
    }

    try {
        // Find input files
        std::vector<std::string> input_files;

        for (const auto& entry : std::filesystem::recursive_directory_iterator(args.input_file)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                if (ext == ".c" || ext == ".cpp" || ext == ".cxx" || ext == ".cc") {
                    input_files.push_back(entry.path().string());
                }
            }
        }

        if (input_files.empty()) {
            std::cerr << "Error: No C/C++ source files found in " << args.input_file << "\n";
            return 1;
        }

        std::cout << "📁 Found " << input_files.size() << " source files to process\n";

        H5XObfuscationEngine engine;
        if (!engine.initialize()) {
            std::cerr << "Error: Failed to initialize H5X engine\n";
            return 1;
        }

        // Configure settings
        ObfuscationConfig config;
        config.obfuscation_level = args.level;
        config.enable_ai_optimization = args.ai_optimize;
        config.enable_blockchain_verification = args.blockchain_verify;
        config.target_platforms = args.targets.empty() ? std::vector<std::string>{"linux"} : args.targets;
        engine.configure(config);

        std::cout << "🚀 Starting batch obfuscation...\n";

        auto results = engine.obfuscate_batch(input_files, args.output_file);

        // Print summary
        int successful = 0;
        int failed = 0;

        for (const auto& result : results) {
            if (result.success) {
                successful++;
                if (args.verbose) {
                    std::cout << "✅ " << result.input_file_path << " -> " << result.output_file_path << "\n";
                }
            } else {
                failed++;
                std::cerr << "❌ " << result.input_file_path << ": " << result.error_message << "\n";
            }
        }

        std::cout << "\n📊 BATCH PROCESSING SUMMARY:\n";
        std::cout << "  Total Files:    " << results.size() << "\n";
        std::cout << "  Successful:     " << successful << "\n";
        std::cout << "  Failed:         " << failed << "\n";
        std::cout << "  Success Rate:   " << std::fixed << std::setprecision(1) 
                  << (100.0 * successful / results.size()) << "%\n";

        return failed > 0 ? 1 : 0;

    } catch (const std::exception& e) {
        std::cerr << "❌ Batch processing error: " << e.what() << "\n";
        return 1;
    }
}

int main(int argc, char* argv[]) {
    // Parse command line arguments
    CLIArgs args = parse_arguments(argc, argv);

    // Handle no command or help
    if (args.command.empty() || args.command == "help" || args.command == "-h" || args.command == "--help") {
        print_banner();
        print_usage();
        return 0;
    }

    // Handle version
    if (args.command == "version" || args.command == "-v" || args.command == "--version") {
        print_version();
        return 0;
    }

    // Handle configuration
    if (args.command == "config") {
        if (args.input_file == "show" || args.input_file.empty()) {
            print_config();
            return 0;
        }
        // Add config set functionality here
        std::cout << "Configuration management not yet implemented\n";
        return 0;
    }

    // Print banner for other commands unless quiet
    if (!args.quiet) {
        print_banner();
    }

    // Route to appropriate command handler
    try {
        if (args.command == "obfuscate") {
            return cmd_obfuscate(args);
        } else if (args.command == "analyze") {
            return cmd_analyze(args);
        } else if (args.command == "verify") {
            return cmd_verify(args);
        } else if (args.command == "batch") {
            return cmd_batch(args);
        } else {
            std::cerr << "Error: Unknown command '" << args.command << "'\n";
            std::cerr << "Use 'h5x-cli help' for usage information\n";
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "❌ Fatal error: " << e.what() << "\n";
        return 1;
    }
}
