#!/bin/env python

import os
from anautilities import saveSummary
from gempython.utils.nesteddict import nesteddict as ndict
from macros.plotoptions import parser

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
    saveSummary(dictSummary=vComparison, name=("%s_FitSummary.png"%filename),drawOpt="colz")
    saveSummary(dictSummary=vNoiseTrim, name=("%s_TrimNoiseSummary.png"%filename),drawOpt="colz")
    saveSummary(dictSummary=vThreshold, name=("%s_FitThreshSummary.png"%filename),drawOpt="")
    saveSummary(dictSummary=vPedestal, name=("%s_FitPedestalSummary.png"%filename),drawOpt="")
    saveSummary(dictSummary=vNoise, name=("%s_FitNoiseSummary.png"%filename),drawOpt="")
    pass

if options.chi2_plots or options.all_plots:
    saveSummary(dictSummary=vChi2, name=("%s_FitChi2Summary.png"%filename),drawOpt="")
    pass
