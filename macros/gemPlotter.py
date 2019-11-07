#!/bin/env python

r"""
``gemPlotter.py`` --- Plot time evolution of scan results
=========================================================

Synopsis
--------

**gemPlotter.py** :token:`--anaType` <*ANALYSIS TYPE*> :token:`--branchName` <*BRANCH*> :token:`-i` <*INPUT FILE*> :token:`-v` <*VFAT*> [*OPTIONS*]

Description
-----------

The :program:`gemPlotter.py` tool is for making plots of an observable stored in
one of the ``TTree`` objects produced by the (ana-) ultra scan scripts vs an
arbitrary indepdent variable specified by the user. Here each data point is from
a different ``scandate``. This is useful if you run mulitple scans in which only
a single parameter is changed (e.g. applied high voltage, or ``VThreshold1``)
and you want to track the dependency on this parameter.

Each plot produced will be stored as an output ``*.png`` file. Additionally an
output ``TFile`` will be produced which will contain each of the plots, stored
as ``TGraph`` objects, and canvases produced.

Mandatory arguments
-------------------

The following list shows the mandatory inputs that must be supplied to execute
the script.

.. program:: gemPlotter.py

.. option:: --anaType <ANALYSIS TYPE>

    Analysis type to be executed, see :any:`utils.anaInfo.tree_names` for
    possible inputs.

.. option:: --branchName <NAME>

    Name of ``TBranch`` where dependent variable is found, note that this
    ``TBranch`` should be found in the ``TTree`` that corresponds to the value
    given to the :option:`--anaType` argument.

.. option:: -i, --infilename <FILE NAME>

    Physical filename of the input file to be passed to
    :program:`gemPlotter.py`, in the
    :doc:`Three Column Format </scandate-list-formats>`.

.. option:: -v, --vfat <NUMBER>

    Specify VFAT to plot

Note for those :option:`--anaType` values which have the substring ``Ana`` in
their names it is expected that the user has already run :program:`ana_scans.py`
on the corresponding ``scandate`` to produce the necessary input file for
:program:`gemPlotter.py`.

Optional arguments
------------------

.. option:: -a, --all

    When providing this flag data from all 24 VFATs will be plotted.
    Additionally a summary plot in the typical 3x8 grid will be created showing
    the results of all 24 VFATs. May be used instead of the :option:`--vfat`
    option.

.. option:: --alphaLabels

    When providing this flag :program:`gemPlotter.py` will interpret the
    **Indep. Variable** as a string and modify the output X axis accordingly

.. option:: --axisMax <NUMBER>

    Maximum value for the axis depicting :option:`--branchName`.

.. option:: --axisMin <NUMBER>

    Minimum value for the axis depicting :option:`--branchName`.

.. option:: -c, --channels

    When providing this flag the :option:`--strip` option is interpreted as VFAT
    channel number instead of readout board (ROB) strip number.

.. option:: -s, --strip <NUMBER>

    Specific ROB strip number to plot for :option:`--branchName`. Note for ROB
    strip level :option:`--branchName` values (e.g. ``trimDAC``) if this option
    is not provided the data point (error bar) will represent the mean (standard
    deviation) of :option:`--branchName` from all strips.

.. option:: --make2D

    When providing this flag a 2D plot of ROB strip/vfat channel vs. independent
    variable will be plotted whose z-axis value is :option:`--branchName`.

.. option:: -p, --print

    Prints a comma separated table of the plot's data to the terminal. The
    format of this table will be compatible with the ``genericPlotter``
    executable of the `CMS GEM Analysis Framework`_.

    .. _CMS GEM Analysis Framework: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#3b-genericplotter

.. option:: --rootOpt <OPTION>

    Option for creating the output ``TFile``, e.g. ``RECREATE`` or ``UPDATE``

.. option:: --skipBadFiles

    ``TFiles`` that fail to load, or where the ``TTree`` cannot be successfully
    loaded, will be skipped.

.. option:: --showStat

    Causes the statistics box to be drawn on created plots. Note only applicable
    when used with :option:`--make2D`.

.. option:: --vfatList <COMMA-SEPARATED LIST OF INTEGERS>

    List of VFATs that should be plotted. May be used instead of the
    :option:`--vfat` option.

.. option:: --ztrim <NUMBER>

    The ``ztrim`` value that was used when running the scans listed in
    :option:`--infilename`

Examples
--------

Making a time series
....................

To automatically consider the last two weeks worth of s-curve scans, run the
script specifying ``vt1bump`` option like this:

.. code-block:: bash

    plotTimeSeries.py --vt1bump=10

resulting plots will be stored under:

.. code-block:: bash

    $ELOG_PATH/timeSeriesPlots/<chamber name>/vt1bumpX/

Making a 1D Plot --- Channel Level
..................................

To make a 1D plot for a given strip of a given VFAT execute:

.. code-block:: bash

    gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.> --strip=<Strip No.>

For example, to plot ``trimDAC`` vs. an **Indep. Variable Name** defined in
``listOfScanDates.txt`` for VFAT 12, strip number 49 execute:

.. code-block:: bash

    gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimDAC --vfat=12 --strip=49

Additional VFATs could be plotted by either:

* Making successive calls of the above command and using the
  ``--rootOpt=UPDATE``,
* Using the :option:`--vfatList` argument instead of the :option:`--vfat`
  argument, or
* Using the :option:`-a` argument to make all VFATs.

Making a 1D Plot --- VFAT Level
...............................

To make a 1D plot for a given VFAT execute:

.. code-block:: bash

    gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.>

For example, to plot ``trimRange`` vs. an **Indep. Variable Name** defined in
``listOfScanDates.txt`` for VFAT 12 execute:

.. code-block:: bash

    gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimRange --vfat=12

Note if **TBranch Name** is a strip level observable the data points
(y-error bars) in the produced plot will represent the mean (standard deviation)
from all of the VFAT's channels.

Additional VFATs could be plotted by either:

* Making successive calls of the above command and using the
  ``--rootOpt=UPDATE``,
* Using the :option:`--vfatList` argument instead of the :option:`--vfat`
  argument, or
* Using the :option:`-a` argument to make all VFATs.

To automatically extend this to all channels execute:

.. code-block:: bash

    gemPlotterAllChannels.sh <InFile> <anaType> <branchName>

Making a 2D Plot
................

To make a 2D plot for a given VFAT execute:

.. code-block:: bash

    gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.> --make2D

Here the output plot will be of the form "ROB Strip/VFAT Channel vs. Indep.
Variable Name" with the z-axis storing the value of :option:`--branchName`.

For example to make a 2D plot with the z-axis as trimDAC and the **Indep.
Variable Name** defined in ``listOfScanDates.txt`` for VFAT 12 execute:

.. code-block:: bash

    gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimDAC --vfat=12 --make2D

Additional VFATs could be plotted by either:

* Making successive calls of the above command and using the
  ``--rootOpt=UPDATE``,
* Using the :option:`--vfatList` argument instead of the :option:`--vfat`
  argument, or
* Using the :option:`-a` argument to make all VFATs.

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

    :envvar:`ELOG_PATH`
        Results are written in the directory pointed to by this variable

Internals
---------
"""

