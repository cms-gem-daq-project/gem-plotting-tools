# gem-plotting-tools

Branch|[Travis CI](https://travis-ci.org)|[Coveralls](https://www.coveralls.io)|[Codecov](https://www.codecov.io)|[Codacy](https://www.codacy.com)|[Landscape](https://www.landscape.io)|[CodeClimate](https://www.codeclimate.com)
---|---|---|---|---|---|---
master|[![Build Status](https://travis-ci.org/cms-gem-daq-project/gem-plotting-tools.svg?branch=master)](https://travis-ci.org/cms-gem-daq-project/gem-plotting-tools)|[![Coveralls Status](https://coveralls.io/repos/github/cms-gem-daq-project/gem-plotting-tools/badge.svg?branch=master)](https://coveralls.io/github/cms-gem-daq-project/gem-plotting-tools?branch=master)|[![codecov](https://codecov.io/gh/cms-gem-daq-project/gem-plotting-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/cms-gem-daq-project/gem-plotting-tools)|[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b81a9dc9270248b6b66155511369bec5)](https://www.codacy.com/app/cms-gem-daq-project/gem-plotting-tools?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cms-gem-daq-project/gem-plotting-tools&amp;utm_campaign=Badge_Grade)|[![Landscape Status](https://landscape.io/github/cms-gem-daq-project/gem-plotting-tools/master/landscape.svg)](https://landscape.io/github/cms-gem-daq-project/gem-plotting-tools/master)|[![Code Climate](https://codeclimate.com/github/cms-gem-daq-project/gem-plotting-tools/badges/gpa.svg)](https://codeclimate.com/github/cms-gem-daq-project/gem-plotting-tools)
develop|[![Build Status](https://travis-ci.org/cms-gem-daq-project/gem-plotting-tools.svg?branch=develop)](https://travis-ci.org/cms-gem-daq-project/gem-plotting-tools)|[![Coveralls Status](https://coveralls.io/repos/github/cms-gem-daq-project/gem-plotting-tools/badge.svg?branch=develop)](https://coveralls.io/github/cms-gem-daq-project/gem-plotting-tools?branch=develop)|[![codecov](https://codecov.io/gh/cms-gem-daq-project/gem-plotting-tools/branch/develop/graph/badge.svg)](https://codecov.io/gh/cms-gem-daq-project/gem-plotting-tools)|[![Codacy Badge](https://api.codacy.com/project/badge/Grade/00f0de54bcc94812b553ebeab74e9320)](https://www.codacy.com/app/cms-gem-daq-project/gem-plotting-tools?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cms-gem-daq-project/gem-plotting-tools&amp;utm_campaign=Badge_Grade)|[![Landscape Status](https://landscape.io/github/cms-gem-daq-project/gem-plotting-tools/develop/landscape.svg)](https://landscape.io/github/cms-gem-daq-project/gem-plotting-tools/develop)|[![Code Climate](https://codeclimate.com/github/cms-gem-daq-project/gem-plotting-tools/badges/issue_count.svg)](https://codeclimate.com/github/cms-gem-daq-project/gem-plotting-tools)


Table of Contents
=================

   * [gem-plotting-tools](#gem-plotting-tools)
      * [Setup:](#setup)
      * [Analyzing Scans:](#analyzing-scans)
         * [Analyzing Python Ultra Scan Data](#analyzing-python-ultra-scan-data)
            * [plot_eff.py](#plot_effpy)
            * [plot_eff.py Arguments](#plot_effpy-arguments)
            * [plot_eff.py Input File](#plot_effpy-input-file)
            * [plot_eff.py Example](#plot_effpy-example)
         * [Analyzing xDAQ Scan Data](#analyzing-xdaq-scan-data)
      * [Arbitray Plotting Tools](#arbitray-plotting-tools)
         * [gemPlotter.py](#gemplotterpy)
            * [gemPlotter.py Arguments](#gemplotterpy-arguments)
            * [gemPlotter.py Input File](#gemplotterpy-input-file)
            * [gemPlotter.py Example: Making a 1D Plot - Channel Level](#gemplotterpy-example-making-a-1d-plot---channel-level)
            * [gemPlotter.py Example: Making a 1D Plot - VFAT Level](#gemplotterpy-example-making-a-1d-plot---vfat-level)
            * [gemPlotter.py Example: Making a 2D Plot](#gemplotterpy-example-making-a-2d-plot)
         * [gemTreeDrawWrapper.py](#gemtreedrawwrapperpy)
            * [gemTreeDrawWrapper.py Arguments](#gemtreedrawwrapperpy-arguments)
            * [gemTreeDrawWrapper.py Input File](#gemtreedrawwrapperpy-input-file)
            * [gemTreeDrawWrapper.py Example: Making a Plot](#gemtreedrawwrapperpy-example-making-a-plot)
            * [gemTreeDrawWrapper.py Example: Fitting a Plot](#gemtreedrawwrapperpy-example-fitting-a-plot)
      * [Scurve Plotting Tools](#scurve-plotting-tools)
         * [gemSCurveAnaToolkit.py](#gemscurveanatoolkitpy)
            * [gemSCurveAnaToolkit.py Arguments](#gemscurveanatoolkitpy-arguments)
            * [gemSCurveAnaToolkit.py Input File](#gemscurveanatoolkitpy-input-file)
            * [gemSCurveAnaToolkit.py Example: Making a Plot](#gemscurveanatoolkitpy-example-making-a-plot)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)

## Setup:
The following `$SHELL` variables should be defined:

- `$BUILD_HOME`
- `$DATA_PATH`
- `$ELOG_PATH`

Then execute:

```
source $BUILD_HOME/gem-plotting-tools/setup/paths.sh
```

## Analyzing Scans:
Analysis is broken down into either analyzing data taken with the python ultra scan tools or with xdaq.

### Analyzing Python Ultra Scan Data
The following tools exist to help you to analyze scans taken with the ultra tools in the [vfatqc-python-scripts](https://github.com/cms-gem-daq-project/vfatqc-python-scripts) repository:

- `ana_scans.py`,
- `anaUltraLatency.py`,
- `anaUltraScurve.py`, and
- `anaUltraThreshold.py`.

See extensive documentation written on the [GEM DOC Twiki Page](https://twiki.cern.ch/twiki/bin/view/CMS/GEMDOCDoc#How_to_Produce_Scan_Plots).

#### plot_eff.py
For some test stands where you have configured the input L1A to pass only through a specific point of a detector you can use the data taken by `ultraLatency.py` to calculate the efficiency of the detector.  To help you perform this analysis the `plot_eff.py` tool has been created.

#### plot_eff.py Arguments
The following table shows the mandatory inputs that must be supplied to execute the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| ` --latSig` | int | Latency bin for which efficiency should be determined from. |
| `-i`, `--infilename` | string | physical filename of the input file to be passed to `plot_eff.py`.  The format of this input file is the same as for the `gemPlotter.py` tool, see [gemPlotter.py Input File](#gemplotterpy-input-file) for more details. |
| `-p`, `--print` | none | Prints a comma separated table of the plot's data to the terminal.  The format of this table will be compatible with the `genericPlotter` executable of the [CMS_GEM_Analysis_Framework](https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#3b-genericplotter). | 
| `-v`, `--vfat` | int | Specify VFAT to use when calculating the efficiency. |

The following table shows the optional inputs that can be supplied when executing the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| ` --bkgSub` | none | Background subtraction is used to determine the efficiency instead of a single latency bin. May be used instead of the `--latSig` option. |
| `--vfatList` | Comma separated list of int's | List of VFATs to use when calculating the efficiency.  May be used instead of the `--vfat` option. |

Note if the `--bkgSub` option is used then you **must** first call `anaUltraLatency.py` for each of the scandates given in the `--infilename`.

#### plot_eff.py Input File
The format of this input file is the same as for the `gemPlotter.py` tool, see [gemPlotter.py Input File](#gemplotterpy-input-file) for more details.

#### plot_eff.py Example
To calculate the efficiency using VFATs 12 & 13 in latency bin 39 for a list of scandates defined in `listOfScanDates.txt` call:

```
plot_eff.py --infilename=listOfScanDates.txt --vfatList=12,13 --latSig=39 --print
```

To calculate the efficiency using VFAT4 using background subtraction first call `anaUltraLatency.py` on each of the scandates given in `listOfScanDates.txt` and then call:

```
plot_eff.py --infilename=listOfScanDates.txt -v4 --bkgSub --print
```

### Analyzing xDAQ Scan Data
The following tools exist to help you to analyze scans taken with xDAQ:

- `anaXDAQLatency.py`

See documentation written on the [GEM DOC Twiki Page](https://twiki.cern.ch/twiki/bin/viewauth/CMS/GEMDOCDoc#How_to_Produce_Scan_Plots_Ta_AN1).

## Arbitray Plotting Tools
There are two tools for helping you to make arbitrary plots from python scan data:

- `gemPlotter.py`
- `gemTreeDrawWrapper.py`

The first tool is for plotting from multiple different scandates. The second tool is for making a given plot from a list of scandates, for each scandate.

### gemPlotter.py
The `gemPlotter.py` tool is for making plots of an observable stored in one of the `TTree` objects produced by the (ana-) ultra scan scripts vs an arbitrary indepdent variable specified by the user.  Here each data point is from a different scandate.  This is useful if you run mulitple scans in which only a single parameter is changed (e.g. applied high voltage, or `VThreshold1`) and you want to track the dependency on this parameter.

Each plot produced will be stored as an output `*.png` file. Additionally an output `TFile` will be produced which will contain each of the plots, stored as `TGraph` objects, and canvases produced.

#### gemPlotter.py Arguments
The following table shows the mandatory inputs that must be supplied to execute the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `--anaType` | string | Analysis type to be executed, see `tree_names.keys()` of [anaInfo.py](https://github.com/cms-gem-daq-project/gem-plotting-tools/blob/master/anaInfo.py) for possible inputs |
| `--branchName` | string | Name of TBranch where dependent variable is found, note that this TBranch should be found in the `TTree` that corresponds to the value given to the `--anaType` argument |
| `-i`, `--infilename` | string | physical filename of the input file to be passed to `gemPlotter.py`.  See [gemPlotter.py Input File](#gemplotterpy-input-file) for details on the format and contents of this file. |
| `-v`, `--vfat` | int | Specify VFAT to plot |

Note for those `anaType` values which have the substring `Ana` in their names it is expected that the user has already run `ana_scans.py` on the corresponding `scandate` to produce the necessary input file for `gemPlotter.py`.

The following table shows the optional inputs that can be supplied when executing the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `-a`, `--all` | none | When providing this flag data from all 24 VFATs will be plotted.  Additionally a summary plot in the typical 3x8 grid will be created showing the results of all 24 VFATs. May be used instead of the `--vfat` option. |
| `--alphaLabels` | none | When providing this flag `gemPlotter.py` will interpret the **Indep. Variable** as a string and modify the output X axis accordingly |
| `--axisMax` | float | Maximum value for the axis depicting `--branchName`. |
| `--axisMin` | float | Minimum value for the axis depicting `--branchName`. |
| `-c`, `--channels` | none | When providing this flag the `--strip` option is interpreted as VFAT channel number instead of readout board (ROB) strip number. |
| `-s`, `--strip` | int | Specific ROB strip number to plot for `--branchName`.  Note for ROB strip level `--branchName` values (e.g. `trimDAC`) if this option is *not* provided the data point (error bar) will represent the mean (standard deviation) of `--branchName` from all strips. |
| `--make2D` | none| When providing this flag a 2D plot of ROB strip/vfat channel vs. independent variable will be plotted whose z-axis value is `--branchName`. |
| `-p`, `--print` | none | Prints a comma separated table of the plot's data to the terminal.  The format of this table will be compatible with the `genericPlotter` executable of the [CMS_GEM_Analysis_Framework](https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#3b-genericplotter). | 
| `--rootOpt` | string | Option for creating the output `TFile`, e.g. {'RECREATE','UPDATE'} |
| `--showStat` | none | Causes the statistics box to be drawn on created plots. Note only applicable when used with `--make2D`. |
| `--vfatList` | Comma separated list of int's | List of VFATs that should be plotted.  May be used instead of the `--vfat` option. |
| `--ztrim` | int | The ztrim value that was used when running the scans listed in `--infilename` |

#### gemPlotter.py Input File
This should be a `tab` deliminited text file.  The first line of this file should be a list of column headers formatted as:

```
ChamberName scandate    <Indep. Variable Name>
```

Subsequent lines of this file are the values that correspond to these column headings.  The value of the `ChamberName` column must correspond to the value of one entry in the `chamber_config` dictionary found in [mapping/chamberInfo.py](https://github.com/cms-gem-daq-project/gem-plotting-tools/blob/master/mapping/chamberInfo.py).  The **Indep. Variable Name** is the independent variable that `--branchName` will be plotted against, if it is *not* numeric please use the `--alphaLabels` command line option.  Please note the `#` character is  understood as a comment, lines starting with a `#` will be skipped.

A complete example for a single detector is given as:

```
ChamberName scandate    VT_{1}
GE11-VI-L-CERN-0002 2017.09.04.20.12    10
GE11-VI-L-CERN-0002 2017.09.04.22.52    20
GE11-VI-L-CERN-0002 2017.09.05.01.33    30
GE11-VI-L-CERN-0002 2017.09.05.04.21    40
GE11-VI-L-CERN-0002 2017.09.05.07.11    50
```

Here the `ChamberName` is always `GE11-VI-L-CERN-0002` and `--branchName` will be plotted against `VT_{1}` which is the **Indep. Variable Name**.  Note the axis of interest will be assigned the label, with subscripts in this case, of `VT_{1}`.

A complete example for multiple detectors is given as:

```
ChamberName scandate    Layer
GEMINIm27L1 2019.09.04.20.12    GEMINIm27L1
GEMINIm27L2 2019.09.04.22.52    GEMINIm27L2
GEMINIm28L1 2019.09.05.01.33    GEMINIm28L1
GEMINIm28L2 2019.09.05.04.21    GEMINIm28L2
GEMINIp02L1 2019.09.05.07.11    GEMINIp02L1
GEMINIp02L2 2019.09.05.07.11    GEMINIp02L2
```

Here the `ChamberName` is different for each line and `--branchName` will be plotted against `Layer`.  Note since the **Indep. Variable Name** is not numeric the command line option `--alphaLabels` must be used.

#### gemPlotter.py Example: Making a 1D Plot - Channel Level
To make a 1D plot for a given strip of a given VFAT execute:

```
gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.> --strip=<Strip No.>
```

For example, to plot `trimDAC` vs. an **Indep. Variable Name** defined in `listOfScanDates.txt` for VFAT 12, strip number 49 execute:

```
gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimDAC --vfat=12 --strip=49
```

Additional VFATs could be plotted by either:
- Making successive calls of the above command and using the `--rootOpt=UPDATE`,
- Using the `--vfatList` argument instead of the `--vfat` argument, or
- Using the `-a` argument to make all VFATs.

#### gemPlotter.py Example: Making a 1D Plot - VFAT Level
To make a 1D plot for a given VFAT execute:

```
gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.> 
```

For example, to plot `trimRange` vs. an **Indep. Variable Name** defined in `listOfScanDates.txt` for VFAT 12 execute:

```
gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimRange --vfat=12
```

Note if **TBranch Name** is a strip level observable the data points (y-error bars) in the produced plot will represent the mean (standard deviation) from all of the VFAT's channels.

Additional VFATs could be plotted by either:
- Making successive calls of the above command and using the `--rootOpt=UPDATE`,
- Using the `--vfatList` argument instead of the `--vfat` argument, or
- Using the `-a` argument to make all VFATs.

To automatically extend this to all channels execute:

```
gemPlotterAllChannels.sh <InFile> <anaType> <branchName>
```

#### gemPlotter.py Example: Making a 2D Plot
To make a 2D plot for a given VFAT execute:

```
gemPlotter.py --infilename=<inputfilename> --anaType=<anaType> --branchName=<TBranch Name> --vfat=<VFAT No.> --make2D
```

Here the output plot will be of the form "ROB Strip/VFAT Channel vs. Indep. Variable Name" with the z-axis storing the value of `--branchName`.

For example to plot `trimDAC` for "ROB Strip vs. Indep. Variable Name" wher
For example to make a 2D plot with the z-axis as `trimDAC` and the **Indep. Variable Name** defined in `listOfScanDates.txt` for VFAT 12 execute:

```
gemPlotter.py -ilistOfScanDates.txt --anaType=trimAna --branchName=trimDAC --vfat=12 --make2D 
```

Additional VFATs could be plotted by either:
- Making successive calls of the above command and using the `--rootOpt=UPDATE`,
- Using the `--vfatList` argument instead of the `--vfat` argument, or
- Using the `-a` argument to make all VFATs.

### gemTreeDrawWrapper.py
The `gemTreeDrawWrapper.py` tool is for making a given 'Y vs. X' plot for each scandate of interest.  Here *Y* and *X* are quantities stored in `TBranches` of one of the `TTree` objects procued by the (ana-) ultra scan scripts.  This is designed to complement `gemPlotter.py` and should speed up plotting in general.  This tool is essesntially a wrapper for the `TTree::Draw()` method.  To make full use of this tool you should familiarize yourself with the `TTree::Draw()` [documentation](https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45).

Additionally `gemTreeDrawWrapper.py` can also fit produced plots with a function defined at runtime through the command line arguments.

Each plot produced will be stored as an output `*.png` file. Additionally an output `TFile` will be produced which will contain each of the plots, stored as `TGraph` objects, canvases, and fits produced. 

#### gemTreeDrawWrapper.py Arguments
The following table shows the mandatory inputs that must be supplied to execute the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `--anaType` | string | Analysis type to be executed, see `tree_names.keys()` of [anaInfo.py](https://github.com/cms-gem-daq-project/gem-plotting-tools/blob/master/anaInfo.py) for possible inputs |
| `-i`, `--infilename` | string | physical filename of the input file to be passed to `gemTreeDrawWrapper.py`.  See [gemTreeDrawWrapper.py Input File](#gemtreedrawwrapperpy-input-file) for details on the format and contents of this file. |
| `--treeExpress` | string | Expression to be drawn, corresponds to the `varexp` argument of [TTree::Draw()](https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45). |

Note for those `anaType` values which have the substring `Ana` in their names it is expected that the user has already run `ana_scans.py` on the corresponding `scandate` to produce the necessary input file for `gemTreeDrawWrapper.py`.

The following table shows the optional inputs that can be supplied when executing the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `--axisMaxX` | float | Maximum value for X-axis range. |
| `--axisMinX` | float | Minimum value for X-axis range, note this parameter will default to 0 `--axisMaxX` is given. | 
| `--axisMaxY` | float | Maximum value for Y-axis range. |
| `--axisMinY` | float | Minimum value for Y-axis range, note this parameter will default to 0 `--axisMaxY` is given. | 
| `--drawLeg` | none | When used with `--summary` option draws a TLegend on the output plot. |
| `--fitFunc` | string | Expression following the [TFormula syntax](https://root.cern.ch/doc/master/classTFormula.html) for defining a TF1 to be fit to the plot. |
| `--fitGuess` | string | Initial guess for fit parameters defined in `--fitFunc`. Note, order of params here should match that of `--fitFunc`. |
| `--fitOpt` | string | Option to be used when fitting, a complete list can be found [here](https://root.cern.ch/doc/master/classTH1.html#a7e7d34c91d5ebab4fc9bba3ca47dabdd). |
| `--fitRange | Comma separated list of float's | Defines the range the fit function is valid on. |
| `--rootOpt` | string | Option for creating the output `TFile`, e.g. {'RECREATE','UPDATE'} |
| `--showStat` | none | Causes the statistics box to be drawn on created plots. |
| `--summary` | none | Make a summary canvas with all created plots drawn on it. |
| `--treeSel` | string | Selection to be used when making the plot, corresponds to the `selection` argument of [TTree::Draw()](https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45). |
| `--treeDrawOpt` | string | Draw option to be used for the procued plots. |
| `--ztrim` | int | The ztrim value that was used when running the scans listed in `--infilename` |

#### gemTreeDrawWrapper.py Input File
This should be a `tab` deliminited text file.  The first line of this file should be a list of column headers formatted as:

```
ChamberName scandate
```

Subsequent lines of this file are the values that correspond to these column headings.  The value of the `ChamberName` column must correspond to the value of one entry in the `chamber_config` dictionary found in `mapping/chamberInfo.py`.  The next column is for `scandate` values.  Please note the `#` character is  understood as a comment, lines starting with a `#` will be skipped.

A complete example for a single detector is given as:

```
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
```

#### gemTreeDrawWrapper.py Example: Making a Plot
For example to make a plot from a latency scan, `Nhits` vs. `lat` for VFAT12, use the following example:

```
gemTreeDrawWrapper.py -ilistOfScanDates_TreeDraw.txt --anaType=latency --summary --treeExpress="Nhits:lat" --treeDrawOpt=APE1 --treeSel="vfatN==12" --axisMaxY=1000 --axisMinX=39 --axisMaxX=49 --drawLeg
```

This will produce one `Nhits` vs. `lat` plot for VFAT12 for each (ChamberName,scandate) pair found in `listOfScanDates_TreeDraw.txt`.  Additionally it will make one summary plot with a legend drawn which contains all of the produced plots.

#### gemTreeDrawWrapper.py Example: Fitting a Plot
For example to plot and fit an scurve from an scurve scan, `Nhits` vs `vcal`, for VFAT12 channel 45, use the following example:

```
gemTreeDrawWrapper.py -ilistOfScanDates_TreeDraw.txt --anaType=scurve --treeExpress="Nhits:vcal" --treeDrawOpt=APE1 --treeSel="vfatN==12 && vfatCH==45" --fitFunc="500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500" --fitRange=70,150 --fitOpt="RM" --fitGuess=110,10,10
```

Here the fit that will be applied will be equivalent too:
```
myFunc = r.TF1(strName,"500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500",70,150)
myFunc.SetParameter(0,110)
myFunc.SetParameter(0,10)
myFunc.SetParameter(0,10)
```

The fit option that will be used will be `RM`.  This fit will be applied to the scurve generated from VFAT12 channel 45 for each (ChamberName,scandate) pair found in `listOfScanDates_TreeDraw.txt`.

## Scurve Plotting Tools

The following tools exist for helping to understand scurve data:

1. `gemSCurveAnaToolkit.py`
2. `plot_noise_vs_trim.py`
3. `plot_vfat_and_channel_Scurve.py`
4. `plot_vfat_summary.py`
5. `summary_plots.py`

These tools can all by found in the `macros/` subdirectory and are designed to be run on `TFile` objects containing the `scurveFitTree` `TTree` object (e.g. produced by `anaUltraScurve.py`).  The first tool `gemSCurveAnaToolkit.py` is for plotting the same (vfat,channel/ROBstr) scurve from a list of scandates and it is described in a dedicated subsection below. The rest of the tools above are for making plots from a single input file; the plots made by tools 2-4 are:

- `plot_noise_vs_trim.py`: Plots a channel/strip's scurve width (e.g. `noise`) vs. trimDAC as a `TH2D` on a `TCanvas`, 
- `plot_vfat_and_channel_Scurve.py`: Plots a channel/strip's scurve as a `TH1D` and its `TF1` on a `TCanvas`, and
- `plot_vfat_summary.py`: Plots all scurves from a given VFAT as a `TH2D` on a `TCanvas`.

Tool 5 `summary_plots.py` produces the following plots from a single input file for a given VFAT depending on the command line argument supplied:

- Plot of channel/strip scurve mean as a `TH1D`,
- Plot of channel/strip scurve width as a `TH1D`,
- Plot of channel/strip scurve pedestal as a `TH1D`,
- Plot of Chi<sup>2</sup> of the channel/strip scurve fits as a `TH1D`,
- Plot of channel/strip scurve mean vs. scurve width as a `TH2D`, and
- Plot of channel/strip scurve width vs. trimDAC as a `TH2D`.

The command line options for tools 2-5 are:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `-c`, `--channels` | none | Make plots vs VFAT channels instead of ROB strips. |
| `-i`, `--infilename` | string | Physical filename of the input file.  Note this must be a `TFile` which contains the `scurveFitTree` `TTree` object. |
| `-s`, `--strip` | int | If the `-c` option is (not) supplied this will be the VFAT channel (ROB strip) the plot will be made for. |
| `-v`, `--vfat` | int | The VFAT to plot. |

Additionally tool 5 `summary_plots.py` has the following additional command line options:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `-a`, `--all` | none | Equivalent to supplying `-f` and `-x` options. |
| `-f`, `--fit` | none | Make fit parameter plots. |
| `-x`, `--chi2` | none | Make Chi2 plots. |

Note that for tool 5 `summary_plots.py` you must supply at least one of these additional options {`-a`,`-f`,`-x`}.

### gemSCurveAnaToolkit.py
The `gemSCurveAnaToolkit.py` tool is for plotting scurves and their fits from a given (vfat, vfatCH/ROBstr) from a list of scandates that correspond to `TFile` objects which contain the `scurveFitTree` `TTree` (e.g. files produced by `anaUltraScurve.py`). Each plot produced will be stored as an output `*.png` file. Additionally an output `TFile` will be produced which will contain each of the scurves and their fits.

#### gemSCurveAnaToolkit.py Arguments

| Name | Type | Description |
| ---- | ---- | ----------- |
| `-c`, `--channels` | none | Make plots vs VFAT channels instead of ROB strips. |
| `-i`, `--infilename` | string | Physical filename of the input file to be passed to `gemSCurveAnaToolkit.py`.  The format of this input file is the same as for the `gemTreeDrawWrapper.py` tool, see [gemTreeDrawWrapper.py Input File](#gemtreedrawwrapperpy-input-file) for more details. |
| `-s`, `--strip` | int | If the `-c` option is (not) supplied this will be the VFAT channel (ROB strip) the plot will be made for. |
| `-v`, `--vfat` | int | The VFAT to plot. |
| `--anaType` | string | Analysis type to be executed, taken from the list {'scurveAna','trimAna'}. |
| `--drawLeg` | none | When used with `--summary` option draws a TLegend on the output plot. |
| `--rootOpt` | string | Option for creating the output `TFile`, e.g. {'RECREATE','UPDATE'} |
| `--summary` | none | Make a summary canvas with all created plots drawn on it. |
| `--ztrim` | int | The ztrim value that was used when running the scans listed in `--infilename` |

#### gemSCurveAnaToolkit.py Input File
The format of this input file is the same as for the `gemTreeDrawWrapper.py` tool, see [gemTreeDrawWrapper.py Input File](#gemtreedrawwrapperpy-input-file) for more details.

#### gemSCurveAnaToolkit.py Example: Making a Plot
To plot the scurves, and their fits, for VFAT0 channel 29 from a set of scandates defined in `listOfScanDates_Scurve.txt` taken by `ultraScurve.py` and analyzed with `anaUltraScurve.py` you would call:

```
gemSCurveAnaToolkit.py -ilistOfScanDates_Scurve.txt -v0 -s29 --anaType=scurveAna -c --summary --drawLeg 
```

This will produce a `*.png` file for each of the scandates defined in `listOfScanDates_Scurve.txt` and one `*.png` file showing all the scurves with their fits drawn on it as a summary.  Additionally an output `TFile` will be produced containing each of the scurves and their fits.
