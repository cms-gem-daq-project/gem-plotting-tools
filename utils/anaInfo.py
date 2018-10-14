r"""
``anaInfo`` --- Analysis information
====================================

.. code-block:: python

    import gempython.gemplotting.utils.anahistory

Documentation
-------------
"""

import string

#: Nominal current and voltage values from Tables 9 and 10 of the VFAT3 manual
nominalDacValues = {
        "CFG_IREF":(10,"uA"),
        "CFG_BIAS_PRE_I_BIT":(150,"uA"),
        "CFG_BIAS_PRE_I_BLCC":(25,"nA"),
        "CFG_BIAS_SH_I_BFCAS":(26,"uA"),
        "CFG_BIAS_SH_I_BDIFF":(16,"uA"),
        "CFG_BIAS_SD_I_BDIFF":(28,"uA"),
        "CFG_BIAS_SD_I_BFCAS":(27,"uA"),
        "CFG_BIAS_SD_I_BSF":(30,"uA"),
        "CFG_BIAS_CFD_DAC_1":(20,"uA"),
        "CFG_BIAS_CFD_DAC_2":(20,"uA"),
        "CFG_HYST":(100,"nA"),
        "CFG_THR_ARM_DAC":(3.2,"uA"),
        "CFG_THR_ZCC_DAC":(275,"nA"),
        "CFG_BIAS_PRE_VREF":(430,'mV'),
        "CFG_ADC_VREF":(400,'mV')
}

#: Types of analysis and corresponding analysis tools
ana_config = {
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
        "trimV3":"anaUltraScurve.py"
        }

#: key values match ana_config (mostly...)
#: stores a tuple where:
#:   [0] -> path of root file inside scandate/
#:   [1] -> name of TTree inside root file
tree_names = {
        "latency":("LatencyScanData.root","latTree"),
        "latencyAna":("LatencyScanData/latencyAna.root","latFitTree"),
        "scurve":("SCurveData.root","scurveTree"),
        "scurveAna":("SCurveData/SCurveFitData.root","scurveFitTree"),
        "threshold":("ThresholdScanData.root","thrTree"),
        "thresholdch":("ThresholdScanData.root","thrTree"),
        "thresholdvftrig":("ThresholdScanData.root","thrTree"),
        "thresholdvftrk":("ThresholdScanData.root","thrTree"),
        "thresholdAna":("ThresholdScanData/ThresholdPlots.root","thrAnaTree"),
        "trim":("SCurveData_Trimmed.root","scurveTree"),
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
