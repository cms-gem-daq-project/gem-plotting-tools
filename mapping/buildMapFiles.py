import os

from gempython.gemplotting.mapping.channelMaps import *
from gempython.gemplotting.mapping.PanChannelMaps import *

from gempython.utils.wrappers import envCheck
envCheck('GEM_PLOTTING_PROJECT')

import pkg_resources
MAPPING_PATH = pkg_resources.resource_filename('gemplotting', 'mapping/')
mapPath  = "%s/mapping"%(MAPPING_PATH)

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
