import numpy as np
import sys
import os
from array import array
import random
import math
import tqdm
from struct import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm


#변수 정의
TrainImg = []
TrainLabel = []
TestImg = []
TestLabel = []
epoch = 0
Lost = 1000000000000000
PaddingNum = 0
TrainImgNum = 10000
KernelSize = 3
Filter1Count = 4
Filter2Count = 8
F1 = np.random.randn(KernelSize * KernelSize, Filter1Count) * np.sqrt(2/ KernelSize * KernelSize * Filter1Count)
F2 = np.random.randn(Filter1Count, KernelSize * KernelSize, Filter2Count) * np.sqrt(2/Filter1Count * (KernelSize * KernelSize) * Filter2Count)
F3 = np.random.randn(7 *7 *Filter2Count, 10) * np.sqrt(2 / 7 * 7 * Filter2Count * 10)
Input = []
MaxPoolingL1Result = np.zeros((Filter1Count, 28, 28), dtype = float)
MaxPoolingL2Result = np.zeros((Filter2Count, 14, 14), dtype = float)
bias = np.ones((10))
learning_rate = 0.01
WrongCount=0
plt.switch_backend('agg')


def Padding(img, size):
    if np.array(img.shape).size == 2:
        height, width = img.shape
        img = np.insert(img, [0, width], [PaddingNum, PaddingNum], axis=1)
        img = np.insert(img, 0, np.zeros(width+2), axis=0)
        img = np.insert(img, height+1, np.zeros(width + 2), axis=0)
        return img
    else:
        depth, height, width = img.shape
        result = np.zeros((depth, height + size*2, width + size*2))
        for d in range(depth):
            for h in range(height):
                for w in range(width):
                    result[d][h+1][w+1] = img[d][h][w]
        return result



def ChangeToConvolutionMatrix(img):
    if np.array(img.shape).size == 2:
        height, width = img.shape
        matrix = np.zeros(KernelSize * KernelSize)
        for i in range(28):
            for j in range (28):
                array = img[i][j:j+KernelSize]
                for k in np.arange(1, KernelSize):
                    array1 = img[i + k][j:j+KernelSize].copy()
                    array = np.concatenate((array, array1))
                matrix = np.vstack((matrix, array))
        matrix = np.delete(matrix, 0, axis = 0)
        return matrix
    else:
        depth, height, width = img.shape
        cube = np.zeros((depth, 14*14, 9))

        for d in range(depth):
            matrix = np.zeros(KernelSize * KernelSize)
            for i in range(14):
                for j in range(14):
                    array = img[d][i][j:j + KernelSize]
                    for k in np.arange(1, KernelSize):
                        array1 = img[d][i + k][j:j + KernelSize]
                        array = np.concatenate((array, array1))
                    matrix = np.vstack((matrix, array))
            matrix = np.delete(matrix, 0, axis=0)
            cube[d] = matrix
        return cube

def ReLU(img):
    height, width = img.shape
    for i in range(height):
        for j in range(width):
            img[i][j] = max(img[i][j], 0)
    return img

def MaxPooling(input):
    depth, height, width = input.shape
    LayerMax = np.zeros((depth, int(height/2), int(width/2)))
    for d in range(depth):
        for h in range(height):
            if h%2 != 0:
                continue
            else:
                for w in range(width):
                    if w %2 != 0:
                        continue
                    else:
                        list = [input[d][h][w],input[d][h][w+1], input[d][h+1][w], input[d][h+1][w+1]]
                        value = max(list)
                        index = list.index(value)
                        if index == 0:
                            if depth == Filter1Count:
                                MaxPoolingL1Result[d][h][w] = 1
                            elif depth == Filter2Count:
                                MaxPoolingL2Result[d][h][w] = 1
                            else:
                                print("MaxPooling Error!\n")
                                return -1

                        elif index == 1:
                            if depth == Filter1Count:
                                MaxPoolingL1Result[d][h][w+1] = 1
                            elif depth == Filter2Count:
                                MaxPoolingL2Result[d][h][w+1] = 1
                            else:
                                print("MaxPooling Error!\n")
                                return -1

                        elif index == 2:
                            if depth == Filter1Count:
                                MaxPoolingL1Result[d][h+1][w] = 1
                            elif depth == Filter2Count:
                                MaxPoolingL2Result[d][h+1][w] = 1
                            else:
                                print("MaxPooling Error!\n")
                                return -1
                        else:
                            if depth == Filter1Count:
                                MaxPoolingL1Result[d][h+1][w+1] = 1
                            elif depth == Filter2Count:
                                MaxPoolingL2Result[d][h+1][w+1] = 1
                            else:
                                print("MaxPooling Error!\n")
                                return -1

                        LayerMax[d][int(h/2)][int(w/2)] = value
    return LayerMax

