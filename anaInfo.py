import string

ana_config = {
        "latency":"anaUltraLatency.py",
        "scurve":"anaUltraScurve.py",
        "threshold":"anaUltraThreshold.py",
        "trim":"anaUltraScurve.py"
        }

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
