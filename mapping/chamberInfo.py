r"""
``chamberInfo`` --- Information about installed chambers
========================================================

.. code-block:: python

    import gempython.gemplotting.mapping.chamberInfo

Documentation
-------------
"""

#: Available chambers
"""
Keys should be a tuple of (shelf,slot,link)
"""
chamber_config = {
    #Cosmic Stand
    (1,4,11):"GE11-X-S-CERN-0007",
    (1,4,10):"GE11-X-S-BARI-0006",
    (1,4,6):"GE11-X-S-INDIA-0007",
    (1,4,3):"GE11-X-S-CERN-0009",
    (1,4,2):"GE11-X-S-CERN-0010",
    #Sustained Ops
    (2,5,0):"GE11-X-L-CERN-0002",
    (2,5,1):"GE11-X-S-CERN-0011",
    (2,5,3):"GE11-X-L-GHENT-0002",
    (2,5,4):"GE11-X-S-PAK-0005"     #Update for connectivity testing
    }

"""
Keys should be a tuple of (shelf,slot,link)
"""
GEBtype = {
    ##Cosmic Stand
    (1,4,11):"short",
    (1,4,10):"short",
    (1,4,7):"short",
    (1,4,3):"short",
    (1,4,2):"short",
    #Sustained Ops
    (2,5,0):"long",
    (2,5,1):"short",
    (2,5,3):"long",
    (2,5,4):"short"     #Update for connectivity testing
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
chamber_vfatPos2iEtaiPhi = {}
for ieta, vfatRow in chamber_iEta2VFATPos.iteritems():
    for vfat,phi in vfatRow.iteritems():
        chamber_vfatPos2iEta[vfat] = ieta
        chamber_vfatPos2iEtaiPhi[vfat] = (ieta,phi)
        pass
    pass

"""
Keys should be a tuple of (shelf,slot,link)
"""
chamber_vfatDACSettings = {    
    # V2b Electronics Instructions:
    # For changing VFAT DAC settings from defaults shown in vfat_user_functions.py
    # add a line to this dictionary with the following syntax:
    #    <gtx #>: {"IPreampIn": <val>, "IPreampFeed": <val>, "IPreampOut": <val>, "IShaper": <val>, "IShaperFeed": <val>, "IComp": <val>}
    #
    # V3 Electronics Example
        (1,4,11):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (1,4,10):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (1,4,6):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (1,4,3):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (1,4,2):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (2,5,0):{
            #Latency
            "CFG_LATENCY":43,
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (2,5,1):{
            #Latency
            "CFG_LATENCY":43,
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (2,5,3):{
            #Latency
            "CFG_LATENCY":43,
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
        (2,5,4):{
            #Pulse Stertch
            "CFG_PULSE_STRETCH":3,
            #Ensure the cal pulse is off
            "CFG_CAL_MODE":0,
            #Provide a slight offset to the ZCC comparator baseline voltage
            "CFG_THR_ZCC_DAC":10,
            #High VFAT3 preamp gain
            #"CFG_RES_PRE":1,
            #"CFG_CAP_PRE":0,
            #Medium VFAT3 preamp gain
            "CFG_RES_PRE":2,
            "CFG_CAP_PRE":1,
            #Low VFAT3 preamp gain
            #"CFG_RES_PRE":4,
            #"CFG_CAP_PRE":3,
            #Comparator Mode - CFD
            "CFG_PT":0xf,
            "CFG_FP_FE":0x7,
            "CFG_SEL_COMP_MODE":0,
            "CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ARM
            #"CFG_SEL_COMP_MODE":1,
            #"CFG_FORCE_EN_ZCC":0
            #Comparator Mode - ZCC
            #"CFG_SEL_COMP_MODE":2,
            #"CFG_FORCE_EN_ZCC":1
            },
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
