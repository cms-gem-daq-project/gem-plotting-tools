#!/bin/sh

find %{python2_sitelib} -type f -name buildMapFiles.py -exec python {} \;
find %{python2_sitelib}/gempython/gemplotting/macros -type f -iname '*.py' -exec chmod +x {} \+

patchfile=/opt/cmsgemos/etc/patches/gempython.gemplotting.patch
if [ -e $patchfile ]
then
    cd %{python2_sitelib}/gempython/gemplotting
    patch -p1 < $patchfile
fi
