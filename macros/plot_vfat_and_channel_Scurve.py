if __name__ == '__main__':
    from macros.plotoptions import parser
    
    (options, args) = parser.parse_args()
    
    from anautilities import overlay_scurve
    overlay_scurve(
            vfat=options.vfat, 
            vfatCH=options.strip, 
            fit_filename=options.filename, 
            vfatChNotROBstr=options.channels)
