r"""
``fitScanData`` --- S-curve fitting tools
=========================================

.. code-block:: python

    import gempython.gemplotting.fitting.fitScanData

Documentation
-------------
"""

import numpy as np
import ROOT as r
from gempython.gemplotting.utils.anaInfo import dict_calSF

class DeadChannelFinder(object):
    r"""
    Finds channels that returned no data during an S-curve scan ("dead"
    channels).

    This class has only one function, :py:meth:`feed`, that takes an entry from
    the S-curve tree and updates the results.

    Example:
        Typical usage:

        .. code-block:: python

            finder = DeadChannelFinder()
            for event in file.scurveTree:
                finder.feed(event)
                pass
            # Use the results...

    Attributes:
        isDead (numpy.ndarray): 2D array of ``bool``, indexed as
            ``[vfat][channel]``. Each entry is ``True`` if the channel is
            dead, ``False`` otherwise.
    """
    def __init__(self, nVFats=24):
        self.isDead = [ np.ones(128, dtype=bool) for i in range(nVFats) ]

    def feed(self, event):
        """
        Takes an entry from the S-curve tree and updates the results
        accordingly.
        """
        self.isDead[event.vfatN][event.vfatCH] = False

class ScanDataFitter(DeadChannelFinder):
    r"""
    Fits S-curves.

    This class is used in two steps:

    #. The data to fit is passed to the object using :py:meth:`feedHisto`,
       :py:meth:`readFile` or repeated calls to :py:meth:`feed`.
    #. The fit is performed by calling :py:meth:`fit`.

    One cannot count on all attributes being present before calling
    :py:meth:`fit`.

    .. note::

        If the :py:attr:`calDAC2Q_m` and :py:attr:`calDAC2Q_b` were supplied at
        construction time, values will be in charge units instead of DAC units.

    See :program:`anaUltraScurve.py` for example usage.

    Attributes:
        Nev (ndict): 2D array of ``int``, indexed as ``[vfat][channel]``.

        scanFuncs (ndict): 2D array of ``TF1``, indexed as ``[vfat][channel]``.
            After fitting, each entry contains the fit function for the
            corresponding channel. The functions are color-coded:

            ======= =====================================
            Color   Meaning
            ======= =====================================
            Black   Default
            Blue    Fit Converged
            Gray    Dead channel or empty input histogram
            Orange  Fit result is empty
            ======= =====================================

        scanHistos (ndict): 2D array of ``TH1``, indexed as
            ``[vfat][channel]``, that contain the S-curve results (number of
            events vs charge)

        scanCount (ndict): 2D array of ``int``, indexed as ``[vfat][channel]``.
            Each entry contains the total number of events for the corresponding
            channel.

        scanFitResults (ndict): 3D array of ``float``, indexed as
            ``[idx][vfat][channel]``, that contain the fit results. ``idx`` has
            the following meaning:

            0. S-curve mean in either DAC units or charge (threshold of
               comparator)
            1. S-curve width in either DAC units or charge (noise seen by
               comparator)
            2. S-curve pedestal in hits (e.g. at 0 VCAL this is the
               noise)
            3. :math:`\chi^2` of the fit
            4. Same as ``self.scanCount[vfat][channel]``
            5. Number of degrees of freedom (NDF) of the fit
            6. Value of ROOT::Fit::FitResult::IsValid()

        calDAC2Q_m (numpy.ndarray): Calibration of ``calDAC`` to charge for each
            VFAT. This corresponds to :math:`m` in

            .. math::

                Q = m * \mathtt{calDAC} + b

            If no value was given at construction time, this is an arrays of
            ones.

        calDAC2Q_b (numpy.ndarray): Calibration of ``calDAC`` to charge for each
            VFAT. This corresponds to :math:`b` in

            .. math::

                Q = m * \mathtt{calDAC} + b

            If no value was given at construction time, this is an arrays of
            zeros.

        isVFAT3 (bool): Whether the detector under consideration uses VFAT3
    """

    def __init__(self, calDAC2Q_m=None, calDAC2Q_b=None, isVFAT3=False, nVFats=24):
        super(ScanDataFitter, self).__init__(nVFats)

        from gempython.utils.nesteddict import nesteddict as ndict
        from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
        r.gStyle.SetOptStat(0)

        self.Nev = ndict()
        self.scanFuncs  = ndict()
        self.scanHistos = ndict()
        self.scanHistosChargeBins = ndict()
        self.scanCount  = ndict()
        self.scanFitResults   = ndict()

        self.isVFAT3    = isVFAT3
        self.nVFats     = nVFats
        
        self.calDAC2Q_m = np.ones(self.nVFats)
        if calDAC2Q_m is not None:
            self.calDAC2Q_m = calDAC2Q_m

        self.calDAC2Q_b = np.zeros(self.nVFats)
        if calDAC2Q_b is not None:
            self.calDAC2Q_b = calDAC2Q_b

        for vfat in range(0,self.nVFats):
            self.scanFitResults[0][vfat] = np.zeros(maxChans)
            self.scanFitResults[1][vfat] = np.zeros(maxChans)
            self.scanFitResults[2][vfat] = np.zeros(maxChans)
            self.scanFitResults[3][vfat] = np.zeros(maxChans)
            self.scanFitResults[4][vfat] = np.zeros(maxChans)
            self.scanFitResults[5][vfat] = np.zeros(maxChans)
            self.scanFitResults[6][vfat] = np.zeros(maxChans, dtype=bool)
            for ch in range(0,maxChans):
                self.scanCount[vfat][ch] = 0
                if self.isVFAT3:
                    self.scanFuncs[vfat][ch] = r.TF1('scurveFit_vfat{0}_chan{1}'.format(vfat,ch),'[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',
                            self.calDAC2Q_m[vfat]*253+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*1+self.calDAC2Q_b[vfat])
                    self.scanHistos[vfat][ch] = r.TH1D('scurve_vfat{0}_chan{1}_h'.format(vfat,ch),'scurve_vfat{0}_chan{1}_h'.format(vfat,ch),
                            254,self.calDAC2Q_m[vfat]*254.5+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*0.5+self.calDAC2Q_b[vfat])
                else:
                    self.scanFuncs[vfat][ch] = r.TF1('scurveFit_vfat{0}_chan{1}'.format(vfat,ch),'[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',
                            self.calDAC2Q_m[vfat]*1+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*253+self.calDAC2Q_b[vfat])
                    self.scanHistos[vfat][ch] = r.TH1D('scurve_vfat{0}_chan{1}_h'.format(vfat,ch),'scurve_vfat{0}_chan{1}_h'.format(vfat,ch),
                            254,self.calDAC2Q_m[vfat]*0.5+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*254.5+self.calDAC2Q_b[vfat])
                    pass
                self.scanHistosChargeBins[vfat][ch] = [self.scanHistos[vfat][ch].GetXaxis().GetBinLowEdge(binX) for binX in range(1,self.scanHistos[vfat][ch].GetNbinsX()+2) ] #Include overflow
                pass
            pass

        self.fitValid = [ np.zeros(maxChans, dtype=bool) for vfat in range(self.nVFats) ]

        return

    def feed(self, event):
        # Docs inherited from parent class
        super(ScanDataFitter, self).feed(event)

        charge = self.calDAC2Q_m[event.vfatN]*event.vcal+self.calDAC2Q_b[event.vfatN]
        if self.isVFAT3: #v3 electronics
            if event.isCurrentPulse:
                #Q = CAL_DUR * CAL_DAC * 10nA * CAL_FS
                charge = (1./ 40079000) * event.vcal * (10 * 1e-9) * dict_calSF[event.calSF] * 1e15
                if(event.vcal > 254):
                    self.scanCount[event.vfatN][event.vfatCH] += event.Nhits
            else:
                charge = self.calDAC2Q_m[event.vfatN]*(event.vcal)+self.calDAC2Q_b[event.vfatN]
                if((256-event.vcal) > 254):
                    self.scanCount[event.vfatN][event.vfatCH] += event.Nhits
        else:
            if(event.vcal > 250):
                self.scanCount[event.vfatN][event.vfatCH] += event.Nhits
                pass
            pass

        from gempython.gemplotting.utils.anautilities import first_index_gt
        from math import sqrt
        chargeBin = first_index_gt(self.scanHistosChargeBins[event.vfatN][event.vfatCH], charge)-1
        self.scanHistos[event.vfatN][event.vfatCH].SetBinContent(chargeBin,event.Nhits)
        self.scanHistos[event.vfatN][event.vfatCH].SetBinError(chargeBin,sqrt(event.Nhits))
        self.Nev[event.vfatN][event.vfatCH] = event.Nev

        return

    def feedHisto(self, vfatN, vfatCH, histo, nEvts=None):
        """
        Feed the fitter with data stored in an histogram.

        Args:
            vfatN (int): The VFAT under consideration
            vfatCH (int): The channel under consideration
            histo (int): The data for the channel under consideration
            nEvts (int): Override :py:attr`Nev` for the channel under
                consideration (else the maximum value in the histogram is used)
        """
        self.scanHistos[vfatN][vfatCH] = histo
        self.isDead[vfatN][vfatCH] = False
        if nEvts is None:
            maxBin = self.scanHistos[vfatN][vfatCH].GetMaximumBin()
            self.Nev[vfatN][vfatCH] = self.scanHistos[vfatN][vfatCH].GetBinContent(maxBin)
        else:
            self.Nev[vfatN][vfatCH] = nEvts

        return

    def fit(self, debug=False):
        """
        Iteratively fits all scurves, and populates the relevant class
        attributes.

        Returns: The filled :py:attr:`scanFitResults`
        """

        r.gROOT.SetBatch(True)
        r.gStyle.SetOptStat(0)
        from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
    
        random = r.TRandom3()
        random.SetSeed(0)
        for vfat in range(0,self.nVFats):
            if self.isVFAT3:
                fitTF1 = r.TF1('myERF','[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',
                            self.calDAC2Q_m[vfat]*253+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*1+self.calDAC2Q_b[vfat])
            else:
                fitTF1 = r.TF1('myERF','[3]*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+[3]',
                            self.calDAC2Q_m[vfat]*1+self.calDAC2Q_b[vfat],self.calDAC2Q_m[vfat]*253+self.calDAC2Q_b[vfat])
            fitTF1.SetLineColor(r.kBlack)
            
            if not debug:
                print('fitting vfat {0}'.format(vfat))

            for ch in range(0,maxChans):
                if debug:
                    print('fitting vfat {0} chan {1}'.format(vfat,ch))
                
                if self.isDead[vfat][ch]:
                    fitTF1.SetLineColor(r.kGray)
                    continue # Don't try to fit dead channels
                elif not (self.scanHistos[vfat][ch].Integral() > 0):
                    fitTF1.SetLineColor(r.kGray)
                    continue # Don't try to fit with 0 entries
                
                fitChi2 = 0
                MinChi2Temp = 99999999
                stepN = 0
                
                if debug:
                    print("| stepN | vfatN | vfatCH | isVFAT3 | p0_low | p0 | p0_high | p1_low | p1 | p1_high | p2_low | p2 | p2_high |")
                    print("| ----- | ----- | ------ | ------- | ------ | -- | ------- | ------ | -- | ------- | ------ | -- | ------- |")
                while(stepN < 30):
                    #rand = max(0.0, random.Gaus(10, 5)) # do not accept negative numbers
                    rand = abs(random.Gaus(10, 5)) # take positive definite numbers

                    # Make sure the input parameters are positive
                    if rand > 100: continue
                    if (self.calDAC2Q_m[vfat]*(8+stepN*8)+self.calDAC2Q_b[vfat]) < 0:
                        stepN +=1
                        continue
                    #if (self.calDAC2Q_m[vfat]*(rand)+self.calDAC2Q_b[vfat]) < 0: continue

                    # Provide an initial guess
                    init_guess_p0 = self.calDAC2Q_m[vfat]*(8+stepN*8)+self.calDAC2Q_b[vfat] 
                    init_guess_p1 = abs(self.calDAC2Q_m[vfat]*rand) #self.calDAC2Q_m[vfat] might be negative (e.g. VFAT3 case)
                    init_guess_p2 = 0.
                    init_guess_p3 = self.Nev[vfat][ch]/2.

                    fitTF1.SetParameter(0, init_guess_p0)
                    fitTF1.SetParameter(1, init_guess_p1)
                    fitTF1.SetParameter(2, init_guess_p2)
                    fitTF1.SetParameter(3, init_guess_p3)

                    # Set Parameter Limits
                    if self.isVFAT3:
                        fitTF1.SetParLimits(0, self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat], self.calDAC2Q_m[vfat]*(1)+self.calDAC2Q_b[vfat])
                        fitTF1.SetParLimits(1, 0.0, self.calDAC2Q_m[vfat]*(128)+self.calDAC2Q_b[vfat])
                        fitTF1.SetParLimits(2, -0.01, self.calDAC2Q_m[vfat]*(1)+self.calDAC2Q_b[vfat])
                    else:
                        fitTF1.SetParLimits(0, -0.01, self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat])
                        fitTF1.SetParLimits(1, 0.0,  self.calDAC2Q_m[vfat]*(128)+self.calDAC2Q_b[vfat])
                        fitTF1.SetParLimits(2, -0.01, self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat])
                        pass

                    fitTF1.SetParLimits(3, 0.75*init_guess_p3, 1.25*init_guess_p3)
                    
                    if debug:
                        if self.isVFAT3:
                            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} | {10} | {11} | {12} |".format(
                                        stepN,
                                        vfat,
                                        ch,
                                        self.isVFAT3,
                                        self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat],
                                        init_guess_p0,
                                        self.calDAC2Q_m[vfat]*(1)+self.calDAC2Q_b[vfat],
                                        self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat],
                                        init_guess_p1,
                                        self.calDAC2Q_m[vfat]*(128)+self.calDAC2Q_b[vfat],
                                        -0.01,
                                        init_guess_p2,
                                        self.Nev[vfat][ch]
                                    ))
                        else:
                            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} | {10} | {11} | {12} |".format(
                                        stepN,
                                        vfat,
                                        ch,
                                        self.isVFAT3,
                                        -0.01,
                                        init_guess_p0,
                                        self.calDAC2Q_m[vfat]*(256)+self.calDAC2Q_b[vfat],
                                        0.0,
                                        init_guess_p1,
                                        self.calDAC2Q_m[vfat]*(128)+self.calDAC2Q_b[vfat],
                                        -0.01,
                                        init_guess_p2,
                                        self.Nev[vfat][ch]
                                    ))
                    # Fit
                    fitResult = self.scanHistos[vfat][ch].Fit('myERF','SQ')
                    fitEmpty = fitResult.IsEmpty()
                    if fitEmpty:
                        fitTF1.SetLineColor(kOrange-2)
                        # Don't try to fit empty data again
                        break
                    fitValid = fitResult.IsValid()
                    if not fitValid:
                        continue
                    fitChi2 = fitTF1.GetChisquare()
                    fitNDF = fitTF1.GetNDF()
                    stepN +=1
                    if (fitChi2 < MinChi2Temp and fitChi2 > 0.0):
                        self.scanFuncs[vfat][ch] = fitTF1.Clone('scurveFit_vfat{0}_chan{1}_h'.format(vfat,ch))
                        self.scanFuncs[vfat][ch].SetLineColor(r.kBlue-2)
                        self.scanFitResults[0][vfat][ch] = fitTF1.GetParameter(0)
                        self.scanFitResults[1][vfat][ch] = fitTF1.GetParameter(1)
                        self.scanFitResults[2][vfat][ch] = fitTF1.GetParameter(2)
                        self.scanFitResults[3][vfat][ch] = fitChi2
                        self.scanFitResults[4][vfat][ch] = self.scanCount[vfat][ch]
                        self.scanFitResults[5][vfat][ch] = fitNDF
                        self.scanFitResults[6][vfat][ch] = fitValid
                        self.fitValid[vfat][ch] = True
                        MinChi2Temp = fitChi2
                        pass
                    if (MinChi2Temp < 50): break
                    pass
                if debug:
                    print("Converged fit results:")
                    print("| stepN | vfatN | vfatCH | isVFAT3 | p0 | p1 | p2 | Chi2 | NDF | NormChi2 |")
                    print("| :---: | :---: | :----: | :-----: | :-: | :-: | :-: | :--: | :-: | :------: |")
                    print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} |".format(
                            stepN,
                            vfat,
                            ch,
                            self.isVFAT3,
                            self.scanFitResults[0][vfat][ch],
                            self.scanFitResults[1][vfat][ch],
                            self.scanFitResults[2][vfat][ch],
                            self.scanFitResults[3][vfat][ch],
                            self.scanFitResults[5][vfat][ch],
                            self.scanFitResults[3][vfat][ch] / self.scanFitResults[5][vfat][ch]))
                    pass
                pass
            pass
        return self.scanFitResults
    
    def getFunc(self, vfat, ch):
        """Returns the fit function for the given VFAT and channel"""
        return self.scanFuncs[vfat][ch]

    def readFile(self, treeFileName):
        """
        Reads data from an ``scurveData.root`` file produced by
        ``ultraScurve.py``.
        """
        inF = r.TFile(treeFileName)
        for event in inF.scurveTree :
            self.feed(event)
        return

