#!/usr/bin/env python

# Insert pages into exams, given the correct exam length and
# a special marker on the cover page of each exam.

import os
import sys
import argparse
import tempfile
from wand.image import Image
from qrtools import QR
from multiprocessing import Pool

# hack to get pypdftk to import correctly on mac
if not os.path.exists('/usr/bin/pdftk'):
    os.environ['PDFTK_PATH'] = '/usr/local/bin/pdftk'
import pypdftk

FRONT_PAGE_CODE = "exam-normalizer-1"
BLANK_PAGE_FILENAME = "blank.pdf"

class Document(object):
    """Class representing a document. Automatically handles padding to the
    correct length."""
    def __init__(self, target_length):
        self._scans = []
        self.target_length = target_length

    def add_page(self, page):
        """Page should be a tuple of (pdf filename, image filename)."""
        self._scans.append(page)

    @property
    def pages(self):
        """Returns the list of pages added to this document so far, with
        padding to a multiple of the target length."""
        padding = [(BLANK_PAGE_FILENAME, None)]
        return self._scans + padding*(-len(self._scans) % self.target_length)

    @property
    def pdf_pages(self):
        """As pages, but returns only the pdfs, not associated images."""
        return [pdf for pdf, _ in self.pages]

    @property
    def isPadded(self):
        return len(self._scans) < self.target_length


def split(input_filename):
    """Split the input file given by input_filename into individual pages.
    The page files will be written as PDFs into a temporary directory.
    Returns a tuple, where the first element is the output directory name,
    and the second is the list of PDFs of the pages."""
    pdf_directory = tempfile.mkdtemp(dir="./")
    pages = pypdftk.split(input_filename, pdf_directory)
    # Keep only PDFs. PDFTk puts out a document info text file as well, which
    # we delete.
    pdfs = []
    for page in pages:
        if page.rsplit(".", 1)[1] == "pdf":
            pdfs.append(page)
        else:
            os.remove(page)
    return (pdf_directory, pdfs)

def convert_file_to_image(file_dir_tuple):
    """Convert a single file into a jpg. Helper function to convert_to_images.
    input_file and output_dir are received as a tuple so this can be more easily
    used with Pool.map."""
    input_file, image_directory = file_dir_tuple
    handle, output_filename = tempfile.mkstemp(dir=image_directory,
                                               suffix=".jpg")
    with Image(filename=input_file, resolution=60) as img:
        img.compression_quality = 90
        img.save(filename=output_filename)
    os.close(handle)
    return output_filename

def convert_to_images(input_filenames):
    """ Convert each of the files given by the input filenames into a jpg.
    The files will be written into a temporary directory.
    Return a tuple, where the first element is the directory created to hold
    the images, and the second is a list of image filenames. """
    pool = Pool(4)
    image_directory = tempfile.mkdtemp(dir="./")
    # pack arguments to convert_file_to_image
    input_filenames = zip(input_filenames,
                          [image_directory]*len(input_filenames))
    image_files = pool.map(convert_file_to_image,
                           input_filenames)
    return (image_directory, image_files)

def is_front_page(image_filename):
    """ Return True if the given image is a front page (based on a QR code)
    or false otherwise. The QR code must contain FRONT_PAGE_CODE to indicate
    that the page is a front page. """
    scanner = QR(filename=image_filename)
    if scanner.decode():
        data = scanner.data
        if data == FRONT_PAGE_CODE:
            return True
    return False

def split_documents(pages, correct_length):
    """Given a list of all the documents' pages in order, detects cover pages
    and splits into Documents.
    pages: a list of tuples, where each tuple is:
           0. The page's PDF filename
           1. The page's image filename
    Returns a list of Documents.
    """
    documents = []
    cur_doc = Document(correct_length)
    for page_tuple in pages:
        _, image_name = page_tuple
        if is_front_page(image_name):
            documents.append(cur_doc)
            cur_doc = Document(correct_length)
        cur_doc.add_page(page_tuple)
    documents.append(cur_doc)
    return documents


def main(input_filename, output_filename, correct_length):
    pdf_directory, pages = split(input_filename)
    image_directory, images = convert_to_images(pages)
    pages_with_images = zip(pages, images)

    docs = split_documents(pages_with_images, correct_length)
    # split into docs with and without padding
    good_docs = [doc for doc in docs if not doc.isPadded]
    padded_docs = [doc for doc in docs if doc.isPadded]
    # flatten and pull out just the pdf filenames
    good_pdfs = [pdf for doc in good_docs for pdf in doc.pdf_pages]
    padded_pdfs = [pdf for doc in padded_docs for pdf in doc.pdf_pages]

    if len(good_pdfs) > 0:
        pypdftk.concat(good_pdfs, output_filename + '_good.pdf')
    if len(padded_pdfs) > 0:
        pypdftk.concat(padded_pdfs, output_filename + '_padded.pdf')

    # cleanup temp files
    for pdf_name, image_name in pages_with_images:
        os.remove(pdf_name)
        os.remove(image_name)
    os.rmdir(pdf_directory)
    os.rmdir(image_directory)

    print("Merged results written to {0}_good.pdf and {0}_padded.pdf".format(
        output_filename))
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pad exams with blank pages.')
    parser.add_argument('input_file', type=str, nargs=1,
                        help='the filename of the PDF of exams')
    parser.add_argument('output_file', type=str, nargs=1,
                    help='the filename prefix for the resulting PDFs of padded exams')
    parser.add_argument('correct_page_count', type=int, nargs=1,
                    help='the correct number of pages per exam')

    args = parser.parse_args()
    input_filename = args.input_file[0]
    output_filename = args.output_file[0]
    correct_length = args.correct_page_count[0]
    sys.exit(main(input_filename, output_filename, correct_length))
