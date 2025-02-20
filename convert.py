#! /usr/bin/env python3

import argparse
import os.path
import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


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


class CMarkdownConverter(MarkdownConverter):

    """Convert HTML to Markdown for C document titles."""

    class Options(MarkdownConverter.DefaultOptions):
        escape_misc = True


def convert_to_md(content):
    """Convert some HTML content to Markdown."""
    soup = BeautifulSoup(content, 'html5lib')
    return CMarkdownConverter().convert_soup(soup).strip()


def get_ndoc_data():
    """Get the data from the document log."""
    with open(LOCAL_DOCS_LOG, 'r', encoding='utf-8') as f:
        text = f.read()
    text = re.sub(r'^.*?<h4 align=left>Last Update: .*?<hr>\s*<!--.*?-->\s*',
                  '', text, flags=re.DOTALL)
    text = re.sub(r'<hr>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->\s*', '', text, flags=re.DOTALL)
    data = {}
    months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
              'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
              'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    for line in re.split(r'\s*<br>\s*', text):
        if not line:
            continue
        m = re.fullmatch(r'<span class="nolink">N([0-9]+)</span>\s+(.*)', line)
        if m:
            link = None
            nnum = m.group(1)
            line = m.group(2)
        else:
            m = re.fullmatch(r'<a href=([^>]*)>N([0-9]+)</a>\s+(.*)', line)
            if m:
                link = m.group(1).strip('"').replace(
                    'http://www.open-std.org/',
                    'https://www.open-std.org/')
                link = urllib.parse.urljoin(WG14_DOCS_LOG, link)
                nnum = m.group(2)
                line = m.group(3)
            else:
                raise ValueError('could not parse line: %s' % line)
        if line == 'Not assigned.':
            continue
        m = re.fullmatch(r'(20[0-2][0-9])/([01][0-9])/([0-3][0-9])\s+(.*)',
                         line)
        if m:
            date = '%s-%s-%s' % (m.group(1), m.group(2), m.group(3))
            line = m.group(4)
        else:
            # Typo on one line in list (N1112).
            line = line.replace('21-Mat-2005', '21-Mar-2005')
            # Six lines N953 through N958 use this abbreviation.
            line = line.replace('-Sept-2001', '-Sep-2001')
            # One line N659 has this in place of a full date.
            line = line.replace('nn-Feb-97', '09-Feb-97')
            m = re.fullmatch(r'([0-3][0-9])-([A-Z][a-z]{2})-(200[1-5])\s+(.*)',
                             line)
            if m:
                date = '%s-%s-%s' % (m.group(3), months[m.group(2)], m.group(1))
                line = m.group(4)
            else:
                m = re.fullmatch(
                    r'([0-3][0-9])[- ]([A-Z][a-z]{2})[- ]([089][0-9])\s+(.*)',
                    line)
                if m:
                    year = m.group(3)
                    if year.startswith('0'):
                        year = '20%s' % year
                    else:
                        year = '19%s' % year
                    date = '%s-%s-%s' % (year, months[m.group(2)], m.group(1))
                    line = m.group(4)
                else:
                    raise ValueError('could not parse date: %s' % line)
        # Cases with no author where the first word can sensibly be
        # used as an author.
        if ',' not in line:
            if nnum == '1569':
                line = line.replace('Jones - ', 'Jones, ')
            if nnum == '245':
                line = line.replace('Plum ', 'Plum, ')
            if nnum == '189':
                line = line.replace('WG21 ', 'WG21, ')
            if nnum == '185':
                line = line.replace('UK ', 'UK, ')
            if nnum == '104':
                line = line.replace('ITSCJ ', 'ITSCJ, ')
        # This one starts with a comma.
        if nnum == '868':
            line = line.lstrip(',')
        # This one has a comma but not after the author.
        if nnum == '1570':
            line = line.replace('Jones - ', 'Jones, ')
        line_split = line.split(',', 1)
        if len(line_split) == 1:
            line_split = ('WG14', line_split[0])
        author = line_split[0].strip()
        title = line_split[1].strip().rstrip('.')
        # Where the title starts with a standard number, do not treat
        # it as an author.
        if author.startswith('ISO/IEC '):
            title = '%s, %s' % (author, title)
            author = 'WG14'
        # Sometimes &amp; is used (or plain & in one place), sometimes "and".
        author = author.replace('&amp;', 'and')
        author = author.replace('&', 'and')
        # Remove unnecessary markup before Markdown conversion.
        title = title.replace('<b>', '')
        title = title.replace('</b>', '')
        title = re.sub('<a href=[^>]*>', '', title)
        title = title.replace('</a>', '')
        # One stray unescaped >, one ^.
        title = title.replace(' > ', ' &gt; ')
        title = title.replace(' & ', ' &amp; ')
        # One title with '`' not intended as Markdown.
        title = title.replace('``', '&ldquo;')
        title = title.replace("''", '&rdquo;')
        # One title with <i> inside <code>, swap for Markdown.
        title = title.replace(
            '<code>UINT<i>N</i>_C</code>',
            '<code>UINT</code><i><code>N</code></i><code>_C</code>')
        # If the title contains `, it's already meant as Markdown;
        # otherwise, convert it.
        if '`' not in title:
            title = convert_to_md(title)
        if nnum in data:
            raise ValueError('duplicate N%s' % nnum)
        data[nnum] = {'link': link,
                      'date': date,
                      'author': author,
                      'title' : title}
    return data


def action_convert():
    """Convert the document log to JSON metadata."""
    data = get_ndoc_data()
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
