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
                      'title': title,
                      'meetings': set()}
    return data


# Documents where the default classification based on heuristics
# applied to the title should be overridden.
OVERRIDE_CLASS = {
    '3584': 'cm',
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
    '1191': 'cpub',
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
    '998': 'cpub',
    '996': 'cpub',
    '994': 'cadm',
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
    '908': 'c',
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
    '667': 'cpub',
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
    '544': 'cpub',
    '543': 'cadm',
    '542': 'cadm',
    '536': 'cpub',
    '524': 'cpub',
    '491': 'cpub',
    '482': 'cm',
    '460': 'cadm',
    '457': 'cpub',
    '442': 'cadm',
    '441': 'cpub',
    '440': 'cpub',
    '439': 'cpub',
    '438': 'cpub',
    '437': 'cm',
    '433': 'c',
    '428': 'cadm',
    '425': 'cpub',
    '423': 'cpub',
    '412': 'cpub',
    '403': 'cpub',
    '399': 'cadm',
    '394': 'cadm',
    '385': 'cpub',
    '382': 'cadm',
    '380': 'cadm',
    '377': 'cpub',
    '373': 'cadm',
    '366': 'cadm',
    '360': 'cadm',
    '351': 'cadm',
    '347': 'cpub',
    '346': 'cadm',
    '341': 'cadm',
    '337': 'cadm',
    '333': 'cpub',
    '332': 'cpub',
    '329': 'cadm',
    '325': 'cpub',
    '315': 'cadm',
    '314': 'cadm',
    '294': 'cm',
    '293': 'cm',
    '290': 'cpub',
    '289': 'cpub',
    '288': 'cpub',
    '284': 'cpub',
    '277': 'cpub',
    '266': 'cm',
    '263': 'cpub',
    '261': 'cadm',
    '260': 'cpub',
    '259': 'cpub',
    '254': 'cadm',
    '284': 'cpub',
    '246': 'cpub',
    '245': 'cpub',
    '233': 'cadm',
    '232': 'cadm',
    '231': 'cadm',
    '229': 'cm',
    '210': 'cpub',
    '205': 'cpub',
    '192': 'cadm',
    '191': 'cadm',
    '189': 'c',
    '187': 'cadm',
    '182': 'cpub',
    '180': 'cpub',
    '179': 'cadm',
    '178': 'cadm',
    '177': 'cadm',
    '174': 'cm',
    '169': 'cpub',
    '163': 'cadm',
    '145': 'cpub',
    '137': 'cm',
    '132': 'cadm',
    '127': 'cm',
    '119': 'cpub',
    '116': 'cpub',
    '109': 'cm',
    '108': 'cadm',
    '104': 'cpub',
    '101': 'cpub',
    '097': 'cadm',
    '093': 'cadm',
    '080': 'cadm',
    '078': 'cadm',
    '073': 'c',
    '067': 'cpub',
    '064': 'cadm',
    '061': 'cadm',
    '058': 'cadm',
    '057': 'cadm',
    '048': 'cadm',
    '045': 'cadm',
    '039': 'cadm',
    '038': 'cm',
    '037': 'cadm',
    '036': 'cadm',
    '021': 'cadm',
    '013': 'cm',
    }


# Remapping main titles to help in grouping.
REMAP_TITLE = {
    '`if`declarations': '`if` declarations',
    '`if` declarations, v5, wording improvements': '`if` declarations',
    '`if` declarations, v5.1, wording improvements': '`if` declarations',
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
    'Pitch for dialect directive': 'Pitch for #dialect directive',
    'The C Standard Charter': 'The C Standard charter',
    'Required JTC 1 Summary of ISO and IEC Codes of Conduct': 'Updated JTC 1 Code of Conduct slide',
    'Resolved \\& discarded, III (updates 3504\\)': 'Discarded',
    'Discarded, IV': 'Discarded',
    'Discarded, V': 'Discarded',
    'Quasi-literals': 'Generic replacement',
    'add strsfx()': 'add strsfx(), stpsfx(), wcssfx(), wcpsfx()',
    'add strpfx()': 'add strpfx(), stppfx(), wcspfx(), and wcppfx()',
    'Additional String comparison functions to completement strcmp': 'Additional String comparison functions to complement strcmp',
    'Add operators \\_Widthof, \\_Minof, \\_Maxof': 'Add operators \\_Minof and \\_Maxof',
    'Composite types': 'Composite Types',
    'Relax restrictions on standard attributes': 'Standard prefixed attributes',
    '\\_Any\\_func\\_t \\- A Universal Function Pointer Storage Type': '\\_Any\\_func\\* \\- A Universal Function Pointer Storage Type',
    'Generic replacement (v. 2 of quasi-literals)': 'Generic replacement',
    'Literal functions': 'Function literals'}


# Override titles for grouping (same title used for more than one
# paper).
OVERRIDE_GROUP_TITLE = {
    '3141': 'Composite types 2023'}


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
        elif 'issue log' in ndata['maintitle'].lower():
            ndata['class'] = 'cpub'
        elif 'educational undefined behavior' in ndata['maintitle'].lower():
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
        if ndata['class'] in ('c', 'cadm'):
            group_title = ndata['maintitle']
            if group_title in REMAP_TITLE:
                group_title = REMAP_TITLE[group_title]
            if nnum in OVERRIDE_GROUP_TITLE:
                group_title = OVERRIDE_GROUP_TITLE[nnum]
            by_title[group_title].add(nnum)
    # Group documents with the same main title together.
    for nnum, ndata in data.items():
        if ndata['class'] in ('c', 'cadm'):
            group_title = ndata['maintitle']
            if group_title in REMAP_TITLE:
                group_title = REMAP_TITLE[group_title]
            if nnum in OVERRIDE_GROUP_TITLE:
                group_title = OVERRIDE_GROUP_TITLE[nnum]
            ndata['group'].update(by_title[group_title])
    # Group documents explicitly said to update another together.
    changed = True
    while changed:
        changed = False
        for nnum, ndata in data.items():
            if ndata['class'] not in ('c', 'cadm'):
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


