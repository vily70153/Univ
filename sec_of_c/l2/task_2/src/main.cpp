#include <cstdlib>
#include <iostream>
#include <regex>
#include <string>

struct FileArgument {
    long long value;
    std::string extension;
};

bool parse_argument(const std::string& argument, FileArgument& result) {
    static const std::regex pattern(R"(^(-?[0-9]+)\.(txt|png)$)");
    std::smatch match;

    if (!std::regex_match(argument, match, pattern)) {
        return false;
    }

    try {
        result.value = std::stoll(match[1].str());
    } catch (...) {
        return false;
    }

    result.extension = match[2].str();
    return true;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Error: exactly two arguments are required.\n";
        return EXIT_FAILURE;
    }

    FileArgument first{};
    FileArgument second{};

    if (!parse_argument(argv[1], first) || !parse_argument(argv[2], second)) {
        std::cerr << "Error: arguments must have format <INT>.<EXT>.\n";
        return EXIT_FAILURE;
    }

    if (first.extension == "txt" && second.extension == "txt") {
        std::cout << (first.value + second.value) / 2 << '\n';
        return EXIT_SUCCESS;
    }

    if (first.extension == "png" && second.extension == "png") {
        std::cout << first.value + second.value << '\n';
        return EXIT_SUCCESS;
    }

    if (first.extension == "txt" && second.extension == "png") {
        if (second.value == 0) {
            std::cerr << "Error: division by zero.\n";
            return EXIT_FAILURE;
        }

        std::cout << first.value % second.value << '\n';
        return EXIT_SUCCESS;
    }

    std::cerr << "Error: unsupported extension combination.\n";
    return EXIT_FAILURE;
}
