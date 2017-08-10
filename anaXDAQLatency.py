#!/bin/env python

import sys, re
import time, datetime, os
import ROOT as r

sys.path.append('${GEM_PYTHON_PATH}')

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i","--infile", type="string", dest="infile",
                      help="Input file to process", metavar="infile")
    parser.add_option("--amc13", type="int", dest="amc13", default=1,
                      help="AMC13 to look at", metavar="amc13")
    parser.add_option("--amc", type="int", dest="amc",
                      help="AMC to look at", metavar="amc")
    parser.add_option("--gtx", type="int", dest="gtx",
                      help="GTX to look at", metavar="gtx")
    parser.add_option("--min", type="int", dest="min", default=0,
                      help="Min parameter range to look at", metavar="min")
    parser.add_option("--max", type="int", dest="max", default=256,
                      help="Max parameter range to look at", metavar="max")
    
    (options, args) = parser.parse_args()
    
    if (options.amc == None):
        print "Please specify a valid AMC [1,12]"
        exit(0)

    if (options.gtx == None):
        print "Please specify a valid AMC [0,1]"
        exit(0)

    infilename = "%s"%(options.infile)
    
    latencyMean = r.TH1D("latencyMean", "Latency spread across all VFATs", (options.max-options.min)*10, options.min, options.max)
    latencyRMS  = r.TH1D("latencyRMS",  "Latency RMS across all VFATs",    100, 0, 10)
    allVFATsLatency = None
    
    infile = r.TFile(infilename,"READ")
    if not infile:
        print infilename,"does not exist"
        exit(0)
    if infile.IsZombie():
        print infilename,"is a zombie"
        exit(0)
    if not infile.IsOpen():
        print infilename,"is not open"
        exit(0)
    baseDir = "AMC13-%d/AMC-%d/GTX-%d/"%(options.amc13,options.amc,options.gtx)
    vfatDirs = ["VFAT-%d"%x for x in range(24)]
    
    latCan = r.TCanvas("latCan","latCan", 1000,1000)
    latCan.Divide(5,5)

    for i,vfat in enumerate(vfatDirs):
        inHist = infile.Get(baseDir+vfat+"/latencyScan")
        print inHist
        if inHist:
            latMean = inHist.GetMean()
            latRMS  = inHist.GetRMS()
            print "%s - %2.4f %2.4f"%(vfat,latMean,latRMS)
            latencyMean.Fill(latMean)
            latencyRMS.Fill(latRMS)
            if not allVFATsLatency:
                allVFATsLatency = inHist.Clone("allVFATSLatency")
                allVFATsLatency.SetTitle("Latency scan for all VFATs summed")
            else:
                allVFATsLatency.Add(inHist)
                pass
            pass
        inHist = infile.Get(baseDir+vfat+"/latencyScan2D")
        print inHist
        if inHist:
            latCan.cd(i+1)
            inHist.SetTitle(vfat)
            inHist.GetXaxis().SetRangeUser(options.min,options.max)
            inHist.Draw("colz")
            #inHist.GetXaxis().SetRangeUser(145,170)
            pass
        pass
    
    latCan.cd(25)
    allVFATsLatency.GetXaxis().SetRangeUser(options.min,options.max)
    allVFATsLatency.Draw()

    outname = options.infile.split('/')[-1]
    print outname
    latCan.SaveAs("~/latency_scan_all_vfats_AMC13%02d_AMC%02d_OH%02d_%s.pdf"%(options.amc13,options.amc,options.gtx,outname))
    latCan.SaveAs("~/latency_scan_all_vfats_AMC13%02d_AMC%02d_OH%02d_%s.png"%(options.amc13,options.amc,options.gtx,outname))
    outCan = r.TCanvas("outCan","outCan", 1000,600)
    outCan.Divide(2,1)
    outCan.cd(1)
    latencyMean.Draw("ep0")
    outCan.cd(2)
    latencyRMS.Draw("ep0")
    outCan.SaveAs("~/latency_scan_AMC13%02d_AMC%02d_OH%02d_%s.pdf"%(options.amc13,options.amc,options.gtx,outname))
    outCan.SaveAs("~/latency_scan_AMC13%02d_AMC%02d_OH%02d_%s.png"%(options.amc13,options.amc,options.gtx,outname))
    raw_input("press enter to quit")
