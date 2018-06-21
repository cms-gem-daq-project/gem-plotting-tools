#!/bin/sh

find %{python2_sitelib} -type f -name buildMapFiles.py -exec python {} \;
find %{python2_sitelib}/gempython/gemplotting/macros -type f -iname '*.py' -exec chmod +x {} \+

patchfile=/opt/cmsgemos/etc/patches/gemplotting.patch
if [ -e $patchfile ]
then
    cd %{python2_sitelib}
    patch -p1 < $patchfile
fi