def arbitraryPlotter(anaType, listDataPtTuples, rootFileName, treeName, branchName, vfat, vfatCH=None, strip=None, ztrim=4, skipBad=False):
    """
    Provides a list of tuples for 1D data where each element is of the form:
    ``(indepVarVal, depVarVal, depVarValErr)``

    Args:
        anaType (string): type of analysis to perform, helps build the file path
            to the input file(s), from the keys of
            :any:`utils.anaInfo.ana_config`

        listDataPtTuples: list of tuples where each element is of the form
            ``(cName, scandate, indepVar)``, note ``indepVar`` is expected to be
            numeric

        rootFileName (string): name of the ``TFile`` that will be found in the
            data path corresponding to ``anaType``

        treeName (string): name of the ``TTree`` inside ``rootFileName``

        branchName (string): name of a branch inside ``treeName`` that the
            dependent variable will be extracted from

        vfat (int): vfat number that plots should be made for

        vfatCH (int): channel of the vfat that should be used, if ``None`` an
            average is performed w/stdev for error bar, mutually exclusive
            w/ ``strip``

        strip (int): strip of the detector that should be used, if ``None`` an
            average is performed w/stdev for error bar, mutually exclusive w/
            ``vfatCH``

        skipBad (bool): if a file fails to open or the ``TTree`` cannot be
            found, the input is skipped and the processing continues rather than
            exiting
    """

    from gempython.gemplotting.utils.anautilities import filePathExists, getDirByAnaType

    import numpy as np
    import os
    import root_numpy as rp

    # Make branches to load
    listNames = ["vfatN"]
    if vfatCH is not None and strip is None:
        listNames.append("vfatCH")
    elif strip is not None and vfatCH is None:
        listNames.append("ROBstr")
    listNames.append(branchName)

    # Load data
    listData = []
    for dataPt in listDataPtTuples:
        # Get human readable info
        cName = dataPt[0]
        scandate = dataPt[1]
        indepVarVal = dataPt[2]

        # Setup Paths
        dirPath = getDirByAnaType(anaType.strip("Ana"), cName, ztrim)
        if not filePathExists(dirPath, scandate):
            print('Filepath {0}/{1} does not exist!'.format(dirPath, scandate))
            if skipBad:
                print('Skipping')
                continue
            else:
                print('Please cross-check, exiting!')
                exit(os.EX_DATAERR)
                pass
        filename = "{0}/{1}/{2}".format(dirPath, scandate, rootFileName)

        # Get TTree
        try:
            dataFile = r.TFile(filename, "READ")
            dataTree = dataFile.Get(treeName)
            knownBranches = dataTree.GetListOfBranches()
        except AttributeError as e:
            print('{0} may not exist in {1}'.format(treeName,filename))
            print(e)
            if skipBad:
                print('Skipping')
                continue
            else:
                print('Please cross-check, exiting!')
                exit(os.EX_DATAERR)
                pass
            pass

        # Check to make sure listNames are present in dataTree
        for testBranch in listNames:
            if testBranch not in knownBranches:
                print("Branch {0} not in TTree {1} of file {2}".format(branchName, treeName, filename))
                print("Existing Branches are:")
                for realBranch in knownBranches:
                    print(realBranch)
                print("Please try again using one of the existing branches")
                exit(os.EX_DATAERR)

        # Get dependent variable value
        arrayVFATData = rp.tree2array(dataTree,listNames)
        dataThisVFAT = arrayVFATData[ arrayVFATData['vfatN'] == vfat] #VFAT Level

        # Close the TFile
        dataFile.Close()
        
        if vfatCH is not None and strip is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['vfatCH'] == vfatCH ] #VFAT Channel Level
        elif strip is not None and vfatCH is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['ROBstr'] == strip ] #Readout Board Strip Level
        
        depVarVal = np.asscalar(np.mean(dataThisVFAT[branchName]))   #If a vfatCH/ROBstr obs & chan/strip not give will be avg over all, else a number
        depVarValErr = np.asscalar(np.std(dataThisVFAT[branchName])) #If a vfatCH/ROBstr obs & chan/strip not given will be stdev over all, or zero

        #Record this dataPt
        listData.append( (indepVarVal, depVarVal, depVarValErr) )

    # Return Data
    return listData

