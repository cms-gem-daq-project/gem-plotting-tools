#!/bin/env python

# -*- coding: utf-8 -*-
"""

@author: Anastasia and Cameron Bravo (c.bravo@cern.ch)
         Brian Dorney (brian.l.dorney@cern.ch)

"""
import numpy as np
import os

from anaoptions import parser
from array import array
from gempython.utils.nesteddict import nesteddict as ndict

parser.set_defaults(outfilename="LatencyData.root")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outputfilename = options.outfilename

import ROOT as r
r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(1111111)
inF = r.TFile(filename+'.root',"READ")

#Initializing Histograms
print 'Initializing Histograms'
dict_hVFATHitsVsLat = ndict()
for vfat in range(0,24):
    dict_hVFATHitsVsLat[vfat]   = r.TH1F("vfat%iHitsVsLat"%vfat,"vfat%i"%vfat,256,-0.5,255.5)
    pass

#Filling Histograms
print 'Filling Histograms'
latMin = 1000
latMax = -1
for event in inF.latTree:
    dict_hVFATHitsVsLat[int(event.vfatN)].Fill(event.lat,event.Nhits)
    if event.lat < latMin and event.Nhits > 0:
        latMin = event.lat
        pass
    elif event.lat > latMax:
        latMax = event.lat
        pass
    pass

from math import sqrt
outF = r.TFile(filename+"/"+options.outfilename,"RECREATE")
dict_grNHitsVFAT = ndict()
dict_fitNHitsVFAT = ndict()
grNMaxLatBinByVFAT = r.TGraphAsymmErrors(len(dict_hVFATHitsVsLat))
grMaxLatBinByVFAT = r.TGraphAsymmErrors(len(dict_hVFATHitsVsLat))
grVFATSigOverSigPBkg = r.TGraphAsymmErrors(len(dict_hVFATHitsVsLat))
r.gStyle.SetOptStat(0)
canv_Summary = r.TCanvas("canv_Summary","Latency Summary",500*8,500*3)
canv_Summary.Divide(8,3)
for vfat in dict_hVFATHitsVsLat:
    #Store Max Info
    NMaxLatBin = dict_hVFATHitsVsLat[vfat].GetBinContent(dict_hVFATHitsVsLat[vfat].GetMaximumBin())
    grNMaxLatBinByVFAT.SetPoint(vfat, vfat, NMaxLatBin)
    grNMaxLatBinByVFAT.SetPointError(vfat, 0, 0, sqrt(NMaxLatBin), sqrt(NMaxLatBin))

    grMaxLatBinByVFAT.SetPoint(vfat, vfat, dict_hVFATHitsVsLat[vfat].GetBinCenter(dict_hVFATHitsVsLat[vfat].GetMaximumBin()))
    grMaxLatBinByVFAT.SetPointError(vfat, 0, 0, 0.5, 0.5) #could be improved upon

    #Initialize
    dict_fitNHitsVFAT[vfat] = r.TF1("vfat%iFitHitsVsLat"%vfat,"[0]",latMin,latMax)
    dict_grNHitsVFAT[vfat] = r.TGraphAsymmErrors(dict_hVFATHitsVsLat[vfat])
    dict_grNHitsVFAT[vfat].SetName("lat%i_ga"%vfat)
    
    #Fit
    canv_fit = r.TCanvas("canv_fit%i"%vfat,"Fit VFAT%i"%vfat,500,500)
    dict_fitNHitsVFAT[vfat].SetParameter(0, 0.0005)
    dict_grNHitsVFAT[vfat].Fit(dict_fitNHitsVFAT[vfat],"QR")
    dict_hVFATHitsVsLat[vfat].Fit(dict_fitNHitsVFAT[vfat],"QR")

    error_SigOverSigPBkg = sqrt( (sqrt(NMaxLatBin) / dict_fitNHitsVFAT[vfat].GetParameter(0) )**2 + ( (dict_fitNHitsVFAT[vfat].GetParError(0) * NMaxLatBin ) / dict_fitNHitsVFAT[vfat].GetParameter(0)**2 )**2)
    grVFATSigOverSigPBkg.SetPoint(vfat, vfat, NMaxLatBin / dict_fitNHitsVFAT[vfat].GetParameter(0) )
    grVFATSigOverSigPBkg.SetPointError(vfat, 0, 0, error_SigOverSigPBkg, error_SigOverSigPBkg)

    #Draw
    r.gStyle.SetOptStat(0)
    canv_Summary.cd(vfat+1)
    dict_grNHitsVFAT[vfat].SetMarkerStyle(21)
    dict_grNHitsVFAT[vfat].SetMarkerSize(0.7)
    dict_grNHitsVFAT[vfat].SetLineWidth(2)
    dict_grNHitsVFAT[vfat].GetXaxis().SetRangeUser(latMin, latMax)
    dict_grNHitsVFAT[vfat].GetXaxis().SetTitle("Lat")
    dict_grNHitsVFAT[vfat].GetYaxis().SetTitle("N")
    dict_grNHitsVFAT[vfat].Draw("APE1")

    #Write
    dirVFAT = outF.mkdir("VFAT%i"%vfat)
    dirVFAT.cd()
    dict_grNHitsVFAT[vfat].Write()
    dict_hVFATHitsVsLat[vfat].Write()
    dict_fitNHitsVFAT[vfat].Write()
    pass

