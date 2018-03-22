import numpy as np
import ROOT as r

class DeadChannelFinder(object):
    def __init__(self):
        self.isDead = [ np.ones(128, dtype=bool) for i in range(24) ]

    def feed(self, event):
        self.isDead[event.vfatN][event.vfatCH] = False

class ScanDataFitter(DeadChannelFinder):
    def __init__(self):
        super(ScanDataFitter, self).__init__()

        from gempython.utils.nesteddict import nesteddict as ndict
        r.gStyle.SetOptStat(0)

        self.Nev = ndict()
        self.scanFuncs  = ndict()
        self.scanHistos = ndict()
        self.scanCount  = ndict()
        self.scanFits   = ndict()

        for vfat in range(0,24):
            self.scanFits[0][vfat] = np.zeros(128)
            self.scanFits[1][vfat] = np.zeros(128)
            self.scanFits[2][vfat] = np.zeros(128)
            self.scanFits[3][vfat] = np.zeros(128)
            self.scanFits[4][vfat] = np.zeros(128)
            self.scanFits[5][vfat] = np.zeros(128)
            self.scanFits[6][vfat] = np.zeros(128, dtype=bool)
            for ch in range(0,128):
                self.scanFuncs[vfat][ch] = r.TF1('scurveFit_vfat%i_chan%i'%(vfat,ch),'[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',1,253)
                self.scanHistos[vfat][ch] = r.TH1D('scurve_vfat%i_chan%i_h'%(vfat,ch),'scurve_vfat%i_chan%i_h'%(vfat,ch),254,0.5,254.5)
                self.scanCount[vfat][ch] = 0

        self.fitValid = [ np.zeros(128, dtype=bool) for vfat in range(24) ]

    def feed(self, event):
        super(ScanDataFitter, self).feed(event)
        self.scanHistos[event.vfatN][event.vfatCH].Fill(event.vcal,event.Nhits)
        if(event.vcal > 250):
            self.scanCount[event.vfatN][event.vfatCH] += event.Nhits
        self.Nev[event.vfatN][event.vfatCH] = event.Nev

    def feedHisto(self, vfatN, vfatCH, histo, nEvts=None):
        self.scanHistos[vfatN][vfatCH] = histo
        self.isDead[vfatN][vfatCH] = False
        if nEvts is None:
            maxBin = self.scanHistos[vfatN][vfatCH].GetMaximumBin()
            self.Nev[vfatN][vfatCH] = self.scanHistos[vfatN][vfatCH].GetBinContent(maxBin)
        else:
            self.Nev[vfatN][vfatCH] = nEvts

    def fit(self):
        r.gROOT.SetBatch(True)
        r.gStyle.SetOptStat(0)

        random = r.TRandom3()
        random.SetSeed(0)
        fitTF1 = r.TF1('myERF','[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',1,253)
        for vfat in range(0,24):
            print 'fitting vfat %i'%vfat
            for ch in range(0,128):
                if self.isDead[vfat][ch]:
                    continue # Don't try to fit dead channels
                elif not (self.scanHistos[vfat][ch].Integral() > 0):
                    continue # Don't try to fit with 0 entries
                fitChi2 = 0
                MinChi2Temp = 99999999
                stepN = 0
                while(stepN < 15):
                    rand = random.Gaus(10, 5)
                    if (rand < 0.0 or rand > 100): continue
                    # Provide an initial guess
                    fitTF1.SetParameter(0, 8+stepN*8)
                    fitTF1.SetParameter(1,rand)
                    fitTF1.SetParameter(2,8+stepN*8)
                    fitTF1.SetParameter(3, self.Nev[vfat][ch]/2.)

                    # Set Parameter Limits
                    fitTF1.SetParLimits(0, 0.01, 300.0)
                    fitTF1.SetParLimits(1, 0.0, 100.0)
                    fitTF1.SetParLimits(2, 0.0, 300.0)
                    fitTF1.SetParLimits(3, 0.0, self.Nev[vfat][ch] * 2.)

                    # Fit
                    fitResult = self.scanHistos[vfat][ch].Fit('myERF','SQ')
                    fitEmpty = fitResult.IsEmpty()
                    if fitEmpty:
                        # Don't try to fit empty data again
                        break
                    fitValid = fitResult.IsValid()
                    if not fitValid:
                        continue
                    fitChi2 = fitTF1.GetChisquare()
                    fitNDF = fitTF1.GetNDF()
                    stepN +=1
                    if (fitChi2 < MinChi2Temp and fitChi2 > 0.0):
                        self.scanFuncs[vfat][ch] = fitTF1.Clone('scurveFit_vfat%i_chan%i_h'%(vfat,ch))
                        self.scanFits[0][vfat][ch] = fitTF1.GetParameter(0)
                        self.scanFits[1][vfat][ch] = fitTF1.GetParameter(1)
                        self.scanFits[2][vfat][ch] = fitTF1.GetParameter(2)
                        self.scanFits[3][vfat][ch] = fitChi2
                        self.scanFits[4][vfat][ch] = self.scanCount[vfat][ch]
                        self.scanFits[5][vfat][ch] = fitNDF
                        self.fitValid[vfat][ch] = True
                        MinChi2Temp = fitChi2
                        pass
                    if (MinChi2Temp < 50): break
                    pass
                pass
            pass
        return self.scanFits
    
    def getFunc(self, vfat, ch):
        return self.scanFuncs[vfat][ch]

    def readFile(self, treeFileName):
        inF = r.TFile(treeFileName)
        for event in inF.scurveTree :
            self.feed(event)

def fitScanData(treeFileName):
    fitter = ScanDataFitter()
    fitter.readFile(treeFileName)
    return fitter.fit()
