#! /usr/bin/env python

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

class TimeSeriesData(object):
    def __init__(self, inputDir):
        import ROOT as r
        import numpy as np
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

        self.mask = np.array(self.mask)
        self.maskReason = np.array(self.maskReason)

        self.mask = np.swapaxes(self.mask, 0, 1) # Reorder to [time][vfat][strip]
        self.maskReason = np.swapaxes(self.maskReason, 0, 1) # Reorder to [time][vfat][strip]

    def removeBadScans(self):
        import numpy as np
        numMaskedChannels = np.count_nonzero(self.mask, (1, 2))
        badScans = np.logical_or(numMaskedChannels == 0,
                                 numMaskedChannels / 24. / 128 > 0.07)
        self.mask = self.mask[np.logical_not(badScans)]
        self.maskReason = self.maskReason[np.logical_not(badScans)]

    def analyze(self):
        import numpy as np
        for vfat in range(24):
            print '======== VFAT %d =========' % vfat
            for chan in range(128):
                chanMask = self.mask[:,vfat,chan]
                chanMaskReason = self.maskReason[:,vfat,chan]

                start = 0
                timePoints = len(chanMask)
                while start < timePoints - 1:
                    if chanMask[start]:
                        mrange = MaskedRange(chanMask, start)
                        start = mrange.end + 1

                        length = mrange.end - mrange.start
                        ratio = np.count_nonzero(chanMask[mrange.start:mrange.end]) / float(length)
                        if ratio * length >= 4:
                            print '%3d %3d [%3d %3d): %f' % (
                                chan, length, mrange.start, mrange.end, ratio)
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
