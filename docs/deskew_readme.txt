Deskew
------------------------
by Marek Mauder
http://galfar.vevb.net/deskew/
https://bitbucket.org/galfar/app-deskew

v1.10 2014-03-04

Overview
------------------------

Deskew is a command line tool for deskewing scanned text documents.
It uses Hough transform to detect "text lines" in the image. As an output, you get
an image rotated so that the lines are horizontal.

There are binaries built for these platforms (located in Bin folder):
Win32, Win64, Linux 32bit+64bit, Mac OSX 32bit. Some binaries have sufix
identifying their platform (deskew64.exe, deskew-osx, etc.).

You can find some test images in TestImages folder and
scripts to run tests (RunTests.bat and runtests.sh) in Bin.
Note that scripts just call 'deskew' command so you may need
to rename binary for your platform to just 'deskew'.

Usage
------------------------

deskew [-o output] [-a angle] [-t a|treshold] [-b color] [-r rect] [-f format] [-s info] input
    -o output:     Output image file (default: out.png)
    -a angle:      Maximal skew angle in degrees (default: 10)
    -t a|treshold: Auto threshold or value in 0..255 (default: a)
    -b color:      Background color in hex format RRGGBB (default: trns. black)
    -r rect:       Skew detection only in content rectangle (pixels):
                   left,top,right,bottom (default: whole page)
    -f format:     Force output pixel format (values: b1|g8|rgba32)
    -s info:       Info dump (any combination of):
                   s - skew detection stats, p - program parameters
    input:         Input image file

  Supported file formats
    Input:  BMP, JPG, PNG, JNG, GIF, DDS, TGA, PBM, PGM, PPM, PAM, PFM, PSD, TIF (depends on platform)
    Output: BMP, JPG, PNG, JNG, GIF, DDS, TGA, PGM, PPM, PAM, PFM, PSD, TIF (depends on platform)

Version History
------------------------
  1.10 2014-03-04:
    - TIFF support for Win64 and 32/64bit Linux
    - forced output formats
    - fix: output file name were always lowercase
    - fix: preserves resolution metadata (e.g. 300dpi) of input when writing output
  1.00 2012-06-04:
    - background color
    - "area of interest" content rect
    - 64bit and Mac OSX support
    - PSD and TIFF (win32) support
    - show skew detection stats and program parameters
  0.95 2010-12-28:
    - Added auto thresholding
    - Imaging library updated.
  0.90 2010-02-12:
    -Initial version


