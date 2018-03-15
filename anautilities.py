#!/bin/env python

"""
Utilities for vfatqc scans
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

def filePathExists(searchPath, subPath=None, debug=False):
    import os
    
    testPath = searchPath
    if subPath is not None:
        testPath = "%s/%s"%(searchPath, subPath)

    if not os.path.exists(testPath):
        if debug:
            print "Unable to find location: %s"%(testPath)
        return False
    else:
        if debug:
            print "Found %s"%s(testPath)
        return True

def getDirByAnaType(anaType, cName, ztrim=4):
    from anaInfo import ana_config
    
    import os

    # Check anaType is understood
    if anaType not in ana_config.keys():
        print "getDirByAnaType() - Invalid analysis specificed, please select only from the list:"
        print ana_config.keys()
        exit(os.EX_USAGE)
        pass

    # Check Paths
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    dataPath  = os.getenv('DATA_PATH')

    dirPath = ""
    if anaType == "latency":
        dirPath = "%s/%s/%s/trk/"%(dataPath,cName,anaType)
    elif anaType == "scurve":
        dirPath = "%s/%s/%s/"%(dataPath,cName,anaType)
    elif anaType == "thresholdch":
        dirPath = "%s/%s/%s/channel/"%(dataPath,cName,"threshold")
    elif anaType == "thresholdvftrig":
        dirPath = "%s/%s/%s/vfat/trig/"%(dataPath,cName,"threshold")
    elif anaType == "thresholdvftrk":
        dirPath = "%s/%s/%s/vfat/trk/"%(dataPath,cName,"threshold")
    elif anaType == "trim":
        dirPath = "%s/%s/%s/z%f/"%(dataPath,cName,anaType,ztrim)

    return dirPath

def getStringNoSpecials(inputStr):
    """
    returns a string without special characters
    """

    inputStr = inputStr.replace('*','')
    inputStr = inputStr.replace('-','')
    inputStr = inputStr.replace('+','')
    inputStr = inputStr.replace('(','')
    inputStr = inputStr.replace(')','')
    inputStr = inputStr.replace('/','')
    inputStr = inputStr.replace('{','')
    inputStr = inputStr.replace('}','')
    inputStr = inputStr.replace('#','')

    return inputStr

def initVFATArray(array_dtype, nstrips=128):
    import numpy as np
    
    list_dtypeTuple = []

    for idx in range(0,len(array_dtype)):
        if array_dtype.names[idx] == 'vfatN':   continue
        if array_dtype.names[idx] == 'vfatCh':  continue
        if array_dtype.names[idx] == 'panPin':  continue
        if array_dtype.names[idx] == 'ROBstr':  continue
        list_dtypeTuple.append((array_dtype.names[idx],array_dtype[idx]))
        pass

    return np.zeros(nstrips, dtype=list_dtypeTuple)

#Use inter-quartile range (IQR) to reject outliers
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQR(arrayData):
    import numpy as np
    
    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    return (arrayData < (q1 - 1.5 * IQR)) | (arrayData > (q3 + 1.5 * IQR))

#Use inter-quartile range (IQR) to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQROneSided(arrayData, rejectHighTail=True):
    import numpy as np
    
    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    if rejectHighTail:
        return arrayData > (q3 + 1.5 * IQR)
    else:
        return arrayData < (q1 - 1.5 * IQR)

#Use Median absolute deviation (MAD) to reject outliers
#See: https://github.com/joferkington/oost_paper_code/blob/master/utilities.py
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMAD(arrayData, thresh=3.5):
    import numpy as np
    
    median = np.median(arrayData, axis=0)
    diff = np.abs(arrayData - median)
    med_abs_deviation = np.median(diff)

    if med_abs_deviation == 0:
        return isOutlierIQR(arrayData)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation
        return modified_z_score > thresh

#Use MAD to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    import numpy as np
    
    median = np.median(arrayData, axis=0)
    diff = arrayData - median
    med_abs_deviation = np.median(np.abs(diff))

    if med_abs_deviation == 0:
        return isOutlierIQROneSided(arrayData, rejectHighTail)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation

        if rejectHighTail:
            return modified_z_score > thresh
        else:
            return modified_z_score < -1.0 * thresh

def make3x8Canvas(name, initialContent = None, initialDrawOpt = '', secondaryContent = None, secondaryDrawOpt = ''):
    """
    Creates a 3x8 canvas for summary plots.

    name - TName of output TCanvas
    initialContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on the canvas.
    initialDrawOpt - draw option to be used when drawing elements of initialContent
    secondaryContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on top of the canvas.
    secondaryDrawOpt - draw option to be used when drawing elements of secondaryContent
    """

    import ROOT as r
    
    canv = r.TCanvas(name,name,500*8,500*3)
    canv.Divide(8,3)
    if initialContent is not None:
        for vfat in range(24):
            canv.cd(vfat+1)
            initialContent[vfat].Draw(initialDrawOpt)
    if secondaryContent is not None:
        for vfat in range(24):
            canv.cd(vfat+1)
            secondaryContent[vfat].Draw("same%s"%secondaryDrawOpt)
    canv.Update()
    return canv

def parseListOfScanDatesFile(filename, alphaLabels=False, delim='\t'):
    """
    Parses a filename which describes a list of scandates.  Two formats of the filename
    are supported, one in which there are three columns and one in which there are two.
    The first column is always expected to be the chamber name, the second column is 
    always expected to be the scandate.  If a third column is present it is expected to
    be an independent variable and will be alphanumeric input.  Two examples are presented:

    Example1, two columns:

    ChamberName scandate
    GE11-VI-L-CERN-0001    2017.08.11.16.30
    GE11-VI-L-CERN-0001    2017.08.14.20.54
    GE11-VI-L-CERN-0001    2017.08.30.15.03

    Example2, three columns:

    ChamberName scandate indepVarName
    GE11-VI-L-CERN-0001    2017.08.11.16.30 100
    GE11-VI-L-CERN-0001    2017.08.14.20.54 200
    GE11-VI-L-CERN-0001    2017.08.30.15.03 300

    Please note that '#' character is understood as a comment and lines starting with 
    this character will be skipped.

    Arguments are described as:
    
    filename - physical filename of input list of scandate files
    alphaLabels - True (False): the optional third column is understood as alphanumeric (floating point)

    The return value is a tuple:
        [0] -> updated parsedListOfScanDates
        [1] -> indepVarName if present (empty string if not)
    """

    import os

    # Check input file
    try:
        fileScanDates = open(options.filename, 'r') 
    except Exception as e:
        print '%s does not seem to exist or is not readable'%(options.filename)
        print e
        exit(os.EX_NOINPUT)
        pass

    parsedListOfScanDates = []
    strIndepVar = ""
    indepVar = ""
    for i,line in enumerate(fileScanDates):
        if line[0] == "#":
            continue

        # Split the line
        line = line.strip('\n')
        analysisList = line.rsplit(delim) #chamber name, scandate, independent var

        # Get the indepVar name
        if i==0 and len(analysisList) == 3:
            if i == 0:
                strIndepVar = analysisList[2]
                continue

        cName = analysisList[0]
        scandate = analysisList[1]
        if len(analysisList) == 2:
            indepVar = scandate
        elif len(analysisList) == 3:
            if alphaLabels:
                indepVar = analysisList[2]
            else:
                try:
                    indepVar = float(analysisList[2])
                except Exception as e:
                    print("Non-numeric input given, maybe you ment to call with option 'alphaLabels=True'?")
                    print("Exiting")
                    exit(os.EX_USAGE)
        else:
            print "Input format incorrect"
            print "I was expecting a delimited file using '%s' with all lines having either 2 or 3 entries"%delim
            print "But I received:"
            print "\t%s"%(line)
            print "Exiting"
            exit(os.EX_USAGE)

        
        parsedListOfScanDates.append( (cName, scandate, indepVar) )

    return (parsedListOfScanDates,strIndepVar)

#Use Median absolute deviation (MAD) to reject outliers
#See: http://stackoverflow.com/questions/22354094/pythonic-way-of-detecting-outliers-in-one-dimensional-observation-data
#And also: http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
def rejectOutliersMAD(arrayData, thresh=3.5):    
    arrayOutliers = isOutlierMAD(arrayData, thresh)
    return arrayData[arrayOutliers != True]

#Use MAD to reject outliers, but consider only high or low tail
def rejectOutliersMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    arrayOutliers = isOutlierMADOneSided(arrayData, thresh, rejectHighTail)
    return arrayData[arrayOutliers != True]
