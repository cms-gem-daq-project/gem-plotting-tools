#def overlay_fit(VFAT, CH, data_filename, fit_filename):
def overlay_fit(VFAT, CH, fit_filename):
    import ROOT as r

    #rawFile     = r.TFile(data_filename)
    fitFile   = r.TFile(fit_filename)
    scurveHisto = r.TH1D()

    #for event in rawFile.scurveTree:
    #    if (event.vfatN == VFAT) and (event.vfatCH == CH):
    #        scurveHisto.Fill(event.vcal, event.Nhits)
    #        pass
    #    pass
    for event in fitFile.scurveFitTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            scurveHisto = event.scurve_h.Clone()
            param0 = event.threshold
            param1 = event.noise
            param2 = event.pedestal
            pass
        pass
    #fitTF1 =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    #fitTF1.SetParameter(0, param0)
    #fitTF1.SetParameter(1, param1)
    #fitTF1.SetParameter(2, param2)
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    scurveHisto.Draw()
    #fitTF1.Draw('SAME')
    #canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Channel%i.png'%(VFAT, CH))
    #Chi2 = fitTF1.GetChisquare()
    #print Chi2
    return
