#! /usr/bin/env python

import numpy as np

class MaskedRange(object):
    """Represents a range of scans in TimeSeriesData, for a given VFAT and
    channel

    Attributes:
        begin: Index of the first scan in the range
        end: Index of the first scan not in the range
        vfat: VFAT number
        channel: Channel number
    """

    def __init__(self, data, vfat, channel, start, end):
        """Constructor

        Args:
            data: A TimeSeriesData object to load scan results from
            vfat: The VFAT number
            channel: The channel number in the VFAT
            start: The index of the first scan in the range
            end: The index of the first scan not in the range
        """
        self._dates = data.dates
        self._mask = data.mask[vfat,channel]
        self._maskReason = data.maskReason[vfat,channel]
        self._noise = data.noise[vfat,channel]

        self.vfat = vfat
        self.channel = channel
        self.start = start
        self.end = end

    def beforeStartString(self):
        """Returns the date of the last scan before the range

        Returns:
            If the range includes the first available scan, returns 'never'.
            Else returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.start == 0:
            return 'never'
        else:
            return self._dates[self.start - 1]

    def startString(self):
        """Returns the date of the first scan in the range, formatted as
        %Y.%m.%d.%H.%M."""
        return self._dates[self.start]

    def endString(self):
        """Returns the date of the last scan in the range

        Returns:
            If the range includes the last available scan, returns 'never'. Else
            returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.end == len(self._dates):
            return 'never'
        else:
            return self._dates[self.end - 1]

    def afterEndString(self):
        """Returns the date of the first scan after the range

        Returns:
            If the range includes the last available scan, returns 'none'. Else
            returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.end >= len(self._dates) - 1:
            return 'none'
        else:
            return self._dates[self.end]

    def scanCount(self):
        """Returns the number of scans in the range"""
        return self.end - self.start

    def badMaskReasonScanCount(self):
        """Returns the number of scans with non-zero maskReason in the range"""
        return np.count_nonzero(self._maskReason[self.start:self.end])

    def maskedScanCount(self):
        """Returns the number of scans with mask set in the range"""
        return np.count_nonzero(self._mask[self.start:self.end])

    def maskedScanRatio(self):
        """Returns the fraction of scans with mask set in the range"""
        return float(self.maskedScanCount()) / self.scanCount()

    def initialMaskReason(self):
        """Returns the maskReason for the first scan in the range"""
        return int(self._maskReason[self.start])

    def allMaskReasons(self):
        """Returns a maskReason bitmask that contains all the maskReasons in the
        range"""
        res = 0
        for time in range(self.start, self.end):
            res |= int(self._maskReason[time])
        return res

    def additionnalMaskReasons(self):
        """Returns a maskReason bitmask that contains all the maskReaons in the
        range but not in the first scan"""
        return self.allMaskReasons() ^ self.initialMaskReason()

    def noise(self):
        """Returns a Numpy array containing the noise information for scans in
        the range"""
        return self._noise[self.start:self.end]

def _findRangesMeta(data, vfat, channel, channelData, maxSkip):
    """Finds ranges of scans based on the contents of channelData.

    Searches the data for ranges of scans with channelData == true. During the
    search, at most maxSkip scans with no maskReason set can be skipped. Only
    ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        channelData: A list of booleans, with each entry representing one scan
        maxSkip: The maximum number of "good" scans between two "bad" scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = []

    start = 0
    while start < len(channelData) - 1:
        if channelData[start]:
            end = start
            skipped = 0
            for time in range(start, len(channelData)):
                if channelData[time]:
                    end = time + 1
                    skipped = 0
                else:
                    skipped += 1
                if skipped > maxSkip:
                    break
                pass

            if end > start:
                ranges.append(MaskedRange(data, vfat, channel, start, end))

            start = end + 1
        else:
            start += 1
        pass

    return ranges


