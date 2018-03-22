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

def getEmptyPerVFATList(n_vfat=24):
    """
    Returns a list of lists
    Each of the inner lists are empty

    There are n_vfat inner lists
    """

    return [ [] for vfat in range(0,n_vfat) ]

def getMapping(mappingFileName):
    """
    Returns a nested dictionary, the outer dictionary uses VFAT position as the has a key,
    the inner most dict has keys from the list anaInfo.py mappingNames.
    
    The inner dict stores a list whose index is ordered by ASIC channel number, accessing
    the i^th element of this list gives either the readout strip number, the readout connector
    pin number, or the vfat channel number as shown in this example:

        ret_dict[vfatN]['Strip'][asic_chan] is the strip number
        ret_dict[vfatN]['PanPin'][asic_chan] is the pin number on the readout connector
        ret_dict[vfatN]['vfatCH'][asic_chan] is the vfat channel number

    mappingFile - physical filename of file which contains the mapping information, 
                  expected format:

                        vfat/I:strip/I:channel/I:PanPin/I
                        0	0	16	63
                        0	1	20	62
                        0	2	24	61
                        ...
                        ...

                  Here these column headings are:
                        vfat - the VFAT position on the detector (e.g. vfatN)
                        strip - the anode strip on the readout board in an ieta row
                        channel - the channel on the ASIC
                        PanPin - the pin number on the panasonic connector
    """
    from gempython.utils.nesteddict import nesteddict

    from anaInfo import mappingNames
    import ROOT as r

    # Try to get the mapping data
    try:
        mapFile = open(mappingFileName, 'r')
    except IOError as e:
        print "Exception:", e
        print "Failed to open: '%s'"%mappingFileName
    else:
        listMapData = mapFile.readlines()
    finally:
        mapFile.close()

    # strip trhe end of line character
    listMapData = [x.strip('\n') for x in listMapData]

    # setup the look up table
    ret_mapDict = nesteddict()
    for vfat in range(0,24):
        for name in mappingNames:
            ret_mapDict[vfat][name] = [0] * 128

    # Set the data in the loop up table
    for idx, line in enumerate(listMapData):
        if idx == 0: 
            continue # skip the header line
        mapping = line.rsplit('\t')
        ret_mapDict[int(mapping[0])]['Strip'][int(mapping[2]) - 1] = int(mapping[1])
        ret_mapDict[int(mapping[0])]['PanPin'][int(mapping[2]) -1] = int(mapping[3])
        ret_mapDict[int(mapping[0])]['vfatCH'][int(mapping[2]) - 1] = int(mapping[2]) - 1

    return ret_mapDict

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

def saveSummary(dictSummary, dictSummaryPanPin2=None, name='Summary', trimPt=None):
    """
    Makes an image with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per VFAT.  Each will be 
                         drawn on a separate canvas
    dictSummaryPanPin2 - Optional, as dictSummary but if the independent variable is the
                         readout connector pin this is the other side of the connector
    name               - Name of output image
    trimPt             - Optional, list of trim points the dependent variable was aligned
                         to if it is the result of trimming.  One entry per VFAT
    """

    import ROOT as r

    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    if dictSummaryPanPin2 is None:
        canv = make3x8Canvas('canv', dictSummary, 'colz')
        for vfat in range(0,24):
            canv.cd(vfat+1)
            if trimPt is not None and trimLine is not None:
                trimLine = r.TLine(-0.5, trimVcal[vfat], 127.5, trimVcal[vfat])
                legend.Clear()
                legend.AddEntry(trimLine, 'trimVCal is %f'%(trimVcal[vfat]))
                legend.Draw('SAME')
                trimLine.SetLineColor(1)
                trimLine.SetLineWidth(3)
                trimLine.Draw('SAME')
                pass
            canv.Update()
            pass
        pass
    else:
        canv = r.TCanvas('canv','canv',500*8,500*3)
        canv.Divide(8,6)
        r.gStyle.SetOptStat(0)
        for ieta in range(0,8):
            for iphi in range (0,3):
                r.gStyle.SetOptStat(0)
                canv.cd((ieta+1 + iphi*16)%48 + 16)
                dictSummary[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                canv.cd((ieta+9 + iphi*16)%48 + 16)
                dictSummaryPanPin2[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                pass
            pass
        pass

    canv.SaveAs(name)

    return
