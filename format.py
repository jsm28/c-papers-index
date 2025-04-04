#! /usr/bin/env python3

import argparse
import json
import os
import os.path
import re
from mistletoe import Document
from mistletoe.html_renderer import HtmlRenderer


# The location of papers data and metadata.
PAPERS_DIR = 'out/papers'


# The location of formatted (HTML) output.
OUT_HTML_DIR = 'out_html'


def split_doc_id(text):
    """Split a document ID into a sequence of alphabetical and
    numerical parts."""
    orig_text = text
    out = []
    while text:
        m = re.match('[A-Za-z]+', text)
        if m:
            out.append(m.group(0))
            text = text[m.end(0):]
            continue
        m = re.match(r'[0-9]+(?:\.[0-9]+)*', text)
        if m:
            out.append(tuple(int(i) for i in m.group(0).split('.')))
            text = text[m.end(0):]
            continue
        raise ValueError('could not parse ID %s' % orig_text)
    return out


def split_doc_id_rev(text):
    """Split a document ID into a sequence of alphabetical and
    numerical parts, then reverse the first two components."""
    s = split_doc_id(text)
    return [s[1], s[0]] + s[2:]


class DocList:

    """All the data stored relating to documents."""

    def __init__(self, dirname):
        """Get all the data stored relating to documents."""
        self.by_class = {}
        self.rev_sort = {}
        self.by_rev = {}
        for doc_class in ('C', 'CADM', 'CPUB', 'CPUBX', 'CM', 'CMA', 'CMM',
                          'CFPTCA', 'CFPTCM'):
            c_dir = os.path.join(dirname, doc_class)
            data = {}
            paper_nums = os.listdir(c_dir)
            for n in paper_nums:
                n_dir = os.path.join(c_dir, n)
                with open(os.path.join(n_dir, 'metadata.json'), 'r',
                          encoding='utf-8') as f:
                    data[n] = json.load(f)
            self.by_class[doc_class] = data
            has_editions = doc_class == 'CPUB'
            if has_editions:
                these_docs = []
                for doc in data.values():
                    these_docs.extend(doc['editions'])
            else:
                these_docs = data.values()
            for doc in these_docs:
                for rev in doc['revisions']:
                    rev['class'] = doc_class
                    self.by_rev[rev['id']] = rev
                    # Sort first by date, then, within a date, by
                    # document revision ID.
                    self.rev_sort[rev['id']] = (rev['date'],
                                                split_doc_id(rev['id']))


