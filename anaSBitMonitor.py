#!/bin/env python

"""
anaSbitMonitor.py
=================
"""

if __name__ == '__main__':
    import os
    import sys
    
    import argparse
    from gempython.gemplotting.utils.anaoptions import parent_parser
    parser = argparse.ArgumentParser(description="Options to give to anaSBitMonitor.py", parents=[parent_parser])
    parser.add_argument("--checkInvalid",action="store_true",help="If provided invalid sbits will be considered")
    
    parser.set_defaults(outfilename="SBitMonitorData.root")
    args = parser.parse_args()
    
    filename = args.infilename[:-5]
    os.system("mkdir " + args.infilename[:-5])

    outfilename = args.outfilename

    import ROOT as r
    #r.TH1.SetDefaultSumw2(True)
    r.gROOT.SetBatch(True)
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    inF = r.TFile(filename+'.root')

    # Determine the rates scanned
    print('Determining rates tested')
    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')

    list_bNames = ['calEnable','isValid','ratePulsed']
    initInfo = rp.tree2array(tree=inF.sbitDataTree, branches=list_bNames)
    calEnableValues = np.unique(initInfo['calEnable'])
    isValidValues = np.unique(initInfo['isValid'])
    ratesUsed = np.unique(initInfo['ratePulsed'])

    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in inF.sbitDataTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=inF.sbitDataTree, branches =[ 'gemType' ] )[0][0]]
    print gemType
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
    
    print('Initializing histograms')
    from gempython.utils.nesteddict import nesteddict as ndict, flatten

    # Summary plots - 2D
    dict_h_vfatObsVsVfatPulsed = ndict() #Keys as: [isValid][calEnable][rate]

    # VFAT lvl plots - 1D
    dict_h_sbitMulti = ndict() #Keys as: [isValid][calEnable][rate][vfat]
    dict_h_sbitSize = ndict() #Keys as: [isValid][calEnable][rate][vfat]

    # VFAT lvl plots - 2D 
    dict_g_rateObsCTP7VsRatePulsed = ndict() #Keys as: [isValid][vfat]
    dict_g_rateObsFPGAVsRatePulsed = ndict() #Keys as: [isValid][vfat]
    dict_g_rateObsVFATVsRatePulsed = ndict() #Keys as: [isValid][vfat]
    dict_h_chanVsRatePulsed_ZRateObs = ndict() #Z axis is rate observed; Keys as: [isValid][calEnable][vfat]
    dict_h_sbitObsVsChanPulsed = ndict() #Keys as: [isValid][calEnable][rate][vfat]
    dict_h_sbitMultiVsSbitSize = ndict() #Keys as: [isValid][calEnable][rate][vfat]

    rateMap = {}
    from gempython.gemplotting.utils.anautilities import formatSciNotation
    for isValid in isValidValues:
        if not isValid and not args.checkInvalid:
            continue

        if isValid:
            strValidity="validSbits"
        else:
            strValidity="invalidSbits"

        for calEnable in calEnableValues:
            if calEnable:
                strCalStatus="calEnabled"
                strPulsedOrUnmasked="Pulsed"
            else:
                strCalStatus="calDisabled"
                strPulsedOrUnmasked="Unmasked"

            postScript = "{0}_{1}".format(strValidity,strCalStatus)

            # Summary Case
            for rate in ratesUsed:
                if ( not ( (calEnable and rate > 0) or (not calEnable and rate == 0.0) ) ):
                    continue

                # 2D Observables
                dict_h_vfatObsVsVfatPulsed[isValid][calEnable][rate] = r.TH2F(
                        "h_vfatObservedVsVfatPulsed_{0}_{1}Hz".format(postScript,int(rate)),
                        "Summmary - Rate {0} Hz;VFAT {1};VFAT Observed".format(int(rate),strPulsedOrUnmasked),
                        nVFATS,-0.5,nVFATS-0.5, nVFATS,-0.5,nVFATS-0.5)
                dict_h_vfatObsVsVfatPulsed[isValid][calEnable][rate].Sumw2()

            for vfat in range(0, nVFATS):
                dict_h_chanVsRatePulsed_ZRateObs[isValid][calEnable][vfat] = r.TH2F(
                        "h_chanVsRatePulsed_ZRateObs_vfat{0}_{1}".format(vfat,postScript),
                        "VFAT{0};Rate #left(Hz#right);Channel",
                        len(ratesUsed),0,len(ratesUsed),
                        maxChans, -0.5, maxChans-0.5)

                # Overall Rate Observed by CTP7
                if calEnable:
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat] = r.TGraphErrors()
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetName(
                            "g_rateObsCTP7VsRatePulsed_vfat{0}_{1}".format(vfat,strValidity))
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetTitle(
                            "VFAT {0};Rate Pulsed #left(Hz#right);Rate Observed #left(Hz#right)".format(vfat))
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetLineColor(r.kBlue)
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetLineWidth(2)
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetMarkerColor(r.kBlue)
                    dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].SetMarkerStyle(22)

                    # Overall Rate Observed by OH FPGA
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat] = r.TGraphErrors()
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetName(
                            "g_rateObsFPGAVsRatePulsed_vfat{0}_{1}".format(vfat,strValidity))
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetTitle(
                            "VFAT {0};Rate Pulsed #left(Hz#right);Rate Observed #left(Hz#right)".format(vfat))
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetLineColor(r.kRed)
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetLineWidth(2)
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetMarkerColor(r.kRed)
                    dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].SetMarkerStyle(23)

                    # Per VFAT Rate Observed by OH
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat] = r.TGraphErrors()
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetName(
                            "g_rateObsVFATVsRatePulsed_vfat{0}_{1}".format(vfat,strValidity))
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetTitle(
                            "VFAT {0};Rate Pulsed #left(Hz#right);Rate Observed #left(Hz#right)".format(vfat))
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetLineColor(r.kGreen)
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetLineWidth(2)
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetMarkerColor(r.kGreen)
                    dict_g_rateObsVFATVsRatePulsed[isValid][vfat].SetMarkerStyle(24)

                for binX,rate in enumerate(ratesUsed):
                    if vfat == 0: # Summary Case
                        # Set bin labels
                        rateMap[rate]=binX+1 # Used later to translate rate to bin position
                    dict_h_chanVsRatePulsed_ZRateObs[isValid][calEnable][vfat].GetXaxis().SetBinLabel(binX+1,formatSciNotation(str(rate)))

                    # VFAT level
                    if (calEnable or (not calEnable and rate == 0.0)):
                        # 1D Obs
                        dict_h_sbitMulti[isValid][calEnable][rate][vfat] = r.TH1F(
                                "h_sbitMulti_vfat{0}_{1}_{2}Hz".format(vfat,postScript,int(rate)),
                                "VFAT{0} - Rate {1} Hz;SBIT Multiplicity;N".format(vfat,int(rate)),
                                9,-0.5,8.5)
                        dict_h_sbitMulti[isValid][calEnable][rate][vfat].Sumw2()

                        dict_h_sbitSize[isValid][calEnable][rate][vfat] = r.TH1F(
                                "h_sbitSize_vfat{0}_{1}_{2}Hz".format(vfat,postScript,int(rate)),
                                "VFAT{0} - Rate {1} Hz;SBIT Size;N".format(vfat,int(rate)),
                                8,-0.5,7.5)
                        dict_h_sbitSize[isValid][calEnable][rate][vfat].Sumw2()

                        # 2D Obs
                        dict_h_sbitObsVsChanPulsed[isValid][calEnable][rate][vfat] = r.TH2F(
                                "h_sbitObsVsChanPulsed_vfat{0}_{1}_{2}Hz".format(vfat,postScript,int(rate)),
                                "VFAT{0} - Rate {1} Hz;Channel {2};SBIT Observed".format(vfat,int(rate),strPulsedOrUnmasked),
                                maxChans, -0.5, maxChans-0.5,64,-0.5,63.5)
                        dict_h_sbitObsVsChanPulsed[isValid][calEnable][rate][vfat].Sumw2()

                        dict_h_sbitMultiVsSbitSize[isValid][calEnable][rate][vfat] = r.TH2F(
                                "h_sbitMultiVsSbitSize_vfat{0}_{1}_{2}Hz".format(vfat,postScript,int(rate)),
                                "VFAT{0} - Rate {1} Hz;SBIT Size;SBIT Multiplicity".format(vfat,int(rate)),
                                8,-0.5,7.5,9,-0.5,8.5)
                        dict_h_sbitMultiVsSbitSize[isValid][calEnable][rate][vfat].Sumw2()

    print("Looping over events and filling histograms")
    dict_validSbitsPerEvt = ndict()
    dict_listSbitSizesPerEvt = ndict()
    dict_wrongSbit2ChanMapping = ndict() # Keys [vfatN][vfatSBIT][sbitSize] = number of occurrences
    dict_wrongVfatObs2VfatPulsedMapping = ndict() # Key [(vfatN,vfatObs)] = number of occurrences
    from math import floor, sqrt
    lastPrintedEvt = 0
    for entry in inF.sbitDataTree:
        # Get Values from tree for readability
        calEnable = entry.calEnable
        evtNum = entry.evtNum
        isValid = entry.isValid
        rate = entry.ratePulsed
        rateObsCTP7 = entry.rateObservedCTP7
        rateObsFPGA = entry.rateObservedFPGA
        rateObsVFAT = entry.rateObservedVFAT
        sbitSize = entry.sbitClusterSize
        vfatCH = entry.vfatCH
        vfatSBIT = entry.vfatSBIT
        vfatN = entry.vfatN
        vfatObs = entry.vfatObserved

        if( (evtNum % 1000) == 0 and lastPrintedEvt != evtNum):
            lastPrintedEvt = evtNum
            print("processed {0} events so far".format(entry.evtNum))

        # Skip this event because it's invaldi?
        if not isValid and not args.checkInvalid:
            continue

        # Summary Plots
        dict_h_vfatObsVsVfatPulsed[isValid][calEnable][rate].Fill(vfatN,vfatObs)

        if(vfatN == vfatObs): # Fill the following plots only when isVFATMappingCorrect is true
            # Track if sbit is mismatched
            if (vfatSBIT != floor(vfatCH/2)):
                if (sbitSize in dict_wrongSbit2ChanMapping[vfatN][vfatSBIT].keys()):
                    dict_wrongSbit2ChanMapping[vfatN][vfatSBIT][sbitSize] += 1
                else:
                    dict_wrongSbit2ChanMapping[vfatN][vfatSBIT][sbitSize] = 1

            # Track sbit multiplicity
            if evtNum in dict_validSbitsPerEvt[isValid][calEnable][rate][vfatN].keys():
                if isValid:
                    dict_validSbitsPerEvt[isValid][calEnable][rate][vfatN][evtNum]+=1
            else:
                if isValid:
                    dict_validSbitsPerEvt[isValid][calEnable][rate][vfatN][evtNum]=1
                else:
                    dict_validSbitsPerEvt[isValid][calEnable][rate][vfatN][evtNum]=0

            # Store sbit size
            if evtNum in dict_listSbitSizesPerEvt[isValid][calEnable][rate][vfatN].keys():
                if isValid:
                    dict_listSbitSizesPerEvt[isValid][calEnable][rate][vfatN][evtNum].append(sbitSize)
            else:
                if isValid:
                    dict_listSbitSizesPerEvt[isValid][calEnable][rate][vfatN][evtNum] = [sbitSize]
                else:
                    dict_listSbitSizesPerEvt[isValid][calEnable][rate][vfatN][evtNum] = []

            # VFAT lvl plots - 1D
            dict_h_sbitSize[isValid][calEnable][rate][vfatN].Fill(sbitSize)

            # VFAT lvl plots - 2D
            newPt = dict_g_rateObsCTP7VsRatePulsed[isValid][vfatN].GetN()
            dict_g_rateObsCTP7VsRatePulsed[isValid][vfatN].SetPoint(
                    newPt,
                    rate,
                    rateObsCTP7)
            dict_g_rateObsCTP7VsRatePulsed[isValid][vfatN].SetPointError(
                    newPt,
                    0,
                    sqrt(rateObsCTP7))

            newPt = dict_g_rateObsFPGAVsRatePulsed[isValid][vfatN].GetN()
            dict_g_rateObsFPGAVsRatePulsed[isValid][vfatN].SetPoint(
                    newPt,
                    rate,
                    rateObsFPGA)
            dict_g_rateObsFPGAVsRatePulsed[isValid][vfatN].SetPointError(
                    newPt,
                    0,
                    sqrt(rateObsFPGA))

            newPt = dict_g_rateObsVFATVsRatePulsed[isValid][vfatN].GetN()
            dict_g_rateObsVFATVsRatePulsed[isValid][vfatN].SetPoint(
                    newPt,
                    rate,
                    rateObsVFAT)
            dict_g_rateObsVFATVsRatePulsed[isValid][vfatN].SetPointError(
                    newPt,
                    0,
                    sqrt(rateObsVFAT))

            #dict_h_chanVsRatePulsed_ZRateObs

            dict_h_sbitObsVsChanPulsed[isValid][calEnable][rate][vfatN].Fill(vfatCH,vfatSBIT)
        else: #VFAT Mapping is incorrect?
            if( (vfatN,vfatObs) in dict_wrongVfatObs2VfatPulsedMapping.keys()):
                dict_wrongVfatObs2VfatPulsedMapping[(vfatN,vfatObs)] += 1
            else:
                dict_wrongVfatObs2VfatPulsedMapping[(vfatN,vfatObs)] = 1

    print("Filling multiplicity distributions")
    for isValid in isValidValues:
        if not isValid and not args.checkInvalid:
            continue
        
        for calEnable in calEnableValues:
            for rate in ratesUsed:
                for vfat in range(0, nVFATS):
                    for event,multi in dict_validSbitsPerEvt[isValid][calEnable][rate][vfat].iteritems():
                        dict_h_sbitMulti[isValid][calEnable][rate][vfat].Fill(multi)

                        for size in dict_listSbitSizesPerEvt[isValid][calEnable][rate][vfat][event]:
                            dict_h_sbitMultiVsSbitSize[isValid][calEnable][rate][vfat].Fill(size,multi)
    
    print("Making summary plots")
    from gempython.gemplotting.utils.anautilities import addPlotToCanvas, getSummaryCanvas
    for isValid in isValidValues:
        if not isValid and not args.checkInvalid:
            continue
        
        if isValid:
            strValidity="validSbits"
        else:
            strValidity="invalidSbits"

        # All Rates
        rateCanvas = getSummaryCanvas(dict_g_rateObsCTP7VsRatePulsed[isValid],
                                      name="rateObservedVsRatePulsed_{0}".format(strValidity),
                                      drawOpt="APE1", gemType=gemType)
        rateCanvas = addPlotToCanvas(rateCanvas, dict_g_rateObsFPGAVsRatePulsed[isValid], drawOpt="PE1", gemType=gemType)
        rateCanvas = addPlotToCanvas(rateCanvas, dict_g_rateObsVFATVsRatePulsed[isValid], drawOpt="PE1", gemType=gemType)
        
        # Make the legend
        rateLeg = r.TLegend(0.5,0.5,0.9,0.9)
        rateLeg.AddEntry(
                dict_g_rateObsCTP7VsRatePulsed[isValid][0],
                "CTP7 Rate",
                "LPE")
        rateLeg.AddEntry(
                dict_g_rateObsFPGAVsRatePulsed[isValid][0],
                "FPGA Rate",
                "LPE")
        rateLeg.AddEntry(
                dict_g_rateObsVFATVsRatePulsed[isValid][0],
                "VFAT Rate",
                "LPE")

        rateCanvas.cd(1)
        rateLeg.Draw("same")

        # Save Canvas
        rateCanvas.SaveAs("{0}/rateObservedVsRatePulsed_{1}.png".format(filename,strValidity))

        # CalDisable rate 0 case
        getSummaryCanvas(dict_h_sbitMulti[isValid][0][0], name="{0}/sbitMulti_{1}_calDisabled_0Hz.png".format(filename,strValidity), drawOpt="", gemType=gemType, write2Disk=True)
        getSummaryCanvas(dict_h_sbitSize[isValid][0][0], name="{0}/sbitSize_{1}_calDisabled_0Hz.png".format(filename,strValidity), drawOpt="", gemType=gemType, write2Disk=True)

        getSummaryCanvas(dict_h_sbitObsVsChanPulsed[isValid][0][0], name="{0}/sbitObsVsChanUnmasked_{1}_calDisabled_0Hz.png".format(filename,strValidity), drawOpt="COLZ", gemType=gemType, write2Disk=True)
        getSummaryCanvas(dict_h_sbitMultiVsSbitSize[isValid][0][0], name="{0}/sbitMultiVsSbitSize_{1}_calDisabled_0Hz.png".format(filename,strValidity), drawOpt="COLZ", gemType=gemType, write2Disk=True)
        
        for idx,rate in enumerate(ratesUsed):
            # Sum over all rates
            if rate > 0:
                if (-1 not in dict_h_vfatObsVsVfatPulsed[isValid][1].keys()):
                    name = dict_h_vfatObsVsVfatPulsed[isValid][1][rate].GetName()
                    title = dict_h_vfatObsVsVfatPulsed[isValid][1][rate].GetTitle()
                    dict_h_vfatObsVsVfatPulsed[isValid][1][-1] = dict_h_vfatObsVsVfatPulsed[isValid][1][rate].Clone(name.replace("{0}Hz".format(int(rate)),"SumOfAllRates"))
                    dict_h_vfatObsVsVfatPulsed[isValid][1][-1].SetTitle(title.replace("Rate {0} Hz".format(int(rate)), "Sum of All Rates"))
                else:
                    dict_h_vfatObsVsVfatPulsed[isValid][1][-1].Add(dict_h_vfatObsVsVfatPulsed[isValid][1][rate])

                cloneExists = { vfat:False for vfat in range(0, nVFATS) }
                for vfat in range(0, nVFATS):
                    if ( not cloneExists[vfat] ):
                        cloneExists[vfat] = True

                        name = dict_h_sbitMulti[isValid][1][rate][vfat].GetName()
                        title = dict_h_sbitMulti[isValid][1][rate][vfat].GetTitle()
                        dict_h_sbitMulti[isValid][1][-1][vfat] = dict_h_sbitMulti[isValid][1][rate][vfat].Clone(name.replace("{0}Hz".format(int(rate)),"SumOfAllRates"))
                        dict_h_sbitMulti[isValid][1][-1][vfat].SetTitle(title.replace("Rate {0} Hz".format(int(rate)), "Sum of All Rates"))
                        
                        name = dict_h_sbitSize[isValid][1][rate][vfat].GetName()
                        title = dict_h_sbitSize[isValid][1][rate][vfat].GetTitle()
                        dict_h_sbitSize[isValid][1][-1][vfat] = dict_h_sbitSize[isValid][1][rate][vfat].Clone(name.replace("{0}Hz".format(int(rate)),"SumOfAllRates"))
                        dict_h_sbitSize[isValid][1][-1][vfat].SetTitle(title.replace("Rate {0} Hz".format(int(rate)), "Sum of All Rates"))

                        name = dict_h_sbitObsVsChanPulsed[isValid][1][rate][vfat].GetName()
                        title = dict_h_sbitObsVsChanPulsed[isValid][1][rate][vfat].GetTitle()
                        dict_h_sbitObsVsChanPulsed[isValid][1][-1][vfat] = dict_h_sbitObsVsChanPulsed[isValid][1][rate][vfat].Clone(name.replace("{0}Hz".format(int(rate)),"SumOfAllRates"))
                        dict_h_sbitObsVsChanPulsed[isValid][1][-1][vfat].SetTitle(title.replace("Rate {0} Hz".format(int(rate)), "Sum of All Rates"))

                        name = dict_h_sbitMultiVsSbitSize[isValid][1][rate][vfat].GetName()
                        title = dict_h_sbitMultiVsSbitSize[isValid][1][rate][vfat].GetTitle()
                        dict_h_sbitMultiVsSbitSize[isValid][1][-1][vfat] = dict_h_sbitMultiVsSbitSize[isValid][1][rate][vfat].Clone(name.replace("{0}Hz".format(int(rate)),"SumOfAllRates"))
                        dict_h_sbitMultiVsSbitSize[isValid][1][-1][vfat].SetTitle(title.replace("Rate {0} Hz".format(int(rate)), "Sum of All Rates"))
                    else:
                        dict_h_sbitMulti[isValid][1][-1][vfat].Add(dict_h_sbitMulti[isValid][1][rate][vfat])
                        dict_h_sbitSize[isValid][1][-1][vfat].Add(dict_h_sbitSize[isValid][1][rate][vfat])
                        dict_h_sbitObsVsChanPulsed[isValid][1][-1][vfat].Add(dict_h_sbitObsVsChanPulsed[isValid][1][rate][vfat])
                        dict_h_sbitMultiVsSbitSize[isValid][1][-1][vfat].Add(dict_h_sbitMultiVsSbitSize[isValid][1][rate][vfat])
        
                getSummaryCanvas(dict_h_sbitMulti[isValid][1][-1], name="{0}/sbitMulti_{1}_calEnabled_SumOfAllRates.png".format(filename,strValidity), drawOpt="", gemType=gemType, write2Disk=True)
                getSummaryCanvas(dict_h_sbitSize[isValid][1][-1], name="{0}/sbitSize_{1}_calEnabled_SumOfAllRates.png".format(filename,strValidity), drawOpt="", gemType=gemType, write2Disk=True)

                getSummaryCanvas(dict_h_sbitObsVsChanPulsed[isValid][1][-1], name="{0}/sbitObsVsChanPulsed_{1}_calEnabled_SumOfAllRates.png".format(filename,strValidity), drawOpt="COLZ", gemType=gemType, write2Disk=True)
                getSummaryCanvas(dict_h_sbitMultiVsSbitSize[isValid][1][-1], name="{0}/sbitMultiVsSbitSize_{1}_calEnabled_SumOfAllRates.png".format(filename,strValidity), drawOpt="COLZ", gemType=gemType, write2Disk=True)

    print("Storing TObjects in output TFile")
    # Per VFAT Plots
    for vfat in range(0, nVFATS):
        dirVFAT = outF.mkdir("VFAT{0}".format(vfat))

        for isValid in isValidValues:
            if not isValid and not args.checkInvalid:
                continue

            if isValid:
                strValidity="validSbits"
            else:
                strValidity="invalidSbits"
            dirIsValid = dirVFAT.mkdir(strValidity)
            dirIsValid.cd()
            dict_g_rateObsCTP7VsRatePulsed[isValid][vfat].Write()
            dict_g_rateObsFPGAVsRatePulsed[isValid][vfat].Write()
            dict_g_rateObsVFATVsRatePulsed[isValid][vfat].Write()

            for calEnable in calEnableValues:
                if calEnable:
                    strCalStatus="calEnabled"
                else:
                    strCalStatus="calDisabled"

                dirCalStatus = dirIsValid.mkdir(strCalStatus)
                if calEnable:
                    dirCalStatus.cd()
                    dict_h_sbitMulti[isValid][calEnable][-1][vfat].Write()
                    dict_h_sbitSize[isValid][calEnable][-1][vfat].Write()
                    dict_h_sbitObsVsChanPulsed[isValid][calEnable][-1][vfat].Write()
                    dict_h_sbitMultiVsSbitSize[isValid][calEnable][-1][vfat].Write()

                for rate in ratesUsed:
                    if ( not ( (calEnable and rate > 0) or (not calEnable and rate == 0.0) ) ):
                        continue

                    dirRate = dirCalStatus.mkdir("{0}Hz".format(int(rate)))
                    dirRate.cd()
                    dict_h_sbitMulti[isValid][calEnable][rate][vfat].Write()
                    dict_h_sbitSize[isValid][calEnable][rate][vfat].Write()
                    dict_h_sbitObsVsChanPulsed[isValid][calEnable][rate][vfat].Write()
                    dict_h_sbitMultiVsSbitSize[isValid][calEnable][rate][vfat].Write()

    # Summary Plots
    dirSummary = outF.mkdir("Summary")
    for isValid in isValidValues:
        if not isValid and not args.checkInvalid:
            continue

        if isValid:
            strValidity="validSbits"
        else:
            strValidity="invalidSbits"
        dirIsValid = dirSummary.mkdir(strValidity)

        for calEnable in calEnableValues:
            if calEnable:
                strCalStatus="calEnabled"
            else:
                strCalStatus="calDisabled"

            dirCalStatus = dirIsValid.mkdir(strCalStatus)

            if calEnable:
                dirCalStatus.cd()
                dict_h_vfatObsVsVfatPulsed[isValid][calEnable][-1].Write() 

            for rate in ratesUsed:
                if ( not ( (calEnable and rate > 0) or (not calEnable and rate == 0.0) ) ):
                    continue

                dirRate = dirCalStatus.mkdir("{0}Hz".format(int(rate)))
                dirRate.cd()
                dict_h_vfatObsVsVfatPulsed[isValid][calEnable][rate].Write() 

    # Close input TFile
    inF.Close()
    
    # Close output TFile
    outF.Close()

    arrayPos=0
    list_nameNtype = [('vfatN','i4'),('vfatSBIT','i4'),('sbitSize','i4'),('N_Mismatches','i4')]
    wrongSBITMapping = np.zeros(len(flatten(dict_wrongSbit2ChanMapping)), dtype=list_nameNtype)
    for vfat,dictBadSBits in dict_wrongSbit2ChanMapping.iteritems():
        for sbit,dictSizeCounts in dictBadSBits.iteritems():
            for size,nTimes in dictSizeCounts.iteritems():
                wrongSBITMapping[arrayPos]['vfatN'] = vfat
                wrongSBITMapping[arrayPos]['vfatSBIT'] = sbit
                wrongSBITMapping[arrayPos]['sbitSize'] = size
                wrongSBITMapping[arrayPos]['N_Mismatches'] = nTimes
                arrayPos+=1
    wrongSBITMapping.sort(order=['vfatN','vfatSBIT','sbitSize','N_Mismatches'])

    fileMisMappedSbits = open("{0}/MisMappedSbits.txt".format(filename),"w")
    print("List Of Mis-mapped Sbits")
    fileMisMappedSbits.write("List Of Mis-mapped Sbits\n")
    print("| vfatN | vfatSBIT | SBIT_Size | N_Mismatches |")
    fileMisMappedSbits.write("| vfatN | vfatSBIT | SBIT_Size | N_Mismatches |\n")
    print("| :---: | :------: | :-------: | :----------: |")
    fileMisMappedSbits.write("| :---: | :------: | :-------: | :----------: |\n")
    for idx in range(0,len(wrongSBITMapping)):
        print("| {0:5d} | {1:8d} | {2:9d} | {3:12d} |".format(
            wrongSBITMapping[idx]['vfatN'],
            wrongSBITMapping[idx]['vfatSBIT'],
            wrongSBITMapping[idx]['sbitSize'],
            wrongSBITMapping[idx]['N_Mismatches']))
        fileMisMappedSbits.write("| {0} | {1} | {2} | {3} |\n".format(
            wrongSBITMapping[idx]['vfatN'],
            wrongSBITMapping[idx]['vfatSBIT'],
            wrongSBITMapping[idx]['sbitSize'],
            wrongSBITMapping[idx]['N_Mismatches']))
    fileMisMappedSbits.close()

    list_nameNtype = [('vfatN','i4'),('vfatObs','i4'),('N_Mismatches','i4')]
    wrongVFATMapping = np.zeros(len(dict_wrongVfatObs2VfatPulsedMapping), dtype=list_nameNtype)
    for idx,vfatTuple in enumerate(dict_wrongVfatObs2VfatPulsedMapping.keys()):
        wrongVFATMapping[idx]['vfatN']=vfatTuple[0]
        wrongVFATMapping[idx]['vfatObs']=vfatTuple[1]
        wrongVFATMapping[idx]['N_Mismatches']=dict_wrongVfatObs2VfatPulsedMapping[vfatTuple]
    wrongVFATMapping.sort(order='vfatN')

    fileMisMappedVFATs = open("{0}/MisMappedVFATs.txt".format(filename),"w")
    print("List of Mis-mapped VFATs")
    fileMisMappedVFATs.write("List of Mis-mapped VFATs\n")
    print("| vfatPulsed | vfatObserved | N_Mismatches |")
    fileMisMappedVFATs.write("| vfatPulsed | vfatObserved | N_Mismatches |\n")
    print("| :--------: | :----------: | :----------: |")
    fileMisMappedVFATs.write("| :--------: | :----------: | :----------: |\n")
    for idx in range(0,len(wrongVFATMapping)):
        print("| {0:10d} | {1:12d} | {2:12d} |".format(
            wrongVFATMapping[idx]['vfatN'],
            wrongVFATMapping[idx]['vfatObs'],
            wrongVFATMapping[idx]['N_Mismatches']))
        fileMisMappedVFATs.write("| {0} | {1} | {2} |".format(
            wrongVFATMapping[idx]['vfatN'],
            wrongVFATMapping[idx]['vfatObs'],
            wrongVFATMapping[idx]['N_Mismatches']))
    fileMisMappedVFATs.close()

    print("\nDone")
