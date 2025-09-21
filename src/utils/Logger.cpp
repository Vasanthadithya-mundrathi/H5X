#include "Logger.hpp"

namespace h5x {

void Logger::initialize(const std::string& log_file, LogLevel level) {
    std::lock_guard<std::mutex> lock(log_mutex_);

    if (initialized_) {
        return;
    }

    current_level_ = level;

    // Create logs directory if it doesn't exist
    std::filesystem::create_directories("logs");

    log_file_.open(log_file, std::ios::app);
    if (!log_file_.is_open()) {
        std::cerr << "Failed to open log file: " << log_file << std::endl;
        return;
    }

    initialized_ = true;

    // Log initialization message directly (avoid re-acquiring mutex)
    std::string timestamp = getCurrentTimestamp();
    std::ostringstream log_entry;
    log_entry << "[" << timestamp << "] [INFO ] H5X Logger initialized - " << log_file;
    
    if (log_file_.is_open()) {
        log_file_ << log_entry.str() << std::endl;
        log_file_.flush();
    }
    
    if (console_output_) {
        std::cout << log_entry.str() << std::endl;
    }
}

void Logger::log(LogLevel level, const std::string& message) {
    if (level < current_level_) {
        return;
    }

    std::lock_guard<std::mutex> lock(log_mutex_);

    std::string timestamp = getCurrentTimestamp();
    std::string level_str = levelToString(level);

    std::ostringstream log_entry;
    log_entry << "[" << timestamp << "] [" << level_str << "] " << message;

    // Write to file if initialized
    if (initialized_ && log_file_.is_open()) {
        log_file_ << log_entry.str() << std::endl;
        log_file_.flush();
    }

    // Write to console if enabled
    if (console_output_) {
        if (level >= LogLevel::ERROR) {
            std::cerr << log_entry.str() << std::endl;
        } else {
            std::cout << log_entry.str() << std::endl;
        }
    }
}

std::string Logger::getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;

    std::ostringstream oss;
    oss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count();

    return oss.str();
}

std::string Logger::levelToString(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG:    return "DEBUG";
        case LogLevel::INFO:     return "INFO ";
        case LogLevel::WARNING:  return "WARN ";
        case LogLevel::ERROR:    return "ERROR";
        case LogLevel::CRITICAL: return "CRIT ";
        default:                 return "UNKNOWN";
    }
}

} // namespace h5x