#Store - Summary
canv_Summary.SaveAs(filename+'/Summary.png')

#Store - Sig Over (Sig + Bkg)
canv_SigOverSigPBkg = r.TCanvas("canv_SigOverSigPBkg","canv_SigOverSigPBkg",600,600)
canv_SigOverSigPBkg.cd()
grVFATSigOverSigPBkg.SetTitle("")
grVFATSigOverSigPBkg.SetMarkerStyle(21)
grVFATSigOverSigPBkg.SetMarkerSize(0.7)
grVFATSigOverSigPBkg.SetLineWidth(2)    
grVFATSigOverSigPBkg.GetXaxis().SetTitle("VFAT Pos")
grVFATSigOverSigPBkg.GetYaxis().SetTitle("Sig / (Sig+Bkg)")
grVFATSigOverSigPBkg.GetYaxis().SetTitleOffset(1.2)
grVFATSigOverSigPBkg.GetYaxis().SetRangeUser(0,20)
grVFATSigOverSigPBkg.GetXaxis().SetRangeUser(-0.5,24.5)
grVFATSigOverSigPBkg.Draw("APE1")
canv_SigOverSigPBkg.SaveAs(filename+'/SignalOverSigPBkg.png')

#Store - Max Hits By Lat Per VFAT
canv_MaxHitsPerLatByVFAT = r.TCanvas("canv_MaxHitsPerLatByVFAT","canv_MaxHitsPerLatByVFAT",1200,600)
canv_MaxHitsPerLatByVFAT.Divide(2,1)
canv_MaxHitsPerLatByVFAT.cd(1)
grNMaxLatBinByVFAT.SetTitle("")
grNMaxLatBinByVFAT.SetMarkerStyle(21)
grNMaxLatBinByVFAT.SetMarkerSize(0.7)
grNMaxLatBinByVFAT.SetLineWidth(2)    
grNMaxLatBinByVFAT.GetXaxis().SetTitle("VFAT Pos")
grNMaxLatBinByVFAT.GetYaxis().SetTitle("Hit Count of Max Lat Bin")
grNMaxLatBinByVFAT.GetYaxis().SetTitleOffset(1.7)
grNMaxLatBinByVFAT.GetXaxis().SetRangeUser(-0.5,24.5)
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

#Store - TObjects
outF.cd()
grNMaxLatBinByVFAT.SetName("grNMaxLatBinByVFAT")
grNMaxLatBinByVFAT.Write()
grMaxLatBinByVFAT.SetName("grMaxLatBinByVFAT")
grMaxLatBinByVFAT.Write()
grVFATSigOverSigPBkg.SetName("grVFATSigOverSigPBkg")
grVFATSigOverSigPBkg.Write()
outF.Close()
