#include <iostream>
#include <vector>
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <climits>

class ArraySorter {
private:
    std::vector<int> numbers;
    std::vector<int> sorted_numbers;
    double sort_time_ms;
    int min_value;
    int max_value;
    size_t array_size;
    std::string sort_algorithm;

    // Simple manual YAML writer (no external libs)
    void writeYAML(const std::string& filename) {
        std::ofstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Error: Could not create YAML file: " << filename << std::endl;
            return;
        }

        // Write YAML metadata
        file << "# Array Sorting Metadata\n";
        file << "---\n";
        file << "sorting_metadata:\n";
        file << "  timestamp: \"" << getCurrentTimestamp() << "\"\n";
        file << "  algorithm: \"" << sort_algorithm << "\"\n";
        file << "  array_size: " << array_size << "\n";
        file << "  execution_time_ms: " << std::fixed << std::setprecision(3) << sort_time_ms << "\n";
        file << "  statistics:\n";
        file << "    min_value: " << min_value << "\n";
        file << "    max_value: " << max_value << "\n";
        file << "    range: " << (max_value - min_value) << "\n";

        // Write original array
        file << "  original_array:\n";
        file << "    - [";
        for (size_t i = 0; i < numbers.size(); ++i) {
            file << numbers[i];
            if (i < numbers.size() - 1) file << ", ";
        }
        file << "]\n";

        // Write sorted array
        file << "  sorted_array:\n";
        file << "    - [";
        for (size_t i = 0; i < sorted_numbers.size(); ++i) {
            file << sorted_numbers[i];
            if (i < sorted_numbers.size() - 1) file << ", ";
        }
        file << "]\n";

        // Performance metrics
        file << "  performance:\n";
        file << "    elements_per_second: " << std::fixed << std::setprecision(0)
             << (array_size / (sort_time_ms / 1000.0)) << "\n";
        file << "    time_per_element_ns: " << std::fixed << std::setprecision(2)
             << (sort_time_ms * 1000000.0 / array_size) << "\n";

        // Additional info
        file << "  verification:\n";
        file << "    is_sorted: " << (isSorted() ? "true" : "false") << "\n";
        file << "    first_element: " << sorted_numbers[0] << "\n";
        file << "    last_element: " << sorted_numbers[array_size - 1] << "\n";

        file.close();
        std::cout << "✅ Metadata saved to: " << filename << std::endl;
    }

    std::string getCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        auto tm = *std::localtime(&time_t);

        char buffer[100];
        std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &tm);
        return std::string(buffer);
    }

    bool isSorted() {
        for (size_t i = 1; i < sorted_numbers.size(); ++i) {
            if (sorted_numbers[i] < sorted_numbers[i-1]) {
                return false;
            }
        }
        return true;
    }

    void findMinMax() {
        if (numbers.empty()) {
            min_value = max_value = 0;
            return;
        }

        min_value = max_value = numbers[0];
        for (int num : numbers) {
            if (num < min_value) min_value = num;
            if (num > max_value) max_value = num;
        }
    }