# C-documents to include in consideration (mentioned for possible
# future scheduling in agendas, or discussed for C2Y) despite
# predating cut-off date.
C_EXTRA_INCLUDE = {
    '2658', '2948', '2995', '3051', '3064', '3160', '3025', '3058'}


# C-documents to exclude in consideration (C23 ballot comments)
# despite postdating cut-off date.
C_EXTRA_EXCLUDE = {
    '3191', '3216'}


# Extra CADM-documents to include.
CADM_EXTRA_INCLUDE = {
    '3118', '3002', '2947'}


# Extra CADM-documents to exclude.
CADM_EXTRA_EXCLUDE = set()


# Data about CPUB documents (numbered manually, intended to be in
# order of first N-document corresponding to a given CPUB document,
# or, for issue logs not issued or initially issued as an N-document,
# the first snapshot of the issue log that can be found; C23 and
# future issue logs are intended to be added at the point where a
# snapshot is created for a meeting).  Cutoff dates are the dates
# from which a committee document should be associated with that
# edition rather than a previous edition.
CPUB_DOCS = [
    # CPUB1
    { 'title': 'Programming languages — C',
      'editions': [{ 'number': 0,
                     'title-md': 'C89',
                     'desc-md': 'Published as ANSI X3.159-1989.  Adopted as [FIPS PUB 160](https://nvlpubs.nist.gov/nistpubs/Legacy/FIPS/fipspub160.pdf), available online from NIST.'},
                   { 'number': 1,
                     'title-md': 'C90',
                     'desc-md': 'Published (1990-12-15) as ISO/IEC 9899:1990.'},
                   { 'number': 2,
                     'cutoff': '1991-01-01',
                     'title-md': 'C99',
                     'desc-md': 'Published (1999-12-01) as ISO/IEC 9899:1999.'},
                   { 'number': 3,
                     'cutoff': '2000-01-01',
                     'title-md': 'C11',
                     'desc-md': 'Published (2011-12-15) as ISO/IEC 9899:2011.'},
                   { 'number': 4,
                     'cutoff': '2012-01-01',
                     'title-md': 'C17',
                     'desc-md': 'Published (2018-07) as ISO/IEC 9899:2018.'},
                   { 'number': 5,
                     'cutoff': '2018-08-01',
                     'title-md': 'C23',
                     'desc-md': 'Published (2024-10) as ISO/IEC 9899:2024.'},
                   { 'number': 6,
                     'cutoff': '2024-02-22',
                     'title-md': 'C2y',
                     'desc-md': ''}] },
    # CPUB2
    { 'title': 'Rationale for Programming languages — C',
      'editions': [{ 'number': 0,
                     'title-md': 'C89 Rationale',
                     'desc-md': 'Included with ANSI C3.159-1989.  [Available online from NIST](https://nvlpubs.nist.gov/nistpubs/Legacy/FIPS/fipspub160.pdf#page=235).' },
                   { 'number': 2,
                     'cutoff': '1995-01-01',
                     'title-md': 'C99 Rationale',
                     'desc-md': '[Available online](https://www.open-std.org/jtc1/sc22/wg14/www/C99RationaleV5.10.pdf).'}] },
    # CPUB3
    { 'title': 'Amendment 1: C Integrity',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (1995-04-01) as ISO/IEC 9899:1990/Amd 1:1995.  Integrated into C99.' }] },
    # CPUB4
    { 'title': 'C90 issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'The [final issue log](https://www.open-std.org/jtc1/sc22/wg14/www/docs/dr.htm) is available.  Individual committee documents listed may correspond to different parts of older versions of the log, with later ones not always containing all the issues from earlier ones.' }] },
    # CPUB5
    { 'title': 'C90 Technical Corrigendum 1',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (1994-09-15) as ISO/IEC 9899:1990/Cor 1:1994.' },
                   { 'number': 2,
                     'cutoff': '1996-01-01',
                     'desc-md': 'Corrected and reprinted (1995-09-15).  Integrated into C99.' }] },
    # CPUB6
    { 'title': 'Numerical C Extensions',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published as X3/TR-17:1995 (?).  Most parts integrated into C99.' }] },
    # CPUB7
    { 'title': 'C90 Technical Corrigendum 2',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (1996-04-01) as ISO/IEC 9899:1990/Cor 2:1996.  Integrated into C99.' }] },
    # CPUB8
    { 'title': 'Programming languages — C — Extensions to support embedded processors',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2004-07-15) as ISO/IEC TR 18037:2004.' },
                   { 'number': 2,
                     'cutoff': '2005-01-01',
                     'desc-md': 'Published (2008-06-15) as ISO/IEC TR 18037:2008.' }] },
    # CPUB9
    { 'title': 'C99 issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'The [final issue log](https://www.open-std.org/jtc1/sc22/wg14/www/docs/summary-c99.htm) is available.  Individual committee documents here relate to this log, but do not correspond to older versions of it.' }] },
    # CPUB10
    { 'title': 'C99 Technical Corrigendum 1',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2001-09-01) as ISO/IEC 9899:1999/Cor 1:2001.  Integrated into C11.' }] },
    # CPUB11
    { 'title': 'Extensions for the programming language C to support new character data types',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2004-07-15) as ISO/IEC TR 19769:2004.  Integrated into C11.' }] },
    # CPUB12
    { 'title': 'Extension for the programming language C to support decimal floating-point arithmetic',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2009-01-15) as ISO/IEC TR 24732:2009.  Superseded by TS 18661-2.' }] },
    # CPUB13
    { 'title': 'Extensions to the C library — Part 1: Bounds-checking interfaces',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2007-09-01) as ISO/IEC TR 24731-1:2007.  The ISO website lists this as Edition 2 without mentioning Edition 1 and with the same publication date as for versions of the cover page that say Edition 1.  Integrated into C11.' }] },
    # CPUB14
    { 'title': 'Extensions to the C Library to support mathematical special functions',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2009-01-15) as ISO/IEC 24747:2009.' }] },
    # CPUB15
    { 'title': 'C99 Technical Corrigendum 2',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2004-11-15) as ISO/IEC 9899:1999/Cor 2:2004.  Integrated into C11.' }] },
    # CPUB16
    { 'title': 'Embedded C (2004) issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.  Some documents here only include new issues rather than being a consolidated list also including older issues.' }] },
    # CPUB17
    { 'title': 'Extensions to the C library — Part 2: Dynamic Allocation Functions',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2010-12-01) as ISO/IEC TR 24731-2:2010.' }] },
    # CPUB18
    { 'title': 'Rationale for Extensions to the C library — Part 1: Bounds-checking interfaces',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB19
    { 'title': 'Rationale for Extension for the programming language C to support decimal floating-point arithmetic',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB20
    { 'title': 'C99 Technical Corrigendum 3',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2007-11-15) as ISO/IEC 9899:1999/Cor 3:2007.  Integrated into C11.' }] },
    # CPUB21
    { 'title': 'Rationale for Extensions to the C Library to support mathematical special functions',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB22
    { 'title': 'C secure coding rules',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2013-11-15) as ISO/IEC TS 17961:2013.' },
                   { 'number': 2,
                     'cutoff': '2014-01-01',
                     'desc-md': ''}] },
    # CPUB23
    { 'title': 'C11/C17 issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'The most recent versions were issued only as committee documents.' }] },
    # CPUB24
    { 'title': 'C11 Technical Corrigendum 1',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2012-07-15) as ISO/IEC 9899:2011/Cor 1:2012.  Integrated into C23.' }] },
    # CPUB25
    { 'title': 'Floating-point extensions for C — Part 1: Binary floating-point arithmetic',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2014-07-15) as ISO/IEC TS 18861-1:2014.  Integrated into C23.' }] },
    # CPUB26
    { 'title': 'Floating-point extensions for C — Part 2: Decimal floating-point arithmetic',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2015-02-15) as ISO/IEC TS 18861-2:2015.' },
                   { 'number': 2,
                     'cutoff': '2015-03-01',
                     'desc-md': 'Published (2015-05-15) as ISO/IEC TS 18861-2:2015 (second edition).  Integrated into C23.' }] },
    # CPUB27
    { 'title': 'Floating-point extensions for C — Part 3: Interchange and extended types',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2015-10-01) as ISO/IEC TS 18861-3:2015.  Integrated into C23.' }] },
    # CPUB28
    { 'title': 'Floating-point extensions for C — Part 4: Supplementary functions',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2015-10-01) as ISO/IEC TS 18861-4:2015.  Partly integrated into C23.' },
                   { 'number': 2,
                     'cutoff': '2016-01-01',
                     'desc-md': 'Published (2025-03) ISO/IEC TS 18661-4:2025.' }] },
    # CPUB29
    { 'title': 'C Secure Coding Rules issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB30
    { 'title': 'Programming language C — Extensions for parallel programming — Part 1: Thread-based parallelism',
      'editions': [{ 'number': 1,
                     'desc-md': 'This was planned to be TS 21938-1, but the project was cancelled before publication.' }] },
    # CPUB31
    { 'title': 'Floating-point extensions for C — Part 5: Supplementary attributes',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2016-08-15) as ISO/IEC TS 18861-5:2016.' },
                   { 'number': 2,
                     'cutoff': '2017-01-01',
                     'desc-md': 'Published (2025-03) as ISO/IEC TS 18861-5:2025.' }] },
    # CPUB32
    { 'title': 'C Secure Coding Rules (2013) Technical Corrigendum 1',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2016-08-15) as ISO/IEC TS 17961:2013/Cor 1:2016.' }] },
    # CPUB33
    { 'title': 'Floating-point extensions for C (2014–2016) issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB34
    { 'title': 'Programming languages — C — A provenance-aware memory object model for C',
      'editions': [{ 'number': 1,
                     'desc-md': 'Published (2025-05) as ISO/IEC TS 6010:2025.' }] },
    # CPUB35
    { 'title': 'C Extensions to Support Generalized Function Calls',
      'editions': [{ 'number': 1,
                     'desc-md': 'Under development as draft TS 25007.' }] },
    # CPUB36
    { 'title': 'Examples of Undefined Behavior',
      'editions': [{ 'number': 1,
                     'desc-md': '' }] },
    # CPUB37
    { 'title': 'Programming Languages — C — defer, a mechanism for general purpose, lexical scope-based undo',
      'editions': [{ 'number': 1,
                     'desc-md': 'Under development as draft TS 25755.' }] },
    # CPUB38
    { 'title': 'C23 issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB39
    { 'title': 'Floating-point TS 18661 (C23 version, 2025) issue log',
      'editions': [{ 'number': 1,
                     'desc-md': 'Issued only as a committee document.' }] },
    # CPUB40
    { 'title': 'Undefined Behavior in the C Programming Language',
      'editions': [{'number': 1,
                    'desc-md': '' }]}
    ]


CPUB_STD = 1
CPUB_RAT = 2
CPUB_AMD1 = 3
CPUB_C90_ISSUES = 4
CPUB_C90TC1 = 5
CPUB_NCE = 6
CPUB_C90TC2 = 7
CPUB_EMBC = 8
CPUB_C99_ISSUES = 9
CPUB_C99TC1 = 10
CPUB_CHAR = 11
CPUB_DFP = 12
CPUB_BOUNDS = 13
CPUB_SPECMATH = 14
CPUB_C99TC2 = 15
CPUB_EMBC_ISSUES = 16
CPUB_DYN = 17
CPUB_RAT_BOUNDS = 18
CPUB_RAT_DFP = 19
CPUB_C99TC3 = 20
CPUB_RAT_SPECMATH = 21
CPUB_CSCR = 22
CPUB_C11_ISSUES = 23
CPUB_C11TC1 = 24
CPUB_FP1 = 25
CPUB_FP2 = 26
CPUB_FP3 = 27
CPUB_FP4 = 28
CPUB_CSCR_ISSUES = 29
CPUB_CPLEX = 30
CPUB_FP5 = 31
CPUB_CSCRTC1 = 32
CPUB_FP_ISSUES = 33
CPUB_PROV = 34
CPUB_FUNC = 35
CPUB_EXUB = 36
CPUB_DEFER = 37
CPUB_C23_ISSUES = 38
CPUB_FP_C23_ISSUES = 39
CPUB_EDUC_UB = 40


def generate_autonum_docs(data, doc_class, start_num, cutoff_date,
                          extra_exclude, extra_include):
    """Generate C-document data from groups of N-documents."""
    docs = []
    for nnum, ndata in data.items():
        if ndata['class'] == doc_class:
            convert_doc = (ndata['date'] >= cutoff_date and nnum not in extra_exclude) or nnum in extra_include
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
                docs.append(cdoc)
    docs.sort(key=lambda x: x['sortkey'])
    doc_class_upper = doc_class.upper()
    for num, doc in enumerate(docs, start=start_num):
        doc['id'] = '%s%d' % (doc_class_upper, num)
        for rev, num in enumerate(doc['nums'], start=1):
            data[num]['cdoc-rev'] = rev
    return docs


# CPUB documents where the heuristic identification of document number
# should be overridden.
OVERRIDE_CPUB = {
    '2060': CPUB_CSCR_ISSUES,
    '2010': CPUB_CSCRTC1,
    '1778': CPUB_FP1,
    '1756': CPUB_FP1,
    '1606': CPUB_C11TC1,
    '1235': CPUB_C99TC3,
    '1191': CPUB_C99_ISSUES,
    '1143': CPUB_BOUNDS,
    '1142': CPUB_C99_ISSUES,
    '1125': CPUB_C99_ISSUES,
    '1060': CPUB_C99TC2,
    '1040': CPUB_CHAR,
    '1010': CPUB_CHAR,
    '998': CPUB_CHAR,
    '932': CPUB_C99TC1,
    '854': CPUB_EMBC,
    '624': CPUB_C90TC2,
    '621': CPUB_C90TC1,
    '440': CPUB_C90TC2,
    '439': CPUB_C90_ISSUES,
    '438': CPUB_C90_ISSUES,
    '423': CPUB_C90TC1,
    '403': CPUB_NCE,
    '332': CPUB_C90TC1,
    '290': CPUB_C90TC1,
    '246': CPUB_C90_ISSUES,
    '245': CPUB_C90_ISSUES,
    '210': CPUB_AMD1,
    '182': CPUB_AMD1,
}


# CPUB documents where identification of edition by cutoff date should
# be overridden.
OVERRIDE_CPUB_EDITION = {
    '3219': 5
}


# CPUBX documents where identification of whether auxiliary should be
# overridden.
OVERRIDE_CPUB_AUX = {
    '2733': True,
    '1949': False,
    '1775': False,
    '1191': True,
    '940': True,
    '800': True,
    '438': True,
}


def generate_cpub_docs(data):
    """Generate CPUB-document data from N-documents."""
    nnums_by_cpub_num = {}
    nnums_by_cpubx_num = {}
    cpubx_editions = {}
    cpub_by_num = {}
    for n, d in enumerate(CPUB_DOCS, start=1):
        cpub_by_num[n] = d
        nnums_by_cpub_num[n] = {}
        for e in d['editions']:
            nnums_by_cpub_num[n][e['number']] = set()
        nnums_by_cpubx_num[n] = set()
    docs = []
    xdocs = []
    for nnum, ndata in data.items():
        if ndata['class'] == 'cpub':
            ltitle = ndata['maintitle'].lower()
            if 'multibyte support extension' in ltitle:
                pub = CPUB_AMD1
            elif 'mse' in ltitle:
                pub = CPUB_AMD1
            elif 'normative addendum' in ltitle:
                pub = CPUB_AMD1
            elif 'rationale' in ltitle:
                if '24731' in ltitle:
                    pub = CPUB_RAT_BOUNDS
                elif '24732' in ltitle:
                    pub = CPUB_RAT_DFP
                elif '24747' in ltitle:
                    pub = CPUB_RAT_SPECMATH
                else:
                    pub = CPUB_RAT
            elif 'defect' in ltitle:
                if '18037' in ltitle:
                    pub = CPUB_EMBC_ISSUES
                elif '17961' in ltitle or 'cscr' in ltitle:
                    pub = CPUB_CSCR_ISSUES
                elif 'c11' in ltitle:
                    pub = CPUB_C11_ISSUES
                else:
                    pub = CPUB_C90_ISSUES
            elif 'record of responses' in ltitle:
                pub = CPUB_C90_ISSUES
            elif '18037' in ltitle:
                pub = CPUB_EMBC
            elif '24731-2' in ltitle or '24731 part ii' in ltitle or 'dynamic alloc' in ltitle:
                pub = CPUB_DYN
            elif '24731' in ltitle:
                pub = CPUB_BOUNDS
            elif '24732' in ltitle:
                pub = CPUB_DFP
            elif '24747' in ltitle or 'special math' in ltitle:
                pub = CPUB_SPECMATH
            elif '17961' in ltitle or 'secure coding' in ltitle:
                pub = CPUB_CSCR
            elif 'secure' in ltitle or 'security' in ltitle:
                pub = CPUB_BOUNDS
            elif 'parallel' in ltitle or 'cplex' in ltitle:
                pub = CPUB_CPLEX
            elif 'part 1' in ltitle or '18661-1' in ltitle:
                pub = CPUB_FP1
            elif 'part 2' in ltitle or '18661-2' in ltitle:
                pub = CPUB_FP2
            elif 'part 3' in ltitle or '18661-3' in ltitle:
                pub = CPUB_FP3
            elif 'part 4' in ltitle or '18661-4' in ltitle:
                pub = CPUB_FP4
            elif 'part 5' in ltitle or '18661-5' in ltitle:
                pub = CPUB_FP5
            elif 'decimal' in ltitle:
                pub = CPUB_DFP
            elif 'provenance' in ltitle or '6010' in ltitle:
                pub = CPUB_PROV
            elif 'defer' in ltitle:
                pub = CPUB_DEFER
            elif 'function' in ltitle:
                pub = CPUB_FUNC
            elif 'educational undefined behavior' in ltitle:
                pub = CPUB_EDUC_UB
            elif 'undefined' in ltitle:
                pub = CPUB_EXUB
            elif 'cscr compendium' in ltitle or 'cscr drs' in ltitle or 'rules dr' in ltitle:
                pub = CPUB_CSCR_ISSUES
            elif 'fpe compendium' in ltitle or 'floating point extension dr' in ltitle or 'summary for fpe' in ltitle:
                pub = CPUB_FP_ISSUES
            elif 'compendium' in ltitle or 'drs' in ltitle or 'dr report' in ltitle or 'request summary' in ltitle or 'cr summary' in ltitle:
                pub = CPUB_C11_ISSUES
            elif 'c23 issue log' in ltitle:
                pub = CPUB_C23_ISSUES
            elif 'ts 18661 (c23 version, 2025\\) issue log' in ltitle:
                pub = CPUB_FP_C23_ISSUES
            else:
                pub = CPUB_STD
            if nnum in OVERRIDE_CPUB:
                pub = OVERRIDE_CPUB[nnum]
            edition = cpub_by_num[pub]['editions'][0]['number']
            for e in cpub_by_num[pub]['editions']:
                if 'cutoff' in e and ndata['date'] >= e['cutoff']:
                    edition = e['number']
            if nnum in OVERRIDE_CPUB_EDITION:
                edition = OVERRIDE_CPUB_EDITION[nnum]
            if 'editor' in ltitle or 'redactor' in ltitle or 'cross ref' in ltitle or 'status' in ltitle:
                is_aux = True
            else:
                is_aux = False
            if nnum in OVERRIDE_CPUB_AUX:
                is_aux = OVERRIDE_CPUB_AUX[nnum]
            if is_aux:
                nnums_by_cpubx_num[pub].add(nnum)
                cpubx_editions[nnum] = edition
            else:
                nnums_by_cpub_num[pub][edition].add(nnum)
    for n, d in enumerate(CPUB_DOCS, start=1):
        doc = {
            'id': 'CPUB%d' % n,
            'title': d['title'],
            'editions': []}
        for e in d['editions']:
            doc['editions'].append({
                'edition-num': e['number'],
                'desc-md': e['desc-md'],
                'nums': sorted(nnums_by_cpub_num[n][e['number']], key=int)})
            if 'title-md' in e:
                doc['editions'][-1]['title'] = e['title-md']
            for rev, num in enumerate(doc['editions'][-1]['nums'], start=1):
                data[num]['cdoc-rev'] = rev
        docs.append(doc)
        for x, num in enumerate(sorted(nnums_by_cpubx_num[n], key=int), start=1):
            ndata = data[num]
            doc = {
                'id': 'CPUBX%dx%d' % (n, x),
                'author': ndata['author'],
                'title': ndata['title'],
                'nums': [num]}
            for rev, num_sub in enumerate(doc['nums'], start=1):
                data[num_sub]['cdoc-rev'] = rev
                data[num_sub]['cpub-edition'] = 'CPUB%de%d' % (n, cpubx_editions[num_sub])
            xdocs.append(doc)
    return docs, xdocs


# Date overrides for meeting documents.
OVERRIDE_DATE = {
    '3735': '202510.2',
    '3730': '202510.2',
    '3729': '202510.1',
    '3726': '202510.1',
    '3649': '202409',
    '3501': '202508',
    '3399': '202502',
    '3373': '202406',
    '3372': '202409',
    '3281': '202406',
    '3270': '202409',
    '3172': '202401',
    '3168': '202308.2',
    '3162': '202308.2',
    '3161': '202308.1',
    '3159': '202308.1',
    '3100': '202301.3',
    '3099': '202301.3',
    '3085': '202301.2',
    '3084': '202301.2',
    '3083': '202301.1',
    '3069': '202301.1',
    '2971': '202203.2',
    '2950': '202203.2',
    '2949': '202203.1',
    '2943': '202203.1',
    # Typo in date in document list.
    '2925': '202201',
    '2921': '202111',
    '2691': '202011',
    '2690': '202103',
    # Typo in date in document list.
    '2648': '202101',
    '2628': '202011',
    '2605': '202010',
    '2519': '202003',
    '2516': '202003',
    '2509': '201910',
    '2463': '202003',
    '2451': '201910',
    '2439': '202201',
    '2377': '201904',
    '2376': '201904',
    '2375': '201810',
    '2308': '201904',
    '2239': '201804',
    '2238': '201710',
    '1984': '201604',
    '1983': '201604',
    '1900': '201410',
    '1840': '201406',
    # Typo in date in document list.
    '1828': '201404',
    '1820': '201404',
    '1819': '201309',
    '1799': '201410',
    '1795': '201403',
    '1764': '201309',
    '1763': '201304',
    '1737': '201309',
    '1708': '201309',
    '1686': '201309',
    '1681': '201302',
    '1640': '201304',
    '1604': '201202',
    '1603': '201110',
    # Typo in date in document list.
    '1597': '201202',
    # Typo in date in document list.
    '1589': '201202',
    '1588': '201110',
    '1587': '201103',
    '1557': '201011',
    '1542': '201005',
    # Typo in date in document list.
    '1449': '201004',
    '1475': '200910',
    '1375': '200809',
    '1231': '200704',
    '1211': '200704',
    '1198': '200610',
    '1195': '200603',
    '1168': '200603',
    '1166': '200509',
    '1153': '200610',
    '1145': '200509',
    '1140': '200504',
    '1136': '200603',
    '1116': '200504',
    '1115': '200410',
    '1083': '200410',
    '1081': '200403',
    '1064': '200403',
    '1039': '200403',
    '1022': '200403',
    '1004': '200303',
    '999': '200303',
    '989': '200303',
    '988': '200303',
    '981': '200210',
    '960': '200110',
    '928': '200010',
    '914': '200004',
    '862': '199806',
    '840': '199806',
    '855': '199902',
    '812': '199802',
    '718': '199706',
    '630': '199702',
    '597': '199610',
    '352': '199406',
    '201': '199112.1',
    '200': '199112.2',
    '176': '199112.1',
    '174': '199112.1',
    '092': '198904.1',
    '086': '198904.2',
    '077': '198904.1',
    '018': '198706.2',
    '013': '198711',
    # Guess that this is the meeting this document refers to.
    '012': '198711',
    '010': '198706.1',
    '002': '198706.1',
}


# Cases where multiple meeting documents are versions of the same
# document.
MEETING_DOC_GROUPS = [
    ['1745', '1788'],
    ['1799', '1811', '1831', '1861'],
    ['2047', '2057'],
    ['2247', '2284']]


# Map meeting numbers to lists of documents discussed there.
MEETING_TO_DOCS = {
    '202103': ['2596', '2598', '2619', '2645', '2621', '2623', '2626', '2629',
               '2630', '2631', '2624', '2577', '2638', '2632', '2633', '2661',
               '2639', '2680', '2640', '2641', '2642', '2643', '2683', '2682',
               '2675', '2674'],
    '202106': ['2683', '2738', '2676', '2737', '2709', '2650', '2651', '2652',
               '2670', '2671', '2672', '2668', '2700', '2659', '2660', '2662',
               '2663', '2665', '2659', '2654', '2718', '2692'],
    '202108': ['2673', '2785', '2684', '2686', '2687', '2688', '2699', '2773',
               '2720', '2756', '2757', '2772', '2710', '2711', '2712', '2713',
               '2714', '2715', '2716', '2745', '2746', '2748', '2749', '2755',
               '2799', '2800', '2801', '2741', '2777', '2739', '2726', '2727',
               '2728', '2729'],
    '202111': ['2731', '2733', '2761', '2781', '2850', '2778', '2770', '2771',
               '2806', '2805', '2747', '2842', '2843', '2790', '2797', '2823',
               '2845', '2846', '2848', '2788', '2808', '2774', '2807', '2838',
               '2821', '2822', '2804', '2743', '2838', '2817', '2837'],
    '202201': ['2833', '2834', '2676', '2809', '2836', '2810', '2797', '2754',
               '2844', '2847', '2849', '2879', '2880', '2881', '2882', '2890',
               '2891', '2923', '2892', '2787', '2862', '2895', '2762', '2764',
               '2775', '2851', '2852', '2918', '2854', '2919', '2855', '2920',
               '2701', '2841', '2860', '2840', '2884', '2885', '2922', '2826',
               '2647', '2818', '2937', '2819', '2887', '2653', '2829', '2827',
               '2903', '2828', '2724', '2927', '2725', '2898', '2796', '2900',
               '2906', '2780', '2859', '2896', '2931', '2934', '2935'],
    '202205': ['2912', '2913', '2976', '2867', '2868', '2947', '2676', '2857',
               '2856', '2658', '2983', '2878', '2966', '2963', '2964', '2886',
               '2888', '2889', '2861', '2863', '2905', '2907', '2992', '2909',
               '2897', '2932', '2986'],
    '202207': ['2930', '2939', '2940', '2969', '2974', '2975', '3005', '2993',
               '3011', '3021', '2997', '3017', '2999', '2929', '2938', '3003',
               '3020', '2957', '2994', '3016', '2951', '2960', '3006', '3007',
               '3018', '2956', '3019', '2955', '3034', '3033', '3037', '3029',
               '3030', '3035', '3038', '3039', '3031', '3042', '3022'],
    '202301': ['3067', '3073', '3082', '3046', '3066', '3077', '3072', '3080',
               '3078', '3082', '3070', '3059', '3090', '3076', '3079'],
    '202302': ['3091', '3073', '3092', '3070', '3071', '3072', '3078', '3086',
               '3067', '3073', '3103', '3098', '3102', '3105', '3107', '3104',
               '3095', '3031', '3106'],
    '202306': ['3132', '3131', '3135', '3141', '3140', '3144', '3138', '3143',
               '3145', '3147'],
    '202310': ['3163', '3164', '3165', '3002', '3171'],
    '202401': ['3191', '3180', '3181', '2611', '2948', '3183', '3089', '3184',
               '3185', '3189', '3190', '3197', '3186', '3187', '3188', '3207',
               '3192', '3193', '3195', '3194', '3196', '3203', '3204', '3205',
               '3199', '3198', '3200', '3206', '3051'],
    '202406': ['3053', '3261', '3210', '3211', '3246', '3260', '3255', '3223',
               '3232', '3233', '3242', '3234', '3239', '3263', '3241', '3212',
               '3254', '3252', '3250', '3064', '3247', '3243', '3253', '3244',
               '3259', '3262', '3273', '3274'],
    '202409': ['3275', '3285', '3286', '3287', '3288', '3326', '3306', '3315',
               '3353', '3356', '3355', '3354', '3320', '3312', '3321', '3295',
               '3348', '3331', '3340', '3341', '3342', '3343', '3344', '3345',
               '3346', '3347', '3265', '3298', '3317', '3155', '3330', '3327',
               '3325', '3350', '3272', '3318', '3322', '3323', '3291', '3303',
               '3305', '3324', '3307', '3316', '3352', '3364', '3370', '3349',
               '3363', '3369', '3367', '3366'],
    '202502': ['3363', '2998', '3472', '3484', '3459', '3503', '3377', '3493',
               '3464', '3465', '3473', '3390', '3432', '3495', '3332', '3451',
               '3409', '2698', '3499', '3498', '3394', '3433', '3395', '3426',
               '3398', '3422', '3471', '3466', '3410', '3411', '3478', '3418',
               '3480', '3481', '3482', '3496', '3329', '3442', '3497', '3494',
               '3427', '3357', '3461', '3460', '3401', '3492', '3405', '3452',
               '3437', '3423', '3512', '3438', '3469', '3443', '3505', '3507',
               '3389', '3453', '3450', '3408', '3447', '3448', '3449', '3508'],
    '202508': ['3582', '3428', '3348', '3457', '3636', '3235', '3486', '3656',
               '3433', '3558', '3609', '3559', '3602', '3545', '3610', '3631',
               '3557', '3577', '3629', '3511', '3611', '3593', '3627', '3487',
               '3490', '3644', '3623', '3563', '3532', '3565', '3603', '3604',
               '3525', '3637', '3533', '3600', '3601', '3485', '3599', '3621',
               '3543', '3606', '3540', '3544', '3519', '3658', '3535', '3568',
               '3455', '3536', '3537', '3500', '3598', '3607', '3608', '3628',
               '3622', '3632', '3614', '3662', '3617', '3619', '3549', '3548',
               '3605', '3561']
}


def generate_meeting_docs(data, doc_class):
    """Generate meeting document data from N-documents."""
    nnums_by_meeting = collections.defaultdict(set)
    docs = []
    months = [('Jan', 'January'), ('Feb', 'February'), ('Mar', 'March'),
              ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'),
              ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'),
              ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')]
    for nnum, ndata in data.items():
        if ndata['class'] == doc_class:
            title_words = re.split("[-\\\\ .,/'()]", ndata['maintitle'])
            month = None
            year = None
            for y in range(1986, 2026):
                if str(y) in title_words:
                    year = str(y)
                    break
            if year is None:
                for y in range(86, 100):
                    if str(y) in title_words:
                        year = str(1900 + y)
                        break
            for m_no, m_names in enumerate(months, start=1):
                if m_names[0] in title_words or m_names[1] in title_words:
                    month = '%02d' % m_no
                    break
            if year is not None and month is None:
                for m_no in range(1, 13):
                    if '%s-%02d' % (year, m_no) in ndata['maintitle']:
                        month = '%02d' % m_no
                        break
                    if '%s/%02d' % (year, m_no) in ndata['maintitle']:
                        month = '%02d' % m_no
                        break
            if month is not None and year is None:
                dyear = ndata['date'][:4]
                dmon = ndata['date'][5:7]
                if dmon == month:
                    year = dyear
                if doc_class in ('cmm', 'cfptcm') and int(dmon) == int(month) + 1:
                    year = dyear
            if nnum in OVERRIDE_DATE:
                year = OVERRIDE_DATE[nnum][:4]
                month = OVERRIDE_DATE[nnum][4:]
            if month is None or year is None:
                raise ValueError('could not parse date: N%s %s' % (nnum, ndata['title']))
            else:
                nnums_by_meeting['%s%s' % (year, month)].add(nnum)
    doc_class_upper = doc_class.upper()
    if doc_class == 'cm':
        # These are distinct documents, or multiple versions where
        # explicitly listed as such.
        later_vers = set()
        group_contents = {}
        for g in MEETING_DOC_GROUPS:
            for n in g[1:]:
                later_vers.add(n)
            group_contents[g[0]] = g
        for k, v in nnums_by_meeting.items():
            nums = sorted(v, key=int)
            nums = [n for n in nums if n not in later_vers]
            for xnum, nnum in enumerate(nums, start=1):
                doc = {
                    'id': '%s%sx%d' % (doc_class_upper, k, xnum),
                    'author': data[nnum]['author'],
                    'title': data[nnum]['title'],
                    'nums': [nnum]}
                if nnum in group_contents:
                    doc['nums'] = group_contents[nnum]
                    ldata = data[doc['nums'][-1]]
                    doc['author'] = ldata['author']
                    doc['title'] = ldata['title']
                    for r, nn in enumerate(group_contents[nnum], start=1):
                        data[nn]['cdoc-rev'] = r
                else:
                    data[nnum]['cdoc-rev'] = 1
                docs.append(doc)
    else:
        # These are versions of one agenda / minutes document.
        for k, v in nnums_by_meeting.items():
            nums = sorted(v, key=int)
            last_ndata = data[nums[-1]]
            doc = {
                'id': '%s%s' % (doc_class_upper, k),
                'author': last_ndata['author'],
                'title': last_ndata['title'],
                'nums': nums}
            for rev, num_sub in enumerate(nums, start=1):
                data[num_sub]['cdoc-rev'] = rev
            docs.append(doc)
    return docs


def convert_docs(data, doc_class, doc_list):
    """Convert documents in a given class to JSON metadata."""
    for doc in doc_list:
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
                'ext-url': ndata['link'],
                'meetings': sorted(ndata['meetings'])}
            doc_json['revisions'].append(ndoc)
            ndata['cid'] = ndoc['id']
        out_dir = os.path.join('out', 'papers', doc_class, doc['id'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'metadata.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(doc_json, f, indent=4, sort_keys=True)


def convert_cpub_docs(data, doc_list, xdoc_list):
    """Convert CPUB documents to JSON metadata."""
    for doc in doc_list:
        doc_json = {
            'id': doc['id'],
            'title': doc['title'],
            'editions': []}
        for e in doc['editions']:
            edition_json = {
                'id': '%se%d' % (doc['id'], e['edition-num']),
                'edition-num': e['edition-num'],
                'desc-md': e['desc-md'],
                'revisions': []}
            if 'title' in e:
                edition_json['title'] = e['title']
            for n in e['nums']:
                ndata = data[n]
                ndoc = {
                    'rev-id': 'r%d' % ndata['cdoc-rev'],
                    'id': '%se%dr%d' % (doc['id'], e['edition-num'],
                                        ndata['cdoc-rev']),
                    'doc-id': doc['id'],
                    'edition-id': '%se%d' % (doc['id'], e['edition-num']),
                    'edition-num': e['edition-num'],
                    'author': ndata['author'],
                    'title': ndata['title'],
                    'date': ndata['date'],
                    'ext-id': 'N%s' % n,
                    'ext-url': ndata['link'],
                    'meetings': sorted(ndata['meetings'])}
                edition_json['revisions'].append(ndoc)
                ndata['cid'] = ndoc['id']
            doc_json['editions'].append(edition_json)
        out_dir = os.path.join('out', 'papers', 'CPUB', doc['id'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'metadata.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(doc_json, f, indent=4, sort_keys=True)
    for doc in xdoc_list:
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
                'cpub-edition': ndata['cpub-edition'],
                'author': ndata['author'],
                'title': ndata['title'],
                'date': ndata['date'],
                'ext-id': 'N%s' % n,
                'ext-url': ndata['link'],
                'meetings': sorted(ndata['meetings'])}
            doc_json['revisions'].append(ndoc)
            ndata['cid'] = ndoc['id']
        out_dir = os.path.join('out', 'papers', 'CPUBX', doc['id'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'metadata.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(doc_json, f, indent=4, sort_keys=True)


def action_convert():
    """Convert the document log to JSON metadata."""
    data = get_ndoc_data()
    for m, dl in MEETING_TO_DOCS.items():
        for d in dl:
            data[d]['meetings'].add(m)
    classify_docs(data)
    c_docs = generate_autonum_docs(data, 'c', 4000, '2023-10-01',
                                   C_EXTRA_EXCLUDE, C_EXTRA_INCLUDE)
    convert_docs(data, 'C', c_docs)
    cadm_docs = generate_autonum_docs(data, 'cadm', 1, '2023-09-01',
                                      CADM_EXTRA_EXCLUDE, CADM_EXTRA_INCLUDE)
    convert_docs(data, 'CADM', cadm_docs)
    cpub_docs, cpubx_docs = generate_cpub_docs(data)
    convert_cpub_docs(data, cpub_docs, cpubx_docs)
    for c in ('cm', 'cma', 'cmm', 'cfptca', 'cfptcm'):
        m_docs = generate_meeting_docs(data, c)
        convert_docs(data, c.upper(), m_docs)
    # Also generate a list of N-documents that don't have new
    # identifiers, for use in displaying a list of all documents
    # including those.  Also generate a text list of all papers, for
    # convenience in improving the classification logic; a similar
    # list in JSON; and a list of paper locations on the WG14 website,
    # for link checking.
    text_list = []
    all_classes = {}
    url_list = []
    ndocs = {}
    text_list_meetings = []
    for m, dl in MEETING_TO_DOCS.items():
        for d in dl:
            ddata = data[d]
            text_list_meetings.append(
                '%s: N%s %s %s, %s'
                % (m, d, ddata['date'], ddata['author'], ddata['title']))
    for nnum, ndata in data.items():
        text_list.append('%s\tN%s %s %s, %s'
                         % (ndata['cid'] if 'cid' in ndata else ndata['class'],
                            nnum, ndata['date'], ndata['author'],
                            ndata['title']))
        all_classes[nnum] = {
            'author': ndata['author'],
            'title': ndata['title'],
            'date': ndata['date'],
            'ext-id': 'N%s' % nnum,
            'ext-url': ndata['link'],
            'class': ndata['class'].upper()
        }
        if ndata['class'] == 'cpub' and 'cid' in ndata and ndata['cid'].startswith('CPUBX'):
            all_classes[nnum]['class'] = 'CPUBX'
        if ndata['link'] and ndata['link'].startswith(WG14_BASE):
            url_list.append(ndata['link'][len(WG14_BASE):])
        if 'cid' not in ndata:
            doc_json = {
                'author': ndata['author'],
                'title': ndata['title'],
                'date': ndata['date'],
                'ext-id': 'N%s' % nnum,
                'ext-url': ndata['link'],
                'meetings': sorted(ndata['meetings'])}
            ndocs[nnum] = doc_json
    ndocs_out = []
    for n in sorted(ndocs.keys(), key=int, reverse=True):
        ndocs_out.append(ndocs[n])
    all_classes_out = []
    for n in sorted(all_classes.keys(), key=int, reverse=True):
        all_classes_out.append(all_classes[n])
    with open(os.path.join('out', 'papers', 'N-documents.json'), 'w',
              encoding='utf-8') as f:
        json.dump(ndocs_out, f, indent=4, sort_keys=True)
    with open('all-classes.json', 'w', encoding='utf-8') as f:
        json.dump(all_classes_out, f, indent=4, sort_keys=True)
    with open('tmp-papers-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_list) + '\n')
    with open('tmp-file-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(url_list) + '\n')
    with open('tmp-papers-meetings-list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_list_meetings) + '\n')


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
