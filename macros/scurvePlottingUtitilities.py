def overlay_scurve(vfat, vfatCH, fit_filename=None, tupleTObjects=None, vfatChNotROBstr=True, debug=False):
    """
    Draws an scurve histogram and the fit to the scurve on a common canvas
    and saves the canvas as a png file.  If fit_filename is supplied it 
    will return a tuple of (histo, fit) otherwise nothing will be returned

    vfat - vfat number
    vfatCH - vfat channel number
    fit_filename - TFile that holds the scurve fit data (histo & fit)
    tupleTObjects - tuple of TObjects (TH1F, TF1) first element is histo, second histo's fit
    vfatChNotROBstr - true if plotted for vfatCh; false if plotted for readout strip
    """
    
    import os
    import ROOT as r
    
    strCanvasName = 'canv_SCurveFitOverlay_VFAT%i_Chan%i'%(vfat, vfatCH)
    strCanvasTitle = 'SCurve and Fit for VFAT %i Chan %i'%(vfat,vfatCH)
    if not vfatChNotROBstr:
        strCanvasName = 'canv_SCurveFitOverlay_VFAT%i_Strip%i'%(vfat, vfatCH)
        strCanvasTitle = 'SCurve and Fit for VFAT %i Strip %i'%(vfat,vfatCH)

    canvas = r.TCanvas(strCanvasName, strCanvasTitle, 500, 500)
    scurveHisto = r.TH1D()
    scurveFit = r.TF1()

    if fit_filename is not None:
        r.TH1.AddDirectory(False)
        fitFile   = r.TFile(fit_filename)
        for event in fitFile.scurveFitTree:
            if (event.vfatN == vfat) and ((event.vfatCH == vfatCH and vfatChNotROBstr) or (event.ROBstr == vfatCH and not vfatChNotROBstr)):
                scurveHisto = event.scurve_h.Clone()
                scurveFit = event.scurve_fit.Clone()
                pass
            pass
    elif tupleTObjects is not None:
        scurveHisto = tupleTObjects[0]
        scurveFit = tupleTObjects[1]
    else:
        print("overlay_scurve(): Both fit_filename or tupleTObjects cannot be None")
        print("\tYou must supply at least one of them")
        print("\tExiting")
        exit(os.EX_USAGE)
   
    canvas.cd()
    scurveHisto.Draw()
    scurveFit.Draw("same")
    canvas.SaveAs("%s.png"%(canvas.GetName()))

    if debug:
        print scurveFit.GetParameter(0)
        print scurveFit.GetParameter(1)
        print scurveFit.GetParameter(2)
        print scurveFit.GetParameter(3)
        print scurveFit.GetChisquare()
        print scurveFit.GetNDF()
    
    if fit_filename is not None:
        return (scurveHisto, scurveFit)
    else:
        return

def plot_noise_vs_trimDAC(vfat, vfatCH, fit_filename, vfatChNotROBstr=True):
    """
    Plots scurve width (noise) vs trimDAC for a given (vfat,vfatCH)

    vfat - vfat number
    vfatCH - vfat channel number
    fit_filename - TFile that holds the scurve fit data (histo & fit)
    vfatChNotROBstr - true if plotted for vfatCh; false if plotted for readout strip
    """
    import ROOT as r

    fitF = r.TFile(fit_filename)
    if vfatChNotROBstr:
        vNoise = r.TH2D('vNoise', 'Noise vs trimDAC for VFAT %i Channel %i; trimDAC [DAC units]; Noise [DAC units]'%(vfat, vfatCH), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    else:
        vNoise = r.TH2D('vNoise', 'Noise vs trimDAC for VFAT %i Strip %i; trimDAC [DAC units]; Noise [DAC units]'%(vfat, vfatCH), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    vNoise.GetYaxis().SetTitleOffset(1.5)
    for event in fitF.scurveFitTree:
        if (event.vfatN == vfat) and ((event.vfatCH == vfatCH and vfatChNotROBstr) or (event.ROBstr == vfatCH and not vfatChNotROBstr)):
            vNoise.Fill(event.trimDAC, event.noise)
            pass
        pass
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(0)
    vNoise.Draw('colz')
    canvas.Update()
    if vfatChNotROBstr:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Channel_%i.png'%(vfat, vfatCH))
        pass
    else:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Strip_%i.png'%(vfat, vfatCH))
        pass
    return

def plot_vfat_summary(vfat, fit_filename, vfatChNotROBstr=True):
    """
    Plots all scurves for a given vfat

    vfat - vfat number
    fit_filename - TFile that holds the scurve fit data (histo & fit)
    vfatChNotROBstr - true if plotted for vfatCh; false if plotted for readout strip
    """
    import ROOT as r
    fitF = r.TFile(fit_filename)
    Scurve = r.TH1D()
    if vfatChNotROBstr:
        vSum = r.TH2D('vSum', 'vSum for VFAT %i; Channels; VCal [DAC units]'%vfat, 128, -0.5, 127.5, 256, -0.5, 255.5)
        pass
    else:
        vSum = Tr.H2D('vSum', 'vSum for VFAT %i; Strips; VCal [DAC units]'%vfat, 128, -0.5, 127.5, 256, -0.5, 255.5)
        pass
    vSum.GetYaxis().SetTitleOffset(1.5)
    for event in fitF.scurveFitTree:
        if (event.vfatN == vfat):
            Scurve = ((event.scurve_h).Clone())
            for valX in range(0, 256):
                valY = Scurve.FindBin(valX)
                if vfatChNotROBstr:
                    vSum.Fill(event.vfatCH, valX, Scurve.GetBinContent(valY))
                    pass
                else:
                    vSum.Fill(event.ROBstr, valX, Scurve.GetBinContent(valY))
                    pass
                pass
            pass
        pass
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(0)
    vSum.Draw('colz')
    canvas.Update()
    canvas.SaveAs('Summary_VFAT_%i.png'%vfat)
    return

