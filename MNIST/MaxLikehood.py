# -*- coding: utf-8 -*-
"""
Created on Mon Oct 06 15:46:07 2014

@author: Administrator
"""
from numpy import *
from MNISTData import *
from PCA import *
from time import *
D = 20

trainingData, trainingLabel, testData, testLabel = getData()
trainingData, DimReduVct, PCAmean = PCA(trainingData[:59999], D)
trainingLabel = trainingLabel[:59999]
#下标分类
indexOf = [None for i in range(10)]
for i in range(10):
    indexOf[i] = argwhere(trainingLabel == i)
#均值
meanOf = [None for i in range(10)]
for i in range(10):
    meanOf[i] = mean(trainingData[indexOf[i], : ], axis = 0)
#协方差矩阵
covarianceOf = [None for i in range(10)]
for i in range(10):
    temp = indexOf[i]
    temp.shape = -1
    covarianceOf[i] = cov(trainingData[temp].T)

testData = (testData - PCAmean)
testData = dot(testData, DimReduVct)

print "start"
t = time()
#识别
hit = 0
for sample in range(10000):
    testPoint = testData[sample,:]
    possibilityOf = [0 for i in range(10)]
    for i in range(10):
        possibilityOf[i] = exp(-0.5*dot(dot((testPoint- meanOf[i]),inv(covarianceOf[i])),(testPoint- meanOf[i]).T)) / sqrt(det(covarianceOf[i])) 
    guest = argmax( possibilityOf)
    if guest == testLabel[sample]:
        hit += 1
print "\ntest complete!"
print hit,"hit"     
print "correct rate:", (hit/10000.0)*100,"%"
print time() - t
