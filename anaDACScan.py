#!/usr/bin/env python

r"""
``anaDACScan`` -- analyzes DAC scan data
========================================

Synopsis
--------

**anaDACScan.py** [*OPTIONS*]

Description
-----------

This script reads in ADC0 or ADC1 calibration coefficients and DAC scan data, performs a fit for each VFAT, computes the DAC value corresponding to the nominal current or voltage for each VFAT, and reports the results.

Arguments
---------

.. program:: anaDACScan.py

.. option:: infilename

    Name of the input file root.

.. option:: --assignXErrors  

    If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case). 

.. option:: --calFileList
  
    Provide a file containing a list of calFiles.  The space character is used as a delimiter.  The first column is the link number.  The second is the calibration file (given with full physical filename) for that link number. Example::

    0 /path/to/my/cal/file.txt
    1 /path/to/my/cal/file.txt
    ...
    ...

.. option:: --outfilename

    Name of the output root file. Default is DACFitData.root.

.. option:: --print

    If provided prints a summary table to terminal for each DAC showing for each VFAT position the nominal value that was found

Example
-------

.. code-block:: bash

    anaDACScan.py /path/to/input.root  --calFileList calibration.txt --assignXErrors
"""

if __name__ == '__main__':
    from gempython.gemplotting.utils.anautilities import parseCalFile
    from gempython.gemplotting.utils.anautilities import make3x8Canvas
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', type=str, help="Filename from which input information is read", metavar='infilename')
    parser.add_argument('--assignXErrors', dest='assignXErrors', action='store_true', help="If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case).")
    parser.add_argument("--calFileList", type=str, help="File specifying which calFile to use for each OH. Format: 0 /path/to/my/cal/file.txt<newline> 1 /path/to/my/cal/file.txt<newline>...", metavar="calFileList")
    parser.add_argument('-o','--outfilename', dest='outfilename', type=str, default="DACFitData.root", help="Filename to which output information is written", metavar='outfilename')
    parser.add_argument("-p","--print",dest="printSum", action="store_true", help="If provided prints a summary table to terminal for each DAC showing for each VFAT position the nominal value that was found")
    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)
    
    dacScanFile = r.TFile(args.infilename,"READ")

    print("Loading info from input TTree")

    import root_numpy as rp
    import numpy as np
    list_bNames = ['vfatN','link','dacValY','nameX']
    vfatArray = rp.tree2array(tree=dacScanFile.dacScanTree,branches=list_bNames)
    ohArray = np.unique(vfatArray['link'])
    dacNameArray = np.unique(vfatArray['nameX'])
    dict_nonzeroVFATs = {}
    for ohN in ohArray:
        dict_nonzeroVFATs[ohN] = np.unique(vfatArray[np.logical_and(vfatArray['dacValY'] > 0,vfatArray['link'] == ohN)]['vfatN'])

    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    import os
    dataPath = os.getenv("DATA_PATH")
    elogPath = os.getenv("ELOG_PATH") 
    
    if len(args.infilename.split('/')) > 1 and len(args.infilename.split('/')[len(args.infilename.split('/')) - 2].split('.')) == 5:
        scandate = args.infilename.split('/')[len(args.infilename.split('/')) - 2]
    else:    
        scandate = 'noscandate'
        
    from gempython.utils.wrappers import runCommand
    for oh in ohArray:
        if scandate == 'noscandate':
            runCommand(["mkdir", "-p", "{0}/{1}".format(elogPath,chamber_config[oh])])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(elogPath,chamber_config[oh])])
        else:
            runCommand(["mkdir", "-p", "{0}/{1}/dacScans/{2}".format(dataPath,chamber_config[oh],scandate)])
            runCommand(["chmod", "g+rw", "{0}/{1}/dacScans/{2}".format(dataPath,chamber_config[oh],scandate)])
            
    # Determine which DAC was scanned and against which ADC
    adcName = ""
    for event in dacScanFile.dacScanTree:
        adcName = str(event.nameY.data())
        break # all entries will be the same

    from gempython.utils.gemlogger import colormsg
    import logging
    if adcName not in ['ADC0', 'ADC1']:
        print(colormsg("Error: unexpected value of adcName: '%s'"%adcName,logging.ERROR))
        exit(os.EX_DATAERR)

    from gempython.gemplotting.utils.anaInfo import nominalDacValues, nominalDacScalingFactors
    nominal = {}
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        if dacName not in nominalDacValues.keys():
            print(colormsg("Error: unexpected DAC Name: '{}'".format(dacName),logging.ERROR))
            exit(os.EX_DATAERR)
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
                print(colormsg("Error: unexpected units: '%s'"%nominalDacValues[dacName][1],logging.ERROR))
                exit(os.EX_DATAERR)

    #the nominal reference current is 10 uA and it has a scaling factor of 0.5   
    nominal_iref = 10*0.5

    calInfo = {}
    if args.calFileList != None:
        for line in open(args.calFileList):
            if line[0] == "#":
                continue
            dataEntry = (line.strip()).split()
            link = dataEntry[0]
            calFile = dataEntry[1]
            tuple_calInfo = parseCalFile(calFile)
            calInfo[int(link)] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}

    #for each OH, check if calibration files were provided, if not search for the calFile in the $DATA_PATH, if it is not there, then skip that OH for the rest of the script
    for oh in ohArray:
        if oh not in calInfo.keys():
            calAdcCalFile = "{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,chamber_config[oh],adcName)
            calAdcCalFileExists = os.path.isfile(calAdcCalFile)
            if calAdcCalFileExists:
                tuple_calInfo = parseCalFile(calAdcCalFile)
                calInfo[oh] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}
            else:    
                print("Skipping OH{0}, detector {1}, missing {2} calibration file:\n\t{3}".format(
                    oh,
                    chamber_config[oh],
                    adcName,
                    calAdcCalFile))
                ohArray = np.delete(ohArray,(oh))

    if len(ohArray) == 0:
        print(colormsg('No OHs with a calFile, exiting.',logging.ERROR))
        exit(os.EX_DATAERR)
           
    # Initialize nested dictionaries
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_DACvsADC_Graphs = ndict()
    dict_RawADCvsDAC_Graphs = ndict()
    dict_DACvsADC_Funcs = ndict()

    print("Initializing TObjects")

    # Initialize a TGraphErrors and a TF1 for each vfat
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for oh in ohArray:
            for vfat in range(0,24):
                dict_RawADCvsDAC_Graphs[dacName][oh][vfat] = r.TGraphErrors()
                dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetXaxis().SetTitle(dacName)
                dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetYaxis().SetTitle(adcName)
                dict_DACvsADC_Graphs[dacName][oh][vfat] = r.TGraphErrors()
                dict_DACvsADC_Graphs[dacName][oh][vfat].SetTitle("VFAT{}".format(vfat))
                dict_DACvsADC_Graphs[dacName][oh][vfat].SetMarkerSize(5)
                #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
                dict_DACvsADC_Graphs[dacName][oh][vfat].GetYaxis().SetTitle(dacName)
                if nominalDacValues[dacName][1][len(nominalDacValues[dacName][1])-1] == 'A':
                    dict_DACvsADC_Graphs[dacName][oh][vfat].GetXaxis().SetTitle(adcName + " (#muA)")
                else:
                    dict_DACvsADC_Graphs[dacName][oh][vfat].GetXaxis().SetTitle(adcName + " (mV)")
                #we will use a fifth degree polynomial to do the fit
                dict_DACvsADC_Funcs[dacName][oh][vfat] = r.TF1("DAC Scan Function","[0]*x^5+[1]*x^4+[2]*x^3+[3]*x^2+[4]*x+[5]")
                dict_DACvsADC_Funcs[dacName][oh][vfat].SetLineWidth(1)
                dict_DACvsADC_Funcs[dacName][oh][vfat].SetLineStyle(3)

    outputFiles = {}         
    for oh in ohArray:
        if scandate == 'noscandate':
            outputFiles[oh] = r.TFile(elogPath+"/"+chamber_config[oh]+"/"+args.outfilename,'recreate')
        else:    
            outputFiles[oh] = r.TFile(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/"+args.outfilename,'recreate')

    print("Looping over stored events in dacScanTree")

    # Loop over events in the tree and fill plots
    for event in dacScanFile.dacScanTree:
        oh = event.link
        vfat = event.vfatN

        if vfat not in dict_nonzeroVFATs[oh]:
            continue

        #the output of the calibration is mV
        calibrated_ADC_value=calInfo[oh]['slope'][vfat]*event.dacValY+calInfo[oh]['intercept'][vfat]
        calibrated_ADC_error=calInfo[oh]['slope'][vfat]*event.dacValY_Err

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
                
        #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
        #the dacName variable is the DAC register that is scanned, and we want to determine its nominal value
        if args.assignXErrors:
            dict_DACvsADC_Graphs[dacName][oh][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][oh][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][oh][vfat].GetN()-1,calibrated_ADC_error,event.dacValX_Err)
            dict_RawADCvsDAC_Graphs[dacName][oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetN()-1,event.dacValX_Err,0)
        else:
            dict_DACvsADC_Graphs[dacName][oh][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][oh][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][oh][vfat].GetN()-1,calibrated_ADC_error,0)
            dict_RawADCvsDAC_Graphs[dacName][oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][oh][vfat].GetN()-1,0,0)

    print("fitting DAC vs. ADC distributions")

    # Fit the TGraphErrors objects
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for oh in ohArray:
            for vfat in range(0,24):
                if vfat not in dict_nonzeroVFATs[oh]:
                    #so that the output plots for these VFATs are completely empty
                    dict_DACvsADC_Funcs[dacName][oh][vfat].SetLineColor(0)
                    continue
                #the fits fail when the errors on dacValY (the x-axis variable) are used
                dict_DACvsADC_Graphs[dacName][oh][vfat].Fit(dict_DACvsADC_Funcs[dacName][oh][vfat],"QEX0")

    # Create Determine max DAC size
    dict_maxByDacName = {}
    from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
    for dacSelect,dacInfo in maxVfat3DACSize.iteritems():
        dict_maxByDacName[dacInfo[1]]=dacInfo[0]

    print("Determining nominal values for bias voltage and/or current settings")

    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = ndict()
    dict_dacVals = ndict()
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        maxDacValue = dict_maxByDacName[dacName]

        for oh in ohArray:
            graph_dacVals[dacName][oh] = r.TGraph()
            graph_dacVals[dacName][oh].SetMinimum(0)
            graph_dacVals[dacName][oh].GetXaxis().SetTitle("VFATN")
            graph_dacVals[dacName][oh].GetYaxis().SetTitle("nominal {} value".format(dacName))

            for vfat in range(0,24):
                if vfat not in dict_nonzeroVFATs[oh]:
                    continue

                #evaluate the fitted function at the nominal current or voltage value and convert to an integer
                fittedDacValue = int(dict_DACvsADC_Funcs[dacName][oh][vfat].Eval(nominal[dacName]))
                finalDacValue = max(0,min(maxDacValue,fittedDacValue))
                
                if fittedDacValue != finalDacValue:
                    errorMsg = "Warning: when fitting DAC {0} the fitted value, {1}, is outside range the register can hold: [0,{2}]. It will be replaced by {3}.".format(
                            dacName,
                            fittedDacValue,
                            maxDacValue,
                            finalDacValue)
                    print(colormsg(errorMsg,logging.ERROR))
                    
                dict_dacVals[dacName][oh][vfat] = finalDacValue
                graph_dacVals[dacName][oh].SetPoint(graph_dacVals[dacName][oh].GetN(),vfat,dict_dacVals[dacName][oh][vfat])

    print("Writing output data")

    # Write out the dacVal results to a root file, a text file, and the terminal
    outputTxtFiles_dacVals = ndict()
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for oh in ohArray:
            if scandate == 'noscandate':
                outputTxtFiles_dacVals[dacName][oh] = open("{0}/{1}/NominalValues-{2}.txt".format(elogPath,chamber_config[oh],dacName),'w')
            else:
                outputTxtFiles_dacVals[dacName][oh] = open("{0}/{1}/dacScans/{2}/NominalValues-{3}.txt".format(dataPath,chamber_config[oh],scandate,dacName),'w')

    for oh in ohArray:
        # Per VFAT Poosition
        for vfat in range(0,24):
            thisVFATDir = outputFiles[oh].mkdir("VFAT{0}".format(vfat))

            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                thisDACDir = thisVFATDir.mkdir(dacName)
                thisDACDir.cd()

                dict_DACvsADC_Graphs[dacName][oh][vfat].Write("g_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_DACvsADC_Funcs[dacName][oh][vfat].Write("func_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_RawADCvsDAC_Graphs[dacName][oh][vfat].Write("g_VFAT{0}_RawADCvsDAC_{1}".format(vfat,dacName))

                if vfat in dict_nonzeroVFATs[oh]:
                    outputTxtFiles_dacVals[dacName][oh].write("{0}\t{1}\n".format(vfat,dict_dacVals[dacName][oh][vfat]))

        # Summary Case
        dirSummary = outputFiles[oh].mkdir("Summary")
        dirSummary.cd()
        for idx in range(len(dacNameArray)):
            dacName = np.asscalar(dacNameArray[idx])

            # Store summary graph
            graph_dacVals[dacName][oh].Write("g_NominalvsVFATPos_{0}".format(dacName))

            # Store summary grid canvas and print images
            canv_Summary = make3x8Canvas("canv_Summary_{0}".format(dacName),dict_DACvsADC_Graphs[dacName][oh],'APE1',dict_DACvsADC_Funcs[dacName][oh],'')
            if scandate == 'noscandate':
                canv_Summary.SaveAs("{0}/{1}/Summary_{1}_DACScan_{2}.png".format(elogPath,chamber_config[oh],dacName))
            else:
                canv_Summary.SaveAs("{0}/{1}/dacScans/{2}/Summary{1}_DACScan_{2}.png".format(dataPath,chamber_config[oh],scandate,dacName))

    # Print Summary?
    if args.printSum:
        print("| ohN | vfatN | dacName | Value |")
        print("| :-: | :---: | :-----: | :---: |")
        for oh in ohArray:
            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])
            
                for vfat in range(0,24):
                    if vfat not in dict_nonzeroVFATs[oh]:
                        continue

                    print("| {0} | {1} | {2} | {3} |".format(
                        oh,
                        vfat,
                        dacName,
                        dict_dacVals[dacName][oh][vfat])
                    )

    print("\nAnalysis completed. Goodbye")
