#!/bin/env python

if __name__ == '__main__':
    from gempython.gemplotting.macros.plotoptions import parser
    (options, args) = parser.parse_args()

    from gempython.gemplotting.macros.scurvePlottingUtitilities import plot_vfat_summary
    plot_vfat_summary(options.vfat, options.filename)
