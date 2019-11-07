r"""
``anautilities`` --- Various other utilities
============================================

.. code-block:: python

    import gempython.gemplotting.utils.anautilities

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for gem-plotting-tools scripts/macros and vfatqc scans

Documentation
-------------
"""

from gempython.utils.gemlogger import printYellow, printRed

def cleanup(listOfFilePaths,listOfFileObjects=None,listOfTFiles=None,perm="g+rw"):
    """
    Typically used inside the 'finally' block of a try...except statement.
    For each element of listOfFilePaths this will recursively set permissions 'perm'.
    For each element of listOfFileObjects this will call file::close()
    For each element of listOfTFiles this will call TFile::Close()
    """

    from gempython.utils.wrappers import runCommand
    for element in listOfFilePaths:
        runCommand(["chmod", "-R", perm, element])
        pass

    if listOfFileObjects is not None:
        for element in listOfFileObjects:
            element.close()
            pass
        pass

    if listOfTFiles is not None:
        for element in listOfTFiles:
            element.Close()
            pass
        pass

    return

def dacAnalysis(args, dacScanTree, chamber_config, scandate='noscandate'):
    """
    Analyzes DAC scan data to determine nominal bias current/voltage settings for a particular VFAT3 DAC.
    Returns a dictionary where:

        dict_dacVals[dacName][ohKey][vfat] = value

    Where ohKey is a tuple of (shelf,slot,link) providing the mapping for uTCA shelf -> slot -> link mapping

    Will raise a ValueError if one or more DAC's are found to need a DAC value that places the DAC out of its
    range to hit the correct bias voltage/current required.

    Here dacName are the values stored in the "nameX" TBranch of the input TTree.

        dacScanTree - Instance of gemDacCalTreeStructure.  Note the "nameY" TBranch must be either "ADC0" or "ADC1"
        chamber_config - chamber_config dictionary
        scandate - Either a string 'noscandate' or an a datetime object formated as YYYY.MM.DD.hh.mm, e.g
                   returned from "datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")"
    """

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    print("Loading info from input TTree")

    import root_numpy as rp
    import numpy as np

    list_bNames = ['dacValY','link','nameX','shelf','slot','vfatID','vfatN','detName']

    #for backwards compatibility, handle input trees that do not have a detName branch by finding the detName using the chamber_config
    if not 'detName' in dacScanTree.GetListOfBranches():    
        list_bNames.remove('detName')

    def getDetName(entry):
        if "detName" in np.dtype(entry).names:
            return entry['detName'][0]
	else:
            return chamber_config[(entry['shelf'],entry['slot'],entry['link'])]

    vfatArray = rp.tree2array(tree=dacScanTree,branches=list_bNames)
    dacNameArray = np.unique(vfatArray['nameX'])

    # Get VFATID's
    vfatIDArray = getSubArray(vfatArray, ['vfatID','vfatN'])
    vfatIDArray = np.sort(vfatIDArray,order='vfatN')['vfatID'] # index now gauranteed to match vfatN

    # make the crateMap
    list_bNames.remove('dacValY')
    list_bNames.remove('nameX')
    list_bNames.remove('vfatID')
    list_bNames.remove('vfatN')
    crateMap = np.unique(rp.tree2array(tree=dacScanTree,branches=list_bNames))

    ### FIXME
    def getGemType(entry):
        detName = getDetName(entry)
        return detName[:detName.find('-')].lower()
    gemType = getGemType(crateMap[0])
    ### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    
    # get nonzero VFATs
    dict_nonzeroVFATs = {}
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        arrayMask = np.logical_and(vfatArray['dacValY'] > 0, vfatArray['link'] == entry['link'])
        arrayMask = np.logical_and(arrayMask, vfatArray['slot'] == entry['slot'])
        arrayMask = np.logical_and(arrayMask, vfatArray['shelf'] == entry['shelf'])
        dict_nonzeroVFATs[ohKey] = np.unique(vfatArray[arrayMask]['vfatN'])

    dataPath = getDataPath()
    elogPath = getElogPath()

    from gempython.utils.wrappers import runCommand
    for entry in crateMap:
        detName = getDetName(entry)
        if scandate == 'noscandate':
            runCommand(["mkdir", "-p", "{0}/{1}".format(elogPath,detName)])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(elogPath,detName)])
        else:
            runCommand(["mkdir", "-p", "{0}/{1}/dacScans/{2}".format(dataPath,detName,scandate)])
            runCommand(["chmod", "g+rw", "{0}/{1}/dacScans/{2}".format(dataPath,detName,scandate)])
            if scandate != "current":
                runCommand(["unlink", "{0}/{1}/dacScans/current".format(dataPath,detName)])
                runCommand(["ln","-s","{0}/{1}/dacScans/{2}".format(dataPath,detName,scandate),"{0}/{1}/dacScans/current".format(dataPath,detName)])
            pass

    # Determine which DAC was scanned and against which ADC
    adcName = ""
    for event in dacScanTree:
        adcName = str(event.nameY.data())
        break # all entries will be the same

    from gempython.utils.gemlogger import colormsg
    import logging
    if adcName not in ['ADC0', 'ADC1']:
        raise ValueError(colormsg("Error: unexpected value of adcName: '{0}'".format(adcName),logging.ERROR), os.EX_DATAERR)

    from gempython.gemplotting.utils.anaInfo import nominalDacValues, nominalDacScalingFactors
    nominal = {}
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        if dacName not in nominalDacValues.keys():
            raise ValueError(colormsg("Error: unexpected DAC Name: '{}'".format(dacName),logging.ERROR), os.EX_DATAERR)
        else:
            nominal[dacName] = nominalDacValues[dacName][0]

            #convert all voltages to mV and currents to uA
            if nominalDacValues[dacName][1] == "V":
                nominal[dacName] *= pow(10.0,3)
            elif nominalDacValues[dacName][1] == 'mV':
                pass
            elif nominalDacValues[dacName][1] == 'uV':
                nominal[dacName] *= pow(10.0,-3)
            elif nominalDacValues[dacName][1] == 'nV':
                nominal[dacName] *= pow(10.0,-6)
            elif nominalDacValues[dacName][1] == "A":
                nominal[dacName] *= pow(10.0,6)
            elif nominalDacValues[dacName][1] == 'mA':
                nominal[dacName] *= pow(10.0,3)
            elif nominalDacValues[dacName][1] == 'uA':
                pass
            elif nominalDacValues[dacName][1] == 'nA':
                nominal[dacName] *= pow(10.0,-3)
            else:
                # Maybe a TypeError is more appropriate...?
                raise ValueError(colormsg("Error: unexpected units: '{0}'".format(nominalDacValues[dacName][1]),logging.ERROR), os.EX_DATAERR)

    #the nominal reference current is 10 uA and it has a scaling factor of 0.5
    nominal_iref = 10*0.5

    calInfo = {}
    if args.calFileList != None:
        for line in open(args.calFileList):
            if line[0] == "#":
                continue
            dataEntry = (line.strip()).split()
            shelf   = dataEntry[0]
            slot    = dataEntry[1]
            link    = dataEntry[2]
            calFile = dataEntry[3]
            ohKey = (int(shelf),int(slot),int(link))
            tuple_calInfo = parseCalFile(calFile, gemType=gemType)
            calInfo[ohKey] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}

    #for each OH, check if calibration files were provided, if not search for the calFile in the $DATA_PATH, if it is not there, then skip that OH for the rest of the script
    import os
    for idx,entry in enumerate(crateMap):
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        detName = getDetName(entry)
        if ohKey not in calInfo.keys():
            calAdcCalFile = "{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,detName,adcName)
            calAdcCalFileExists = os.path.isfile(calAdcCalFile)
            if calAdcCalFileExists:
                tuple_calInfo = parseCalFile(calAdcCalFile, gemType=gemType)
                calInfo[ohKey] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}
            else:
                # FIXME should perform a DB query with chipID's in input dacScanTree to get calibration constants
                print("Skipping Shelf{0}, Slot{1}, OH{2}, detector {3}, missing {4} calibration file:\n\t{5}".format(
                    ohKey[0],
                    ohKey[1],
                    ohKey[2],
                    detName,
                    adcName,
                    calAdcCalFile))
                crateMap = np.delete(crateMap,(idx))

    if len(crateMap) == 0:
        raise RuntimeError(colormsg('No OHs with a calFile, exiting.',logging.ERROR),os.EX_DATAERR)

    # Initialize nested dictionaries
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_DACvsADC_Graphs = ndict()
    dict_RawADCvsDAC_Graphs = ndict()
    dict_DACvsADC_Funcs = ndict()

    print("Initializing TObjects")

    # Initialize a TGraphErrors and a TF1 for each vfat
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for vfat in range(0,nVFATS):
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat] = r.TGraphErrors()
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(dacName)
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetYaxis().SetTitle(adcName)
                dict_DACvsADC_Graphs[dacName][ohKey][vfat] = r.TGraphErrors()
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetTitle("VFAT{}".format(vfat))
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetMarkerSize(5)
                #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetYaxis().SetTitle(dacName)
                if nominalDacValues[dacName][1][len(nominalDacValues[dacName][1])-1] == 'A':
                    dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(adcName + " (#muA)")
                else:
                    dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(adcName + " (mV)")
                #we will use a fifth degree polynomial to do the fit
                dict_DACvsADC_Funcs[dacName][ohKey][vfat] = r.TF1("DAC Scan Function","[0]*x^5+[1]*x^4+[2]*x^3+[3]*x^2+[4]*x+[5]")
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineWidth(1)
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineStyle(3)

    outputFiles = {}
    for entry in crateMap:
        detName = getDetName(entry)
        if scandate == 'noscandate':
            outputFiles[ohKey] = r.TFile(elogPath+"/"+detName+"/"+args.outfilename,'recreate')
        else:    
            outputFiles[ohKey] = r.TFile(dataPath+"/"+detName+"/dacScans/"+scandate+"/"+args.outfilename,'recreate')

    print("Looping over stored events in dacScanTree")

    # Loop over events in the tree and fill plots
    for event in dacScanTree:
        ohKey = (event.shelf,event.slot,event.link)
        vfat = event.vfatN

        if vfat not in dict_nonzeroVFATs[ohKey]:
            continue

        #the output of the calibration is mV
        calibrated_ADC_value=calInfo[ohKey]['slope'][vfat]*event.dacValY+calInfo[ohKey]['intercept'][vfat]
        calibrated_ADC_error=calInfo[ohKey]['slope'][vfat]*event.dacValY_Err

        #Get the DAC Name in question
        dacName = str(event.nameX.data())

        #Use Ohm's law to convert the currents to voltages. The VFAT3 team told us that a 20 kOhm resistor was used.
        if nominalDacValues[dacName][1][len(nominalDacValues[dacName][1])-1] == "A":

            #V (mV) = I (uA) R (kOhm)
            #V (10^-3) = I (10^-6) R (10^3)
            calibrated_ADC_value = calibrated_ADC_value/20.0
            calibrated_ADC_error = calibrated_ADC_error/20.0

            if dacName != 'CFG_IREF':
                calibrated_ADC_value -= nominal_iref

            calibrated_ADC_value /= nominalDacScalingFactors[dacName]
            calibrated_ADC_error /= nominalDacScalingFactors[dacName]
                
        #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
        #the dacName variable is the DAC register that is scanned, and we want to determine its nominal value
        if args.assignXErrors:
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN()-1,calibrated_ADC_error,event.dacValX_Err)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN()-1,event.dacValX_Err,0)
        else:
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN()-1,calibrated_ADC_error,0)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN()-1,0,0)

    print("fitting DAC vs. ADC distributions")

    # Fit the TGraphErrors objects
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for vfat in range(0,nVFATS):
                if vfat not in dict_nonzeroVFATs[ohKey]:
                    #so that the output plots for these VFATs are completely empty
                    dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineColor(0)
                    continue
                #the fits fail when the errors on dacValY (the x-axis variable) are used
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].Fit(dict_DACvsADC_Funcs[dacName][ohKey][vfat],"QEX0")

    # Create Determine max DAC size
    dict_maxByDacName = {}
    from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
    for dacSelect,dacInfo in maxVfat3DACSize.iteritems():
        dict_maxByDacName[dacInfo[1]]=dacInfo[0]

    print("Determining nominal values for bias voltage and/or current settings")

    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = ndict()
    dict_dacVals = ndict()
    dictOfDACsWithBadBias = {} # [(shelf,slot,link,vfat)] = (vfatID,dacName)
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        maxDacValue = dict_maxByDacName[dacName]

        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            getDame = getDetName(entry)
            graph_dacVals[dacName][ohKey] = r.TGraph()
            graph_dacVals[dacName][ohKey].SetMinimum(0)
            graph_dacVals[dacName][ohKey].GetXaxis().SetTitle("VFATN")
            graph_dacVals[dacName][ohKey].GetYaxis().SetTitle("nominal {} value".format(dacName))

            for vfat in range(0,nVFATS):
                if vfat not in dict_nonzeroVFATs[ohKey]:
                    continue

                #evaluate the fitted function at the nominal current or voltage value and convert to an integer
                fittedDacValue = int(dict_DACvsADC_Funcs[dacName][ohKey][vfat].Eval(nominal[dacName]))
                finalDacValue = max(0,min(maxDacValue,fittedDacValue))

                if fittedDacValue != finalDacValue:
                    dictOfDACsWithBadBias[(ohKey[0],ohKey[1],ohKey[2],vfat)] = (vfatIDArray[vfat],dacName)
                    errorMsg = "Warning: when fitting VFAT{5} of chamber {6} (Shelf{7},Slot{8},OH{4}) DAC {0} the fitted value, {1}, is outside range the register can hold: [0,{2}]. It will be replaced by {3}.".format(
                            dacName,
                            fittedDacValue,
                            maxDacValue,
                            finalDacValue,
                            ohKey[2],
                            vfat,
                            detName, 
                            ohKey[0],
                            ohKey[1])
                    print(colormsg(errorMsg,logging.ERROR))

                dict_dacVals[dacName][ohKey][vfat] = finalDacValue
                graph_dacVals[dacName][ohKey].SetPoint(graph_dacVals[dacName][ohKey].GetN(),vfat,dict_dacVals[dacName][ohKey][vfat])

    print("Writing output data")

    # Write out the dacVal results to a root file, a text file, and the terminal
    outputTxtFiles_dacVals = ndict()
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            detName = getDetName(entry)
            if scandate == 'noscandate':
                outputTxtFiles_dacVals[dacName][ohKey] = open("{0}/{1}/NominalValues-{2}.txt".format(elogPath,detName,dacName),'w')
            else:
                outputTxtFiles_dacVals[dacName][ohKey] = open("{0}/{1}/dacScans/{2}/NominalValues-{3}.txt".format(dataPath,detName,scandate,dacName),'w')

    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        detName = getDetName(entry)
        # Per VFAT Poosition
        for vfat in range(0,nVFATS):
            thisVFATDir = outputFiles[ohKey].mkdir("VFAT{0}".format(vfat))

            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                thisDACDir = thisVFATDir.mkdir(dacName)
                thisDACDir.cd()

                dict_DACvsADC_Graphs[dacName][ohKey][vfat].Write("g_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].Write("func_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].Write("g_VFAT{0}_RawADCvsDAC_{1}".format(vfat,dacName))

                if vfat in dict_nonzeroVFATs[ohKey]:
                    outputTxtFiles_dacVals[dacName][ohKey].write("{0}\t{1}\n".format(vfat,dict_dacVals[dacName][ohKey][vfat]))

        # Summary Case
        dirSummary = outputFiles[ohKey].mkdir("Summary")
        dirSummary.cd()
        for idx in range(len(dacNameArray)):
            dacName = np.asscalar(dacNameArray[idx])

            # Store summary graph
            graph_dacVals[dacName][ohKey].Write("g_NominalvsVFATPos_{0}".format(dacName))

            # Store summary grid canvas and print images
            canv_Summary = getSummaryCanvas(dict_DACvsADC_Graphs[dacName][ohKey], name="canv_Summary_{0}".format(dacName), drawOpt='APE1', gemType=gemType)
            canv_Summary = addPlotToCanvas(canv_Summary, dict_DACvsADC_Funcs[dacName][ohKey], gemType=gemType)
            if scandate == 'noscandate':
                canv_Summary.SaveAs("{0}/{1}/Summary_{1}_DACScan_{2}.png".format(elogPath,detName,dacName))
            else:
                canv_Summary.SaveAs("{0}/{1}/dacScans/{2}/Summary{1}_DACScan_{3}.png".format(dataPath,detName,scandate,dacName))

    # Print Summary
    if args.printSum:
        print("| detName | shelf | slot | ohN | vfatN | dacName | Value |")
        print("| :-----: | :---: | :--: | :-: | :---: | :-----: | :---: |")
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            detName = getDetName(entry)
            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                for vfat in range(0,nVFATS):
                    if vfat not in dict_nonzeroVFATs[ohKey]:
                        continue

                    print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
                        detName,
                        ohKey[0],
                        ohKey[1],
                        ohKey[2],
                        vfat,
                        dacName,
                        dict_dacVals[dacName][ohKey][vfat])
                    )
                    pass
                pass
            pass
        pass

    # Raise a ValueError if a DAC is found to be out of range
    if len(dictOfDACsWithBadBias):
        err_msg = "The following (vfatN,DAC Names) where found to be out of range"
        for ohKey,vfatDACtuple in dictOfDACsWithBadBias.iteritems():
            err_msg = "{0}\n\t{1}\t{2}".format(err_msg,ohKey,vfatDACtuple)
            pass
        from gempython.gemplotting.utils.exceptions import VFATDACBiasCannotBeReached
        raise VFATDACBiasCannotBeReached(err_msg, os.EX_DATAERR)

    return dict_dacVals

