#!/bin/env python

r"""
``calibrateThrDac.py`` --- Calibrating CFG_THR_*_DAC of VFAT3
====================

Synopsis
--------

**calibrateThrDac.py** :token:`--fitRange` <*FIT RANGE*> :token:`--listOfVFATs` <*LIST OF VFATS INPUT FILE*> :token:`--noLeg` :token:`--savePlots` :token:[*FILENAME*]

Description
-----------

The :program:`calibrateThrDac.py` tool is for calibrating either the ``CFG_THR_ARM_DAC`` or the ``CFG_THR_ZCC_DAC`` register of a set of ``vfat3`` ``ASIC``s.  The user should have taken a set of scurves at varying ``CFG_THR_X_DAC`` settings, for ``X={ARM,ZCC}``. Then these scurves are expected to have been analyzed, including fitting, with the :program:`anaUltraScurve.py`.  The correct `CFG_CAL_DAC` calibration must have been used during this analysis.

The ``FILENAME`` file is expected to be in the :any:`Three Column Format` with the independent variable being ``CFG_THR_X_DAC``. For each scandate in ``FILENAME`` the scruve ``gScurveMeanDist_*`` and ``gScurveSigmaDist_*`` ``TGraphErrors`` objects for each VFAT, and summary level, will be fit with a Gaussian distribution.  The mean of this Gaussian will be plotted against the provided ``CFG_THR_X_DAC`` value with the Gaussian's sigma taken as the error on the mean.  The resulting scurveMean(Sigma) vs. ``CFG_THR_X_DAC`` distribution will be fit with a ``pol1``(``pol0``) function.  The fit function for the scurveMean vs. ``CFG_THR_X_DAC`` gives the calibration of the THR DAC in terms of fC while the fit function for the scurveSigma vs. ``CFG_THR_X_DAC`` gives the horizontal asymptote of the average ENC across the ``vfat``.

An output table will be produced at the end of the function call which shows the calibration information and ENC by VFAT position and overall (e.g. vfat position = ``All``).  Numerically the ``All`` case is assigned a value of ``-1``.

Output files will be found in :envvar:`$ELOG\_PATH`.  The ``calFile_CFG_THR_X_DAC_<Det S/N>.txt`` file will be a text file specifying the ``CFG_THR_X_DAC`` calibration parameters (slope and intercept) by vfat position.  Additionally all ``TObject``s created during the analysis will be found in ``calFile_<Det S/N>_CFG_THR_X_DAC.root``.

Mandatory arguments
-------------------

.. option:: [*FILENAME*]

    Physical filename of the input file to be passed to
    :program:`calibrateThrDac.py`.  See :any:`Three Column Format` for
    details on the format and contents of this file.  The independent
    variable is expected to be ``CFG_THR_X_DAC`` for ``X={ARM,ZCC}``.

Optional arguments
------------------

.. option:: --fitRange <FIT RANGE>

    Two comma separated integers which specify the range
    of 'CFG_THR_*_DAC' to use in fitting when deriving the
    calibration curve.

.. option:: --listOfVFATs <LIST OF VFATS INPUT FILE>

    If provided the VFATID will be taken from this file
    rather than scurveTree. Tab delimited file, first line
    is a column header, subsequent lines specify
    respectively VFAT position and VFAT serial number.
    Lines beginning with the '#' character will be skipped.

.. option:: --noLeg

    Do not draw a TLegend on the output plots

.. option:: --savePlots

    Make ``*.png`` file for all plots that will be saved in
    the output TFile

Example
-------

To use the scurve fit results from scandates contained in listOfScanDates_armCal.txt execute:

.. code-block:: bash

    calibrateThrDac.py listOfScanDates_armCal.txt --fitRange=30,150

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

    :envvar:`ELOG_PATH`
        Results are written in the directory pointed to by this variable if no "/" characters appear in ``--filename``

Internals
---------
"""

if __name__ == '__main__':
    # create the parser
    import argparse
    from gempython.gemplotting.utils.anaoptions import parser_scurveChanMasks
    parser = argparse.ArgumentParser(description='Arguments to supply to calibrateThrDac.py',parents=[parser_scurveChanMasks])
    parser.add_argument("inputFile", type=str, help="Tab delimited file specifying the input list of scandates, in three column format, specifying chamberName, scandate, and either CFG_THR_ARM_DAC or CFG_THR_ZCC_DAC value")
    parser.add_argument("-d","--debug", action="store_true", help="Prints additional debugging information")
    parser.add_argument("--fitRange", type=str, default="0,255", 
            help="Two comma separated integers which specify the range of 'CFG_THR_*_DAC' to use in fitting when deriving the calibration curve")
    parser.add_argument("--listOfVFATs", type=str, default=None,
            help="If provided the VFATID will be taken from this file rather than scurveTree.  Tab delimited file, first line is a column header, subsequent lines specify respectively VFAT position and VFAT serial number.  Lines beginning with the '#' character will be skipped")
    parser.add_argument("--numOfGoodChansMin", type=int, default=10, help="Minimum number of channels that must be good (unmasked) for an armDacVal point to be use in the calibration procedure.")
    parser.add_argument("--noLeg", action="store_true", help="Do not draw a TLegend on the output plots")
    parser.add_argument("--savePlots", action="store_true", help="Make *.png file for all plots that will be saved in the output TFile")
    args = parser.parse_args()

    # Check paths
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')

    # Determine outputDir
    if "/" in args.inputFile:
        outputDir = args.inputFile[0:args.inputFile.rfind("/")+1]
    else:
        from gempython.gemplotting.utils.anautilities import getElogPath
        outputDir = getElogPath()
        pass
    
    from gempython.gemplotting.utils.threshAlgos import calibrateThrDAC
    from gempython.utils.gemlogger import printGreen, printRed
    from gempython.utils.wrappers import runCommand
    from gempython.gemplotting.utils.namespace import Namespace
    import os, sys, traceback
    ns = Namespace(
        inputFile=args.inputFile,
        fitRange=args.fitRange,
        listOfVFATs=args.listOfVFATs,
        maxEffPedPercent=args.maxEffPedPercent,
        highNoiseCut=args.highNoiseCut,
        deadChanCutLow=args.deadChanCutLow,
        deadChanCutHigh=args.deadChanCutHigh,
        noLeg=args.noLeg,
        outputDir=outputDir,
        savePlots=args.savePlots,
        debug=args.debug
    )

    try:
        retCode = calibrateThrDAC(ns)
    except IOError as err:
        printRed("IOError: {0}".format(err.message))
        printRed("Analysis failed with error code {0}".format(retCode))
        traceback.print_exc(file=sys.stdout)
        sys.exit(os.EX_IOERR)
    else:
        printGreen("Analysis completed successfully")
    finally:
        from gempython.gemplotting.utils.anautilities import cleanup
        cleanup( [outputDir] )
