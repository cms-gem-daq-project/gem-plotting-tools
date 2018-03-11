
from setuptools import setup,find_packages

def readme():
    with open('README.md') as f:
        return f.read()

def getscripts():
    from os import listdir
    from os.path import isfile,join
    scriptdir = 'gempython/__longpackage__/bin'
    scripts   = listdir(scriptdir)
    return ['{0:s}/{1:s}'.format(scriptdir,x) for x in scripts if isfile(join(scriptdir,x)) ]

def getreqs():
    with open('requirements.txt') as f:
        reqs = f.readlines()
        return [x.strip() for x in reqs]

setup(name             = '__packagename__',
      version          = '__version__',
      # use_scm_version  = True,
      description      = '__description__',
      long_description = readme(),
      # author           = __author__,
      author           = 'GEM Online Systems Group',
      # author_email     = __author_email__,
      author_email     = 'cms-gem-online-sw@cern.ch',
      # url              = __url__,
      url              = 'https://cms-gem-daq-project.github.io/__package__',
      install_requires = ['numpy>=1.7', 'root_numpy>=4.7'],
      scripts          = getscripts(),
      # build_requires   = '__build_requires__',
      # namespace_package = "gempython",
      # packages         = __pythonmodules__, # for PEP420 native namespace util
      packages           = find_packages(), # for pkgutil namespace method
      # package_dir      = {'' : ''},
      # package_data     = dict((pkg,['*.so']) for pkg in __pythonmodules__),
      # dependency_links   = ['http://cmsgemos.web.cern.ch/cmsgemos/repo/tarball/master#egg=package-1.0']
      zip_safe         = False,
      # setup_requires   = ['setuptools_scm'],
      license          = '__license__',
)
