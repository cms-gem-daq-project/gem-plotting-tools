#! /usr/bin/env python

r"""
``timeHistoryAnalyzer.py`` --- Analyze the time evolution of channels
=====================================================================

Synopsis
--------

**timeHistoryAnalyzer.py** :token:`-i` <*INPUT DIRECTORY*> [*OPTIONS*]

Description
-----------

:program:`timeHistoryAnalyzer.py` is a tool that finds when a channel turns bad
(see below for the available definitions), and possibly when it is recovered. It
takes as input a set of files produced by :program:`plotTimeSeries.py`, and the
results are printed to the terminal.

The analysis proceeds in three steps, executed in the following order:

1. `Bad scan removal`_: Scans that failed to produce consistent results are
   removed.
2. `Range detection`_: The time evolution of each channel is searched for
   successive scans with consistent "bad" behavior (see below). A set of such
   scans for a given channel is called a (time) range. What kind of behavior is
   searched for is used-defined.
3. `Analysis <#output>`_: The properties of "ranges" are computed and printed.

Bad scan removal
................

Scans that pass any the following cuts are removed:

* The average noise over the entire detector is lower than 0.1 fC (or
  :token:`--minScanAvgNoise`). This cuts scans with no or very few channels
  responding.
* The fraction of masked channels is above 7% (or
  :token:`--maxScanMaskedFrac`). This cuts e.g scans that produced no data and
  for which all fits failed.

Note that the options are named in the positive way, ie they tell which scans to
*keep*.

Range detection
...............

The time evolution of each channel is searched for successive scans with
consistent behavior. A set of such scans "bad" scans for a given channel is
called a (time) range; the definition of bad is user defined (see below).

Range finding starts with a list of scans, where each scan is marked as "good"
or "bad". The definition of "bad" depends on what's being searched for (and
"good" is always defined as "not bad"). The start of a range is determined by:

* Starts with a "bad" scan (see below)
* The channel wasn't "bad" in the previous scan (e.g going good to bad)

Then the range continues and the end of the range is determined by 5 consecutive
good scans appearing (option: :token:`--numEndScans`). To prevent the printing
of spurious ranges due to transient effects ranges with less than 4 "bad" scans
in total are suppressed (option: :token:`--minBadScans`). A "range" found by
this algorithm can have include some "good" scans.

As a side-effect, channels with sparse "bad" behavior are also extracted. This
can be controlled by tightening the cuts in the algorithm above.

Three definitions of "bad" are currently available:

* ``mask``: the channel under consideration is masked
* ``maskReason``: the channel under consideration has a non-zero ``maskReason``
* ``zeroInputCap``: the channel under consideration has an scurve width that is
  consistent with zero input capacitance (``4.14E-02 < scurevWidth < 1.09E-01
  fC``). The precise values can be controlled using the :token:`--minNoise`
  and :token:`--maxNoise` options.

Output
......

For every "range" found in each of the VFATs, the following properties are
computed and printed in a table:

=============================== =======
Column header                   Meaning
=============================== =======
``ROBstr`` or ``vfatCH``        Strip number and VFAT channel, respectively
Last known good                 Date and time of the last good scan before the range ("never" if the range starts at the first scan)
Range begins                    Start date and time
Range ends                      End date and time ("never" if the range includes the lastest scan)
#scans                          Total number of scans (good and bad)
masked%                         Percentage of #scans where the channel is "masked", not to be confused with "bad" (useful to investigate channels that behave badly once in a while)
Initial ``maskReason``          ``maskReason`` for the first scan in the range
Other subsequent ``maskReason`` ``maskReason`` not present for the first scan but found in a later scan in the same range
=============================== =======

A summary table of initial ``maskReason`` vs VFAT is also printed at the end.

Arguments
---------

.. program:: timeHistoryAnalyzer.py

General arguments
.................

.. option:: -i,--inputDir <DIRECTORY>

    Input directory (=output directory of :program:`plotTimeSeries.py`)

.. option:: --ranges <STRING>

    Defines the range selection algorithm. Allowed values: ``mask``,
    ``maskReason``, ``zeroInputCap``

.. option:: --onlyCurrent

    Only show ranges that extend until the last scan

Options controlling bad scan removal
....................................

.. option:: --minScanAvgNoise <CHARGE>

    Minimum noise in fC, averaged over the whole detector, for a scan to be
    considered

.. option:: --maxScanMaskedFrac <FRACTION>

    Maximum fraction of masked channel, over the whole detector, for a scan to
    be considered

Options controlling the range finding algorithms
................................................

.. option:: --numEndScans <NUMBER>

    Number of "good" scans to end a range

.. option:: --minBadScans <NUMBER>

    Minimum number of "bad" scans to keep a range

.. option:: --minNoise <CHARGE>

    Lower bound on noise for the ``zeroInputCap`` range finder, in fC

.. option:: --maxNoise <CHARGE>

    Upper bound on noise for the ``zeroInputCap`` range finder, in fC

Examples
--------

The examples below assume that you have analyzed S-curves using
:program:`plotTimeSeries.py`, and that the output is located at:

.. code-block:: bash

    $ELOG_PATH/timeSeriesPlots/<chamber name>/vt1bumpX/

Note that the above structure is created automatically by
:program:`plotTimeSeries.py`.

Simple analysis
...............

The simplest possible call to :program:`timeHistoryAnalyzer.py` is:

.. code-block:: bash

    timeHistoryAnalyzer.py -i $ELOG_PATH/timeSeriesPlots/<chamber name>/vt1bumpX/

This will use the default range finder, ``maskReason``, and settings. Depending
on the detector and number of scans being analyzed, it may result in a lot of
output being printed to the terminal. For every VFAT, you will get a table that
looks like this:


========== ================ ================ ================ ====== ======= ====================== ==============================
``ROBstr`` Last known good  Range begins     Range ends       #scans Masked% Initial ``maskReason`` Other subsequent ``maskReason``
========== ================ ================ ================ ====== ======= ====================== ==============================
18         2017.10.11.11.24 2017.10.13.12.53 never            127    100     HotChannel,FitFailed
31         2017.10.11.11.24 2017.10.13.12.53 never            127    0       DeadChannel
91         2017.06.15.15.10 2017.06.16.14.35 2018.02.06.12.07 107    47      HotChannel             HighNoise
93         2017.03.27.16.22 2017.03.29.13.27 2017.05.31.14.48 46     56      HotChannel
93         2017.06.15.15.10 2017.06.16.14.35 2018.02.06.12.07 107    50      HotChannel             HighNoise
========== ================ ================ ================ ====== ======= ====================== ==============================

The meaning of the column headers is explained `above <#output>`_. Here's the
information that we can extract from the table (take a look :doc:`here
</masking>` first if you're not confident with the meaning of ``maskReason``):

* Strip number 18 became hot between 2017.10.11.11.24 and 2017.10.13.12.53. In
  the same period of time, strip number 31 died.
* Strip number 91 became hot in July 2017; afterwards, it was also found to have
  a high noise. It was recovered in February 2018. The masked fraction at 47%
  indicates that during this period, about half the scans didn't result in the
  corresponding channel being masked.
* Strip number 93 was hot during two periods: from the end of March to the end
  of May 2017, and afterwards from the beginning of April 2017 to the beginning
  of February 2018. Since both ranges have similar properties and the masked
  fraction is low, the split in two is likely an accident.

Using a different range finder
..............................

The example above used the ``maskReason`` range finder. One could also use
``zeroInputCap``:

.. code-block:: bash

    timeHistoryAnalyzer.py -i $ELOG_PATH/timeSeriesPlots/<chamber name>/vt1bumpX/ --ranges zeroInputCap

Note that ``--ranges zeroInputCap`` typically produces in a lot less output than
the default.

Reading the summary table
.........................

At the end of its output, :program:`timeHistoryAnalyzer.py` prints the following
table (some lines were stripped for concision):

= ========== ========= =========== ========= ==========
. HotChannel FitFailed DeadChannel HighNoise HighEffPed
= ========== ========= =========== ========= ==========
0      0         0          2          0         0
7      2         0          3          0         0
= ========== ========= =========== ========= ==========

The first column is the VFAT number; the others correspond to the possible
entries in ``maskReason``.

The table counts how many times a given ``MaskReason`` appears in the "Initial
``maskReason``" column of each per-VFAT tables. Indeed, if we look at VFAT 0 for
the above example, we find:

========== ================ ================ ================ ====== ======= ====================== ==============================
``ROBstr`` Last known good  Range begins     Range ends       #scans Masked% Initial ``maskReason`` Other subsequent ``maskReason``
========== ================ ================ ================ ====== ======= ====================== ==============================
    63     2017.04.07.15.46 2017.04.09.14.27 never            220    6       DeadChannel            HotChannel
    64     never            2017.03.27.13.51 never            229    0       DeadChannel
========== ================ ================ ================ ====== ======= ====================== ==============================

The two entries in the DeadChannel column correspond to two ranges, that turn
out to be from different strips (this may not be the case). Now VFAT 7:

========== ================ ================ ================ ====== ======= ====================== ==============================
``ROBstr`` Last known good  Range begins     Range ends       #scans Masked% Initial ``maskReason`` Other subsequent ``maskReason``
========== ================ ================ ================ ====== ======= ====================== ==============================
    0      2017.05.10.20.41 2017.05.31.09.21 never            182       0    DeadChannel
    2      2017.05.08.09.10 2017.05.10.19.57 never            184       1    HotChannel,DeadChannel
    3      2017.05.08.09.10 2017.05.10.19.57 never            184       1    HotChannel,DeadChannel
========== ================ ================ ================ ====== ======= ====================== ==============================

We can see that the three entries in the DeadChannel column and the two in the
HotChannel column come from the *same* ranges.

.. note::

    When using the :option:`--onlyCurrent` option, there's only one range per
    channel, which makes the table easier to understand.
"""

