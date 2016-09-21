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
    scanpdf [options] scan pdf <pdffile>
    scanpdf [options] pdf
    scanpdf [options] scan pdf


Options:
    -v --verbose                Verbose logging
    -d --debug                  Debug logging
    --dpi=<dpi>                 DPI to scan in [default: 300]
    --device=<device>           Scanning device (sub '%' for spaces)
    --crop                      Run ImageMagick cropping routine
    --tmpdir=<dir>              Temporary directory 
    --keep-tmpdir               Whether to keep the tmp dir after scanning or not [default: False]
    --face-up=<true/false>      Face-up scanning [default: True]
    --keep-blanks               Don't check for and remove blank pages
    --blank-threshold=<ths>     Percentage of white to be marked as blank [default: 0.97]
    --post-process              Process finished images with unpaper
    --text-recognize            Run pdfsandwich for text recognition
    
"""

import glob
import logging
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import time
import wx
from multiprocessing.dummy import Pool as Threadpool

import docopt

from version import __version__

date_format = '%m/%d/%Y %H:%M:%S'


class ProcessPage:
    page = None
    scanpdf = None

    def __init__(self, page, scanpdf):
        """
        """
        self.page = page
        self.scanpdf = scanpdf
        os.chdir(self.scanpdf.tmp_dir)

    def process(self):
        self.run_deskew()
        if self.scanpdf.crop:
            self.run_crop()
        self.convert_to_bw()
        if not self.scanpdf.keep_blanks:
            self.remove_blank()
        if self.page is not None and self.scanpdf.post_process:
            self.run_postprocess()

    def run_deskew(self):
        deskew = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'deskew64'
        logging.info("Deskewing: " + os.path.basename(self.page))
        ppm_page = '%s.ppm' % self.page
        c = [deskew, ' %s ' % self.page, '-o', ppm_page]
        result = self.scanpdf.cmd(c)
        logging.debug("deskew result: " + result)
        os.remove(self.page)
        self.page = ppm_page

    def run_crop(self):
        logging.info("Cropping: " + os.path.basename(self.page))
        crop_page = '%s.crop' % self.page
        c = ['convert', '-fuzz 20%', '-trim', self.page, crop_page]
        self.scanpdf.cmd(c)
        os.remove(self.page)
        self.page = crop_page

    def run_postprocess(self):
        logging.info("Post-processing with unpaper: " + os.path.basename(self.page))
        shutil.move(self.page, '%s.ppm' % self.page)
        self.page = '%s.ppm' % self.page
        processed_page = '%s_unpaper' % self.page
        c = ['unpaper', self.page, processed_page]
        self.scanpdf.cmd(c)
        os.remove(self.page)
        self.page = processed_page

    def convert_to_bw(self):
        logging.info("Checking if: " + os.path.basename(self.page) + " is bw...")
        if not self._is_color():
            self._page_to_bw()

    def _page_to_bw(self):
        bw_page = "%s_bw" % self.page
        c = "convert %s +dither -colors 2 -colorspace gray -normalize %s_bw" % (self.page, self.page)
        self.scanpdf.cmd(c)
        # Remove the old file
        os.remove(self.page)
        self.page = bw_page

    @staticmethod
    def run(args):
        process_page = ProcessPage(args[0], args[1])
        process_page.process()
        return process_page.page

    def remove_blank(self):
        logging.info("Checking if: " + os.path.basename(self.page) + " is blank")
        if self.is_blank():
            os.remove(self.page)
            self.page = None

    def is_blank(self):
        """
        :return: true if image is blank
        """
        if not os.path.exists(self.page):
            return True
        c = 'identify -verbose %s' % self.page
        result = self.scanpdf.cmd(c)
        m_std_dev = re.compile("""\s*standard deviation:\s*\d+\.\d+\s*\((?P<percent>\d+\.\d+)\).*""")
        for line in result.splitlines():
            match = m_std_dev.search(line)
            if match:
                stdev = float(match.group('percent'))
                logging.info(os.path.basename(self.page) + " std. dev: " + "{0:.4f}".format(stdev))
                if stdev > 1. - self.scanpdf.blank_threshold:
                    return False
        return True

    def _is_color(self):
        """
        Run the following command from ImageMagick:
        convert holi.pdf -colors 8 -depth 8 -format %c histogram:info:-
        This outputs something like the following:
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
        c = "convert %s -colors 8 -depth 8 -format %%c histogram:info:-" % self.page
        out = self.scanpdf.cmd(c)
        m_line = re.compile(r"""\s*(?P<count>\d+):\s*\(\s*(?P<R>\d+),\s*(?P<G>\d+),\s*(?P<B>\d+).+""")
        colors = []
        for line in out.splitlines():
            match_line = m_line.search(line)
            if match_line:
                logging.debug("Found RGB values")
                color = [int(x) for x in (match_line.group('count'),
                                          match_line.group('R'),
                                          match_line.group('G'),
                                          match_line.group('B'),
                                          )
                         ]
                colors.append(color)
        # sort
        colors.sort(reverse=True, key=lambda y: y[0])
        logging.debug(colors)
        is_color = False
        logging.debug(colors)
        for color in colors:
            # Calculate the mean differences between the RGB components
            # Shades of grey will be very close to zero in this metric...
            diff = float(sum([abs(color[2] - color[1]),
                              abs(color[3] - color[1]),
                              abs(color[3] - color[2]),
                              ])) / 3
            if diff > 20:
                is_color = True
                logging.debug("Found color")
        return is_color


