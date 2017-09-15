# gem-plotting-tools


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
See extensive documentation written on the [GEM DOC Twiki Page](https://twiki.cern.ch/twiki/bin/view/CMS/GEMDOCDoc#How_to_Produce_Scan_Plots).

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
| `-i`, `--infilename` | string | physical filename of the input file to be passed to `gemPlotter.py`.  See [gemPlotter.py Input File](#gemPlotter.py-Input-File) for details on the format and contents of this file. |
| `-v`, `--vfat` | int | Specify VFAT to plot |

Note for those `anaType` values which have the substring `Ana` in their names it is expected that the user has already run `ana_scans.py` on the corresponding `scandate` to produce the necessary input file for `gemPlotter.py`.

The following table shows the optional inputs that can be supplied when executing the script:

| Name | Type | Description |
| ---- | ---- | ----------- |
| `-a`, `--all` | none | When providing this flag data from all 24 VFATs will be plotted.  Additionally a summary plot in the typical 3x8 grid will be created showing the results of all 24 VFATs. May be used instead of the `--vfat` option. |
| `--axisMax` | float | Maximum value for the axis depicting `--branchName`. |
| `--axisMin` | float | Minimum value for the axis depicting `--branchName`. |
| `-c`, `--channels` | none | When providing this flag the `--strip` option is interpreted as VFAT channel number instead of readout board (ROB) strip number. |
| `-s`, `--strip` | int | Specific ROB strip number to plot for `--branchName`.  Note for ROB strip level `--branchName` values (e.g. `trimDAC`) if this option is *not* provided the data point (error bar) will represent the mean (standard deviation) of `--branchName` from all strips. |
| `--make2D` | none| When providing this flag a 2D plot of ROB strip/vfat channel vs. independent variable will be plotted whose z-axis value is `--branchName`. |
| `-p`, `--print` | none | Prints a comma separated table of the plot's data to the terminal.  The format of this table will be compatible with the `genericPlotter` executable of the [CMS_GEM_Analysis_Framework](https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data). | 
| `--rootOpt` | string | Option for creating the output `TFile`, e.g. {'RECREATE','UPDATE'} |
| `--showStat` | none | Causes the statistics box to be drawn on created plots. Note only applicable when used with `--make2D`. |
| `--vfatList` | Comma separated list of int's | List of VFATs that should be plotted.  May be used instead of the `--vfat` option. |
| `--ztrim` | int | The ztrim value that was used when running the scans listed in `--infilename` |

#### gemPlotter.py Input File
This should be a `tab` deliminited text file.  The first line of this file should be a list of column headers formatted as:

```
ChamberName scandate    <Indep. Variable Name>
```

Subsequent lines of this file are the values that correspond to these column headings.  The value of the `ChamberName` column must correspond to the value of one entry in the `chamber_config` dictionary found in `mapping/chamberInfo.py`.  The **Indep. Variable Name** is the independent variable that `--branchName` will be plotted against and is assumed to be numeric.  Please note the `#` character is  understood as a comment, lines starting with a `#` will be skipped.

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
| `-i`, `--infilename` | string | physical filename of the input file to be passed to `gemTreeDrawWrapper.py`.  See [gemTreeDrawWrapper.py Input File](#gemTreeDrawWrapper.py-Input-File) for details on the format and contents of this file. |
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