def filePathExists(searchPath, subPath=None, debug=False):
    import os
    
    testPath = searchPath
    if subPath is not None:
        testPath = "{0}/{1}".format(searchPath, subPath)

    if not os.path.exists(testPath):
        if debug:
            print("Unable to find location: {0}".format(testPath))
        return False
    else:
        if debug:
            print("Found {0}".format(testPath))
        return True

# Find Inflection Point /////////////////////////////////////////////////////////////////
#----------------------------------------------------------------------------------------

def findInflectionPts(graph):
    '''
    Find and return the "knee", inflection point, of the SBit Rate scan
    graph should be a TGraph or TH1F of the SBit Rate scan for 1 vfat 
    '''


    import ROOT as root
    import numpy as np
    from itertools import groupby

    # Allow for yellow and red warning colors
    from gempython.utils.gemlogger import printYellow, printRed

    # make TH1F into TGraph
    if type(graph) == root.TH1F :
        graph = root.TGraph(graph)

    # make arrays out of the x and y components
    x = graph.GetX()
    y = graph.GetY()
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if len(x) == 0 or len(y) == 0:
        printRed("No data points were passed to the inflection point finder")
        printRed("This could be due to missing VFATs on the detector, please make sure you expect this")
        printRed("Returning None")
        return (np.array([None]), np.array([None]) ) 

    # Calculate the gradient of y as a function of x
    # Documentation here: https://docs.scipy.org/doc/numpy/reference/generated/numpy.gradient.html
    grad = np.gradient(y, x)

    # Split the array when the slope changes sign and store the partitions of gradients
    posGrad = [list(g) for k, g in groupby(grad, lambda x: x > 0) if k]
    negGrad = [list(g) for k, g in groupby(grad, lambda x: x < 0) if k]
   
    # Sum the split arrays and find the most negative sum
    negSum = []
    bigNegSum = 0
    bigIdx = 0
    for iNegArr in range(0, len(negGrad) ) :
        tmpNegSum = sum(negGrad[iNegArr] )
        negSum.append(tmpNegSum)
        if tmpNegSum < bigNegSum :
            bigNegSum = tmpNegSum
            bigIdx =  iNegArr

    # Get the inflection point
    # We are defining the inflection point as the point where the most negative gradient sum begins
    try:
        inflxGrad = negGrad[bigIdx][0]
        inflxIdx = np.where(grad == inflxGrad) #return the index at the specified value
        inflxPnt = (x[inflxIdx], y[inflxIdx] )
    # Error handling for problematic VFATs
    except IndexError:
        if bigIdx == 0:
            printYellow("Warning: No values with negative slope, so no inflection point! Assigning 0")
            inflxPnt = (np.array([0.0], dtype=float), np.array([0.0], dtype=float) )
        else:
            printYellow("Warning: There is no negative gradient value at the index (bigIdx) value {:f}, Assigning 0".format(bigIdx) )
            inflxPnt = (np.array([0.0], dtype=float), np.array([0.0], dtype=float) )
    except ValueError:
        printYellow("Warning: the inflection point gradient (inflxGrad) value {:f} was not found in the gradient list. Assigning 0".format(inflxGrad) )
        inflxPnt = (np.array([0.0], dtype=float), np.array([0.0], dtype=float) )
    except NameError:
        printYellow("Warning: The inflection point was not found (unqualified name). Assigning 0")
        inflxPnt = (np.array([0.0], dtype=float), np.array([0.0], dtype=float) )

    return inflxPnt

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

