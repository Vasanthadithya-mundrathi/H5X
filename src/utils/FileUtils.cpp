#include "FileUtils.hpp"
#include <fstream>
#include <sys/stat.h>
#include <filesystem>

namespace h5x {

bool FileUtils::file_exists(const std::string& path) {
    struct stat buffer;
    return (stat(path.c_str(), &buffer) == 0);
}

bool FileUtils::create_directory(const std::string& path) {
    return std::filesystem::create_directories(path);
}

std::string FileUtils::get_file_extension(const std::string& path) {
    size_t pos = path.find_last_of('.');
    if (pos != std::string::npos) {
        return path.substr(pos);
    }
    return "";
}

std::string FileUtils::get_filename_without_extension(const std::string& path) {
    size_t pos1 = path.find_last_of('/');
    size_t pos2 = path.find_last_of('.');
    
    std::string filename = (pos1 != std::string::npos) ? path.substr(pos1 + 1) : path;
    
    if (pos2 != std::string::npos && pos2 > pos1) {
        return filename.substr(0, pos2 - (pos1 + 1));
    }
    return filename;
}

std::string FileUtils::get_directory_path(const std::string& path) {
    size_t pos = path.find_last_of('/');
    if (pos != std::string::npos) {
        return path.substr(0, pos);
    }
    return ".";
}

std::vector<uint8_t> FileUtils::read_binary_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        return {};
    }
    
    file.seekg(0, std::ios::end);
    size_t size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<uint8_t> data(size);
    file.read(reinterpret_cast<char*>(data.data()), size);
    
    return data;
}

bool FileUtils::write_binary_file(const std::string& path, const std::vector<uint8_t>& data) {
    std::ofstream file(path, std::ios::binary);
    if (!file) {
        return false;
    }
    
    file.write(reinterpret_cast<const char*>(data.data()), data.size());
    return file.good();
}

size_t FileUtils::get_file_size(const std::string& path) {
    struct stat stat_buf;
    return (stat(path.c_str(), &stat_buf) == 0) ? stat_buf.st_size : 0;
}

} // namespace h5x