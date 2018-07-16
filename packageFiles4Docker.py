#!/bin/env python

r"""
``packageFiles4Docker.py`` --- Creates a tarball containing data
================================================================

Synopsis
--------

**packageFiles4Docker.py** [*OPTIONS*]

Description
-----------

You may occasionally need to update the travis CI docker which checks the code
quality or you may want to transfer a number of files corresponding to a series
of scandates from the P5 machine to another area. The
:program:`packageFiles4Docker.py` tool enables you to do this. The output of :program:`packageFiles4Docker.py` will be a ``*.tar`` file that:

* mimics the file structure of ``$DATA_PATH``, and
* contains each of the input ``listOfScandates.txt`` files supplied at runtime,
  and
* a temorary ``chamberInfo.py`` file which can be placed in the docker for
  testing.

Arguments
---------

.. program:: packageFiles4Docker.py

.. option:: --fileListLat <FILE>

    Specify Input Filename for list of scandates for latency files.

.. option:: --fileListScurve <FILE>

    Specify Input Filename for list of scandates for scurve files.

.. option:: --fileListThresh <FILE>

    Specify Input Filename for list of scandates for threshold files.

.. option:: --fileListTrim <FILE>

    Specify Input Filename for list of scandates for trim files.

.. option:: --ignoreFailedReads

    Ignores failed read errors in tarball creation, useful for ignoring scans
    that did not finish successfully.

.. option:: --onlyRawData

    Files produced by ``anaUltra*.py`` scripts will not be included.

.. option:: --tarBallName <FILE>

    Specify the name of the output tarball.

.. option:: --ztrim <NUMBER>

    The ztrim value of interest for scandates given in --fileListTrim.

.. option:: -d, --debug

    Prints the commands that would be exectuted but does not call them.

Please note that multiple :token:`--fileListX` arguments can be supplied at
runtime, but at least one must be supplied.

Each of the :token:`--fileListX` arguments can be supplied with a
``listOfScanDates.txt`` file (:doc:`see here </scandate-list-formats>`).

Example
-------

To make a tarball of containing scurve scandates defined in
``listOfScanDates.txt`` for ``GEMINIm01L1`` execute:

.. code-block:: bash

    packageFiles4Docker.py --ignoreFailedReads --fileListScurve=$DATA_PATH/GEMINIm01L1/scurve/listOfScanDates.txt --tarBallName=GEMINIm01L1_scurves.tar --ztrim=4 --onlyRawData

In this case failed read errors in the tar command will be ignored and only the
raw data, e.g. ``SCurveData.root`` files, will be stored in the tarball
following the appropriate file structure.

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

Internals
---------
"""

def getListOfCmdTuples(filename, anaType):
    """
    Returns a list of tuples where each element is:
    ``(anaType, cName, scandate)``

    Args:
        filename (string): Physical filename of input file, see
            :any:`parseListOfScanDatesFile` for details on expected format

        anaType (string): String matching a key in
            :any:`utils.anaInfo.ana_config`
    """

    from gempython.gemplotting.utils.anaInfo import ana_config
    from gempython.gemplotting.utils.anautilities import parseListOfScanDatesFile

    import os

    # Check anaType is understood
    if anaType not in ana_config.keys():
        print "getListOfCmdTuples() - Invalid analysis specificed, please select only from the list:"
        print ana_config.keys()
        exit(os.EX_USAGE)
    
    parsedTuple = parseListOfScanDatesFile(filename, alphaLabels=True)

    ret_list_cmd_tuples = []
    for item in parsedTuple[0]:
        ret_list_cmd_tuples.append( (anaType, item[0], item[1]) )

    return ret_list_cmd_tuples

