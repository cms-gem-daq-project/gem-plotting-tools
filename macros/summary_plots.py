#!/bin/env python

"""
summary\_plots
==============
"""

if __name__ == '__main__':
    import os

    from gempython.gemplotting.utils.anautilities import getSummaryCanvas
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

    gemType = "ge11"
    from gempython.tools.hw_constants import vfatsPerGemVariant
    
    for vfat in range(0,vfatsPerGemVariant[gemType]):
        vNoise[vfat] = r.TH1D('Noise{0}'.format(vfat),'Noise{0};Noise [DAC units]'.format(vfat),35,-0.5,34.5)
        vPedestal[vfat] = r.TH1D('Pedestal{0}'.format(vfat),'Pedestal{0};Pedestal [DAC units]'.format(vfat),256,-0.5,255.5)
        vThreshold[vfat] = r.TH1D('Threshold{0}'.format(vfat),'Threshold{0};Threshold [DAC units]'.format(vfat),60,-0.5,299.5)
        vChi2[vfat] = r.TH1D('ChiSquared{0}'.format(vfat),'ChiSquared{0};Chi2'.format(vfat),100,-0.5,999.5)
        vComparison[vfat] = r.TH2D('vComparison{0}'.format(vfat),'Fit Summary {0};Threshold [DAC units];Noise [DAC units]'.format(vfat),60,-0.5,299.5,70,-0.5,34.5)
        vNoiseTrim[vfat] = r.TH2D('vNoiseTrim{0}'.format(vfat),'Noise vs. Trim Summary {0};Trim [DAC units];Noise [DAC units]'.format(vfat),32,-0.5,31.5,70,-0.5,34.5)
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
        getSummmaryCanvas(dictSummary=vComparison, name=("{0}_FitSummary.png".format(filename)),drawOpt="colz", write2Disk=True)
        getSummmaryCanvas(dictSummary=vNoiseTrim, name=("{0}_TrimNoiseSummary.png".format(filename)),drawOpt="colz", write2Disk=True)
        getSummmaryCanvas(dictSummary=vThreshold, name=("{0}_FitThreshSummary.png".format(filename)),drawOpt="", write2Disk=True)
        getSummmaryCanvas(dictSummary=vPedestal, name=("{0}_FitPedestalSummary.png".format(filename)),drawOpt="", write2Disk=True)
        getSummmaryCanvas(dictSummary=vNoise, name=("{0}_FitNoiseSummary.png".format(filename)),drawOpt="", write2Disk=True)
        pass

    if options.chi2_plots or options.all_plots:
        getSummmaryCanvas(dictSummary=vChi2, name=("{0}_FitChi2Summary.png".format(filename)),drawOpt="", write2Disk=True)
        pass
