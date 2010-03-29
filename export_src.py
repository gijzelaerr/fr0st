#!/usr/bin/env python
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
import os, sys, shutil
from tarfile import TarFile


# setup and invoke bzr export
if not len(sys.argv) == 2:
    print 'Usage: %s release_number (e.g. "1.0beta2")' %sys.argv[0]
    exit()
version = sys.argv[1]
tempdir = os.path.join("..", "releases", version, "fr0st-%s-src" %version)
if not os.path.exists(tempdir):
    os.makedirs(tempdir)

os.system("bzr export %s" %tempdir)


# make the tarfile
excludes = ['export_src.py',
            'setup_py2exe.py',
            os.path.join('fr0stlib', 'tests')]
def exclude(path):
    return os.path.relpath(path, tempdir) in excludes

tar = TarFile.open(tempdir + '.tgz', mode='w:gz')
tar.add(tempdir, arcname=os.path.basename(tempdir), exclude=exclude)
tar.close()

# clean up
shutil.rmtree(tempdir)
