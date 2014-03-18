#!/usr/bin/env python2.7
# Copyright 2014 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Scan to PDF.

Usage:
    scanpdf [options] scan <pdffile>


Options:
    -v --verbose    Verbose logging
    -d --debug      Debug logging
    --dpi=<dpi>     DPI to scan in [default: 300]
    --tmpdir=<dir>  Temporary directory [default: /tmp]

"""

import argparse
import sys, os
import logging
import shutil

from version import __version__
import yaml
import docopt

import subprocess
import time



class ScanPdf(object):
    """
        The main clas.  Performs the following functions:

    """

    def __init__ (self):
        """ 
        """
        self.config = None

    def cmd(self, cmd_list):
        if isinstance(cmd_list, list):
            cmd_list = ' '.join(cmd_list)
        out = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, shell=True)
        return out


    def run_scan(self):
        device = os.environ['SCANBD_DEVICE']
        self.cmd('logger -t "scanbd: " "Begin of scan "')
        c = ['scanadf',
                '-d %s' % device,
                '--source "ADF Duplex"',
                '--mode Lineart',
                '--resolution %sdpi' % self.dpi,
                '--y-resolution %sdpi' % self.dpi,
                '-o %s/page_%%04d' % self.tmp_dir,
                ]
        self.cmd(c)
        self.cmd('logger -t "scanbd: " "End of scan "')

    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        self.args = argv

        if argv['--verbose']:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        if argv['--debug']:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')                
        self.pdf_filename = self.args['<pdffile>']
        self.dpi = self.args['--dpi']

        output_dir = time.strftime('%Y-%m-%d_%H%M.%S', time.localtime())
        self.tmp_dir = os.path.join(self.args['--tmpdir'], output_dir)
        self.tmp_dir = os.path.abspath(self.tmp_dir)
        if os.path.exists(self.tmp_dir):
            self._error("Temporary output directory %s already exists!" % self.tmp_dir)
            sys.exit(-1)
        else:
            os.makedirs(self.tmp_dir)


    def go(self, argv):
        """ 
            The main entry point into ScanPdf

            #. Get the options
            #. Create the temp dir
            #. Run scanadf
        """
        # Read the command line options
        self.get_options(argv)
        logging.info("Temp dir: %s" % self.tmp_dir)
        self.run_scan()




def main():
    args = docopt.docopt(__doc__, version='Scan PDF %s' % __version__ )
    script = ScanPdf()
    print args
    script.go(args)

if __name__ == '__main__':
    main()

