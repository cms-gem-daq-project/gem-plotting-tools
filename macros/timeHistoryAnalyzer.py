#! /usr/bin/env python

import numpy as np

class MaskedRange(object):
    def __init__(self, data, vfat, channel, start, maxSkip = 5):
        self.dates = data.dates
        self.mask = data.mask[vfat,channel]
        self.maskReason = data.maskReason[vfat,channel]
        self.vfat = vfat
        self.channel = channel

        # Assumption: start is masked
        self.start = start
        self.end = start + 1

        skipped = 0
        for time in range(self.start, len(self.maskReason)):
            if self.maskReason[time] !=0:
                self.end = time + 1
                skipped = 0
            else:
                skipped += 1
            if skipped > maxSkip:
                break

    def beforeStartString(self):
        if self.start == 0:
            return 'never'
        else:
            return self.dates[self.start - 1]

    def startString(self):
        if self.start == 0:
            return 'first'
        else:
            return self.dates[self.start]

    def endString(self):
        if self.end == len(self.dates):
            return 'never'
        else:
            return self.dates[self.end]

    def afterEndString(self):
        if self.end + 1 >= len(self.dates):
            return 'never'
        else:
            return self.dates[self.end + 1]

    def scanCount(self):
        return self.end - self.start

    def badMaskReasonScanCount(self):
        return np.count_nonzero(self.maskReason[self.start:self.end])

    def maskedScanCount(self):
        return np.count_nonzero(self.mask[self.start:self.end])

    def maskedScanRatio(self):
        return float(self.maskedScanCount()) / self.scanCount()

    def initialMaskReason(self):
        return int(self.maskReason[self.start])

    def allMaskReasons(self):
        res = 0
        for time in range(self.start, self.end):
            res |= int(self.maskReason[time])
        return res

    def additionnalMaskReasons(self):
        return self.allMaskReasons() ^ self.initialMaskReason()

def findRangesMaskReason(data, vfat, channel):
    ranges = []

    start = 0
    while start < data.maskReason.shape[2] - 1:
        if data.maskReason[vfat,channel,start]:
            r = MaskedRange(data, vfat, channel, start)
            start = r.end + 1

            if r.badMaskReasonScanCount() >= 4:
                ranges.append(r)
        else:
            start += 1

    return ranges

class TimeSeriesData(object):
    def __init__(self, inputDir):
        import ROOT as r
        from root_numpy import hist2array

        file_mask = r.TFile('%s/gemPlotterOutput_mask_vs_scandate.root' % inputDir, 'READ')
        file_maskReason = r.TFile('%s/gemPlotterOutput_maskReason_vs_scandate.root' % inputDir, 'READ')

        self.mask = [] # [vfat][time][strip]; warning: reordered after loading
        self.maskReason = [] # [vfat][time][strip]; warning: reordered after loading

        for vfat in range(0,24):
            dirname = 'VFAT%d' % vfat
            dir_mask = file_mask.Get(dirname)
            dir_maskReason = file_maskReason.Get(dirname)

            hist_mask = dir_mask.Get("h_ROBstr_vs_scandate_Obsmask_VFAT%d" % vfat)
            hist_maskReason = dir_maskReason.Get("h_ROBstr_vs_scandate_ObsmaskReason_VFAT%d" % vfat)

            self.mask.append(hist2array(hist_mask))
            self.maskReason.append(hist2array(hist_maskReason))

            self.dates = [] # [time]
            for bin in range(hist_mask.GetNbinsX()):
                self.dates.append(hist_mask.GetXaxis().GetBinLabel(bin + 1))

        self.dates = np.array(self.dates)
        self.mask = np.array(self.mask)
        self.maskReason = np.array(self.maskReason)

        self.mask = np.swapaxes(self.mask, 1, 2) # Reorder to [vfat][strip][time]
        self.maskReason = np.swapaxes(self.maskReason, 1, 2) # Reorder to [vfat][strip][time]

    def removeBadScans(self):
        numMaskedChannels = np.count_nonzero(self.mask, (0, 1))
        badScans = np.logical_or(numMaskedChannels == 0,
                                 numMaskedChannels / 24. / 128 > 0.07)
        self.dates = self.dates[np.logical_not(badScans)]
        self.mask = self.mask[:,:,np.logical_not(badScans)]
        self.maskReason = self.maskReason[:,:,np.logical_not(badScans)]

    def analyze(self):
        from gempython.gemplotting.utils.anaInfo import MaskReason
        for vfat in range(24):
            timePoints = self.mask.shape[2]
            print '''
## VFAT %d

first scan is %s
latest scan is %s

| Channel | Known good       | Range begins     | Range ends       | #scans | Masked%% | Initial `maskReason`                | Other subsequent `maskReason`s |
| ------: | :--------------- | :--------------- | :--------------- | -----: | ------: | :---------------------------------- | :----------------------------- |''' % (
                vfat,
                self.dates[0],
                self.dates[timePoints - 1])
            for chan in range(128):
                ranges = findRangesMaskReason(self, vfat, chan)
                for r in ranges:
                    additionnalReasons = r.additionnalMaskReasons()
                    print '| {:>7} | {:<16} | {:<16} | {:<16} | {:>6} | {:>7.0f} | {:<35} | {:<30} |'.format(
                        chan,
                        r.beforeStartString(),
                        r.startString(),
                        r.endString(),
                        r.scanCount(),
                        100 * r.maskedScanRatio(),
                        MaskReason.humanReadable(r.initialMaskReason()),
                        MaskReason.humanReadable(additionnalReasons) if additionnalReasons != 0 else '')

if __name__ == '__main__':
    import os
    import os.path
    import sys

    from optparse import OptionParser, OptionGroup
    parser = OptionParser()
    parser.add_option("-i", "--inputDir", type=str, dest="inputDir",
                      help="Input directory (=output directory of plotTimeSeries.py)")
    (options, args) = parser.parse_args()

    if options.inputDir is None:
        print("Error: The -i argument is required")
        sys.exit(os.EX_USAGE)

    if not os.path.isdir(options.inputDir):
        print("Error: Not a directory: %s" % options.inputDir)
        sys.exit(os.EX_USAGE)

    data = TimeSeriesData(options.inputDir)
    data.removeBadScans()
    data.analyze()
