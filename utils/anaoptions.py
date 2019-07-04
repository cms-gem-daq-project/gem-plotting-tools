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
