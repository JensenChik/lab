# -*- coding: utf-8 -*-
"""
Created on Thu Oct 02 17:51:57 2014

@author: Administrator
"""
from MNISTData import *
from numpy import *


trainingData, trainingLabel, testData, testLabel = getData()
#归一化
modulus = power(sum(power(trainingData, 2, dtype = int), axis = 1), 0.5)
modulus.shape = -1,1
trainingData = true_divide(trainingData, modulus)

sigma = 10
hit = 0
for sample in range(10000):
   # sample = random.randint(0,10000)
    testPoint = testData[sample,:]
    testPoint.shape = -1, 1
    net = exp((dot(trainingData, testPoint)-1)/sigma)
    possibilityOf = [0 for i in range(10)]
    for i in range(60000):
        possibilityOf[trainingLabel[i]] += net[i]
    guest = argmax(possibilityOf)
    if guest == testLabel[sample]:
        hit += 1    
#    else:
 #       print "sample",sample,":real",testLabel[sample],"guest", guest

print "\ntest complete!"
print hit,"hit"     
print "correct rate:", (hit/100.0)*100,"%"