def Convolution(img):
    #F1 일때
    if np.array(img.shape).size == 2:
        result = np.matmul(img, F1)
        return result
    #F2 일때
    else:
        depth, height, width = img.shape
        Filterdepth, Filterheight, Filterwidth = F2.shape
        result = np.zeros((height, Filterwidth))
        for h in range(height):
            for w in range(Filterwidth):
                sum = 0
                for d in range(depth):
                    array1 = img[d][h]
                    array2 = F2[d].T[w]
                    sum = sum + np.sum(array1 * array2)
                result[h][w] = sum
        return result

def Softmax(input):
    layer = input - np.max(input)
    layer = np.exp(layer)
    sum = np.sum(layer)
    layer = layer/sum
    return layer

def BackpropagateMaxPooling(input):
    if input.shape[0] == Filter1Count:
        result = MaxPoolingL1Result
        depth, height, width = MaxPoolingL1Result.shape
    elif input.shape[0] == Filter2Count:
        result = MaxPoolingL2Result
        depth, height, width = MaxPoolingL2Result.shape
    else:
        print("Error in BackpropagateMaxPooling")

    for d in range(depth):
        for h in range(height):
            for w in range(width):
                if result[d][h][w] == 0:
                    continue
                else:
                    result[d][h][w] = result[d][h][w] * input[d][int(h/2)][int(w/2)]
    return result





#파일 읽기
fp_train_image = open('C:\\Users\\user\\Documents\\LAB\\MNIST\\training_set\\train-images.idx3-ubyte','rb')
fp_train_label = open('C:\\Users\\user\\Documents\\LAB\\MNIST\\training_set\\train-labels.idx1-ubyte', 'rb')
fp_test_image = open('C:\\Users\\user\\Documents\\LAB\\MNIST\\test_set\\t10k-images.idx3-ubyte','rb')
fp_test_label = open('C:\\Users\\user\\Documents\\LAB\\MNIST\\test_set\\t10k-labels.idx1-ubyte','rb')
#read mnist and show numberc

#train data 저장
while True:
    s  = fp_train_image.read(784) #784 바이트씩 읽음
    label = fp_train_label.read(1) #1 바이트 씩 읽음

    if not s:
        break
    if not label:
        break
    #unpack
    num = int(label[0])
    img = np.array(unpack(len(s) * 'B', s))  # byte를 unsigned char 형식으로
    # img = list(unpack(len(s) * 'B', s))  # byte를 unsigned char 형식으로
    if len(img) !=  784:
        continue
    elif num >9 : continue
    else:
        img = np.reshape(img, (28,28))
        img = img/255.0

        TrainImg.append(img)
        TrainLabel.append(num)

TrainImg = np.array(TrainImg)


#test data 저장
while True:
    s = fp_test_image.read(784)  # 784 바이트씩 읽음
    label = fp_test_label.read(1)  # 1 바이트 씩 읽음

    if not s:
        break
    if not label:
        break

    # unpack
    num = int(label[0])
    img =  np.reshape(np.array(unpack(len(s) * 'B', s)), (28,28))  # byte를 unsigned char 형식으로

    TestImg.append(img)
    TestLabel.append(num)

TestImg = np.array(TestImg)
TestImg = TestImg/255.0





TrainImgNum = len(TrainImg)

