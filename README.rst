Scan PDF - Easy scans in Linux with a document scanner like the Fujitsu ScanSnap
################################################################################

.. image:: http://badge.fury.io/py/scanpdf.png
    :target: http://badge.fury.io/py/scanpdf

.. image:: http://pypip.in/d/scanpdf/badge.png
    :target: https://crate.io/packages/scanpdf?version=latest


If you're looking for a simple way to use a multi-page scanner and get your
document into a PDF in Linux without any proprietary or commercial software,
then ScanPDF might be the solution.  I wrote it to quickly take the Linux SANE
scanner system output image files, and process them into usable PDFs.  By
usable, I mean PDFs that maintain their original scanned resolution, omit blank
pages (if you're scanning in duplex mode, for example), preserve color unless
the original is greyscale/black and white, in which case they are intelligently
down-converted to B/W PDFs to save space.

* Free and open-source software: ASL2 license
* Documentation: http://virantha.github.io/scanpdf/html
* Source: https://github.com/virantha/scanpdf

Features
--------
* Uses SANE/scanadf to automatically scan to multi-page compressed PDFs
* `Integrates with ScanBd <http://virantha.github.io/scanpdf/html>`_ to respond to hardware button presses
* Automatically removes blank pages.
* Scans in color, and automatically down-converts into 1-bit B/W image for text/greyscale images
* Auto-crops to the proper page size.

Usage:
------
The simplest way to use this is:

::

    scanpdf scan pdf <pdffile>

This will first perform the scan, and then the conversion to PDF.  If you want
to split up the scan and the PDF conversion into two separate invocations (for
reasons clarified below), then you can do:

::

    scanpdf --tmpdir=tmp scan
    scanpdf --tmpdir=tmp pdf <pdffile>
  
One reason for the separation might be if you want to keep scanning documents
(very quick) while the post-processing (slower) for the PDF conversion is
taking place in the background.   For instance, if you're using the hardware
button on the scanner to initiate scans (as detailed in this_ document), then
you want to return immediately after the scan instead of waiting for the full
conversion to PDF has taken place.

.. _this: http://virantha.com/2014/03/17/one-touch-scanning-with-fujitsu-scansnap-in-linux/

You can optionally use the following switches to control if you're putting pages face up or face down in the auto
document feeder, if you want to skip the blank page processing, adjust the blank page detection threshold, or add 
additional post-processing using unpaper_:

.. _unpaper: http://unpaper.berlios.de

::

        --dpi=<dpi>                 DPI to scan in [default: 300]
        --face-up=<true/false>      Face-up scanning [default: True]
        --keep-blanks               Don't check for and remove blank pages
        --blank-threshold=<ths>     Percentage of white to be marked as blank [default: 0.97] 
        --post-process              Run unpaper to deskew/clean up


Right now, I'm assuming this is getting called via ScanBD, so I don't have the option to manually specify the 
scanner.  If you really want to use this standalone, for now, please just set the ``SCANBD_DEVICE`` environment 
variable to your scanner device name before running this script.


Installation
------------
::

    $ pip install scanpdf

Requires ImageMagick and SANE to be installed, for the command line tools:

* ``convert``
* ``identify``
* ``ps2pdf``
* ``scanadf``

Also requires epstopdf.

Disclaimer
----------
The software is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
