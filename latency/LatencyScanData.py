#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""

@author: Anastasia and Cameron Bravo (c.bravo@cern.ch)

"""
import ROOT as r
import numpy as np
from array import array
from optparse import OptionParser

#Define and parse options
parser = OptionParser()

parser.add_option("-i", "--infilename", type="string", dest="filename", default="LatencyScanData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename", default="SCurveFitData.root",
                  help="Specify Output Filename", metavar="outfilename")

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
    Nhits_hs[vfat] = r.TH1D("Nhits%i_h"%vfat,"Nhits%i_h"%vfat,61,139.5,200.5)
    Nev_hs[vfat] = r.TH1D("Nev%i_h"%vfat,"Nev%i_h"%vfat,61,139.5,200.5)
    pass

for evt in t:
    Nhits_hs[int(evt.vfatN)].AddBinContent(evt.lat - 139,evt.Nhits)
    Nev_hs[int(evt.vfatN)].AddBinContent(evt.lat - 139,evt.Nev)
    pass

canv = r.TCanvas("canv","canv",1000,1000)
canv.cd()
outF = r.TFile(options.outfilename,"RECREATE")
lat_ga = {}
fit_f = {}
for vfat in range(0,24):
    fit_f[vfat] = r.TF1("fit%i_f"%vfat,"[0]",140,200)
    lat_ga[vfat] = r.TGraphAsymmErrors(Nhits_hs[vfat],Nev_hs[vfat])
    lat_ga[vfat].SetName("lat%i_ga"%vfat)
    vfats.append(vfat)
    lat_ga[vfat].Draw("AP")
    fit_f[vfat].SetParameter(0, 0.0005)
    lat_ga[vfat].Fit(fit_f[vfat])
    parameters = fit_f[vfat].GetParameters()
    par.append(parameters[0])
    errY.append(fit_f[vfat].GetParError(0))
    errX.append(0.0)
    canv.SaveAs("VFAT%i_Nhits_vs_Latency.png" %vfat)
    lat_ga[vfat].Write()

tgr= r.TGraphErrors(24,vfats,par,errX,errY)
tgr.SetName("Average_Nhits_per_Vfat")
canv1 = r.TCanvas("canv1","canv1")
canv1.cd()
canv1.SetGrid()
tgr.GetXaxis().SetLimits(0,24)
tgr.GetXaxis().SetTitle("VFAT Position")
tgr.GetYaxis().SetTitle("Average Nhits")
tgr.GetYaxis().SetTitleOffset(1.6)


tgr.Draw("AP")
tgr.SetMarkerStyle(20)
tgr.SetMarkerSize(0.7)
tgr.SetTitle("Average Nhits per Vfat")
canv1.SaveAs("Average_Nhits_per_vfat.png")
tgr.Write()


outF.Close()

