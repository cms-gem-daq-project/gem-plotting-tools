#!/bin/env python
"""
    Script to analyze sbitreadout data
    By: Caterina Aruta (caterina.aruta@cern.ch) and Francesco Ivone (francesco.ivone@cern.ch)
    """

r"""
``anaSBitReadout.py`` --- Unpack and plot the data collected by sbitReadOut.py
=========================================================
Synopsis
--------
**anaSBitReadout.py**  :token:`-i` <*INPUT FOLDER*> :token:`-t` <*GEB size*> :token:`-o` <*OUTPUT FILE*>
Description
-----------
The :program:`anaSBitReadout.py` tool is for unpacking data collected with sbitReadOut.py. It will make a TFile containing:
    -TTree "Packed" which are the data as they have been read
    -TTree "unPacked" which is a summary of the unpacked data
    -Folder "VFATs" which are the unpacked data sorted by VFAT number
    -Folder "iETAs" which are the unpacked data sorted by iEta number
   
It will also print the following plots in .png format:
    -ChannSummary.png which is a 3x8 canvas containing all the 24 VFATs with their channel hits
    -StripSummary.png which is a 3x8 canvas containing all the 24 VFATs with their strips hits
    -ietaChanSummary.png which is a summary of the channel hits for each of the 8 iEta positions
    -ietaStripSummary.png which is a summary of the strip hits for each of the 8 iEta positions
    -ietaDelaySummary.png which is a summary of the delay for each of the 8 iEta positions
    -ietaSbitSizeSummary.png which is a summary of the sbitsize for each of the 8 iEta positions
    -ChvsiEta.png which is a 2D histogram with channel number and iEta as X-Y axis
    -StripvsiEta.png which is a 2D histogram with strip number and iEta as X-Y axis

Mandatory arguments
-------------------
The following list shows the mandatory inputs that must be supplied to execute
the script.

.. program:: anaSBitReadout.py

.. option:: path
    Physical path of the directory with .dat files to be passed to :program:`gemPlotter.py`.

.. option:: type
    Size of the GEB. Could be long or short. If this option is not provided the GEB type will be assumed to be long

Optional arguments
------------------
.. option:: -o, --outfilename <STRING>
    Name of the otuput TFile. If this option is not provided the TFile will be named sbitReadOut.root
.. option:: -m, --mapping <STRING>
    Mapping file that provides the channel <-> strip conversion. If this option is not provided a default mapping will be loaded based on GEB size

Examples
--------

.. code-block:: bash
    anaSBitReadout.py -i <pathname> -t short
resulting plots will be stored under:
.. code-block:: bash
    pathname/sbitReadOut/
"""

