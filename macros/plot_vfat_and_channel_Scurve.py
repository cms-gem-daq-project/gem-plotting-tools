#!/bin/env python

if __name__ == '__main__':
    import gempython.gemplotting as gemplotting
    
    from gemplotting.macros.plotoptions import parser
    (options, args) = parser.parse_args()
    
    from gemplotting.macros.scurvePlottingUtitilities import overlay_scurve
    overlay_scurve(
            vfat=options.vfat, 
            vfatCH=options.strip, 
            fit_filename=options.filename, 
            vfatChNotROBstr=options.channels)
