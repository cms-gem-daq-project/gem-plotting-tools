r"""
``multiprocUtils`` --- Utilities for multiprocessing
============================================================

.. code-block:: python

    import gempython.gemplotting.utils.multiprocUtils

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for analyzing scurve scan data

Documentation
-------------
"""

def redirectStdOutAndErr(callingFunc, outputDir):
    """
    If not the main porcess is not the process that is calling callingFunc
    this will overwrite stdout and stderr to "outputDir/anaLog.log"

    callingFunc - name of function calling this function, used for logging
    outputDir   - Output directory to write stdout and stderr too; note if 
                  outputDir does not exist or is not writeable this will
                  raise an IOError.
    """

    from multiprocessing import current_process
    if (current_process().name != 'MainProcess'):
        import os, sys
        anaLog = open("{0}/anaLog.log".format(outputDir), "w+", buffering=0)
        sys.stdout = anaLog
        sys.stderr = anaLog
        print("{0}() called by process ID: {1}".format(callingFunc, os.getpid()))
        pass

    return