public:
    // Constructor with initializer list
    ArraySorter(std::initializer_list<int> init_list) : numbers(init_list) {
        array_size = numbers.size();
        sorted_numbers = numbers; // Copy for sorting
    }

    // Constructor with vector
    ArraySorter(const std::vector<int>& nums) : numbers(nums) {
        array_size = numbers.size();
        sorted_numbers = numbers; // Copy for sorting
    }

    // Sort using std::sort (Quicksort/Introsort hybrid)
    void sortArray(const std::string& algorithm = "std::sort") {
        if (numbers.empty()) {
            std::cout << "⚠️  Array is empty, nothing to sort." << std::endl;
            return;
        }

        sort_algorithm = algorithm;
        findMinMax();

        std::cout << "🔄 Sorting array of " << array_size << " elements..." << std::endl;
        std::cout << "   Range: " << min_value << " to " << max_value << std::endl;

        // Measure sorting time
        auto start = std::chrono::high_resolution_clock::now();

        if (algorithm == "bubble_sort") {
            bubbleSort();
        } else if (algorithm == "selection_sort") {
            selectionSort();
        } else if (algorithm == "insertion_sort") {
            insertionSort();
        } else {
            // Default: use std::sort (highly optimized)
            std::sort(sorted_numbers.begin(), sorted_numbers.end());
        }

        auto end = std::chrono::high_resolution_clock::now();

        // Calculate time in milliseconds
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        sort_time_ms = duration.count() / 1000.0;

        std::cout << "✅ Sorting completed in " << std::fixed << std::setprecision(3)
                  << sort_time_ms << " ms" << std::endl;
    }

    // Manual bubble sort implementation
    void bubbleSort() {
        for (size_t i = 0; i < array_size - 1; ++i) {
            for (size_t j = 0; j < array_size - i - 1; ++j) {
                if (sorted_numbers[j] > sorted_numbers[j + 1]) {
                    std::swap(sorted_numbers[j], sorted_numbers[j + 1]);
                }
            }
        }
    }

    // Manual selection sort implementation
    void selectionSort() {
        for (size_t i = 0; i < array_size - 1; ++i) {
            size_t min_idx = i;
            for (size_t j = i + 1; j < array_size; ++j) {
                if (sorted_numbers[j] < sorted_numbers[min_idx]) {
                    min_idx = j;
                }
            }
            if (min_idx != i) {
                std::swap(sorted_numbers[i], sorted_numbers[min_idx]);
            }
        }
    }

    // Manual insertion sort implementation
    void insertionSort() {
        for (size_t i = 1; i < array_size; ++i) {
            int key = sorted_numbers[i];
            int j = i - 1;
            while (j >= 0 && sorted_numbers[j] > key) {
                sorted_numbers[j + 1] = sorted_numbers[j];
                j--;
            }
            sorted_numbers[j + 1] = key;
        }
    }

    // Display arrays
    void displayArrays() {
        std::cout << "\n📊 Array Information:" << std::endl;
        std::cout << "   Size: " << array_size << " elements" << std::endl;
        std::cout << "   Min value: " << min_value << std::endl;
        std::cout << "   Max value: " << max_value << std::endl;
        std::cout << "   Algorithm: " << sort_algorithm << std::endl;

        std::cout << "\n🔤 Original array: [";
        for (size_t i = 0; i < std::min(size_t(10), numbers.size()); ++i) {
            std::cout << numbers[i];
            if (i < std::min(size_t(10), numbers.size()) - 1) std::cout << ", ";
        }
        if (numbers.size() > 10) std::cout << ", ...";
        std::cout << "]" << std::endl;

        std::cout << "✅ Sorted array:   [";
        for (size_t i = 0; i < std::min(size_t(10), sorted_numbers.size()); ++i) {
            std::cout << sorted_numbers[i];
            if (i < std::min(size_t(10), sorted_numbers.size()) - 1) std::cout << ", ";
        }
        if (sorted_numbers.size() > 10) std::cout << ", ...";
        std::cout << "]" << std::endl;
    }

    // Save metadata to YAML file
    void saveMetadata(const std::string& filename = "sort_metadata.yml") {
        writeYAML(filename);
    }

    // Generate random array for testing
    static std::vector<int> generateRandomArray(size_t size, int min_val = 1, int max_val = 1000) {
        std::vector<int> arr;
        arr.reserve(size);

        // Simple random number generation (no external libs)
        srand(time(nullptr));
        for (size_t i = 0; i < size; ++i) {
            int random_num = min_val + (rand() % (max_val - min_val + 1));
            arr.push_back(random_num);
        }
        return arr;
    }
};

// Demo function
void runSortingDemo() {
    std::cout << "🚀 C++ Array Sorting Demo\n" << std::endl;

    // Example 1: Small predefined array
    std::cout << "=== Example 1: Small Array ===" << std::endl;
    ArraySorter sorter1({64, 34, 25, 12, 22, 11, 90, 88, 76, 50, 42});
    sorter1.sortArray("std::sort");
    sorter1.displayArrays();
    sorter1.saveMetadata("small_array_sort.yml");

    std::cout << "\n=== Example 2: Bubble Sort Comparison ===" << std::endl;
    ArraySorter sorter2({64, 34, 25, 12, 22, 11, 90});
    sorter2.sortArray("bubble_sort");
    sorter2.displayArrays();
    sorter2.saveMetadata("bubble_sort_metadata.yml");

    // Example 3: Larger random array
    std::cout << "\n=== Example 3: Large Random Array ===" << std::endl;
    auto large_array = ArraySorter::generateRandomArray(1000, 1, 10000);
    ArraySorter sorter3(large_array);
    sorter3.sortArray("std::sort");
    sorter3.displayArrays();
    sorter3.saveMetadata("large_array_sort.yml");

    std::cout << "\n🎯 All sorting operations completed!" << std::endl;
}

int main() {
    try {
        runSortingDemo();

        // Interactive mode
        std::cout << "\n" << std::string(50, '=') << std::endl;
        std::cout << "🔧 Custom Array Sorting" << std::endl;
        std::cout << "Enter numbers separated by spaces (or 'q' to quit): ";

        std::string input;
        std::getline(std::cin, input);

        if (input != "q" && !input.empty()) {
            std::vector<int> custom_numbers;
            std::istringstream iss(input);
            int num;

            while (iss >> num) {
                custom_numbers.push_back(num);
            }

            if (!custom_numbers.empty()) {
                ArraySorter custom_sorter(custom_numbers);
                custom_sorter.sortArray("std::sort");
                custom_sorter.displayArrays();
                custom_sorter.saveMetadata(OUT_SORTED.YML);
            }
        }

    } catch (const std::exception& e) {
        std::cerr << "❌ Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
