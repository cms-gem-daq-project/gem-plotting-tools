#!/usr/bin/env python

def makeInputList(chamberName, scanType):
    ofname = getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt'
    with open(template,"rt") as fin:
        with open(ofname, "wt") as fout:
            for line in fin:
                fout.write(line.replace("GEMINI", chamberName)) 

def makePlots(chamberName, scanType, vt1bump, elog_path):
    call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=threshold --make2D --alphaLabels -c -a'
    os.system(call_command)
    call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=noise --make2D --alphaLabels -c -a --axisMax=25'
    os.system(call_command)
    call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=mask --make2D --alphaLabels -c -a --axisMax=1'
    os.system(call_command)
    call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=maskReason --make2D --alphaLabels -c -a --axisMax=32'
    os.system(call_command)
    call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+getDirByAnaType(scanType,chamberName)+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=vthr --alphaLabels -c -a'
    os.system(call_command)
    call_command = 'sudo -u gempro -i mkdir -p '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
    call_command = 'sudo -u gempro -i mv '+elog_path+'/summary*.png '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
    call_command = 'sudo -u gempro -i mv '+elog_path+'/gemPlotter*.root '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
    os.system(call_command)
  
if __name__== '__main__':
    import os
    from optparse import OptionParser
    from gempython.utils.wrappers import envCheck
    from anautilities import getDirByAnaType
    
    parser = OptionParser()
    parser.add_option("-t", "--templatefile", type="string", dest="tfilename", default="listOfScanDates_gemPlotter.txt",
                      help="Specify Template Filename", metavar="tfilename")
    parser.add_option("--vt1bump", type="int", dest="vt1bump", default=0,
                      help="Specify the value of vt1bump", metavar="vt1bump")
    parser.add_option("--scanType", type="string", dest="scanType", default="scurve",
                      help="Specify Scan Type", metavar="scanType")
    
    (options, args) = parser.parse_args()
    
    from mapping.chamberInfo import chamber_config
    
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    dataPath  = os.getenv('DATA_PATH')
    elog_path = os.getenv("ELOG_PATH")
    template = options.tfilename
    vt1bump = 'vt1bump'+str(options.vt1bump)
    scanType = options.scanType
    
    print "Options: vt1bump=%s, template=%s, dataPath=%s, scanType=%s"%(vt1bump, template, dataPath, scanType)
    for chamber in chamber_config.values():
        makeInputList(chamber, scanType)
        makePlots(chamber, scanType, vt1bump, elog_path)
        call_command = 'rm '+getDirByAnaType(scanType,chamber)+'listOfScanDates_gemPlotter.txt'
        os.system(call_command) # remove the file lists


