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
    scanpdf [options] scan 
    scanpdf [options] pdf <pdffile> 
    scanpdf [options] scan pdf <pdfile> 


Options:
    -v --verbose                Verbose logging
    -d --debug                  Debug logging
    --dpi=<dpi>                 DPI to scan in [default: 300]
    --tmpdir=<dir>              Temporary directory 
    --face-up=<true/false>      Face-up scanning [default: True]
    --keep-blanks               Don't check for and remove blank pages
    --blank-threshold=<ths>     Percentage of white to be marked as blank [default: 0.97] 
    --post-process              Run unpaper to deskew/clean up
    
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
from itertools import combinations


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
        try:
            out = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, shell=True)
            logging.debug(out)
            return out
        except subprocess.CalledProcessError as e:
            print e.output
            self._error("Could not run command %s" % cmd_list)
            


    def run_scan(self):
        device = os.environ['SCANBD_DEVICE']
        self.cmd('logger -t "scanbd: " "Begin of scan "')
        c = ['scanadf',
                '-d "%s"' % device,
                '--source "ADF Duplex"',
                '--mode Color',
                '--resolution %sdpi' % self.dpi,
                '--y-resolution %sdpi' % self.dpi,
                '-o %s/page_%%04d' % self.tmp_dir,
                '-y 876',
                '--page-height 876',
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

	     standard deviation: 56.9662 (0.223397)
        """
        if not os.path.exists(filename):
            return True


        c = 'identify -verbose %s' % filename
        result = self.cmd(c)
        mStdDev = re.compile("""\s*standard deviation:\s*\d+\.\d+\s*\((?P<percent>\d+\.\d+)\).*""")
        for line in result.splitlines():
            match = mStdDev.search(line)
            if match:
                stdev = float(match.group('percent'))
                if stdev > 0.1:
                    return False
        return True

        # OLD CODE - doesn't work for color images
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

    def run_crop(self, page_files):
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        crop_pages = []
        for i, page in enumerate(page_files):
            logging.debug("Cropping page %d" % i)
            crop_page = '%s.crop' % page
            crop_pages.append(crop_page)
            c = ['convert',
                    '-fuzz 20%',
                    '-trim',
                    ' %s ' % page,
                    crop_page,
                ]
            self.cmd(c)
            os.remove(page)

        os.chdir(cwd)
        return crop_pages

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
        c = ['epstopdf',
                ps_filename,
                ]
        
        self.cmd(c)
        shutil.move(pdf_basename, self.pdf_filename)
        for filename in page_files+[ps_filename]:
            os.remove(filename)
           
        # IF we did the scan, then remove the tmp dir too
        if self.args['scan'] and not self.args['--keep-tmpdir']:
            os.rmdir(self.tmp_dir)
        os.chdir(cwd)
        

    def convert_to_bw(self, pages):
        new_pages = []
        for i, page in enumerate(pages):
            filename = os.path.join(self.tmp_dir, page)
            logging.info("Checking if %s is bw..." % filename)
            if self._is_color(filename):
                new_pages.append(page)
            else: # COnvert to BW
                bw_page = self._page_to_bw(filename)
                new_pages.append(bw_page)
        return new_pages

            
    def _page_to_bw(self, page):
        out_page = "%s_bw" % page
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)

        cmd = "convert %s +dither -colors 2 -colorspace gray -normalize %s_bw" % (page, page)
        out = self.cmd(cmd)
        # Remove the old file
        os.remove(page)
        os.chdir(cwd)
        return out_page

    def _is_color(self, filename):
        """
            Run the following command from ImageMagick:

            ::
                
                 convert holi.pdf -colors 8 -depth 8 -format %c histogram:info:- 

            This outputs something like the following:
            ::

                  10831: ( 24, 26, 26,255) #181A1A srgba(24,26,26,1)
                  4836: ( 55, 87, 79,255) #37574F srgba(55,87,79,1)
                  6564: ( 77,138,121,255) #4D8A79 srgba(77,138,121,1)
                  4997: ( 86, 96, 93,255) #56605D srgba(86,96,93,1)
                  7005: ( 92,153,139,255) #5C998B srgba(92,153,139,1)
                  2479: (143,118,123,255) #8F767B srgba(143,118,123,1)
                  8870: (169,176,170,255) #A9B0AA srgba(169,176,170,1)
                442906: (254,254,254,255) #FEFEFE srgba(254,254,254,1)
                  1053: (  0,  0,  0,255) #000000 black
                484081: (255,255,255,255) #FFFFFF white
 
        """
        cmd = "convert %s -colors 8 -depth 8 -format %%c histogram:info:-" % filename
        out = self.cmd(cmd)
        mLine = re.compile(r"""\s*(?P<count>\d+):\s*\(\s*(?P<R>\d+),\s*(?P<G>\d+),\s*(?P<B>\d+).+""")
        colors = []
        for line in out.splitlines():
            matchLine = mLine.search(line)
            if matchLine:
                logging.debug("Found RGB values")
                color = [int(x) for x in (matchLine.group('count'),
                             matchLine.group('R'),
                             matchLine.group('G'),
                             matchLine.group('B'),
                             )
                        ]
                colors.append(color)
        # sort
        colors.sort(reverse=True, key = lambda x: x[0])
        logging.debug(colors)
        is_color = False
        logging.debug(colors)
        for color in colors:
            # Calculate the mean differences between the RGB components
            # Shades of grey will be very close to zero in this metric...
            diff = float(sum([abs(color[2]-color[1]),
                         abs(color[3]-color[1]),
                         abs(color[3]-color[2]),
                         ]))/3
            if diff > 20:
                is_color = True
                logging.debug("Found color")
        return is_color



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
        if self.args['pdf']:
            self.pdf_filename = os.path.abspath(self.args['<pdffile>'])

        self.dpi = self.args['--dpi']

        output_dir = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        if argv['--tmpdir']:
            self.tmp_dir = argv['--tmpdir']
        else:
            self.tmp_dir = os.path.join('/tmp', output_dir)
        self.tmp_dir = os.path.abspath(self.tmp_dir)

        # Make the tmp dir only if we're scanning, o/w throw an error
        if argv['scan']:
            if os.path.exists(self.tmp_dir):
                self._error("Temporary output directory %s already exists!" % self.tmp_dir)
            else:
                os.makedirs(self.tmp_dir)
        else:
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
        
        if self.args['pdf']:
            # Now, convert the files to ps
            pages = self.get_pages()
            logging.debug( pages )
            if self.args['--face-up']:
                pages = self.reorder_face_up(pages)
            
            logging.debug( pages )

            # Crop the pages
            pages = self.run_crop(pages)

            # Now, check if color or bw
            pages = self.convert_to_bw(pages)
            logging.debug(pages)

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