def formatSciNotation(value, digits=2):
    """
    Returns a string formated in scientific notation with a number of digits to the
    right of the decimal place equal to the digits value
    """
    from decimal import Decimal

    sciNotation = '%.{0}E'.format(digits)

    return sciNotation % Decimal(value)

def get2DMapOfDetector(vfatChanLUT, obsData, mapName, zLabel, gemType="ge11"):
    """
    Generates a 2D map of the detector as a TH2D. Y-axis will be ieta. X-axis will be ROBstr (strip),
    vfat channel or panasonic pin number.  The z-axis will be the elements of obsData with label zLabel

    vfatChanLUT - Nested dictionary specifying the VFAT channel to strip and PanPin mapping;
                  see getMapping() for details on expected format
    obsData     - Numpy array w/3072 entries storing, index goes as [vfat*128+chan]
    mapName     - Type of map to be produced, will be the x-axis.  See mappingNames of anaInfo
                  for possible options
    zLabel      - Label of the z-axis
    """

    from anaInfo import mappingNames
    import os

    if mapName not in mappingNames:
        print("get2DMapOfDetector(): mapName {0} not recognized".format(mapName))
        print("\tAvailable options are:")
        print("\t",mappingNames)
        raise LookupError

    import ROOT as r
    from ..mapping.chamberInfo import chamber_maxiEtaiPhiPair
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
    maxiEta, maxiPhi = chamber_maxiEtaiPhiPair[gemType]
    
    hRetMap = r.TH2F("ieta_vs_{0}_{1}".format(mapName,zLabel),"",maxiPhi*maxChans, -0.5, maxiPhi*maxChans-0.5, maxiEta, 0.5, maxiEta + 0.5)
    hRetMap.SetXTitle(mapName)
    hRetMap.SetYTitle("i#eta")
    hRetMap.SetZTitle(zLabel)

    from gempython.gemplotting.mapping.chamberInfo import chamber_vfatPos2iEtaiPhi
    from gempython.tools.hw_constants import vfatsPerGemVariant
    for idx in range(maxChans*vfatsPerGemVariant[gemType]):
        # Determine vfat, ieta, and iphi
        vfat = idx // maxChans
        ieta = chamber_vfatPos2iEtaiPhi[gemType][vfat][0]
        iphi = chamber_vfatPos2iEtaiPhi[gemType][vfat][1]

        # Determine strip, panasonic pin, or channel
        chan = idx % maxChans
        stripPinOrChan = vfatChanLUT[vfat][mapName][chan]

        # Set Bin Content of Histogrma
        hRetMap.SetBinContent(((iphi-1)*maxChans+stripPinOrChan)+1, ieta, obsData[idx])
        pass

    return hRetMap

