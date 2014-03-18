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

import argparse
import sys, os
import logging
import shutil

from version import __version__
import yaml


"""
   
.. automodule:: scanpdf
    :private-members:
"""

class ScanPdf(object):
    """
        The main clas.  Performs the following functions:

    """

    def __init__ (self):
        """ 
        """
        self.config = None

    def _get_config_file(self, config_file):
        """
           Read in the yaml config file

           :param config_file: Configuration file (YAML format)
           :type config_file: file
           :returns: dict of yaml file
           :rtype: dict
        """
        with config_file:
            myconfig = yaml.load(config_file)
        return myconfig


    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        p = argparse.ArgumentParser(
                description = "",
                epilog = "Scan PDF version %s (Copyright 2014 Virantha Ekanayake)" % __version__,
                )

        p.add_argument('-d', '--debug', action='store_true',
            default=False, dest='debug', help='Turn on debugging')

        p.add_argument('-v', '--verbose', action='store_true',
            default=False, dest='verbose', help='Turn on verbose mode')

        p.add_argument('-m', '--mail', action='store_true',
            default=False, dest='mail', help='Send email after conversion')

        #---------
        # Single or watch mode
        #--------
        single_or_watch_group = p.add_mutually_exclusive_group(required=True)
        # Positional argument for single file conversion
        single_or_watch_group.add_argument("pdf_filename", nargs="?", help="Scanned pdf file to OCR")
        # Watch directory for watch mode
        single_or_watch_group.add_argument('-w', '--watch', 
             dest='watch_dir', help='Watch given directory and run ocr automatically until terminated')

        #-----------
        # Filing options
        #----------
        filing_group = p.add_argument_group(title="Filing optinos")
        filing_group.add_argument('-f', '--file', action='store_true',
            default=False, dest='enable_filing', help='Enable filing of converted PDFs')
        filing_group.add_argument('-c', '--config', type = argparse.FileType('r'),
             dest='configfile', help='Configuration file for defaults and PDF filing')
        filing_group.add_argument('-e', '--evernote', action='store_true',
            default=False, dest='enable_evernote', help='Enable filing to Evernote')


        args = p.parse_args(argv)

        self.debug = args.debug
        self.verbose = args.verbose
        self.pdf_filename = args.pdf_filename
        self.watch_dir = args.watch_dir
        self.enable_email = args.mail

        if self.debug:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        if self.verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')

        # Parse configuration file (YAML) if specified
        if args.configfile:
            self.config = self._get_config_file(args.configfile)
            logging.debug("Read in configuration file")
            logging.debug(self.config)

        if args.enable_evernote:
            self.enable_evernote = True
        else:
            self.enable_evernote = False

        if args.enable_filing or args.enable_evernote:
            self.enable_filing = True
            if not args.configfile:
                p.error("Please specify a configuration file(CONFIGFILE) to enable filing")
        else:
            self.enable_filing = False

        self.watch = False

        if args.watch_dir:
            logging.debug("Starting to watch")
            self.watch = True

        if self.enable_email:
            if not args.configfile:
                p.error("Please specify a configuration file(CONFIGFILE) to enable email")


    def go(self, argv):
        """ 
            The main entry point into ScanPdf

            #. Do something
            #. Do something else
        """
        # Read the command line options
        self.get_options(argv)


def main():
    script = ScanPdf()
    script.go(sys.argv[1:])

if __name__ == '__main__':
    main()

