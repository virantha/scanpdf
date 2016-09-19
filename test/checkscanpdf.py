#!/usr/bin/env python2.7

# Basic Test for scanpdf.py

import os
from scanpdf import scanpdf

OUTPUT_DIRECTORY = "/home/dale/Temp"
FILENAME = "image_test.pdf"

def main():
    full_path = os.path.join(OUTPUT_DIRECTORY, FILENAME)
    if os.path.exists(full_path):
        os.remove(full_path)
    os.environ["SCANBD_DEVICE"] = 'net:localhost:fujitsu:ScanSnap S1500:1448'
    args = {'scan': True, 'pdf': True, '<pdffile>': full_path,
            '--verbose': True, '--debug': True, '--dpi': 300, '--crop': False, '--tmpdir':False,
            '--keep-blanks':False, '--blank-threshold':0.80, '--post-process':False,
            '--face-up':False, '--keep-tmpdir':False}
    script = scanpdf.ScanPdf()
    print args
    script.go(args)


if __name__ == '__main__':
    main()
