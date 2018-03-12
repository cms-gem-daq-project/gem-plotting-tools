#!/bin/env python

if __name__ == '__main__':
    from plotoptions import parser
    (options, args) = parser.parse_args()

    from scurvePlottingUtitilities import plot_vfat_summary
    plot_vfat_summary(options.vfat, options.filename)
