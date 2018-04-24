#!/bin/env python

def getListOfCmdTuples(filename, anaType):
    """
    Returns a list of tuples where each element is:
        (anaType, cName, scandate)

    filename - physical filename of input file, see parseListOfScanDatesFile 
               for details on expected format
    anaType - string matching a key in ana_config of anaInfo.py
    """

    from anaInfo import ana_config
    from anautilities import parseListOfScanDatesFile

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
    """
    Creates a tar ball to be used with the docker for unit tests with travis
    """
    from anaInfo import tree_names
    from anautilities import getDirByAnaType
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