if __name__ == '__main__':
    import numpy as np
    import os
    import os.path
    import sys

    from optparse import OptionParser, OptionGroup
    parser = OptionParser()
    parser.add_option("-i", "--inputDir", type=str, dest="inputDir",
                      help="Input directory (=output directory of plotTimeSeries.py)")
    parser.add_option("--ranges", type=str, dest="ranges", default="maskReason",
                      help="Range selection. Possible values: mask, maskReason, zeroInputCap")
    parser.add_option("--onlyCurrent", dest="onlyCurrent", action="store_true",
                      help="Only show ranges that extend until the last scan")

    # Configuration of bad scan recovery
    group = OptionGroup(parser, 'Options controlling bad scan removal')
    group.add_option("--minScanAvgNoise", type=float, dest="minScanAvgNoise", default=0.1,
                     help="Minimum noise if fC, averaged over the whole detector, for a scan to be considered")
    group.add_option("--maxScanMaskedFrac", type=float, dest="maxScanMaskedFrac", default=0.07,
                     help="Maximum fraction of masked channel, over the whole detector, for a scan to be considered")
    parser.add_option_group(group)

    # Configuration of the range finding algo
    group = OptionGroup(parser, 'Options controlling the range finding algorithm')
    group.add_option("--numEndScans", type=int, dest="numEndScans", default=5,
                     help="Number of 'good' scans to end a range")
    group.add_option("--minBadScans", type=int, dest="minBadScans", default=4,
                     help="Minimum number of 'bad' scans to keep a range")
    # Only for 'zeroInputCap' range finder
    group.add_option("--minNoise", type=float, dest="minNoise", default=0.0414,
                     help="Lower bound on noise for the 'zeroInputCap' range finder, in fC")
    group.add_option("--maxNoise", type=float, dest="maxNoise", default=0.109,
                     help="Upper bound on noise for the 'zeroInputCap' range finder, in fC")
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if options.inputDir is None:
        print("Error: The -i argument is required")
        sys.exit(os.EX_USAGE)

    if not os.path.isdir(options.inputDir):
        print("Error: Not a directory: {0}".format(options.inputDir))
        sys.exit(os.EX_USAGE)

    from gempython.gemplotting.utils.anahistory import (
        findRangesMaskReason,
        findRangesMask,
        findRangesZeroInputCap,
        TimeSeriesData)

    findRangesFct = None
    findRangesKwArgs = {
        'numEndScans': options.numEndScans,
        'minBadScans': options.minBadScans,
    }
    if options.ranges == "mask":
        findRangesFct = findRangesMask
    elif options.ranges == "maskReason":
        findRangesFct = findRangesMaskReason
    elif options.ranges == "zeroInputCap":
        findRangesFct = findRangesZeroInputCap
        findRangesKwArgs['minNoise'] = options.minNoise
        findRangesKwArgs['maxNoise'] = options.maxNoise
    else:
        print("Error: Invalid argument for --ranges: {0} ".format(options.ranges))
        sys.exit(os.EX_USAGE)

    gemType="ge11"
        
    data = TimeSeriesData(options.inputDir, gemType)
    data.removeBadScans(minAverageNoise = options.minScanAvgNoise,
                        maxMaskedStripOrChanFraction = options.maxScanMaskedFrac)

    from gempython.gemplotting.utils.anaInfo import MaskReason
    from gempython.gemplotting.utils.anautilities import getEmptyPerVFATList
    from gempython.tools.hw_constants import vfatsPerGemVariant
    
    # Find ranges
    ranges = getEmptyPerVFATList() # [vfat][stripOrChan][ranges]
    for vfat in range(vfatsPerGemVariant[gemType]):
        for stripOrChan in range(128):
            ranges[vfat].append(findRangesFct(data, vfat, stripOrChan, **findRangesKwArgs))
            pass
        pass

    # Filter if needed
    if options.onlyCurrent:
        for vfat in range(vfatsPerGemVariant[gemType]):
            for stripOrChan in range(128):
                ranges[vfat][stripOrChan] = list(filter(lambda r: r.end == data.numScans(),
                                                        ranges[vfat][stripOrChan]))

    # Initialize tables
    rangesTables = getEmptyPerVFATList()

    maskReasonList = MaskReason.listReasons()
    summaryTable = np.zeros((vfatsPerGemVariant[gemType], len(maskReasonList)))

    # Fill tables
    for vfat in range(vfatsPerGemVariant[gemType]):
        for stripOrChan in range(128):
            for rng in ranges[vfat][stripOrChan]:
                # Per-vfat table
                additionnalReasons = rng.additionnalMaskReasons()
                rangesTables[vfat].append([
                    rng.stripOrChan,
                    rng.beforeStartString(),
                    rng.startString(),
                    rng.endString(),
                    rng.scanCount(),
                    int(100 * rng.maskedScanRatio()),
                    MaskReason.humanReadable(rng.initialMaskReason()),
                    MaskReason.humanReadable(additionnalReasons) if additionnalReasons != 0 else ''])

                # Summary
                for i in range(len(maskReasonList)):
                    if rng.initialMaskReason() & maskReasonList[i][1]:
                        summaryTable[vfat][i] += 1
                    pass
                pass
            pass
        pass

    # Print per-VFAT tables
    from tabulate import tabulate

    headers = [
        '`{0}`'.format(data.stripOrChanMode),
        'Last known good',
        'Range begins',
        'Range ends',
        '#scans',
        'Masked%',
        'Initial `maskReason`',
        'Other subsequent `maskReason`s' ]

    for vfat in range(vfatsPerGemVariant[gemType]):
        print('''
        ## VFAT {0}
        '''.format(vfat))

        print(tabulate(rangesTables[vfat],
                       headers = headers,
                       tablefmt = 'pipe',
                       numalign = 'center'))
        pass

    # Print summary table
    print('''
## Initial maskReason summary

The table below shows the distribution of the initial maskReason for ranges found in each VFAT.
Note that a single range is counted as many times as it has maskReasons.
''')

    headers = [ name for name, _ in maskReasonList ]
    print(tabulate(summaryTable,
                   headers = headers,
                   tablefmt = 'pipe',
                   showindex = True,
                   numalign = 'center'))