def getChamberNameFromFilename(filename, returnType=False):
    """
    Determines ChamberName from filename

    If returnType is False this function returns a string 
    specifying the ChamberName. If the ChamberName cannot 
    be determined from the input filename None is returned

    If returnType is True this function will return a tuple
    where the first element is a string specifying the 
    ChamberName and the second element will be the gemType.
    Here gemType is the key from the gemVariants dictionary
    from gempython.tools.hw_constants that was found in
    the ChamberName, e.g. returned tuple is:

        (ChamberName, gemType)

    filename - string delimited by "/" characters; expected to have a Detector Name in the path somewhere
    """
    if not (len(filename.split("/")) > 1):
        raise RuntimeError("Could Not Determine Detector Name from Input Filename: {0}".format(filename))

    dataPath = getDataPath()
    
    import copy
    tmpName = copy.deepcopy(filename)
    tmpName = tmpName.replace(dataPath,"")

    from gempython.tools.hw_constants import gemVariants
    cName = None
    thisType = None
    for el in tmpName.split("/"):
        for gemType in gemVariants.keys():
            if gemType in el.lower():
                cName = el
                thisType = gemType
                break
            pass
        if cName is not None:
            break
        pass

    if returnType:
        return (cName, thisType)
    else:
        return cName

def getCyclicColor(idx):
    return 30+4*idx

def getDataPath():
    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")

    import os
    return os.getenv("DATA_PATH")

