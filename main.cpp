#include <iostream>
#include <stdlib.h>
#include <string>
#include <filesystem>
#include <opencv4/opencv2/imgproc.hpp>
#include <opencv4/opencv2/imgcodecs.hpp>

using namespace cv;
using namespace std;
namespace fs = filesystem;

int main(int argc, char**argv){
    if (argc!=2){
        cout << "Usage: ./main <training_dir_path> <testing_dir_path> <model_save_path>" << endl;
        return -1;
    }

    fs::path training_dir = argv[1];
    fs::path testing_dir = argv[2];

    if (fs::exists(training_dir)){

        Mat dataset
        for(const auto& entry: fs::directory_iterator(training_dir)){
            Mat img = imread(entry.path());
            resize((InputArray)img, (OutputArray))

        }
    }




}