def fitScanData(treeFileName, isVFAT3=False, calFileName=None, calTuple=None, gemType="ge11"):
    """
    Helper function to fit scan data. Creates a :py:class:`ScanDataFitter`,
    loads the data and returns the results of :py:meth:`ScanDataFitter.fit`.

    Args:
        treeFileName (string): Path to the ``TFile`` that contains the scan data
        isVFAT3 (bool): Whether the detector uses VFAT3
        calFileName (string): Path to the file that contains calibration data
        calTuple (tuple): Tuple of numpy arrays providing CAL_DAC calibration, idx = 0 (1) for slope (intercept); indexed by VFAT position

    .. seealso::

        :py:func:`gempython.gemplotting.utils.anautilities.parseCalFile` for the
        format of the calibration file.
    """
    from gempython.gemplotting.utils.anautilities import parseCalFile
    from gempython.tools.hw_constants import vfatsPerGemVariant

    nVFATS = vfatsPerGemVariant[gemType]
    # Get the fitter
    if calFileName is not None:
        tuple_calInfo = parseCalFile(calFileName, gemType)
        fitter = ScanDataFitter(
                calDAC2Q_m = tuple_calInfo[0],
                calDAC2Q_b = tuple_calInfo[1],
                isVFAT3=isVFAT3,
                nVFATS=nVFATS
                )
    elif calTuple is not None:
        fitter = ScanDataFitter(
                calDAC2Q_m = calTuple[0],
                calDAC2Q_b = calTuple[1],
                isVFAT3=isVFAT3,
                nVFATS=nVFATS
                )
    else:
        fitter = ScanDataFitter(isVFAT3=isVFAT3, nVFATS=nVFATS)
        pass

    # Read the output data
    fitter.readFile(treeFileName)

    # Fit
    return fitter.fit()
