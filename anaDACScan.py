#!/bin/env python

"""
anaDACScan
==============
"""

import argparse
import numpy as np
import root_numpy as rp
import ROOT as r

from gempython.gemplotting.utils.anautilities import parseCalFile

from gempython.utils.nesteddict import nesteddict

from gempython.gemplotting.utils.anautilities import make3x8Canvas

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', metavar='infilename', type=str, help="Filename from which input information is read")
#    parser.add_argument("calFile", metavar="calFile", type=str,help="File specifying CAL_DAC/VCAL to fC equations per VFAT")
    parser.add_argument('-o','--outfilename', metavar='outfilename', type=str, help="Filename to which output information is written", default="DACFitData.root")

    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    dacScanFile = r.TFile(args.infilename)
    
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

    # Initialize nested dictionaries
    dict_dacScanResults = nesteddict()
    dict_dacScanFuncs = nesteddict()

    # Get ADC0 or ADC1 calibration
    # tuple_calInfo = parseCalFile(args.calFile)
    
    # Initialize a TGraphErrors for each vfat
    for link in ohArray:
        for vfat in range(0,24):
             dict_dacScanResults[link][vfat] = r.TGraphErrors()
             
    # Loop over events in the tree and fill plots         
    for event in dacScanFile.dacScanTree:
        link = event.link
        vfat = event.vfatN

        dict_dacScanResults[link][vfat].SetPoint(dict_dacScanResults[link][vfat].GetN(),event.dacValY,event.dacValX)
        dict_dacScanResults[link][vfat].SetPointError(dict_dacScanResults[link][vfat].GetN()-1,event.dacValY_Err,event.dacValX_Err)

    # Fit the TGraphErrors objects    
    for oh in ohArray:
        for vfat in range(0,24):
            dict_dacScanFuncs[oh][vfat] = r.TF1("DAC Scan Function","[0]*x+[1]")
            dict_dacScanResults[oh][vfat].Fit(dict_dacScanFuncs[oh][vfat]) 

    # Determine DAC values to achieve recommended bias voltage and current settings        

    # Make plots        
    for oh in ohArray:
        canv_Summary = make3x8Canvas('canv_Summary',dict_dacScanResults[oh],'AP',dict_dacScanFuncs[oh],'')
        canv_Summary.SaveAs("SummaryOH"+str(oh)+".png")
