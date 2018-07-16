Format of ``scandate`` list files
=================================

Many of the macros require a ``listOfScanDates.txt`` file. These come in either
two or three column versions and :py:func:`anautilities.makeListOfScanDatesFile <gempython.gemplotting.utils.anautilities.makeListOfScanDatesFile>` is designed
to parse either version and provide the tool with the correct information. This
means that, baring other command line arguments, the two formats are relatively
interchangeable.

.. contents:: Table of Contents
    :local:

Two Column Format
-----------------

This should be a tab deliminited text file. The first line of this file should
be a list of column headers formatted as:

::

    ChamberName scandate

Subsequent lines of this file are the values that correspond to these column
headings. The value of the ``ChamberName`` column must correspond to the value
of one entry in the :py:data:`chamber_config
<gempython.gemplotting.mapping.chamberInfo.chamber_config>` dictionary. The
next column is for ``scandate`` values. Please note the ``#`` character is
understood as a comment, lines starting with a ``#`` will be skipped.

A complete example for a single detector is given as:

::

    ChamberName scandate
    GE11-VI-L-CERN-0001    2017.08.11.16.30
    GE11-VI-L-CERN-0001    2017.08.14.20.54
    GE11-VI-L-CERN-0001    2017.08.30.15.03
    GE11-VI-L-CERN-0001    2017.08.30.21.39
    GE11-VI-L-CERN-0001    2017.08.31.08.28
    GE11-VI-L-CERN-0001    2017.08.31.15.46
    GE11-VI-L-CERN-0001    2017.09.05.11.41
    GE11-VI-L-CERN-0001    2017.09.12.14.24
    GE11-VI-L-CERN-0001    2017.09.13.16.45

Three Column Format
-------------------

This should be a tab delimited text file. The first line of this file should
be a list of column headers formatted as:

::

    ChamberName scandate    <Indep. Variable Name>

Subsequent lines of this file are the values that correspond to these column
headings. The value of the ``ChamberName`` column must correspond to the value
of one entry in the :py:data:`chamber_config
<gempython.gemplotting.mapping.chamberInfo.chamber_config>` dictionary. The
**Indep. Variable Name** is the independent variable that ``--branchName`` will
be plotted against, if it is not numeric please use the ``--alphaLabels``
command line option. Please note the ``#`` character is understood as a comment,
lines starting with a ``#`` will be skipped.

A complete example for a single detector is given as:

::

    ChamberName scandate    VT_{1}
    GE11-VI-L-CERN-0002 2017.09.04.20.12    10
    GE11-VI-L-CERN-0002 2017.09.04.22.52    20
    GE11-VI-L-CERN-0002 2017.09.05.01.33    30
    GE11-VI-L-CERN-0002 2017.09.05.04.21    40
    GE11-VI-L-CERN-0002 2017.09.05.07.11    50

Here the ChamberName is always ``GE11-VI-L-CERN-0002`` and ``--branchName`` will
be plotted against ``VT_{1}`` which is the **Indep. Variable Name**. Note the
axis of interest will be assigned the label, with subscripts in this case, of
``VT_{1}``.

A complete example for multiple detectors is given as:

::

    ChamberName scandate    Layer
    GEMINIm27L1 2019.09.04.20.12    GEMINIm27L1
    GEMINIm27L2 2019.09.04.22.52    GEMINIm27L2
    GEMINIm28L1 2019.09.05.01.33    GEMINIm28L1
    GEMINIm28L2 2019.09.05.04.21    GEMINIm28L2
    GEMINIp02L1 2019.09.05.07.11    GEMINIp02L1
    GEMINIp02L2 2019.09.05.07.11    GEMINIp02L2

Here the ``ChamberName`` is different for each line and ``--branchName`` will be
plotted against ``Layer``. Note since the **Indep. Variable Name** is not
numeric the command line option ``--alphaLabels`` must be used.

Automatically generating sets of ``listOfScanDates.txt``
--------------------------------------------------------

To automatically generate a set of ``listOfScanDates.txt`` files for all S-curve
measurements for each of the chambers defined in the keys of
:py:data:`chamber_config
<gempython.gemplotting.mapping.chamberInfo.chamber_config>`, execute:

::

    plotTimeSeries.py --listOfScanDatesOnly --startDate=2017.01.01

For each detector defined in the keys of :py:data:`chamber_config
<gempython.gemplotting.mapping.chamberInfo.chamber_config>`, the
``listOfScanDAtes.txt`` file will be found at:

::

    $DATA_PATH/<ChamberName>/scurve/

If you are interested in generating a set of ``listOfScanDates.txt`` files for
measurements other than S-curves, supply the ``--anaType`` argument at the time
of execution like:

::

    plotTimeSeries.py --listOfScanDatesOnly --startDate=2017.01.01 --anaType=<type>

The list of supported ``anaType``'s are from the keys of the keys of :py:data:`chamber_config
<gempython.gemplotting.mapping.chamberInfo.chamber_config>`. In this case the ``listOfScanDAtes.txt`` file for each chamber will be found at:

::

    $DATA_PATH/<ChamberName>/<anaType>/
