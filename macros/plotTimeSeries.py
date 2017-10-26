#!/usr/bin/env python
import os
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-t", "--templatefile", type="string", dest="tfilename", default="listOfScanDates_gemPlotter.txt",
                  help="Specify Template Filename", metavar="tfilename")
parser.add_option("--vt1bump", type="int", dest="vt1bump", default=0,
                  help="Specify the value of vt1bump", metavar="vt1bump")
parser.add_option("--dataprefix", type="string", dest="data_prefix", default="/gemdata/",
                  help="Specify Data Prefix", metavar="data_prefix")
parser.add_option("--scanType", type="string", dest="scanType", default="scurve",
                  help="Specify Scan Type", metavar="scanType")

(options, args) = parser.parse_args()

chambers = ["GEMINIm01L1",
            "GEMINIm27L1",
            "GEMINIm27L2",
            "GEMINIm28L1",
            "GEMINIm28L2",
            "GEMINIm29L1",
            "GEMINIm29L2",
            "GEMINIm30L1",
            "GEMINIm30L2"]

vt1bump = 'vt1bump'+str(options.vt1bump)
data_prefix = options.data_prefix
scanType = '/'+options.scanType+'/'
template = options.tfilename
elog_path = os.getenv("ELOG_PATH")

print "Options: vt1bump=%s, template=%s, data_prefix=%s, scanType=%s"%(vt1bump, template, data_prefix, scanType)

def makeInputList(chamberName):
  ofname = data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt'
  with open(template,"rt") as fin:
    with open(ofname, "wt") as fout:
      for line in fin:
        fout.write(line.replace("GEMINI", chamberName)) 

def makePlots(chamberName, vt1bump):
  call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=threshold --make2D --alphaLabels -c -a'
  os.system(call_command)
  call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=noise --make2D --alphaLabels -c -a --axisMax=25'
  os.system(call_command)
  call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=mask --make2D --alphaLabels -c -a --axisMax=1'
  os.system(call_command)
  call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=maskReason --make2D --alphaLabels -c -a --axisMax=32'
  os.system(call_command)
  call_command = 'sudo -u gempro -i gemPlotter.py --infilename='+data_prefix+chamberName+scanType+'listOfScanDates_gemPlotter.txt --anaType=scurveAna --branchName=vthr --alphaLabels -c -a'
  os.system(call_command)
  call_command = 'sudo -u gempro -i mkdir -p '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
  os.system(call_command)
  call_command = 'sudo -u gempro -i mv '+elog_path+'/summary*.png '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
  os.system(call_command)
  call_command = 'sudo -u gempro -i mv '+elog_path+'/gemPlotter*.root '+elog_path+'/timeSeriesPlots/'+chamberName+'/'+vt1bump+'/'
  os.system(call_command)
  
def main():
  for chamber in chambers:
    makeInputList(chamber)
    makePlots(chamber, vt1bump)
    call_command = 'rm '+data_prefix+chamber+scanType+'listOfScanDates_gemPlotter.txt'
    os.system(call_command) # remove the file lists

if __name__== '__main__':
  main()