if __name__ == '__main__':
    from gempython.gemplotting.utils.anaInfo import tree_names
    from gempython.gemplotting.utils.anautilities import getDirByAnaType
    from gempython.utils.wrappers import runCommand

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--fileListLat", type="string", dest="fileListLat", default=None,
                      help="Specify Input Filename for list of scandates for latency files", metavar="fileListLat")
    parser.add_option("--fileListScurve", type="string", dest="fileListScurve", default=None,
                      help="Specify Input Filename for list of scandates for scurve files", metavar="fileListScurve")
    parser.add_option("--fileListThresh", type="string", dest="fileListThresh", default=None,
                      help="Specify Input Filename for list of scandates for threshold files", metavar="fileListThresh")
    parser.add_option("--fileListTrim", type="string", dest="fileListTrim", default=None,
                      help="Specify Input Filename for list of scandates for trim files", metavar="fileListTrim")
    parser.add_option("--ignoreFailedReads", action="store_true", dest="ignoreFailedReads",
                      help="Ignores failed read errors in tarball creation", metavar="ignoreFailedReads")
    parser.add_option("--onlyRawData", action="store_true", dest="onlyRawData",
                      help="Files produced by anaUltra*.py scripts will not be included", metavar="onlyRawData")
    parser.add_option("--tarBallName", type="string", dest="tarBallName", default="testFiles.tar",
                      help="Specify the name of the output tarball", metavar="tarBallName")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                      help="Specify the p value of the trim", metavar="ztrim")
    parser.add_option("-d","--debug", action="store_true", dest="debug",
                      help="prints the tarball command but does not make one", metavar="debug")
    (options, args) = parser.parse_args()

    import os

    # Start the tar ball command
    if options.ignoreFailedReads:
        tarBallCmd = ["tar", "--ignore-failed-read", "-cf", options.tarBallName]
    else:
        tarBallCmd = ["tar", "-cf", options.tarBallName]
        pass
    list_cmd_tuple = [] # 0 -> cName; 1 -> anaType; 2 -> scandate
    
    # Add Latency
    if options.fileListLat is not None:
        tarBallCmd.append(options.fileListLat)
        list_cmd_tuple.extend( getListOfCmdTuples(options.fileListLat, "latency") )
        if options.debug:
            print "info after parsing latency:"
            print list_cmd_tuple

    # Add Scurve
    if options.fileListScurve is not None:
        tarBallCmd.append(options.fileListScurve)
        list_cmd_tuple.extend( getListOfCmdTuples(options.fileListScurve, "scurve") )
        if options.debug:
            print "info after parsing scurve:"
            print list_cmd_tuple

    # Add threhsold per channel
    if options.fileListThresh is not None:
        tarBallCmd.append(options.fileListThresh)
        list_cmd_tuple.extend( getListOfCmdTuples(options.fileListThresh, "thresholdch") )
        if options.debug:
            print "info after parsing thresholdch:"
            print list_cmd_tuple

    # Add trim
    if options.fileListTrim is not None:
        tarBallCmd.append(options.fileListTrim)
        list_cmd_tuple.extend( getListOfCmdTuples(options.fileListTrim, "trim") )
        if options.debug:
            print "info after parsing trim:"
            print list_cmd_tuple

    if len(list_cmd_tuple) == 0:
        print("No inputs provided")
        print("Exiting")
        exit(os.EX_USAGE)

    # Append Each File to the tarBallCmd
    listOfChamberNames = []
    for item in list_cmd_tuple:
        if item[1] not in listOfChamberNames:
            listOfChamberNames.append(item[1])

        rawFile = (tree_names[item[0]])[0]

        anaKey = "%sAna"%item[0]
        if "threshold" in anaKey:
            anaKey = "thresholdAna"
        anaFile = (tree_names[anaKey])[0]

        rawFilePath = "%s/%s/%s"%(getDirByAnaType(anaType=item[0], cName=item[1], ztrim=options.ztrim), item[2], rawFile ) # basePath/scandate/rawFile
        tarBallCmd.append(rawFilePath)
        if not options.onlyRawData:
            anaFilePath = "%s/%s/%s"%(getDirByAnaType(anaType=item[0], cName=item[1], ztrim=options.ztrim), item[2], anaFile )# basePath/scandate/anaFile
            tarBallCmd.append(anaFilePath)
            pass
        
    # Make the fake chamberInfo.py file
    tmpChamberInfoFile = open("chamberInfo.py_tmp", "w")
    
    # Write the chamber_config dict
    tmpChamberInfoFile.write('chamber_config = {\n')
    for i,cName in enumerate(listOfChamberNames):
        if i == 0:
            tmpChamberInfoFile.write('\t   %i:"%s"\n'%(i,cName))
        else:
            tmpChamberInfoFile.write('\t , %i:"%s"\n'%(i,cName))
    tmpChamberInfoFile.write('}\n')

    # Write the GEBtype dict - treat them all as long (sub-optimal)
    tmpChamberInfoFile.write('GEBtype = {\n')
    for i,cName in enumerate(listOfChamberNames):
        if i == 0:
            tmpChamberInfoFile.write('\t   %i:"long"\n'%(i) )
        else:
            tmpChamberInfoFile.write('\t , %i:"long"\n'%(i) )
    tmpChamberInfoFile.write('}\n')
    tmpChamberInfoFile.close()

    tarBallCmd.append("chamberInfo.py_tmp")

    # Make the tarball
    if options.debug:
        print "tarball command:"
        for cmd in tarBallCmd:
            print cmd
    else:
        runCommand(tarBallCmd)
        print "Your tarball can be found at %s: "%(options.tarBallName)
        deleteTmpChamberInfo = ["rm","chamberInfo.py_tmp"]
        runCommand(deleteTmpChamberInfo)
