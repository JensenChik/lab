# -*- coding: utf-8 -*-
"""
Created on Fri Oct 10 11:58:56 2014

@author: Administrator
"""

from numpy import *

def PCA(trainingData, k = 2):
    means = mean(trainingData)
    covariance = cov(trainingData.T)
    scatterMatrix =  (covariance.shape[0] - 1) *  covariance
    eigVal, eigVct = linalg.eig(scatterMatrix)
    topK = argsort(eigVal)[-k : ]
    DimReduVct = eigVct[:,topK]
    principal = (trainingData - means)
    principal = dot(principal, DimReduVct)
    return principal, DimReduVct,means
    

    