def write_md(filename, content, title):
    """Write Markdown to a file in HTML format."""
    with HtmlRenderer() as renderer:
        doc = Document(content)
        content = renderer.render(doc)
    with HtmlRenderer() as renderer:
        doc = Document(title)
        title = renderer.render_to_plain(doc)
    content = (
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '<meta http-equiv="Content-Type" content="text/html; '
            'charset=UTF-8">\n'
            '<title>%s</title>\n'
            '</head>\n'
            '<body>\n'
            '%s\n'
            '</body>\n'
            '</html>\n'
            % (title, content))
    os.makedirs(OUT_HTML_DIR, exist_ok=True)
    with open(os.path.join(OUT_HTML_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(content)


def link_for_rev(rev):
    """Generate a Markdown link for a document revision."""
    if rev['ext-url']:
        link = '[%s (%s)](%s)' % (rev['rev-id'], rev['ext-id'], rev['ext-url'])
    else:
        link = '%s (%s)' % (rev['rev-id'], rev['ext-id'])
    return link


def table_line_for_rev(rev, show_num):
    """Generate a Markdown table line for a document revision."""
    link = link_for_rev(rev)
    n = (rev['edition-id'] if 'edition-id' in rev else rev['doc-id']) if show_num else ' '
    return ('|%s|%s|%s|%s|%s|\n'
            % (n, link, rev['author'], rev['date'], rev['title']))


def write_chron(all_data, filename, title, classes):
    """Write out a reverse-chronological list of papers."""
    out_list = ['# %s\n\n' % title]
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for rev_id in sorted(
            (k for k in all_data.by_rev.keys()
             if all_data.by_rev[k]['class'] in classes),
            key=lambda k: all_data.rev_sort[k],
            reverse=True):
        out_list.append(table_line_for_rev(all_data.by_rev[rev_id], True))
    write_md(filename, ''.join(out_list), title)


def do_format_simple(all_data, doc_class):
    """Format simple lists of a papers in a given class.  The source
    data is in PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    doc_class_upper = doc_class.upper()
    data = all_data.by_class[doc_class_upper]
    out_list = ['# Prototype %s document list by document number\n\n'
                % doc_class_upper]
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for n in sorted(data.keys(), key=split_doc_id, reverse=True):
        cdoc = data[n]
        out_list.append('|%s| |%s| |%s|\n' % (cdoc['id'], cdoc['author'],
                                            cdoc['title']))
        for rev in reversed(cdoc['revisions']):
            out_list.append(table_line_for_rev(rev, False))
    write_md(
        '%s-num.html' % doc_class,
        ''.join(out_list),
        'Prototype %s document list by document number' % doc_class_upper)
    write_chron(
        all_data,
        '%s-all.html' % doc_class,
        'Prototype %s document list, reverse-chronological' % doc_class_upper,
        (doc_class_upper,))


def do_format_cpub(all_data):
    """Format lists of CPUB and CPUBX documents.  The source data is
    in PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    cpub_data = all_data.by_class['CPUB']
    cpubx_data = all_data.by_class['CPUBX']
    aux_for_cpub_ed = {}
    for doc in cpub_data.values():
        for e in doc['editions']:
            aux_for_cpub_ed[e['id']] = set()
    for doc in cpubx_data.values():
        for rev in doc['revisions']:
            aux_for_cpub_ed[rev['cpub-edition']].add(rev['id'])
    out_list = ['# Prototype CPUB and CPUBX document list by document number\n\n']
    for n in sorted(cpub_data.keys(), key=split_doc_id):
        out_list.append('## %s: %s\n\n' % (cpub_data[n]['id'],
                                           cpub_data[n]['title']))
        for e in reversed(cpub_data[n]['editions']):
            if 'title' in e:
                out_list.append('### Edition %d: %s\n\n' % (e['edition-num'],
                                                            e['title']))
            else:
                out_list.append('### Edition %d\n\n' % e['edition-num'])
            out_list.append('%s\n\n' % e['desc-md'])
            out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
            all_revs = e['revisions'] + [all_data.by_rev[r] for r in aux_for_cpub_ed[e['id']]]
            for rev in sorted(all_revs, key=lambda k: all_data.rev_sort[k['id']], reverse=True):
                out_list.append(table_line_for_rev(rev, True))
    write_md(
        'cpub-num.html',
        ''.join(out_list),
        'Prototype CPUB and CPUBX document list by document number')
    write_chron(
        all_data,
        'cpub-all.html',
        'Prototype CPUB and CPUBX document list, reverse-chronological',
        ('CPUB', 'CPUBX'))


def do_format_cm(all_data):
    """Format lists of meeting papers.  The source data is in
    PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    cm_data = all_data.by_class['CM']
    cma_data = all_data.by_class['CMA']
    cmm_data = all_data.by_class['CMM']
    data = cm_data.copy()
    data.update(cma_data)
    data.update(cmm_data)
    out_list = ['# Prototype meeting document list by document number\n\n']
    out_list.append('## Summary table of meetings\n\n')
    out_list.append('|YYYYMM|Agenda|Minutes|\n|-|-|-|\n')
    by_meeting = {}
    for n in data.keys():
        by_meeting[split_doc_id_rev(n)[0]] = [None, None]
    for k, v in cma_data.items():
        by_meeting[split_doc_id_rev(k)[0]][0] = v
    for k, v in cmm_data.items():
        by_meeting[split_doc_id_rev(k)[0]][1] = v
    for n in sorted(by_meeting.keys(), reverse=True):
        agenda = by_meeting[n][0]
        if agenda is None:
            agenda_txt = ' '
        else:
            agenda_txt = link_for_rev(agenda['revisions'][-1])
        minutes = by_meeting[n][1]
        if minutes is None:
            minutes_txt = ' '
        else:
            minutes_txt = link_for_rev(minutes['revisions'][-1])
        out_list.append('|%s|%s|%s|\n' % (
            '.'.join(str(i) for i in n), agenda_txt, minutes_txt))
    out_list.append('\n## Full document list\n\n')
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for n in sorted(data.keys(), key=split_doc_id_rev, reverse=True):
        cdoc = data[n]
        out_list.append('|%s| |%s| |%s|\n' % (cdoc['id'], cdoc['author'],
                                            cdoc['title']))
        for rev in reversed(cdoc['revisions']):
            out_list.append(table_line_for_rev(rev, False))
    write_md(
        'cm-num.html',
        ''.join(out_list),
        'Prototype meeting document list by document number')
    write_chron(
        all_data,
        'cm-all.html',
        'Prototype meeting document list, reverse-chronological',
        ('CM', 'CMA', 'CMM'))


def do_format_cfptc(all_data):
    """Format lists of CFP teleconference papers.  The source data is
    in PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    cfptca_data = all_data.by_class['CFPTCA']
    cfptcm_data = all_data.by_class['CFPTCM']
    data = cfptca_data.copy()
    data.update(cfptcm_data)
    out_list = ['# Prototype CFP teleconference document list by document number\n\n']
    out_list.append('## Summary table of CFP teleconferences\n\n')
    out_list.append('|YYYYMM|Agenda|Minutes|\n|-|-|-|\n')
    by_meeting = {}
    for n in data.keys():
        by_meeting[split_doc_id_rev(n)[0]] = [None, None]
    for k, v in cfptca_data.items():
        by_meeting[split_doc_id_rev(k)[0]][0] = v
    for k, v in cfptcm_data.items():
        by_meeting[split_doc_id_rev(k)[0]][1] = v
    for n in sorted(by_meeting.keys(), reverse=True):
        agenda = by_meeting[n][0]
        if agenda is None:
            agenda_txt = ' '
        else:
            agenda_txt = link_for_rev(agenda['revisions'][-1])
        minutes = by_meeting[n][1]
        if minutes is None:
            minutes_txt = ' '
        else:
            minutes_txt = link_for_rev(minutes['revisions'][-1])
        out_list.append('|%s|%s|%s|\n' % (
            '.'.join(str(i) for i in n), agenda_txt, minutes_txt))
    out_list.append('\n## Full document list\n\n')
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for n in sorted(data.keys(), key=split_doc_id_rev, reverse=True):
        cdoc = data[n]
        out_list.append('|%s| |%s| |%s|\n' % (cdoc['id'], cdoc['author'],
                                            cdoc['title']))
        for rev in reversed(cdoc['revisions']):
            out_list.append(table_line_for_rev(rev, False))
    write_md(
        'cfptc-num.html',
        ''.join(out_list),
        'Prototype CFP teleconference document list by document number')
    write_chron(
        all_data,
        'cfptc-all.html',
        'Prototype CFP teleconference document list, reverse-chronological',
        ('CFPTCA', 'CFPTCM'))


def action_format():
    """Format the papers lists.  The source data is in PAPERS_DIR; the
    formatted output goes to OUT_HTML_DIR."""
    all_data = DocList(PAPERS_DIR)
    do_format_simple(all_data, 'c')
    do_format_simple(all_data, 'cadm')
    do_format_cpub(all_data)
    do_format_cm(all_data)
    do_format_cfptc(all_data)
    with open('index.md', 'r', encoding='utf-8') as f:
        index_md = f.read()
    write_md(
        'index.html',
        index_md,
        'Prototype C document lists')


def main():
    """Main program."""
    parser = argparse.ArgumentParser(
        description='Format C papers lists in Markdown')
    parser.add_argument('action',
                        help='What to do',
                        choices=('format'))
    args = parser.parse_args()
    action_map = {'format': action_format}
    action_map[args.action]()


if __name__ == '__main__':
    main()
