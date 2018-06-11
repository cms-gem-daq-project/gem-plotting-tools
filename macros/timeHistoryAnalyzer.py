#! /usr/bin/env python

import numpy as np

class MaskedRange(object):
    def __init__(self, mask, start, maxSkip = 5):
        # Assumption: start is masked
        self.start = start
        self.end = start + 1

        skipped = 0
        for time in range(self.start, len(mask)):
            if mask[time]:
                self.end = time + 1
                skipped = 0
            else:
                skipped += 1
            if skipped > maxSkip:
                break

    def beforeStartString(self, dates):
        if self.start == 0:
            return 'never'
        else:
            return dates[self.start - 1]

    def startString(self, dates):
        if self.start == 0:
            return 'first'
        else:
            return dates[self.start]

    def endString(self, dates):
        if self.end == len(dates):
            return 'never'
        else:
            return dates[self.end]

    def afterEndString(self, dates):
        if self.end + 1 >= len(dates):
            return 'never'
        else:
            return dates[self.end + 1]

    def scanCount(self):
        return self.end - self.start

    def maskedScanCount(self, mask):
        return np.count_nonzero(mask[self.start:self.end])

    def maskedScanRatio(self, mask):
        return float(self.maskedScanCount(mask)) / self.scanCount()

    def initialMaskReason(self, maskReason):
        return int(maskReason[self.start])

    def allMaskReasons(self, maskReason):
        res = 0
        for time in range(self.start, self.end):
            res |= int(maskReason[time])
        return res

    def additionnalMaskReasons(self, maskReason):
        return self.allMaskReasons(maskReason) ^ self.initialMaskReason(maskReason)

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

        self.mask = np.swapaxes(self.mask, 0, 1) # Reorder to [time][vfat][strip]
        self.maskReason = np.swapaxes(self.maskReason, 0, 1) # Reorder to [time][vfat][strip]

    def removeBadScans(self):
        numMaskedChannels = np.count_nonzero(self.mask, (1, 2))
        badScans = np.logical_or(numMaskedChannels == 0,
                                 numMaskedChannels / 24. / 128 > 0.07)
        self.dates = self.dates[np.logical_not(badScans)]
        self.mask = self.mask[np.logical_not(badScans)]
        self.maskReason = self.maskReason[np.logical_not(badScans)]

    def analyze(self):
        from gempython.gemplotting.utils.anaInfo import MaskReason
        for vfat in range(24):
            timePoints = self.mask.shape[0]
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
                chanMask = self.mask[:,vfat,chan]
                chanMaskReason = self.maskReason[:,vfat,chan]

                start = 0
                while start < timePoints - 1:
                    if chanMaskReason[start]:
                        mrange = MaskedRange(chanMaskReason, start)
                        start = mrange.end + 1

                        if mrange.maskedScanCount(chanMaskReason) >= 4:
                            additionnalReasons = mrange.additionnalMaskReasons(chanMaskReason)
                            print '| {:>7} | {:<16} | {:<16} | {:<16} | {:>6} | {:>7.0f} | {:<35} | {:<30} |'.format(
                                chan,
                                mrange.beforeStartString(self.dates),
                                mrange.startString(self.dates),
                                mrange.endString(self.dates),
                                mrange.scanCount(),
                                100 * mrange.maskedScanRatio(chanMask),
                                MaskReason.humanReadable(mrange.initialMaskReason(chanMaskReason)),
                                MaskReason.humanReadable(additionnalReasons) if additionnalReasons != 0 else '')
                    else:
                        start += 1

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
