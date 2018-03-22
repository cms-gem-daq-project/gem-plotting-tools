#!/bin/env python

# -*- coding: utf-8 -*-
"""

@author: Anastasia and Cameron Bravo (c.bravo@cern.ch)
         Brian Dorney (brian.l.dorney@cern.ch)

"""
import numpy as np
import os

from anaoptions import parser
from anautilities import make3x8Canvas
from array import array
from gempython.utils.nesteddict import nesteddict as ndict

parser.add_option("-f", "--fit", action="store_true", dest="performFit",
                  help="Fit the latency distributions", metavar="performFit")
parser.add_option("--latSigRange", type="string", dest="latSigRange", default=None,
                  help="Comma separated pair of values defining expected signal range, e.g. lat #epsilon [41,43] is signal", metavar="latSigRange")
parser.add_option("--latSigMaskRange", type="string", dest="latSigMaskRange", default=None,
                  help="Comma separated pair of values defining the region to be masked when trying to fit the noise, e.g. lat #notepsilon [40,44] is noise (lat < 40 || lat > 44)", 
                  metavar="latSigMaskRange")

parser.set_defaults(outfilename="latencyAna.root")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outputfilename = options.outfilename

import ROOT as r
r.TH1.SetDefaultSumw2(False)
r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(1111111)
inF = r.TFile(filename+'.root',"READ")

#Initializing Histograms
print 'Initializing Histograms'
dict_hVFATHitsVsLat = ndict()
for vfat in range(0,24):
    #dict_hVFATHitsVsLat[vfat]   = r.TH1F("vfat%iHitsVsLat"%vfat,"vfat%i"%vfat,256,-0.5,255.5)
    dict_hVFATHitsVsLat[vfat]   = r.TH1F("vfat%iHitsVsLat"%vfat,"vfat%i"%vfat,1024,-0.5,1023.5)
    pass

#Filling Histograms
print 'Filling Histograms'
latMin = 1000
latMax = -1
nTrig = -1
dict_vfatID = dict((vfat, 0) for vfat in range(0,24))
listOfBranches = inF.latTree.GetListOfBranches()
for event in inF.latTree:
    dict_hVFATHitsVsLat[int(event.vfatN)].Fill(event.latency,event.Nhits)
    if event.latency < latMin and event.Nhits > 0:
        latMin = event.latency
        pass
    elif event.latency > latMax:
        latMax = event.latency
        pass

    if not (dict_vfatID[event.vfatN] > 0):
        if 'vfatID' in listOfBranches:
            dict_vfatID[event.vfatN] = event.vfatID
        else:
            dict_vfatID[event.vfatN] = 0

    if nTrig < 0:
        nTrig = event.Nev
        pass
    pass

from math import sqrt
for vfat in range(0,24):
    for binX in range(1, dict_hVFATHitsVsLat[vfat].GetNbinsX()+1):
        dict_hVFATHitsVsLat[vfat].SetBinError(binX, sqrt(dict_hVFATHitsVsLat[vfat].GetBinContent(binX)))

hHitsVsLat_AllVFATs = dict_hVFATHitsVsLat[0].Clone("hHitsVsLat_AllVFATs")
hHitsVsLat_AllVFATs.SetTitle("Sum over all VFATs")
for vfat in range(1,24):
    hHitsVsLat_AllVFATs.Add(dict_hVFATHitsVsLat[vfat])

# Set Latency Fitting Bounds - Signal
latFitMin_Sig = latMin
latFitMax_Sig = latMax
if options.latSigRange is not None:
    listLatValues = map(lambda val: float(val), options.latSigRange.split(","))
    if len(listLatValues) != 2:
        print "You must specify exactly two values for determining the latency signal range"
        print "I was given:", listLatValues
        print "Please cross-check"
        exit(os.EX_USAGE)
    else: 
        latFitMin_Sig = min(listLatValues)
        latFitMax_Sig = max(listLatValues)

# Set Latency Fitting Bounds - Noise
latFitMin_Noise = latFitMin_Sig - 1
latFitMax_Noise = latFitMax_Sig + 1
if options.latSigMaskRange is not None:
    listLatValues = map(lambda val: float(val), options.latSigMaskRange.split(","))
    if len(listLatValues) != 2:
        print "You must specify exactly two values for determining the latency noise range"
        print "I was given:", listLatValues
        print "Please cross-check"
        exit(os.EX_USAGE)
    else: 
        latFitMin_Noise = min(listLatValues)
        latFitMax_Noise = max(listLatValues)

