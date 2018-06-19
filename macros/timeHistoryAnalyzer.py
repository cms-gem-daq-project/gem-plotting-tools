#! /usr/bin/env python

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
        print("Error: Not a directory: %s" % options.inputDir)
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
        print("Error: Invalid argument for --ranges: %s " % options.ranges)
        sys.exit(os.EX_USAGE)

    data = TimeSeriesData(options.inputDir)
    data.removeBadScans(minAverageNoise = options.minScanAvgNoise,
                        maxMaskedStripOrChanFraction = options.maxScanMaskedFrac)

    from gempython.gemplotting.utils.anaInfo import MaskReason
    from gempython.gemplotting.utils.anautilities import getEmptyPerVFATList

    # Find ranges
    ranges = getEmptyPerVFATList() # [vfat][stripOrChan][ranges]
    for vfat in range(24):
        for stripOrChan in range(128):
            ranges[vfat].append(findRangesFct(data, vfat, stripOrChan, **findRangesKwArgs))
            pass
        pass

    # Filter if needed
    if options.onlyCurrent:
        for vfat in range(24):
            for stripOrChan in range(128):
                ranges[vfat][stripOrChan] = list(filter(lambda r: r.end == data.numScans(),
                                                        ranges[vfat][stripOrChan]))

    # Initialize tables
    rangesTables = getEmptyPerVFATList()

    maskReasonList = MaskReason.listReasons()
    summaryTable = np.zeros((24, len(maskReasonList)))

    # Fill tables
    for vfat in range(24):
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
        '`%s`' % data.stripOrChanMode,
        'Last known good',
        'Range begins',
        'Range ends',
        '#scans',
        'Masked%',
        'Initial `maskReason`',
        'Other subsequent `maskReason`s' ]

    for vfat in range(24):
        print '''
## VFAT %d
''' % vfat

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
