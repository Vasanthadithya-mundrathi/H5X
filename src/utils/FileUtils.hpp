#ifndef H5X_FILE_UTILS_HPP
#define H5X_FILE_UTILS_HPP

#include <string>
#include <vector>

namespace h5x {

class FileUtils {
public:
    static bool file_exists(const std::string& path);
    static bool create_directory(const std::string& path);
    static std::string get_file_extension(const std::string& path);
    static std::string get_filename_without_extension(const std::string& path);
    static std::string get_directory_path(const std::string& path);
    static std::vector<uint8_t> read_binary_file(const std::string& path);
    static bool write_binary_file(const std::string& path, const std::vector<uint8_t>& data);
    static size_t get_file_size(const std::string& path);
};

} // namespace h5x

#endif // H5X_FILE_UTILS_HPP