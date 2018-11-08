#!/usr/bin/env python

r"""
``anaDACScan`` -- analyzes DAC scan data
========================================

Synopsis
--------

**anaDACScan.py** [*OPTIONS*]

Description
-----------

This script reads in calibration information and DAC scan data, performs a fit for each VFAT, computes the DAC value corresponding to the nominal current or voltage for each VFAT, and reports the results.

Arguments
---------

.. program:: anaDACScan.py

.. option:: infilename

    Name of the input file root.

.. option:: --assignXErrors  

    If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case). 

.. option:: --calFileList
  
    Provide a file containing a list of calFiles in the following format. Example:: 

    0 /path/to/my/cal/file.txt
    1 /path/to/my/cal/file.txt
    ...
    ...

.. option:: --outfilename

    Name of the output root file. Default is DACFitData.root.

Example
-------

.. code-block:: bash

    anaDACScan.py /path/to/input.root  --calFileList calibration.txt --assignXErrors
"""

if __name__ == '__main__':

    import ROOT as r
    
    from gempython.gemplotting.utils.anautilities import parseCalFile
    from gempython.utils.nesteddict import nesteddict
    from gempython.gemplotting.utils.anautilities import make3x8Canvas
    
    from gempython.gemplotting.mapping.chamberInfo import chamber_config

    from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
    
    import os
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', type=str, help="Filename from which input information is read", metavar='infilename')
    parser.add_argument("--calFileList", type=str, help="File specifying which calFile to use for each OH. Format: 0 /path/to/my/cal/file.txt<newline> 1 /path/to/my/cal/file.txt<newline>...", metavar="calFileList")
    parser.add_argument('-o','--outfilename', dest='outfilename', type=str, default="DACFitData.root", help="Filename to which output information is written", metavar='outfilename')
    parser.add_argument('--assignXErrors', dest='assignXErrors', action='store_true', help="If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case).")

    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)
    
    dacScanFile = r.TFile(args.infilename)

    import root_numpy as rp
    import numpy as np
    list_bNames = ['vfatN','link','dacValY']
    vfatArray = rp.tree2array(tree=dacScanFile.dacScanTree,branches=list_bNames)
    ohArray = np.unique(vfatArray['link'])
    dict_nonzeroVFATs = {}
    for ohN in ohArray:
        dict_nonzeroVFATs[ohN] = np.unique(vfatArray[np.logical_and(vfatArray['dacValY'] > 0,vfatArray['link'] == ohN)]['vfatN'])

    dataPath = os.getenv("DATA_PATH")
    elogPath = os.getenv("ELOG_PATH") 
    
    if len(args.infilename.split('/')) > 1 and len(args.infilename.split('/')[len(args.infilename.split('/')) - 2].split('.')) == 5:
        scandate = args.infilename.split('/')[len(args.infilename.split('/')) - 2]
    else:    
        scandate = 'noscandate'
        
    for oh in ohArray:
        if scandate == 'noscandate':
            os.system("mkdir -p "+ elogPath+"/"+chamber_config[oh])
        else:
            os.system("mkdir -p "+ dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate)
            
    # Determine which DAC was scanned and against which ADC
    nameX = ""
    nameY = ""
    for event in dacScanFile.dacScanTree:
        nameX = str(event.nameX.data())
        nameY = str(event.nameY.data())
        break # all entries will be the same

    if nameY not in ['ADC0', 'ADC1']:
        print("Error: unexpected value of nameY: '%s'"%nameY)
        exit(1)

    from utils.anaInfo import nominalDacValues
    from utils.anaInfo import nominalDacScalingFactors
        
    if nameX not in nominalDacValues.keys():
        print("Error: unexpected value of nameX: '%s'"%nameX)
        exit(1)

    #the nominal reference current is 10 uA and it has a scaling factor of 0.5   
    nominal_iref = 10*0.5

    nominal = nominalDacValues[nameX][0]

    #convert all voltages to mV and currents to uA
    if nominalDacValues[nameX][1] == "V":
        nominal *= pow(10.0,3)
    elif nominalDacValues[nameX][1] == 'mV':
        pass
    elif nominalDacValues[nameX][1] == 'uV':
        nominal *= pow(10.0,-3)
    elif nominalDacValues[nameX][1] == 'nV':
        nominal *= pow(10.0,-6)
    elif nominalDacValues[nameX][1] == "A":
        nominal *= pow(10.0,6)
    elif nominalDacValues[nameX][1] == 'mA':
        nominal *= pow(10.0,3)
    elif nominalDacValues[nameX][1] == 'uA':
        pass
    elif nominalDacValues[nameX][1] == 'nA':
        nominal *= pow(10.0,-3)
    else:
        print("Error: unexpected units: '%s'"%nominalDacValues[nameX][1])
        exit(1)

    calInfo = {}

    if args.calFileList != None:
        for line in open(args.calFileList):
            if line[0] == "#":
                continue
            line = line.strip()
            first = line.split()[0]
            second = line.split()[1]
            tuple_calInfo = parseCalFile(second)
            calInfo[int(first)] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}

    #for each OH, check if calibration files were provided, if not search for the calFile in the $DATA_PATH, if it is not there, then skip that OH for the rest of the script
    for oh in ohArray:
        if oh not in calInfo.keys():
            calAdcCalFile = "{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,chamber_config[oh],nameY)
            calAdcCalFileExists = os.path.isfile(calAdcCalFile)
            if not calAdcCalFileExists:
                print("Skipping OH{0}, detector {1}, missing {2} calibration file:\n\t{3}".format(
                    oh,
                    chamber_config[oh],
                    nameY,
                    calAdcCalFile))
                ohArray = np.delete(ohArray,(oh))

    if len(ohArray) == 0:
        print('No OHs with a calFile, exiting.')
        exit(1)
           
    # Initialize nested dictionaries
    dict_DACvsADC_Graphs = nesteddict()
    dict_RawADCvsDAC_Graphs = nesteddict()
    dict_DACvsADC_Funcs = nesteddict()

    # Initialize a TGraphErrors and a TF1 for each vfat
    for oh in ohArray:
        for vfat in range(0,24):
            dict_RawADCvsDAC_Graphs[oh][vfat] = r.TGraphErrors()
            dict_RawADCvsDAC_Graphs[oh][vfat].GetXaxis().SetTitle(nameX)
            dict_RawADCvsDAC_Graphs[oh][vfat].GetYaxis().SetTitle(nameY)
            dict_DACvsADC_Graphs[oh][vfat] = r.TGraphErrors()
            dict_DACvsADC_Graphs[oh][vfat].SetTitle("VFAT{}".format(vfat))
            dict_DACvsADC_Graphs[oh][vfat].SetMarkerSize(5)
            #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
            dict_DACvsADC_Graphs[oh][vfat].GetYaxis().SetTitle(nameX)
            if nominalDacValues[nameX][1][len(nominalDacValues[nameX][1])-1] == 'A':
                dict_DACvsADC_Graphs[oh][vfat].GetXaxis().SetTitle(nameY + " (#muA)")
            else:
                dict_DACvsADC_Graphs[oh][vfat].GetXaxis().SetTitle(nameY + " (mV)")
            #we will use a fifth degree polynomial to do the fit
            dict_DACvsADC_Funcs[oh][vfat] = r.TF1("DAC Scan Function","[0]*x^5+[1]*x^4+[2]*x^3+[3]*x^2+[4]*x+[5]")
            dict_DACvsADC_Funcs[oh][vfat].SetLineWidth(1)
            dict_DACvsADC_Funcs[oh][vfat].SetLineStyle(3)

    outputFiles = {}         
             
    for oh in ohArray:
        if scandate == 'noscandate':
            outputFiles[oh] = r.TFile(elogPath+"/"+chamber_config[oh]+"/"+args.outfilename,'recreate')
        else:    
            outputFiles[oh] = r.TFile(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/"+args.outfilename,'recreate')

    # Loop over events in the tree and fill plots
    for event in dacScanFile.dacScanTree:
        oh = event.link
        vfat = event.vfatN

        if vfat not in dict_nonzeroVFATs[oh]:
            continue

        #the output of the calibration is mV
        calibrated_ADC_value=calInfo[oh]['slope'][vfat]*event.dacValY+calInfo[oh]['intercept'][vfat]
        calibrated_ADC_error=calInfo[oh]['slope'][vfat]*event.dacValY_Err

        #Use Ohm's law to convert the currents to voltages. The VFAT3 team told us that a 20 kOhm resistor was used.
        if nominalDacValues[nameX][1][len(nominalDacValues[nameX][1])-1] == "A":

            #V (mV) = I (uA) R (kOhm)
            #V (10^-3) = I (10^-6) R (10^3)
            calibrated_ADC_value = calibrated_ADC_value/20.0
            calibrated_ADC_error = calibrated_ADC_error/20.0

            if nameX != 'CFG_IREF':
                calibrated_ADC_value -= nominal_iref 

            calibrated_ADC_value /= nominalDacScalingFactors[nameX]
                
        #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
        #the nameX variable is the DAC register that is scanned, and we want to determine its nominal value
        if args.assignXErrors:
            dict_DACvsADC_Graphs[oh][vfat].SetPoint(dict_DACvsADC_Graphs[oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[oh][vfat].GetN(),event.dacValX,event.dacValY)
            dict_DACvsADC_Graphs[oh][vfat].SetPointError(dict_DACvsADC_Graphs[oh][vfat].GetN()-1,calibrated_ADC_error,event.dacValX_Err)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[oh][vfat].GetN()-1,event.dacValX_Err,0)
        else:
            dict_DACvsADC_Graphs[oh][vfat].SetPoint(dict_DACvsADC_Graphs[oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[oh][vfat].GetN(),event.dacValX,event.dacValY)
            dict_DACvsADC_Graphs[oh][vfat].SetPointError(dict_DACvsADC_Graphs[oh][vfat].GetN()-1,calibrated_ADC_error,0)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[oh][vfat].GetN()-1,0,0)

    # Fit the TGraphErrors objects    
    for oh in ohArray:
        for vfat in range(0,24):
            if vfat not in dict_nonzeroVFATs[oh]:
                #so that the output plots for these VFATs are completely empty
                dict_DACvsADC_Funcs[oh][vfat].SetLineColor(0)
                continue
            #the fits fail when the errors on dacValY (the x-axis variable) are used 
            dict_DACvsADC_Graphs[oh][vfat].Fit(dict_DACvsADC_Funcs[oh][vfat],"QEX0")

    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = {}
    dict_dacVals = nesteddict()
    for oh in ohArray:
        graph_dacVals[oh] = r.TGraph()
        graph_dacVals[oh].SetMinimum(0)
        graph_dacVals[oh].GetXaxis().SetTitle("VFATN")
        graph_dacVals[oh].GetYaxis().SetTitle("nominal DAC value")
        for vfat in range(0,24):
            if vfat not in dict_nonzeroVFATs[oh]:
                continue

            maxDacValue = 255
            
            for dacSelect in maxVfat3DACSize.keys():

                #the registers CFG_THR_ARM_DAC and CFG_THR_ZCC_DAC could correspond to voltages or currents
                #we will use voltages until a way of distinguishing the two cases is implemented 
                if dacSelect == 14 or dacSelect == 15:
                    continue
                
                if maxVfat3DACSize[dacSelect][1] == nameX:
                    maxDacValue = int(maxVfat3DACSize[dacSelect][0])
                    break
                    
            #evaluate the fitted function at the nominal current or voltage value and convert to an integer
            fittedDacValue = int(dict_DACvsADC_Funcs[oh][vfat].Eval(nominal))
            finalDacValue = max(0,min(maxDacValue,fittedDacValue))
            
            if fittedDacValue != finalDacValue:
                print('Warning: The fitted DAC value, %i, is outside of the range that the register can hold: [0,%i]. It will be replaced by %i.'%(fittedDacValue,maxDacValue,finalDacValue))
                
            dict_dacVals[oh][vfat] = finalDacValue
            graph_dacVals[oh].SetPoint(graph_dacVals[oh].GetN(),vfat,dict_dacVals[oh][vfat])
             
    # Write out the dacVal results to a root file, a text file, and the terminal
    outputTxtFiles_dacVals = {}    

    for oh in ohArray:
        if scandate == 'noscandate':
            outputTxtFiles_dacVals[oh] = open(elogPath+"/"+chamber_config[oh]+"/NominalDACValues.txt",'w')
        else:    
            outputTxtFiles_dacVals[oh] = open(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/NominalDACValues.txt",'w')

    print( "| OH | vfatN | dacVal |")
    print( "| :-: | :---: | :----: |")        
    
    for oh in ohArray:
        outputFiles[oh].cd()
        outputFiles[oh].mkdir("Summary")
        outputFiles[oh].cd("Summary")
        graph_dacVals[oh].Write("nominalDacValVsVFATX")
        for vfat in range(0,24):
            if vfat not in dict_nonzeroVFATs[oh]:
                continue            
            
            outputFiles[oh].cd()
            outputFiles[oh].mkdir("VFAT"+str(vfat))
            outputFiles[oh].cd("VFAT"+str(vfat))
            dict_DACvsADC_Graphs[oh][vfat].Write("DACvsADC")
            dict_RawADCvsDAC_Graphs[oh][vfat].Write("RawADCvsDAC")
            outputFiles[oh].cd("../")
            outputTxtFiles_dacVals[oh].write(str(vfat)+"\t"+str(dict_dacVals[oh][vfat])+"\n")
            print("| {0} | {1}  | {2} | ".format(
                oh,
                vfat,
                dict_dacVals[oh][vfat]
            ))

    # Make plots        
    for oh in ohArray:
        canv_Summary = make3x8Canvas('canv_Summary',dict_DACvsADC_Graphs[oh],'APE1',dict_DACvsADC_Funcs[oh],'')
        if scandate == 'noscandate':
            canv_Summary.SaveAs(elogPath+"/"+chamber_config[oh]+"/Summary.png")
        else:
            canv_Summary.SaveAs(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/Summary.png")
