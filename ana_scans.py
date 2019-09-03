#!/bin/env python

r"""
ana\_scans
==========

.. moduleauthor:: Cameron Bravo <c.bravo@cern.ch>
.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>
"""

from gempython.utils.gemlogger import colors, printGreen, printRed, printYellow

import signal

def anaDACScan(args):
    """
    Launches a call of dacAnalysis to analyze DAC Scan Data

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
   
    # Get chamber_config
    chamber_config = getChamberConfig(args)[0]

    # Get list of input files
    dictOfFiles = getFileList(
            "dacScanV3",
            chamber_config,
            args.scandate,
            debug=args.debug,
            inputfilename=args.inputfilename,
            listOfScandatesFile=args.listOfScandatesFile)

    # Set default histogram behavior
    import ROOT as r

    from gempython.gemplotting.utils.anautilities import dacAnalysis
    from gempython.gemplotting.utils.anautilities import getScandateFromFilename
    from gempython.gemplotting.utils.exceptions import VFATDACBiasCannotBeReached
    args.assignXErrors = False
    args.printSum = False
    for geoAddr,fileTuple in dictOfFiles.iteritems():
        print("Analyzing: {0}".format(fileTuple[0]))
    
        dacScanFile = r.TFile(fileTuple[0],"READ")

        if args.scandate is None:
            args.scandate = getScandateFromFilename(fileTuple[0])

        try:
            dacAnalysis(args, dacScanFile.dacScanTree, chamber_config, scandate=args.scandate)
        except VFATDACBiasCannotBeReached as err:
            from gempython.utils.gemlogger import printRed
            printRed(err.message)
            printRed("VFATs above may *NOT* be properly biased")
            pass
        dacScanFile.Close()
        pass

    printGreen("Analysis Completed Successfully")
    return
    
def anaSBITMonitor(args):
    raise RuntimeError("anaSBITMonitor(): Not implemented yet")

def anaSBITReadout(args):
    raise RuntimeError("anaSBITReadout(): Not implemented yet")

def anaSBITThresh(args):
    """
    Launches a call of sbitRateAnalysis to analyze SBIT Threshold scans

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    # Get chamber_config
    chamber_config = getChamberConfig(args)[0]

    # Get list of input files
    if args.perchannel:
        anaType = "sbitRatech"
    else:
        anaType = "sbitRateor"
    dictOfFiles = getFileList(
            anaType,
            chamber_config,
            args.scandate,
            debug=args.debug,
            inputfilename=args.inputfilename,
            listOfScandatesFile=args.listOfScandatesFile)

    # Set default histogram behavior
    import ROOT as r
    
    from gempython.gemplotting.utils.anautilities import getElogPath
    elogPath = getElogPath()

    from gempython.gemplotting.utils.threshAlgos import sbitRateAnalysis
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, getScandateFromFilename
    for geoAddr,fileTuple in dictOfFiles.iteritems():
        print("Analyzing: {0}".format(fileTuple[0]))

        sbitThreshFile = r.TFile(fileTuple[0],"READ")

        if args.scandate is None:
            args.scandate = getScandateFromFilename(fileTuple[0])

        anaResults = sbitRateAnalysis(
                chamber_config = chamber_config,
                rateTree = sbitThreshFile.rateTree,
                cutOffRate = args.maxNoiseRate,
                debug = args.debug,
                scandate = args.scandate)

        dict_dacValsBelowCutOff = anaResults[1]

        for ohKey,innerDictByVFATKey in dict_dacValsBelowCutOff["THR_ARM_DAC"].iteritems():
            if args.scandate == 'noscandate':
                vfatConfg = open("{0}/{1}/vfatConfig.txt".format(elogPath,chamber_config[ohKey]),'w')
                printGreen("Output Data for {0} can be found in:\n\t{1}/{0}\n".format(chamber_config[ohKey],elogPath))
            else:
                if args.perchannel:
                    strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
                else:
                    strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                    pass
                vfatConfg = open("{0}/{1}/vfatConfig.txt".format(strDirName,args.scandate),'w')
                printGreen("Output Data for {0} can be found in:\n\t{1}/{2}\n".format(chamber_config[ohKey],strDirName,args.scandate))
                pass

            vfatConfg.write("vfatN/I:vt1/I:trimRange/I\n")
            for vfat,armDACVal in innerDictByVFATKey.iteritems():
                vfatConfg.write('%i\t%i\t%i\n'%(vfat, armDACVal,0))
                pass
            vfatConfg.close()
            pass
        pass

    printGreen("Analysis Completed Successfully")
    return

def anaXDAQLatency(args):
    raise RuntimeError("anaXDAQLatency(): Not implemented yet")

