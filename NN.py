# -*- coding: utf-8 -*-
"""
Created on Sun Oct 05 17:42:10 2014

@author: Administrator
"""

from numpy import *
from MNISTData import *

trainingData, trainingLabel, testData, testLabel = getData()

hit = 0
for sample in range(10000):
#    sample = random.randint(0,10000)
    testPoint = testData[sample,:]
    distance = subtract(trainingData, testPoint,dtype = int)
    distance = distance**2
    distance = sum(distance, axis = 1)
    guest = trainingLabel[argmin(distance)]
    if guest == testLabel[sample]:
        hit += 1
#    else:
#        print "sample",sample,":real",testLabel[sample],"guest", guest
        
print "\ntest complete!"
print hit,"hit"     
print "correct rate:", (hit/100.0)*100,"%"
























