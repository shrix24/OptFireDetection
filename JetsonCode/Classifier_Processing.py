import cv2
import numpy as np
import pywt
from scipy.stats import skew, kurtosis


class GaborParams:
    def __init__(self, ksize, sigma, gamma, psi, lambd) -> None:
        self.ksize = ksize
        self.sigma = sigma
        self.gamma = gamma
        self.psi = psi
        self.lambd = lambd

    def __repr__(self) -> str:
        return {f"Kernel size is:({self.ksize}, {self.ksize})",
                f"Sigma (std. deviation) is: {self.sigma}",
                f"Gamma (aspect ratio) is: {self.gamma}",
                f"Psi (orientation offset) is: {self.psi}",
                f"Lambda (wavelength of sine component) is: {self.lambd}"}

class WindowClassifier_Features:
    def __init__(self, dataset, GaborParams) -> None:
        self.dataset = dataset
        self.sigma = GaborParams.sigma
        self.gamma = GaborParams.gamma
        self.psi = GaborParams.psi
        self.lambd = GaborParams.lambd
        self.ksize = GaborParams.ksize

    def filter_bank_init(self):
        gb1_theta = 1*np.pi/2
        gb2_theta = 1*np.pi/4
        gb3_theta = -1*np.pi/4
        gb4_theta = 1*np.pi

        gb1 = cv2.getGaborKernel((self.ksize, self.ksize), self.sigma, gb1_theta, self.lambd, self.gamma, self.psi)
        gb2 = cv2.getGaborKernel((self.ksize, self.ksize), self.sigma, gb2_theta, self.lambd, self.gamma, self.psi)
        gb3 = cv2.getGaborKernel((self.ksize, self.ksize), self.sigma, gb3_theta, self.lambd, self.gamma, self.psi)
        gb4 = cv2.getGaborKernel((self.ksize, self.ksize), self.sigma, gb4_theta, self.lambd, self.gamma, self.psi)

        return [gb1, gb2, gb3, gb4]

    def calc_gabor_image(self, filter_bank):
        img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        print(filter_bank[0])
        gb0_img = cv2.filter2D(img, cv2.CV_8SC3, filter_bank[0])
        gb1_img = cv2.filter2D(img, cv2.CV_8SC3, filter_bank[1])
        gb2_img = cv2.filter2D(img, cv2.CV_8SC3, filter_bank[2])
        gb3_img = cv2.filter2D(img, cv2.CV_8SC3, filter_bank[3])

        return [gb0_img, gb1_img, gb2_img, gb3_img]

    def calc_features(self):
        channels = cv2.split(self.img)
        means, std_devs, maxes, mins = [], [], [], []

        for i in range(channels.shape[0]):
            mean = np.mean(channels[i])
            std_dev = np.std(channels[i])
            max = np.max(channels[i])
            min = np.max(channels[i])

            means.append(mean)
            std_devs.append(std_dev)
            maxes.append(max)
            mins.append(min)

        means = np.array(means)
        std_devs = np.array(std_devs)
        maxes = np.array(maxes)
        mins = np.array(mins)

        return [means, std_devs, maxes, mins]


    def feature_extract(self):
        feature_data = np.zeros((self.dataset.shape[0], 40))
        filter_bank = self.filter_bank_init()

        for image in range(self.dataset.shape[0]):
            self.img = self.dataset[image, :, :]
            HSV_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
            YCrCb_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2YCrCb)
            
            gb0_img, gb1_img, gb2_img, gb3_img = self.calc_gabor_image(filter_bank)
            gb_imgs = cv2.merge([gb0_img, gb1_img, gb2_img, gb3_img])

            HSV_feats = np.ravel(self.calc_features(HSV_img))
            YCrCb_feats = np.ravel(self.calc_features(YCrCb_img))
            gb_feats = np.ravel(self.calc_features(gb_imgs))

            feature_data[image, :] = np.ravel([HSV_feats, YCrCb_feats, gb_feats])

        return feature_data
    

class Window_Wavelet_Features:
    def __init__(self, dataset) -> None:
        self.dataset = dataset


    def calc_features(self, img):
        channels = cv2.split(img)
        channels = np.array(channels)
        means, std_devs, maxes, mins = [], [], [], []

        for i in range(channels.shape[0]):
            mean = np.median(channels[i])
            std_dev = np.std(channels[i])
            max = np.max(channels[i])
            min = np.min(channels[i])

            means.append(mean)
            std_devs.append(std_dev)
            maxes.append(max)
            mins.append(min)

        means = np.array(means)
        std_devs = np.array(std_devs)
        maxes = np.array(maxes)
        mins = np.array(mins)

        return [means, std_devs, maxes, mins]
    
    
    def wavelet_transform_features(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        coeffs = pywt.dwt2(img, 'bior1.1')
        _, (cH, cV, cD) = coeffs
        coeffs = np.array((cH, cV, cD))

        means, skews, kurts = [], [], []

        for i in range(coeffs.shape[0]):
            coeff_data = np.ndarray.flatten(coeffs[i, :, :])
            mean = np.mean(coeff_data)
            skewness = skew(coeff_data)
            kurt = kurtosis(coeff_data)

            means.append(mean)
            skews.append(skewness)
            kurts.append(kurt)

        means = np.array(means)
        skews = np.array(skews)
        kurts = np.array(kurts)

        return [means, skews, kurts]


    def feature_extract(self):
        feature_data = np.zeros((self.dataset.shape[0], 33))

        for image in range(self.dataset.shape[0]):
            self.img = self.dataset[image, :, :]
            YCrCb_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2YCrCb)

            RGB_feats = np.ravel(self.calc_features(self.img))
            YCrCb_feats = np.ravel(self.calc_features(YCrCb_img))
            wavelet_feats = np.ravel(self.wavelet_transform_features(self.img))

            feature_data[image, :] = np.concatenate([RGB_feats, YCrCb_feats, wavelet_feats], axis=0)

        return feature_data
    
    
    def feature_extract_infer(self, img):
        feature_data = np.zeros((1, 33))

        YCrCb_img = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            
        RGB_feats = np.ravel(self.calc_features(img))    
        YCrCb_feats = np.ravel(self.calc_features(YCrCb_img))
        wavelet_feats = np.ravel(self.wavelet_transform_features(img))

        feature_data = np.concatenate([RGB_feats, YCrCb_feats, wavelet_feats], axis=0)

        return feature_data


if __name__ == "__main__":
    pass