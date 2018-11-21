#!/bin/env python

def getDateFromStr(strDate,strFormat="YYYY.MM.DD.hh.mm"):
    """
    Reads in a date given by strDate following strFormat and returns a datetime.datetime object.
    strFormat will look for typical case sensitive date tagging characters:
        
        Y - year
        M - month
        D - day
        h - hour
        m - minute
        s -second

    And generate substrings from strDate

    strDate - string specifying the date
    strFormat - string specifying the format of the strDate
    """

    strDate = strDate.strip()

    # Get the Positions
    posYearMax = strFormat.rfind('Y')
    posYearMin = strFormat.find('Y')

    posMonthMax = strFormat.rfind('M')
    posMonthMin = strFormat.find('M')

    posDayMax = strFormat.rfind('D')
    posDayMin = strFormat.find('D')

    posHourMax = strFormat.rfind('h')
    posHourMin = strFormat.find('h')

    posMinuteMax = strFormat.rfind('m')
    posMinuteMin = strFormat.find('m')

    posSecondMax = strFormat.rfind('s')
    posSecondMin = strFormat.find('s')

    # Extract info
    thisYear = 2017
    if posYearMin > -1:
        thisYear = int(strDate[posYearMin:posYearMax+1])
        if thisYear < 2000:
            thisYear += 2000
        pass

    thisMonth = 1
    if posMonthMin > -1:
        thisMonth = int(strDate[posMonthMin:posMonthMax+1])
        pass

    thisDay = 1
    if posDayMin > -1:
        thisDay = int(strDate[posDayMin:posDayMax+1])
        pass

    thisHour = 0
    if posHourMin > -1:
        thisHour = int(strDate[posHourMin:posHourMax+1])
        pass

    thisMin = 0
    if posMinuteMin > -1:
        thisMin = int(strDate[posMinuteMin:posMinuteMax+1])
        pass

    thisSec = 0
    if posSecondMin > -1:
        thisSec = int(strDate[posSecondMin:posSecondMax+1])
        pass
    
    # Form a date time object, see: https://docs.python.org/2/library/datetime.html
    import datetime
    thisTime = datetime.datetime(
          year=thisYear,
          month=thisMonth,
          day=thisDay,
          hour=thisHour,
          minute=thisMin,
          second=thisSec)

    return thisTime

def getChanLossPlot(args, chamberName, infilename, startingTime):
    """
    Returns a tuple (TGraphErrors, integer) to the user specifying channel loss

    args - object returned by ArgumentParser.parse_args()
    chamberName - String, chamber name
    infilename - physical filename
    startingTime - datetime.datetime object specifying starting date
    """

    # Check infilename input file
    try:
        infilename = open(infilename, 'r')  
    except Exception as e:
        print( '%s does not seem to exist or is not readable'%(infilename) )
        print( e )
        exit(os.EX_NOINPUT)
        pass

    g_chanLostData = r.TGraphErrors()
    g_chanLostData.SetName("g_chanLoss_{0}".format(chamberName))
    chanLost = 0
    maxChanLoss = -1
    for idx,line in enumerate(infilename):
        if line[0] == "#": # allow for comments
            continue
        
        # Split the line
        line = line.strip('\n') # remove trailing new line characters
        dataEntry = line.rsplit(args.delimiter) # gives a list of strings
        
        # Handle column header
        if idx == 0:
            continue # move to next line

        # Load Data from infilenameFile
        evtTimeRangeInit = getDateFromStr(dataEntry[0],args.startDateFormat)
        evtTimeRangeFinal= getDateFromStr(dataEntry[1],args.endDateFormat)

        evtTime = 0.5 * (evtTimeRangeFinal - evtTimeRangeInit).total_seconds() + (evtTimeRangeInit - startingTime).total_seconds()
        
        if args.cummulative:
            chanLost += float(dataEntry[2])
        else:
            chanLost = float(dataEntry[2])
            if chanLost > maxChanLoss:
                maxChanLoss = chanLost
                pass

        if args.debug:
            print("{0} \t {1} \t {2}".format(line,evtTimeRangeInit,evtTimeRangeFinal))

        # Plot as a percentage?
        if args.percentage:
            fillPt = chanLost / args.totalChan
        else:
            fillPt = chanLost
        
        # Add the point
        g_chanLostData.SetPoint(
                g_chanLostData.GetN(),
                evtTime,
                fillPt)
        g_chanLostData.SetPointError(
                g_chanLostData.GetN() - 1, 
                abs( 0.5*(evtTimeRangeFinal - evtTimeRangeInit).total_seconds() ),
                0)
        pass

    if args.cummulative:
        maxChanLoss = chanLost
        pass

    return (g_chanLostData, maxChanLoss)

