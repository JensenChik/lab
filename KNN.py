# -*- coding: utf-8 -*-
"""
Created on Sun Oct 05 19:16:20 2014

@author: Administrator
"""

from numpy import *
from MNISTData import *

trainingData, trainingLabel, testData, testLabel = getData()

hit = 0
k = 11
for sample in range(10000):
#    sample = random.randint(0,10000)
    testPoint = testData[sample,:]
    distance = subtract(trainingData, testPoint,dtype = int)
    distance = distance**2
    distance = sum(distance, axis = 1)
    indexOfTopK = argsort(distance)[:k]
    labelOfNear = trainingLabel[indexOfTopK]
    possibilityOf = [0 for i in range(10)]
    for i in range(k):
         possibilityOf[labelOfNear[i]] += 1
    guest = argmax(possibilityOf)
    if guest == testLabel[sample]:
        hit += 1
#    else:
 #       print "sample",sample,":real",testLabel[sample],"guest", guest
   #      print labelOfNear
        
print "\ntest complete!"
print hit,"hit"     
print "correct rate:", (hit/10000.0)*100,"%"