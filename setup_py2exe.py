##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
from distutils.extension import Extension
from distutils.core import setup
from distutils.command import build_ext
import py2exe
from py2exe.build_exe import py2exe
import os, sys, glob, shutil
import _winreg

import fr0stlib

VERSION = fr0stlib.VERSION.split()[1]


if len(sys.argv) == 1:
    sys.argv.append('py2exe') # If not specified, build the installer
    sys.argv.append('-q') # quiet mode


# Remove build and dist folders
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)



fr0st_package_name = 'fr0stlib'


###########################################################################
#  Find VC9 redistributable path

##key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\VCExpress\9.0\Setup\VC')
##VC_REDIST_DIR = os.path.join(_winreg.QueryValueEx(key, 'ProductDir')[0], 'redist', 'x86', 'Microsoft.VC90.CRT')

# Add it manually until we can fix the manifest stuff. Also add to sys.path,
# so py2exe finds the dlls.
VC_REDIST_DIR = "Microsoft.VC90.CRT"
sys.path.append(VC_REDIST_DIR)

###########################################################################
#  And some InnoSetup stuff

class InnoScript:
    def __init__(self, name, lib_dir, dist_dir, windows_exe_files=[], lib_files=[], version=VERSION):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = name
        self.version = version
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]

    def chop(self, pathname):
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]
    
    def create(self, pathname="dist\\test_wx.iss"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi, r"Compression=lzma/ultra64"
        print >> ofi, r"LicenseFile=license.txt"
        print >> ofi

        print >> ofi, r"[Files]"
        print self.windows_exe_files + self.lib_files
        for path in self.windows_exe_files + self.lib_files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))
        print >> ofi

        print >> ofi, r"[Icons]"
        for path in self.windows_exe_files:
            print >> ofi, r'Name: "{group}\%s"; Filename: "{app}\%s"; WorkingDir: "{app}"' % \
                  (self.name, path)
        print >> ofi, 'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name

    def compile(self):
        import ctypes
        res = ctypes.windll.shell32.ShellExecuteA(0, "compile",
                                                  self.pathname,
                                                  None,
                                                  None,
                                                  0)
        if res < 32:
            raise RuntimeError, "ShellExecute failed, error %d" % res

###########################################################################
#  get py2exe to build the installer

class build_exe_plus_installer(py2exe):
    def run(self):
        py2exe.run(self)
        
        # create the Installer, using the files py2exe has created.
        script = InnoScript("Fractal Fr0st",
                            self.lib_dir,
                            self.dist_dir,
                            self.windows_exe_files + self.console_exe_files,
                            self.lib_files)

        print "*** creating the inno setup script***"
        script.create()
        print "*** compiling the inno setup script***"
        script.compile()

###########################################################################
#  Now define all the py2exe stuff...

class Target(object):
    """ A simple class that holds information on our executable file. """
    def __init__(self, **kw):
        """ Default class constructor. Update as you need. """
        self.__dict__.update(kw)
        

data_files = [('', ['license.txt', 'changelog.txt']
               + glob.glob(fr0st_package_name + '/pyflam3/win32_dlls/*.dll')),
              ('icons/toolbar', glob.glob('icons/toolbar/*.png')),
              ('icons/xformtab', glob.glob('icons/xformtab/*.png')),
              ('icons', ['icons/fr0st.png', 'icons/fr0st.ico']),
              ('samples/parameters', glob.glob('samples/parameters/*.flame')),
              ('samples/scripts/sheep_tools', glob.glob('samples/scripts/sheep_tools/*.py')),
              ('samples/scripts/batches', glob.glob('samples/scripts/batches/*.py')),
              ('samples/scripts', glob.glob('samples/scripts/*.py')),
              ('Microsoft.VC90.CRT', glob.glob(VC_REDIST_DIR + '\\*')),
             ]

includes = [
        'xml',
        'xml.etree',
        'xml.etree.ElementTree', 
        'xml.etree.cElementTree', 
        'pyexpat',
        'hashlib',
        ]

excludes = [
    'BaseHTTPServer', 'ConfigParser', 'Queue',
    'SocketServer', 'Tkconstants', 'Tkinter',
    '_gtkagg', '_socket', '_ssl', '_tkagg',
    'base64', 'bdb', 'bsddb', 'bz2',
    'cPickle', 'calendar', 'cmd', 'compiler', 'cookielib',
    'ctypes.util', 'curses', 'datetime',
    'doctest', 'email', 'multiprocessing',
    'numpy.core._dotblas', 'numpy.numarray', 'numpy.numarray.util',
    'numpy.random', 'optparse', 'parser', 'pdb', 'pkgutil', 
    'pydoc', 'pyreadline', 'pywin.debugger',
    'pywin.debugger.dbgcon', 'pywin.dialogs', 'readline', 'rfc822',
    'select', 'sets', 'shlex', 'signal', 'socket', 'ssl', 'subprocess',
    'symbol', 'symtable', 'tcl', 'textwrap', 'tty', 'uu',
    'webbrowser', 'xmlrpclib', 'zipfile', 'zipimport',
]

packages = [fr0st_package_name]

dll_excludes = [
    'libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll',
    'tcl84.dll', 'tk84.dll',
]

manifest = '''
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
  <assemblyIdentity
    version="0.6.8.0"
    processorArchitecture="x86"
    name="{name}"
    type="win32"
  />
  <description>{name} Program</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
          level="asInvoker"
          uiAccess="false"
        />
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.VC90.CRT"
        version="9.0.21022.8"
        processorArchitecture="x86"
        publicKeyToken="1fc8b3b9a1e18e3b"
      />
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="x86"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
</assembly>
'''.format(name="fr0st")

fr0st_target = Target(
    # what to build
    script = "fr0st.py",
    icon_resources = [(1, 'icons/fr0st.ico')],
    bitmap_resources = [],
    other_resources = [(24, 1, manifest)],
##    other_resources = [],
    dest_base = "fr0st",    
    version = "1.0",
    name = "fr0st"
    )


###########################################################################
#  Finally, hand it off to distutils

setup(

    data_files = data_files,

    options = {"py2exe": {"compressed": 1, 
                          "optimize": 0,
                          "includes": includes,
                          "excludes": excludes,
                          "packages": packages,
                          "dll_excludes": dll_excludes,
                          "bundle_files": 2,
                          "dist_dir": "dist",
                          #"xref": True,
                          "skip_archive": False,
                          "custom_boot_script": '',
                         }
              },
    zipfile = None,
    console = [],
    windows = [fr0st_target],
    cmdclass = {"py2exe": build_exe_plus_installer},
)
