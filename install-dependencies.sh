#!/bin/bash

sudo aptitude install build-essential libtool autoconf libpng12-dev libjpeg62-dev libxml2-dev python-dev python-numpy python-wxgtk2.8 subversion
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