def calArmDACParallelAna(args):
    """
    This will launch a call of calibrateThrDac for each listOfScandates file that is found.
    For each listOfScandates this will check if the scurves that the listOfScandates references
    have been analyzed; if they have not been analyzed this will analyze each one in parallel
    based on the CPU usage case that the user requests.  After all scurves have been analyzed
    this will call calibrateThrDac in parallel on the listOfScandates files that have been found.

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    # Check that we have correct inputs
    if ((hasattr(args,'scandate') is False) and (hasattr(args,'inputfilename') is False)):
        raise RuntimeError("The input args namespace must have an attribute of either 'scandate' or 'inputfilename'")

    # Get chamber_config
    confTuple = getChamberConfig(args)
    chamber_config = confTuple[0]
    GEBtype = confTuple[1]

    # Check that input listOfScandates files are valid
    dictOfFiles = getFileList("armDacCal",chamber_config,args.scandate,args.debug,GEBtype,args.inputfilename,args.listOfScandatesFile)
    dictOfScurvesWithoutAna = {}
    import os
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, getGEBTypeFromFilename, parseListOfScanDatesFile
    from gempython.gemplotting.utils.anaInfo import tree_names
    for geoAddr,calInfoTuple in dictOfFiles.iteritems():
        listOfScandatesFile = calInfoTuple[0].format(DETECTOR=chamber_config[geoAddr])
        listOfScurveTuples = parseListOfScanDatesFile(listOfScandatesFile,False,args.delimiter)[0]

        for scurveTuple in listOfScurveTuples:
            cName = scurveTuple[0]
            thisScandate = scurveTuple[1]

            # Make assumption here that cName matches chamber_config[geoAddr]
            if cName != chamber_config[geoAddr]:
                printRed("calibrateArmDAC() {0} is not found in chamber_config, skipping scandate {1} of input file {2}".format(
                    cName,
                    thisScandate,
                    listOfScandatesFile))
                continue 

            fullPath2File = "{0}/{1}/{2}".format(
                    getDirByAnaType("scurve",cName),
                    thisScandate,
                    tree_names["scurveAna"][0])
            #fullPath2FileNoAna = fullPath2File.replace("/SCurveFitData","")
            fullPath2FileNoAna = "{0}/{1}/{2}".format(
                    getDirByAnaType("scurve",cName),
                    thisScandate,
                    tree_names["scurve"][0]) # Better readability?
            if not os.path.isfile(fullPath2File) and os.path.isfile(fullPath2FileNoAna):
                gebType = getGEBTypeFromFilename(fullPath2FileNoAna,cName)
                newGeoAddr = (geoAddr[0], geoAddr[1], geoAddr[2], thisScandate)
                dictOfScurvesWithoutAna[newGeoAddr] = (fullPath2FileNoAna,cName,gebType)
            elif not os.path.isfile(fullPath2File) and not os.path.isfile(fullPath2FileNoAna):
                printRed("calibrateArmDAC() - I did not find a valid raw scurve or analyzed scurve file for {0} scandate {1} from input file {2}".format(
                    cName,
                    thisScandate,
                    listOfScandatesFile))
                continue
            pass # End loop over listOfScurveTuples
        pass # End loop over dictOfFiles

    # Analyze any raw scurve files needing analysis
    from gempython.utils.wrappers import runCommand
    if len(dictOfScurvesWithoutAna) > 0:
        if args.debug:
            msg="Following scurve files need analysis:\n"
            for geoAddr,infoTuple in dictOfScurvesWithoutAna.iteritems():
                msg="{0}\n\t{1}{2}{3}".format(msg,colors.GREEN,infoTuple[0],colors.ENDC)
            print("{0}\n".format(msg))
            pass

        # Make output directories and set permissions
        makeOutDirectories(dictOfScurvesWithoutAna)

        # Launch the pool processes
        scurveMultiProcessing(args,dictOfScurvesWithoutAna)

        pass # End analyze un-analyzed scurves

    # Setup a pool
    from multiprocessing import Pool
    from gempython.gemplotting.utils.anautilities import getNumCores2Use, init_worker
    pool = Pool(getNumCores2Use(args), initializer=init_worker) # Allocate number of CPU's based on getNumCores2Use()

    # Perform ARM DAC calibration analysis
    from gempython.gemplotting.utils.threshAlgos import calibrateThrDACStar
    import itertools, sys, traceback
    from gempython.gemplotting.utils.namespace import Namespace

    namespaces = []
    for calInfoTuple in dictOfFiles.values():
        namespaces.append(Namespace(
            inputFile = calInfoTuple[0].format(DETECTOR=calInfoTuple[1]),
            fitRange = "0,255",
            listOfVFATs = None,
            noLeg = args.noLeg,
            outputDir = calInfoTuple[0][0:calInfoTuple[0].rfind("/")+1],
            savePlots = args.savePlots,
            debug = args.debug
            ))

    try:
        print("Calibration CFG_THR_ARM_DAC; please be patient")
        pool.map_async(calibrateThrDACStar,
                itertools.izip(namespaces)
                ).get(1800) # wait at most 30 minutes, this should be "relatively" quick
    except KeyboardInterrupt:
        printRed("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        printRed("Analysis Failed")
    except Exception as err:
        printRed("Caught {0}: {1}, terminating workers".format(type(err), err.message))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        printRed("Caught non-Python Exception %s"%(e))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    else:
        printGreen("Analysis Completed Successfully")
        pool.close()
        pool.join()
    finally:
        # Ensure permissions of all files in subdirectories have group read and write
        setPermissions(dictOfFiles)
        pass # End calibration of CFG_THR_ARM_DAC

    return

def getChamberConfig(args):
    """
    Determines the chamber_config and GEBtype dictionaries based on input arguments.
    Returns a tuple:

        (chamber_config, GEBtype)

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    if args.chamberConfig:
        from gempython.gemplotting.mapping.chamberInfo import chamber_config,GEBtype
    elif args.cNameAndAddr is not None:
        cNameAndAddr=args.cNameAndAddr.split(",")
        if len(cNameAndAddr) != 5:
            raise RuntimeError("Length of '--cNameAndAddr' != 5.\nI was expecting an input of the form 'DetectorSerialNo,DetectorType,Shelf,Slot,Link' but received:\n\t{0}".format(args.cNameAndAddr))
        geoAddr = (int(cNameAndAddr[2]),int(cNameAndAddr[3]),int(cNameAndAddr[4]))
        chamber_config = { geoAddr:cNameAndAddr[0] }
        GEBtype = { geoAddr:cNameAndAddr[1] }
    elif args.mappingFile is not None:
        import os, sys, traceback
        if not os.path.isfile(args.mappingFile):
            raise IOError("The following file does not exist or is not readable:\n{0}".format(args.mappingFile))
    
        # Try to get the mapping data
        try:
            mapFile = open(args.mappingFile, 'r')
        except IOError as error:
            print("Exception: {0}".format(error.msg))
            print("Failed to open: {0}".format(args.mappingFile))
            traceback.print_exc(file=sys.stdout)
            sys.exit(os.EX_IOERR)
        else:
            listMapData = mapFile.readlines()
        finally:
            mapFile.close()

        # Parse the mapping file data into chamber_config
        chamber_config = {}
        GEBtype = {}
        for line in listMapData:
            if line[0] == "#":
                continue

            line=line.replace("\n","")
            cNameAndAddr=line.split(",")
            if len(cNameAndAddr) != 5:
                raise RuntimeError("Length of split line != 5.\nI was expecting an input of the form 'DetectorSerialNo,DetectorType,Shelf,Slot,Link' but received:\n\t{0}".format(args.cNameAndAddr))
            geoAddr = (int(cNameAndAddr[2]),int(cNameAndAddr[3]),int(cNameAndAddr[4]))
            chamber_config[geoAddr]=cNameAndAddr[0]
            GEBtype[geoAddr]=cNameAndAddr[1]
            pass
        pass

    if args.debug:
        msg = "chamber_config determined to be:\n"
        for geoAddr,cName in chamber_config.iteritems():
            msg="{0}\n\t{1}{2}:{3}{4}".format(msg,colors.GREEN,geoAddr,cName,colors.ENDC)
        print("{0}\n".format(msg))
        msg = "GEBtype determined to be:\n"
        for geoAddr,cName in GEBtype.iteritems():
            msg="{0}\n\t{1}{2}:{3}{4}".format(msg,colors.GREEN,geoAddr,cName,colors.ENDC)
        print("{0}\n".format(msg))

    return (chamber_config,GEBtype)

