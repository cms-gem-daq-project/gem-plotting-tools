r"""
``anaInfo`` --- Analysis information
====================================

.. code-block:: python

    import gempython.gemplotting.utils.anaInfo

Documentation
-------------
"""

import string

#: If the chisquare value of the fit to DAC vs ADC is above this value, an exception will be raised
dacScanFitChisquareMax = 100.

#: CFG_THR_ARM_DAC calibration parameters
#: The CFG_THR_ARM_DAC calibration routine involves performing a fit of scurveMean vs CFG_THR_ARM_DAC in which some points with bad quality, defined by the parameters below, are removed
scurveMeanMin = 0.1 #: points are removed if they satisfy scurveMean < scurveMeanMin
scurveMeanFracErrMin = 0.001 #: points are removed if they satisfy scurveMeanError/scurveMean < scurveFracErrMin
numOfGoodChansMinDefault = 10 #: default value of: minimum number of good channels scurveMean points are required to have

#: The default values for the cuts that determine the scurve fit quality masks
maxEffPedPercentDefault=0.02
highNoiseCutDefault=1.5
deadChanCutLowDefault=0
deadChanCutHighDefault=0

#: Nominal current and voltage values from Tables 9 and 10 of the VFAT3 manual
#: The registers CFG_THR_ARM_DAC CFG_THR_ZCC_DAC may correspond to either a voltage or a current. Below I have used the voltage. Be careful if you have taken a current scan with these registers (dacSelect options 14 or 15).
nominalDacValues = {
        "CFG_CAL_DAC":(0,"uA"), # there is no nominal value
        "CFG_BIAS_PRE_I_BIT":(150,"uA"),
        "CFG_BIAS_PRE_I_BLCC":(25,"nA"),
        "CFG_BIAS_PRE_I_BSF":(26,"uA"),
        "CFG_BIAS_SH_I_BFCAS":(26,"uA"),
        "CFG_BIAS_SH_I_BDIFF":(16,"uA"),
        "CFG_BIAS_SD_I_BDIFF":(28,"uA"),
        "CFG_BIAS_SD_I_BFCAS":(27,"uA"),
        "CFG_BIAS_SD_I_BSF":(30,"uA"),
        "CFG_BIAS_CFD_DAC_1":(20,"uA"),
        "CFG_BIAS_CFD_DAC_2":(20,"uA"),
        "CFG_HYST":(100,"nA"),
        "CFG_THR_ARM_DAC":(64,"mV"),
        "CFG_THR_ZCC_DAC":(5.5,"mV"),
        "CFG_BIAS_PRE_VREF":(430,'mV'),
        "CFG_VREF_ADC":(1.0,'V')
}

#: From Tables 12 and 13 from the VFAT3 manual
nominalDacScalingFactors = {
        "CFG_CAL_DAC":10, # Valid only for currentPulse; if voltageStep this is 1
        "CFG_BIAS_PRE_I_BIT":0.2,
        "CFG_BIAS_PRE_I_BLCC":100,
        "CFG_BIAS_PRE_I_BSF":0.25,
        "CFG_BIAS_SH_I_BFCAS":1,
        "CFG_BIAS_SH_I_BDIFF":1,
        "CFG_BIAS_SD_I_BDIFF":1,
        "CFG_BIAS_SD_I_BFCAS":1,
        "CFG_BIAS_SD_I_BSF":0.25,
        "CFG_BIAS_CFD_DAC_1":1,
        "CFG_BIAS_CFD_DAC_2":1,
        "CFG_HYST":5,
        "CFG_THR_ARM_DAC":1,
        "CFG_THR_ZCC_DAC":4,
        "CFG_BIAS_PRE_VREF":1,
        "CFG_ADC_VREF": 1
}

#: Types of analysis and corresponding analysis tools
ana_config = {
        "armDacCal":"calibrateThrDac.py",
        "dacScanV3":"dacScanV3.py",
        "latency":"anaUltraLatency.py",
        "sbitMonInt":"anaSBitMonitor.py",
        "sbitMonRO":"anaSbitReadout.py",
        "sbitRatech":"anaSBitThresh.py",
        "sbitRateor":"anaSBitThresh.py",
        "scurve":"anaUltraScurve.py",
        "temperature":"monitorTemperatures.py",
        "thresholdch":"anaUltraThreshold.py",
        "thresholdvftrk":"anaUltraThreshold.py",
        "thresholdvftrig":"anaUltraThreshold.py",
        "trim":"anaUltraScurve.py",
        "trimV3":"anaUltraScurve.py",
        "iterTrim":"anaUltraScurve.py"
        }