def arbitraryPlotter2D(anaType, listDataPtTuples, rootFileName, treeName, branchName, vfat, ROBstr=True, ztrim=4, skipBad=False):
    """
    Provides a list of tuples for 2D data where each element is of the
    ``(x,y,z)`` form: ``(indepVarVal, vfatCHOrROBstr, depVarVal)``

    Args:
        anaType (string): type of analysis to perform, helps build the file path
            to the input file(s), from the keys of
            :any:`utils.anaInfo.ana_config`

        listDataPtTuples: list of tuples where each element is of the form:
            ``(cName, scandate, indepVar)``, note ``indepVar`` is expected to be
            numeric

        rootFileName (string): name of the ``TFile`` that will be found in the
            data path corresponding to ``anaType``

        treeName (string): name of the ``TTree`` inside ``rootFileName``

        branchName (string): name of a branch inside ``treeName`` that the
            dependent variable will be extracted from

        vfat (int): vfat number that plots should be made for

        skipBad (bool): if a file fails to open or the ``TTree`` cannot be
            found, the input is skipped and the processing continues rather than
            exiting
    """
  
    from gempython.gemplotting.utils.anautilities import filePathExists, getDirByAnaType

    import numpy as np
    import os
    import root_numpy as rp

    # Make branches to load
    listNames = ["vfatN"]
    strChanName = "" #Name of channel TBranch, either 'ROBstr' or 'vfatCH'
    if ROBstr:
        listNames.append("ROBstr")
        strChanName = "ROBstr"
    else:
        listNames.append("vfatCH")
        strChanName = "vfatCH"
    listNames.append(branchName)

    # Load data
    listData = []
    for dataPt in listDataPtTuples:
        # Get human readable info
        cName = dataPt[0]
        scandate = dataPt[1]
        indepVarVal = dataPt[2]

        # Setup Paths
        dirPath = getDirByAnaType(anaType.strip("Ana"), cName, ztrim)
        if not filePathExists(dirPath, scandate):
            print('Filepath {0}/{1} does not exist!'.format(dirPath, scandate))
            if skipBad:
                print('Skipping')
                continue
            else:
                print('Please cross-check, exiting!')
                exit(os.EX_DATAERR)
                pass
        filename = "{0}/{1}/{2}".format(dirPath, scandate, rootFileName)

        # Get TTree
        try:
            dataFile = r.TFile(filename, "READ")
            dataTree = dataFile.Get(treeName)
            knownBranches = dataTree.GetListOfBranches()
        except AttributeError as e:
            print('{0} may not exist in {1}'.format(treeName,filename))
            print(e)
            if skipBad:
                print('Skipping')
                continue
            else:
                print('Please cross-check, exiting!')
                exit(os.EX_DATAERR)
                pass
            pass

        # Check to make sure listNames are present in dataTree
        for testBranch in listNames:
            if testBranch not in knownBranches:
                print("Branch {0} not in TTree {1} of file {2}".format(branchName, treeName, filename))
                print("Existing Branches are:")
                for realBranch in knownBranches:
                    print(realBranch)
                print("Please try again using one of the existing branches")
                exit(os.EX_DATAERR)

        # Get dependent variable value - VFAT Level
        arrayVFATData = rp.tree2array(dataTree,listNames)
        dataThisVFAT = arrayVFATData[ arrayVFATData['vfatN'] == vfat] #VFAT Level

        # Close the TFile
        dataFile.Close()

        # Get the data for each strip and store it as a tuple in the list to be returned
        for chan in range(0,128):
            dataThisChan = dataThisVFAT[ dataThisVFAT[strChanName] == chan] #Channel Level
            depVarVal = np.asscalar(np.mean(dataThisChan[branchName]))
            listData.append( (indepVarVal, chan, depVarVal) )
            pass

    # Return Data
    return listData

