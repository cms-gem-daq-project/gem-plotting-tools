#!/usr/bin/env python

"""
anaDACScan
==============
"""
import ROOT as r

from gempython.gemplotting.utils.anautilities import parseCalFile
from gempython.utils.nesteddict import nesteddict
from gempython.gemplotting.utils.anautilities import make3x8Canvas

import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', type=str, help="Filename from which input information is read", metavar='infilename')
    parser.add_argument("calFile", type=str, help="File specifying conversion between DAC to physical units per VFAT", metavar="calFile")
    parser.add_argument('-o','--outfilename', dest='outfilename', type=str, default="DACFitData.root", help="Filename to which output information is written", metavar='outfilename')
    parser.add_argument('--assignXErrors', dest='assignXErrors', action='store_true', help="Whether to assign errors for the X variable (which is actually plotted on the y-axis)")

    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    dacScanFile = r.TFile(args.infilename)

    outputFile = r.TFile(args.outfilename,'recreate')

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
    
    tuple_calInfo = parseCalFile(args.calFile)
    calDAC_Slope = tuple_calInfo[0]
    calDAC_Intercept = tuple_calInfo[1]

    # Initialize nested dictionaries
    dict_dacScanResults = nesteddict()
    dict_dacScanFuncs = nesteddict()

    # Initialize a TGraphErrors for each vfat
    for link in ohArray:
        for vfat in range(0,24):
             dict_dacScanResults[link][vfat] = r.TGraphErrors()
             
    # Loop over events in the tree and fill plots
    for event in dacScanFile.dacScanTree:
        link = event.link
        vfat = event.vfatN

        calibrated_DAC_value=calDAC_Slope[vfat]*event.dacValX+calDAC_Intercept[vfat]
        calibrated_DAC_error=calDAC_Slope[vfat]*event.dacValX_Err+calDAC_Intercept[vfat]
        
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
        outputFile.cd()
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
        canv_Summary.SaveAs("SummaryOH"+str(oh)+".png")
        outputFile.cd()
        canv_Summary.Write()
