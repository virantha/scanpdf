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
    scanpdf [options] skipscan <scanfilesdir> <pdffile>


Options:
    -v --verbose    Verbose logging
    -d --debug      Debug logging
    --dpi=<dpi>     DPI to scan in [default: 300]
    --tmpdir=<dir>  Temporary directory [default: /tmp]
    --face-up=<true/false>       Face-up scanning [default: True]
    --keep-blanks   Don't check for and remove blank pages
    --blank-threshold=<ths>  Percentage of white to be marked as blank [default: 0.97] 
    --post-process  Run unpaper to deskew/clean up
    
"""

import sys, os
import logging
import shutil
import re

from version import __version__
import docopt

import subprocess
import time
import glob


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
        logging.debug("Running cmd: %s" % cmd_list)
        out = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, shell=True)
        logging.debug(out)
        return out


    def run_scan(self):
        device = os.environ['SCANBD_DEVICE']
        self.cmd('logger -t "scanbd: " "Begin of scan "')
        c = ['scanadf',
                '-d "%s"' % device,
                '--source "ADF Duplex"',
                '--mode Lineart',
                '--resolution %sdpi' % self.dpi,
                '--y-resolution %sdpi' % self.dpi,
                '-o %s/page_%%04d' % self.tmp_dir,
                ]
        self.cmd(c)
        self.cmd('logger -t "scanbd: " "End of scan "')

    def _error(self, msg):
        print("ERROR: %s" % msg)
        sys.exit(-1)

    def _atoi(self,text):                                       
         return int(text) if text.isdigit() else text    

    def _natural_keys(self, text):
         '''                                                                                                                    
         alist.sort(key=natural_keys) sorts in human order
         http://nedbatchelder.com/blog/200712/human_sorting.html
         (See Toothy's implementation in the comments)
         ''' 
         return [ self._atoi(c) for c in re.split('(\d+)', text) ]         

    def get_pages(self):
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        pages = glob.glob('./page_*')
        pages.sort(key = self._natural_keys)
        os.chdir(cwd)
        return pages

    def reorder_face_up(self, pages):
        reorder = []
        assert len(pages) % 2 == 0, "Why is page count not even for duplexing??"
        logging.info("Reordering pages")
        #for i in range(0,len(pages),2):
            #pages[i], pages[i+1] = pages[i+1], pages[i]
        pages.reverse()
        return pages
            
    def is_blank(self, filename):
        """
            Returns true if image in filename is blank
        """
        if not os.path.exists(filename):
            return True
        c = 'convert %s -shave 1%%x1%%  -format "%%[fx:mean]" info:' % filename
        result = self.cmd(c)
        if float(result.strip()) > self.blank_threshold:
            return True
        else:
            return False

    def run_postprocess(self, page_files):
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        
        processed_pages = []
        for page in page_files:
            processed_page = '%s_unpaper' % page
            c = ['unpaper', page, processed_page]
            self.cmd(c) 
            os.remove(page)
            processed_pages.append(processed_page)
        os.chdir(cwd)
        return processed_pages

    def run_convert(self, page_files):
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)

        pdf_basename = os.path.basename(self.pdf_filename)
        ps_filename = pdf_basename
        ps_filename = ps_filename.replace(".pdf", ".ps")
        c = ['convert',
                '-density %s' % self.dpi,
                '-rotate 180',
                ' '.join(page_files),
                ps_filename
            ]
        self.cmd(c)
        c = ['ps2pdf',
                '-DPDFSETTINGS=/prepress',
                ps_filename,
                pdf_basename,
            ]
        self.cmd(c)
        shutil.move(pdf_basename, self.pdf_filename)
        for filename in page_files+[ps_filename]:
            os.remove(filename)
           
        # IF we did the scan, then remove the tmp dir too
        if self.args['scan']:
            os.rmdir(self.tmp_dir)
        os.chdir(cwd)
        


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
        self.pdf_filename = os.path.abspath(self.args['<pdffile>'])
        self.dpi = self.args['--dpi']

        if argv['scan']:
            output_dir = time.strftime('%Y-%m-%d_%H%M.%S', time.localtime())
            self.tmp_dir = os.path.join(self.args['--tmpdir'], output_dir)
            self.tmp_dir = os.path.abspath(self.tmp_dir)
            if os.path.exists(self.tmp_dir):
                self._error("Temporary output directory %s already exists!" % self.tmp_dir)
            else:
                    os.makedirs(self.tmp_dir)
        elif argv['skipscan']:
            output_dir = argv['<scanfilesdir>']
            #self.tmp_dir = os.path.join(self.args['--tmpdir'], output_dir)
            self.tmp_dir = os.path.abspath(output_dir)
            if not os.path.exists(self.tmp_dir):
                self._error("Scan files directory %s does not exist!" % self.tmp_dir)

        # Blank checks
        self.keep_blanks =  argv['--keep-blanks']
        self.blank_threshold = float(argv['--blank-threshold'])
        assert(self.blank_threshold >= 0 and self.blank_threshold <= 1.0)
        self.post_process = argv['--post-process']



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
        if self.args['scan']:
            self.run_scan()
        
        # Now, convert the files to ps
        pages = self.get_pages()
        logging.debug( pages )
        if self.args['--face-up']:
            pages = self.reorder_face_up(pages)
        
        logging.debug( pages )
        # Run blanks
        if not self.keep_blanks:
            no_blank_pages = []
            for i,page in enumerate(pages):
                filename = os.path.join(self.tmp_dir, page)
                logging.info("Checking if %s is blank..." % filename)
                if not self.is_blank(filename):
                    no_blank_pages.append(page)
                else:
                    logging.info("  page %s is blank, removing..." % i)
                    os.remove(filename)
            pages = no_blank_pages
                
        logging.debug( pages )

        if self.post_process:
            pages = self.run_postprocess(pages)
            
        self.run_convert(pages)
        
def main():
    args = docopt.docopt(__doc__, version='Scan PDF %s' % __version__ )
    script = ScanPdf()
    print args
    script.go(args)

if __name__ == '__main__':
    main()
