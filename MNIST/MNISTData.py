# -*- coding: utf-8 -*-
"""
Created on Sun Oct 05 18:02:19 2014

@author: Administrator
"""
from struct import * 
from pylab import *
from numpy import *
from datetime import *

def getData():
    #读入训练集
    trainingImageFile = open(r'C:\Users\Administrator\Desktop\MNIST\train-images.idx3-ubyte','rb')
    trainingImageFile.read(16)
    trainingData = fromfile(trainingImageFile, dtype = uint8)
    trainingData.shape = -1, 784
    trainingImageFile.close()
    
    #读入训练标签集
    trainingLabelFile = open(r'C:\Users\Administrator\Desktop\MNIST\train-labels.idx1-ubyte','rb')
    trainingLabelFile.read(8)
    trainingLabel = fromfile(trainingLabelFile, dtype = uint8)
    trainingLabelFile.close()
    
    #读入测试数据
    testImageFile = open(r'C:\Users\Administrator\Desktop\MNIST\t10k-images.idx3-ubyte','rb')
    testImageFile.read(16)
    testData = fromfile(testImageFile, dtype = uint8)
    testData.shape = -1, 784
    testImageFile.close()

    #读入训练标签集
    testLabelFile = open(r'C:\Users\Administrator\Desktop\MNIST\t10k-labels.idx1-ubyte','rb')
    testLabelFile.read(8)
    testLabel = fromfile(testLabelFile, dtype = uint8)
    testLabelFile.close()
    
    return trainingData, trainingLabel, testData, testLabel
    
def drawPicture(data, index=0, label = array([])):
    picture =  data[index,:]
    picture.shape = 28, 28
    if len(label):
        print 'the label is:', label[index]
    for i in range(28):
        for j in range(28):
            if picture[i,j]>200:
                plot(j, 28-i, 'ob')
            elif picture[i,j]>100:
                plot(j, 28-i, 'og')
            elif picture[i,j]>50:
                plot(j, 28-i, 'oc')
    xlim(0, 28)
    ylim(0, 28)
    show()
    
    