def findRangesMaskReason(data, vfat, channel, maxSkip = 5, minBadScans = 4):
    """Finds ranges of scans based on the maskReason attribute.

    Searches the data for the given vfat and channel for ranges of scans with
    non-zero maskReason. During the search, at most maxSkip scans with no
    maskReason set can be skipped. Only ranges with more than minBadScans are
    kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        maxSkip: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             channel,
                             data.maskReason[vfat,channel] != 0,
                             maxSkip)

    return list(filter(lambda r: r.badMaskReasonScanCount() >= minBadScans,
                       ranges))

def findRangesMask(data, vfat, channel, maxSkip = 5, minBadScans = 4):
    """Finds ranges of scans based on the mask attribute.

    Searches the data for the given vfat and channel for ranges of scans with
    non-zero maskReason. During the search, at most maxSkip scans with mask not
    set can be skipped. Only ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        maxSkip: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             channel,
                             data.mask[vfat,channel] != 0,
                             maxSkip)

    return list(filter(lambda r: r.maskedScanCount() >= minBadScans,
                       ranges))

def findRangesNoise(data,
                    vfat,
                    channel,
                    maxNoise = 0.02,
                    maxSkip = 5,
                    minBadScans = 4):
    """Finds ranges of scans based on noise.

    Searches the data for the given vfat and channel for ranges of low-noise
    scans. A scan has low noise if noise < maxNoise. During the search, at most
    maxSkip scans with mask not set can be skipped. Only ranges with more than
    minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        maxNoise: Scans with a noise below this value are considered low-noise
        maxSkip: The maximum number of consecutive scans that don't fulfill the
            low-noise condition between two scans that do
        minBadScans: The minimum number of low-noise scans in any returned range

    Returns:
        A list of MaskedRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             channel,
                             data.noise[vfat,channel] < maxNoise,
                             maxSkip)

    return list(filter(lambda r: np.count_nonzero(r.noise() < maxNoise) >= minBadScans,
                       ranges))

class TimeSeriesData(object):
    """Holds information about time variation of scan results.

    Each property is stored as a 3D Numpy array with indexes
    [vfat][channel][time]. The time index -> scan date mapping is exposed in the
    date attribute.

    Attributes:
        dates: Numpy array of strings containing the scan dates.
        mask: Data for the "mask" property,
        maskReason: Data for the "maskReason" property,
    """

    def __init__(self, inputDir):
        """Creates a TimeSeriesData object by reading the files located in the
        inputDir directory.

        The input directory must contain the following files:

        * gemPlotterOutput_mask_vs_scandate.root
        * gemPlotterOutput_maskReason_vs_scandate.root
        * gemPlotterOutput_noise_vs_scandate.root

        They are created by plotTimeSeries.py.

        Args:
            inputDir: The path to the input directory
        """
        import ROOT as r
        from root_numpy import hist2array

        file_mask = r.TFile('%s/gemPlotterOutput_mask_vs_scandate.root' % inputDir, 'READ')
        if file_mask.IsZombie():
            raise IOError('Could not open %s' % file_mask.GetPath())

        file_maskReason = r.TFile('%s/gemPlotterOutput_maskReason_vs_scandate.root' % inputDir, 'READ')
        if file_maskReason.IsZombie():
            raise IOError('Could not open %s' % file_maskReason.GetPath())

        file_noise = r.TFile('%s/gemPlotterOutput_noise_vs_scandate.root' % inputDir, 'READ')
        if file_noise.IsZombie():
            raise IOError('Could not open %s' % file_noise.GetPath())

        self.mask = [] # [vfat][time][channel]; warning: reordered after loading
        self.maskReason = [] # [vfat][time][channel]; warning: reordered after loading
        self.noise = [] # [vfat][time][channel]; warning: reordered after loading

        for vfat in range(0,24):
            hist_mask = file_mask.Get(
                "VFAT{0:d}/h_ROBstr_vs_scandate_Obsmask_VFAT{0:d}".format(vfat))
            hist_maskReason = file_maskReason.Get(
                "VFAT{0:d}/h_ROBstr_vs_scandate_ObsmaskReason_VFAT{0:d}".format(vfat))
            hist_noise = file_noise.Get(
                "VFAT{0:d}/h_ROBstr_vs_scandate_Obsnoise_VFAT{0:d}".format(vfat))

            self.mask.append(hist2array(hist_mask))
            self.maskReason.append(hist2array(hist_maskReason))
            self.noise.append(hist2array(hist_noise))

            self.dates = [] # [time]
            for bin in range(hist_mask.GetNbinsX()):
                self.dates.append(hist_mask.GetXaxis().GetBinLabel(bin + 1))
                pass
            pass

        self.dates = np.array(self.dates)
        self.mask = np.array(self.mask)
        self.maskReason = np.array(self.maskReason)
        self.noise = np.array(self.noise)

        self.mask = np.swapaxes(self.mask, 1, 2) # Reorder to [vfat][channel][time]
        self.maskReason = np.swapaxes(self.maskReason, 1, 2) # Reorder to [vfat][channel][time]
        self.noise = np.swapaxes(self.noise, 1, 2) # Reorder to [vfat][channel][time]

    def removeBadScans(self, minAverageNoise = 0.1, maxMaskedChannelFraction = 0.07):
        """Finds bad scans and removes them from the data.

        Any scan matching one of the following criteria is considered bad:

        * The average noise is below maxAverageNoise
        * The fraction of masked channels is higher than maxMaskedChannelFraction

        Args:
            minAverageNoise: The minimum noise, averaged over all channels, for
                a scan to be kept. Value in fC.
            maxMaskedChannelFraction: The maximum fraction of masked channels
                for a scan to be kept.
        """
        badScans = np.logical_or(np.mean(self.noise, (0, 1)) < minAverageNoise,
                                 np.count_nonzero(self.mask, (0, 1)) / 24. / 128 > maxMaskedChannelFraction)
        self.dates = self.dates[np.logical_not(badScans)]
        self.mask = self.mask[:,:,np.logical_not(badScans)]
        self.maskReason = self.maskReason[:,:,np.logical_not(badScans)]
        self.noise = self.noise[:,:,np.logical_not(badScans)]

if __name__ == '__main__':
    import os
    import os.path
    import sys

    from optparse import OptionParser, OptionGroup
    parser = OptionParser()
    parser.add_option("-i", "--inputDir", type=str, dest="inputDir",
                      help="Input directory (=output directory of plotTimeSeries.py)")
    parser.add_option("--ranges", type=str, dest="ranges", default="maskReason",
                      help="Range selection. Possible values: mask, maskReason, noise")
    (options, args) = parser.parse_args()

    if options.inputDir is None:
        print("Error: The -i argument is required")
        sys.exit(os.EX_USAGE)

    if not os.path.isdir(options.inputDir):
        print("Error: Not a directory: %s" % options.inputDir)
        sys.exit(os.EX_USAGE)

    findRangesFct = None
    if options.ranges == "mask":
        findRangesFct = findRangesMask
    elif options.ranges == "maskReason":
        findRangesFct = findRangesMaskReason
    elif options.ranges == "noise":
        findRangesFct = findRangesNoise
    else:
        print("Error: Invalid argument for --ranges: %s " % options.ranges)
        sys.exit(os.EX_USAGE)

    data = TimeSeriesData(options.inputDir)
    data.removeBadScans()

    from gempython.gemplotting.utils.anaInfo import MaskReason

    # Find ranges
    ranges = [] # [vfat][channel][ranges]
    for vfat in range(24):
        ranges.append([])
        for channel in range(128):
            ranges[vfat].append(findRangesFct(data, vfat, channel))
            pass
        pass

    # Initialize tables
    rangesTables = [ [] for vfat in range(24) ]

    maskReasonList = MaskReason.listReasons()
    summaryTable = np.zeros((24, len(maskReasonList)))

    # Fill tables
    for vfat in range(24):
        for channel in range(128):
            for rng in ranges[vfat][channel]:
                # Per-vfat table
                additionnalReasons = rng.additionnalMaskReasons()
                rangesTables[vfat].append([
                    rng.channel,
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
        'Channel',
        'Known good',
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