def getDirByAnaType(anaType, cName, ztrim=4):
    from anaInfo import ana_config
    
    import os

    # Check anaType is understood
    if anaType not in ana_config.keys():
        print("getDirByAnaType() - Invalid analysis specificed, please select only from the list:")
        print(ana_config.keys())
        exit(os.EX_USAGE)
        pass

    # Check Paths
    dataPath = getDataPath()

    dirPath = ""
    if anaType == "armDacCal":
        dirPath = "{0}/{1}/{2}".format(dataPath,cName,anaType)
    elif anaType == "dacScanV3":
        dirPath = "{0}/{1}".format(dataPath,anaType)
    elif anaType == "latency":
        dirPath = "{0}/{1}/{2}/trk/".format(dataPath,cName,anaType)
    elif anaType == "sbitMonInt":
        dirPath = "{0}/{1}/sbitMonitor/intTrig/".format(dataPath,cName)
    elif anaType == "sbitMonRO":
        dirPath = "{0}/{1}/sbitMonitor/readout/".format(dataPath,cName)
    elif anaType == "sbitRatech":
        if cName is None:
            dirPath = "{0}/sbitRate/perchannel".format(dataPath)
        else:
            dirPath = "{0}/{1}/sbitRate/perchannel/".format(dataPath,cName)
    elif anaType == "sbitRateor":
        if cName is None:
            dirPath = "{0}/sbitRate/channelOR".format(dataPath)
        else:
            dirPath = "{0}/{1}/sbitRate/channelOR/".format(dataPath,cName)
    elif anaType == "scurve":
        dirPath = "{0}/{1}/{2}/".format(dataPath,cName,anaType)
    elif anaType == "temperature":
        dirPath = "{0}/{1}".format(dataPath,anaType)
    elif anaType == "thresholdch":
        dirPath = "{0}/{1}/threshold/channel/".format(dataPath,cName)
    elif anaType == "thresholdvftrig":
        dirPath = "{0}/{1}/threshold/vfat/trig/".format(dataPath,cName)
    elif anaType == "thresholdvftrk":
        dirPath = "{0}/{1}/threshold/vfat/trk/".format(dataPath,cName)
    elif anaType == "trim":
        dirPath = "{0}/{1}/{2}/z{3}/".format(dataPath,cName,anaType,ztrim)
    elif anaType == "trimV3":
        dirPath = "{0}/{1}/trim/".format(dataPath,cName)
    elif anaType == "iterTrim":
        dirPath = "{0}/{1}/itertrim/".format(dataPath,cName)

    return dirPath

def getElogPath():
    from gempython.utils.wrappers import envCheck
    envCheck("ELOG_PATH")

    import os
    return os.getenv("ELOG_PATH")

def getEmptyPerVFATList(n_vfat=24):
    """
    Returns a list of lists
    Each of the inner lists are empty

    There are n_vfat inner lists
    """

    return [ [] for vfat in range(0,n_vfat) ]

def getGEBTypeFromFilename(filename, cName=None):
    """
    Determines GEBtype from filename

    Returns a string specifying the GEB type.
    If the GEB type cannot be determined from the input
    filename returns None
    """
    if not (len(filename.split("/")) > 1):
        raise RuntimeError("Could Not Determine Detector/GEB Type from Input Filename: {0}".format(filename))

    from gempython.tools.hw_constants import gemVariants
    if cName is None:
        infoTuple = getChamberNameFromFilename(filename,True)
        cName = infoTuple[0]
        thisType = infoTuple[1]
    else:
        for gemType in gemVariants.keys():
            if gemType in cName.lower():
                thisType = gemType
                break
    
    if cName is not None:
        for identifier in cName.split("-"):
            for detType in gemVariants[thisType]:
                if identifier.lower() in detType:
                    return detType
    else:
        return None

def getMapping(mappingFileName, isVFAT2=True, gemType="ge11"):
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
    from ...utils.nesteddict import nesteddict
    
    from anaInfo import mappingNames
    import ROOT as r
    
    from gempython.tools.hw_constants import vfatsPerGemVariant
    
    # Try to get the mapping data
    try:
        mapFile = open(mappingFileName, 'r')
    except IOError as e:
        print("Exception:", e)
        print("Failed to open: '{0}'".format(mappingFileName))
    else:
        listMapData = mapFile.readlines()
    finally:
        mapFile.close()

    # strip trhe end of line character
    listMapData = [x.strip('\n') for x in listMapData]

        # setup the look up table
    ret_mapDict = nesteddict()
    for vfat in range(0,vfatsPerGemVariant[gemType]):
        for name in mappingNames:
            ret_mapDict[vfat][name] = [0] * 128

    # Set the data in the loop up table
    for idx, line in enumerate(listMapData):
        if idx == 0: 
            continue # skip the header line
        mapping = line.rsplit('\t')
        if isVFAT2: 
            ret_mapDict[int(mapping[0])]['Strip'][int(mapping[2]) - 1] = int(mapping[1])
            ret_mapDict[int(mapping[0])]['PanPin'][int(mapping[2]) -1] = int(mapping[3])
            ret_mapDict[int(mapping[0])]['vfatCH'][int(mapping[2]) - 1] = int(mapping[2]) - 1
        else: #EDMS document numbers VFAT3 channels from [0,127]
            ret_mapDict[int(mapping[0])]['Strip'][int(mapping[2])] = int(mapping[1])
            ret_mapDict[int(mapping[0])]['PanPin'][int(mapping[2])] = int(mapping[3])
            ret_mapDict[int(mapping[0])]['vfatCH'][int(mapping[2])] = int(mapping[2])

    return ret_mapDict

def getNumCores2Use(args):
    """
    Determines the number of cpu cores to use for parallel processing

    args - object returned by argparse.ArgumentParser.parse_args() 

    args is expected to have the following boolean attributes:
    
        light - 25% of cores will be used; rounded down
        medium - 50% of cores will be used; rounded down
        heavy - 75% of cores will be used; rounded down
    """
    from multiprocessing import cpu_count
    try:
        availableCores = cpu_count() # Docs say this may raise following exception: see https://docs.python.org/2/library/multiprocessing.html#miscellaneous
    except NotImplementedError as err:
        from gempython.utils.wrappers import runCommandWithOutput
        availableCores = int(runCommandWithOutput('nproc').strip('\n'))

    # Don't bother catching the AttributeError that would be raised if args doesn't have these
    if args.light:
        usageFactor = 0.25
    elif args.medium:
        usageFactor = 0.5
    elif args.heavy:
        usageFactor = 0.75
    else:
        raise Runtime("getNumCores2Use() - at least one of the usage {'light','medium','heavy'} options must be True")

    if availableCores < 4:
        printYellow("Your machine is a dinosaur and only has {0} core; we will only use 1 Core.  Analysis might take awhile...".format(availableCores))
        return 1

    return int(usageFactor*availableCores)

