r"""
``anahistory`` --- Tools to analyze the time evolution of detectors
===================================================================

.. code-block:: python

    import gempython.gemplotting.utils.anahistory

Documentation
-------------
"""

import numpy as _np

class ChannelTimeRange(object):
    """Represents a range of scans in TimeSeriesData, for a given VFAT and
    strip/channel

    Attributes:
        begin: Index of the first scan in the range
        end: Index of the first scan not in the range
        vfat: VFAT number
        stripOrChan: Channel number
    """

    def __init__(self, data, vfat, stripOrChan, start, end):
        """Constructor

        Args:
            data: A TimeSeriesData object to load scan results from
            vfat: The VFAT number
            stripOrChan: The stripOrChan number in the VFAT
            start: The index of the first scan in the range
            end: The index of the first scan not in the range
        """
        self._dates = data.dates
        self._mask = data.mask[vfat,stripOrChan]
        self._maskReason = data.maskReason[vfat,stripOrChan]
        self._noise = data.noise[vfat,stripOrChan]

        self.vfat = vfat
        self.stripOrChan = stripOrChan
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
        return _np.count_nonzero(self._maskReason[self.start:self.end])

    def maskedScanCount(self):
        """Returns the number of scans with mask set in the range"""
        return _np.count_nonzero(self._mask[self.start:self.end])

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

def _findRangesMeta(data, vfat, stripOrChan, stripOrChanData, numEndScans):
    """Finds ranges of scans based on the contents of stripOrChanData.

    Searches the data for ranges of scans with stripOrChanData == true. During
    the search, at most numEndScans scans with no maskReason set can be skipped.
    Only ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        stripOrChan: The stripOrChan to return ranges for
        stripOrChanData: A list of booleans, with each entry representing one
            scan.
        numEndScans: The maximum number of "good" scans between two "bad" scans

    Returns:
        A list of ChannelTimeRange objects
    """
    ranges = []

    start = 0
    while start < len(stripOrChanData) - 1:
        if stripOrChanData[start]:
            end = start
            skipped = 0
            for time in range(start, len(stripOrChanData)):
                if stripOrChanData[time]:
                    end = time + 1
                    skipped = 0
                else:
                    skipped += 1
                if skipped > numEndScans:
                    break
                pass

            if end > start:
                ranges.append(ChannelTimeRange(data, vfat, stripOrChan, start, end))

            start = end + 1
        else:
            start += 1
        pass

    return ranges


def findRangesMaskReason(data, vfat, stripOrChan, numEndScans = 5, minBadScans = 4):
    """Finds ranges of scans based on the maskReason attribute.

    Searches the data for the given vfat and stripOrChan for ranges of scans
    with non-zero maskReason. During the search, at most numEndScans scans with no
    maskReason set can be skipped. Only ranges with more than minBadScans are
    kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        stripOrChan: The stripOrChan to return ranges for
        numEndScans: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of ChannelTimeRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             stripOrChan,
                             data.maskReason[vfat,stripOrChan] != 0,
                             numEndScans)

    return list(filter(lambda r: r.badMaskReasonScanCount() >= minBadScans,
                       ranges))

def findRangesMask(data, vfat, stripOrChan, numEndScans = 5, minBadScans = 4):
    """Finds ranges of scans based on the mask attribute.

    Searches the data for the given vfat and stripOrChan for ranges of scans
    with non-zero maskReason. During the search, at most numEndScans scans with mask
    not set can be skipped. Only ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        stripOrChan: The stripOrChan to return ranges for
        numEndScans: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of ChannelTimeRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             stripOrChan,
                             data.mask[vfat,stripOrChan] != 0,
                             numEndScans)

    return list(filter(lambda r: r.maskedScanCount() >= minBadScans,
                       ranges))

