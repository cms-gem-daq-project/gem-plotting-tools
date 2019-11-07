#!/bin/env python

"""
anaXDAQLatency
==============
"""

import sys, re
import time, datetime, os

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to anaXDAQLatency.py')

    # Positional Arguments
    parser.add_argument("infile", type=str, help="Input file to process")

    # Optional Arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("--amc13", type=int, dest="amc13", help="AMC13 to look at", default=1)
    parser.add_argument("-m","--mapping", type=str, help="If provided results will be in Readout Strip instead of VFAT channel.  Input file should be comma separated.  For each row first number is OH number, second number is path to mapping file",default=None)
    parser.add_argument("-o","--ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", default=0xfff)
    parser.add_argument("-s", "--slot", type=int, help="slot in uTCA crate", default=2)
    parser.add_argument("--scanmin", type=int, dest="scanmin", default=0,
                      help="Minimum value of scan parameter range to look at")
    parser.add_argument("--scanmax", type=int, dest="scanmax", default=1024,
                      help="Maximum value of scan parameter range to look at")
    args = parser.parse_args()

    import os
    if (args.slot < 1 or args.slot > 12):
        print("Please specify a valid AMC [1,12]")
        exit(os.EX_USAGE)

    if (args.ohMask < 0x0 or args.ohMask > 0xfff):
        print("Please specify a valid ohMask [0x0,0xfff]")
        exit(os.EX_USAGE)

    from gempython.utils.wrappers import envCheck
    envCheck("ELOG_PATH")
    elogPath = os.getenv("ELOG_PATH")
    
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in inFile.latTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=inFile.latTree, branches =[ 'gemType' ] )[0][0]]
    print gemType
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans

    # Open input file
    print("Opening input file: {0}".format(args.infile))
    infile = r.TFile(args.infile,"READ")
    if not infile:
        print("{0} does not exist".format(infilename))
        exit(os.EX_IOERR)
    if infile.IsZombie():
        print("{0} is a zombie".format(infilename))
        exit(os.EX_IOERR)
    if not infile.IsOpen():
        print("{0} is not open".format(infilename))
        exit(os.EX_IOERR)
        pass

    # Get run number
    fields = args.infile.split("_")
    if "run" in fields[0]:
        runNo = fields[0]
    else:
        runNo = "runUnknown"
        pass

    # Make output dir in $ELOG_PATH
    from gempython.utils.wrappers import runCommand
    runCommand(["mkdir", "{0}/{1}".format(elogPath,runNo)])

    # Make nested containers
    from gempython.utils.nesteddict import nesteddict as ndict
    baseDir = ndict() # baseDir[slot][oh] -> string
    vfatDirs = ["VFAT-{0}".format(x) for x in range(nVFATS)]

    allVFATsLatency = ndict()   #   allVFATsLatency[slot][oh]      -> histogram
    dictMapping = ndict()       #   dictMapping[slot][oh]          -> mapping dict
    latencyMean = ndict()       #   latencyMean[slot][oh]          -> histogram
    latencyRMS = ndict()        #   latencyRMS[slot][oh]           -> histogram
    vfatHitMulti = ndict()      #   vfatHitMulti[slot][oh][vfatN]  -> histogram
    vfatLatHists = ndict()      #   vfatHists[slot][oh][vfatN]     -> histogram
    vfatLatHists2D = ndict()    #   vfatHists2D[slot][oh][vfatN]   -> histogram

    # Get channel mapping?
    from gempython.gemplotting.utils.anautilities import getMapping, getSummaryCanvas
    if args.mapping is not None:
        print("Getting mapping")
        # Try to get the mapping data
        try:
            mapFile = open(args.mapping, 'r')
        except IOError as e:
            print("Exception:", e)
            print("Failed to open: '{0}'".format(mappingFileName))
        else:
            listMapData = mapFile.readlines()
        finally:
            mapFile.close()
    
        # strip trhe end of line character
        listMapData = [x.strip('\n') for x in listMapData]

        for line in listMapData:
            mapInfo = line.split(",")
            dictMapping[args.slot][int(mapInfo[0])] = getMapping(mapInfo[1])
            pass

        # Make an output TFile to store the remapped histo's in
        outname = args.infile.split("/")[-1].replace(".analyzed.root")
        outFileRemapped = r.TFile("{0}/{1}_readoutStrips.analyzed.root".format(elogPath,outname),"RECREATE")
        outFileRemapped.mkdir("AMC{0}".format(args.slot))
        pass

    # This could be expanded in the future to accommodate multiple slots
    # loop over OH's
    from gempython.utils.gemlogger import printRed, printYellow
    import numpy as np
    import root_numpy as rp
    print("Getting histograms and making output canvases")
    for oh in range(0,12):
        # Skip masked OH's        
        if( not ((args.ohMask >> oh) & 0x1)):
            continue

        # Make base directory
        baseDir[args.slot][oh] = "AMC13-{0}/AMC-{1}/GEB-{2}/".format(args.amc13, args.slot, oh)
    
        # Check to make sure this AMC13 & AMC exist in the file
        currentDir = infile.GetDirectory(baseDir[args.slot][oh])
        if currentDir == 0:
            printRed("Directory: {0} in file {1} does not exist".format(baseDir[slot][oh],args.infile))
            printRed("Skipping AMC{0} OH{1}".format(args.slot,oh))
            continue

        # Make mean & RMS lat dist
        latencyMean[args.slot][oh] = r.TH1D(
                "latencyMean_AMC{0}_OH{1}".format(args.slot,oh), 
                "Latency spread across all VFATs for #left(AMC{0},OH{1}#right)".format(args.slot,oh), 
                (args.scanmax-args.scanmin)*10, args.scanmin-0.5, args.scanmax-0.5)
        latencyRMS[args.slot][oh]  = r.TH1D(
                "latencyRMS_AMC{0}_OH{1}".format(args.slot,oh),
                "Latency RMS across all VFATs for #left(AMC{0},OH{1}#right)".format(args.slot,oh),
                100, -0.5, 9.5)
        allVFATsLatency[args.slot][oh] = None

        # Make a directory in the output file
        if args.mapping is not None:
            dirAMC = outFileRemapped.GetDirectory("AMC{0}".format(args.slot))
            dirAMC.mkdir("OH{0}".format(oh))
            pass

        # Get Distributions from File
        for vfat,path in enumerate(vfatDirs):
            # Load Dist
            print(baseDir[args.slot][oh]+path+"/n_hits_per_event")
            vfatHitMulti[args.slot][oh][vfat] = infile.Get(baseDir[args.slot][oh]+path+"/n_hits_per_event") 
            vfatLatHists[args.slot][oh][vfat] = infile.Get(baseDir[args.slot][oh]+path+"/latencyScan")
            vfatLatHists2D[args.slot][oh][vfat] = infile.Get(baseDir[args.slot][oh]+path+"/latencyScan2D")

            # Rename
            vfatHitMulti[args.slot][oh][vfat].SetName("{0}_AMC{1}_OH{2}_VFAT{3}".format(vfatHitMulti[args.slot][oh][vfat].GetName(),args.slot,oh,vfat))
            vfatLatHists[args.slot][oh][vfat].SetName("{0}_AMC{1}_OH{2}_VFAT{3}".format(vfatLatHists[args.slot][oh][vfat].GetName(),args.slot,oh,vfat))
            vfatLatHists2D[args.slot][oh][vfat].SetName("{0}_AMC{1}_OH{2}_VFAT{3}".format(vfatLatHists2D[args.slot][oh][vfat].GetName(),args.slot,oh,vfat))

            # Remap Y-Axis
            chanOrStripLabel = "VFAT Channels" # Placeholder
            if args.mapping is not None:
                if oh not in dictMapping[args.slot].keys():
                    printYellow("I did not find OH{0} in the mapping dict for AMC{1}".format(oh,args.slot))
                    printYellow("AMC{0} OH{1} will not be remapped. Please recheck input file: {2}".format(args.slot,oh,args.mapping))
                else:
                    chanOrStripLabel = "Readout Strip"
                    (histArray,edges) = rp.hist2array(vfatLatHists2D[args.slot][oh][vfat],return_edges=True)
                    remappedArray = np.zeros(histArray.shape)
                    xMax = histArray.shape[0]
                    yMax = histArray.shape[1]
                    for lat in range(0,xMax):
                        for vfatCH in range(0,yMax): 
                            strip = dictMapping[args.slot][oh][vfat]['Strip'][vfatCH]
                            remappedArray[lat][strip] = histArray[lat][vfatCH]
                            pass
                        pass
                    vfatLatHists2D[args.slot][oh][vfat] = rp.array2hist(remappedArray,vfatLatHists2D[args.slot][oh][vfat])
                    pass
                pass
    
            # Set Style
            vfatHitMulti[args.slot][oh][vfat].SetTitle("VFAT{0}".format(vfat))
            vfatHitMulti[args.slot][oh][vfat].GetXaxis().SetTitle("Hit Multiplicity per Event")
            vfatHitMulti[args.slot][oh][vfat].GetXaxis().SetRangeUser(1e-1,129)
            vfatHitMulti[args.slot][oh][vfat].GetYaxis().SetTitle("N")
            vfatHitMulti[args.slot][oh][vfat].GetYaxis().SetRangeUser(1e-1,1e8)

            # Set Style
            vfatLatHists[args.slot][oh][vfat].SetTitle("VFAT{0}".format(vfat))
            vfatLatHists[args.slot][oh][vfat].GetXaxis().SetTitle("CFG_LATENCY")
            vfatLatHists[args.slot][oh][vfat].GetXaxis().SetRangeUser(args.scanmin,args.scanmax)
            vfatLatHists[args.slot][oh][vfat].GetYaxis().SetTitle("N")
            vfatLatHists[args.slot][oh][vfat].GetYaxis().SetRangeUser(1e-1,2e5)

            # Set Style
            vfatLatHists2D[args.slot][oh][vfat].SetTitle("VFAT{0}".format(vfat))
            vfatLatHists2D[args.slot][oh][vfat].GetXaxis().SetTitle("CFG_LATENCY")
            vfatLatHists2D[args.slot][oh][vfat].GetXaxis().SetRangeUser(args.scanmin,args.scanmax)
            vfatLatHists2D[args.slot][oh][vfat].GetYaxis().SetTitle(chanOrStripLabel)
            vfatLatHists2D[args.slot][oh][vfat].GetZaxis().SetRangeUser(1e-1,2e5)

            # Store remapped 2D histogram
            if args.mapping is not None:
                if oh in dictMapping[args.slot].keys():
                    dirOH = dirAMC.GetDirectory("OH{0}".format(oh))
                    dirVFAT = dirOH.mkdir("VFAT{0}".format(vfat))
                    dirVFAT.cd()
                    vfatLatHists2D[args.slot][oh][vfat].Write()
                    pass
                pass

            # Get Info from 1D Distribution
            if vfatLatHists[args.slot][oh][vfat]:
                latMean = vfatLatHists[args.slot][oh][vfat].GetMean()
                latRMS  = vfatLatHists[args.slot][oh][vfat].GetRMS()
                print("AMC{0} OH{1} VFAT{2} - {3:2.4f} {4:2.4f}".format(args.slot,oh,vfat,latMean,latRMS))
                latencyMean[args.slot][oh].Fill(latMean)
                latencyRMS[args.slot][oh].Fill(latRMS)
                if not allVFATsLatency[args.slot][oh]:
                    allVFATsLatency[args.slot][oh] = vfatLatHists[args.slot][oh][vfat].Clone("allVFATSLatency_AMC{0}_OH{1}".format(args.slot,oh))
                    allVFATsLatency[args.slot][oh].SetTitle("Latency scan for all VFATs on AMC{0} OH{1} summed".format(args.slot,oh))
                else:
                    allVFATsLatency[args.slot][oh].Add(vfatLatHists[args.slot][oh][vfat])
                    pass
                pass
            pass # End loop over VFATs of this OH

        # Print Canvas
        r.gStyle.SetOptStat(0)
        canvHitMulti = getSummaryCanvas(vfatHitMulti[args.slot][oh], name="canvHitMulti_AMC{0}_OH{1}".format(args.slot,oh), drawOpt="hist", gemType=gemType)
        canvLat1D = getSummaryCanvas(vfatLatHists[args.slot][oh], name="canvLatScan1D_AMC{0}_OH{1}".format(args.slot,oh), drawOpt="hist", gemType=gemType)
        canvLat2D = getSummaryCanvas(vfatLatHists2D[args.slot][oh], name="canvLatScan2D_AMC{0}_OH{1}".format(args.slot,oh), drawOpt="colz", gemType=gemType)
        
        for vfat in range(0,nVFATS):
            canvHitMulti.cd(vfat).SetLogx()
            canvHitMulti.cd(vfat).SetLogy()
            canvLat1D.cd(vfat).SetLogy()
            canvLat2D.cd(vfat).SetLogz()
        
        canvHitMulti.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,runNo,canvHitMulti.GetName()))
        canvLat1D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,runNo,canvLat1D.GetName()))
        canvLat2D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,runNo,canvLat2D.GetName()))

        r.gStyle.SetOptStat(1111111)
        canvLatScanAllVFATs = r.TCanvas("canvLatScanAllVFATs_AMC{0}_OH{1}".format(args.slot,oh),"Sum of All VFATs on AMC{0} OH{1}".format(args.slot,oh),600,600)
        canvLatScanAllVFATs.Draw()
        canvLatScanAllVFATs.cd()
        allVFATsLatency[args.slot][oh].Draw()
        allVFATsLatency[args.slot][oh].GetXaxis().SetRangeUser(args.scanmin,args.scanmax)
        allVFATsLatency[args.slot][oh].Draw("hist")
        canvLatScanAllVFATs.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,runNo,canvLatScanAllVFATs.GetName()))

        canvLatScanStats = r.TCanvas("canvLatScanStats_AMC{0}_OH{1}".format(args.slot,oh),"Latency Scan Summary Statistics",1200,600)
        canvLatScanStats.Divide(2,1)
        canvLatScanStats.cd(1)
        latencyMean[args.slot][oh].Draw("ep0")
        canvLatScanStats.cd(2)
        latencyRMS[args.slot][oh].Draw("ep0")
        canvLatScanStats.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,runNo,canvLatScanStats.GetName()))
        pass # End Loop over OH's of this AMC

    print("Your distributions can be found under:")
    print("")
    print("\t{0}/{1}".format(elogPath,runNo))
    print("")
    
    if args.mapping is not None:
        print("You can find your remapped histograms in the following root file:")
        print("")
        print("\t{0}/{1}_readoutStrips.analyzed.root".format(elogPath,outname))
        print("")
        pass
    
    print("Goodbye")
