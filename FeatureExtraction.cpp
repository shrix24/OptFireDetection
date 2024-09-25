#include <iostream>
#include <vector>
#include <opencv4/opencv2/imgproc.hpp>
#include "FeatureExtraction.hpp"

using namespace std;
using namespace cv;

class Window_Features{
    private:
        vector<Mat> m_channels;
        vector<float> m_features;
        float* m_training_features;
        Scalar m_mean;
        Scalar m_std_dev;
        double m_max;
        double m_min;
        Scalar means[3];
        Scalar std_devs[3];
        Scalar maxes[3];
        Scalar mins[3];

    public:
        vector<float> features;
        float* training_features;

    private:
        vector<float> calc_infer_features(Mat image){
            split((InputArray)image, (OutputArrayOfArrays)m_channels);
            size_t num_channels = m_channels.size();

            for(int i=0;i<num_channels;i++){
                meanStdDev((InputArray)m_channels[i], m_mean, m_std_dev);
                minMaxLoc((InputArray)m_channels[i], &m_min, &m_max, NULL, NULL);
                means[i] = m_mean;
                std_devs[i] = m_std_dev;
                maxes[i] = m_max;
                mins[i] = m_min;
            }

            features.insert(features.end(), means, means+3);
            features.insert(features.end(), std_devs, std_devs+3);
            features.insert(features.end(), maxes, maxes+3);
            features.insert(features.end(), mins, mins+3);

            return features;
        }

        float* calc_training_features(uint64* dataset){

        }

    public:
        float* get_training_features(){
            float* training_features = m_training_features;
            return training_features;
        }
        vector<float> get_infer_features(){
            vector<float> features = m_features;
            return features;
        }
};

