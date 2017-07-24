#!/bin/env python
import os
import numpy as np
from optparse import OptionParser
from array import array
from anautilities import *
from fitScanData import *
from channelMaps import *
from PanChannelMaps import *
from gempython.utils.nesteddict import nesteddict as ndict

from anaoptions import parser

parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                  help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
parser.add_option("-f", "--fit", action="store_true", dest="SaveFile",
                  help="Save the Fit values to Root file", metavar="SaveFile")
parser.add_option("--IsTrimmed", action="store_true", dest="IsTrimmed",
                  help="If the data is from a trimmed scan, plot the value it tried aligning to", metavar="IsTrimmed")
parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                  help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")
parser.set_defaults(outfilename="SCurveData.root")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename

vToQb = -0.8
vToQm = 0.05

import ROOT as r
r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(1111111)
GEBtype = options.GEBtype
inF = r.TFile(filename+'.root')
if options.SaveFile:
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    myT = r.TTree('scurveFitTree','Tree Holding FitData')
    pass

#Build the channel to strip mapping from the text file
chanToStripLUT = []
stripToChanLUT = []
chanToPanPinLUT = []
for vfat in range(0,24):
    chanToStripLUT.append([])
    stripToChanLUT.append([])
    chanToPanPinLUT.append([])
    for channel in range(0,128):
        chanToStripLUT[vfat].append(0)
        stripToChanLUT[vfat].append(0)
        chanToPanPinLUT[vfat].append(0)
        pass
    pass

buildHome = os.environ.get('BUILD_HOME')

if GEBtype == 'long':
    intext = open(buildHome+'/gem-plotting-tools/setup/longChannelMap.txt', 'r')
    pass
if GEBtype == 'short':
    intext = open(buildHome+'/gem-plotting-tools/setup/shortChannelMap.txt', 'r')
    pass

for i, line in enumerate(intext):
    if i == 0: continue
    mapping = line.rsplit('\t')
    chanToStripLUT[int(mapping[0])][int(mapping[2]) - 1] = int(mapping[1])
    stripToChanLUT[int(mapping[0])][int(mapping[1])] = int(mapping[2]) - 1
    chanToPanPinLUT[int(mapping[0])][int(mapping[2]) -1] = int(mapping[3])
    pass

if options.IsTrimmed:
    trimmed_text = open('scanInfo.txt', 'r')
    trimVcal = []
    for vfat in range(0,24):
        trimVcal.append(0)
        pass
    for n, line in enumerate(trimmed_text):
        if n == 0: continue
        print line
        scanInfo = line.rsplit('  ')
        trimVcal[int(scanInfo[0])] = float(scanInfo[4])
        pass
    pass

if options.SaveFile:
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    ROBstr = array( 'i', [ 0 ] )
    myT.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
    mask = array( 'i', [ 0 ] )
    myT.Branch( 'mask', mask, 'mask/I' )
    maskDead = array( 'i', [ 0 ] )
    myT.Branch( 'maskDead', maskDead, 'maskDead/I' )
    maskHot = array( 'i', [ 0 ] )
    myT.Branch( 'maskHot', maskHot, 'maskHot/I' )
    panPin = array( 'i', [ 0 ] )
    myT.Branch( 'panPin', panPin, 'panPin/I' )
    trimRange = array( 'i', [ 0 ] )
    myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
    vthr = array( 'i', [ 0 ] )
    myT.Branch( 'vthr', vthr, 'vthr/I' )
    trimDAC = array( 'i', [ 0 ] )
    myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
    threshold = array( 'f', [ 0 ] )
    myT.Branch( 'threshold', threshold, 'threshold/F')
    noise = array( 'f', [ 0 ] )
    myT.Branch( 'noise', noise, 'noise/F')
    pedestal = array( 'f', [ 0 ] )
    myT.Branch( 'pedestal', pedestal, 'pedestal/F')
    ped_eff = array( 'f', [ 0 ] )
    myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
    scurve_h = r.TH1D()
    myT.Branch( 'scurve_h', scurve_h)
    chi2 = array( 'f', [ 0 ] )
    myT.Branch( 'chi2', chi2, 'chi2/F')
    ndf = array( 'i', [ 0 ] )
    myT.Branch( 'ndf', ndf, 'ndf/I')
    Nhigh = array( 'i', [ 0 ] )
    myT.Branch( 'Nhigh', Nhigh, 'Nhigh/I')
    pass

vSum  = ndict()
vSum2 = ndict()
vSumPruned = ndict()
vSumPruned2 = ndict()
vScurves = []
vthr_list = []
trim_list = []
trimrange_list = []
lines = []
def overlay_fit(VFAT, CHAN):
    Scurve = r.TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CHAN),255,-0.5,254.5)
    strip = chanToStripLUT[VFAT][CHAN]
    pan_pin = chanToPanPinLUT[VFAT][CHAN]
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CHAN):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    param0 = scanFits[0][VFAT][CHAN]
    param1 = scanFits[1][VFAT][CHAN]
    param2 = scanFits[2][VFAT][CHAN]
    fitTF1 =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    fitTF1.SetParameter(2, param2)
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(1111111)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, strip))
    return

