Scan PDF - 
=========================================

.. image:: http://badge.fury.io/py/scanpdf.png
    :target: http://badge.fury.io/py/scanpdf

.. image:: http://pypip.in/d/scanpdf/badge.png
    :target: https://crate.io/packages/scanpdf?version=latest

.. image:: https://coveralls.io/repos/virantha/scanpdf/badge.png?branch=develop
    :target: https://coveralls.io/r/virantha/scanpdf 

* Free and open-source software: ASL2 license
* Documentation: http://virantha.github.io/scanpdf/html
* Source: https://github.com/virantha/scanpdf

Features
--------
* Uses SANE/scanadf to automatically scan to multi-page compressed PDFs
* `Integrates with ScanBd <http://virantha.github.io/scanpdf/html>`_ to respond to hardware button presses
* Automatically removes blank pages.
* Scans in color, and automatically down-converts into 1-bit B/W image for text/greyscale images

Usage:
------
The simplest usage is:

::

    scanpdf scan <pdffile>

Some of the options supported:

::
    
    --dpi=<dpi>     DPI to scan in [default: 300]
    --tmpdir=<dir>  Temporary directory [default: /tmp]
    --face-up=<true/false>       Face-up scanning [default: True]
    --keep-blanks   Don't check for and remove blank pages
    --blank-threshold=<ths>  Percentage of white to be marked as blank [default: 0.97] 
    --post-process  Run unpaper to deskew/clean up

Right now, I'm assuming this is getting called via ScanBD, so I don't have the option to manually specify the 
scanner.  If you really want to use this standalone, for now, please just set the ``SCANBD_DEVICE`` environment 
variable to your scanner device name before running this script


Installation
------------
::

    $ pip install scanpdf

Requires ImageMagick and SANE to be installed.

Disclaimer
----------
The software is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
