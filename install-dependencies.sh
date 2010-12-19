#!/bin/bash
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

sudo apt-get install build-essential libtool autoconf libpng12-dev libjpeg62-dev libxml2-dev python-dev python-numpy python-wxgtk2.8 subversion
#svn co http://flam3.svn.sourceforge.net/svnroot/flam3/branches/early-clip/src flam3-2.8-src
svn co http://flam3.googlecode.com/svn/trunk/src flam3-2.8-src

pushd flam3-2.8-src
aclocal
automake
autoconf
libtoolize
./configure --prefix=/usr --enable-shared
make clean
make 
sudo make install
popd


