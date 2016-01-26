Some things don't easily work in virtualenv, so use them from the system 
python, without --system-site-packages.

Example using pygame
====================

After install pygame to the system python, install vext.pygame in your virtualenv:

(my-virtualenv) $ pip vext vext.pygame


Available packages
==================

These can be installed using pip as long as corresponding package is installed in the system python

  vext.panda3d
  
  vext.pygame

  vext.pygtk
  
  vext.gi

  vext.pyqt4

  vext.pyqt5

  vext.vtk


Blerb
=====

Virtualenv is great and is really well supported in the web development
community.  

Packages for graphics, audio and guis often use the python C API and
so can't be installed a virtualenv using pip.

Vext lets you use access specific modules in the system python, using
just pip and standard requirements.


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

Acts as a gatekeeper allowing access to particular libraries.
Works 


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

install_hint:
   This message will be displayed if the system dependencies
   are not installed.

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
These are modules that should be able to be imported if everything
is working correctly, you can test this using vext -c, for instance

```
$ vext -c pygtk
pygtk.vext
import gtk: [success]
import pygtk: [success]
```

You can also use ```vext -c '*'``` to check every vext files imports,
which can be useful to help diagnose problems.


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
  -c CHECK, --check CHECK
                        [external package] Test imports for external package
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

```VEXT_DEBUG_LOG=1``` enables extra debugging.

```VEXT_LOG_BLOCKS=1``` store blocked imports in vext.blocked_imports.

```VEXT_DISABLED=1``` disable vext when set.


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


TODO
====

The 'test import' part of the .vext file is not implemented yet,
this would stop installs unless the system requirements are
available (or at least write a warning to the console).


Merging the finder and loader should make it possible to know if we
are importing an allowed module, this would mean the submodules wouldn't
need to be specified in the .vext file.


Thanks
======
ruamel/venvgtk - for showing something like this is possible

pymotw article on modules and imports