def getFileList(anaType,chamber_config,scandate,debug=False,GEBtype=None,inputfilename=None, listOfScandatesFile=None):
    """
    Determines the list of files to be processed based on input arguments
    Returns a dictionary whose keys are geographic addresses (shelf,slot,link) and whose 
    values are tuple (filename,chamberName,type).  The chamberName and type values 
    might be 'None' depending on the inputs.  The type entry in the tuple will be
    None if GEBtype input argument is None.  The chamberName entry in the tuple will be
    None if scandate is None and if the chamberName cannot be determined from the input filename.

    anaType         - analysis type you are conducting, see keys of ana_config dictionary from gempython.gemplotting.utils.anaInfo for available options
    chamber_config  - Dictionary whose key values are geographic address, e.g. (shelf,slot,link), and values are detector serial numbers
    scandate        - Either None or a string specifying the scandate of the files of interest, in YYYY.MM.DD.hh.mm format
    debug           - Prints debugging information if True
    GEBtype         - Optional, dictionary whose key values are geographic address, e.g. (shelf,slot,link), and values are GEB type (e.g. detector type)
    inputfilename   - Either None or a string specifying the physical filename of a single input file. Note if this is not None you should set scandate to None
    """
    fileDict = {}

    from gempython.gemplotting.utils.anaInfo import tree_names
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, getGEBTypeFromFilename
    import os
    if scandate is not None:
        listOfFoundFiles = [ ]
        for geoAddr,cName in chamber_config.iteritems():
            # Determine filename
            if "Ana" in anaType:
                thisPath = "{0}/{1}".format(getDirByAnaType(anaType.replace("Ana",""),cName),scandate)
            elif ((anaType == "sbitRateor") or (anaType == 'sbitRatech')):
                thisPath = "{0}/{1}".format(getDirByAnaType(anaType,None),scandate)
            else:
                thisPath = "{0}/{1}".format(getDirByAnaType(anaType,cName),scandate)
            filename = "{0}/{1}".format(thisPath,tree_names[anaType][0])

            # Check that this file is not in listOfFoundFiles
            #if( os.path.isfile(filename) and (filename not in listOfFoundFiles)):
            if filename not in listOfFoundFiles:
                if GEBtype is not None:
                    if geoAddr in GEBtype.keys():
                        infoTuple = (filename,cName,GEBtype[geoAddr])
                    else:
                        infoTuple = (filename,cName,None)
                else:
                    infoTuple = (filename,cName,None)
                    pass
                
                # If anaType is trimV3, armDacCal or armDacCalAna check if the path, excluding file, is valid
                # For all other anaTypes check if the file is valid
                if (((anaType == "trimV3") or ("armDacCal" in anaType)) and os.path.isdir(thisPath)):
                    fileDict[geoAddr]=infoTuple
                    listOfFoundFiles.append(filename)
                elif os.path.isfile(filename):
                    fileDict[geoAddr]=infoTuple
                    listOfFoundFiles.append(filename)
                    pass
                pass
            pass
        pass
    elif inputfilename is not None:
        from gempython.gemplotting.utils.anautilities import getChamberNameFromFilename
        cName   = getChamberNameFromFilename(inputfilename)
        if cName is not None:
            detType = getGEBTypeFromFilename(inputfilename, cName)
        else:
            detType = None

        geoAddr = None
        if cName in chamber_config.values():
            idx = chamber_config.values().index(cName)
            geoAddr = chamber_config.keys()[idx]

        fileDict[geoAddr]=(inputfilename,cName,detType)
    elif listOfScandatesFile is not None:
        listOfUnsupportedTypes = ["armDacCal","armDacCalAna","dacScanV3","sbitRatech","sbitRateor"]
        if anaType in listOfUnsupportedTypes:
            raise RuntimeError("getFileList() does not support listOfScandatesFile input with anaType {0}".format(anaType)) 

        from gempython.gemplotting.utils.anautilities import parseListOfScanDatesFile
        listOfTuples = parseListOfScanDatesFile(listOfScandatesFile, False, "\t")

        listOfFoundFiles = [ ]
        for infoTuple in listOfTuples:
            # Get info from tuple
            cName = infoTuple[0]
            scandate = infoTuple[1]
            detType = getGEBTypeFromFilename(cName)

            # Determine filename
            if "Ana" in anaType:
                thisPath = "{0}/{1}".format(getDirByAnaType(anaType.replace("Ana",""),cName),scandate)
            else:
                thisPath = "{0}/{1}".format(getDirByAnaType(anaType,cName),scandate)
            filename = "{0}/{1}".format(thisPath,tree_names[anaType][0])

            # If anaType is trimV3, armDacCal or armDacCalAna check if the path, excluding file, is valid
            # For all other anaTypes check if the file is valid
            if (((anaType == "trimV3") or ("armDacCal" in anaType)) and (not os.path.isdir(thisPath))):
                printYellow("Path {0} does not exist or is not readable; no matching path for entry ({1},{2},{3}). Skipping".format(thisPath,cName,scandate,anaType))
                continue
            elif not os.path.isfile(filename):
                printYellow("File {0} does not exist or is not readable; no matching file for entry ({1},{2},{3}). Skipping".format(filename,cName,scandate,anaType))
                continue

            # Check that this file has not already been included
            if filename in listOfFoundFiles:
                printYellow("File {0} has already been added, duplicate entry for ({1},{2},{3}) detected. Skipping".format(filename,cName,scandate,anaType))
                continue

            # Determine geoAddr
            if cName in chamber_config.values():
                idx = chamber_config.values().index(cName)
                geoAddr = chamber_config.keys()[idx]
            else:
                import ROOT as r
                thisFile = r.TFile(filename,"READ")
                thisTree = thisFile.Get(tree_names[anaType][1])

                import root_numpy as rp
                list_bNames = ['link','shelf','slot']
                crateMap = rp.tree2array(tree=thisTree,branches=list_bNames)
                crateMap = np.unique(crateMap)

                geoAddr = (crateMap['shelf'],crateMap['slot'],crateMap['link'])
                thisFile.Close()
                pass

            # Set output
            fileDict[geoAddr]=(filename,cName,detType)
            listOfFoundFiles.append(filename)
            pass # end loop over listOfTuples
        pass
    else:
        raise RuntimeError("Neither a scandate, inputfilename, or listOfScandatesFile was provided")

    if debug:
        msg="analyzing the following files:\n"
        for geoAddr,infoTuple in fileDict.iteritems():
            msg="{0}\n\t{1}{2}{3}".format(msg,colors.GREEN,infoTuple[0],colors.ENDC)
        print("{0}\n".format(msg))
        pass

    if len(fileDict) == 0:
        raise RuntimeError("getFileList() - {0}No input files found! Please cross-check input arguments and try again{1}".format(colors.RED,colors.ENDC))

    return fileDict

