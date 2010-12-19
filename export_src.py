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

import fr0stlib


def export_src(version, path):
    # setup and invoke bzr export
    tempdir = os.path.join(path, "fr0st-%s-src" %version)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    os.system("bzr export %s" %tempdir)

    # make the tarfile
    excludes = ['export_src.py',
                'setup_py2exe.py',
                'setup_py2exe_step2.py',
                os.path.join('fr0stlib', 'tests'),
                'Microsoft.VC90.CRT']
    def exclude(path):
        return os.path.relpath(path, tempdir) in excludes

    tar = TarFile.open(tempdir + '.tgz', mode='w:gz')
    tar.add(tempdir, arcname=os.path.basename(tempdir), exclude=exclude)
    tar.close()

    # clean up
    shutil.rmtree(tempdir)


version = fr0stlib.VERSION.split()[1]
release_dir = os.path.join('..', 'releases', version)
if not os.path.exists(release_dir):
    os.makedirs(release_dir)

export_src(version, release_dir)
