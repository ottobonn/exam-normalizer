# exam-normalizer
Make exams the correct length by reading a QR code on the cover sheet of each
exam, using that to split exams into separate PDFs, and appending blank pages
as needed to ensure all the resulting exams are the same length.

## Installing

exam-normalizer is a Python script implemented in 'normalize.py'.

### Prerequisites

Since exam-normalizer manipulates PDF files, it depends on an installation of
the PDFTk library. In addition, you'll need to have 'zbar', a QR scanning
library, installed. The Python dependencies listed in requirements.txt require
these native libraries to be installed and working (see below for installing
the Python dependencies).

* Python 2 (clearly)
* PDFTk
* zbar
* pip (for the next step)

## Install the dependencies

In the root directory of the repository, run

    pip install -r requirements.txt

to install the python libraries. Or, if you don't want to use pip, have a look
in requirements.txt for the things you'll need to install.

## Usage

    normalize.py [-h] input_file output_file correct_page_count

    Pad exams with blank pages.

    positional arguments:
      input_file          the filename of the PDF of exams
      output_file         the filename of the resulting PDF of padded exams
      correct_page_count  the correct number of pages per exam

    optional arguments:
      -h, --help          show this help message and exit

### Usage example

Let's say I have scanned several exams into 'exams.pdf'. Each exam is supposed
to have 8 pages, but students might have ripped some out. I give
exam-normalizer:

* the name of the collection of exams, followed by
* the name of the PDF file it should produce, followed by
* the correct number of pages in an exam.

In this case, to create a file called 'normalized.pdf':

    ./normalize.py exams.pdf normalized.pdf 8

It might take a while to run; it has to convert each page to an image and scan
it for QR codes.