def latencyParallelAna(args):
    """
    This launches a call of anaUltraLatency in parallel on each of the 
    input files that have been found.

    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    # Get chamber_config
    confTuple = getChamberConfig(args)
    chamber_config = confTuple[0]
    GEBtype = confTuple[1]

    # Get list of input files
    dictOfFiles = getFileList("latency",chamber_config,args.scandate,args.debug,GEBtype,args.inputfilename,args.listOfScandatesFile)
    
    # Make output directories and set permissions
    makeOutDirectories(dictOfFiles)

    # Setup a pool
    from multiprocessing import Pool
    from gempython.gemplotting.utils.anautilities import getNumCores2Use, init_worker
    pool = Pool(getNumCores2Use(args), initializer=init_worker) # Allocate number of CPU's based on getNumCores2Use()

    # Launch the pool processes
    from gempython.gemplotting.utils.latAlgos import anaUltraLatencyStar
    import itertools, sys, traceback
    try:
        pool.map_async(anaUltraLatencyStar,
                itertools.izip(
                    [latFile[0] for latFile in dictOfFiles.values()],                       # infilename
                    [args.debug for latFile in dictOfFiles.values()],                       # debug
                    [args.latSigMaskRange for geoAddr in dictOfFiles.keys()],               # latSigMaskRange
                    [args.latSigRange for geoAddr in dictOfFiles.keys()],                   # latSigRange
                    [latFile[0].replace(".root","") for latFile in dictOfFiles.values()],   # outputDir
                    ["latencyAna.root" for geoAddr in dictOfFiles.keys()],                  # outfilename
                    [args.performFit for geoAddr in dictOfFiles.keys()]                     # performFit
                    )
                ).get(7200) # wait at most 2 hours
    except KeyboardInterrupt:
        printRed("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        printRed("Analysis Failed")
    except Exception as err:
        printRed("Caught {0}: {1}, terminating workers".format(type(err), err.message))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        printRed("Caught non-Python Exception %s"%(e))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    else:
        printGreen("Analysis Completed Successfully")
        pool.close()
        pool.join()
    finally:
        # Ensure permissions of all files in subdirectories have group read and write
        setPermissions(dictOfFiles)

    return

def makeOutDirectories(dictOfFiles, permissions="g+rw"):
    """
    For each tuple element of dictOfFiles this will create an output directory for the first element in the tuple

        dictOfFiles - dictionary of tuples where the first element of each tuple is a the name of a TFile.
                      See documentation for getFileList()
        permissions - Permissions to set the directory with; if None no permissions are set and this will
                      default to the umask
    """

    from gempython.utils.wrappers import runCommand
    import os
    for infoTuple in dictOfFiles.values():
        runCommand(["mkdir", "-p", "{0}".format(infoTuple[0].replace(".root",""))])
        if setPermissions is not None:
            os.system("chmod -R {0} {1} 2> /dev/null".format(permissions, infoTuple[0].replace(".root","")))
            pass
        pass
    return

def scurveMultiProcessing(args, dictOfFiles):
    """
    Analyze a set of scurve measurements in parallel with anaUltraScurve

    args        - object returned by argparse.ArgumentParser.parse_args() 
    dictOfFiles - dictionary where keys are a tuple of the geographic address (shelf,slot,link) and
                  whose values are a tuple (filename,chamberName,GEBtype). See the values of the
                  gemVariants dictionary of gempython.tools.hw_constants for possible GEBtype values
    """

    # Setup a pool
    from multiprocessing import Pool
    from gempython.gemplotting.utils.anautilities import getNumCores2Use, init_worker
    pool = Pool(getNumCores2Use(args), initializer=init_worker) # Allocate number of CPU's based on getNumCores2Use()

    # Launch the pool processes
    from gempython.gemplotting.utils.scurveAlgos import anaUltraScurveStar
    import itertools, sys, traceback
    try:
        print("Launching scurve analysis processes, this may take some time, please be patient")
        pool.map_async(anaUltraScurveStar,
            itertools.izip(
                [args for geoAddr in dictOfFiles.keys()],                                    # args namespace
                [scurveFile[0] for scurveFile in dictOfFiles.values()],                      # scurveFilename
                [None for geoAddr in dictOfFiles.keys()],                                    # calFile
                [scurveFile[2] for scurveFile in dictOfFiles.values()],                      # GEBtype
                [scurveFile[0].replace(".root","") for scurveFile in dictOfFiles.values()],  # outputDir
                [None for geoAddr in dictOfFiles.keys()]                                     # vfatList
                )
            ).get(7200) # wait at most 2 hours
    except KeyboardInterrupt:
        printRed("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        printRed("Analysis Failed")
        sys.exit()
    except Exception as err:
        printRed("Caught {0}: {1}, terminating workers".format(type(err), err.message))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
        sys.exit()
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        printRed("Caught non-Python Exception %s"%(e))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
        sys.exit()
    else:
        printGreen("Analysis Completed Successfully")
        pool.close()
        pool.join()
        analysisPassed = True
    finally:
        # Ensure permissions of all files in subdirectories have group read and write
        setPermissions(dictOfFiles)
        pass

    return

def scurveParallelAna(args):
    """
    This will find all input files and launch a call of scurveMultiProcessing.
    
    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    # Get chamber_config
    confTuple = getChamberConfig(args)
    chamber_config = confTuple[0]
    GEBtype = confTuple[1]

    # Get list of input files
    dictOfFiles = getFileList("scurve",chamber_config,args.scandate,args.debug,GEBtype,args.inputfilename,args.listOfScandatesFile)

    # Make output directories and set permissions
    makeOutDirectories(dictOfFiles)

    # Launch the pool processes
    scurveMultiProcessing(args,dictOfFiles)
    
    return

