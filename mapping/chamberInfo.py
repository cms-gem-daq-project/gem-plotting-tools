chamber_config = {
    #Coffin Setup
    #0:"GE11-VI-L-CERN-0002"
    #Cosmic Stand
    #0:"GE11-VI-L-CERN-0001"
    #Point 5
    0:"GEMINIm01L1",
    1:"GEMINIm01L2",
    2:"GEMINIm27L1",
    3:"GEMINIm27L2",
    4:"GEMINIm28L1",
    5:"GEMINIm28L2",
    6:"GEMINIm29L1",
    7:"GEMINIm29L2",
    8:"GEMINIm30L1",
    9:"GEMINIm30L2"
    }

GEBtype = {
    #Coffin Setup
    #0:"long"
    #Cosmic Stand
    #0:"long"
    #Point 5
    0:"short",
    1:"short",
    2:"short",
    3:"short",
    4:"long",
    5:"long",
    6:"short",
    7:"short",
    8:"long",
    9:"long"
    }

chamber_vfatMask = {
    #Coffin Setup
    #0:0x0
    #Cosmic Stand
    #0:0xF40400
    #Point 5
    0:0x0,
    1:0x0,
    2:0x0,
    3:0x0,
    4:0x0,
    5:0x0,
    6:0x0,
    7:0x0,
    8:0x0,
    9:0x0
    }
   
# Matches CMS coordinates
chamber_iEta2VFATPos = {
        1: { 7:1, 15:2, 23:3 }, #ieta: [ (vfat, iphi), (vfat, iphi), (vfat, iphi) ]
        2: { 6:1, 14:2, 22:3 },
        3: { 5:1, 13:2, 21:3 },
        4: { 4:1, 12:2, 20:3 },
        5: { 3:1, 11:2, 19:3 },
        6: { 2:1, 10:2, 18:3 },
        7: { 1:1,  9:2, 17:3 },
        8: { 0:1,  8:2, 16:3 }
        }

chamber_vfatPos2iEta = {}
for ieta, vfatRow in chamber_iEta2VFATPos.iteritems():
    for vfat,phi in vfatRow.iteritems():
        chamber_vfatPos2iEta[vfat] = ieta
        pass
    pass

chamber_vfatDACSettings = {    
    # V2b Electronics Instructions:
    # For changing VFAT DAC settings from defaults shown in vfat_user_functions.py
    # add a line to this dictionary with the following syntax:
    #    <gtx #>: {"IPreampIn": <val>, "IPreampFeed": <val>, "IPreampOut": <val>, "IShaper": <val>, "IShaperFeed": <val>, "IComp": <val>}
    #
    # V3 Electronics Example
    #    0:{
    #        #Pulse Stertch
    #        "CFG_PULSE_STRETCH":4,
    #        #Ensure the cal pulse is off
    #        "CFG_CAL_MODE":0,
    #        #Set the Latency - 10x10 PMT on R&D Setup
    #        "CFG_LATENCY":98,
    #        #Correct the bug in the shaper
    #        "CFG_PT":3,
    #        #Updated DAC settings from Flavio
    #        "CFG_BIAS_SH_I_BDIFF":150,
    #        "CFG_BIAS_SH_I_BFCAS":250,
    #        "CFG_BIAS_SD_I_BDIFF":255,
    #        "CFG_BIAS_SD_I_BFCAS":255,
    #        #Provide a slight offset to the ZCC comparator baseline voltage
    #        "CFG_THR_ZCC_DAC":10,
    #        #High VFAT3 preamp gain
    #        #"CFG_RES_PRE":1,
    #        #"CFG_CAP_PRE":0,
    #        #Medium VFAT3 preamp gain
    #        "CFG_RES_PRE":2,
    #        "CFG_CAP_PRE":1,
    #        #Low VFAT3 preamp gain
    #        #"CFG_RES_PRE":4,
    #        #"CFG_CAP_PRE":3,
    #        #Comparator Mode - CFD
    #        "CFG_SEL_COMP_MODE":0,
    #        "CFG_FORCE_EN_ZCC":0
    #        #Comparator Mode - ARM
    #        #"CFG_SEL_COMP_MODE":1,
    #        #"CFG_FORCE_EN_ZCC":0
    #        #Comparator Mode - ZCC
    #        #"CFG_SEL_COMP_MODE":2,
    #        #"CFG_FORCE_EN_ZCC":1
    #        },
    #    1:{
    #        #Pulse Stertch
    #        "CFG_PULSE_STRETCH":4,
    #        #Ensure the cal pulse is off
    #        "CFG_CAL_MODE":0,
    #        #Set the Latency - 10x10 PMT on R&D Setup
    #        "CFG_LATENCY":98,
    #        #Correct the bug in the shaper
    #        "CFG_PT":3,
    #        #Updated DAC settings from Flavio
    #        "CFG_BIAS_SH_I_BDIFF":150,
    #        "CFG_BIAS_SH_I_BFCAS":250,
    #        "CFG_BIAS_SD_I_BDIFF":255,
    #        "CFG_BIAS_SD_I_BFCAS":255,
    #        #Provide a slight offset to the ZCC comparator baseline voltage
    #        "CFG_THR_ZCC_DAC":10,
    #        #High VFAT3 preamp gain
    #        #"CFG_RES_PRE":1,
    #        #"CFG_CAP_PRE":0,
    #        #Medium VFAT3 preamp gain
    #        "CFG_RES_PRE":2,
    #        "CFG_CAP_PRE":1,
    #        #Low VFAT3 preamp gain
    #        #"CFG_RES_PRE":4,
    #        #"CFG_CAP_PRE":3,
    #        #Comparator Mode - CFD
    #        "CFG_SEL_COMP_MODE":0,
    #        "CFG_FORCE_EN_ZCC":0
    #        #Comparator Mode - ARM
    #        #"CFG_SEL_COMP_MODE":1,
    #        #"CFG_FORCE_EN_ZCC":0
    #        #Comparator Mode - ZCC
    #        #"CFG_SEL_COMP_MODE":2,
    #        #"CFG_FORCE_EN_ZCC":1
    #        }
    }

# Canvas to VFAT Position Mapping
chamber_vfatPos2PadIdx = { }
for vfat in range(0,24):
    if (0 <= vfat and vfat < 8):
        chamber_vfatPos2PadIdx[vfat] = vfat+17
    elif (8 <= vfat and vfat < 16):
        chamber_vfatPos2PadIdx[vfat] = vfat+1
    elif (16 <= vfat and vfat < 24):
        chamber_vfatPos2PadIdx[vfat] = vfat-15
        pass # end if-elif statement
    pass # end loop over all VFATs