def getPhaseScanPlots(phaseScanFile,phaseSetPtsFile,identifier=None,ohMask=0xfff,savePlots=True, gemType="ge11"): 
    """
    Plots GBT phase scan data as a TH2F and the GBT phase set points as a TGraph for
    each optohybrid found in the two input files.  Note it's assume that if OHX is in
    one input file it's in the other.

    Returns a tuple of dictionaries, the first element of the tuple is a dictionary
    of TH2F objects with the phase scan data plotted; the second element of the tuple
    is a dictionary of TGraph objects with the phase set points plotted.  Each of the
    dictionaries uses ohN as the key value.

    phaseScanFile   - file storing phase scan results, expected format to be what is 
                      defined in xhal.reg_interface_gem.core.gbt_utils_extended function
                      saveGBTPhaseScanResults
    phaseSetPtsFile - file storing phase set points determined by testConnectivity.py
    identifier      - String that will be inserted to all TObject Names, e.g. 'shelf02'
    ohMask          - Optohybrids to consider, 12 bit number, a 1 in the N^th bit means
                      plot this optohybrid
    savePlots       - If true this will make a 4x3 grid plot showing the phase scan results
                      and it will be stored under $ELOG_PATH
    """
    import numpy as np
    import ROOT as r

    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    # Create 2D plot showing phase scan results
    # =========================================
    # Load input data
    arrayType = { 
            'names':('ohN','vfatN','phase','nRepetitions','nSuccesses'), 
            'formats':('i4','i4','i4','i4','i4') 
            }
    
    from gempython.utils.gemlogger import printRed
    import os
    try:
        phaseScanArray = np.loadtxt(phaseScanFile, dtype=arrayType, skiprows=1)
    except IOError:
        printRed("An exception has occurred\nProbably file:\n\t{0}\t\nDoes not exist or is not readable.".format(phaseScanFile))
        exit(os.EX_IOERR)

    # Strip all rows not found in ohMask
    phaseScanArray = np.where( 
            (ohMask >> phaseScanArray['ohN']) & 0x1,
            phaseScanArray, 
            np.array([(-1,-1,-1,-1,-1)],dtype=arrayType) 
            )
    index2Remove = np.where(phaseScanArray['ohN'] == -1)
    phaseScanArray = np.delete(phaseScanArray,index2Remove)

    # Make distributions
    dict_phaseScanDists = {}
    for ohN in range(12):
        # Skip masked OH's
        if( not ((ohMask >> ohN) & 0x1)):
            continue

        if identifier is not None:
            name = "h2D_phaseScan_{0}_OH{1}".format(identifier,ohN)
        else:
            name = "h2D_phaseScan_OH{0}".format(ohN)
            pass

        dict_phaseScanDists[ohN] = r.TH2D(name,"", nVFATS, -0.5, nVFATS-0.5, 16,-0.5,15.5)
        dict_phaseScanDists[ohN].SetNdivisions(512,"X")
        dict_phaseScanDists[ohN].GetXaxis().SetTitle("VFAT Position")
        dict_phaseScanDists[ohN].GetYaxis().SetTitle("GBT Phase")
        pass

    # Fill distribution
    for row in phaseScanArray:
        dict_phaseScanDists[row['ohN']].SetBinContent(
                    np.asscalar(row['vfatN'])+1,
                    np.asscalar(row['phase'])+1,
                    np.asscalar(row['nSuccesses'])
                )
        pass

    # Create 1D plots showing selected phase set points
    # =================================================
    # Load input data
    arrayType = { 'names':('link','vfatN','GBTPhase'), 'formats':('i4','i4','i4') }

    try:
        phaseSetPtsArray = np.loadtxt(phaseSetPtsFile, dtype=arrayType, skiprows=1)
    except IOError:
        printRed("An exception has occurred\nProbably file:\n\t{0}\t\nDoes not exist or is not readable.".format(phaseSetPtsFile))
        exit(os.EX_IOERR)

    # Strip all rows not found in ohMask
    phaseSetPtsArray = np.where( 
            (ohMask >> phaseSetPtsArray['link']) & 0x1,
            phaseSetPtsArray, 
            np.array([(-1,-1,-1)],dtype=arrayType) 
            )
    index2Remove = np.where(phaseSetPtsArray['link'] == -1)
    phaseSetPtsArray = np.delete(phaseSetPtsArray,index2Remove)
    
    # Make distributions
    dict_phaseSetPtDists = {}
    for ohN in range(12):
        # Skip masked OH's
        if( not ((ohMask >> ohN) & 0x1)):
            continue

        dict_phaseSetPtDists[ohN] = r.TGraph(24)
        dict_phaseSetPtDists[ohN].SetMarkerStyle(22)
        dict_phaseSetPtDists[ohN].SetMarkerSize(1.0)
        dict_phaseSetPtDists[ohN].SetMarkerColor(r.kGreen)
        dict_phaseSetPtDists[ohN].GetXaxis().SetTitle("VFAT Position")
        dict_phaseSetPtDists[ohN].GetYaxis().SetTitle("GBT Phase")

        if identifier is not None:
            name = "g_phaseSetPts_vs_vfatN_{0}_OH{1}".format(identifier,ohN)
        else:
            name = "g_phaseSetPts_vs_vfatN_OH{0}".format(ohN)
            pass
        dict_phaseSetPtDists[ohN].SetName(name)
        pass

    # Fill distributions
    for row in phaseSetPtsArray:
        dict_phaseSetPtDists[row['link']].SetPoint(
                    np.asscalar(row['vfatN']),
                    np.asscalar(row['vfatN']),
                    np.asscalar(row['GBTPhase'])
                )
        pass

    # Make an output canvas?
    if savePlots:
        from gempython.utils.wrappers import envCheck
        envCheck('ELOG_PATH')
        elogPath  = os.getenv('ELOG_PATH')

        nPadX = 4
        nPadY = 3
        if identifier is not None:
            name = "canv_GBTPhaseScanResults_{0}".format(identifier)
        else:
            name = "canv_GBTPhaseScanResults"

        r.gROOT.SetBatch(True)
        r.gStyle.SetOptStat(0)
        thisCanv = r.TCanvas(name,"GBT Phase Scan Results",nPadX*600,nPadY*600)
        thisCanv.Divide(nPadX,nPadY)
        for ohN in range(12):
            # Skip masked OH's
            if( not ((ohMask >> ohN) & 0x1)):
                continue

            thisCanv.cd(ohN+1)
            thisCanv.cd(ohN+1).SetGrid()
            dict_phaseScanDists[ohN].Draw("COLZ")
            dict_phaseSetPtDists[ohN].Draw("sameP")
            thisLat = r.TLatex()
            thisLat.SetTextSize(0.045)
            thisLat.DrawLatexNDC(0.10,0.95,"OH{0}".format(ohN))
            pass

        thisCanv.SaveAs("{0}/{1}.png".format(elogPath,thisCanv.GetName()))
        thisCanv.SaveAs("{0}/{1}.pdf".format(elogPath,thisCanv.GetName()))
        pass

    return (dict_phaseScanDists,dict_phaseSetPtDists)

