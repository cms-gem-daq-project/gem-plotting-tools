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

def first_index_gt(data_list, value):
    """
    http://code.activestate.com/recipes/578071-fast-indexing-functions-greater-than-less-than-equ/
    
    return the first index greater than value from a given list like object.
    If value is greater than all elements in the list like object, the length 
    of the list like object is returned instead
    """
    try:
        index = next(data[0] for data in enumerate(data_list) if data[1] > value)
        return index
    except StopIteration: 
        return len(data_list)

def getCyclicColor(idx):
    import ROOT as r

    colors = {
        0:r.kBlack,
        1:r.kGreen-1,
        2:r.kRed-1,
        3:r.kBlue-1,
        4:r.kGreen-2,
        5:r.kRed-2,
        6:r.kBlue-2,
        7:r.kGreen-3,
        8:r.kRed-3,
        9:r.kBlue-3,
            }

    return colors[idx % 10]

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

def make2x4Canvas(name, initialContent = None, initialDrawOpt = '', secondaryContent = None, secondaryDrawOpt = '', canv=None):
    """
    Creates a 2x4 canvas for summary plots.

    name - TName of output TCanvas
    initialContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on the canvas.
    initialDrawOpt - draw option to be used when drawing elements of initialContent
    secondaryContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on top of the canvas.
    secondaryDrawOpt - draw option to be used when drawing elements of secondaryContent
    canv - TCanvas previously produced by make3x8Canvas() or one that has been subdivided into a 3x8 grid
    """

    import ROOT as r
    
    if canv is None:
        canv = r.TCanvas(name,name,500*8,500*3)
        canv.Divide(4,2)

    if initialContent is not None:
        for ieta in range(1,9):
            canv.cd(ieta)
            initialContent[ieta].Draw(initialDrawOpt)
    if secondaryContent is not None:
        for ieta in range(1,9):
            canv.cd(ieta)
            secondaryContent[ieta].Draw("same%s"%secondaryDrawOpt)
    canv.Update()
    return canv

