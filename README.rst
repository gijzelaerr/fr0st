# Introduction

Fractal Fr0st is a fractal flame editor. It comes with an elegant and easy to use GUI and powerful python scripting. It
is built on top of flam3, but also supports alternate renderers such as flam4 (for GPU rendering).

This repository is forked from https://launchpad.net/fr0st

# installation

On Ubuntu 16.04 do::

    $ sudo apt-get install python-wxgtk3.0 flam3


problem is that the debian flam3 package doesn't contain the flam3 shared library: http://bugs.debian.org/833369
