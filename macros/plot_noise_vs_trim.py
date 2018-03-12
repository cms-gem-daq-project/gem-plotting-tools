#!/bin/env python

if __name__ == '__main__':
    from plotoptions import parser
    (options, args) = parser.parse_args()
    
    from scurvePlottingUtitilities import plot_noise_vs_trimDAC
    plot_noise_vs_trimDAC(
            vfat=options.vfat, 
            vfatCH=options.strip, 
            fit_filename=options.filename, 
            vfatChNotROBstr=options.channels)
