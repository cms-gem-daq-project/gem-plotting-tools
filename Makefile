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
ManDir       := pkg/man

# Explicitly define the modules that are being exported (for PEP420 compliance)
PythonModules = ["$(Namespace).$(ShortPackage)", \
                 "$(Namespace).$(ShortPackage).utils", \
                 "$(Namespace).$(ShortPackage).fitting", \
                 "$(Namespace).$(ShortPackage).macros", \
                 "$(Namespace).$(ShortPackage).mapping" \
]
$(info PythonModules=${PythonModules})

GEMPLOTTING_VER_MAJOR:=$(shell ./config/tag2rel.sh | awk '{split($$0,a," "); print a[1];}' | awk '{split($$0,b,":"); print b[2];}')
GEMPLOTTING_VER_MINOR:=$(shell ./config/tag2rel.sh | awk '{split($$0,a," "); print a[2];}' | awk '{split($$0,b,":"); print b[2];}')
GEMPLOTTING_VER_PATCH:=$(shell ./config/tag2rel.sh | awk '{split($$0,a," "); print a[3];}' | awk '{split($$0,b,":"); print b[2];}')

include $(BUILD_HOME)/$(Project)/config/mfCommonDefs.mk
include $(BUILD_HOME)/$(Project)/config/mfPythonDefs.mk

# include $(BUILD_HOME)/$(Project)/config/mfDefs.mk

include $(BUILD_HOME)/$(Project)/config/mfSphinx.mk
include $(BUILD_HOME)/$(Project)/config/mfPythonRPM.mk

default:
	$(MakeDir) $(PackageDir)
	@cp -rf macros fitting mapping utils $(PackageDir)
	@echo "__path__ = __import__('pkgutil').extend_path(__path__, __name__)" > pkg/$(Namespace)/__init__.py
	@cp -rf __init__.py $(PackageDir)

# need to ensure that the python only stuff is packaged into RPMs
.PHONY: clean preprpm doc

doc:
	make html

_rpmprep: preprpm
preprpm: default man
	@if ! [ -e pkg/installrpm.sh ]; then \
		cp -rf config/scriptlets/installrpm.sh pkg/; \
	fi
	$(MakeDir) $(ScriptDir)
	@cp -rf anaUltra*.py $(ScriptDir)
	@cp -rf anaSBit*.py $(ScriptDir)
	@cp -rf anaXDAQ*.py $(ScriptDir)
	@cp -rf ana_scans.py $(ScriptDir)
	@cp -rf anaDACScan.py $(ScriptDir)
	@cp -rf anaXDAQLatency.py $(ScriptDir)
	@cp -rf packageFiles4Docker.py $(ScriptDir)
	-rm -rf $(ManDir)
	$(MakeDir) $(ManDir)
	@cp -rf doc/_build/man/* $(ManDir)
	gzip $(ManDir)/*
	-cp -rf README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt $(PackageDir)
	-cp -rf README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt pkg

clean:
	-rm -rf $(ScriptDir)
	-rm -rf $(PackageDir)
	-rm -rf $(ManDir)
	-rm -f  pkg/$(Namespace)/__init__.py
	-rm -f  pkg/README.md
	-rm -f  pkg/LICENSE
	-rm -f  pkg/MANIFEST.in
	-rm -f  pkg/CHANGELOG.md
	-rm -f  pkg/requirements.txt

print-env:
	@echo BUILD_HOME     $(BUILD_HOME)
	@echo GIT_VERSION    $(GIT_VERSION)
	@echo PYTHON_VERSION $(PYTHON_VERSION)
	@echo GEMDEVELOPER   $(GEMDEVELOPER)