class ScanPdf(object):
    pages = None
    cwd = None
    tmp_dir = None
    args = None
    device = None
    pdf_filename = None
    dpi = None
    keep_blanks = None
    blank_threshold = None
    crop = None
    post_process = None
    text_recognize = None
    """
        The main class.  Performs the following functions:

    """

    def __init__(self):
        """ 
        """
        self.config = None
        self.cwd = os.getcwd()

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
        if self.device is None:
            self._error("Scanning device is undefined!")
        self.cmd('logger -t "scanbd: " "Begin of scan "')
        c = ['scanadf',
             '-d "%s"' % self.device,
             '--source "ADF Duplex"',
             '--mode Color',
             '--resolution %sdpi' % self.dpi,
             '-o %s/page_%%04d' % self.tmp_dir,
             '-y 279.364',
             '--page-height 279.364',
             ]
        self.cmd(c)
        self.cmd('logger -t "scanbd: " "End of scan "')
        file_count = len([name for name in os.listdir(self.tmp_dir) if
                          os.path.isfile(os.path.join(self.tmp_dir, name))])
        logging.info('Receved {0:d} files in {1:}...'.format(file_count, self.tmp_dir))

    @staticmethod
    def _error(msg):
        print("ERROR: %s" % msg)
        sys.exit(-1)

    @staticmethod
    def _atoi(text):
        return int(text) if text.isdigit() else text

    def _natural_keys(self, text):
        """
         alist.sort(key=natural_keys) sorts in human order
         http://nedbatchelder.com/blog/200712/human_sorting.html
         (See Toothy's implementation in the comments)
        :param text:
        :return: sorted
        """
        return [self._atoi(c) for c in re.split('(\d+)', text)]

    def get_pages(self):
        cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        pages = glob.glob('page_*')
        pages.sort(key=self._natural_keys)
        os.chdir(cwd)
        return pages

    def reorder_face_up(self):
        assert len(self.pages) % 2 == 0, "Why is page count not even for duplexing??"
        logging.info("Reordering pages")
        # for i in range(0,len(pages),2):
        # pages[i], pages[i+1] = pages[i+1], pages[i]
        self.pages.reverse()

        # OLD CODE - doesn't work for color images
        # c = 'convert %s -shave 1%%x1%%  -format "%%[fx:mean]" info:' % filename
        # result = self.cmd(c)
        # if float(result.strip()) > self.blank_threshold:
        #     return True
        # else:
        #     return False

    def run_text_recognize(self, pdf_file):
        c = ['pdfsandwich', '-coo', '\"-deskew 40%\"', pdf_file]
        self.cmd(c)
        filename, file_extension = os.path.splitext(pdf_file)
        ocr_file = filename + "_ocr" + file_extension
        os.remove(pdf_file)
        shutil.move(ocr_file, pdf_file)

    @staticmethod
    def save_file(source_file):
        path = None
        _ = wx.App(redirect=True)
        wildcard = "PDF Files (*.pdf)|*.pdf|" \
                   "All files (*.*)|*.*"

        dialog = wx.FileDialog(None, "Choose a file", os.path.expanduser("~"), "", wildcard, wx.SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()

        dialog.Destroy()
        logging.info("Saving from Dialog: " + path)
        shutil.move(source_file, path)

    def run_convert(self, text_recognize):
        os.chdir(self.tmp_dir)
        if self.pdf_filename is not None:
            pdf_basename = os.path.basename(self.pdf_filename)
        else:
            pdf_basename = "temp.pdf"
        ps_filename = pdf_basename
        ps_filename = ps_filename.replace(".pdf", ".ps")
        c = ['convert',
             '-density %s' % self.dpi,
             ' '.join(self.pages),
             ps_filename
             ]
        self.cmd(c)
        c = ['ps2pdf',
             '-DPDFSETTINGS=/prepress',
             ps_filename,
             pdf_basename,
             ]
        self.cmd(c)
        if text_recognize:
            logging.info("running pdf sandwich for text recognition...")
            self.run_text_recognize(pdf_basename)
        if self.pdf_filename is not None:
            shutil.move(pdf_basename, self.pdf_filename)
        else:
            source_file = os.path.join(self.tmp_dir, pdf_basename)
            self.save_file(source_file)
        for filename in self.pages + [ps_filename]:
            os.remove(filename)

        # IF we did the scan, then remove the tmp dir too
        if self.args['scan'] and not self.args['--keep-tmpdir']:
            os.rmdir(self.tmp_dir)
        os.chdir(self.cwd)

    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing
        """
        self.args = argv

        if argv['--verbose']:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        if argv['--debug']:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        if self.args['pdf']:
            if self.args['<pdffile>']:
                self.pdf_filename = os.path.abspath(self.args['<pdffile>'])
                logging.info('saving to file: ' + self.pdf_filename)
            else:
                logging.info('saving file via dialog after processing...')
        self.dpi = self.args['--dpi']
        output_dir = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        if argv['--tmpdir']:
            self.tmp_dir = argv['--tmpdir']
        else:
            self.tmp_dir = os.path.join('/tmp', output_dir)
        self.tmp_dir = os.path.abspath(self.tmp_dir)

        # Make the tmp dir only if we're scanning, o/w throw an error, also get device
        if argv['scan']:
            if argv['--device']:
                self.device = argv['--device'].replace('%', ' ')  # Replace % with spaces to comply with docopt
            else:
                self.device = os.environ.get('SCANBD_DEVICE')
            if os.path.exists(self.tmp_dir):
                self._error("Temporary output directory %s already exists!" % self.tmp_dir)
            else:
                os.makedirs(self.tmp_dir)
        else:
            if not os.path.exists(self.tmp_dir):
                self._error("Scan files directory %s does not exist!" % self.tmp_dir)

        # Blank checks
        self.keep_blanks = argv['--keep-blanks']
        self.blank_threshold = float(argv['--blank-threshold'])
        assert (0 <= self.blank_threshold <= 1.0)
        self.crop = argv['--crop']
        self.text_recognize = argv['--text-recognize']
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
        start = time.time()
        logging.info("Starting: " + time.strftime(date_format))
        logging.info("Temp dir: %s" % self.tmp_dir)
        if self.args['scan']:
            self.run_scan()

        if self.args['pdf']:
            # Now, convert the files to ps
            self.pages = self.get_pages()
            logging.debug(self.pages)
            if self.args['--face-up'] == 'True':  # Default is a text value of 'True'
                self.reorder_face_up()

            start_pages = [(page, self) for page in self.pages]

            threads_to_run = multiprocessing.cpu_count()
            logging.info('Processing pages with {0:d} threads...'.format(threads_to_run))

            pool = Threadpool(threads_to_run)
            results = pool.map(ProcessPage.run, start_pages)
            pool.close()
            pool.join()

            self.pages = [page for page in results if page is not None]

            logging.debug(self.pages)
            self.run_convert(self.text_recognize)

            end = time.time()
            logging.info("End: " + time.strftime(date_format))
            logging.info("Elapsed Time (seconds): {0:.2f}".format(end-start))


def main():
    args = docopt.docopt(__doc__, version='Scan PDF %s' % __version__)
    script = ScanPdf()
    print args
    script.go(args)


if __name__ == '__main__':
    main()
