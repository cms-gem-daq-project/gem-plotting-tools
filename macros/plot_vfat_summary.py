#!/bin/env python

if __name__ == '__main__':
    import gempython.gemplotting as gemplotting
    
    from gemplotting.macros.plotoptions import parser
    (options, args) = parser.parse_args()

    from gemplotting.macros.scurvePlottingUtitilities import plot_vfat_summary
    plot_vfat_summary(options.vfat, options.filename)
