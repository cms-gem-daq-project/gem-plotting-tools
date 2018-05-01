import string

ana_config = {
        "latency":"anaUltraLatency.py",
        "scurve":"anaUltraScurve.py",
        "thresholdch":"anaUltraThreshold.py",
        "thresholdvftrk":"anaUltraThreshold.py",
        "thresholdvftrig":"anaUltraThreshold.py",
        "trim":"anaUltraScurve.py"
        }

# key values match ana_config (mostly...)
# stores a tuple where:
#   [0] -> path of root file inside scandate/ 
#   [1] -> name of TTree inside root file
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
    """Enum-like class to represent the reasons for which a channel was masked.
    Reasons are bitmasks. Example usage:

        reasons = MaskReason.HotChannel | MaskReason.FitFailed
        print MaskReason.humanReadable(reasons)
    """

    NotMasked   = 0x0
    HotChannel  = 0x01
    FitFailed   = 0x02
    DeadChannel = 0x04
    HighNoise   = 0x08
    HighEffPed  = 0x10

    @staticmethod
    def humanReadable(reason):
        """Returns the human-readable string that corresponds to a mask reason"""
        names = []
        for name, value in MaskReason.__dict__.iteritems():
            if type(value) == int and reason & value:
                names.append(name)
        if len(names) == 0:
            return 'NotMasked'
        else:
            return string.join(names, ',')