def make3x8Canvas(name, initialContent = None, initialDrawOpt = '', secondaryContent = None, secondaryDrawOpt = '', canv=None):
    """
    Creates a 3x8 canvas for summary plots.

    name - TName of output TCanvas
    initialContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on the canvas.
    initialDrawOpt - draw option to be used when drawing elements of initialContent
    secondaryContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on top of the canvas.
    secondaryDrawOpt - draw option to be used when drawing elements of secondaryContent
    canv - TCanvas previously produced by make3x8Canvas() or one that has been subdivided into a 3x8 grid
    """

    import ROOT as r
    from mapping.chamberInfo import chamber_vfatPos2PadIdx
    
    if canv is None:
        canv = r.TCanvas(name,name,500*8,500*3)
        canv.Divide(8,3)

    if initialContent is not None:
        for vfat in range(24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
            initialContent[vfat].Draw(initialDrawOpt)
    if secondaryContent is not None:
        for vfat in range(24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
            secondaryContent[vfat].Draw("same%s"%secondaryDrawOpt)
    canv.Update()
    return canv

def makeListOfScanDatesFile(chamberName, anaType, startDate=None, endDate=None, delim='\t', ztrim=4):
    """
    Given a starting scandate startDate and an ending scandate endDate this
    will make a text file for chamberName which is a two-column list of 
    scandates for anaType compatible with parseListOfScanDatesFile()

    chamberName - Chamber name, expected to be in chamber_config.values()
    startDate   - starting scandate in YYYY.MM.DD.hh.mm format, if None then
                  the earliest possible date is used
    endDate     - ending scandate in YYYY.MM.DD.hh.mm format, if None then
                  today is used (latest possible date)
    delim       - delimiter to use in output file name
    """

    from gempython.utils.wrappers import envCheck, runCommand
    envCheck('DATA_PATH')

    import datetime
    startDay = datetime.date(datetime.MINYEAR,1,1)
    if startDate is not None:
        startDateInfo = [ int(info) for info in startDate.split(".") ]
        startDay = datetime.date(startDateInfo[0], startDateInfo[1], startDateInfo[2])
        pass

    endDay = datetime.date.today()
    if endDate is not None:
        endDateInfo = [ int(info) for info in endDate.split(".") ]
        endDat = datetime.date(endDateInfo[0], endDateInfo[1], endDateInfo[2])
        pass

    import os
    dirPath = getDirByAnaType(anaType, chamberName, ztrim)
    listOfScanDates = os.listdir(dirPath)

    try:
        listOfScanDatesFile = open('%s/listOfScanDates.txt'%dirPath,'w+')
    except IOError as e:
        print "Exception:", e
        print "Failed to open write output file"
        print "Is the below directory writeable?"
        print ""
        print "\t%s"%dirPath
        print ""
        exit(os.EX_IOERR)
        pass
    
    listOfScanDatesFile.write('ChamberName%sscandate\n'%delim)
    for scandate in listOfScanDates:
	if "current" == scandate:
	    continue
        try:
            scandateInfo = [ int(info) for info in scandate.split('.') ]
        except ValueError as e:
            print "Skipping directory %s/%s"%(dirPath,scandate)
            continue
        thisDay = datetime.date(scandateInfo[0],scandateInfo[1],scandateInfo[2])

        if (startDay < thisDay and thisDay <= endDay):
            listOfScanDatesFile.write('%s%s%s\n'%(chamberName,delim,scandate))
            pass
        pass

    listOfScanDatesFile.close()
    runCommand( ['chmod','g+rw','%s/listOfScanDates.txt'%dirPath] )

    return

def parseCalFile(filename=None):
    """
    Gives the conversion between VCal/CFG_CAL_DAC to fC from either
    an optional external file (filename) or the hard coded vfat2 
    values.

    Returns a tuple of numpy arrays where index 0 (1) of the tuple
    corresponds to the slope (intercept) arrays.  The returned 
    arrays are indexed by VFAT position.
    
    The conversion follows via:

    fC = ret_tuple[0][vfat] * CAL_DAC + ret_tuple[1][vfat]

    The structure of filename, if supplied, is expected to be:

        vfatN/I:slope/F:intercept/F
        0   0.2692  -2.629748
        1   0.238106    -2.65316
        2   0.2532  -2.193826
        3   0.276783    -2.477547
        ...
        5   1.000000    0.000000    
        ...
        ...

    Inputing a slope (intercept) of 1.0 (0.0) will keep the numbers
    in DAC units
    """

    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    import ROOT as r

    # Set the CAL DAC to fC conversion
    calDAC2Q_b = np.zeros(24)
    calDAC2Q_m = np.zeros(24)
    if filename is not None:
        list_bNames = ["vfatN","slope","intercept"]
        calTree = r.TTree('calTree','Tree holding VFAT Calibration Info')
        calTree.ReadFile(filename)
        array_CalData = rp.tree2array(tree=calTree, branches=list_bNames)
    
        for dataPt in array_CalData:
            calDAC2Q_b[dataPt['vfatN']] = dataPt['intercept']
            calDAC2Q_m[dataPt['vfatN']] = dataPt['slope']
            pass
    else:
        calDAC2Q_b = -0.8 * np.ones(24)
        calDAC2Q_m = 0.05 * np.ones(24)
        pass

    return (calDAC2Q_m, calDAC2Q_b)

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
        fileScanDates = open(filename, 'r') 
    except Exception as e:
        print '%s does not seem to exist or is not readable'%(filename)
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

        # Get the indepVar name if it is present, 
        # Always skip the first line
        if i==0:
            if len(analysisList) == 3:
                strIndepVar = analysisList[2]
            elif len(analysisList) == 2:
                strIndepVar = analysisList[1]
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
            pass
        
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

def saveSummary(dictSummary, dictSummaryPanPin2=None, name='Summary', trimPt=None, drawOpt="colz"):
    """
    Makes an image with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per VFAT.  Each will be 
                         drawn on a separate pad
    dictSummaryPanPin2 - Optional, as dictSummary but if the independent variable is the
                         readout connector pin this is the other side of the connector
    name               - Name of output image
    trimPt             - Optional, list of trim points the dependent variable was aligned
                         to if it is the result of trimming.  One entry per VFAT
    drawOpt            - Draw option
    """

    import ROOT as r
    from mapping.chamberInfo import chamber_vfatPos2PadIdx

    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    if dictSummaryPanPin2 is None:
        canv = make3x8Canvas('canv', dictSummary, drawOpt)
        for vfat in range(0,24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
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
                dictSummary[ieta+(8*iphi)].Draw(drawOpt)
                canv.Update()
                canv.cd((ieta+9 + iphi*16)%48 + 16)
                dictSummaryPanPin2[ieta+(8*iphi)].Draw(drawOpt)
                canv.Update()
                pass
            pass
        pass

    canv.SaveAs(name)

    return

def saveSummaryByiEta(dictSummary, name='Summary', trimPt=None, drawOpt="colz"):
    """
    Makes an image with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per ieta.  Each will be 
                         drawn on a separate pad
    name               - Name of output image
    trimPt             - Optional, list of trim points the dependent variable was aligned
                         to if it is the result of trimming.  One entry per VFAT
    drawOpt            - Draw option
    """

    import ROOT as r

    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    canv = make2x4Canvas(name='canv', initialContent=dictSummary, initialDrawOpt=drawOpt)
    for ieta in range(0,8):
        canv.cd(ieta+1)
        if trimPt is not None and trimLine is not None:
            trimLine = r.TLine(-0.5, trimVcal[ieta], 127.5, trimVcal[ieta])
            legend.Clear()
            legend.AddEntry(trimLine, 'trimVCal is %f'%(trimVcal[vfat]))
            legend.Draw('SAME')
            trimLine.SetLineColor(1)
            trimLine.SetLineWidth(3)
            trimLine.Draw('SAME')
            pass
        canv.Update()
        pass

    canv.SaveAs(name)

    return