def setPermissions(dictOfFiles, permissions="g+rw"):
    """
    For each tuple element of dictOfFiles this will create an output directory for the first element in the tuple

        dictOfFiles - dictionary of tuples where the first element of each tuple is a the name of a TFile.
                      See documentation for getFileList()
        permissions - Permissions to set the directory with
    """

    from gempython.utils.wrappers import runCommand
    import os
    for infoTuple in dictOfFiles.values():
        os.system("chmod -R {0} {1} 2> /dev/null".format(permissions,infoTuple[0].replace(".root","")))
        pass
    return

def threshTrkParallelAna(args):
    """
    This launches a call of anaUltraThreshold in parallel on each of the 
    input files that have been found.

    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    # Get chamber_config
    confTuple = getChamberConfig(args)
    chamber_config = confTuple[0]
    GEBtype = confTuple[1]

    # Get list of input files for threshold analysis
    dictOfFiles = getFileList("thresholdch",chamber_config,args.scandate,args.debug,GEBtype,args.inputfilename,args.listOfScandatesFile)
    
    # Setup a pool
    from multiprocessing import Pool
    from gempython.gemplotting.utils.anautilities import getNumCores2Use, init_worker
    pool = Pool(getNumCores2Use(args), initializer=init_worker) # Allocate number of CPU's based on getNumCores2Use()

    # Should the chConfig.txt file produced in the threshold analysis include updates from a completed scurve analysis?
    if args.scurveScandate is not None:
        dictOfScurveAnaFiles = getFileList("scurveAna",chamber_config,args.scurveScandate,args.debug,GEBtype,args.inputfilename,None)
        
        for geoAddr in dictOfFiles.keys():
            if geoAddr not in dictOfScurveAnaFiles.keys():
                # No scurve data for this geoAddr for this args.scurveScandate, set to None
                dictOfScurveAnaFiles[geoAddr] = (None,None)
    else:
        dictOfScurveAnaFiles = {geoAddr:(None,None) for geoAddr,thrFile in dictOfFiles.iteritems()}

    # Make output directories and set permissions
    makeOutDirectories(dictOfFiles)

    # Launch the pool processes
    from gempython.gemplotting.utils.threshAlgos import anaUltraThresholdStar
    import itertools, sys, traceback
    try:
        print("Launching threshold analysis processes, this may take some time, please be patient")
        pool.map_async(anaUltraThresholdStar,
                itertools.izip(
                    [args for geoAddr in dictOfFiles.keys()],                               # args namespace
                    [thrFile[0] for thrFile in dictOfFiles.values()],                       # thrFilename
                    [GEBtype[geoAddr] for geoAddr in dictOfFiles.keys()],                   # GEBtype
                    [thrFile[0].replace(".root","") for thrFile in dictOfFiles.values()],   # outputDir
                    [scurveFile[0] for scurveFile in dictOfScurveAnaFiles.values()]         # fileScurveFitTree
                    )
                ).get(7200) # wait at most 2 hours
    except KeyboardInterrupt:
        printRed("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        printRed("Analysis Failed")
    except Exception as err:
        printRed("Caught {0}: {1}, terminating workers".format(type(err), err.message))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        printRed("Caught non-Python Exception %s"%(e))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        printRed("Analysis Failed")
    else:
        printGreen("Analysis Completed Successfully")
        pool.close()
        pool.join()
    finally:
        # Ensure permissions of all files in subdirectories have group read and write
        setPermissions(dictOfFiles)
        pass

    return

def trimParallelAna(args):
    """
    This will find all input files and launch a call of scurveMultiProcessing.  If args.inputfilename
    is None and args.trimPoints is not None this will also analyze the selected scurves taken at each
    point in args.trimPoints in addition to the 'Trimmed' scurve for each of the input scandates. 
    
    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    # Get chamber_config
    confTuple = getChamberConfig(args)
    chamber_config = confTuple[0]
    GEBtype = confTuple[1]
    
    # Get templated list of input files for trim analysis
    dictOfFiles = getFileList("trimV3",chamber_config,args.scandate,args.debug,GEBtype,args.inputfilename,args.listOfScandatesFile)

    # Fill in the template if not requesting a specific file to analyze
    if args.inputfilename is None:
        if args.trimPoints is not None: # User wants to also analyze the trimmed points
            trimPts = [ int(trimPt) for trimPt in args.trimPoints.split(",") ] # Let this raise a ValueError if nonnumeric input?
            dictOfFilesByTrimVal = {}
            for geoAddr in dictOfFiles.keys():
                for trimVal in trimPts:
                    if abs(trimDac) > 63:
                        printYellow("trimParallelAna() - Requested trimPt {0} is outside the DAC range, only values in [-63,63] are possible; skipping.")
                        continue

                    # Determine trimVal and trimPol
                    if trimVal >= 0:
                        trimPol = 0
                    else:
                        trimPol = 1
                        trimVal = abs(trimVal)

                    # going to add an additional key to dictOfFiles for each trimVal
                    # Key will be an updated tuple (shelf,slot,link,trimVal,trimPol)
                    # Don't update original geoAddr until after all trimVal's have been considered
                    newGeoAddr = (geoAddr[0], geoAddr[1], geoAddr[2], trimVal, trimPol)
                    strTrimVal = "trimdac{0}_trimPol{1}".format(trimVal,trimPol)
                    dictOfFilesByTrimVal[newGeoAddr] = dictOfFiles[geoAddr][0].format(CONDITION=strTrimVal)
                    pass

                # Now set the "Trimmed" condition
                formatedFilename = dictOfFiles[geoAddr][0].format(CONDITION="Trimmed")
                infoTupleWithFormatting = (formatedFilename, dictOfFiles[geoAddr][1], dictOfFiles[geoAddr][2])
                dictOfFiles[geoAddr] = infoTupleWithFormatting
                pass
            
            # Now insert the items of dictOfFilesByTrimVal into dictOfFiles
            # Not gonna deep copy this to save memory; no need to deep copy
            for geoAddr,scurveFile in dictOfFilesByTrimVal.iteritems():
                dictOfFiles[geoAddr] = scurveFile # By construction 'geoAddr' is not already in dictOfFiles.keys()
        else: # User is only interested in the 'Trimmed' condition
            for geoAddr in dictOfFiles.keys():
                formatedFilename = dictOfFiles[geoAddr][0].format(CONDITION="Trimmed")
                infoTupleWithFormatting = (formatedFilename, dictOfFiles[geoAddr][1], dictOfFiles[geoAddr][2])
                dictOfFiles[geoAddr] = infoTupleWithFormatting
                pass
            pass
        pass

    # Make output directories and set permissions
    makeOutDirectories(dictOfFiles)

    # Launch the pool processes
    scurveMultiProcessing(args,dictOfFiles)

    return

