#!/bin/env python

# -*- coding: utf-8 -*-
"""

@author: Anastasia and Cameron Bravo (c.bravo@cern.ch)

"""
import ROOT as r
import numpy as np
from array import array

from anaoptions import parser

parser.set_defaults(outfilename="LatencyData.root")

(options, args) = parser.parse_args()

r.gROOT.SetBatch()
f = r.TFile(options.filename)
t = f.latTree

Nhits_hs = {}
Nev_hs = {}

vfats= array( 'f' )
par= array( 'f' )
errY= array( 'f' )
errX=array('f')

for vfat in range(24):
    Nhits_hs[vfat] = r.TH1D("Nhits%i_h"%vfat,"Nhits%i_h"%vfat,256,-0.5,255.5)
    Nev_hs[vfat] = r.TH1D("Nev%i_h"%vfat,"Nev%i_h"%vfat,256,-0.5,255.5)
    pass

for evt in t:
    Nhits_hs[int(evt.vfatN)].AddBinContent(evt.lat + 1,evt.Nhits)
    Nev_hs[int(evt.vfatN)].AddBinContent(evt.lat + 1,evt.Nev)
    pass

canv = r.TCanvas("canv","canv",1000,1000)
canv.cd()
outF = r.TFile(options.outfilename,"RECREATE")
lat_ga = {}
fit_f = {}
for vfat in range(0,24):
    fit_f[vfat] = r.TF1("fit%i_f"%vfat,"[0]",0,255)
    lat_ga[vfat] = r.TGraphAsymmErrors(Nhits_hs[vfat],Nev_hs[vfat])
    lat_ga[vfat].SetName("lat%i_ga"%vfat)
    vfats.append(vfat)
    lat_ga[vfat].Draw("AP")
    fit_f[vfat].SetParameter(0, 0.0005)
    lat_ga[vfat].Fit(fit_f[vfat],"Q")
    parameters = fit_f[vfat].GetParameters()
    par.append(parameters[0])
    errY.append(fit_f[vfat].GetParError(0))
    errX.append(0.0)
    canv.SaveAs("VFAT%i_Nhits_vs_Latency.png" %vfat)
    lat_ga[vfat].Write()

tgr= r.TGraphErrors(24,vfats,par,errX,errY)
tgr.SetName("Average_Nhits_per_Vfat")
tgr.SetMarkerStyle(2)
tgr.SetMarkerColor(r.kRed+1)
tgr.SetLineColor(r.kRed+1)
tgr.GetXaxis().SetLimits(0,24)
tgr.GetXaxis().SetTitle("VFAT Position")
tgr.GetYaxis().SetTitle("Average Nhits")
tgr.GetYaxis().SetTitleOffset(1.6)


tgr.Draw("AP")
tgr.SetMarkerStyle(20)
tgr.SetMarkerSize(0.7)
tgr.SetTitle("Average Nhits per Vfat")
canv.SaveAs("Average_Nhits_per_vfat.png")
tgr.Write()

outF.Close()
