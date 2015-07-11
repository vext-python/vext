Some things don't easily work in virtualenv, so use them from the system 
python, without --system-site-packages.

Example
=======

Important ! - make sure pip and setuptools are up to date!
(my-virtualenv) $ pip install -U pip setuptools

(my-virtualenv) $ pip vext.pygame

Blerb
=====

Virtualenv is great, many packages in the webdev community support
it, when it comes to fields like graphics and audio getting things
working is a pain.

Why not use --system-site-packages?
-----------------------------------

Pulling in everything gets things working quickly, but negates
many of the advantages of virtualenv.

For instance it can be easy to forget to add packages to 
requirements.txt when everything "works for me(TM)".

What about symlinks?
--------------------

This is quite a clean solution, but doesn't work in Windows.


Vext
----

* Allows only specific libraries to be imported, specified in .vext files.
* Works on windows

Available packages
==================

Use pip to install one of these packages

* vext.panda3d
* vext.pygame

* vext.pygtk
* vext.gi

* vext.pyqt4


Adding packages
===============

Vext is a workaround, if you can - it's might better to fix make
packages to work in virtualenv. 

In the case of bindings then switching from the python C API to
CFFI is often a great solution (as a bonus, your package will
work with pypy too).

Still reading ?

Create a .vext file, the pygtk example looks like this:

```
# Pygtk vext
#

# Vext will allow access to these modules
modules:
    cairo
    gtk
    pygtk
    glib
    gobject

test_import:
    # Vext will try and import any modules here
    # To check if the install worked
    gtk, pygtk

# move glib and gobject to their own vexts

# pygtk.pth does most of the initialisation of pygtk
pths:
    pygtk.pth
```

Then create a setup.py to install it (have a look at vext.pygtk)

Vext is cross platform, so please try and test your vext specs
on windows as well as osx and linux !

Vext Spec File Format
=====================

Vext is yaml that shows which modules to open

modules
-------
List of modules to allow importing from the system site packages.


test-import
------------
*TODO* Vext will check if it can import these modules.

pths
----
Specify any pth files that the module uses to initialise itself.


Limitations
===========

Vext won't stop all imports, (especially when pth files are used)
the idea is that an error will be thrown fairly early though
if you are running Vext and try and import a module.


Usage
=====

Mostly you will use vext just by installing a package like 'vext.pygtk'
the commandline options allow you to get status and enable / disable
Vext.

```
optional arguments:
  -l, --list     List external packages "Vext"
  -e, --enable   Disable Vext loader
  -d, --disable  Enable Vext loader
  -s, --status   Show Vext status
```

If Vext is causing an issue with other tools try disabling it,
also feel free to send a bug report with any information and
the output of ```vext -l```.

Implementation
==============

Vext works as a finder and loader of modules, it installs itself on the
end of the system path, and then will check for any allowed modules.

If Vext runs any .pth files they will be installed after it in the .pth
practically it guards the base level of sitepackages.

So in a virtualenv ```import pygtk``` should definitally fail if vext is 
installed but not vext.pygtk


Environment Variables
=====================

Logging Blocked Imports
-----------------------
To see which modules Vext is blocking set VEXT_LOG_BLOCKS instead of
standard ImportErrors, you will get ones like this:


```bash
$ VEXT_LOG_BLOCKS=1
```
```python
>>> import pyaudio
ImportError("Vext blocked import of pyaudio")
```

Remembering Blocked Imports
---------------------------

Vext can store all blocked imports in vext.blocked_imports by setting
vext.remember_blocks to True:

```
>>> import vext
>>> vext.remember_blocks = True
>>> vext.blocked_imports
set([])
>>> import pygtk
ImportError:
>>> vext.blocked_imports
set(["pygtk"])
```

Help out
========

Please test this, so far it has only been tested on Ubuntu and Windows.

Thanks
======
ruamel/venvgtk - for some of the ideas
pymotw article on modules and imports