for vfat in range(0,24):
    vScurves.append([])
    vthr_list.append([])
    trim_list.append([])
    trimrange_list.append([])
    if options.IsTrimmed:
        lines.append(r.TLine(-0.5, trimVcal[vfat], 127.5, trimVcal[vfat]))
        pass
    if not (options.channels or options.PanPin):
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'VFAT %i;Strip;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSum[vfat].GetYaxis().SetTitleOffset(1.5)
        vSumPruned[vfat] = r.TH2D('vSumPruned%i'%vfat,'VFAT %i;Strip;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSumPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.channels:
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'VFAT %i;Channels;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSum[vfat].GetYaxis().SetTitleOffset(1.5)
        vSumPruned[vfat] = r.TH2D('vSumPruned%i'%vfat,'VFAT %i;Channels;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSumPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.PanPin:
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSum[vfat].GetYaxis().SetTitleOffset(1.5)
        vSumPruned[vfat] = r.TH2D('vSumPruned%i'%vfat,'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSumPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        vSum2[vfat] = r.TH2D('vSum2_%i'%vfat,'vSum%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSum2[vfat].GetYaxis().SetTitleOffset(1.5)
        vSumPruned2[vfat] = r.TH2D('vSumPruned2_%i'%vfat,'vSum%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSumPruned2[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    for chan in range (0,128):
        vScurves[vfat].append(r.TH1D('Scurve_%i_%i'%(vfat,chan),'Scurve_%i_%i;VCal [DAC units]'%(vfat,chan),256,-0.5,255.5))
        vthr_list[vfat].append(0)
        trim_list[vfat].append(0)
        trimrange_list[vfat].append(0)
        pass
    pass

if options.SaveFile:
    scanFits = fitScanData(filename+'.root')
    pass

# Fill
for event in inF.scurveTree:
    strip = chanToStripLUT[event.vfatN][event.vfatCH]
    pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
    if not (options.channels or options.PanPin):
        vSum[event.vfatN].Fill(strip,vToQm*event.vcal+vToQb,event.Nhits)
        pass
    if options.channels:
        vSum[event.vfatN].Fill(event.vfatCH,vToQm*event.vcal+vToQb,event.Nhits)
        pass
    if options.PanPin:
        if (pan_pin < 64):
            vSum[event.vfatN].Fill(63-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
            pass
        else:
            vSum2[event.vfatN].Fill(127-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
            pass
        pass
    x = vScurves[event.vfatN][event.vfatCH].FindBin(event.vcal)
    vScurves[event.vfatN][event.vfatCH].SetBinContent(x, event.Nhits)
    r.gStyle.SetOptStat(1111111)
    vthr_list[event.vfatN][event.vfatCH] = event.vthr
    trim_list[event.vfatN][event.vfatCH] = event.trimDAC
    trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
    pass

# Determine hot channels
import numpy as np
if options.SaveFile:
    print 'Determining hot channels'
    masksDead = []
    masksHot = []
    masks = []
    for vfat in range(0, 24):
        trimValue = np.zeros(128)
        dead = np.zeros(128)
        for ch in range(0, 128):
            # Get fit results
            threshold[0] = scanFits[0][vfat][ch]
            noise[0] = scanFits[1][vfat][ch]
            pedestal[0] = scanFits[2][vfat][ch]
            # Identify dead channels
            dead[ch] = (threshold[0] == 8 and pedestal[0] == 8)
            # Compute the value to apply MAD on for each channel
            trimValue[ch] = threshold[0] - options.ztrim * noise[0]
        masksDead.append(dead)
        # Determine outliers
        hot = isOutlierMADOneSided(trimValue, thresh=options.zscore,
                                   rejectHighTail=False).flatten()
        masksHot.append(hot)
        masks.append(np.logical_or(dead, hot))
        print 'VFAT %2d: %d dead, %d hot channels' % (vfat,
                                                      np.count_nonzero(dead),
                                                      np.count_nonzero(hot))

# Fill pruned
for event in inF.scurveTree:
    if masks[event.vfatN][event.vfatCH]:
        continue
    strip = chanToStripLUT[event.vfatN][event.vfatCH]
    pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
    if not (options.channels or options.PanPin):
        vSumPruned[event.vfatN].Fill(strip,vToQm*event.vcal+vToQb,event.Nhits)
    if options.channels:
        vSumPruned[event.vfatN].Fill(event.vfatCH,vToQm*event.vcal+vToQb,event.Nhits)
    if options.PanPin:
        if (pan_pin < 64):
            vSumPruned[event.vfatN].Fill(63-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
        else:
            vSumPruned2[event.vfatN].Fill(127-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)

# Store values in ROOT file
if options.SaveFile:
    fitSums = {}
    for vfat in range (0,24):
        fitThr = []        
        fitENC = []
        stripList = []
        panList = []
        chanList = []
        for chan in range (0, 128):
            #Get strip and pan pin
            strip = chanToStripLUT[vfat][chan]
            pan_pin = chanToPanPinLUT[vfat][chan]
            #Store strip, chan and pan pin
            stripList.append(float(strip))
            panList.append(float(pan_pin))
            chanList.append(float(chan))
            #Filling the Branches
            param0 = scanFits[0][vfat][chan]
            param1 = scanFits[1][vfat][chan]
            param2 = scanFits[2][vfat][chan]
            FittedFunction =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
            FittedFunction.SetParameter(0, param0)
            FittedFunction.SetParameter(1, param1)
            FittedFunction.SetParameter(2, param2)
            ped_eff[0] = FittedFunction.Eval(0.0)
            vfatN[0] = vfat
            vfatCH[0] = chan
            ROBstr[0] = strip
            panPin[0] = pan_pin
            trimRange[0] = trimrange_list[vfat][chan] 
            vthr[0] = vthr_list[vfat][chan]
            trimDAC[0] = trim_list[vfat][chan]
            threshold[0] = param0
            fitThr.append(vToQm*param0+vToQb)
            noise[0] = param1
            fitENC.append(vToQm*param1*options.ztrim)
            pedestal[0] = param2
            maskHot[0] = masksHot[vfat][chan]
            maskDead[0] = int(masksDead[vfat][ch])
            mask[0] = masks[vfat][chan]
            chi2[0] = scanFits[3][vfat][chan]
            ndf[0] = int(scanFits[5][vfat][chan])
            holder_curve = vScurves[vfat][chan]
            holder_curve.Copy(scurve_h)
            Nhigh[0] = int(scanFits[4][vfat][chan])
            #Filling the arrays for plotting later
            if options.drawbad:
                if (Chi2 > 1000.0 or Chi2 < 1.0):
                    overlay_fit(vfat, chan)
                    print "Chi2 is, %d"%(Chi2)
                    pass
                pass
            myT.Fill()
            pass
        if not (options.channels or options.PanPin):
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(stripList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Strip;Threshold [fC]"%vfat)
            pass
        elif options.channels:
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(chanList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Channel;Threshold [fC]"%vfat)
            pass
        elif options.PanPin:
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(panList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Panasonic Pin;Threshold [fC]"%vfat)
            pass
        
        fitSums[vfat].SetName("fitSum%i"%vfat)
        fitSums[vfat].SetMarkerStyle(2)
        pass
    pass

def saveSummary(vSum, vSum2, name='Summary'):
    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    if not options.PanPin:
        canv = make3x8Canvas('canv', vSum, 'colz')
        for vfat in range(0,24):
            canv.cd(vfat+1)
            if options.IsTrimmed:
                legend.Clear()
                legend.AddEntry(line, 'trimVCal is %f'%(trimVcal[vfat]))
                legend.Draw('SAME')
                print trimVcal[vfat]
                lines[vfat].SetLineColor(1)
                lines[vfat].SetLineWidth(3)
                lines[vfat].Draw('SAME')
                pass
            canv.Update()
            pass
        pass
    else:
        canv = r.TCanvas('canv','canv',500*8,500*3)
        canv.Divide(8,6)
        r.gStyle.SetOptStat(0)
        for ieta in range(0,8):
            for iphi in range (0,3):
                r.gStyle.SetOptStat(0)
                canv.cd((ieta+1 + iphi*16)%48 + 16)
                vSum[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                canv.cd((ieta+9 + iphi*16)%48 + 16)
                vSum2[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                pass
            pass
        pass

    canv.SaveAs(filename+'/%s.png' % name)

saveSummary(vSum, vSum2)
if options.SaveFile:
    saveSummary(vSumPruned, vSumPruned2, name='PrunedSummary')

if options.SaveFile:
    r.gStyle.SetOptStat(0)
    canv = make3x8Canvas('canv', fitSums, 'ap')
    canv.SaveAs(filename+'/fitSummary.png')
    pass

if options.SaveFile:
    confF = open(filename+'/chConfig.txt','w')
    confF.write('vfatN/I:vfatCH/I:trimDAC/I:mask/I\n')
    for vfat in range (0,24):
        for chan in range (0, 128):
            confF.write('%i\t%i\t%i\t%i\n'%(vfat,chan,trim_list[vfat][chan],masks[vfat][chan]))
            pass
        pass
    confF.close()
    outF.cd()
    for vfat in fitSums.keys():
        fitSums[vfat].Write()
        pass
    myT.Write()
    outF.Close()
    pass
