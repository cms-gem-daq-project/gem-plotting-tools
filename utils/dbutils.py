from gempython.utils.gemlogger import getGEMLogger, printYellow
from gempython.utils.wrappers import envCheck

import pandas as pd

knownViews = [
        'GEM_SUPRCHMBR_VFAT_VIEW',
        #'GEM_VFAT2_CHIP_CONF_V_RH',
        'GEM_VFAT3_CHIP_CONF_V_RH',
        'GEM_VFAT3_PROD_SUMMARY_V_RH'
        ]

def getGEMDBView(view, vfatList=None, debug=False):
    """
    Gets the GEM DB view defined by view for the list of vfats provided by vfatList, or
    if no vfatList is provided the full view stored in the DB.

    Returns a pandas dataframe object storing the data read from the DB

    view        - Name of View to retrieve from GEM DB 
    vfatList    - list of VFAT Chip ID's, if None the full view is retrieved
    debug       - Prints additional info if true
    """

    # Check to make sure DB $ENV variables exist
    envCheck("GEM_ONLINE_DB_NAME")
    envCheck("GEM_ONLINE_DB_CONN")

    import os
    if view not in knownViews:
        raise Exception("View {0} not in knownViews: {1}".format(view,knownViews),os.EX_USAGE)

    # Make base query
    query='select * from CMS_GEM_MUON_VIEW.{0} data'.format(view)
    
    # Add a filter on VFAT serial number?
    if vfatList is not None:
        query += getVFATFilter(vfatList)
        pass

    # get a pandas data frame object containing the db query
    dbName = os.getenv("GEM_ONLINE_DB_NAME")
    dbConn = os.getenv("GEM_ONLINE_DB_CONN")
    dfGEMView = pd.read_sql(query, con=(dbConn+dbName))

    if debug:
        dfGEMView.info()
        print("Read {0} rows from view {1}".format(dfGEMView.shape[0],view))
        pass

    if vfatList is not None:
        # First warn the user which VFATs are *not* found
        if len(vfatList) != dfGEMView.shape[1]:
            printYellow("Length of returned view does not match length of input vfat List")
            vfatsNotFound = [ "0x{:x}".format(chipId) for chipId in vfatList if "0x{:x}".format(chipId) not in list(dfGEMView['vfat3_ser_num'])]
            printYellow("VFATs not found: {0}".format(vfatsNotFound))
            pass
        
        # Then add a 'vfatN' column to the output df; this increases row # to len(vfatList)
        dfGEMView = joinOnVFATSerNum(vfatList,df_gemView)
        
        pass

    return dfGEMView

def getVFAT3CalInfo(vfatList, debug=False):
    """
    Gets from GEM_VFAT3_PROD_SUMMARY_V_RH view a subset of data that is necessary
    for VFAT calibration.  Specifically a pandas dataframe will be returned with
    only the following columns:

        ['vfatN','vfat3_ser_num', 'vfat3_barcode', 'iref', 'adc0m', 'adc1m', 'adc0b', 'adc1b', 'cal_dacm', 'cal_dacb']

    vfatList    - list of VFAT Chip ID's.
    debug       - Prints additional info if true
    """

    df_vfatCalInfo = getVFAT3ProdSumView(vfatList, debug)

    return df_vfatCalInfo[['vfatN','vfat3_ser_num', 'vfat3_barcode', 'iref', 'adc0m', 'adc1m', 'adc0b', 'adc1b', 'cal_dacm', 'cal_dacb']]

def getVFAT3ConfView(vfatList, debug=False):
    """
    Gets the GEM_VFAT3_CHIP_CONF_V_RH view in the GEM DB for a list of input VFATs.

    Returns a pandas dataframe object storing the data read from the DB

    vfatList    - list of VFAT Chip ID's.
    debug       - Prints additional info if true
    """

    return getGEMDBView("GEM_VFAT3_CHIP_CONF_V_RH",vfatList,debug)

def getVFAT3ProdSumView(vfatList, debug=False):
    """
    Gets the GEM_VFAT3_PROD_SUMMARY_V_RH view in the GEM DB for a list of input VFATs.

    Returns a pandas dataframe object storing the data read from the DB

    vfatList    - list of VFAT Chip ID's.
    debug       - Prints additional info if true
    """

    return getGEMDBView("GEM_VFAT3_PROD_SUMMARY_V_RH",vfatList,debug)

def getVFATFilter(vfatList):
    """
    Returns a string that can be used as a filter in an SQL query.

    vfatList - list of VFAT Chip ID's
    """

    strRetFilter = " WHERE ("
    for idx, vfatID in enumerate(vfatList):
        if idx == 0:
            strRetFilter += " data.VFAT3_SER_NUM='0x{:x}'".format(vfatID)
        else:
            strRetFilter += " OR data.VFAT3_SER_NUM='0x{:x}'".format(vfatID)
            pass
        pass
    strRetFilter += " )\n"

    return strRetFilter

def joinOnVFATSerNum(vfatList, dfGEMView):
    """
    Creates a dataframe object from vfatList with keys 'vfat3_ser_num' and 'vfatN'.
    Then it joins this dataframe with dfGEMView using the 'vfat3_ser_num'.

    vfatList - A list of vfat ChipID's ordered by vfat position (sw)
    dfGEMView - A pandas dataframe containing the column name 'vfat3_ser_num'
    """

    if 'vfat3_ser_num' in dfGEMView.columns:
        dfVFATPos = pd.DataFrame(
                    {   'vfatN':[vfat for vfat in range(24)], 
                        'vfat3_ser_num':["0x{:x}".format(id) for id in vfatList]}
                )

        dfGEMView = pd.merge(dfVFATPos, dfGEMView, on='vfat3_ser_num', how='outer')
    else:
        printYellow("column 'vfat3_ser_num' not in input dataframe columns: {0}".format(dfGEMView.columns))
        pass

    return dfGEMView
