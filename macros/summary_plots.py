#!/bin/env python

import os

from gempython.utils.nesteddict import nesteddict as ndict    
from gempython.gemplotting.macros.plotoptions import parser

parser.add_option("-a","--all", action="store_true", dest="all_plots",
                  help="Make all plots", metavar="all_plots")
parser.add_option("-f","--fit", action="store_true", dest="fit_plots",
                  help="Make fit parameter plots", metavar="fit_plots")
parser.add_option("-x","--chi2", action="store_true", dest="chi2_plots",
                  help="Make Chi2 plots", metavar="chi2_plots")

(options, args) = parser.parse_args()
filename = options.filename[:-5]

import ROOT as r

r.gROOT.SetBatch(True)
inF = r.TFile(filename+'.root')

vSum   = ndict()
vNoise = ndict()
vThreshold = ndict()
vChi2      = ndict()
vComparison = ndict()
vNoiseTrim  = ndict()
vPedestal   = ndict()

for vfat in range(0,24):
    vNoise[vfat] = r.TH1D('Noise%i'%vfat,'Noise%i;Noise [DAC units]'%vfat,35,-0.5,34.5)
    vPedestal[vfat] = r.TH1D('Pedestal%i'%vfat,'Pedestal%i;Pedestal [DAC units]'%vfat,256,-0.5,255.5)
    vThreshold[vfat] = r.TH1D('Threshold%i'%vfat,'Threshold%i;Threshold [DAC units]'%vfat,60,-0.5,299.5)
    vChi2[vfat] = r.TH1D('ChiSquared%i'%vfat,'ChiSquared%i;Chi2'%vfat,100,-0.5,999.5)
    vComparison[vfat] = r.TH2D('vComparison%i'%vfat,'Fit Summary %i;Threshold [DAC units];Noise [DAC units]'%vfat,60,-0.5,299.5,70,-0.5,34.5)
    vNoiseTrim[vfat] = r.TH2D('vNoiseTrim%i'%vfat,'Noise vs. Trim Summary %i;Trim [DAC units];Noise [DAC units]'%vfat,32,-0.5,31.5,70,-0.5,34.5)
    vComparison[vfat].GetYaxis().SetTitleOffset(1.5)
    vNoiseTrim[vfat].GetYaxis().SetTitleOffset(1.5)
    pass

for event in inF.scurveFitTree:
    strip = event.ROBstr
    param0 = event.threshold
    param1 = event.noise
    param2 = event.pedestal
    vThreshold[event.vfatN].Fill(param0)
    vNoise[event.vfatN].Fill(param1)
    vPedestal[event.vfatN].Fill(param2)
    vChi2[event.vfatN].Fill(event.chi2)
    vComparison[event.vfatN].Fill(param0, param1)
    vNoiseTrim[event.vfatN].Fill(event.trimDAC, param1)
    pass

if options.fit_plots or options.all_plots:
    r.gStyle.SetOptStat(111100)
    canv_comp = r.TCanvas('canv_comp','canv_comp',500*8,500*3)
    canv_comp.Divide(8,3)
    for vfat in range(0,24):
        canv_comp.cd(vfat+1)
        r.gStyle.SetOptStat(111100)
        vComparison[vfat].Draw('colz')
        canv_comp.Update()
        pass
    canv_comp.SaveAs(filename+'_FitSummary.png')

    r.gStyle.SetOptStat(111100)
    canv_trim = r.TCanvas('canv_trim','canv_trim',500*8,500*3)
    canv_trim.Divide(8,3)
    for vfat in range(0,24):
        canv_trim.cd(vfat+1)
        r.gStyle.SetOptStat(111100)
        vNoiseTrim[vfat].Draw('colz')
        canv_trim.Update()
        pass
    canv_trim.SaveAs(filename+'_TrimNoiseSummary.png')

    canv_thresh = r.TCanvas('canv_thresh','canv_thresh',500*8,500*3)
    canv_thresh.Divide(8,3)
    for vfat in range(0,24):
        canv_thresh.cd(vfat+1)
        r.gStyle.SetOptStat(111100)
        vThreshold[vfat].Draw()
        r.gPad.SetLogy()
        canv_thresh.Update()
        pass
    canv_thresh.SaveAs(filename+'_FitThreshSummary.png')

    canv_Pedestal = r.TCanvas('canv_Pedestal','canv_Pedestal',500*8,500*3)
    canv_Pedestal.Divide(8,3)
    for vfat in range(0,24):
        canv_Pedestal.cd(vfat+1)
        r.gStyle.SetOptStat(111100)
        vPedestal[vfat].Draw()
        r.gPad.SetLogy()
        canv_Pedestal.Update()
        pass
    canv_Pedestal.SaveAs(filename+'_FitPedestalSummary.png')

    canv_noise = r.TCanvas('canv_noise','canv_noise',500*8,500*3)
    canv_noise.Divide(8,3)
    for vfat in range(0,24):
        canv_noise.cd(vfat+1)
        vNoise[vfat].Draw()
        r.gPad.SetLogy()
        canv_noise.Update()
        pass
    canv_noise.SetLogy()
    canv_noise.SaveAs(filename+'_FitNoiseSummary.png')
    pass
if options.chi2_plots or options.all_plots:
    canv_Chi2 = r.TCanvas('canv_Chi2','canv_Chi2',500*8,500*3)
    canv_Chi2.Divide(8,3)
    canv_Chi2.SetLogy()
    for vfat in range(0,24):
        canv_Chi2.cd(vfat+1)
        vChi2[vfat].Draw()
        r.gPad.SetLogy()
        canv_Chi2.Update()
        pass
    canv_Chi2.SetLogy()
    canv_Chi2.SaveAs(filename+'_FitChi2Summary.png')
    pass