if __name__ == '__main__':
    from gempython.gemplotting.utils.anaInfo import tree_names
    from gempython.gemplotting.utils.anautilities import parseListOfScanDatesFile
    from gempython.utils.wrappers import envCheck
    from plotoptions import parser

    import array
    import numpy as np
    import os
    
    parser.add_option("-a","--all", action="store_true", dest="all_plots",
                    help="vfatList is automatically set to [0,1,...,22,23]", metavar="all_plots")
    parser.add_option("--alphaLabels", action="store_true", dest="alphaLabels",
                    help="Draw output plot using alphanumeric lables instead of pure floating point", metavar="alphaLabels")
    parser.add_option("--axisMax", type="float", dest="axisMax", default=255,
                    help="Maximum value for axis depicting branchName", metavar="axisMax")
    parser.add_option("--axisMin", type="float", dest="axisMin", default=0,
                    help="Minimum value for axis depicting branchName", metavar="axisMin")
    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'latency','scurve','scurveAna','threshold','trim','trimAna'}", metavar="anaType")
    parser.add_option("--branchName", type="string", dest="branchName",
                    help="Name of TBranch where dependent variable is store", metavar="branchName")
    parser.add_option("--make2D", action="store_true", dest="make2D",
                    help="A 2D plot of (indepVar, chan, branchName) is made instead of a 1D plot", metavar="make2D")
    parser.add_option("-p","--print", action="store_true", dest="printData",
                    help="Prints a comma separated table with the data to the terminal", metavar="printData")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--skipBadFiles", action="store_true", dest="skipBadFiles",
                    help="Rather than exiting, simply skip an input scandate that fails to open/load properly", metavar="skipBadFiles")
    parser.add_option("--showStat", action="store_true", dest="showStat",
                    help="Draws the statistics box for 2D plots", metavar="showStat")
    parser.add_option("--vfatList", type="string", dest="vfatList", default=None,
                    help="Comma separated list of VFATs to consider, e.g. '12,13'", metavar="vfatList")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                    help="Specify the p value of the trim", metavar="ztrim")

    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
  
    import ROOT as r

    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    gemType="ge11"
    from gempython.tools.hw_constants import vfatsPerGemVariant
    
    # Get VFAT List
    listVFATs = []
    if options.all_plots:
        listVFATs = (x for x in range(0,vfatsPerGemVariant[gemType]))
    elif options.vfatList != None:
        listVFATs = map(int, options.vfatList.split(','))
    elif options.vfat != None:
        listVFATs.append(options.vfat)
    else:
        print("You must specify at least one VFAT to be considered")
        exit(os.EX_USAGE)
    
    # Check anaType is understood
    if options.anaType not in tree_names.keys():
        print("Invalid analysis specificed, please select only from the list:")
        print(tree_names.keys())
        exit(os.EX_USAGE)
        pass
    
    # Get info from input file
    parsedTuple = parseListOfScanDatesFile(options.filename, options.alphaLabels)
    listDataPtTuples = parsedTuple[0]
    strIndepVar = parsedTuple[1]

    # Do we make strip/channel level plot?
    vfatCH=None
    strip=None
    strDrawOpt = "APE1"
    strStripOrChan = "All"
    if options.strip is not None:
        # Set the strip or channel name
        if options.channels:
            vfatCH = options.strip
            strStripOrChan = "vfatCH{0}".format(options.strip)
        else:
            strip = options.strip
            strStripOrChan = "ROBstr{0}".format(options.strip)
    elif options.make2D:
        strDrawOpt = "COLZ"

        # Set the strip or channel name - no channel number here, over all of them
        if options.channels:
            strStripOrChan = "vfatCH"
        else:
            strStripOrChan = "ROBstr"
        
    # Get difference between independent variable values
    listIndepVarLowEdge = [] #used if either options.alphaLabels or options.make2D is true
    if options.alphaLabels:
        for i in range(0,len(listDataPtTuples)+1):
            listIndepVarLowEdge.append(i)
    elif options.make2D:
        listIndepVarVals = []
        arraydeltaIndepVar = np.zeros(len(listDataPtTuples)) #Difference between i and i+1 indepVar
        for i in range(0,len(listDataPtTuples)):
            listIndepVarVals.append(listDataPtTuples[i][2])
            if i == (len(listDataPtTuples) - 1):
                arraydeltaIndepVar[i] = 0.
            else:
                arraydeltaIndepVar[i] = np.fabs(listDataPtTuples[i][2] - listDataPtTuples[i+1][2])
        arraydeltaIndepVar[len(arraydeltaIndepVar)-1] = np.mean(arraydeltaIndepVar[:(len(arraydeltaIndepVar)-1)])

        # Set the values in listIndepVarLowEdge
        for i in range(0,len(listIndepVarVals)):
            if i == 0:
                # x_low_i = x_i - 0.5 * <delta_x>
                listIndepVarLowEdge.append(listIndepVarVals[i] - 0.5 * arraydeltaIndepVar[len(arraydeltaIndepVar)-1])
            else:
                # x_low_i = x_i - 0.5 * delta_x_(i-1)
                listIndepVarLowEdge.append(listIndepVarVals[i] - 0.5 * arraydeltaIndepVar[i-1])
        listIndepVarLowEdge.append(listIndepVarVals[len(listIndepVarVals)-1] + 0.5 * arraydeltaIndepVar[len(arraydeltaIndepVar)-1])

    # Loop over the vfats in listVFATs and make the requested plot for each
    strIndepVarNoBraces = strIndepVar.replace('{','').replace('}','').replace('_','')
    strRootName = "{0}/gemPlotterOutput_{1}_vs_{2}.root".format(elogPath,options.branchName, strIndepVarNoBraces)
    r.gROOT.SetBatch(True)
    outF = r.TFile(strRootName,options.rootOpt)
    listPlots = []
    for vfat in listVFATs:
        # Make the output directory
        dirVFAT = r.TDirectory()
        if options.rootOpt.upper() == "UPDATE":
            dirVFAT = outF.GetDirectory("VFAT{0}".format(vfat), False, "GetDirectory")
        else:
            dirVFAT = outF.mkdir("VFAT{0}".format(vfat))
            pass

        # Make the output canvas, use a temp name and temp title for now
        strCanvName = ""
        canvPlot = r.TCanvas("canv_VFAT{0}".format(vfat),"VFAT{0}".format(vfat),2400,800)

        # Make the plot, either 2D or 1D
        if options.make2D:
            listData = arbitraryPlotter2D(
                    options.anaType, 
                    listDataPtTuples, 
                    tree_names[options.anaType][0], 
                    tree_names[options.anaType][1], 
                    options.branchName, 
                    vfat,
                    not options.channels,
                    options.ztrim,
                    skipBad=options.skipBadFiles)

            # Print(to the user)
            if options.printData:
                print("===============Printing Data for VFAT{0}===============".format(vfat))
                print("[BEGIN_DATA]")
                print("\tVAR_INDEP,VAR_DEP,VALUE")
                for dataPt in listData:
                    print("\t{0},{1},{2}".format(dataPt[0],dataPt[1],dataPt[2]))
                print("[END_DATA]")
                print("")
            

            # Make the plot
            binsIndepVarLowEdge = array.array('d',listIndepVarLowEdge)
            hPlot2D = r.TH2F("h_{0}_vs_{1}_Obs{2}_VFAT{3}".format(strStripOrChan, strIndepVarNoBraces, options.branchName, vfat),
                            "VFAT{0}".format(vfat),
                            len(listIndepVarLowEdge)-1, binsIndepVarLowEdge,
                            128, -0.5, 127.5)
            hPlot2D.SetXTitle(strIndepVar)
            hPlot2D.SetYTitle(strStripOrChan)
            hPlot2D.SetZTitle(options.branchName)
           
            # Do we have alphanumeric bin labels?
            if options.alphaLabels:
                for binX,item in enumerate(listDataPtTuples):
                    hPlot2D.GetXaxis().SetBinLabel(binX+1,item[2])

            # Fill the plot
            for idx in range(len(listData)):
                hPlot2D.Fill(listData[idx][0],listData[idx][1],listData[idx][2])
            
            # Set the Stat Box Options
            if options.showStat:
                r.gStyle.SetOptStat(1111111)
            else:
                r.gStyle.SetOptStat(0000000)
                
            # Draw this plot on a canvas
            strCanvName = "{0}/canv_{1}_vs_{2}_Obs{3}_VFAT{4}.png".format(elogPath, strStripOrChan, strIndepVarNoBraces, options.branchName, vfat)
            canvPlot.SetName("canv_{0}_vs_{1}_Obs{2}_VFAT{3}.png".format(strStripOrChan, strIndepVarNoBraces, options.branchName, vfat))
            canvPlot.SetTitle("VFAT{0}: {1} vs. {2} - Obs {3}".format(vfat,strStripOrChan,strIndepVarNoBraces, options.branchName))
            canvPlot.SetRightMargin(0.15)
            canvPlot.cd()
            hPlot2D.GetZaxis().SetRangeUser(options.axisMin, options.axisMax)
            hPlot2D.Draw(strDrawOpt)
            hPlot2D.GetYaxis().SetDecimals(True)
            hPlot2D.GetYaxis().SetTitleOffset(1.2)
            
            # Store the plot
            dirVFAT.cd()
            hPlot2D.Write()
            listPlots.append(hPlot2D)
        else:
            listData = arbitraryPlotter(
                    options.anaType, 
                    listDataPtTuples, 
                    tree_names[options.anaType][0], 
                    tree_names[options.anaType][1], 
                    options.branchName, 
                    vfat, 
                    vfatCH, 
                    strip,
                    options.ztrim,
                    skipBad=options.skipBadFiles)

            # Print(to the user)
            # Using format compatible with: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data
            if options.printData:
                print("===============Printing Data for VFAT{0}===============".format(vfat))
                print("[BEGIN_DATA]")
                print("\tVAR_INDEP,VAR_DEP,VAR_DEP_ERR")
                for dataPt in listData:
                    print("\t{0},{1},{2}".format(dataPt[0],dataPt[1],dataPt[2]))
                print("[END_DATA]")
                print("")

            # Make the plot
            thisPlot = r.TGraphErrors(len(listData))
            if options.alphaLabels:
                strDrawOpt = "PE1v"
                
                binsIndepVarLowEdge = array.array('d',listIndepVarLowEdge)
                thisPlot = r.TH1F("h_{0}_vs_{1}_VFAT{2}_{3}".format(options.branchName, strIndepVarNoBraces, vfat, strStripOrChan),
                                  "VFAT{0}_{1}".format(vfat,strStripOrChan),
                                  len(listIndepVarLowEdge)-1, binsIndepVarLowEdge)
           
                for binX,item in enumerate(listDataPtTuples):
                    thisPlot.GetXaxis().SetBinLabel(binX+1,item[2])
                for idx in range(len(listData)):
                    thisPlot.Fill(listData[idx][0], listData[idx][1])
                    
                    if thisPlot.GetXaxis().GetBinLabel(idx+1) == listDataPtTuples[idx][2]:
                        thisPlot.SetBinError(idx+1, listData[idx][2])
            else:
                thisPlot.SetTitle("VFAT{0}_{1}".format(vfat,strStripOrChan))
                thisPlot.SetName("g_{0}_vs_{1}_VFAT{2}_{3}".format(options.branchName, strIndepVarNoBraces, vfat, strStripOrChan))
                for idx in range(len(listData)):
                    thisPlot.SetPoint(idx, listData[idx][0], listData[idx][1])
                    thisPlot.SetPointError(idx, 0., listData[idx][2])

            # Draw this plot on a canvas
            thisPlot.SetMarkerStyle(20)
            thisPlot.SetLineWidth(2)
            strCanvName = "{0}/canv_{1}_vs_{2}_VFAT{3}_{4}.png".format(elogPath, options.branchName,strIndepVarNoBraces, vfat,strStripOrChan)
            canvPlot.SetName("canv_{0}_vs_{1}_VFAT{2}_{3}".format(options.branchName,strIndepVarNoBraces, vfat, strStripOrChan))
            canvPlot.SetTitle("VFAT{0}_{1}: {2} vs. {3}".format(vfat,strStripOrChan,options.branchName,strIndepVarNoBraces))
            canvPlot.cd()
            thisPlot.Draw(strDrawOpt)
            thisPlot.GetXaxis().SetTitle(strIndepVar)
            thisPlot.GetXaxis().SetLabelSize(0.04)
            thisPlot.GetYaxis().SetDecimals(True)
            thisPlot.GetYaxis().SetRangeUser(options.axisMin, options.axisMax)
            thisPlot.GetYaxis().SetTitle(options.branchName)
            thisPlot.GetYaxis().SetTitleOffset(1.2)
        
            # Store the plot
            dirVFAT.cd()
            thisPlot.Write()
            listPlots.append(thisPlot)
            pass
        
        if not options.all_plots:
            print("")
            print("To view your plot, execute:")
            print("eog " + strCanvName)
            print("")

        # Store the Canvas
        canvPlot.Update()
        canvPlot.SaveAs(strCanvName)
        dirVFAT.cd()
        canvPlot.Write()
        pass

    # Make Summary Plot
    if options.all_plots:
        from gempython.gemplotting.utils.anautilities import getSummaryCanvas
        strSummaryName = "summary_{0}_vs_{1}_{2}".format(options.branchName, strIndepVarNoBraces,strStripOrChan)
        canv_summary = getSummaryCanvas(listPlots, name=strSummaryName, drawOpt=strDrawOpt, gemType=gemType)
        
        strCanvName = "{0}/{1}.png".format(elogPath,strSummaryName)
        canv_summary.SaveAs(strCanvName)
        
        outF.cd()
        canv_summary.Write()

        print("")
        print("To view your plot, execute:")
        print("eog " + strCanvName)
        print("")

    print("")
    print("Your plot is stored in a TFile, to open it execute:")
    print("root " + strRootName)
    print("")
