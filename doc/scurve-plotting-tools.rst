S-curve plotting tools
======================

The following tools exist for helping to understand scurve data:

1. :doc:`gemSCurveAnaToolkit.py </man/gemSCurveAnaToolkit>`
2. :program:`plot_noise_vs_trim.py`
3. :program:`plot_vfat_and_channel_Scurve.py`
4. :program:`plot_vfat_summary.py`
5. :program:`summary_plots.py`

These tools can all by found in the ``macros/`` subdirectory and are designed to
be run on ``TFile`` objects containing the ``scurveFitTree`` ``TTree`` object
(e.g. produced by :program:`anaUltraScurve.py`).  The first tool
:program:`gemSCurveAnaToolkit.py` is for plotting the same (vfat,channel/ROBstr)
scurve from a list of scandates and it is described in a dedicated subsection
below. The rest of the tools above are for making plots from a single input
file; the plots made by tools 2-4 are:

- :program:`plot_noise_vs_trim.py`: Plots a channel/strip's scurve width (e.g.
  ``noise``) vs. trimDAC as a ``TH2D`` on a ``TCanvas``,
- :program:`plot_vfat_and_channel_Scurve.py`: Plots a channel/strip's scurve as a
  ``TH1D`` and its ``TF1`` on a ``TCanvas``, and
- :program:`plot_vfat_summary.py`: Plots all scurves from a given VFAT as a ``TH2D`` on
  a ``TCanvas``.

Tool 5 :program:`summary_plots.py` produces the following plots from a single
input file for a given VFAT depending on the command line argument supplied:

- Plot of channel/strip scurve mean as a ``TH1D``,
- Plot of channel/strip scurve width as a ``TH1D``,
- Plot of channel/strip scurve pedestal as a ``TH1D``,
- Plot of Chi<sup>2</sup> of the channel/strip scurve fits as a ``TH1D``,
- Plot of channel/strip scurve mean vs. scurve width as a ``TH2D``, and
- Plot of channel/strip scurve width vs. trimDAC as a ``TH2D``.

The command line options for tools 2-5 are:

.. option:: -c, --channels

    Make plots vs VFAT channels instead of ROB strips.

.. option:: -i, --infilename <FILE>

    Physical filename of the input file.  Note this must be a ``TFile`` which
    contains the ``scurveFitTree`` ``TTree`` object.

.. option:: -s, --strip <STRIP OR CHANNEL>

    If the :token:`-c` option is (not) supplied this will be the VFAT channel
    (ROB strip) the plot will be made for.

.. option:: -v, --vfat <VFAT>

    The VFAT to plot.

Additionally tool 5 :program:`summary_plots.py` has the following additional
command line options:

.. option:: -a, --all

    Equivalent to supplying :token:`-f` and :token:`-x` options.

.. option:: -f, --fit

    Make fit parameter plots.

.. option:: -x, --chi2

    Make Chi2 plots.

Note that for tool 5 :program:`summary_plots.py` you must supply at least one of
these additional options :token:`-a`, :token:`-f` or :token:`-x`.
