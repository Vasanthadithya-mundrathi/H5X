#ifndef H5X_LOGGER_HPP
#define H5X_LOGGER_HPP

#include <string>
#include <fstream>
#include <mutex>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <iostream>

namespace h5x {

enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    CRITICAL = 4
};

class Logger {
public:
    static Logger& getInstance() {
        static Logger instance;
        return instance;
    }

    void initialize(const std::string& log_file, LogLevel level = LogLevel::INFO);
    void log(LogLevel level, const std::string& message);
    void debug(const std::string& message) { log(LogLevel::DEBUG, message); }
    void info(const std::string& message) { log(LogLevel::INFO, message); }
    void warning(const std::string& message) { log(LogLevel::WARNING, message); }
    void error(const std::string& message) { log(LogLevel::ERROR, message); }
    void critical(const std::string& message) { log(LogLevel::CRITICAL, message); }

    void setLevel(LogLevel level) { current_level_ = level; }
    void setConsoleOutput(bool enable) { console_output_ = enable; }

public:
    Logger() = default;
    ~Logger() { if (log_file_.is_open()) log_file_.close(); }

private:

    std::string getCurrentTimestamp();
    std::string levelToString(LogLevel level);

    std::ofstream log_file_;
    std::mutex log_mutex_;
    LogLevel current_level_ = LogLevel::INFO;
    bool console_output_ = true;
    bool initialized_ = false;
};

} // namespace h5x

#endif // H5X_LOGGER_HPP
