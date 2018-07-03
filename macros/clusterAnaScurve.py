#!/bin/env python

r"""
``clusterAnaScurve.py`` --- Analyze S-curves using the LSF cluster
==================================================================

Synopsis
--------

**clusterAnaScurve.py** :token:`-q` <*QUEUE*> :token:`-t` *long|short* :token:`--anaType` *scurve|trim* (:token:`--chamberName` <*NAME*> | :token:`-i` <*FILE*>)

Description
-----------

This tool will allow you to re-analyze the scurve data in a straightforward way
without the time consuming process of launching it by hand. Takes a list of
scandates file in the :any:`Two Columns Format`, and launches a job for each
``(chamberName, scandate)`` pair. Each job will launch
:program:`anaUltraScurve.py`.

Mandatory arguments
-------------------

The following list shows the mandatory inputs that must be supplied to execute
the script.

.. program:: clusterAnaScurve.py

.. option:: --anaType scurve|trim

    Analysis type to be executed.

.. option:: --chamberName <CHAMBER NAME>

    Name of detector to be analyzed, from the values in
    :py:data:`gempython.gemplotting.mapping.chamberInfo.chamber_config`. Either
    this option or :option:`--infilename` must be supplied.

.. option:: -i, --infilename <FILE>

    Physical file name of the input file. The format of this input file should
    follow the :any:`Two Column Format`. Either this option or
    :option:`--chamberName` must be supplied.

.. option:: -q, --queue <QUEUE>

    Queue to submit your jobs to. Suggested options are ``8nm``, ``1nh`` and
    ``1nd``.

.. option:: -t, --type long|short

    Specify GEB/detector type.

Optional arguments
------------------

.. option:: --calFile <FILE>

    File specifying CAL_DAC/VCAL to fC equations per VFAT. If this is not
    provided the analysis will default to hardcoded conversion for VFAT2. See
    :py:class:`gempython.gemplotting.fitting.fitScanData.ScanDataFitter` for
    more information.

.. option:: -c, --channels

    Output plots will be made vs VFAT channel instead of ROB strip.

.. option:: -d, --debug

    If provided all cluster files will be created for inspection, and job
    submission commands printed to terminal, but no jobs will be submitted to
    the cluster. Using this option before submitting a large number of jobs is
    strongly recommended.

.. option:: --endDate <YYYY.MM.DD>

    If :option:`--infilename` is not supplied this is the ending scandate, in
    ``YYYY.MM.DD`` format, to be considered for job submission. The default is
    whatever ``datetime.today()`` evaluates to.

.. option:: --extChanMapping <FILE>

    Physical file name of a custom, non-default, channel mapping file. If not
    provided the default slice test ROB strip to VFAT channel mapping will be
    used.

.. option:: -f, --fit

    Fit S-curves and save fit information to output ``TFile``.

.. option:: -p, --panasonic

    Output plots will be made vs Panasonic pins instead of ROB strip.

.. option:: --startDate <YYYY.MM.DD>

    If :option:`--infilename` is not supplied this is the starting scandate, in
    YYYY.MM.DD format, to be considered for job submission. Default is
    ``2017.01.01`` so the start of the slice test will be used.

.. option:: --zscore <NUMBER>

    Z-Score for Outlier Identification in the MAD Algorithm. For details see
    talks by `B. Dorney`_ or `L. Moureaux`_.

    .. _B. Dorney: https://indico.cern.ch/event/638404/contributions/2643292/attachments/1483873/2302543/BDorney_OpsMtg_20170627.pdf

    .. _L. Moureaux: https://indico.cern.ch/event/659794/contributions/2691237/attachments/1508531/2351619/UpdateOnHotChannelIdentificationAlgo.pdf

.. option:: --ztrim <NUMBER>

    Specify the :math:`P`-value of the trim in the quantity:
    ``scurve_mean - ztrim * scurve_sigma``

Finally :program:`clusterAnaScurve.py` can also be passed the cut values used in
assigning a ``maskReason`` described at
:any:`Providing Cuts for ``maskReason`` at Runtime`.

Full Example For P5 S-Curve Data
--------------------------------

Before you start due to space limitations on AFS it is strongly recommended that
your :envvar:`DATA_PATH` variable on lxplus point to the work area rather than
the user area, e.g.:

.. code-block:: bash

    export DATA_PATH=/afs/cern.ch/work/<first-letter-of-your-username>/<your-user-name>/<somepath>

In your work area you can have up to 100GB of space. If this is your first time
using ``lxplus`` you may want to increase your storage quota by following
instructions `here`_.

.. _here: https://resources.web.cern.ch/resources/Help/?kbid=067040

Now connect to the P5 ``dqm`` machine. Then if you are interested in a chamber
``ChamberName`` execute:

.. code-block:: bash

    cd $HOME
    plotTimeSeries.py --listOfScanDatesOnly --startDate=2017.01.01
    packageFiles4Docker.py --ignoreFailedReads --fileListScurve=/gemdata/<ChamberName>/scurve/listOfScanDates.txt --tarBallName=<ChamberName>_scurves.tar --ztrim=4 --onlyRawData

Then connect to ``lxplus``, and after setting up the env execute:

.. code-block:: bash

    cd $DATA_PATH
    scp <your-user-name>@cmsusr.cms:/nfshome0/<your-user-name>/<ChamberName>_scurves.tar .
    tar -xf <ChamberName>_scurves.tar
    mv gemdata/<ChamberName> .
    clusterAnaScurve.py -i <ChamberName>/scurve/listOfScanDates.txt --anaType=scurve -f -q 1nh

It may take some time to finish the job submission. Please pay attention to the
output at the end of the :program:`clusterAnaScurve.py` command as it provides
helpful information for managing jobs and understanding what comes next. Once
your jobs are complete you should check that they all finished successfully. One
way to do this is to check if any of them exited with status ``Exited`` and
check for the exit code. To do this execute:

.. code-block:: bash

    grep -R "exit code" <ChamberName>/scurve/*/stdout/jobOut.txt --color

This will print a single line from all files where the string exit code appears.
For example:

    GEMINIm01L1/scurve/2017.04.10.20.33/stdout/jobOut.txt:Exited with exit code 255.
    GEMINIm01L1/scurve/2017.04.26.12.25/stdout/jobOut.txt:Exited with exit code 255.
    GEMINIm01L1/scurve/2017.04.27.13.27/stdout/jobOut.txt:Exited with exit code 255.
    GEMINIm01L1/scurve/2017.06.07.12.17/stdout/jobOut.txt:Exited with exit code 255.
    GEMINIm01L1/scurve/2017.07.18.11.09/stdout/jobOut.txt:Exited with exit code 255.
    GEMINIm01L1/scurve/2017.07.18.18.34/stdout/jobOut.txt:Exited with exit code 255.

For those lines that appear in the grep output command you will need to check
the standard err of the job which can be found in:

.. code-block:: bash

    <ChamberName>/scurve/<scandate>/stderr/jobErr.txt

Note since some scans at P5 may have failed to complete successfully some jobs
may intrinsically fail and be non-recoverable. If you have questions about a
particular job you can try to search in the e-log around the scandate in time to
see if anything occurred around this time that might cause problems for the
scan. If you would like to re-analyze a failed job you can do so by calling:

.. code-block:: bash

    $DATA_PATH/<ChamberName>/scurve/<scandate>/clusterJob.sh

If a large number of jobs have failed you should spend some time trying to
understand why, and then re-submit to the cluster, rather than attempting to
analyze them all by hand.

Finally after you are satisfied that all the jobs that could complete
successfully have completed you can:

#. Re-package the re-analyzed data into a tarball, and/or
#. Create time series plots to summarize the entire dataset.

For case 1, re-packaging the re-analyzed files into a tarball, execute:

.. code-block:: bash

    packageFiles4Docker.py --ignoreFailedReads --fileListScurve=<ChamberName>/scurve/listOfScanDates.txt --tarBallName=<ChamberName>_scurves_reanalyzed.tar --ztrim=4
    mv <ChamberName>_scurves_reanalyzed.tar $HOME/public
    chmod 755 $HOME/public/<ChamberName>_scurves_reanalyzed.tar
    echo $HOME/public/<ChamberName>_scurves_reanalyzed.tar

Then provide the terminal output of this last command to one of the GEM DAQ
Experts for mass-storage.

For case 2, create time series plots to summarize the entire dataset, execute:

.. code-block:: bash

    <editor of your choice> $VIRTUAL_ENV/lib/python2.7/site-packages/gempython/gemplotting/mapping/chamberInfo.py

And ensure the only uncommented entries of the ``chamber_config`` dictionary
match the set of ChamberName's that you have submitted jobs for. Then execute:

.. code-block:: bash

    plotTimeSeries.py --startDate=2017.01.01 --anaType=scurve

Please note the above command may take some time to process depending on the
number of detectors worth of data you are trying to analyze. Then a series of
output ``*.png`` and ``*.root`` files will be found at:

.. code-block:: bash

    $ELOG_PATH/timeSeriesPlots/<ChamberName>/vt1bump0/

If you would prefer to analyze ChamberName's one at a time, or to have an output
``*.png`` file for each VFAT, you can produce time series plots individually by
executing the :program:`gemPlotter.py` commands provided at the end of the
:program:`clusterAnaScurve.py` output. This might be preferred as when analyzing
a large period of time the 3-by-8 grid plots that :program:`plotTimeSeries.py`
will produce for you may be hard to read. In either case
:program:`gemPlotter.py` or :program:`plotTimeSeries.py` will produce a
``TFile`` for you in which the plots at the per VFAT level are stored for you to
later investigate.

If you encounter issues in this procedure please spend some time trying to
figure out what wrong on your side first. If after studying the documentation
and reviewing the commands you have exeuted you still do not understand the
failure please ask on the ``Software`` channel of the CMS GEM Ops Mattermost
team or submit an issue to the `github page`_.

.. _github page: https://github.com/cms-gem-daq-project/gem-plotting-tools/issues/new

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

    :envvar:`ELOG_PATH`
        Results are written in the directory pointed to by this variable
"""

