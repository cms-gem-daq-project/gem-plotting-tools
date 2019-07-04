#!/bin/env python

"""
anaUltraScurve
==============
"""

if __name__ == '__main__':
    # Define the parser
    import argparse
    from gempython.gemplotting.utils.anaoptions import parent_parser
    parser = argparse.ArgumentParser(description="Options to give to anaUltraScurve.py", parents=[parent_parser])
    
    # Positional arguments
    parser.add_argument("GEBtype",type=str,help="Specify GEB type, options are 'long,short,m1,...,m8', if analyzing data from an ME0 detector write 'null'")
    
    # Optional Arguments
    parser.add_argument("-b", "--drawbad", action="store_true", help="Draw fit overlays for Chi2 > 10000")
    parser.add_argument("--calFile", type=str, default=None, help="File specifying CAL_DAC/VCAL to fC equations per VFAT")
    parser.add_argument("-e", "--extChanMapping", type=str, default=None,
                      help="Physical filename of a custom, non-default, channel mapping (optional)")
    parser.add_argument("--doNotFit", action="store_true", help="Do not attempt to fit scurves; only the summary plot showing the 2D scurve data will be generated")
    parser.add_argument("--isVFAT2", action="store_true", help="Provide this argument if input data was acquired from vfat2")
    parser.add_argument("-v", "--vfatList", type=str, default=None, help="Comma separated list of VFAT positions to consider for analysis.  If not provided default will be all positions")
    parser.add_argument("-z", "--zscore", type=float, default=3.5, help="Z-Score for Outlier Identification in MAD Algo")

    chanMaskGroup = parser.add_argument_group(
            title="Options for channel mask decisions", 
            description="Parameters which specify how Dead, Noisy, and High Pedestal Channels are charaterized")
    chanMaskGroup.add_argument("--maxEffPedPercent", type=float, default=0.05,
                      help="Percentage, Threshold for setting the HighEffPed mask reason, if channel (effPed > maxEffPedPercent * nevts) then HighEffPed is set")
    chanMaskGroup.add_argument("--highNoiseCut", type=float, default=3.0,
            help="Threshold for setting the HighNoise maskReason, if channel (scurve_sigma > highNoiseCut) then HighNoise is set")
    chanMaskGroup.add_argument("--deadChanCutLow", type=float, default=None,
                      help="If channel (deadChanCutLow < scurve_sigma < deadChanCutHigh) then DeadChannel is set")
    chanMaskGroup.add_argument("--deadChanCutHigh", type=float, default=None,
                      help="If channel (deadChanCutHigh < scurve_sigma < deadChanCutHigh) then DeadChannel is set")

    from gempython.gemplotting.utils.scurveAlgos import anaUltraScurve 
    parser.set_defaults(func=anaUltraScurve, outfilename="SCurveFitData.root")
    args = parser.parse_args()
    
    # Make output directory
    from gempython.utils.wrappers import runCommand
    filePath = args.infilename.replace('.root','')
    runCommand(["mkdir", "-p", "{0}".format(filePath)])
    runCommand(["chmod", "g+rw", "{0}".format(filePath)])

    if args.vfatList is not None:
        vfatList = [int(vfat) for vfat in args.vfatList.split(",")]
    else:
        vfatList = None

    # Run Analysis
    from gempython.utils.gemlogger import printRed
    import os, sys, traceback
    try:
        args.func(args,args.infilename,args.calFile,args.GEBtype,filePath,vfatList)
    except RuntimeError as err:
        printRed("RuntimeError: {0}".format(err.message))
        traceback.print_exc(file=sys.stdout)
        sys.exit(os.EX_SOFTWARE)
    except IOError as err:
        printRed("IOError: {0}".format(err.message))
        traceback.print_exc(file=sys.stdout)
        sys.exit(os.EX_IOERR)
    else:
        print('Analysis Completed Successfully')
    finally:
        from gempython.gemplotting.utils.anautilities import cleanup
        cleanup( [filePath] )
