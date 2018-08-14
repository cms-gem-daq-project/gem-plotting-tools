Algorithmic channel masking
===========================

"Bad" channels can be masked to prevent them from sending spurious data. We have
certain criteria to declare a channel "bad", described by
:py:class:`MaskReason <gempython.gemplotting.utils.anaInfo.MaskReason>`, whose
documentation is copied below for convenience:

.. autoclass:: gempython.gemplotting.utils.anaInfo.MaskReason
    :noindex:

The following table lists the meaning of bits in a ``maskReason``:

=========== =========== ========================================================
Name        Bit         Reason
=========== =========== ========================================================
NotMasked   (none set)  The channel is not masked.
HotChannel  0           The channel was identified as an outlier using the MAD algorithm
FitFailed   1           The S-curve fit of the channel failed.
DeadChannel 2           The channel has a burned or disconnected input.
HighNoise   3           The channel has an S-curve sigma above the cut value.
HighEffPed  4           The channel has an effective pedestal above the cut value.
=========== =========== ========================================================

The following definitions are used in the context of channel masking:

S-curve sigma
    The ``sigma`` of the modified error function used to fit the S-curve
    measurements. It comes from the ``TF1`` object used to fit S-curves in
    :py:meth:`ScanDataFitter.fit <gempython.gemplotting.fitting.ScanDataFitter.fit>`.

Effective pedestal
    The fraction of time a channel's comparator fires when injected charge is
    zero. This is determined from an S-curve measurement via:

    .. code-block:: python

        effPed = scurve_fit_func.Eval(0) / n_pulses,

    where ``n_pulses`` are the number of charge injections for a given DAC value
    performed by the calibration module.

Deriving channel configuration
------------------------------

The following procedure is used, note these steps must be executed one after
another, without LV power cycle or action to cause a reset of the VFAT settings
(e.g. SCA reset):

======= ===================================================== ========= ==================================================== ======
Step    Tool ``v2b`` (``v3``)                                 VFAT Data Input Config                                         Generates
======= ===================================================== ========= ==================================================== ======
1       ``trimChamber.py`` (``trimChamberV3.py``)             Tracking  ``VThreshold1 (CFG_THR_ARM_DAC) = 100, ztrim=4``     Initial channel configuration ``chConfig.txt`` and ``trimRange`` settings.
2       ``confChamber.py``                                    N/A       ``chConfig.txt``, ``trimRange in memory``            Nothing
3       ``ultraThreshold.py``                                 Tracking  Nothing                                              Updated channel config ``chConfig_MasksUpdated.txt`` and initial VFAT settings storing VThreshold1 and trimRange in vfatConfig.txt.
4       ``confChamber.py``                                    N/A       ``chConfig_MasksUpdated.txt`` and ``vfatConfig.txt`` Nothing
5       ``ultraThreshold.py`` (``sbitThreshScanParallel.py``) Trigger   Nothing                                              Updated VFAT settings ``vfatConfig_Updated.txt`` with final ``VThreshold1`` values.
======= ===================================================== ========= ==================================================== ======

Please note that while ``DeadChannel`` is given in ``maskReason``, these
channels are never masked such that they can be tracked over time.

If a channel was masked at the time of acquisition of a test involving an
S-curve measurement (e.g. ``trimChamber(V3).py`` or ``ultraScurve.py``), it will
be assigned the ``FitFailed`` reason since the original reason is not known
without referencing a previous scan.

Providing cuts for ``maskReason`` at runtime
--------------------------------------------

When analyzing the above S-curves taken by ``trimChamber(V3).py``, the following
command line arguments are available for specifying the cut values for assigning
the ``DeadChannel``, ``HighNoise``, and ``HighEffPed`` pedestal:

.. option:: --maxEffPedPercent <NUMBER>

    Value from 0 to 1. Threshold for setting the ``HighEffPed`` mask reason, if
    channel ``effPed > maxEffPedPercent * nevts`` then ``HighEffPed`` is set.

.. option:: --highNoiseCut <NUMBER>

    Threshold for setting the ``HighNoise`` ``maskReason``, if channel
    ``scurve_sigma > highNoiseCut`` then ``HighNoise`` is set.

.. option:: --deadChanCutLow <NUMBER>

    If channel ``deadChanCutLow < scurve_sigma < deadChanCutHigh`` then
    ``DeadChannel`` is set, see slide 22 of `this talk`_ for the origin of the
    default values in fC (VFAT 2 only, values for VFAT 3 coming soon).

.. option:: --deadChanCutHigh <NUMBER>

    If channel ``deadChanCutHigh < scurve_sigma < deadChanCutHigh`` then
    ``DeadChannel`` is set, see slide 22 of `this talk`_ for the origin of the
    default values in fC (VFAT 2 only, values for VFAT 3 coming soon).

.. _this talk: https://indico.cern.ch/event/721622/contributions/2968019/attachments/1631961/2602748/BDorney_GEMDAQMtg_20180412_BurnedVFATInputs.pdf
