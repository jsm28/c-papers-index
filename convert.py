#! /usr/bin/env python3

import argparse
import collections
import json
import os
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
                      'title': title}
    return data


# Documents where the default classification based on heuristics
# applied to the title should be overridden.
OVERRIDE_CLASS = {
    '3489': 'cpub',
    '3408': 'cadm',
    '3328': 'cpub',
    '3191': 'cpub',
    '3171': 'cadm',
    '3135': 'cpub',
    '3118': 'cadm',
    '3117': 'cpub',
    '3105': 'cpub',
    '3103': 'cpub',
    '3102': 'cpub',
    '3101': 'cpub',
    '3098': 'cpub',
    '3092': 'cpub',
    '3090': 'cpub',
    '3088': 'cpub',
    '3082': 'cpub',
    '3081': 'cpub',
    '3080': 'cpub',
    '3079': 'cpub',
    '3078': 'cpub',
    '3077': 'cpub',
    '3076': 'cpub',
    '3073': 'cpub',
    '3072': 'cpub',
    '3071': 'cpub',
    '3070': 'cpub',
    '3057': 'cpub',
    '3054': 'cpub',
    '3005': 'cpub',
    '3002': 'cadm',
    '2784': 'cadm',
    '2733': 'cpub',
    '2676': 'cpub',
    '2652': 'cadm',
    '2613': 'cadm',
    '2577': 'cpub',
    }


# Remapping main titles to help in grouping.
REMAP_TITLE = {
    '`if`declarations': '`if` declarations',
    '`if` declarations, v5, wording improvements': '`if` declarations',
    'Transparent Function Aliases': 'Transparent Aliases',
    'Restartable and Non-Restartable Functions for Efficient Character Conversions': 'Restartable Functions for Efficient Character Conversion',
    'Restartable Functions for Efficient Character Conversions': 'Restartable Functions for Efficient Character Conversion',
    'The Big Array Size Survey': 'Big Array Size Survey',
    'Improved \\_\\_attribute\\_\\_((cleanup(…))) through defer': 'Improved \\_\\_attribute\\_\\_((cleanup(...))) through defer',
    'Improved \\_\\_attribute\\_\\_((cleanup(...))) Through defer': 'Improved \\_\\_attribute\\_\\_((cleanup(...))) through defer',
    'Revision 2 Of Defect With Wording Of restrict Specification': 'Defect with wording of restrict specification',
    'New pointer-proof keyword to determine array length': 'New \\_Lengthof() operator',
    'New nelementsof() operator': 'New \\_Lengthof() operator',
    '\\_Lengthof \\- New pointer-proof keyword to determine array length': 'New \\_Lengthof() operator',
    'The `void`-_which-binds_, v2: typesafe parametric polymorphism': 'The `void`-_which-binds_: typesafe parametric polymorphism',
    'embed Synchronization': '#embed Synchronization',
    'Literal suffixes for size\\_t': 'Literal Suffixes for size\\_t',
    'C2y fopen "p" and bring fopen’s mode closer to POSIX': 'fopen "p" and bring fopen’s mode closer to POSIX 202x',
    'Accessing arrays of character type': 'Accessing byte arrays',
    'Usage of "length", "size", "count", etc. in context of retrieving array length': 'Words used for retrieving number of elements in arrays and array-like objects across computer languages',
    'Obsolete implicitly octal literals': 'Obsolete implicitly octal literals and add delimited escape sequences',
    'restrict atomic\\_flag creation': 'Restrict atomic\\_flag creation',
    'Preprocessing integer expressions': 'Preprocessor integer expressions',
    'Pitch for dialect directive': 'Pitch for #dialect directive'}


# Titles that should not be grouped (same title used for more than one
# paper).
NO_GROUP_TITLE = {
    'Composite types'}


