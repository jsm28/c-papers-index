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


# The base URL for all WG14 documents.
WG14_BASE = 'https://www.open-std.org/jtc1/sc22/wg14/'


# The normal URL start for a WG14 document.
WG14_DOC = WG14_BASE + 'www/docs/n'


# The protected URL start for a WG14 document.
WG14_DOC_PROT = WG14_BASE + 'prot/n'


# The historic URL start for a WG14 document.
WG14_DOC_HIST = WG14_BASE + 'www/docs/historic/n'


# The historic URL start for a WG14 document, variant.
WG14_DOC_HIST0 = WG14_BASE + 'www/docs/historic/n0'


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
                exp_url_1 = WG14_DOC + nnum + '.'
                exp_url_2 = WG14_DOC_PROT + nnum + '.'
                exp_url_3 = WG14_DOC_HIST + nnum + '.'
                exp_url_4 = WG14_DOC_HIST0 + nnum + '.'
                if not (link.startswith(exp_url_1)
                        or link.startswith(exp_url_2)
                        or link.startswith(exp_url_3)
                        or link.startswith(exp_url_4)):
                    print('unexpected URL for N%s: %s' % (nnum, link))
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
        # Erroneous date in the list.
        if nnum == '1559':
            date = '2011-03-14'
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
    '3408': 'cadm',
    '3328': 'cpub',
    '3251': 'cm',
    '3171': 'cadm',
    '3118': 'cadm',
    '3088': 'cpub',
    '3057': 'cpub',
    '3054': 'cpub',
    '3005': 'cpub',
    '3002': 'cadm',
    '2947': 'cadm',
    '2784': 'cadm',
    '2733': 'cpub',
    '2676': 'cpub',
    '2664': 'cadm',
    '2652': 'cadm',
    '2627': 'cadm',
    '2613': 'cadm',
    '2577': 'cpub',
    '2240': 'cpub',
    '2183': 'cadm',
    '2181': 'cm',
    '2177': 'cpub',
    '2176': 'cpub',
    '2131': 'c',
    '2071': 'cadm',
    '2058': 'cpub',
    '2011': 'cpub',
    '2010': 'cpub',
    '2004': 'cpub',
    '1974': 'cpub',
    '1968': 'cpub',
    '1950': 'cpub',
    '1949': 'cpub',
    '1946': 'cpub',
    '1945': 'cpub',
    '1940': 'cpub',
    '1939': 'cpub',
    '1933': 'cm',
    '1926': 'cpub',
    '1924': 'cpub',
    '1919': 'cpub',
    '1912': 'cpub',
    '1897': 'cpub',
    '1896': 'cpub',
    '1892': 'cpub',
    '1891': 'cpub',
    '1862': 'cpub',
    '1852': 'cpub',
    '1851': 'cpub',
    '1846': 'cpub',
    '1836': 'cpub',
    '1835': 'cpub',
    '1832': 'cpub',
    '1814': 'cpub',
    '1810': 'cpub',
    '1809': 'cpub',
    '1805': 'cadm',
    '1799': 'cm',
    '1797': 'cpub',
    '1796': 'cpub',
    '1790': 'cpub',
    '1789': 'cpub',
    '1788': 'cm',
    '1785': 'cpub',
    '1784': 'cpub',
    '1781': 'cpub',
    '1778': 'cpub',
    '1775': 'cpub',
    '1774': 'cpub',
    '1772': 'cfptca',
    '1761': 'cpub',
    '1760': 'c',
    '1758': 'cpub',
    '1757': 'cpub',
    '1756': 'cpub',
    '1724': 'cpub',
    '1722': 'cpub',
    '1709': 'cfptca',
    '1701': 'c',
    '1700': 'c',
    '1699': 'c',
    '1689': 'cfptcm',
    '1686': 'cm',
    '1680': 'cpub',
    '1679': 'cpub',
    '1678': 'cfptca',
    '1676': 'cpub',
    '1669': 'cpub',
    '1664': 'cpub',
    '1663': 'cpub',
    '1657': 'cpub',
    '1656': 'cpub',
    '1644': 'cadm',
    '1638': 'cadm',
    '1632': 'cpub',
    '1631': 'cpub',
    '1624': 'cpub',
    '1622': 'cadm',
    '1616': 'cadm',
    '1615': 'cpub',
    '1609': 'cpub',
    '1608': 'cadm',
    '1607': 'cadm',
    '1606': 'cpub',
    '1605': 'cpub',
    '1591': 'cpub',
    '1590': 'cadm',
    '1583': 'c',
    '1579': 'cpub',
    '1578': 'cpub',
    '1574': 'cm',
    '1570': 'cpub',
    '1569': 'cpub',
    '1455': 'cm',
    '1407': 'cadm',
    '1393': 'cpub',
    '1390': 'cadm',
    '1388': 'cpub',
    '1336': 'cpub',
    '1314': 'cadm',
    '1312': 'cpub',
    '1307': 'cadm',
    '1292': 'cpub',
    '1290': 'cpub',
    '1275': 'cpub',
    '1274': 'cadm',
    '1268': 'cadm',
    '1256': 'cpub',
    '1247': 'c',
    '1245': 'cadm',
    '1244': 'cpub',
    '1243': 'cpub',
    '1242': 'cpub',
    '1241': 'cpub',
    '1235': 'cpub',
    '1230': 'cadm',
    '1225': 'cpub',
    '1205': 'cpub',
    '1202': 'cpub',
    '1201': 'cpub',
    '1199': 'cpub',
    '1197': 'c',
    '1193': 'cpub',
    '1192': 'cadm',
    '1180': 'cpub',
    '1173': 'cpub',
    '1172': 'cpub',
    '1169': 'cpub',
    '1167': 'cadm',
    '1161': 'cpub',
    '1154': 'cpub',
    '1150': 'cpub',
    '1149': 'cpub',
    '1147': 'cpub',
    '1146': 'cpub',
    '1143': 'cpub',
    '1142': 'cpub',
    '1137': 'cpub',
    '1135': 'cpub',
    '1129': 'cadm',
    '1127': 'cadm',
    '1126': 'cpub',
    '1125': 'cpub',
    '1124': 'cpub',
    '1120': 'cpub',
    '1118': 'c',
    '1107': 'cpub',
    '1106': 'c',
    '1096': 'cpub',
    '1095': 'cpub',
    '1089': 'cpub',
    '1087': 'cpub',
    '1082': 'cadm',
    '1077': 'cpub',
    '1071': 'cpub',
    '1060': 'cpub',
    '1059': 'cpub',
    '1057': 'cpub',
    '1055': 'cpub',
    '1051': 'cpub',
    '1040': 'cpub',
    '1038': 'cadm',
    '1031': 'cpub',
    '1030': 'cadm',
    '1027': 'c',
    '1021': 'cpub',
    '1016': 'cpub',
    '1010': 'cpub',
    '1005': 'cpub',
    '996': 'cpub',
    '994': 'cadm',
    '979': 'cpub',
    '966': 'cadm',
    '957': 'cpub',
    '949': 'cpub',
    '948': 'cpub',
    '940': 'cpub',
    '937': 'cpub',
    '932': 'cpub',
    '931': 'cadm',
    '930': 'cadm',
    '925': 'c',
    '922': 'cadm',
    '906': 'cadm',
    '904': 'cmm',
    '897': 'cpub',
    '895': 'c',
    '881': 'cpub',
    '854': 'cpub',
    '850': 'cpub',
    '878': 'cpub',
    '806': 'cpub',
    '802': 'cpub',
    '800': 'cpub',
    '798': 'cadm',
    '679': 'cadm',
    '674': 'cpub',
    '643': 'cpub',
    '627': 'cadm',
    '624': 'cpub',
    '621': 'cpub',
    '610': 'cadm',
    '585': 'cadm',
    '577': 'cadm',
    '559': 'cpub',
    '556': 'cadm',
    '554': 'cadm',
    '553': 'cadm',
    '549': 'cm',
    '543': 'cadm',
    '542': 'cadm',
    '524': 'cpub',
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
        elif "committee draft" in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif "editor's report" in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif "editor report" in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif "editor progress report" in ndata['maintitle'].lower():
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
        elif 'compendium' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'cr summary' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'clarification request summary' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'dr report' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'defect report summary' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'thread-based parallelism' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'latex' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'dts 17961' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'wdtr' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'fp teleconference' in ndata['maintitle'].lower() and 'agenda' in ndata['maintitle'].lower():
            ndata['class'] = 'cfptca'
        elif 'c floating point study group teleconference' in ndata['maintitle'].lower():
            ndata['class'] = 'cfptca'
        elif 'fp teleconference' in ndata['maintitle'].lower() and ('minutes' in ndata['maintitle'].lower() or 'notes' in ndata['maintitle'].lower()):
            ndata['class'] = 'cfptcm'
        elif 'fp meeting minutes' in ndata['maintitle'].lower():
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
        elif 'meeting information' in ndata['maintitle'].lower():
            ndata['class'] = 'cm'
        elif 'hotel' in ndata['maintitle'].lower():
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
        elif 'progress report' in ndata['maintitle'].lower():
            ndata['class'] = 'cadm'
        elif 'annual report' in ndata['maintitle'].lower():
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


# Documents to exclude in consideration (C23 ballot comments) despite
# postdating cut-off date.
EXTRA_EXCLUDE = {
    '3191', '3216'}


def generate_cdocs(data):
    """Generate C-document data from groups of N-documents."""
    cdocs = []
    for nnum, ndata in data.items():
        if ndata['class'] == 'c':
            convert_doc = (ndata['date'] >= '2023-10-01' and nnum not in EXTRA_EXCLUDE) or nnum in EXTRA_INCLUDE
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
    # improving the classification logic, and a list of paper
    # locations on the WG14 website, for link checking.
    text_list = []
    url_list = []
    for nnum, ndata in data.items():
        text_list.append('%s\tN%s %s %s, %s'
                         % (ndata['cid'] if 'cid' in ndata else ndata['class'],
                            nnum, ndata['date'], ndata['author'],
                            ndata['title']))
        if ndata['link'] and ndata['link'].startswith(WG14_BASE):
            url_list.append(ndata['link'][len(WG14_BASE):])
    with open('tmp-papers-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_list) + '\n')
    with open('tmp-file-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(url_list) + '\n')


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