if __name__ == '__main__':
    import pkg_resources
    mappath = pkg_resources.resource_filename(
        'gempython.gemplotting', 'mapping/')

    import argparse
    parser = argparse.ArgumentParser(
        description="Unpack and plot data collected by sbitReadOut.py. The data are stored in the folder: \n path/sbitReadout/ ")
    parser.add_argument("path", type=str, help="Specify the folder containing the .dat files collected by sbitReadOut.py")
    parser.add_argument("GEBtype", type=str,help="Specify GEB (long/short). If not provided, default value is long")
    parser.add_argument("-o", "--outfilename", type=str, default="sbitReadOut.root", dest="outfilename",
                        help="Specify Output Filename. If not provided default value is sbitReadOut.root")
    parser.add_argument("-m", "--mapping", type=str, dest="mapping",
                        help="Specify the txt file containing the channel <-> strip mapping. If not provided a default mapping will be loaded based on GEB size")

    args = parser.parse_args()
    path = args.path
    size = ((args.GEBtype).lower())
    mapping = args.mapping

    # Check the validity of the parsed arguments
    if size not in ('long', 'short'):
        raise AssertionError("Invalid value of GEBtype")
    else:
        pass

    import os
    if not os.path.isdir(path):
        raise IOError("No such file or directory", path)
    else:
        pass

    if mapping is None:
        mapping = mappath+size+"ChannelMap_VFAT3-HV3b-V1_V2_V4.txt"
    elif not os.path.isfile(mapping):
        raise IOError("No such file or directory", mapping)
    else:
        pass

    filename = path+"/sbitReadOut"
    outfilename = args.outfilename

    #import sys
    #from subprocess import call

    from gempython.utils.wrappers import runCommand
    print("Analyzing: '%s'" % path)
    runCommand(["mkdir", "-p", filename])

    """
    At the moment the output of the sbitReadout.py are .dat files with headers that will automatically fill the ROOT TTree. However ther is one last ':' in the first line that shouldn't be there; consequently the ReadFile function is not able to understand the header. So before reading these .dat files, one has to be sure to remove the ':'
    To achieve this the following command is needed (removes the last : in the header of all .dat files in the input path)
    """
    # os.system("find "+path+" -iname \*.dat -exec sed -i 's/7\/i:/7\/i/g' {} \;")

    # Set default histo behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    # Loading the dictionary with the mapping
    from gempython.gemplotting.utils.anautilities import make3x8Canvas, saveSummaryByiEta, getMapping
    vfat_ch_strips = getMapping(mapping)
    print("\nVFAT channels to strips \n"+mapping+"\nMAP loaded")

    # Loading and reversing the dictionary with (eta , phi) <-> vfatN
    from gempython.gemplotting.mapping.chamberInfo import chamber_iEta2VFATPos
    from gempython.utils.nesteddict import nesteddict as ndict
    etaphi_to_vfat = ndict()
    for i in range(1, 9):
        etaphi_to_vfat[i] = {row:ieta for ieta,row in chamber_iEta2VFATPos[i].iteritems()}

    """
    Now it's time to load all the input files and to merge them into one root TTree
    The TTree file it's going to auto extend each time a new file is found
    A TFile it's going to hold this TTree
    """
    # Creating the output File and TTree
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    inT = r.TTree('Packed', 'Tree Holding packed raw data')

    # get starting time
    import time
    start_time = time.time()
    
    # searching for all the files with this format and adding them to the TTree
    import glob
    print ("\nReading .dat files from the folder %s" % path)
    for idx, file in enumerate(glob.glob(path+'/sbitReadOut_run*.dat')):
        os.system("cat "+file+" | tail -n +2 >> "+path + "catfile.txt")
        os.system("echo" + "" + " >>" + path + "catfile.txt")
    inT.ReadFile(path+"catfile.txt", "evtNum/i:sbitClusterData0/i:sbitClusterData1/i:sbitClusterData2/i:sbitClusterData3/i:sbitClusterData4/i:sbitClusterData5/i:sbitClusterData6/i:sbitClusterData7/i")
    print ("%d input files have been read and added to the TTree" % (idx+1))

    inT.Write()
    print ('TTree written\n')
    print ("Removing the catfile.txt ...")
    runCommand(["rm", path+"catfile.txt"])
    print ("Done\n")
    """
    Going to build the output tree starting from the previous TTree converted into an array.
    First of all, going to initilize the array which will hold the data
    """

    # copying the branch names in order to work with input TTree as an array
    import numpy as np
    branches = inT.GetListOfBranches()
    brName = np.empty([branches.GetEntries()], dtype='object')
    for i in range(0, branches.GetEntries()):
        brName[i] = branches[i].GetName()

    # converting the input tree in array then intialiting the unpackd TTree
    import root_numpy as rp
    rawData = rp.tree2array(tree=outF.Packed, branches=brName)
    outT = r.TTree('unPacked', 'Tree holding unpacked data')

    """
    BRANCH VARIABLES DEFINITION
    vfatCH and strip have bigger size because they can hold different
    number of data: from 2 up to 16 (depending on cluster size). In this
    way the associated branch can be filled with these data in one line
    - 16 it's the max value allowed!
    - In each run it will be filled from 0 up to chHitPerCluster
    """
    from array import array
    vfatN = array('i', [0])
    chHitPerCluster = array('i', [0])
    vfatCH = array('i', 16*[0])
    strip = array('i', 16*[0])
    sbitSize = array('i', [0])
    L1Delay = array('i', [0])

    outT.Branch('vfatN', vfatN, 'vfatN/I')
    outT.Branch('chHitPerCluster', chHitPerCluster, 'chHitPerCluster/I')
    outT.Branch('vfatCH', vfatCH, 'vfatCH[chHitPerCluster]/I')
    outT.Branch('strip', strip, 'strip[chHitPerCluster]/I')
    outT.Branch('sbitSize', sbitSize, 'sbitSize/I')
    outT.Branch('L1Delay', L1Delay, 'L1Delay/I')

    """
    Defining both VFAT and iEta histos
    """
    # initializing vfat 1Dhisto
    # While strip & ch branch are filled with arrays, histos are filled with one entries at a time

    vfat_h_strip = ndict()
    vfat_h_ch = ndict()
    vfat_h_sbitSize = ndict()
    vfat_h_delay = ndict()

    for i in range(0, 24):
        vfat_h_strip[i] = r.TH1F("h_VFAT{0}_strips_vs_hit".format(i), "VFAT{0}".format(i), 128, 0., 128.)
        vfat_h_ch[i] = r.TH1F("h_VFAT{0}_chan_vs_hit".format(i), "VFAT{0}".format(i), 128, 0., 128.)
        vfat_h_sbitSize[i] = r.TH1F("h_VFAT{0}_sbitSize_vs_hit".format(i), "VFAT{0}: SBIT Size".format(i), 8, 0., 8.)
        vfat_h_delay[i] = r.TH1F("h_VFAT{0}_L1A_sbit_delay".format(i), "VFAT{0}: L1A delay".format(i), 4096, 0., 4096.)
        vfat_h_ch[i].SetXTitle("Chann Num")
        vfat_h_strip[i].SetXTitle("Strip Num")
        vfat_h_strip[i].SetFillColorAlpha(r.kBlue, 0.35)
        vfat_h_ch[i].SetFillColorAlpha(r.kBlue, 0.35)

    # initializing eta 1Dhisto
    ieta_h_strip = ndict()
    ieta_h_ch = ndict()
    ieta_h_sbitSize = ndict()
    ieta_h_delay = ndict()

    for i in range(1, 9):
        ieta_h_strip[i] = r.TH1F("h_ieta{0}_strips_vs_hit".format(i), "i#eta = {0} | i#phi (1,2,3)".format(i), 384, 0., 384.)
        ieta_h_ch[i] = r.TH1F("h_ieta{0}_chan_vs_hit".format(i), "i#eta = {0} | i#phi (1,2,3)".format(i), 384, 0., 384.)
        ieta_h_sbitSize[i] = r.TH1F("h_ieta{0}_sbitSize_vs_hit".format(i), "i#eta = {0} SBIT Size".format(i), 8, 0., 8.)
        ieta_h_delay[i] = r.TH1F("h_ieta{0}_L1A_Sbit_delay".format(i), "i#eta = {0} L1A delay".format(i), 4096, 0., 4096.)

        ieta_h_strip[i].SetFillColorAlpha(r.kBlue, 0.35)
        ieta_h_ch[i].SetFillColorAlpha(r.kBlue, 0.35)
        ieta_h_strip[i].SetXTitle("Strip num")
        ieta_h_ch[i].SetXTitle("Chan num")

    # initializing 2Dhisto
    dict_h2d_ieta_strip = ndict()
    dict_h2d_ieta_ch = ndict()
    dict_h2d_ieta_strip[0] = r.TH2I('h2d_ieta_strip', 'Strips summary        (i#phi = 1,2,3);strip number;i#eta', 384, 0, 384, 8, 0.5, 8.5)
    dict_h2d_ieta_ch[0] = r.TH2I('h_2d_ieta_ch', 'Channels summary        (i#phi = 1,2,3);chan number;i#eta', 384, 0, 384, 8, 0.5, 8.5)

    # loop over all branch names but the first (evnt num)
    from gempython.gemplotting.mapping.chamberInfo import chamber_vfatPos2iEtaiPhi as vfat_to_etaphi
    from gempython.utils.gemlogger import printRed, printYellow
    for branch in brName[1:]:
        print ("Unpacking now %s, %s entries" %
               (branch, str(rawData[branch].shape).translate(None, "(),")))
        for word in rawData[branch]:
            sbitAddr = ((word) & 0x7FF)
            
            # INVALID ADDRESS CHECK
            if sbitAddr >= 1536:
                continue

            vfatN[0] = (7 - sbitAddr/192 + ((sbitAddr % 192)/64)*8)
            sbitSize[0] = ((word >> 11) & 0x7)
            chHitPerCluster[0] = 2*(sbitSize[0]+1)
            L1Delay[0] = ((word >> 14) & 0xFFF)
            eta = vfat_to_etaphi[vfatN[0]][0]
            phi = vfat_to_etaphi[vfatN[0]][1]
            
            # SBIT always includes doublet of adjacent channels
            vfatCH[0] = 2*(sbitAddr % 64)
            vfatCH[1] = vfatCH[0] + 1
            strip[0] = vfat_ch_strips[vfatN[0]]['Strip'][vfatCH[0]]
            strip[1] = vfat_ch_strips[vfatN[0]]['Strip'][vfatCH[1]]

            # In case of wrong mapping adjacent channels may not be adjacent strips, which is physically inconsistent
            if(np.abs(strip[0] - strip[1]) > 1):
                printRed("WARNING: not adjacent strips")

            # filling vfat 1Dhistos
            vfat_h_strip[vfatN[0]].Fill(strip[0])
            vfat_h_strip[vfatN[0]].Fill(strip[1])
            vfat_h_ch[vfatN[0]].Fill(vfatCH[0])
            vfat_h_ch[vfatN[0]].Fill(vfatCH[1])
            vfat_h_delay[vfatN[0]].Fill(L1Delay[0])
            vfat_h_sbitSize[vfatN[0]].Fill(sbitSize[0])

            # filling ieta 1Dhistos
            ieta_h_strip[eta].Fill((phi-1)*128+strip[0])
            ieta_h_strip[eta].Fill((phi-1)*128+strip[1])
            ieta_h_ch[eta].Fill((phi-1)*128+vfatCH[0])
            ieta_h_ch[eta].Fill((phi-1)*128+vfatCH[1])
            ieta_h_delay[eta].Fill(L1Delay[0])
            ieta_h_sbitSize[eta].Fill(sbitSize[0])

            # filling 2Dhisto
            dict_h2d_ieta_strip[0].Fill(strip[0]+128*(phi-1), eta)
            dict_h2d_ieta_strip[0].Fill(strip[1]+128*(phi-1), eta)
            dict_h2d_ieta_ch[0].Fill(vfatCH[0]+128*(phi-1), eta)
            dict_h2d_ieta_ch[0].Fill(vfatCH[1]+128*(phi-1), eta)

            """
            A single sbit word can specify up to 16 adjacent channel hits
            The following loop takes care of this possibility
            """
            for i in range(2, chHitPerCluster[0]):
                # filling the adjacent channel
                vfatCH[i] = vfatCH[i-1] + 1
                # if the new channel exceeds the total VFAT channels, increase phi and move to the first cannel of the next VFAT
                if vfatCH[i] >= 128 and phi < 3:
                    phi = phi + 1
                    vfatCH[i] = 0
                    vfatN[0] = etaphi_to_vfat[eta][phi]
                elif vfatCH[i] >= 128 and phi >= 3:
                    # if the maximum of phi is reached (so there is no "next VFAT"), there must be some kind of error
                    printRed("ERROR: exceeding VFAT position on the GEB")
                    printYellow("word 0x{0:x}".format(word))
                    printYellow("VFATN: {0}".format(vfatN[0]))
                    printYellow("VFATCH: {0}".format(vfatCH[0]))
                    printYellow("Cluster Size: {0}".format(sbitSize[0]))
                    printYellow("Eta: {0}".format(eta))
                    printYellow("phi: {0}".format(phi))
                    break
                # updating the strip
                strip[i] = vfat_ch_strips[vfatN[0]]['Strip'][vfatCH[i]]

                # At this point both strip and ch are updated, going to fill the histos
                vfat_h_strip[vfatN[0]].Fill(strip[i])
                vfat_h_ch[vfatN[0]].Fill(vfatCH[i])

                ieta_h_strip[eta].Fill((phi-1)*128+strip[i])
                ieta_h_ch[eta].Fill((phi-1)*128+vfatCH[i])
                dict_h2d_ieta_strip[0].Fill(strip[i]+128*(phi-1), eta)
                dict_h2d_ieta_ch[0].Fill(vfatCH[i]+128*(phi-1), eta)

            outT.Fill()

        pass

    #
    # Summaries Canvas
    #
    # make3x8Canvas
    canv_3x8 = make3x8Canvas(
        name="Strip_3x8canv",
        initialContent=vfat_h_strip,
        initialDrawOpt="hist",
        secondaryContent=None,
        secondaryDrawOpt="hist")
    canv_3x8.SaveAs(filename+'/StripSummary.png')

    canv_3x8 = make3x8Canvas(
        name="Chann_3x8canv",
        initialContent=vfat_h_ch,
        initialDrawOpt="hist",
        secondaryContent=None,
        secondaryDrawOpt="hist")
    canv_3x8.SaveAs(filename+'/ChannSummary.png')

    canv_3x8 = make3x8Canvas(
                             name="SbitSize_3x8canv",
                             initialContent=vfat_h_sbitSize,
                             initialDrawOpt="hist",
                             secondaryContent=None,
                             secondaryDrawOpt="hist")
    canv_3x8.SaveAs(filename+'/SbitSizeSummary.png')

    canv_3x8 = make3x8Canvas(
                             name="L1A_Delay_3x8canv",
                             initialContent=vfat_h_delay,
                             initialDrawOpt="hist",
                             secondaryContent=None,
                             secondaryDrawOpt="hist")
    canv_3x8.SaveAs(filename+'/L1A_DelaySummary.png')

    # saveSummaryByiEta
    saveSummaryByiEta(ieta_h_strip, name='%s/ietaStripSummary.png' %
                      filename, trimPt=None, drawOpt="")
    saveSummaryByiEta(ieta_h_ch, name='%s/ietaChanSummary.png' %
                      filename, trimPt=None, drawOpt="")
    saveSummaryByiEta(ieta_h_sbitSize, name='%s/ietaSbitSizeSummary.png' %
                      filename, trimPt=None, drawOpt="")
    saveSummaryByiEta(ieta_h_delay, name='%s/ietaDelaySummary.png' %
                      filename, trimPt=None, drawOpt="")

    # Making&Filling folders in the TFile
    outT.Write()
    vfatDir = outF.mkdir("VFATs")
    ietaDir = outF.mkdir("iETAs")

    vfatDir.cd()
    for vfat in range(0, 24):
        tempDir = vfatDir.mkdir("VFAT%i" % vfat)
        tempDir.cd()
        vfat_h_strip[vfat].Write()
        vfat_h_ch[vfat].Write()
        vfat_h_delay[vfat].Write()
        vfat_h_sbitSize[vfat].Write()

    ietaDir.cd()
    for ieta in range(1, 9):
        tempDir = ietaDir.mkdir("iETA%i" % ieta)
        tempDir.cd()
        ieta_h_strip[ieta].Write()
        ieta_h_ch[ieta].Write()
        ieta_h_delay[ieta].Write()
        ieta_h_sbitSize[ieta].Write()

    # 2D histos aesthetics
    line1 = r.TLine(128, 0.5, 128, 8.5)
    line2 = r.TLine(256, 0.5, 256, 8.5)
    line1.SetLineColor(r.kRed)
    line1.SetLineWidth(3)
    line2.SetLineColor(r.kRed)
    line2.SetLineWidth(3)

    canv = r.TCanvas("summary", "summary", 500*8, 500*3)
    canv.SetGridy()
    canv.cd()
    dict_h2d_ieta_strip[0].Draw('9COLZ')
    line1.Draw()
    line2.Draw()
    canv.Update()
    canv.SaveAs(filename+'/StripvsiEta.png')

    canv.Clear()
    canv.cd()
    dict_h2d_ieta_ch[0].Draw('COLZ')
    line1.Draw()
    line2.Draw()
    canv.Update()
    canv.SaveAs(filename+'/ChvsiEta.png')

    outF.Close()
    print ("\n---Took %f seconds for each .dat file---" %
           ((time.time() - start_time) / int(idx)))
    print ("\nGaranting permission to %s..." % filename)
    runCommand(["chmod", "-R", "770", filename])
    print ("Data stored in %s" % (filename+'/'+outfilename))
    print("Bye now")
