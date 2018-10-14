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
    dict_dacScanResults = nesteddict()
    dict_dacScanFuncs = nesteddict()

    # Initialize a TGraphErrors for each vfat
    for oh in ohArray:
        for vfat in range(0,24):
             dict_dacScanResults[oh][vfat] = r.TGraphErrors()
             #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
             dict_dacScanResults[oh][vfat].GetXaxis().SetTitle(nameY)
             dict_dacScanResults[oh][vfat].GetYaxis().SetTitle(nameX)

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

        #the reversal of x and y is intended - we want to plot the nameX variable on the y-axis and the nameY variable on the x-axis
        calibrated_DAC_value=calInfo[oh]['slope'][vfat]*event.dacValX+calInfo[oh]['intercept'][vfat]
        calibrated_DAC_error=calInfo[oh]['slope'][vfat]*event.dacValX_Err+calInfo[oh]['intercept'][vfat]

        if args.assignXErrors:
            dict_dacScanResults[oh][vfat].SetPoint(dict_dacScanResults[oh][vfat].GetN(),event.dacValY,calibrated_DAC_value)
            dict_dacScanResults[oh][vfat].SetPointError(dict_dacScanResults[oh][vfat].GetN()-1,event.dacValY_Err,calibrated_DAC_error)
        else:    
            dict_dacScanResults[oh][vfat].SetPoint(dict_dacScanResults[oh][vfat].GetN(),event.dacValY,calibrated_DAC_value)
            dict_dacScanResults[oh][vfat].SetPointError(dict_dacScanResults[oh][vfat].GetN()-1,event.dacValY_Err,0)

    # Fit the TGraphErrors objects    
    for oh in ohArray:
        for vfat in range(0,24):
            dict_dacScanFuncs[oh][vfat] = r.TF1("DAC Scan Function","[0]*x+[1]")
            dict_dacScanResults[oh][vfat].Fit(dict_dacScanFuncs[oh][vfat],"Q") 

    nominal = -1        

    #from Tables 9 and 10 of the VFAT3 manual 
    if nameX == "CFG_THR_ARM_DAC":
        nominal = 3.2
    else:
        print("Error: unexpected value of nameX: '%s'"%nameX)
        exit(1)
        
    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = {}
    tree_dacVals = {}
    dict_dacVals = nesteddict()
    for oh in ohArray:
        graph_dacVals[oh] = r.TGraph()
        tree_dacVals[oh] = r.TTree()
        vfatN_branch = np.zeros(1, dtype=int)
        dacVal_branch = np.zeros(1, dtype=int)
        tree_dacVals[oh].Branch('vfatN',vfatN_branch,'vfatN/i')
        tree_dacVals[oh].Branch('dacVal',dacVal_branch,'dacVal/i')
        for vfat in range(0,24):
             dict_dacVals[oh][vfat] = dict_dacScanResults[oh][vfat].Eval(nominal)
             graph_dacVals[oh].SetPoint(graph_dacVals[oh].GetN(),vfat,dict_dacVals[oh][vfat])
             vfatN_branch[0] = vfat
             dacVal_branch[0] = dict_dacVals[oh][vfat]
             tree_dacVals[oh].Fill() 
             
    # Write out the dacVal results to both a file and the terminal         
    print( "| OH | vfatN | dacVal |")
    print( "| :-: | :---: | :----: |")        
    
    for oh in ohArray:
        outputFiles[oh].cd()
        graph_dacVals[oh].Write("dacValsOH"+str(oh))
        tree_dacVals[oh].Write("dacValsOH"+str(oh))
        for vfat in range(0,24):
            print("| {0} | {1}  | {2} | ".format(
                oh,
                vfat,
                dict_dacVals[oh][vfat]
            ))
        
    # Make plots        
    for oh in ohArray:
        canv_Summary = make3x8Canvas('canv_Summary',dict_dacScanResults[oh],'AP',dict_dacScanFuncs[oh],'')
        if scandate == 'noscandate':
            canv_Summary.SaveAs(elogPath+"/"+chamber_config[oh]+"/SummaryOH"+str(oh)+".png")
        else:
            canv_Summary.SaveAs(dataPath+"/"+chamber_config[oh]+"/dacScans/"+scandate+"/SummaryOH"+str(oh)+".png")
        outputFiles[oh].cd()
        canv_Summary.Write()
