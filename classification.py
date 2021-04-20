# -*- coding: utf-8 -*- 
import sys
import time
import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage import metrics
import imagehash
from PIL import Image

#
#Basic config (counter and mid number refreshing)
#
REFRESH_RATE = 3000 #every $$$ processed images
DEGRADE_TO   = 500 #refreshing degrades mid counter to $$$

#sys.stdout.reconfigure(encoding='utf-8')


#
#Exceptions
#
class ImageClassificationError(Exception):
    def __init__(self, text):
        self.txt = text

class CapModeClassificationError(Exception):
    def __init__(self, text):
        self.txt = text

class CompareHashError(Exception):
    def __init__(self, text):
        self.txt = text

#
#DAY/NIGHT camera mode classification (if gray color = night, else = day)
#
def captureModeClassification(frame):
    try:
        r,g,b=cv2.split(frame)
        r_g=np.count_nonzero(abs(r-g))
        r_b=np.count_nonzero(abs(r-b))
        g_b=np.count_nonzero(abs(g-b))
        diff_sum=float(r_g+r_b+g_b)
        ratio=diff_sum/frame.size
        day = False
        #print('ratio: ' + str(ratio))
        if ratio > 0.1:
            day = True
        else:
            day = False
        return day
    except Exception as e:
        raise CapModeClassificationError("Capture Mode Classification error: " + str(e))

#
#Math functions to find difference between images (mse and compare images not using in current version, 
#compare hash have better quality)
#
def mse(imageA, imageB):
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	return err
 
def compare_images(imageA, imageB):
    imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    s = metrics.structural_similarity(imageA, imageB)
    return s

def compare_hash(imageA, imageB):
    try:
        hash_1 = imagehash.dhash(Image.open(imageA))
        hash_2 = imagehash.dhash(Image.open(imageB))
        return (hash_1 - hash_2)
    except Exception as e:
        raise CompareHashError("Compare Hash error: " + str(e))

#
#Adaptive algorithm to compare images using middle value and adaptive threshold 
#Works good with stable light in room 
#You can rewrite it to make better results in different light states in room
#
def processSingleImage(original, image, min_res, max_res, mid_res_array, adaptive_threshold, debug_mode, at_mr_top, at_mr_bot, maxr_midr, midr_minr, at_add_step, at_sub_step, adaptive_mode, fixed_th):#, threshold):   
    result = False
    try:
        result = compare_hash(original, image)
        compare_result = result
        if adaptive_mode:       
            if result < min_res:
                min_res = result
            elif result > max_res:
                max_res = result
            if adaptive_threshold == 0 or adaptive_threshold == None:
                adaptive_threshold = (min_res + max_res) / 2
            mid_res_array[0] = mid_res_array[0] + result
            mid_res_array[1] = mid_res_array[1] + 1
            mid_res = mid_res_array[0] / mid_res_array[1]
            if (adaptive_threshold - mid_res) < at_mr_bot and (max_res - mid_res) > maxr_midr:           #3 6 standart
                adaptive_threshold = adaptive_threshold + at_add_step                                              #3 stan
            elif (adaptive_threshold - mid_res) > at_mr_top and (mid_res - min_res) > midr_minr:        #10 6 standart
                adaptive_threshold = adaptive_threshold - at_sub_step                                             #5 stan
            if debug_mode:
                print('\t\tMin res: ' + str(min_res) + '; Max res: ' + str(max_res) + '; Mid res: ' + str(round(mid_res, 2)) + '; Compare Result: ' + str(compare_result) + '; Adaptive Threshold: ' + str(adaptive_threshold))
            if int(result) > adaptive_threshold:
                result = True
            else:
                result = False
        else:
            if debug_mode:
                print('\t\tCompare result: ' + str(result) + '; Fixed threshold: ' + str(fixed_th) )
            if int(result) > fixed_th:
                result = True
            else:
                result = False
    except PermissionError:
        print('Image not ready now and will be processed in next iteration.')
        raise PermissionError
    except Exception as e:
        raise ImageClassificationError('ICErr Msg: ' + str(e))
    if adaptive_mode:
        if mid_res_array[1] > REFRESH_RATE: 
            mid_res_array[0] = int(mid_res_array[0] / (REFRESH_RATE/DEGRADE_TO))
            mid_res_array[1] = DEGRADE_TO
    return [result, min_res, max_res, mid_res_array, adaptive_threshold, compare_result]