if __name__ == '__main__':
    from optparse import OptionParser, OptionGroup
    parser = OptionParser()
    parser.add_option("--anaType", type="string", dest="anaType",
                      help="Analysis type to be executed, from list {'scurve','trim'}", metavar="anaType")
    parser.add_option("--calFile", type="string", dest="calFile", default=None,
                      help="File specifying CAL_DAC/VCAL to fC equations per VFAT",
                      metavar="calFile")
    parser.add_option("--chamberName", type="string", dest="chamberName", default=None,
                      help="Detector to submit jobs for. Use instead of --infilename", metavar="chamberName")
    parser.add_option("-c","--channels", action="store_true", dest="channels",
                      help="Make plots vs channels instead of strips", metavar="channels")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="print extra debugging information", metavar="debug")
    parser.add_option("--extChanMapping", type="string", dest="extChanMapping", default=None,
                      help="Physical filename of a custom, non-default, channel mapping (optional)", metavar="extChanMapping")
    parser.add_option("-f", "--fit", action="store_true", dest="performFit",
                      help="Fit scurves and save fit information to output TFile", metavar="performFit")
    parser.add_option("-i", "--infilename", type="string", dest="filename", default=None,
                      help="Tab delimited file specifying chamber name and scandates to analyze", metavar="filename")
    parser.add_option("-p","--panasonic", action="store_true", dest="PanPin",
                      help="Make plots vs Panasonic pins instead of strips", metavar="PanPin")
    parser.add_option("-q","--queue", type="string", dest="queue", default="1nh",
                        help="queue to submit your jobs to", metavar="queue")
    parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                      help="Specify GEB (long/short)", metavar="GEBtype")
    parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                      help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                      help="Specify the p value of the trim", metavar="ztrim")
    
    chanMaskGroup = OptionGroup(
            parser,
            "Options for channel mask decisions"
            "Parameters which specify how Dead, Noisy, and High Pedestal Channels are charaterized")
    chanMaskGroup.add_option("--maxEffPedPercent", type="float", dest="maxEffPedPercent", default=0.05,
                      help="Percentage, Threshold for setting the HighEffPed mask reason, if channel (effPed > maxEffPedPercent * nevts) then HighEffPed is set",
                      metavar="maxEffPedPercent")
    chanMaskGroup.add_option("--highNoiseCut", type="float", dest="highNoiseCut", default=1.0,
                      help="Threshold for setting the HighNoise maskReason, if channel (scurve_sigma > highNoiseCut) then HighNoise is set",
                      metavar="highNoiseCut")
    chanMaskGroup.add_option("--deadChanCutLow", type="float", dest="deadChanCutLow", default=4.14E-02,
                      help="If channel (deadChanCutLow < scurve_sigma < deadChanCutHigh) then DeadChannel is set",
                      metavar="deadChanCutLow")
    chanMaskGroup.add_option("--deadChanCutHigh", type="float", dest="deadChanCutHigh", default=1.09E-01,
                      help="If channel (deadChanCutHigh < scurve_sigma < deadChanCutHigh) then DeadChannel is set",
                      metavar="deadChanCutHigh")
    parser.add_option_group(chanMaskGroup)
    
    dateOptions = OptionGroup(parser,
            "Date Options"
            "Options for specifying the starting and ending date range")
    dateOptions.add_option("--startDate", type="string", dest="startDate", default="2017.01.01",
                      help="Starting date range in YYYY.MM.DD format", metavar="startDate")
    dateOptions.add_option("--endDate", type="string", dest="endDate", default=None,
                      help="Starting date range in YYYY.MM.DD format", metavar="endDate")
    parser.add_option_group(dateOptions)
    
    (options, args) = parser.parse_args()
    listOfScanDatesFile = options.filename

    # Check if the queue is supported
    # See: https://cern.service-now.com/service-portal/article.do?n=KB0000470
    import os
    from gempython.gemplotting.utils.anaInfo import queueNames, tree_names
    if options.queue not in queueNames:
        print("queue '%s' not understood"%options.queue)
        print("list of supported queues is:", queueNames)
        exit(os.EX_USAGE)
        pass

    # Check anaType is understood
    supportedAnaTypes = ['scurve','trim']
    if options.anaType not in supportedAnaTypes:
        print("Invalid analysis specificed, please select only from the list:")
        print(supportedAnaTypes)
        exit(os.EX_USAGE)
        pass

    # Prepare the commands for making the
    from gempython.utils.wrappers import envCheck, runCommand
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    envCheck('VIRTUAL_ENV')

    # Get info from input file
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, filePathExists, makeListOfScanDatesFile, parseListOfScanDatesFile
    if (listOfScanDatesFile is None and options.chamberName is not None):
        makeListOfScanDatesFile(options.chamberName, options.anaType, options.startDate, options.endDate, ztrim=options.ztrim)
        listOfScanDatesFile = '%s/listOfScanDates.txt'%(getDirByAnaType(options.anaType, options.chamberName, options.ztrim))
        pass
    parsedTuple = parseListOfScanDatesFile(listOfScanDatesFile, alphaLabels=True)
    listChamberAndScanDate = parsedTuple[0]

    # Setup output scandates list
    outputScanDatesName = listOfScanDatesFile.strip('.txt')
    outputScanDatesName += "_Input4GemPlotter.txt"
    outputScanDatesFile = open(outputScanDatesName, 'w+')
    outputScanDatesFile.write('ChamberName\tscandate\n')

    # invert chamber_config
    from gempython.gemplotting.mapping.chamberInfo import chamber_config, GEBtype

    linkByChamber = dict( (value,key) for key,value in chamber_config.iteritems() )
    ## Only in python 2.7 and up
    # linkByChamber = { value:key for key,value in chamber_config.iteritems() }
    
    # Make and launch a job for each file
    import time
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType(options.anaType, chamberAndScanDatePair[0], options.ztrim)
        dirPath = "%s/%s"%(dirPath,chamberAndScanDatePair[1])

        # Check if file exists, if it does not write to output as commented line but skip to next input
        if not filePathExists(dirPath, tree_names[options.anaType][0]):
            outputScanDatesFile.write('#%s\t%s\n'%(chamberAndScanDatePair[0],chamberAndScanDatePair[1]))
            continue
        outputScanDatesFile.write('%s\t%s\n'%(chamberAndScanDatePair[0],chamberAndScanDatePair[1]))

        # Input file
        jobInputFile = "%s/%s"%(dirPath, tree_names[options.anaType][0])
        
        # stdout
        jobStdOut = "%s/stdout"%dirPath
        runCommand( ["mkdir","-p", jobStdOut ] )
        if len(os.listdir(jobStdOut)) > 0:
            runCommand( ['rm','%s/jobOut.txt'%(jobStdOut) ] )
            pass

        # stderr
        jobStdErr = "%s/stderr"%dirPath
        runCommand( ["mkdir","-p", jobStdErr ] )
        if len(os.listdir(jobStdErr)) > 0:
            runCommand( ['rm','%s/jobErr.txt'%(jobStdErr) ] )
            pass

        # script to be run by the cluster
        jobScriptName = "%s/clusterJob.sh"%dirPath
        jobScript = open(jobScriptName, 'w+')
        jobScript.write("""#! /usr/bin/env bash

# LSF screws up the environment by prepending things to the PATH. Restore it.
source $VIRTUAL_ENV/bin/activate

python --version
gcc --version | grep gcc
""")

        thisGEB = options.GEBtype
        if chamberAndScanDatePair[0] in linkByChamber.keys():
            thisGEB = GEBtype[linkByChamber[chamberAndScanDatePair[0]]]
            pass

        # make the python command
        pythonCmd = 'anaUltraScurve.py -i %s -t %s --zscore=%f --ztrim=%f --maxEffPedPercent=%f --highNoiseCut=%f --deadChanCutLow=%f --deadChanCutHigh=%f'%(
                jobInputFile,
                thisGEB,
                options.zscore,
                options.ztrim,
                options.maxEffPedPercent,
                options.highNoiseCut,
                options.deadChanCutLow,
                options.deadChanCutHigh)
        if options.calFile is not None:
            pythonCmd += ' --calFile=%s'%(options.calFile)
            pass
        if options.channels:
            pythonCmd += ' --channels'
            pass
        if options.extChanMapping is not None:
            pythonCmd += ' --extChanMapping=%s'%(options.extChanMapping)
            pass
        if options.performFit:
            pythonCmd += ' --fit'
            pass
        if options.PanPin:
            pythonCmd += ' --panasonic'
            pass
        pythonCmd += '\n'
        
        jobScript.write(pythonCmd)
        jobScript.close()
        runCommand( ['chmod', '+x', jobScriptName] )

        jobCmd = [
                'bsub',
                '-env',
                'all',
                '-q',
                options.queue,
                '-o',
                "%s/jobOut.txt"%jobStdOut,
                '-e',
                "%s/jobErr.txt"%jobStdErr,
                jobScriptName ]

        if options.debug:
            print(idx, jobCmd)
            pass
        else:
            runCommand(jobCmd)
            time.sleep(1)
            pass
        pass # end loop over listChamberAndScanDate

    print("Job submission completed")
    print("To check the status of your jobs execute:")
    print("")
    print("\tbjos")
    print("")
    print("To kill a running job execute:")
    print("")
    print("\tbkill JOBID")
    print("")
    print("Here JOBID is the number returned when calling 'bjobs'")
    print("")
    print("To force kill a running job call:")
    print("\tbkill -r JOBID")
    print("")
    print("For additional information see: https://batchconf.web.cern.ch/batchconf/doc/lsf/print/lsf_users_guide.pdf")
    print("")
    print("Finally for a time series output of the data call:")
    print("")
    print("\tgemPlotter.py --infilename=%s --anaType=scurveAna --branchName=threshold --make2D --alphaLabels -c -a --axisMax=10"%outputScanDatesName)
    print("\tgemPlotter.py --infilename=%s --anaType=scurveAna --branchName=noise --make2D --alphaLabels -c -a --axisMin=0.05 --axisMax=0.3"%outputScanDatesName)
    print("\tgemPlotter.py --infilename=%s --anaType=scurveAna --branchName=ped_eff --make2D --alphaLabels -c -a --axisMax=1"%outputScanDatesName)
    print("\tgemPlotter.py --infilename=%s --anaType=scurveAna --branchName=mask --make2D --alphaLabels -c -a --axisMax=1"%outputScanDatesName)
    print("\tgemPlotter.py --infilename=%s --anaType=scurveAna --branchName=maskReason --make2D --alphaLabels -c -a --axisMax=32"%outputScanDatesName)
