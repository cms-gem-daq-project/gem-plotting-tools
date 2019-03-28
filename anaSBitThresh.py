#!/bin/env python

"""
anaSBitThresh
=============
"""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')
    parser.add_argument("infilename", type=str, help="Filename from which input data is contained, expected to have a TTree called 'rateTree' with branches defined by the gemSbitRateTreeStructure class")
    parser.add_argument('-d','--debug', action='store_true', help="Prints additional debugging information")
    parser.add_argument('-o','--outfilename', type=str, default="SBitRatePlots.root", help="Filename to which analyzed data is written")
    parser.add_argument("--maxNoiseRate", type=float, dest="maxNoiseRate", default=0,
                    help="Max Noise Rate allowed in Hz")
    args = parser.parse_args()

    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    import os
    elogPath = os.getenv("ELOG_PATH")

    # load input file
    import ROOT as r
    sbitThreshFile = r.TFile(args.infilename,"READ")

    # determine scandate
    if len(args.infilename.split('/')) > 1 and len(args.infilename.split('/')[len(args.infilename.split('/')) - 2].split('.')) == 5:
        scandate = args.infilename.split('/')[len(args.infilename.split('/')) - 2]
    else:    
        scandate = 'noscandate'

    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, sbitRateAnalysis
    anaResults = sbitRateAnalysis(
            chamber_config = chamber_config, 
            rateTree = sbitThreshFile.rateTree,
            cutOffRate = args.maxNoiseRate,
            debug = args.debug,
            outfilename = args.outfilename,
            scandate = scandate)

    perchannel = anaResults[0]
    dict_dacValsBelowCutOff = anaResults[1]

    for ohKey,innerDictByVFATKey in dict_dacValsBelowCutOff["THR_ARM_DAC"].iteritems():
        if scandate == 'noscandate':
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(elogPath,chamber_config[ohKey]),'w')
        else:
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
            else:
                strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                pass
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(strDirName,scandate),'w')
            pass

        vfatConfg.write("vfatN/I:vt1/I:trimRange/I\n")
        for vfat,armDACVal in innerDictByVFATKey.iteritems():
            vfatConfg.write('%i\t%i\t%i\n'%(vfat, armDACVal,0))
            pass
        vfatConfg.close()
        pass

    print('Analysis Completed Successfully')