#: key values match ana_config (mostly...)
#: stores a tuple where:
#:   [0] -> path of root file inside scandate/
#:   [1] -> name of TTree inside root file
tree_names = {
        "armDacCal":("listOfScanDates_calibrateArmDac_{DETECTOR}.txt",None), # here DETECTOR should be the detector serial number, e.g. "GE11-X-S-CERN-0002", this is a text file; hence TTree is "None"
        "armDacCalAna":("calFile_CFG_THR_ARM_DAC_{DETECTOR}.root",None), # here DETECTOR should be the detector serial number, e.g. "GE11-X-S-CERN-0002", there is no TTree presently stored in this TFile hence "None"
        "dacScanV3":("dacScanV3.root","dacScanTree"),
        "latency":("LatencyScanData.root","latTree"),
        "latencyAna":("LatencyScanData/latencyAna.root","latFitTree"),
        #FIXME add sbitMon
        "sbitRatech":("SBitRateData.roo","rateTree"),
        "sbitRateor":("SBitRateData.roo","rateTree"),
        "scurve":("SCurveData.root","scurveTree"),
        "scurveAna":("SCurveData/SCurveFitData.root","scurveFitTree"),
        "threshold":("ThresholdScanData.root","thrTree"),
        "thresholdch":("ThresholdScanData.root","thrTree"),
        "thresholdvftrig":("ThresholdScanData.root","thrTree"),
        "thresholdvftrk":("ThresholdScanData.root","thrTree"),
        "thresholdAna":("ThresholdScanData/ThresholdPlots.root","thrAnaTree"),
        "trim":("SCurveData_Trimmed.root","scurveTree"),
        "trimV3":("SCurveData_{CONDITION}.root","scurveTree"), # here CONDITION should be {Trimmed, or trimdacXX_trimPolY} for XX the trimDac point and Y the trimPol {0,1}
        "trimAna":("SCurveData_Trimmed/SCurveFitData.root","scurveFitTree")
        }

mappingNames = [
        "Strip",
        "PanPin",
        "vfatCH"
        ]

# Names of queues on lxplus
queueNames = [
        "8nm", # 8 natural minutes (natural -> time on wall clock)
        "1nh", # 1 natural hour
        "8nh", # 8 natural hours
        "1nd"  # 1 natural day
        ]

# Cal scale factor (e.g. CFG_CAL_FS)
# Required for determining charge when using 
# Current pulse cal mode of VFAT3
dict_calSF = dict((calSF, 0.25*calSF+0.25) for calSF in range(0,4))

class MaskReason:
    """
    Enum-like class to represent the reasons for which a channel was masked.

    When the analysis software decides a channel should be masked it is because
    it falls under one of the categories listed below. Multiple reasons can be
    assigned to a channel for why it is masked, and the total ``maskReason`` is
    a 5-bit binary number.

    ``maskReason`` is sometimes presented in decimal representation. For
    example, a channel having ``maskReason = 24`` corresponds to ``0b11000``
    which means the channel was assigned the ``HighEffPed`` and ``HighNoise``
    ``maskReason``. The following code performs the conversion for you:

    >>> from gempython.gemplotting.utils.anaInfo import MaskReason
    >>> MaskReason.humanReadable(24)
    'HighNoise,HighEffPed'

    You'll find more detail about channel masking on the :doc:`dedicated page
    </masking>`.
    """

    #: The channel is not masked
    NotMasked   = 0x0

    #: The channel was identified as an outlier using the MAD algorithm, see
    #: talks by `B. Dorney`_ or `L. Moureaux`_.
    #:
    #: .. _`B. Dorney`: https://indico.cern.ch/event/638404/contributions/2643292/attachments/1483873/2302543/BDorney_OpsMtg_20170627.pdf
    #: .. _`L. Moureaux`: https://indico.cern.ch/event/659794/contributions/2691237/attachments/1508531/2351619/UpdateOnHotChannelIdentificationAlgo.pdf
    HotChannel  = 0x01

    #: The s-curve fit of the channel failed.
    FitFailed   = 0x02

    #: The channel has a burned or disconnected input.
    DeadChannel = 0x04

    #: The channel has an scurve sigma above the cut value.
    HighNoise   = 0x08

    #: The channel has an effective pedestal above the cut value.
    HighEffPed  = 0x10

    @staticmethod
    def listReasons():
        """Returns a table of ``(name, mask)`` tuples for all ``MaskReasons``"""
        list = []
        for name, value in MaskReason.__dict__.iteritems():
            if type(value) == int and value != MaskReason.NotMasked:
                list.append((name, value))
        return list

    @staticmethod
    def humanReadable(reason):
        """
        Returns the human-readable string that corresponds to a ``maskReason``.
        """
        names = []
        for name, value in MaskReason.__dict__.iteritems():
            if type(value) == int and reason & value:
                names.append(name)
        if len(names) == 0:
            return 'NotMasked'
        else:
            return string.join(names, ',')
