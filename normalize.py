#!/usr/bin/env python2

# Insert pages into exams, given the correct exam length and
# a special marker on the cover page of each exam.

import os, sys
import pypdftk
import tempfile
from wand.image import Image
from qrtools import QR

TEMP_DIR = "./tmp/"
FRONT_PAGE_CODE = "exam-normalizer-1"
BLANK_PAGE_FILENAME = "blank.pdf"


def split(input_filename):
  """Split the input file given by input_filename into individual pages.
  The page files will be written as PDFs into a temporary directory."""
  output_dirname = tempfile.mkdtemp(dir=TEMP_DIR)
  pages = pypdftk.split(input_filename, output_dirname)
  # Keep only PDFs. PDFTk puts out a document info text file as well.
  pages = [page for page in pages if page.rsplit(".", 1)[1] == "pdf"]
  return pages;

def convert_to_images(input_filenames):
  """ Convert each of the files given by the input filenames into a jpg.
  The files will be written into a temporary directory.
  Return a list of image filenames. """
  image_files = []
  for input_file in input_filenames:
    handle, output_filename = tempfile.mkstemp(dir=TEMP_DIR, suffix=".jpg")
    with Image(filename=input_file, resolution=200) as img:
      img.compression_quality = 70
      img.save(filename=output_filename)
    image_files.append(output_filename)
    os.close(handle)
  return image_files

def is_front_page(image_filename):
  """ Return True if the given image is a front page (based on a QR code)
  or false otherwise. The QR code must contain FRONT_PAGE_CODE to indicate that
  the page is a front page. """
  scanner = QR(filename=image_filename)
  if scanner.decode():
    data = scanner.data
    if data == FRONT_PAGE_CODE:
      return True
  return False

def pad_documents(pages, correct_length):
  """ Insert blank pages into the page list such that the cover pages are separated
  by correct_length pages. "pages" is a list of all the documents' pages, in order.
  pages: a list of tuples, where each tuple is:
    0. The page's PDF filename
    1. The page's image filename
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

def main():
  if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

  pages = split("samples/2samples.pdf")
  images = convert_to_images(pages)
  pages = zip(pages, images)
  padded = pad_documents(pages, 10)
  print padded

  return 0

if __name__ == "__main__":
  sys.exit(main())