if __name__ == "__main__":
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getStringNoSpecials
    
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="Makes a time series plot")
    parser.add_argument("fileChanLoss",type=str,help="physical filename specifying channel loss data")
    parser.add_argument("-f","--fileObsData",type=str,help="If provided plots the data contained here on a secondary y-axis on top of the channel loss data. Format should be a delimited file (matching 'delimiter'), first line should be a column header.  Subsequent lines are delimited datetime then observable data.  Datetime is expected to be in format 'YYYY.MM.DD hh:mm:ss'.")
    parser.add_argument("-c","--cummulative",action="store_true",help="If provided a cummulative channel loss plot is made instead of an instantaneous loss plots",default=None)
    parser.add_argument("-d","--delimiter",type=str,help="delimiter in fileChanLoss file",default=",")
    parser.add_argument("--debug",action="store_true",help="print additional debugging info")
    parser.add_argument("-p","--percentage",action="store_true",help="provide output data as a percentage of the total number of channels in a detector")
    parser.add_argument("--logy1",action="store_true",help="primary y-axis is logarithmic")
    parser.add_argument("--logy2",action="store_true",help="secondary y-axis is logarithmic")
    parser.add_argument("-n","--noLeg",action="store_true",help="Do not draw TLegend")
    parser.add_argument("-t","--totalChan",type=int,help="Specify the total number of channels in a detector",default=3072)

    dateGroup = parser.add_argument_group(title="Datetime and Datetime Formatting",description="Parameters specfiying the datetime format in fileChanLoss; if fileObsData is *not* provided this also specifies the starting and ending dates")
    dateGroup.add_argument("-s","--startDate",type=str,help="starting date given in format specified by 'startDateFormat'",default="2017.04.03.00.01")
    dateGroup.add_argument("--startDateFormat",type=str,help="specifiy starting datetime format, use characters 'Y','M','D','m','h','s' to define format, e.g. '2018.11.05.23.59' is in format 'YYYY.MM.HH.DD.hh.mm' while '18.25.04 12:13' is 'YY.MM.DD hh:mm'",default="YYYY.MM.DD.hh.mm")
    dateGroup.add_argument("-e","--endDate",type=str,help="ending date given in format specified by 'endDateFormat'",default="2018.11.05.23.59")
    dateGroup.add_argument("--endDateFormat",type=str,help="specifiy ending datetime format, use characters 'Y','M','D','m','h','s' to define format, e.g. '2018.11.05.23.59' is in format 'YYYY.MM.HH.DD.hh.mm' while '18.25.04 12:13' is 'YY.MM.DD hh:mm'",default="YYYY.MM.DD.hh.mm")

    args = parser.parse_args()
    
    # Determine Time Range & Get args.fileObsData if supplied
    import datetime
    import numpy as np
    if args.fileObsData is not None:
        try:
            with open(args.fileObsData) as fileObsData:
                obsDataList = fileObsData.readlines()
        except Exception as e:
            print( '%s does not seem to exist or is not readable'%(fileObsData) )
            print( e )
            exit(os.EX_NOINPUT)
            pass
        
        array_time = np.zeros(len(obsDataList)-1)
        array_obsData = np.zeros(len(obsDataList)-1)

        startingTime = None
        endingTime = None
        for idx,line in enumerate(obsDataList):
            if line[0] == "#": # allow for comments
                continue
            
            # Split the line
            line = line.strip('\n') # remove trailing new line characters
            dataEntry = line.rsplit(args.delimiter) # gives a list of strings
            
            # Handle column header
            if idx == 0:
                obsName = dataEntry[1] # in B-field example this will read "BField ( T )"
                if obsName.find("(") > -1:
                    obsNameNoSpecials = getStringNoSpecials( obsName[0:obsName.find("(")] )
                else:
                    obsNameNoSpecials = getStringNoSpecials( obsName )
                obsNameNoSpecials = obsNameNoSpecials.replace(' ','')
                continue # move to next line
              
            # Get the time
            thisTime = getDateFromStr(dataEntry[0],"YYYY.MM.DD hh:mm:ss")

            if startingTime is None:
                startingTime = thisTime
            else:
                array_time[idx-1] = (thisTime - startingTime).total_seconds()
                pass

            if args.debug:
                print(line,dataEntry[0],dataEntry[1])

            # Get the observable
            try:
                array_obsData[idx-1] = float(dataEntry[1])
            except ValueError:
                print("\033[91mSkipping line; unabled to convert to float:\033[0m")
                print(line,dataEntry[0],dataEntry[1])
                continue

            pass
    else:
        startingTime = getDateFromStr(args.startDate,args.startDateFormat)
        endingTime = getDateFromStr(args.endDate,args.endDateFormat)

        array_time = np.zeros(2)
        array_time[0] = 0 
        array_time[1] = (endingTime - startingTime).total_seconds()
    
    import ROOT as r
    rootOffsetTime = r.TDatime(
            startingTime.year, 
            startingTime.month, 
            startingTime.day, 
            startingTime.hour, 
            startingTime.minute, 
            startingTime.second)
    
    # Open input file
    with open(args.fileChanLoss, 'r') as fileList:
        listOfChanLost = fileList.readlines()
        pass
    listOfChanLost = [ line.strip('\n') for line in listOfChanLost ]
    
    # Loop Over Inputs
    dict_chanLoss = {}
    leg = r.TLegend(0.7,0.5,0.9,0.9)
    maxChanLoss = -1
    for idx,line in enumerate(listOfChanLost):
        if line[0] == "#": # allow for comments
            continue
        
        # Split the line
        line = line.strip('\n') # remove trailing new line characters
        dataEntry = line.rsplit(args.delimiter) # gives a list of strings
        
        # Handle column header
        if idx == 0:
            continue # move to next line

        # Chamber name
        cName = dataEntry[0]
        if args.cummulative:
            cName+="_cum"
        if args.percentage:
            cName+="_percent"
            pass

        # Get this plot
        chanLossTuple = getChanLossPlot(args, cName, dataEntry[1], startingTime)
        dict_chanLoss[cName] = chanLossTuple[0]
        if chanLossTuple[1] > maxChanLoss:
            maxChanLoss = chanLossTuple[1]

        # Format the plot holding the data
        dict_chanLoss[cName].GetXaxis().SetTimeDisplay(1)
        dict_chanLoss[cName].GetXaxis().SetTimeOffset(rootOffsetTime.Convert())
        dict_chanLoss[cName].SetMarkerStyle(20+idx)
        dict_chanLoss[cName].SetMarkerSize(1.2)
        dict_chanLoss[cName].SetMarkerColor(getCyclicColor(idx))
        dict_chanLoss[cName].SetLineWidth(2)
        dict_chanLoss[cName].SetLineColor(getCyclicColor(idx))

        leg.AddEntry(dict_chanLoss[cName], dataEntry[0], "LPE")

    # Format Primary Y-axis label
    yAxisLabel = "Channel Loss"
    if args.percentage:
        maxChanLoss = 1.
        yAxisLabel = "Percent {0}".format(yAxisLabel)
    elif args.cummulative:
        yAxisLabel = "Cummulative {0}".format(yAxisLabel)
        pass

    # Format Canvas Label
    if args.fileObsData is not None:
        canvName = "{0}_{1}".format(
                args.fileChanLoss[args.fileChanLoss.rfind("/")+1:args.fileChanLoss.rfind(".")],
                obsNameNoSpecials)
    else:
        canvName = args.fileChanLoss[args.fileChanLoss.rfind("/")+1:args.fileChanLoss.rfind(".")]

    if args.cummulative:
        canvName += "_cum"
    if args.percentage:
        canvName += "_percent"

    # Make a canvas
    canvData = r.TCanvas("canv_chanLoss_{0}".format(canvName),"Channels Lost - {0}".format(canvName),700,700)
    canvData.cd()
   
    # Draw the graph for the primary axis and make it a time axis
    # https://root.cern.ch/root/HowtoTimeAxis.html
    # https://root.cern.ch/root/html602/TDatime.html
    g_timeAxis = r.TGraphErrors(len(array_time), array_time, np.zeros(len(array_time)))
    g_timeAxis.SetTitle("")
    g_timeAxis.GetXaxis().SetTimeDisplay(1)
    g_timeAxis.GetXaxis().SetTimeOffset(rootOffsetTime.Convert())
    g_timeAxis.GetXaxis().SetTimeFormat("%m-%y")
    g_timeAxis.GetYaxis().SetRangeUser(0,maxChanLoss*1.1)
    g_timeAxis.GetYaxis().SetDecimals(True)
    g_timeAxis.GetYaxis().SetTitle(yAxisLabel)

    if args.fileObsData is not None:
        # Draw an empty plot to make a secondary y-axis, use Y+ to have it on the right
        maxObsData = np.asscalar(np.max(array_obsData))
        g_timeAxis2ndPad = g_timeAxis.Clone()
        g_timeAxis2ndPad.GetYaxis().SetRangeUser(0.01,1.1*maxObsData)
        g_timeAxis2ndPad.GetYaxis().SetTitle("")
        g_timeAxis2ndPad.GetXaxis().SetNdivisions(0)
        g_timeAxis2ndPad.Draw("APY+")
    
        # Secondary Y-Axis Label
        yAxisLabel2nd = r.TLatex()
        yAxisLabel2nd.SetTextSize(0.03)
        yAxisLabel2nd.SetTextAngle(90)
        yAxisLabel2nd.DrawLatexNDC(0.98,0.5,obsName)

        # quick google search comes up with: https://root.cern.ch/root/HowtoTimeAxis.html
        g_obsData = r.TGraph(
                len(obsDataList)-1,
                array_time,
                array_obsData)
        g_obsData.GetXaxis().SetTimeDisplay(1)
        g_obsData.GetXaxis().SetTimeOffset(rootOffsetTime.Convert())
        #g_obsData.GetXaxis().SetTitle(obsName)
        g_obsData.SetMarkerStyle(22)
        g_obsData.SetMarkerColor(r.kBlack)
        g_obsData.SetLineWidth(2)
        g_obsData.SetLineColor(r.kBlack)
        #g_obsData.Draw("LP")
        g_obsData.Draw("P")
        leg.AddEntry(g_obsData,obsName,"LPE")
        
        # Make a transparent TPad on top of the primary one
        # https://root.cern.ch/root/roottalk/roottalk01/0983.html
        canvData.cd()
        if args.logy2:
            canvData.cd().SetLogy()

        overlay = r.TPad("overlay","",0,0,1,1)
        overlay.SetFillStyle(4000)
        overlay.SetFillColor(0)
        overlay.SetFrameFillStyle(4000)
        overlay.Draw()
        overlay.cd()
        if args.logy1:
            overlay.cd().SetLogy()
        pass
    else:
        if args.logy1:
            canvData.cd().SetLogy()
 
    # Now draw the channel loss plot
    g_timeAxis.Draw("AP")
    for chamber,plot in dict_chanLoss.iteritems():
        plot.Draw("samePE1")
        pass

    if not args.noLeg:
        leg.Draw("same")
        
    # Store output
    outputFile = r.TFile("out_{0}.root".format(canvName),"RECREATE")
    outputFile.cd()
    for chamber,plot in dict_chanLoss.iteritems():
        plot.Write()
    if args.fileObsData is not None:
        g_obsData.SetName("g_{0}".format(obsNameNoSpecials))
        g_obsData.Write()
        pass
    canvData.Write()

    # Make the plot
    canvData.SaveAs("{0}.png".format( canvData.GetName() ) )
    canvData.SaveAs("{0}.C".format( canvData.GetName() ) )

    # Finished
    print("Done")