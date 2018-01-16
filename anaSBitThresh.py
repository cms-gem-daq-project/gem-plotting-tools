#!/bin/env python
import os
import sys
from optparse import OptionParser
from gempython.utils.nesteddict import nesteddict as ndict

from anaoptions import parser

parser.add_option("--maxNoiseRate", type="float", dest="maxNoiseRate", default=100,
                  help="Max Noise Rate allowed in Hz", metavar="maxNoiseRate")
parser.set_defaults(outfilename="SBitRatePlots.root")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename

import ROOT as r
r.gROOT.SetBatch(True)
inF = r.TFile(filename+'.root')
outF = r.TFile(filename+'/'+outfilename, 'recreate')

VT1_MAX = 256

print 'Initializing Histograms'
vRate = ndict()
for vfat in range(0,24):
    vRate[vfat] = r.TH1D("h_Rate_vs_vthr_VFAT%i"%vfat,"VFAT%i;CFG_THR_ARM_DAC #left[DAC Units#right];Rate #left(Hz#right)"%vfat,VT1_MAX/2,0,VT1_MAX)
    vRate[vfat].GetXaxis().SetRangeUser(1e-1,1e9)

print 'Filling Histograms'
for event in inF.rateTree :
    vRate[event.vfatN].Fill(event.vth,event.Rate)

#Save Output
outF.cd()
from anautilities import make3x8Canvas
canv_RateSummary = make3x8Canvas('canv_RateSummary', vRate, 'hist')
for vfat in range(0,24):
    canv_RateSummary.cd(vfat).SetLogy()
    canv_RateSummary.cd(vfat).Update()
    vRate[vfat].Write()
canv_RateSummary.SaveAs(filename+'/RateSummary.png')

#Now determine what VT1 to use for configuration.  The first threshold bin with no entries for now.
#Make a text file readable by TTree::ReadFile
vt1 = dict((vfat,0) for vfat in range(0,24))
for vfat in range(0,24):
    for binX in range(1,vRate[vfat].GetNbinsX()+1):
        if vRate[vfat].GetBinContent(binX) < options.maxNoiseRate:
            print 'vt1 for VFAT%i found'%vfat
            vt1[vfat]=vRate[vfat].GetBinCenter(binX)
            break
        pass
    pass

print "vt1:"
print vt1

txt_vfat = open(filename+"/vfatConfig.txt", 'w')
txt_vfat.write("vfatN/I:vt1/I:trimRange/I\n")
for vfat in range(0,24):
    txt_vfat.write('%i\t%i\t%i\n'%(vfat, vt1[vfat],0))
    pass
txt_vfat.close()

# Make output TTree
myT = r.TTree('thrAnaTree','Tree Holding Analyzed Threshold Data')
myT.ReadFile(filename+"/vfatConfig.txt")
myT.Write()
outF.Close()

print 'Analysis Completed Successfully'
