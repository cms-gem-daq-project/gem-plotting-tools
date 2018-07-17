r"""
``fitScanData`` --- CTP7 information
====================================

.. code-block:: python

    import gempython.gemplotting.mapping.amcInfo

Documentation
-------------
"""

class ctp7Params:
    # Key (shelf,slot); val = eagleXX
    # See: https://twiki.cern.ch/twiki/bin/view/CMS/GEMDAQExpert#List_of_CTP7_s
    cardLocation = {
            (3,2):"eagle26", #QC8
            (3,5):"eagle60",
            (1,3):"eagle33", #P5
            (1,2):"eagle34"} #Coffin
            #(1,?):"eagle64"}