if __name__ == '__main__':
    import argparse
    
    # create the parent parser for input files and stand config
    parser_fileAndConfig = argparse.ArgumentParser(add_help = False)
    parser_fileAndConfig.add_argument("-d","--debug", action="store_true",help = "Print additional debugging information")
    
    inputFileGroup = parser_fileAndConfig.add_mutually_exclusive_group(required=True)
    inputFileGroup.add_argument("-s","--scandate",type=str,help="scandate in YYYY.MM.DD.hh.mm format of input data.  Will find all files associated to this scandate for the relevant command.")
    inputFileGroup.add_argument("-i","--inputfilename",type=str,help="Specify single filename to analyze")
    inputFileGroup.add_argument("-l","--listOfScandatesFile",type=str,help="Specify listOfScandates file. Note this is {0}not supported for commands armDacCal, dacScanV3 or sbitThresh{1}.  The input file here is a tab delimited file where the first line is the column header 'ChamberName\tScandate' and subsequent lines are ChamberName and scandate pairs, e.g. 'GE11-X-S-BARI-0013\tYYYY.MM.DD.hh.mm'".format(colors.RED,colors.ENDC))

    chamberConfigGroup = parser_fileAndConfig.add_mutually_exclusive_group(required=True)
    chamberConfigGroup.add_argument("--chamberConfig",action="store_true",help="Use system specific chamber_config and GEBtype dictionaries")
    chamberConfigGroup.add_argument("--cNameAndAddr",type=str,help="Comma separated string used to build chamber_config and GEBtype dictionaries at runtime; format expected: detector S/N, detector type, uTCA shelf, AMC slot, and OH link, e.g. 'GE11-X-S-CERN-0001,short,1,4,7'.")
    chamberConfigGroup.add_argument("--mappingFile",type=str,help="Comma separated file used to build chamber_config and GEBtype dictionaries at runtime; each line gives respectively detector S/N, detector type, uTCA shelf, AMC slot, and OH link")

    # Parser for specifying parallel analysis behavior
    # Need double percent signs, see: https://thomas-cokelaer.info/blog/2014/03/python-argparse-issues-with-the-help-argument-typeerror-o-format-a-number-is-required-not-dict/
    parser_parallelAna = argparse.ArgumentParser(add_help = False)
    cpuUsagee = parser_parallelAna.add_mutually_exclusive_group(required=True)
    cpuUsagee.add_argument("--light", action="store_true", help="Analysis uses only 25%% of available cores")
    cpuUsagee.add_argument("--medium", action="store_true", help="Analysis uses only 50%% of available cores")
    cpuUsagee.add_argument("--heavy", action="store_true", help="Analysis uses only 75%% of available cores")

    # create the parent parser for making output plots w.r.t ASIC channel or panasonic connector pin
    parser_stripChanOrPinType = argparse.ArgumentParser(add_help = False)
    stripChanOrPinGroup = parser_stripChanOrPinType.add_mutually_exclusive_group(required=False)
    stripChanOrPinGroup.add_argument("-c","--channels", action="store_true", help="Make plots vs channels instead of strips")
    stripChanOrPinGroup.add_argument("-p","--panasonic", action="store_true", dest="PanPin",help="Make plots vs Panasonic pins instead of strips")

    # create the parent parser for zscore
    parser_zscore = argparse.ArgumentParser(add_help = False)
    parser_zscore.add_argument("-z","--zscore", type=float, default=10,help="Z-Score for Outlier Identification in MAD Algo, used to set HotChannel bit")

    from gempython.gemplotting.utils.anaoptions import parser_scurveChanMasks
    
    # List of parent parsers specifically scurce analysis
    listOfParentParsers4Scurves = [parser_fileAndConfig, parser_parallelAna, parser_scurveChanMasks, parser_stripChanOrPinType, parser_zscore]

    # create the parser that sub parsers will come from
    # =================================================
    parser = argparse.ArgumentParser(description='Arguments to supply to ana_scans.py')

    # Create sub parser
    # =================================================
    subparserCmds = parser.add_subparsers(help="Available subcommands and their descriptions.  To view the sub menu call \033[92mana_scans.py COMMAND -h\033[0m e.g. '\033[92mana_scans.py dacScanV3 -h\033[0m'")
   
    # Create subparser for armDacCal
    # ------------------------------
    parser_armDacCal = subparserCmds.add_parser("armDacCal", help="Uses the anaUltraScurve.py and calibrateThrDac.py tools to analyze calibration data of CFG_THR_ARM_DAC.  This will first check if all scurves in the input listOfScandates files specified by the scandate or inputfilename option have been analyzed.  If not it will analyze them all in parallel.  Then it will perform all calibration analyses in parallel", parents = listOfParentParsers4Scurves)

    parser_armDacCal.add_argument("--delimiter",type=str,default="\t",help="Character used to delimit the listOfScandates files that will be analyzed with the scandate or inputfilename option")
    parser_armDacCal.add_argument("--savePlots",action="store_true",help="Add this argument if you want to save per VFAT output *.png files")
    parser_armDacCal.add_argument("-n","--noLeg",action="store_true", help="Add this option if you do not want output plots to have a legend drawn on them")

    parser_armDacCal.set_defaults(func=calArmDACParallelAna)
    
    # Create subparser for dacScanV3
    # -------------------------------------------------
    parser_dacScan = subparserCmds.add_parser("dacScanV3", help="Uses the anaDACScan.py tool to analyze VFAT3 DAC scan data", parents = [parser_fileAndConfig])
    parser_dacScan.add_argument("--calFileList", type=str, default=None, help="Optional. File specifying which calFile to use for each OH. Format of each line: <shelf> <slot> <link> /path/to/my/cal/file.txt\nIf this is not provided the algorithm will search '$DATA_PATH/DetectorName/calFile_ADC0_DetectorName.txt")
    parser_dacScan.add_argument('-o','--outfilename', dest='outfilename', type=str, default="DACFitData.root", help="Filename to which output information is written")

    parser_dacScan.set_defaults(func=anaDACScan)
  
    # Create subparser for latency analysis taken with python tools
    # -------------------------------------------------
    parser_latency = subparserCmds.add_parser("lat", help="Uses the anaUltraLatency.py tool to analyze latency scans taken with either ultraLatency or 'run_scans.py lat'", parents = [parser_fileAndConfig, parser_parallelAna])
    parser_latency.add_argument("-f", "--fit", action="store_true", dest="performFit",help="Fit the latency distributions")
    parser_latency.add_argument("--latSigRange", type=str,  default=None, help="Comma separated pair of values defining expected signal range, e.g. lat #epsilon [41,43] is signal")
    parser_latency.add_argument("--latSigMaskRange", type=str,  default=None, help="Comma separated pair of values defining the region to be masked when trying to fit the noise, e.g. lat #notepsilon [40,44] is noise (lat < 40 || lat > 44)")

    parser_latency.set_defaults(func=latencyParallelAna)

    # Create subparser for sbitThresh
    # -------------------------------------------------
    parser_sbitThresh = subparserCmds.add_parser("sbitThresh", help="Analyzes scurve data taken with either sbitThreshScanParallel.py or 'run_scans sbitThresh'", parents = [parser_fileAndConfig])
    parser_sbitThresh.add_argument("-m","--maxNoiseRate", type=float, dest="maxNoiseRate", default=0, help="Max Noise Rate allowed in Hz")
    parser_sbitThresh.add_argument("--perchannel", action="store_true", help="If provided files to be analyzed will be treated as if they are a perchannel scan; otherwise they will be treated as if they where acquired taking all channels for a given VFAT in OR")

    parser_sbitThresh.set_defaults(func=anaSBITThresh)

    # Create subparser for scurve
    # -------------------------------------------------
    parser_scurve = subparserCmds.add_parser("scurve", help="Analyzes scurve data taken with either ultraScurve.py or 'run_scans.py scurve'", parents = listOfParentParsers4Scurves)
    parser_scurve.add_argument("--doNotFit", action="store_true", help="Do not attempt to fit the scurves")

    parser_scurve.set_defaults(func=scurveParallelAna)

    # Create subparser for tracking data threshold scans
    # -------------------------------------------------
    parser_thrTrk = subparserCmds.add_parser("thrDac", help="Analyzes tracking data threshold scans taken with either ultraThreshold.py or 'run_scans.py thrDac'", parents = [parser_fileAndConfig, parser_parallelAna, parser_stripChanOrPinType, parser_zscore] )

    parser_thrTrk.add_argument("--pervfat", action="store_true", help="Analysis for a per-VFAT scan (default is per-channel)")
    parser_thrTrk.add_argument("--scurveScandate",type=str, default=None,help="Provide this option if you want the chConfig.txt file(s) that is(are) produced to taken into account the channel register data from a previously analyzed set of scurves that share this scandate, in YYYY.MM.DD.hh.mm forma.")

    parser_thrTrk.set_defaults(func=threshTrkParallelAna)

    # Create subparser for trim
    # -------------------------------------------------
    parser_trim = subparserCmds.add_parser("trim", help="Analyzes scurves taken with trimChamberV3.py or `run_scans.py trim'", parents = listOfParentParsers4Scurves)
    parser_trim.add_argument("--trimPoints", type=str,default=None,help="Comma separated list of trim values that where used when trimming, e.g. '-63,0,63'.  Note a negative number implies the trimPol register was set to 1 instead of 0.  If not provided only the final 'Trimmed' scurve in a trim run will be analyzed. {0}This has no effect if paired with the `--inputfilename` argument{1}".format(colors.RED,colors.ENDC))

    parser_trim.set_defaults(func=trimParallelAna)

    # Parser the arguments and call the appropriate function
    # =================================================
    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    args = parser.parse_args()
    args.func(args)

    print("Good-bye")
