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


def get_data(dirname):
    """Get data for all papers."""
    out_data = {}
    paper_nums = os.listdir(dirname)
    for n in paper_nums:
        n_dir = os.path.join(dirname, n)
        with open(os.path.join(n_dir, 'metadata.json'), 'r',
                  encoding='utf-8') as f:
            out_data[n] = json.load(f)
    return out_data


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


def do_format_simple(doc_class):
    """Format simple lists of a papers in a given class.  The source
    data is in PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    doc_class_upper = doc_class.upper()
    data = get_data(os.path.join(PAPERS_DIR, doc_class_upper))
    rev_sort = {}
    by_rev = {}
    for doc in data.values():
        for rev in doc['revisions']:
            by_rev[rev['id']] = rev
            # Sort first by date, then, within a date, by document
            # revision ID.
            rev_sort[rev['id']] = (rev['date'], split_doc_id(rev['id']))
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
    out_list = ['# Prototype %s document list, reverse-chronological\n\n'
                % doc_class_upper]
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for rev_id in sorted(by_rev.keys(), key=lambda k: rev_sort[k],
                         reverse=True):
        out_list.append(table_line_for_rev(by_rev[rev_id], True))
    write_md(
        '%s-all.html' % doc_class,
        ''.join(out_list),
        'Prototype %s document list, reverse-chronological' % doc_class_upper)


def do_format_cpub():
    """Format lists of CPUB and CPUBX documents.  The source data is
    in PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    cpub_data = get_data(os.path.join(PAPERS_DIR, 'CPUB'))
    cpubx_data = get_data(os.path.join(PAPERS_DIR, 'CPUBX'))
    rev_sort = {}
    by_rev = {}
    aux_for_cpub_ed = {}
    for doc in cpub_data.values():
        for e in doc['editions']:
            aux_for_cpub_ed[e['id']] = set()
            for rev in e['revisions']:
                by_rev[rev['id']] = rev
                # Sort first by date, then, within a date, by document
                # revision ID.
                rev_sort[rev['id']] = (rev['date'], split_doc_id(rev['id']))
    for doc in cpubx_data.values():
        for rev in doc['revisions']:
            by_rev[rev['id']] = rev
            aux_for_cpub_ed[rev['cpub-edition']].add(rev['id'])
            # Sort first by date, then, within a date, by document
            # revision ID.
            rev_sort[rev['id']] = (rev['date'], split_doc_id(rev['id']))
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
            all_revs = e['revisions'] + [by_rev[r] for r in aux_for_cpub_ed[e['id']]]
            for rev in sorted(all_revs, key=lambda k: rev_sort[k['id']], reverse=True):
                out_list.append(table_line_for_rev(rev, True))
    write_md(
        'cpub-num.html',
        ''.join(out_list),
        'Prototype CPUB and CPUBX document list by document number')
    out_list = ['# Prototype CPUB and CPUBX document list, reverse-chronological\n\n']
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for rev_id in sorted(by_rev.keys(), key=lambda k: rev_sort[k],
                         reverse=True):
        out_list.append(table_line_for_rev(by_rev[rev_id], True))
    write_md(
        'cpub-all.html',
        ''.join(out_list),
        'Prototype CPUB and CPUBX document list, reverse-chronological')


def do_format_cm():
    """Format lists of meeting papers.  The source data is in
    PAPERS_DIR; the formatted output goes to OUT_HTML_DIR."""
    cm_data = get_data(os.path.join(PAPERS_DIR, 'CM'))
    cma_data = get_data(os.path.join(PAPERS_DIR, 'CMA'))
    cmm_data = get_data(os.path.join(PAPERS_DIR, 'CMM'))
    data = cm_data.copy()
    data.update(cma_data)
    data.update(cmm_data)
    rev_sort = {}
    by_rev = {}
    for doc in data.values():
        for rev in doc['revisions']:
            by_rev[rev['id']] = rev
            # Sort first by date, then, within a date, by document
            # revision ID.
            rev_sort[rev['id']] = (rev['date'], split_doc_id(rev['id']))
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
    out_list = ['# Prototype meeting document list, reverse-chronological\n\n']
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for rev_id in sorted(by_rev.keys(), key=lambda k: rev_sort[k],
                         reverse=True):
        out_list.append(table_line_for_rev(by_rev[rev_id], True))
    write_md(
        'cm-all.html',
        ''.join(out_list),
        'Prototype meeting document list, reverse-chronological')


def action_format():
    """Format the papers lists.  The source data is in PAPERS_DIR; the
    formatted output goes to OUT_HTML_DIR."""
    do_format_simple('c')
    do_format_simple('cadm')
    do_format_cpub()
    do_format_cm()
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
