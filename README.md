# gem-plotting-tools

Table of Contents
=================

   * [gem-plotting-tools](#gem-plotting-tools)
      * [Setup:](#setup)
      * [Analyzing Scans:](#analyzing-scans)
      * [Using the Arbitray Plotter - gemPlotter.py](#using-the-arbitray-plotter---gemplotterpy)
         * [Command Line Arguments](#command-line-arguments)
         * [Input File Structure](#input-file-structure)
         * [Making a 1D Plot - Channel Level](#making-a-1d-plot---channel-level)
         * [Making a 1D Plot - VFAT Level](#making-a-1d-plot---vfat-level)
         * [Making a 2D Plot](#making-a-2d-plot)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)

## Setup:
The following `$SHELL` variables should be defined:

- $BUILD_HOME
- $DATA_PATH
- $ELOG_PATH

Then execute:

```
source $BUILD_HOME/gem-plotting-tools/setup/paths.sh
```

## Analyzing Scans:
See extensive documentation written on the [GEM DOC Twiki Page](https://twiki.cern.ch/twiki/bin/view/CMS/GEMDOCDoc#How_to_Produce_Scan_Plots).

## Using the Arbitray Plotter - gemPlotter.py
An arbitrary plotter `gemPlotter.py` has been created to help you plot results from python ultra scans. The following subsections describe first the input arguments, the structure of the input file, and the calling syntax.

### Command Line Arguments
The following table shows the mandatory inputs that must be supplied to execute the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| --anaType | string | Analysis type to be executed, see `tree_names.keys()` of `anaInfo.py` for possible inputs |
| --branchName | string | Name of TBranch where dependent variable is found, note that this TBranch should be found in the `TTree` that corresponds to the value given to the `--anaType` argument |
| -i, --infilename | string | physical filename of the input file to be passed to `gemPlotter.py`.  See [Input File Structure](#input-file-structure) for details on the format and contents of this file. |
| -v, --vfat | int | Specify VFAT to plot |

Note for those `anaType` values which have the substring `Ana` in their names it is expected that the user has already run `ana_scans.py` on the corresponding `scandate` to produce the necessary input file for `gemPlotter.py`.

The following table shows the optional inputs that can be supplied when executing the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| -a, --all | none | When providing this flag data from all 24 VFATs will be plotted.  Additionally a summary plot in the typical 3x8 grid will be created showing the results of all 24 VFATs. May be used instead of the `--vfat` option. |
| --axisMax | float | Maximum value for the axis depicting `--branchName`. |
| --axisMin | float | Minimum value for the axis depicting `--branchName`. |
| -c, --channels | none | When providing this flag the `--strip` option is interpreted as VFAT channel number instead of readout board (ROB) strip number. |
| -s, --strip | int | Specific ROB strip number to plot for `--branchName`.  Note for ROB strip level `--branchName` values (e.g. `trimDAC`) if this option is *not* provided the data point (error bar) will represent the mean (standard deviation) of `--branchName` from all strips. |
| --make2D | none| When providing this flag a 2D plot of ROB strip/vfat channel vs. independent variable will be plotted whose z-axis value is `--branchName`. |
| -p, --print | none | Prints a comma separated table of the plot's data to the terminal.  The format of this table will be compatible with the `genericPlotter` executable of the [CMS_GEM_Analysis_Framework](https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data). | 
| --rootOpt | string | Option for creating the output `TFile`, e.g. {'RECREATE','UPDATE'} |
| --showStat | none | Causes the statistics box to be drawn on created plots. Note only applicable when used with `--make2D`. |
| --vfatList | Comma separated list of int's | List of VFATs that should be plotted.  May be used instead of the `--vfat` option. |

### Input File Structure
This should be a `tab` deliminited text file.  The first line of this file should be a list of column headers formatted as:

```
ChamberName scandate    <Indep. Variable Name>
```

Subsequent lines of this file are the values that correspond to these column headings.  The value of the `ChamberName` column must correspond to the value of one entry in the `chamber_config` dictionary found in `mapping/chamberInfo.py`.  The **Indep. Variable Name** is the independent variable that `--branchName` will be plotted against and is assumed to be numeric.

A complete example for a single detector is given as:

```
ChamberName scandate    VT_{1}
GE11-VI-L-CERN-0002 2017.09.04.20.12    10
GE11-VI-L-CERN-0002 2017.09.04.22.52    20
GE11-VI-L-CERN-0002 2017.09.05.01.33    30
GE11-VI-L-CERN-0002 2017.09.05.04.21    40
GE11-VI-L-CERN-0002 2017.09.05.07.11    50
```

Here the `ChamberName` is always `GE11-VI-L-CERN-0002` and `--branchName` will be plotted against `VT_{1}` which is the **Indep. Variable Name** is `RunNo`.  Note the axis of interest will be assigned the label, with subscripts in this case, of `VT_{1}`.

A complete example for multiple detectors is given as:

```
ChamberName scandate    Layer
GEMINIm27L1 2019.09.04.20.12    -27.0
GEMINIm27L2 2019.09.04.22.52    -27.5
GEMINIm28L1 2019.09.05.01.33    -28.0
GEMINIm28L2 2019.09.05.04.21    -28.5
GEMINIp02L1 2019.09.05.07.11    2.0
GEMINIp02L2 2019.09.05.07.11    2.5
```

Here the `ChamberName` is different for each line and `--branchName` will be plotted against `Layer`.  Note we have provided a numerical equivalent for mXXLY and pXXLY:
- minus (plus) given by m (p) corresponds to a negative (positive) number, and
- L1(2) is a whole (half) integer number.

### Making a 1D Plot - Channel Level
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

### Making a 1D Plot - VFAT Level
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

### Making a 2D Plot
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