def getScandateFromFilename(infilename):
    """
    Searches an infilename for a substring of the form 'YYYY.MM.DD.hh.mm'.  If this 
    is found the substring is returned as the scandate; otherwise the string
    'noscandate' is returned.

    Example infilename would be something like:

        /your/dataPath/env/var/detectorName/scanType/YYYY.MM.DD.hh.mm/someTFile.root
    """

    if "current" in infilename:
        return "current"
    elif len(infilename.split('/')) > 1 and len(infilename.split('/')[len(infilename.split('/')) - 2].split('.')) == 5:
        return infilename.split('/')[len(infilename.split('/')) - 2]
    else:    
        return 'noscandate'

def getSinglePhaseScanPlot(ohN,phaseScanFile,phaseSetPtsFile,identifier=None,savePlots=True, gemType="ge11"):
    """
    As getPhaseScanPlots but for a single optohybrid, defined by ohN, inside the input files.
    Returns a tuple where elements are given by:

        [0] - TH2F object with the phase scan data plotted
        [1] - TGraph object with the phase set points plotted

    Arguments are defined as:

    ohN             - Optohybrid number to make the plot for
    phaseScanFile   - file storing phase scan results, expected format to be what is
                      defined in xhal.reg_interface_gem.core.gbt_utils_extended function
                      saveGBTPhaseScanResults
    phaseSetPtsFile - file storing phase set points determined by testConnectivity.py
    identifier      - String that will be inserted to all TObject Names, e.g. 'shelf02'
    savePlots       - If true will save the two output plots to disk
    """

    ohMask = (0x1 << ohN)
    tuplePlotDicts = getPhaseScanPlots(phaseScanFile,phaseSetPtsFile,identifier,ohMask,False)

    phaseScanDist   = tuplePlotDicts[0][ohN]
    phaseScanSetPts = tuplePlotDicts[1][ohN]

    if savePlots:
        from gempython.utils.wrappers import envCheck
        envCheck('ELOG_PATH')

        import os
        elogPath  = os.getenv('ELOG_PATH')

        if identifier is not None:
            name = "canv_GBTPhaseScanResults_{0}".format(identifier)
        else:
            name = "canv_GBTPhaseScanResults"
        pass

        import ROOT as r
        r.gROOT.SetBatch(True)
        r.gStyle.SetOptStat(0)
        canvPhaseScan = r.TCanvas(name,"GBT Phase Scan Results",600,600)
        canvPhaseScan.cd()
        canvPhaseScan.cd().SetGrid()
        phaseScanDist.Draw("COLZ")
        phaseScanSetPts.Draw("sameP")
        thisLat = r.TLatex()
        thisLat.SetTextSize(0.045)
        if identifier is not None:
            thisLat.DrawLatexNDC(0.10,0.95,"OH{0}: {1}".format(ohN,identifier))
        else:
            thisLat.DrawLatexNDC(0.10,0.95,"OH{0}".format(ohN))
            pass

        canvPhaseScan.SaveAs("{0}/{1}.png".format(elogPath,canvPhaseScan.GetName()))
        canvPhaseScan.SaveAs("{0}/{1}.pdf".format(elogPath,canvPhaseScan.GetName()))

    return (phaseScanDist, phaseScanSetPts)

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

def getSubArray(structArray, fields):
    """
    Taken from: https://stackoverflow.com/a/21819324

    Returns a view of a structured numpy array

    structArray - structured numpy array
    fields - list of column names in the structure array
    """
    import numpy as np
    dtype2 = np.dtype({name:structArray.dtype.fields[name] for name in fields})
    return np.ndarray(structArray.shape, dtype2, structArray, 0, structArray.strides)

def init_worker():
    """
    If used as the initializer argument for multiprocessing.Pool object
    this will ignore KeyboardInterrupt exceptions in the worker processes
    and let the parent process handle the exception
    """
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)

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

    from ...utils.wrappers import envCheck, runCommand
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
        endDay = datetime.date(endDateInfo[0], endDateInfo[1], endDateInfo[2])
        pass

    import os
    dirPath = getDirByAnaType(anaType, chamberName, ztrim)
    listOfScanDates = os.listdir(dirPath)

    try:
        listOfScanDatesFile = open('{0}/listOfScanDates.txt'.format(dirPath),'w+')
    except IOError as e:
        print("Exception:", e)
        print("Failed to open write output file")
        print("Is the below directory writeable?")
        print("")
        print("\t{0}".format(dirPath))
        print("")
        exit(os.EX_IOERR)
        pass
    
    listOfScanDatesFile.write('ChamberName{0}scandate\n'.format(delim))
    for scandate in listOfScanDates:
        if "current" == scandate:
            continue
        try:
            scandateInfo = [ int(info) for info in scandate.split('.') ]
        except ValueError as e:
            print("Skipping directory {0}/{1}".format(dirPath,scandate))
            continue
        thisDay = datetime.date(scandateInfo[0],scandateInfo[1],scandateInfo[2])

        if (startDay < thisDay and thisDay <= endDay):
            listOfScanDatesFile.write('{0}{1}{2}\n'.format(chamberName,delim,scandate))
            pass
        pass

    listOfScanDatesFile.close()
    runCommand( ['chmod','g+rw','{0}/listOfScanDates.txt'.format(dirPath)] )

    return

def parseCalFile(filename=None, gemType="ge11"):
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
    from gempython.tools.hw_constants import vfatsPerGemVariant
    calDAC2Q_b = np.zeros(vfatsPerGemVariant[gemType])
    calDAC2Q_m = np.zeros(vfatsPerGemVariant[gemType])
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
        calDAC2Q_b = -0.8 * np.ones(vfatsPerGemVariant[gemType])
        calDAC2Q_m = 0.05 * np.ones(vfatsPerGemVariant[gemType])
        pass

    return (calDAC2Q_m, calDAC2Q_b)

