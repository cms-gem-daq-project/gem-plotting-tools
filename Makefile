#
# Makefile for gemplotting package
#

BUILD_HOME := $(shell dirname `pwd`)

Project      := gem-plotting-tools
ShortProject := gemplotting
Namespace    := gempython
Package      := gemplotting
ShortPackage := gemplotting
LongPackage  := gemplotting
PackageName  := $(Namespace)_$(ShortPackage)
PackageDir   := pkg/$(Namespace)/$(ShortPackage)
ScriptDir    := pkg/$(Namespace)/scripts

# Explicitly define the modules that are being exported (for PEP420 compliance)
PythonModules = ["$(Namespace).$(ShortPackage)", \
                 "$(Namespace).$(ShortPackage).utils", \
                 "$(Namespace).$(ShortPackage).fitting", \
                 "$(Namespace).$(ShortPackage).macros", \
                 "$(Namespace).$(ShortPackage).mapping" \
]
$(info PythonModules=${PythonModules})

GEMPLOTTING_VER_MAJOR=1
GEMPLOTTING_VER_MINOR=0
GEMPLOTTING_VER_PATCH=1

include $(BUILD_HOME)/$(Project)/config/mfCommonDefs.mk
include $(BUILD_HOME)/$(Project)/config/mfPythonDefs.mk

# include $(BUILD_HOME)/$(Project)/config/mfDefs.mk

include $(BUILD_HOME)/$(Project)/config/mfPythonRPM.mk

default:
	$(MakeDir) $(PackageDir)/utils
	@touch $(PackageDir)/utils/__init__.py
	@cp -rfp anaInfo.py anaoptions.py anautilities.py $(PackageDir)/utils
	@cp -rfp macros fitting mapping $(PackageDir)
	@echo "__path__ = __import__('pkgutil').extend_path(__path__, __name__)" > pkg/$(Namespace)/__init__.py
	@cp -rfp __init__.py $(PackageDir)

# need to ensure that the python only stuff is packaged into RPMs
.PHONY: clean preprpm
_rpmprep: preprpm
preprpm: default
	@cp -rfp config/scriptlets/installrpm.sh pkg/
	$(MakeDir) $(ScriptDir)
	@cp -rfp anaUltra*.py $(ScriptDir)
	@cp -rfp ana_scans.py $(ScriptDir)
	@cp -rfp anaXDAQLatency.py $(ScriptDir)
	-cp -rfp README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt $(PackageDir)
	-cp -rfp README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt pkg

clean:
	-rm -rf $(ScriptDir)
	-rm -rf $(PackageDir)
	-rm -f  pkg/$(Namespace)/__init__.py
	-rm -f  pkg/README.md
	-rm -f  pkg/LICENSE
	-rm -f  pkg/MANIFEST.in
	-rm -f  pkg/CHANGELOG.md
	-rm -f  pkg/requirements.txt
	-rm -f  pkg/installrpm.sh

print-env:
	@echo BUILD_HOME     $(BUILD_HOME)
	@echo GIT_VERSION    $(GIT_VERSION)
	@echo PYTHON_VERSION $(PYTHON_VERSION)
	@echo GEMDEVELOPER   $(GEMDEVELOPER)
