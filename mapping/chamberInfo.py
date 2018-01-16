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
    
chamber_vfatDACSettings = {    
    # For changing VFAT DAC settings from defaults shown in vfat_user_functions.py
    # add a line to this dictionary with the following syntax:
    #    <gtx #>: {"IPreampIn": <val>, "IPreampFeed": <val>, "IPreampOut": <val>, "IShaper": <val>, "IShaperFeed": <val>, "IComp": <val>}
        0:{
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Correct the bug in the shaper
            "CFG_PT":3,
            #Updated DAC settings from Flavio
            "CFG_BIAS_SH_I_BDIFF":150,
            "CFG_BIAS_SH_I_BFCAS":250,
            "CFG_BIAS_SD_I_BDIFF":255,
            "CFG_BIAS_SD_I_BFCAS":255,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Comparator Mode - CFD
            #"CFG_SEL_COMP_MODE":0,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            "CFG_SEL_COMP_MODE":1,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            }
    }
