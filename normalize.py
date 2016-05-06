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

def pad_documents(pages, correct_length):
    """ Insert blank pages into the page list such that the cover pages are
    separated by correct_length pages. "pages" is a list of all the documents'
    pages, in order.
    pages: a list of tuples, where each tuple is:
    0. The page's PDF filename
    1. The page's image filename
    Returns the augmented list of pages and images.
    """
    # Start with a correct_length document already "processed", so we don't try
    # to pad before the very first cover page.
    new_pages = []
    for page_tuple in pages:
        _, image_name = page_tuple
        if is_front_page(image_name):
            new_pages += [(BLANK_PAGE_FILENAME, None)]*(-len(new_pages)%correct_length)
        new_pages.append(page_tuple)
    # Pad last document to correct length
    new_pages += [(BLANK_PAGE_FILENAME, None)]*(-len(new_pages)%correct_length)
    return new_pages

def main(input_filename, output_filename, correct_length):
    pdf_directory, pages = split(input_filename)
    image_directory, images = convert_to_images(pages)
    pages_with_images = zip(pages, images)
    padded = pad_documents(pages_with_images, correct_length)
    padded_pdfs = [page_tuple[0] for page_tuple in padded]
    merged_filename = pypdftk.concat(padded_pdfs, output_filename)
    for pdf_name, image_name in pages_with_images:
        os.remove(pdf_name)
        os.remove(image_name)
    os.rmdir(pdf_directory)
    os.rmdir(image_directory)
    print("Merged result written to " + merged_filename + ".")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pad exams with blank pages.')
    parser.add_argument('input_file', type=str, nargs=1,
                        help='the filename of the PDF of exams')
    parser.add_argument('output_file', type=str, nargs=1,
                    help='the filename of the resulting PDF of padded exams')
    parser.add_argument('correct_page_count', type=int, nargs=1,
                    help='the correct number of pages per exam')

    args = parser.parse_args()
    input_filename = args.input_file[0]
    output_filename = args.output_file[0]
    correct_length = args.correct_page_count[0]
    sys.exit(main(input_filename, output_filename, correct_length))
