#! /usr/bin/env python3

import argparse
import json
import os
import os.path
from mistletoe import Document
from mistletoe.html_renderer import HtmlRenderer


# The location of papers data and metadata.
PAPERS_DIR = 'out/papers/C'


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


def table_line_for_rev(rev, show_num):
    """Generate a Markdown table line for a document revision."""
    if rev['ext-url']:
        link = '[%s (%s)](%s)' % (rev['rev-id'], rev['ext-id'], rev['ext-url'])
    else:
        link = '%s (%s)' % (rev['rev-id'], rev['ext-id'])
    n = rev['doc-id'] if show_num else ' '
    return ('|%s|%s|%s|%s|%s|\n'
            % (n, link, rev['author'], rev['date'], rev['title']))


def action_format():
    """Format the papers lists.  The source data is in PAPERS_DIR; the
    formatted output goes to OUT_HTML_DIR."""
    data = get_data(PAPERS_DIR)
    rev_sort = {}
    by_rev = {}
    by_rev_num = {}
    for doc in data.values():
        for rev in doc['revisions']:
            by_rev[rev['id']] = rev
            # Sort first by date, then, within a date, by document
            # revision ID.  This should properly sort after splitting
            # out numbers, not by strings, for a non-prototype.
            rev_sort[rev['id']] = (rev['date'], rev['id'])
    out_list = ['# Prototype C document list by document number\n\n']
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for n in sorted(data.keys(), reverse=True):
        cdoc = data[n]
        out_list.append('|%s| |%s| |%s|\n' % (cdoc['id'], cdoc['author'],
                                            cdoc['title']))
        for rev in reversed(cdoc['revisions']):
            out_list.append(table_line_for_rev(rev, False))
    write_md(
        'c-num.html',
        ''.join(out_list),
        'Prototype C document list by document number')
    out_list = ['# Prototype C document list, reverse-chronological\n\n']
    out_list.append('|Number|Revision|Author|Date|Title|\n|-|-|-|-|-|\n')
    for rev_id in sorted(by_rev.keys(), key=lambda k: rev_sort[k],
                         reverse=True):
        out_list.append(table_line_for_rev(by_rev[rev_id], True))
    write_md(
        'c-all.html',
        ''.join(out_list),
        'Prototype C document list, reverse-chronological')
    write_md(
        'index.html',
        '# Prototype C document lists\n\n'
        '* [All revisions of C-documents, reverse-chronological](c-all.html)\n'
        '* [C-documents in reverse order by document number](c-num.html)\n',
        'Prototype C document lists')


def main():
    """Main program."""
    parser = argparse.ArgumentParser(
        description='Format C issues in Markdown')
    parser.add_argument('action',
                        help='What to do',
                        choices=('format'))
    args = parser.parse_args()
    action_map = {'format': action_format}
    action_map[args.action]()


if __name__ == '__main__':
    main()
