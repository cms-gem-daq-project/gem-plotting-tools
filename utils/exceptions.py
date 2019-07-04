r"""
``exceptions`` --- gem-plotting-tools specific exceptions
============================================

.. code-block:: python

    import gempython.gemplotting.utils.exceptions

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Exceptions for gem-plotting-tools scripts/macros and vfatqc scans

Documentation
-------------
"""

class VFATDACBiasCannotBeReached(ValueError):
    """
    This exception is raised if DAC analysis determines that to achieve the 
    nominal bias current/voltages in ``nominalDacValues`` dictionary, 
    of: ``gempython.gemplotting.utils.anaInfo``, the DAC would need to be set
    to a value outside of the DAC range ``[0, max]`` where ``max`` is
    ``maxVfat3DACSize[dacSelect][0]``.  Info can be found on these ranges in
    the ``maxVfat3DACSize`` dictionary of: ``gempython.tools.hw_constants``
    """
    def __init__(self, message, errors):
        super(VFATDACBiasCannotBeReached, self).__init__(message)

        self.errors = errors
        return

class DBViewNotFound(KeyError):
    def __init__(self, message, errors):
        super(DBViewNotFound, self).__init__(message)

        self.errors = errors
        return
