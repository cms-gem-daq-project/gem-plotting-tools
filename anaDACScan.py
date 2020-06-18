#!/usr/bin/env python

r"""
``anaDACScan`` -- analyzes DAC scan data
========================================

Synopsis
--------

**anaDACScan.py** [*OPTIONS*]

Description
-----------

This script reads in ADC0 or ADC1 calibration coefficients and DAC scan data, performs a fit for each VFAT, computes the DAC value corresponding to the nominal current or voltage for each VFAT, and reports the results.

Arguments
---------

.. program:: anaDACScan.py

.. option:: infilename

    Name of the input file root.

.. option:: --assignXErrors  

    If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case). 

.. option:: --calFileList
  
    Provide a file containing a list of calFiles.  The space character is used as a delimiter.  The first three columns are respectively shelf, slot and link number.  The fourth column is the calibration file (given with full physical filename) for that link number. Example::

    1 4 0 /path/to/my/cal/file.txt
    1 4 1 /path/to/my/cal/file.txt
    ...
    ...

.. option:: --outfilename

    Name of the output root file. Default is DACFitData.root.

.. option:: --print

    If provided prints a summary table to terminal for each DAC showing for each VFAT position the nominal value that was found

Example
-------

.. code-block:: bash

    anaDACScan.py /path/to/input.root  --calFileList calibration.txt --assignXErrors
"""

if __name__ == '__main__':
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')

    parser.add_argument('infilename', type=str, help="Filename from which input information is read")
    parser.add_argument('--assignXErrors', dest='assignXErrors', action='store_true', help="If this flag is set then an uncertain on the DAC register value is assumed, otherwise the DAC register value is assumed to be a fixed unchanging value (almost always the case).")
    parser.add_argument("--calFileList", type=str, help="File specifying which calFile to use for each OH. Format of each line: <shelf> <slot> <link> /path/to/my/cal/file.txt")
    parser.add_argument('-o','--outfilename', dest='outfilename', type=str, default="DACFitData.root", help="Filename to which output information is written")
    parser.add_argument("-p","--print",dest="printSum", action="store_true", help="If provided prints a summary table to terminal for each DAC showing for each VFAT position the nominal value that was found")
    args = parser.parse_args()

    print("Analyzing: '%s'"%args.infilename)

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)
    
    dacScanFile = r.TFile(args.infilename,"READ")

    if len(args.infilename.split('/')) > 1 and len(args.infilename.split('/')[len(args.infilename.split('/')) - 2].split('.')) == 5:
        scandate = args.infilename.split('/')[len(args.infilename.split('/')) - 2]
    else:    
        scandate = 'noscandate'

    from gempython.gemplotting.utils.anautilities import dacAnalysis
    from gempython.gemplotting.utils.exceptions import DACAnalysisException
    try:
        dacAnalysis(args, dacScanFile.dacScanTree, chamber_config, scandate=scandate)
    except DACAnalysisException as err:
        from gempython.utils.gemlogger import printRed
        printRed(err.message)
        printRed("VFATs above may *NOT* be properly biased")
    dacScanFile.Close()

    print("\nAnalysis completed. Goodbye")
