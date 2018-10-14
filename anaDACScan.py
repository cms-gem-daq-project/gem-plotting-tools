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

    Use the dacValX_Err values stored in the input file

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
    parser.add_argument('--assignXErrors', dest='assignXErrors', action='store_true', help="Whether to assign errors for the X variable (which is actually plotted on the y-axis)")

    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    dacScanFile = r.TFile(args.infilename)

    import numpy as np
    import root_numpy as rp
    
    list_bNames = ['link']
    ohArray = rp.tree2array(tree=dacScanFile.dacScanTree, branches=list_bNames)
    ohArray = np.unique(ohArray['link'])
    
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
        
    if nameX not in nominalDacValues.keys():
        print("Error: unexpected value of nameX: '%s'"%nameX)
        exit(1)

    nominal_iref = nominalDacValues['CFG_IREF'][0]

    if nominalDacValues['CFG_IREF'][1] == 'A':
        pass
    elif nominalDacValues['CFG_IREF'][1] == 'mA':
        nominal_iref *= pow(10.0,-3)
    elif nominalDacValues['CFG_IREF'][1] == 'uA':
        nominal_iref *= pow(10.0,-6)
    elif nominalDacValues['CFG_IREF'][1] == 'nA':
        nominal_iref *= pow(10.0,-9)
    else:
        print("Error: unexpected units for nominal reference current: '%s'"%nominalDacValues['CFG_IREF'][1])
        exit(1)
     
    nominal = nominalDacValues[nameX][0]

    if nominalDacValues[nameX][1] == "V" or nominalDacValues[nameX][1] == "A":
        pass
    elif nominalDacValues[nameX][1][0] == 'm':
        nominal *= pow(10.0,-3)        
    elif nominalDacValues[nameX][1][0] == 'u':
        nominal *= pow(10.0,-6)
    elif nominalDacValues[nameX][1][0] == 'n':
        nominal *= pow(10.0,-9)
    else:
        print("Error: unexpected units: '%s'"%nominalDacValues[nameX][1])
        exit(1)

    calInfo = {}

    if args.calFileList != None:
        for line in open(args.calFileList):
            if line[0] == "#":
                continue
            line = line.strip(' ').strip('\n')
            first = line.split(' ')[0].strip(' ')
            second = line.split(' ')[1].strip(' ')
            tuple_calInfo = parseCalFile(second)
            calInfo[int(first)] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}

    #for each OH, check if calibration files were provided, if not search for the calFile in the $DATA_PATH, if it is not there, then skip that OH for the rest of the script
    for oh in ohArray:
        if oh not in calInfo.keys():
            calDacCalFile = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[oh])
            calDacCalFileExists = os.path.isfile(calDacCalFile)
            if not calDacCalFileExists:
                print("Skipping OH{0}, detector {1}, missing CFG_CAL_DAC Calibration file:\n\t{2}".format(
                    oh,
                    chamber_config[oh],
                    calDacCalFile))
                ohArray = np.delete(ohArray,(oh))

    if len(ohArray) == 0:
        print('No OHs with a calFile, exiting.')
        exit(1)
           
    # Initialize nested dictionaries
    dict_DACvsADC_Graphs = nesteddict()
    dict_RawADCvsDAC_Graphs = nesteddict()
    dict_DACvsADC_Funcs = nesteddict()

    # Initialize a TGraphErrors for each vfat
    for oh in ohArray:
        for vfat in range(0,24):
             dict_DACvsADC_Graphs[oh][vfat] = r.TGraphErrors()
             dict_RawADCvsDAC_Graphs[oh][vfat] = r.TGraphErrors()
             #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
             dict_DACvsADC_Graphs[oh][vfat].GetXaxis().SetTitle(nameY)
             dict_DACvsADC_Graphs[oh][vfat].GetYaxis().SetTitle(nameX)
             dict_RawADCvsDAC_Graphs[oh][vfat].GetXaxis().SetTitle(nameY)
             dict_RawADCvsDAC_Graphs[oh][vfat].GetYaxis().SetTitle(nameX)

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

        calibrated_ADC_value=calInfo[oh]['slope'][vfat]*event.dacValY+calInfo[oh]['intercept'][vfat]
        calibrated_ADC_error=calInfo[oh]['slope'][vfat]*event.dacValY_Err

        #from Table 29 of the VFAT3 manual, we are guessing the calibrated voltage is in mV
        calibrated_ADC_value /= 1000.0
        calibrated_ADC_error /= 1000.0
        
        #Use Ohm's law to convert the currents to voltages. The VFAT3 team told us that a 20k ohm resistor was used.
        if nominalDacValues[nameX][1][1] == "A":

            calibrated_ADC_value = calibrated_ADC_value/20000.0
            calibrated_ADC_error = calibrated_ADC_error/20000.0

            if nameX != 'CFG_IREF':
                calibrated_ADC_value -= nominal_iref 
            
        #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
        #the nameX variable is the DAC register that is scanned, and we want to determine its nominal value
        if args.assignXErrors:
            dict_DACvsADC_Graphs[oh][vfat].SetPoint(dict_DACvsADC_Graphs[oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[oh][vfat].GetN(),event.dacValY,event.dacValX)
            dict_DACvsADC_Graphs[oh][vfat].SetPointError(dict_DACvsADC_Graphs[oh][vfat].GetN()-1,calibrated_ADC_error,event.dacValX_Err)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[oh][vfat].GetN()-1,event.dacValY_Err,event.dacValX_Err)
        else:
            dict_DACvsADC_Graphs[oh][vfat].SetPoint(dict_DACvsADC_Graphs[oh][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPoint(dict_RawADCvsDAC_Graphs[oh][vfat].GetN(),event.dacValY,event.dacValX)
            dict_DACvsADC_Graphs[oh][vfat].SetPointError(dict_DACvsADC_Graphs[oh][vfat].GetN()-1,calibrated_ADC_error,0)
            dict_RawADCvsDAC_Graphs[oh][vfat].SetPointError(dict_RawADCvsDAC_Graphs[oh][vfat].GetN()-1,event.dacValY_Err,0)

    # Fit the TGraphErrors objects    
    for oh in ohArray:
        for vfat in range(0,24):
            #use a fifth degree polynomial to do the fit
            dict_DACvsADC_Funcs[oh][vfat] = r.TF1("DAC Scan Function","[0]*x^5+[1]*x^4+[2]*x^3+[3]*x^2+[4]*x+[5]")
            dict_DACvsADC_Graphs[oh][vfat].Fit(dict_DACvsADC_Funcs[oh][vfat],"Q") 

    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = {}
    dict_dacVals = nesteddict()
    for oh in ohArray:
        graph_dacVals[oh] = r.TGraph()
        for vfat in range(0,24):

            maxDacValue = 255
            
            for dacSelect in maxVfat3DACSize.keys():

                #the registers CFG_THR_ARM_DAC and CFG_THR_ZCC_DAC could correspond to voltages or currents
                #we will use voltages until a way of distinguishing the two cases is implemented 
                if dacSelect == 14 or dacSelect == 15:
                    continue
                
                if maxVfat3DACSize[dacSelect][1] == nameX:
                    maxDacValue = int(maxVfat3DACSize[dacSelect][0])
                    
            #evaluate the fitted function at the nominal current or voltage value and convert to an integer
            nominalDacValue = int(dict_DACvsADC_Funcs[oh][vfat].Eval(nominal))
            
            if nominalDacValue > maxDacValue:
                print('Warning: the nominal DAC value that was found from the fit is larger than the maximum value that the DAC register will hold')

            if nominalDacValue < 0:
                print('Warning: the nominal DAC value is that was found from the fit is less than 0')                
            
            dict_dacVals[oh][vfat] = int(dict_DACvsADC_Funcs[oh][vfat].Eval(nominal))
            graph_dacVals[oh].SetPoint(graph_dacVals[oh].GetN(),vfat,dict_dacVals[oh][vfat])
             
    # Write out the dacVal results to a root file, a text file, and the terminal
    outputTxtFiles_dacVals = {}    
            
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
            outputFiles[oh].cd()
            outputFiles[oh].mkdir("VFAT"+str(vfat))
            outputFiles[oh].cd("VFAT"+str(vfat))
            dict_DACvsADC_Graphs[oh][vfat].Write("DACvsADC")
            outputFiles[oh].cd("../")
            outputTxtFiles_dacVals[oh].write(str(vfat)+"\t"+str(dict_dacVals[oh][vfat])+"\n")
            print("| {0} | {1}  | {2} | ".format(
                oh,
                vfat,
                dict_dacVals[oh][vfat]
            ))

    # Make plots        
    for oh in ohArray:
        canv_Summary = make3x8Canvas('canv_Summary',dict_DACvsADC_Graphs[oh],'AP',dict_DACvsADC_Funcs[oh],'')
        if scandate == 'noscandate':
            canv_Summary.SaveAs(elogPath+"/"+chamber_config[oh]+"/Summary.png")
        else:
            canv_Summary.SaveAs(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/Summary.png")
