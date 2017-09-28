#!/bin/env python

if __name__ == '__main__':
    from macros.plotoptions import parser
    (options, args) = parser.parse_args()

    from macros.scurvePlottingUtitilities import plot_vfat_summary
    plot_vfat_summary(options.vfat, options.filename)
