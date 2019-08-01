r"""
``anaoptions`` --- Common options for analysis tools
====================================================

.. code-block:: python

    import gempython.gemplotting.utils.anahistory

Documentation
-------------
"""

import argparse
parent_parser = argparse.ArgumentParser(add_help = False)

# Positional arguments
parent_parser.add_argument("infilename",type=str,help="Specify Input Filename by full path")

# Optional arguments
parent_parser.add_argument("-d", "--debug", action="store_true", help="print extra debugging information")
parent_parser.add_argument("-o", "--outfilename", type=str, help="Specify Output Filename")

stripChanOrPinType = parent_parser.add_mutually_exclusive_group(required=False)
stripChanOrPinType.add_argument("-c","--channels", action="store_true", help="Make plots vs channels instead of strips")
stripChanOrPinType.add_argument("-p","--panasonic", action="store_true", dest="PanPin",help="Make plots vs Panasonic pins instead of strips")

parser_scurveChanMasks = argparse.ArgumentParser(add_help = False)	

from anaInfo import maxEffPedPercentDefault,highNoiseCutDefault,deadChanCutLowDefault,deadChanCutHighDefault

chanMaskGroup = parser_scurveChanMasks.add_argument_group(title="Options for channel mask decisions", description="Parameters which specify how Dead, Noisy, and High Pedestal Channels are charaterized")
chanMaskGroup.add_argument("--maxEffPedPercent", type=float, default=maxEffPedPercentDefault, help="Percentage, threshold for setting the HighEffPed mask reason, if channel (effPed > maxEffPedPercent * nevts) then HighEffPed is set")
chanMaskGroup.add_argument("--highNoiseCut", type=float, default=highNoiseCutDefault, help="Threshold in fC for setting the HighNoise maskReason, if channel (scurve_sigma > highNoiseCut) then HighNoise is set")
chanMaskGroup.add_argument("--deadChanCutLow", type=float, default=deadChanCutLowDefault,help="If channel (deadChanCutLow < scurve_sigma < deadChanCutHigh) then DeadChannel is set")
chanMaskGroup.add_argument("--deadChanCutHigh", type=float, default=deadChanCutHighDefault, help="If channel (deadChanCutHigh < scurve_sigma < deadChanCutHigh) then DeadChannel is set")