def findRangesZeroInputCap(data,
                           vfat,
                           stripOrChan,
                           minNoise = 0.0414,
                           maxNoise = 0.109,
                           numEndScans = 5,
                           minBadScans = 4):
    """Finds ranges of scans whose noise is compatible with zero input
    capacitance.

    Searches the data for the given vfat and stripOrChan for ranges of low-noise
    scans. A scan has low noise if minNoise < noise < maxNoise. During the
    search, at most numEndScans scans with mask not set can be skipped. Only ranges
    with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        stripOrChan: The stripOrChan to return ranges for
        maxNoise: Scans with a noise below this value are considered low-noise
        numEndScans: The maximum number of consecutive scans that don't fulfill the
            low-noise condition between two scans that do
        minBadScans: The minimum number of low-noise scans in any returned range

    Returns:
        A list of ChannelTimeRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             stripOrChan,
                             _np.logical_and(data.noise[vfat,stripOrChan] > minNoise,
                                             data.noise[vfat,stripOrChan] < maxNoise),
                             numEndScans)

    return list(filter(lambda r: _np.count_nonzero(r.noise() < maxNoise) >= minBadScans,
                       ranges))

class TimeSeriesData(object):
    """Holds information about time variation of scan results.

    Each property is stored as a 3D Numpy array with indexes
    [vfat][stripOrChan][time]. The time index -> scan date mapping is exposed in the
    date attribute.

    Attributes:
        dates: Numpy array of strings containing the scan dates.
        stripOrChanMode (string): Meaning of the ``stripOrChan`` index in the
            property arrays, can be ``ROBstr`` or ``vfatCH``.
        mask: Data for the "mask" property,
        maskReason: Data for the "maskReason" property,
    """

    def __init__(self, inputDir, gemType="ge11"):
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

        self.gemType = gemType
        
        file_mask = r.TFile('{0}/gemPlotterOutput_mask_vs_scandate.root'.format(inputDir), 'READ')
        if file_mask.IsZombie():
            raise IOError('Could not open {0}. Is {1} the output directory of plotTimeSeries.py?'.format(
                file_mask.GetPath(), inputDir))

        file_maskReason = r.TFile('{0}/gemPlotterOutput_maskReason_vs_scandate.root'.format(inputDir), 'READ')
        if file_maskReason.IsZombie():
            raise IOError('Could not open {0}. Is {1} the output directory of plotTimeSeries.py?'.format(
                file_maskReason.GetPath(), inputDir))

        file_noise = r.TFile('{0}/gemPlotterOutput_noise_vs_scandate.root'.format(inputDir), 'READ')
        if file_noise.IsZombie():
            raise IOError('Could not open {0}. Is {1} the output directory of plotTimeSeries.py?'.format(
                file_noise.GetPath(), inputDir))

        # Auto-detect the meaning of stripOrChan
        possibleModes = ['ROBstr', 'vfatCH'] # See gemPlotter.py
        for mode in possibleModes:
            if file_mask.Get('VFAT0/h_{0}_vs_scandate_Obsmask_VFAT0'.format(mode)):
                self.stripOrChanMode = mode
                break
        else:
            from string import join
            raise RuntimeError(
                'No key VFAT0/h_<MODE>_vs_scandate_Obsmask_VFAT0 in file {0}\nTried MODE={1}. Was the file produced by plotTimeSeries.py?'.format(file_mask.GetPath(), join(possibleModes, ',')))
        
        self.mask = [] # [vfat][time][stripOrChan]; warning: reordered after loading
        self.maskReason = [] # [vfat][time][stripOrChan]; warning: reordered after loading
        self.noise = [] # [vfat][time][stripOrChan]; warning: reordered after loading

        from gempython.tools.hw_constants import vfatsPerGemVariant
        
        for vfat in range(0,vfatsPerGemVariant[self.gemType]):
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

        self.dates = _np.array(self.dates)
        self.mask = _np.array(self.mask)
        self.maskReason = _np.array(self.maskReason)
        self.noise = _np.array(self.noise)

        self.mask = _np.swapaxes(self.mask, 1, 2) # Reorder to [vfat][stripOrChan][time]
        self.maskReason = _np.swapaxes(self.maskReason, 1, 2) # Reorder to [vfat][stripOrChan][time]
        self.noise = _np.swapaxes(self.noise, 1, 2) # Reorder to [vfat][stripOrChan][time]

    def removeBadScans(self, minAverageNoise = 0.1, maxMaskedStripOrChanFraction = 0.07):
        """Finds bad scans and removes them from the data.

        Any scan matching one of the following criteria is considered bad:

        * The average noise is below minAverageNoise
        * The fraction of masked strips/channels is higher than maxMaskedStripOrChanFraction

        Args:
            minAverageNoise: The minimum noise, averaged over all channels, for
                a scan to be kept. Value in fC.
            maxMaskedStripOrChanFraction: The maximum fraction of masked
                strips/channels for a scan to be kept.
        """
        from gempython.tools.hw_constants import vfatsPerGemVariant
        badScans = _np.logical_or(_np.mean(self.noise, (0, 1)) < minAverageNoise,
                                 _np.count_nonzero(self.mask, (0, 1)) / vfatsPerGemVariant[self.gemType] / 128 > maxMaskedStripOrChanFraction)
        self.dates = self.dates[_np.logical_not(badScans)]
        self.mask = self.mask[:,:,_np.logical_not(badScans)]
        self.maskReason = self.maskReason[:,:,_np.logical_not(badScans)]
        self.noise = self.noise[:,:,_np.logical_not(badScans)]

    def numScans(self):
        """Returns how many scans are available"""
        return len(self.dates)
