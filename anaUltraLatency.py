#!/bin/env python

r"""
anaUltraLatency
===============

.. moduleauthor:: Anastasia and Cameron Bravo <c.bravo@cern.ch>
.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>
"""

if __name__ == '__main__':
    # Define the parser
    import argparse
    parser = argparse.ArgumentParser(description="Options to give to anaUltraLatency.py")
    parser.add_argument("infilename",type=str,help="Specify Input Filename by full path")
    
    # Optional arguments
    parser.add_argument("-d", "--debug", action="store_true", help="print extra debugging information")
    parser.add_argument("-f", "--fit", action="store_true", dest="performFit",help="Fit the latency distributions")
    parser.add_argument("-o", "--outfilename", type=str, help="Specify Output Filename")
    parser.add_argument("--latSigRange", type=str,  default=None, help="Comma separated pair of values defining expected signal range, e.g. lat #epsilon [41,43] is signal")
    parser.add_argument("--latSigMaskRange", type=str,  default=None, help="Comma separated pair of values defining the region to be masked when trying to fit the noise, e.g. lat #notepsilon [40,44] is noise (lat < 40 || lat > 44)")

    from gempython.gemplotting.utils.latAlgos import anaUltraLatency
    parser.set_defaults(func=anaUltraLatency, outfilename="latencyAna.root")
    args = parser.parse_args()

    # Make output directory
    from gempython.utils.wrappers import runCommand
    filePath = args.infilename.replace('.root','')
    runCommand(["mkdir", "-p", "{0}".format(filePath)])
    runCommand(["chmod", "g+rw", "{0}".format(filePath)])

    # Run Analysis
    from gempython.utils.gemlogger import printRed
    import os, sys, traceback
    try:
        args.func(
                infilename      = args.infilename,
                debug           = args.debug,
                latSigMaskRange = args.latSigMaskRange,
                latSigRange     = args.latSigRange,
                outputDir       = filePath,
                outfilename     = args.outfilename,
                performFit      = args.performFit)
    except IndexError as err:
        printRed("IndexError: {0}".format(err.message))
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
