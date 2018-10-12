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
  
    Provide a file containing a list of calFiles in the format: 
    OH1 calFileOH1
    OH2 calFileOH2
    OH3 calFileOH3

.. option:: --outfilename

    Name of the output root file. Default is DACFitData.root.

Example
-------

.. code-block:: bash

    anaDACScan.py /afs/cern.ch/user/d/dorney/public/v3Hack/dacScanV3.root  --calFileList calibration.txt --assignXErrors


Environment
-----------


Internals
---------


"""

if __name__ == '__main__':

    import ROOT as r
    
    from gempython.gemplotting.utils.anautilities import parseCalFile
    from gempython.utils.nesteddict import nesteddict
    from gempython.gemplotting.utils.anautilities import make3x8Canvas
    
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', type=str, help="Filename from which input information is read", metavar='infilename')
    parser.add_argument("calFileFile", type=str, help="File specifying which calFile to use for each OH. Format: OH1 filenameOH1 <newline> OH2 filenameOH2 <newline> etc", metavar="calFileFile")
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
    
    # Determine which links present
    list_bNames = ['link']
    ohArray = rp.tree2array(tree=dacScanFile.dacScanTree, branches=list_bNames)
    ohArray = np.unique(ohArray['link'])

    # Determine which DAC was scanned and against which ADC
    nameX = ""
    nameY = ""
    for event in dacScanFile.dacScanTree:
        nameX = event.nameX.data()
        nameY = event.nameY.data()
        break # all entries will be the same

    if nameY not in ['ADC0', 'ADC1']:
        print("Error: unexpected value of nameY: '%s'"%nameY)
        exit(1)

    calInfo = {}

    for line in open(args.calFileFile):
        line = line.strip(' ').strip('\n')
        first = line.split(' ')[0].strip(' ')
        second = line.split(' ')[1].strip(' ')
        tuple_calInfo = parseCalFile(second)
        calInfo[int(first)] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}
        
    # Initialize nested dictionaries
    dict_dacScanResults = nesteddict()
    dict_dacScanFuncs = nesteddict()

    # Initialize a TGraphErrors for each vfat
    for link in ohArray:
        for vfat in range(0,24):
             dict_dacScanResults[link][vfat] = r.TGraphErrors()

    outputFiles = {}         
             
    for link in ohArray:         
        outputFiles[link] = r.TFile("$DATA_PATH/"+chamber_config[link]+"/dacScans/scandate/"+args.outfilename,'recreate')
             
    # Loop over events in the tree and fill plots
    for event in dacScanFile.dacScanTree:
        link = event.link
        vfat = event.vfatN

        if link not in calInfo.keys():
            print('Error: calibration file for link %i was not provided'%link)
            exit(1)
        
        calibrated_DAC_value=calInfo[link]['slope'][vfat]*event.dacValX+calInfo[link]['intercept'][vfat]
        calibrated_DAC_error=calInfo[link]['slope'][vfat]*event.dacValX_Err+calInfo[link]['intercept'][vfat]
        
        if args.assignXErrors:
            dict_dacScanResults[link][vfat].SetPoint(dict_dacScanResults[link][vfat].GetN(),event.dacValY,calibrated_DAC_value)
            dict_dacScanResults[link][vfat].SetPointError(dict_dacScanResults[link][vfat].GetN()-1,event.dacValY_Err,calibrated_DAC_error)
        else:    
            dict_dacScanResults[link][vfat].SetPoint(dict_dacScanResults[link][vfat].GetN(),event.dacValY,calibrated_DAC_value)
            dict_dacScanResults[link][vfat].SetPointError(dict_dacScanResults[link][vfat].GetN()-1,event.dacValY_Err,0)

    # Fit the TGraphErrors objects    
    for oh in ohArray:
        for vfat in range(0,24):
            dict_dacScanFuncs[oh][vfat] = r.TF1("DAC Scan Function","[0]*x+[1]")
            dict_dacScanResults[oh][vfat].Fit(dict_dacScanFuncs[oh][vfat]) 

    nominal = -1        

    #from Tables 9 and 10 of the VFAT3 manual 
    if nameX == "CFG_THR_ARM_DAC":
        nominal = 3.2
    else:
        print("Error: unexpected value of nameX: '%s'"%nameX)
        exit(1)
        
    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = {}
    dict_dacVals = nesteddict()
    for oh in ohArray:
        graph_dacVals[oh] = r.TGraph()
        for vfat in range(0,24):
             dict_dacVals[oh][vfat] = dict_dacScanResults[oh][vfat].Eval(nominal)
             graph_dacVals[oh].SetPoint(graph_dacVals[oh].GetN(),vfat,dict_dacVals[oh][vfat]) 

    # Write out the dacVal results to both a file and the terminal         
    print( "| OH | vfatN | dacVal |")
    print( "| -- | ----- | ------ |")        
    
    for oh in ohArray:
        outputFiles[oh].cd()
        graph_dacVals[oh].Write("dacValsOH"+str(oh))
        for vfat in range(0,24):
            print("| {0} | {1}  | {2} | ".format(
                oh,
                vfat,
                dict_dacVals[oh][vfat]
            ))
        
    # Make plots        
    for oh in ohArray:
        canv_Summary = make3x8Canvas('canv_Summary',dict_dacScanResults[oh],'AP',dict_dacScanFuncs[oh],'')
        canv_Summary.SaveAs("$DATA_PATH/"+chamber_config[oh]+"/dacScans/scandate/SummaryOH"+str(oh)+".png")
        outputFiles[oh].cd()
        canv_Summary.Write()