def parseArmDacCalFile(filename, gemType="ge11"):
    """
    Reads a text file and supplies the coefficients of the 
    quartic polynomial used for used for converting between 
    DAC units to charge units (in fC) for CFG_THR_ARM_DAC

    Returns a tuple of numpy arrays where index i of the tuple
    corresponds to the coefficient of x^(4-i).  The returned 
    arrays are indexed by VFAT position.
    
    The structure of filename is expected to be:

        vfatN/I:coef4/F:coef3/F:coef2/F:coef1/F:coef0/F
        0 4.612e-8  -1.361e-5 0.001  0.092    -0.211
        1 8.657e-8  -2.742e-5 0.003  2.936e-6 1.610
        2 6.987e-8  -2.152e-5 0.002  0.042    4.880
        3 -2.584e-8  1.127e-5 -0.001 0.204    -1.949
        ...
        ...

    """
    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    import ROOT as r
    from gempython.tools.hw_constants import vfatsPerGemVariant

    
    # Set the CAL DAC to fC conversion
    coef4 = np.zeros(vfatsPerGemVariant[gemType])
    coef3 = np.zeros(vfatsPerGemVariant[gemType])
    coef2 = np.zeros(vfatsPerGemVariant[gemType])
    coef1 = np.zeros(vfatsPerGemVariant[gemType])
    coef0 = np.zeros(vfatsPerGemVariant[gemType])
    list_bNames = ["vfatN","coef4","coef3","coef2","coef1","coef0"]
    calTree = r.TTree('calTree','Tree holding VFAT Calibration Info')
    try:
        calTree.ReadFile(filename)
    except IOError:
        printRed("file {0} is not readable or does not exist, please cross-check".format(filename))
        import os
        exit(os.EX_IOERR)
    array_CalData = rp.tree2array(tree=calTree, branches=list_bNames)
    
    for dataPt in array_CalData:
        coef4[dataPt['vfatN']] = dataPt['coef4']
        coef3[dataPt['vfatN']] = dataPt['coef3']
        coef2[dataPt['vfatN']] = dataPt['coef2']
        coef1[dataPt['vfatN']] = dataPt['coef1']
        coef0[dataPt['vfatN']] = dataPt['coef0']
        pass
    
    return (coef4, coef3, coef2, coef1, coef0)

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
        [0] -> parsedListOfScanDates, a list of tuples of the form: (cName, scandate, indepVarValue)
        [1] -> indepVarName if present (empty string if not)
    """

    import os

    # Check input file
    try:
        fileScanDates = open(filename, 'r') 
    except IOError as e:
        print('{0} does not seem to exist or is not readable'.format(filename))
        print(e)
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
                except ValueError as e:
                    print("Non-numeric input given, maybe you ment to call with option 'alphaLabels=True'?")
                    print("Exiting")
                    exit(os.EX_USAGE)
        else:
            print("Input format incorrect")
            print("I was expecting a delimited file using '{0}' with all lines having either 2 or 3 entries".format(delim))
            print("But I received:")
            print("\t{0}".format(line))
            print("Exiting")
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

  
def getSummaryCanvas(dictSummary, dictSummaryPanPin2=None, name='Summary', trimPt=None, drawOpt="colz", gemType="ge11", write2Disk=False):
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
    gemType            - gemType used for getting the correct mapping
    write2Disk         - Option to save canvas with the name as the variable
    """

    import ROOT as r
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx, chamber_maxiEtaiPhiPair
    from gempython.tools.hw_constants import vfatsPerGemVariant
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
    
    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)

    maxiEta, maxiPhi =chamber_maxiEtaiPhiPair[gemType]
    
    canv = r.TCanvas(name, name, 500 * maxiEta, 500 * maxiPhi)
    
    if dictSummary is not None and dictSummaryPanPin2 is None:
        canv.Divide(maxiEta, maxiPhi)
        for vfat, padIdx in chamber_vfatPos2PadIdx[gemType].iteritems():
            canv.cd(padIdx)
            try:
                dictSummary[vfat].Draw(drawOpt)
            except KeyError as err:
                continue
            if trimPt is not None and trimLine is not None:
                trimLine = r.TLine(-0.5, trimVcal[vfat], maxChans-0.5, trimVcal[vfat])
                legend.Clear()
                legend.AddEntry(trimLine, 'trimVCal is {0}'.format(trimVcal[vfat]))
                legend.Draw('SAME')
                trimLine.SetLineColor(1)
                trimLine.SetLineWidth(3)
                trimLine.Draw('SAME')
                pass
            
    elif dictSummary is not None and dictSummaryPanPin2 is not None:
        # possibly remove unless fixed, or at the very least needs to be improved!!
        canv.Divide(maxiEta, 2*maxiPhi)
        shift = maxiEta*(maxiPhi+4) + 1
        for vfat in range(0, vfatsPerGemVariant[gemType]):
            if vfat % maxiEta == 0:
                shift -= maxiEta*3
            canv.cd(vfat+shift)
            dictSummary[vfat].Draw(drawOpt)
            canv.Update()
            canv.cd(vfat+shift+maxiEta)
            dictSummaryPanPin2[vfat].Draw(drawOpt)
            canv.Update()
            pass
        pass
    
    canv.Update()
    
    if write2Disk:
        canv.SaveAs(name)        

    return canv

def getSummaryCanvasByiEta(dictSummary, name='Summary', drawOpt="colz", gemType="ge11", write2Disk=False):
    """
    Makes an Canvas with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per ieta.  Each will be 
                         drawn on a separate pad
    name               - Name of canvas
    drawOpt            - Draw option
    gemType            - gemType used for getting the correct mapping
    write2Disk         - Option to save canvas with the name as the variable "name"
    """

    import ROOT as r
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx, chamber_maxiEtaiPhiPair
    
    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    
    maxiEta = chamber_maxiEtaiPhiPair[gemType][0]
    xyPair = (4,maxiEta//4) 
    
    canv = r.TCanvas(name, name, 500 * xyPair[0], 500 * xyPair[1])
    canv.Divide(xyPair[0], xyPair[1])

    for index in range(1,maxiEta+1):
        canv.cd(index)
        try:
            dictSummary[index].Draw(drawOpt)
        except KeyError as err:
            continue
                                                                                
    canv.Update()

    if write2Disk:
        canv.SaveAs(name)

    return canv




def addPlotToCanvas(canv=None, content = None, drawOpt = '', gemType="ge11"):
    """
    Adds additional plots to a canvas created by getSummaryCanvas() (takes care of the mapping)
    
    canv - TCanvas previously produced by getSummaryCanvas
    content - either None or an array of TObjects (one per VFAT) that will be drawn on the canvas.
    drawOpt - draw option to be used when drawing elements of initialContent
    gemType - gemType used for getting the correct mapping
                               
    """

    import ROOT as r
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx
    
    
    for index, padIdx in chamber_vfatPos2PadIdx[gemType].iteritems():
        canv.cd(padIdx)
        try:
            content[index].Draw(drawOpt)
        except KeyError as err:
            continue

    canv.Update()
    return canv

