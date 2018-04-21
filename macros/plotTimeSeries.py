#!/usr/bin/env python

def makePlots(chamberName, anaType, vt1bump, elog_path):
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=threshold --make2D --alphaLabels -a --axisMax=10'
    os.system(call_command)
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=noise --make2D --alphaLabels -a --axisMin=0.05 --axisMax=0.3'
    os.system(call_command)
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=ped_eff --make2D --alphaLabels -a --axisMax=1'
    os.system(call_command)
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=mask --make2D --alphaLabels -a --axisMax=1'
    os.system(call_command)
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=maskReason --make2D --alphaLabels -a --axisMax=32'
    os.system(call_command)
    call_command = 'gemPlotter.py --skipBadFiles --infilename='+getDirByAnaType(anaType,chamberName)+'listOfScanDates.txt --anaType=scurveAna --branchName=vthr --alphaLabels -a'
    os.system(call_command)
    call_command = 'mkdir -p '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
    call_command = 'mv '+elog_path+'/summary*.png '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
    call_command = 'mv '+elog_path+'/gemPlotter*.root '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
  
if __name__== '__main__':
    import os
    from optparse import OptionParser, OptionGroup
    from gempython.utils.wrappers import envCheck
    from anautilities import getDirByAnaType, makeListOfScanDatesFile

    parser = OptionParser()
    parser.add_option("--vt1bump", type="int", dest="vt1bump", default=0,
                      help="Specify the value of vt1bump", metavar="vt1bump")
    parser.add_option("--anaType", type="string", dest="anaType", default="scurve",
                      help="Specify Scan Type", metavar="anaType")
    parser.add_option("--listOfScanDatesOnly", action="store_true", dest="listOfScanDatesOnly",
                      help="Make a listOfScanDates.txt for each detector, no plots are made", metavar="listOfScanDatesOnly")

    from datetime import datetime, timedelta 
    date_two_weeks_ago = datetime.now() - timedelta(days=14)
    defaultStartTime = date_two_weeks_ago.strftime("%Y.%m.%d.%H.%M")

    dateOptions = OptionGroup(parser,
            "Date Options"
            "Options for specifying the starting and ending date range")
    dateOptions.add_option("--startDate", type="string", dest="startDate", default=defaultStartTime,
                      help="Starting date range in YYYY.MM.DD format", metavar="startDate")
    dateOptions.add_option("--endDate", type="string", dest="endDate", default=None,
                      help="Starting date range in YYYY.MM.DD format", metavar="endDate")

    parser.add_option_group(dateOptions)
    (options, args) = parser.parse_args()
    
    from mapping.chamberInfo import chamber_config
    
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    dataPath  = os.getenv('DATA_PATH')
    elog_path = os.getenv("ELOG_PATH")
    vt1bump = 'vt1bump'+str(options.vt1bump)
    anaType = options.anaType
   
    print "Options: vt1bump=%s, dataPath=%s, anaType=%s"%(vt1bump, dataPath, anaType)
    for chamber in chamber_config.values():
        makeListOfScanDatesFile(chamber, anaType, options.startDate, options.endDate)
        if not options.listOfScanDatesOnly:
            makePlots(chamber, anaType, vt1bump, elog_path)
            call_command = 'rm '+getDirByAnaType(anaType,chamber)+'listOfScanDates.txt'
            os.system(call_command) # remove the file lists
            pass
        pass