def classify_docs(data):
    """Apply heuristic classification to N-documents."""
    by_title = collections.defaultdict(set)
    for nnum, ndata in data.items():
        ndata['group'] = {nnum}
        m = re.fullmatch(
            r'(.*?)((?:[. ,(]+(?:[Uu]pdates?[: ]+(?:[Nnrv][0-9.]+)|(?:[rRvV]|[rR]evision|[vV]ersion)\.? ?[0-9.]+)[. ,)]*)+)',
            ndata['title'])
        if m:
            ndata['maintitle'] = m.group(1)
            ndata['auxtitle'] = m.group(2).lstrip(' ,.')
            if ndata['auxtitle'].startswith('(') and ndata['auxtitle'].endswith(')'):
                ndata['auxtitle'] = ndata['auxtitle'].lstrip('(').rstrip(')')
        else:
            ndata['maintitle'] = ndata['title']
            ndata['auxtitle'] = None
        if 'working draft' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif "editor's report" in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'dts draft' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'revision draft' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'dis draft' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'examples of undefined behavior' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'ts proposal' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'generalized function calls' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'ballot comment' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'disposition' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'cfp teleconference agenda' in ndata['maintitle'].lower():
            ndata['class'] = 'cfptca'
        elif 'cfp teleconference minutes' in ndata['maintitle'].lower():
            ndata['class'] = 'cfptcm'
        elif 'agenda' in ndata['maintitle'].lower():
            ndata['class'] = 'cma'
        elif 'minutes' in ndata['maintitle'].lower():
            ndata['class'] = 'cmm'
        elif 'agneda' in ndata['maintitle'].lower():
            # Typo in papers list.
            ndata['class'] = 'cma'
        elif 'munutes' in ndata['maintitle'].lower():
            # Typo in papers list.
            ndata['class'] = 'cmm'
        elif 'venue' in ndata['maintitle'].lower():
            ndata['class'] = 'cm'
        elif 'invitation' in ndata['maintitle'].lower():
            ndata['class'] = 'cm'
        elif 'charter' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'schedule' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'liaison report' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'liaison statement' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'compat teleconference' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'omnibus' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'business plan' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'standing document' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'misra' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'call for' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        else:
            ndata['class'] = 'c'
        if nnum in OVERRIDE_CLASS:
            ndata['class'] = OVERRIDE_CLASS[nnum]
        if ndata['class'] == 'c':
            group_title = ndata['maintitle']
            if group_title in REMAP_TITLE:
                group_title = REMAP_TITLE[group_title]
            if group_title not in NO_GROUP_TITLE:
                by_title[group_title].add(nnum)
    # Group documents with the same main title together.
    for nnum, ndata in data.items():
        if ndata['class'] == 'c':
            group_title = ndata['maintitle']
            if group_title in REMAP_TITLE:
                group_title = REMAP_TITLE[group_title]
            if group_title not in NO_GROUP_TITLE:
                ndata['group'].update(by_title[group_title])
    # Group documents explicitly said to update another together.
    changed = True
    while changed:
        changed = False
        for nnum, ndata in data.items():
            if ndata['class'] != 'c':
                continue
            if ndata['auxtitle'] is None:
                continue
            m = re.search('[Uu]pdates?[: ][Nn]([0-9]+)', ndata['auxtitle'])
            if m:
                onum = m.group(1)
                if onum not in ndata['group']:
                    changed = True
                    ndata['group'] |= data[onum]['group']
                    for n in ndata['group']:
                        if data[n]['group'] != ndata['group']:
                            data[n]['group'] |= ndata['group']


# Documents to include in consideration (mentioned for possible future
# scheduling in agendas, or discussed for C2Y) despite predating
# cut-off date.
EXTRA_INCLUDE = {
    '2658', '2948', '2995', '3051', '3064', '3160', '3025', '3058'}


def generate_cdocs(data):
    """Generate C-document data from groups of N-documents."""
    cdocs = []
    for nnum, ndata in data.items():
        if ndata['class'] == 'c':
            convert_doc = ndata['date'] >= '2023-10-01' or nnum in EXTRA_INCLUDE
            if int(nnum) != max(int(n) for n in ndata['group']):
                continue
            for n in ndata['group']:
                data[n]['convert-doc'] = convert_doc
            if convert_doc:
                cdoc = {
                    'sortkey': min((data[n]['date'], int(n))
                                   for n in ndata['group']),
                    'title': ndata['maintitle'],
                    'author': ndata['author'],
                    'nums': sorted(ndata['group'], key=int)
                    }
                cdocs.append(cdoc)
    cdocs.sort(key=lambda x: x['sortkey'])
    for num, doc in enumerate(cdocs, start=4000):
        doc['id'] = 'C%d' % num
        for rev, num in enumerate(doc['nums'], start=1):
            data[num]['cdoc-rev'] = rev
    return cdocs


def action_convert():
    """Convert the document log to JSON metadata."""
    data = get_ndoc_data()
    classify_docs(data)
    cdocs = generate_cdocs(data)
    for doc in cdocs:
        doc_json = {
            'id': doc['id'],
            'author': doc['author'],
            'title': doc['title'],
            'revisions': []}
        for n in doc['nums']:
            ndata = data[n]
            ndoc = {
                'rev-id': 'r%d' % ndata['cdoc-rev'],
                'id': '%sr%d' % (doc['id'], ndata['cdoc-rev']),
                'doc-id': doc['id'],
                'author': ndata['author'],
                'title': ndata['title'],
                'date': ndata['date'],
                'ext-id': 'N%s' % n,
                'ext-url': ndata['link']}
            doc_json['revisions'].append(ndoc)
            ndata['cid'] = ndoc['id']
        out_dir = os.path.join('out', 'papers', 'C', doc['id'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'metadata.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(doc_json, f, indent=4, sort_keys=True)
    # Also generate a text list of all papers, for convenience in
    # improving the classification logic.
    text_list = []
    for nnum, ndata in data.items():
        text_list.append('%s\tN%s %s %s, %s'
                         % (ndata['cid'] if 'cid' in ndata else ndata['class'],
                            nnum, ndata['date'], ndata['author'],
                            ndata['title']))
    with open('tmp-papers-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_list) + '\n')


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
