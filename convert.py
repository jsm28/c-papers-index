#! /usr/bin/env python3

import argparse
import os.path
import urllib.request


# The location of the WG14 document log.
WG14_DOCS_LOG = 'https://www.open-std.org/jtc1/sc22/wg14/www/wg14_document_log.htm'


# The location of the local document log copy.
LOCAL_DOCS_LOG = os.path.join('in', 'wg14_document_log.htm')


def download_wg14_doc(doc):
    """Download a file from the WG14 website."""
    urllib.request.urlretrieve(doc_url(doc), filename=input_filename(doc))
    time.sleep(1)


def action_download():
    """Download the document log."""
    urllib.request.urlretrieve(WG14_DOCS_LOG, filename=LOCAL_DOCS_LOG)


def action_convert():
    """Convert the document log to JSON metadata."""
    # TODO


def main():
    """Main program."""
    parser = argparse.ArgumentParser(
        description='Convert WG14 document log to JSON metadata')
    parser.add_argument('action',
                        help='What to do',
                        choices=('download', 'convert'))
    args = parser.parse_args()
    action_map = {'download': action_download, 'convert': action_convert}
    action_map[args.action]()


if __name__ == '__main__':
    main()
