import cv2
import numpy as np
import pywt
from skimage.util import view_as_blocks

class ImageProcessor:
    def __init__(self, image) -> None:
        self.image = image

    def preprocessor(self):
        B_n = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint16)
        G_n = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint16)
        R_n = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint16)

        img_copy = np.zeros((self.image.shape), dtype=np.uint16)
        img_copy = self.image.copy()

        color_criteria = (img_copy[:, :, 0]>150) & (img_copy[:, :, 1]>190) & (img_copy[:, :, 2]>210)
        img_copy[color_criteria] = [0, 0, 0]
        
        channel_sum = np.uint32(img_copy[:, :, 0] + img_copy[:, :, 1] + img_copy[:, :, 2])
        channel_sum = np.nan_to_num(channel_sum, False, 1)
        channel_sum_corrected = np.where(channel_sum==0, 1, channel_sum)

        B_n = (255*img_copy[:, :, 0])/channel_sum_corrected
        G_n = (255*img_copy[:, :, 1])/channel_sum_corrected
        R_n = (255*img_copy[:, :, 2])/channel_sum_corrected

        self.pp_image = np.zeros((self.image.shape), dtype=np.uint16)
        self.pp_image = cv2.merge([B_n, G_n, R_n])

        return self.pp_image
    
    def vbi_idx(self):
        B_n, G_n, R_n = cv2.split(self.pp_image)
        self.vbi = np.zeros((B_n.shape[0], B_n.shape[1]), dtype=np.int16)
        add_result = cv2.add(R_n, B_n)
        self.vbi = cv2.subtract(2*G_n, add_result)
        self.vbi = cv2.GaussianBlur(self.vbi, (5, 5), 125, 200)

        return self.vbi
    
    def fi_idx(self):
        B_n, G_n, R_n = cv2.split(self.pp_image)
        self.fi = np.zeros(B_n.shape, dtype=np.int16)
        add_result = cv2.add(G_n, B_n)
        self.fi = cv2.subtract(3*R_n, add_result)
        self.fi = cv2.GaussianBlur(self.fi, (5, 5), 125, 200)

        return self.fi
    
    def ffi_idx(self, alpha):
        self.ffi = np.zeros((self.image.shape[0:2]), dtype=np.int16)
        self.ffi = alpha*self.fi - self.vbi
        self.ffi = cv2.GaussianBlur(self.ffi, (5, 5), 125, 200)
        self.ffi = self.ffi.astype(np.uint16)

        return self.ffi
    
    def calc_tf(self, alpha):
        ffi_sigma = np.std(self.ffi)
        vbi_sigma = np.std(self.vbi)

        self.tf = (alpha*ffi_sigma + vbi_sigma)/(alpha+1)

        return self.tf
    
    def ffi_binarize(self):
        self.ffi_bin = np.zeros((self.ffi.shape), dtype=np.uint8)
        self.ffi_bin = np.where(self.ffi>self.tf, 255, 0).astype(np.uint8)

        return self.ffi_bin
    
    def erosion(self):
        self.ffi_eroded = cv2.erode(self.ffi_bin, (7, 7), iterations=1)

        return self.ffi_eroded
    
    def dilation(self):
        self.ffi_dilated = cv2.dilate(self.ffi_eroded, (7, 7), iterations=1)

        return self.ffi_dilated
    
    def blur(self):
        self.ffi_blurred = cv2.GaussianBlur(self.ffi_dilated, (7, 7), 100, 175)

        return self.ffi_blurred
    
    def rule_1(self, beta):
        self.rule1_result = np.zeros(np.shape(self.vbi), dtype=np.uint8)
        cond1 = np.where(abs(self.pp_image[:, :, 2]-self.pp_image[:, :, 1])<beta, 255, 0)
        cond2 = np.where(abs(self.pp_image[:, :, 1]-self.pp_image[:, :, 0])<beta, 255, 0)
        cond3 = np.where(abs(self.pp_image[:, :, 2]-self.pp_image[:, :, 0])<beta, 255, 0)

        cond_result = cv2.bitwise_or(cond1, cond2)
        cond_result = cv2.bitwise_or(cond_result, cond3)

        return self.rule1_result
    
    def rule_2(self, R_thresh, B_thresh):
        self.rule2_result = np.zeros(np.shape(self.vbi), dtype=np.uint8)
        cond1 = np.where(self.pp_image[:, :, 2]>R_thresh, 255, 0)
        cond2 = np.where(self.pp_image[:, :, 0]<B_thresh, 255, 0)
        cond_result = cv2.bitwise_or(cond1, cond2)

        return cond_result
    
    def rule_3(self):
        self.I_ty = np.zeros((np.shape(self.vbi)[0], np.shape(self.vbi)[1]), dtype=np.uint16)
        self.I_ty = (self.pp_image[:, :, 0] + self.pp_image[:, : , 1] + self.pp_image[:, :, 2])/3
        self.rule3_result = np.zeros(np.shape(self.rule1_result), dtype=np.uint8)

        cond1 = np.where(self.I_ty > 80, 255, 0)
        cond2 = np.where(self.I_ty < 150, 255, 0)
        cond3 = np.where(self.I_ty > 150, 255, 0)
        cond4 = np.where(self.I_ty < 220, 255, 0)
        cond1_result = cv2.bitwise_and(cond1, cond2)
        cond2_result = cv2.bitwise_and(cond3, cond4)
        cond_result = cv2.bitwise_and(cond1_result, cond2_result)

        return cond_result
    
    def wavelet_transform(self, D_fs, D_o):
        D_fs_g = cv2.cvtColor(D_fs, cv2.COLOR_BGR2GRAY)
        D_o_g = cv2.cvtColor(D_o, cv2.COLOR_BGR2GRAY)

        _, (LH_fs, HL_fs, HH_fs) = pywt.dwt2(D_fs_g, 'db2')
        _, (LH_o, HL_o, HH_o) = pywt.dwt2(D_o_g, 'db2')

        E_fs = np.zeros(LH_fs.shape, dtype=np.float32)
        E_o = np.zeros(LH_o.shape, dtype=np.float32)

        E_fs = LH_fs**2 + HL_fs**2 + HH_fs**2
        E_o = LH_o**2 + HL_o**2 + HH_o**2

        E_fs = np.delete(E_fs, -1, axis=0)
        E_fs = np.delete(E_fs, -1, axis=1)
        E_o = np.delete(E_o, -1, axis=0)
        E_o = np.delete(E_o, -1, axis=1)

        block_shape = (5, 5)
        E_fs_blocks = view_as_blocks(E_fs, block_shape)
        E_o_blocks = view_as_blocks(E_o, block_shape)

        E_fs_map = np.zeros((E_fs_blocks.shape[0], E_fs_blocks.shape[1]), dtype=np.uint16)
        E_o_map = np.zeros((E_o_blocks.shape[0], E_o_blocks.shape[1]), dtype=np.uint16)
        E_noise = np.zeros((E_o_blocks.shape[0], E_o_blocks.shape[1]), dtype=np.uint16)

        for i in range(E_fs_blocks.shape[0]):
            for j in range(E_o_blocks.shape[1]):
                E_fs_map[i, j] = np.ndarray.sum(E_fs_blocks[i, j])
                E_o_map[i, j] = np.ndarray.sum(E_o_blocks[i, j])
                
                if E_fs_map[i, j] > E_o_map[i, j]:
                    E_noise[i, j] = 255
                else:
                    E_noise[i, j] = 0

                if E_fs_map[i, j] > 0:
                    E_fs_map[i, j] = 255
                else:
                    E_fs_map[i, j] = 0

        E_result = np.zeros((E_o_blocks.shape[0], E_o_blocks.shape[1]), dtype=np.uint8)
        E_result = (E_fs_map - E_noise).astype(np.uint8)

        E_result = cv2.resize(E_result, (500, 500), cv2.INTER_AREA)

        return E_result


if __name__=="__main__":
    pass