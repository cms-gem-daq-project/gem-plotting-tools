import os
from mapping.channelMaps import *
from mapping.PanChannelMaps import *

from gempython.utils.wrappers import envCheck
envCheck('GEM_PLOTTING_PROJECT')

mapPath  = "%s/mapping"%(os.getenv('GEM_PLOTTING_PROJECT'))

chamberType = ['long','short']
for cT in chamberType:
    outF = open('%s/%sChannelMap.txt'%(mapPath,cT),'w')
    outF.write('vfat/I:strip/I:channel/I:PanPin/I\n')
    for vfat in range(0,24):
        for strip in range(0,128):
            channel = stripToChannel(cT,vfat,strip)
            panpin = StripToPan(cT, vfat, strip)
            outF.write('%i\t%i\t%i\t%i\n'%(vfat,strip,channel+1,panpin))
            pass
        pass
    outF.close()
    pass