epoch = 0
while epoch <10:
    for i in tqdm.tqdm(range(TrainImgNum)):
        L1 = TrainImg[i]
        L1Padding = Padding(L1, 1)
        L1ConvolBefore = ChangeToConvolutionMatrix(L1Padding)
        L1ConvolAfter = Convolution(L1ConvolBefore)
        L1ReLu = ReLU(L1ConvolAfter)
        L1T = L1ReLu.T
        L1Reshape = np.reshape(L1T, (Filter1Count, 28, 28))
        MaxPoolingL1Result = np.zeros((Filter1Count, 28, 28))
        L2 = MaxPooling(L1Reshape)

        L2Padding = Padding(L2, 1)
        L2ConvolBefore = ChangeToConvolutionMatrix(L2Padding)
        L2ConvolAfter = Convolution(L2ConvolBefore)
        L2ReLU = ReLU(L2ConvolAfter)
        L2T = L2ReLU.T
        L2ReShape = np.reshape(L2T, (Filter2Count, 14, 14))
        MaxPoolingL2ResultMatrix = np.zeros((Filter2Count, 14, 14), dtype = float)
        L3 = MaxPooling(L2ReShape)
        L3Reshape = np.reshape(L3, (1, -1))
        L3FullConnect = np.matmul(L3Reshape, F3)

        L3Input = L3FullConnect + bias

        for i in range(10):
            if L3Input[0][i] < -709:
                L3Input[0][i] = -709
        L3Output = 1 / (1 + np.exp(-L3Input))


        if ((np.argmax(L3Output)+1) != TrainLabel[i]):
            WrongCount+=1
        #Backpropagation
        onehot = np.zeros(10, dtype=float)
        onehot[TrainLabel[i]] = 1

        # DErrorByL3Output =P - target
        DErrorByBias = DErrorByL3FullConnect = L3Output - onehot
        DErrorByF3 = np.matmul(L3Reshape.T , DErrorByL3FullConnect)
        DErrorByL3Reshape = np.matmul(DErrorByL3FullConnect, F3.T)
        DErrorByL3 = np.reshape(DErrorByL3Reshape, (Filter2Count, 7, 7))
        DErrorByL2Reshape = BackpropagateMaxPooling(DErrorByL3)
        DErrorByL2Reshape = np.reshape(DErrorByL2Reshape, (Filter2Count, 14*14))
        DErrorByL2T = DErrorByL2Reshape.T
        #ReLus는 동일하니까
        DErrorByL2ConvolAfter = DErrorByL2T

        #F2
        DErrorByF2 = np.zeros((Filter1Count, KernelSize * KernelSize, Filter2Count), dtype = float)
        DErrorByL2ConvolBefore = np.zeros((Filter1Count, 14 * 14, KernelSize*KernelSize), dtype = float)

        for h in range(DErrorByL2ConvolAfter.shape[0]): #14*14
            for w in range(DErrorByL2ConvolAfter.shape[1]): #Filter2Count
                for d in range(Filter1Count):
                    for k in range(KernelSize * KernelSize):
                        DErrorByL2ConvolBefore[d][h][k] = F2[d][k][w] * DErrorByL2ConvolAfter[h][w]
                        DErrorByF2[d][k][w] = L2ConvolBefore[d][h][k] * DErrorByL2ConvolAfter[h][w]

        #Padding & ChangeToConvolutionMatrix Backpropagation
        DErrorByL2Padding = np.zeros((Filter1Count, 16, 16))
        depth, height, width = DErrorByL2ConvolBefore.shape

        for h in range(height):
            row = int(h / 14)
            col = h % 14
            DErrorByL2Padding[:, row:(row+1), col:(col+3)] += DErrorByL2ConvolBefore[:, h:h+1, 0:3].copy()
            DErrorByL2Padding[:, row+1:row+2, col: col+3] += DErrorByL2ConvolBefore[:, h:h+1, 3:6].copy()
            DErrorByL2Padding[:, row+2:row+3, col: col + 3] += DErrorByL2ConvolBefore[:, h:h+1, 6:9].copy()

        DErrorByL2 = DErrorByL2Padding[:, 1:15, 1:15].copy()
        DErrorByL1Reshape = BackpropagateMaxPooling(DErrorByL2)
        DErrorByL1Reshape = np.reshape(DErrorByL1Reshape, (Filter1Count, 28*28))
        DErrorByL1T = DErrorByL1Reshape.T
        #ReLU
        DErrorByL1ConvolAfter = DErrorByL1T

        #F1
        DErrorByF1 = np.matmul(L1ConvolBefore.T, DErrorByL1ConvolAfter)
        DErrorByL1ConvolBefore = np.matmul(DErrorByL1ConvolAfter, F1.T)


        F1 = F1 - learning_rate * DErrorByF1
        F2 = F2 - learning_rate *DErrorByF2
        F3 = F3 - learning_rate *DErrorByF3

    print("Wrong count: ", WrongCount, "\n")
    epoch+=1
    WrongCount = 0












