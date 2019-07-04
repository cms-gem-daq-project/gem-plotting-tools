#!/bin/env python

"""
anaUltraThreshold
=================
"""

if __name__ == '__main__':
    # Define the parser
    import argparse
    from gempython.gemplotting.utils.anaoptions import parent_parser
    parser = argparse.ArgumentParser(description="Options to give to anaUltraThreshold.py", parents=[parent_parser])
    
    # Positional arguments
    parser.add_argument("GEBtype",type=str,help="Specify GEB type, options are 'long,short,m1,...,m8', if analyzing data from an ME0 detector write 'null'")
    
    # Optional Arguments
    parser.add_argument("--fileScurveFitTree", type=str, default=None, help="TFile containing scurveFitTree from this detector, if provided this will provide an updated chConfig file taking into account analysis here and data stored in the scurveFitTree")
    parser.add_argument("--isVFAT2", action="store_true", default=False, help="Provide this argument if input data was acquired from vfat2")
    parser.add_argument("--pervfat", action="store_true", help="Analysis for a per-VFAT scan (default is per-channel)")
    parser.add_argument("--doNotSavePlots", action="store_true", help="If provided output plots will not be made")
    parser.add_argument("--zscore", type=float, default=3.5, help="Z-Score for Outlier Identification in MAD Algo")

    from gempython.gemplotting.utils.threshAlgos import anaUltraThreshold
    parser.set_defaults(func=anaUltraThreshold,outfilename="ThresholdPlots.root")
    args = parser.parse_args()
   
    # Make output directory
    from gempython.utils.wrappers import runCommand
    filePath = args.infilename.replace('.root','')
    runCommand(["mkdir", "-p", "{0}".format(filePath)])
    runCommand(["chmod", "g+rw", "{0}".format(filePath)])

    # Run Analysis
    import ROOT as r
    from gempython.utils.gemlogger import printRed
    import os, sys, traceback
    try:
        args.func(args,args.infilename,args.GEBtype,filePath,args.fileScurveFitTree)
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