# Make output TFile and TTree
outF = r.TFile(filename+"/"+options.outfilename,"RECREATE")
dirVFATPlots = outF.mkdir("VFAT_Plots")
myT = r.TTree('latFitTree','Tree Holding FitData')
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatID = array( 'i', [-1] )
myT.Branch( 'vfatID', vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT
hitCountMaxLat = array( 'f', [ 0 ] )
myT.Branch( 'hitCountMaxLat', hitCountMaxLat, 'hitCountMaxLat/F' )
hitCountMaxLatErr = array( 'f', [ 0 ] )
myT.Branch( 'hitCountMaxLatErr', hitCountMaxLatErr, 'hitCountMaxLatErr/F' )
maxLatBin = array( 'f', [ 0 ] )
myT.Branch( 'maxLatBin', maxLatBin, 'maxLatBin/F' )
hitCountBkg = array( 'f', [ 0 ] )
hitCountBkgErr = array( 'f', [ 0 ] )
hitCountSig = array( 'f', [ 0 ] )
hitCountSigErr = array( 'f', [ 0 ] )
SigOverBkg = array( 'f', [ 0 ] )
SigOverBkgErr = array( 'f', [ 0 ] )
if options.performFit:
    myT.Branch( 'hitCountBkg', hitCountBkg, 'hitCountBkg/F')
    myT.Branch( 'hitCountBkgErr', hitCountBkgErr, 'hitCountBkgErr/F')
    myT.Branch( 'hitCountSig', hitCountSig, 'hitCountSig/F')
    myT.Branch( 'hitCountSigErr', hitCountSigErr, 'hitCountSigErr/F')
    myT.Branch( 'SigOverBkg', SigOverBkg, 'SigOverBkg/F')
    myT.Branch( 'SigOverBkgErr', SigOverBkgErr, 'SigOverBkgErr/F')

# Make output plots
from math import sqrt
dict_grNHitsVFAT = ndict()
dict_fitNHitsVFAT_Sig = ndict()
dict_fitNHitsVFAT_Noise = ndict()
grNMaxLatBinByVFAT = r.TGraphErrors(len(dict_hVFATHitsVsLat))
grMaxLatBinByVFAT = r.TGraphErrors(len(dict_hVFATHitsVsLat))
grVFATSigOverBkg = r.TGraphErrors(len(dict_hVFATHitsVsLat))
grVFATNSignalNoBkg = r.TGraphErrors(len(dict_hVFATHitsVsLat))
r.gStyle.SetOptStat(0)
if options.debug and options.performFit:
    print "VFAT\tSignalHits\tSignal/Noise"
for vfat in dict_hVFATHitsVsLat:
    # Store VFAT info
    vfatN[0] = vfat
    vfatID[0] = dict_vfatID[vfat]

    # Store Max Info
    hitCountMaxLat[0] = dict_hVFATHitsVsLat[vfat].GetBinContent(dict_hVFATHitsVsLat[vfat].GetMaximumBin())
    hitCountMaxLatErr[0] = sqrt(hitCountMaxLat[0])
    grNMaxLatBinByVFAT.SetPoint(vfat, vfat, hitCountMaxLat[0])
    grNMaxLatBinByVFAT.SetPointError(vfat, 0, hitCountMaxLatErr[0])

    maxLatBin[0] = dict_hVFATHitsVsLat[vfat].GetBinCenter(dict_hVFATHitsVsLat[vfat].GetMaximumBin())
    grMaxLatBinByVFAT.SetPoint(vfat, vfat, maxLatBin[0])
    grMaxLatBinByVFAT.SetPointError(vfat, 0, 0.5) #could be improved upon

    # Initialize
    dict_fitNHitsVFAT_Sig[vfat] = r.TF1("func_N_vs_Lat_VFAT%i_Sig"%vfat,"[0]",latFitMin_Sig,latFitMax_Sig)
    dict_fitNHitsVFAT_Noise[vfat] = r.TF1("func_N_vs_Lat_VFAT%i_Noise"%vfat,"[0]",latMin,latMax)
    dict_grNHitsVFAT[vfat] = r.TGraphAsymmErrors(dict_hVFATHitsVsLat[vfat])
    dict_grNHitsVFAT[vfat].SetName("g_N_vs_Lat_VFAT%i"%vfat)
    
    # Fitting
    if options.performFit:
        # Fit Signal
        dict_fitNHitsVFAT_Sig[vfat].SetParameter(0, hitCountMaxLat[0])
        dict_fitNHitsVFAT_Sig[vfat].SetLineColor(r.kGreen+1)
        dict_grNHitsVFAT[vfat].Fit(dict_fitNHitsVFAT_Sig[vfat],"QR")

        # Remove Signal Region
        latVal = r.Double()
        hitVal = r.Double()
        gTempDist = dict_grNHitsVFAT[vfat].Clone("g_N_vs_Lat_VFAT%i_NoSig"%vfat)
        for idx in range(dict_grNHitsVFAT[vfat].GetN()-1,0,-1):
            gTempDist.GetPoint(idx,latVal,hitVal)
            if latFitMin_Noise < latVal and latVal < latFitMax_Noise:
                gTempDist.RemovePoint(idx)

        # Fit Noise
        dict_fitNHitsVFAT_Noise[vfat].SetParameter(0, 0.)
        dict_fitNHitsVFAT_Noise[vfat].SetLineColor(r.kRed+1)
        gTempDist.Fit(dict_fitNHitsVFAT_Noise[vfat],"QR")

        # Calc Signal & Signal/Noise
        hitCountBkg[0] = dict_fitNHitsVFAT_Noise[vfat].GetParameter(0)
        hitCountBkgErr[0] = dict_fitNHitsVFAT_Noise[vfat].GetParError(0)
        hitCountSig[0] = dict_fitNHitsVFAT_Sig[vfat].GetParameter(0) - hitCountBkg[0]
        hitCountSigErr[0] = sqrt( (dict_fitNHitsVFAT_Sig[vfat].GetParError(0))**2 + hitCountBkgErr[0]**2)

        SigOverBkg[0] = hitCountSig[0] / hitCountBkg[0]
        SigOverBkgErr[0] = sqrt( (hitCountSigErr[0] / hitCountBkg[0])**2 + (hitCountBkgErr[0]**2 * (hitCountSig[0] / hitCountBkg[0]**2)**2) )

        # Add to Plot
        grVFATSigOverBkg.SetPoint(vfat, vfat, SigOverBkg[0] )
        grVFATSigOverBkg.SetPointError(vfat, 0, SigOverBkgErr[0] )

        grVFATNSignalNoBkg.SetPoint(vfat, vfat, hitCountSig[0] )
        grVFATNSignalNoBkg.SetPointError(vfat, 0, hitCountSigErr[0] )

        # Print if requested
        if options.debug:
            print "%i\t%f\t%f"%(vfat, hitCountSig[0], SigOverBkg[0])
        pass

    # Format
    r.gStyle.SetOptStat(0)
    dict_grNHitsVFAT[vfat].SetMarkerStyle(21)
    dict_grNHitsVFAT[vfat].SetMarkerSize(0.7)
    dict_grNHitsVFAT[vfat].SetLineWidth(2)
    dict_grNHitsVFAT[vfat].GetXaxis().SetRangeUser(latMin, latMax)
    dict_grNHitsVFAT[vfat].GetXaxis().SetTitle("Lat")
    dict_grNHitsVFAT[vfat].GetYaxis().SetRangeUser(0, nTrig)
    dict_grNHitsVFAT[vfat].GetYaxis().SetTitle("N")

    # Write
    dirVFAT = dirVFATPlots.mkdir("VFAT%i"%vfat)
    dirVFAT.cd()
    dict_grNHitsVFAT[vfat].Write()
    dict_hVFATHitsVsLat[vfat].Write()
    if options.performFit:
        dict_fitNHitsVFAT_Sig[vfat].Write()
        dict_fitNHitsVFAT_Noise[vfat].Write()
    myT.Fill()
    pass

# Store - Summary
if options.performFit:
    canv_Summary = make3x8Canvas('canv_Summary', dict_grNHitsVFAT, 'APE1', dict_fitNHitsVFAT_Noise, '')
    canv_Summary.SaveAs(filename+'/Summary.png')
else:
    canv_Summary = make3x8Canvas('canv_Summary', dict_grNHitsVFAT, 'APE1')
    canv_Summary.SaveAs(filename+'/Summary.png')

# Store - Sig Over Bkg
if options.performFit:
    canv_SigOverBkg = r.TCanvas("canv_SigOverBkg","canv_SigOverBkg",600,600)
    canv_SigOverBkg.cd()
    canv_SigOverBkg.cd().SetLogy()
    canv_SigOverBkg.cd().SetGridy()
    grVFATSigOverBkg.SetTitle("")
    grVFATSigOverBkg.SetMarkerStyle(21)
    grVFATSigOverBkg.SetMarkerSize(0.7)
    grVFATSigOverBkg.SetLineWidth(2)    
    grVFATSigOverBkg.GetXaxis().SetTitle("VFAT Pos")
    grVFATSigOverBkg.GetYaxis().SetTitle("Sig / Bkg)")
    grVFATSigOverBkg.GetYaxis().SetTitleOffset(1.25)
    grVFATSigOverBkg.GetYaxis().SetRangeUser(1e-1,1e2)
    grVFATSigOverBkg.GetXaxis().SetRangeUser(-0.5,24.5)
    grVFATSigOverBkg.Draw("APE1")
    canv_SigOverBkg.SaveAs(filename+'/SignalOverBkg.png')

# Store - Signal
if options.performFit:
    canv_Signal = r.TCanvas("canv_Signal","canv_Signal",600,600)
    canv_Signal.cd()
    grVFATNSignalNoBkg.SetTitle("")
    grVFATNSignalNoBkg.SetMarkerStyle(21)
    grVFATNSignalNoBkg.SetMarkerSize(0.7)
    grVFATNSignalNoBkg.SetLineWidth(2)    
    grVFATNSignalNoBkg.GetXaxis().SetTitle("VFAT Pos")
    grVFATNSignalNoBkg.GetYaxis().SetTitle("Signal Hits")
    grVFATNSignalNoBkg.GetYaxis().SetTitleOffset(1.5)
    grVFATNSignalNoBkg.GetYaxis().SetRangeUser(0,nTrig)
    grVFATNSignalNoBkg.GetXaxis().SetRangeUser(-0.5,24.5)
    grVFATNSignalNoBkg.Draw("APE1")
    canv_Signal.SaveAs(filename+'/SignalNoBkg.png')

# Store - Sum over all VFATs
canv_LatSum = r.TCanvas("canv_LatSumOverAllVFATs","canv_LatSumOverAllVFATs",600,600)
canv_LatSum.cd()
hHitsVsLat_AllVFATs.SetXTitle("Latency")
hHitsVsLat_AllVFATs.SetYTitle("N")
hHitsVsLat_AllVFATs.GetXaxis().SetRangeUser(latMin,latMax)
hHitsVsLat_AllVFATs.Draw("hist")
canv_LatSum.SaveAs(filename + '/LatSumOverAllVFATs.png')

# Store - Max Hits By Lat Per VFAT
canv_MaxHitsPerLatByVFAT = r.TCanvas("canv_MaxHitsPerLatByVFAT","canv_MaxHitsPerLatByVFAT",1200,600)
canv_MaxHitsPerLatByVFAT.Divide(2,1)
canv_MaxHitsPerLatByVFAT.cd(1)
grNMaxLatBinByVFAT.SetTitle("")
grNMaxLatBinByVFAT.SetMarkerStyle(21)
grNMaxLatBinByVFAT.SetMarkerSize(0.7)
grNMaxLatBinByVFAT.SetLineWidth(2)    
grNMaxLatBinByVFAT.GetXaxis().SetRangeUser(-0.5,24.5)
grNMaxLatBinByVFAT.GetXaxis().SetTitle("VFAT Pos")
grNMaxLatBinByVFAT.GetYaxis().SetRangeUser(0,nTrig)
grNMaxLatBinByVFAT.GetYaxis().SetTitle("Hit Count of Max Lat Bin")
grNMaxLatBinByVFAT.GetYaxis().SetTitleOffset(1.7)
grNMaxLatBinByVFAT.Draw("APE1")
canv_MaxHitsPerLatByVFAT.cd(2)
grMaxLatBinByVFAT.SetTitle("")
grMaxLatBinByVFAT.SetMarkerStyle(21)
grMaxLatBinByVFAT.SetMarkerSize(0.7)
grMaxLatBinByVFAT.SetLineWidth(2)    
grMaxLatBinByVFAT.GetXaxis().SetTitle("VFAT Pos")
grMaxLatBinByVFAT.GetYaxis().SetTitle("Max Lat Bin")
grMaxLatBinByVFAT.GetYaxis().SetTitleOffset(1.2)
grMaxLatBinByVFAT.GetXaxis().SetRangeUser(-0.5,24.5)
grMaxLatBinByVFAT.Draw("APE1")
canv_MaxHitsPerLatByVFAT.SaveAs(filename+'/MaxHitsPerLatByVFAT.png')

# Store - TObjects
outF.cd()
hHitsVsLat_AllVFATs.Write()
grNMaxLatBinByVFAT.SetName("grNMaxLatBinByVFAT")
grNMaxLatBinByVFAT.Write()
grMaxLatBinByVFAT.SetName("grMaxLatBinByVFAT")
grMaxLatBinByVFAT.Write()
if options.performFit:
    grVFATSigOverBkg.SetName("grVFATSigOverBkg")
    grVFATSigOverBkg.Write()
    grVFATNSignalNoBkg.SetName("grVFATNSignalNoBkg")
    grVFATNSignalNoBkg.Write()
myT.Write()
outF.Close()
