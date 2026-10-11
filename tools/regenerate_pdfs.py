#!/usr/bin/env python3
"""Export the lecture and lab notebooks to PDF (for GitHub Releases).

The notebooks are exported as they are stored, with their saved outputs (nothing is re-executed):

* code hidden in Jupyter (tag ``hide-input``) is hidden in the PDF too, and the library setup cell
  of each lecture is left out;
* every interactive figure (ipywidgets ``interact``) is replaced by the figure it shows for the
  default slider positions, with those values printed under it;
* the HTML used for the notebook layout (title table, coloured boxes, collapsible answers) is turned
  into LaTeX: a title page, framed boxes and plain "question / answer" paragraphs;
* emoji markers are removed (LaTeX text fonts have no glyphs for them).

Nothing outside this repository is changed: the nbconvert template is written to a temporary
directory, your Jupyter configuration is left alone.

Usage:
    python3 tools/regenerate_pdfs.py                 # all notebooks -> pdf/
    python3 tools/regenerate_pdfs.py Лекція_04 Лб2   # only notebooks whose name contains one of these
    python3 tools/regenerate_pdfs.py --out DIR       # another output directory
    python3 tools/regenerate_pdfs.py --check         # only check that xelatex, pandoc, fonts are installed

Output file names are ASCII (GitHub renames non-ASCII release assets):
    Lecture_01.pdf … Lecture_13.pdf, Lectures_all.pdf (all lectures in one file), Lab_1.pdf … Lab_4.pdf,
    Glossary.pdf (from Глосарій.md).

Requires xelatex with the fvextra, xurl, mdframed, fancyhdr and polyglossia packages, pandoc and the DejaVu fonts:
    sudo apt install texlive-xetex texlive-latex-extra texlive-fonts-recommended pandoc fonts-dejavu
    pip install nbconvert pypdf
"""
import argparse
import copy
import glob
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = 'Електронні прилади та мікроелектроніка'
AUTHOR = 'Пахалюк Богдан Петрович'
UNIVERSITY = 'Національний університет «Чернігівська політехніка»'
LATEX_PACKAGES = ['fvextra', 'xurl', 'mdframed', 'fancyhdr', 'polyglossia']
FONTS = ['DejaVu Serif', 'DejaVu Sans', 'DejaVu Sans Mono']


def out_name(nb_path):
    """Лекція_04_….ipynb -> Lecture_04.pdf, Лб2_….ipynb -> Lab_2.pdf"""
    name = Path(nb_path).name
    m = re.match(r'Лекція_(\d+)_', name)
    if m:
        return f'Lecture_{m.group(1)}.pdf'
    m = re.match(r'Лб(\d+)_', name)
    if m:
        return f'Lab_{m.group(1)}.pdf'
    return Path(name).with_suffix('.pdf').name


# ---------------------------------------------------------------- prerequisites

def check_prerequisites():
    problems = []
    for cmd in ('xelatex', 'pandoc', 'kpsewhich'):
        if not shutil.which(cmd):
            problems.append(f'`{cmd}` not found')
    if shutil.which('kpsewhich'):
        for pkg in LATEX_PACKAGES:
            r = subprocess.run(['kpsewhich', f'{pkg}.sty'], capture_output=True, text=True)
            if not r.stdout.strip():
                problems.append(f'LaTeX package `{pkg}` not found')
    if shutil.which('fc-list'):
        fams = subprocess.run(['fc-list', '--format=%{family}\n'], capture_output=True, text=True).stdout
        for f in FONTS:
            if f not in fams:
                problems.append(f'font `{f}` not found')
    for mod in ('nbconvert', 'pypdf'):
        try:
            __import__(mod)
        except ImportError:
            problems.append(f'Python package `{mod}` not installed')
    if problems:
        print('Missing prerequisites:\n  - ' + '\n  - '.join(problems))
        print('\nInstall on Debian/Ubuntu:\n'
              '  sudo apt install texlive-xetex texlive-latex-extra texlive-fonts-recommended pandoc fonts-dejavu\n'
              '  pip install nbconvert pypdf')
    return not problems


# ---------------------------------------------------------------- nbconvert template

TEMPLATE = r'''((*- extends 'index.tex.j2' -*))

((* block docclass *))
\documentclass[11pt]{article}
((* endblock docclass *))

((* block packages *))
    ((( super() )))
    % Cyrillic text fonts (Cyrillic letters in formulas are wrapped in \text{} by cyrillic_math())
    \usepackage{polyglossia}
    \setdefaultlanguage{ukrainian}
    \setmainfont{DejaVu Serif}
    \setsansfont{DejaVu Sans}
    \setmonofont[Scale=0.85]{DejaVu Sans Mono}
    \usepackage{fvextra}
    \fvset{breaklines=true, breakanywhere=true}
    \usepackage{xurl}
    \usepackage{fancyhdr}
    \setlength{\headheight}{14pt}
    \usepackage{mdframed}
    % \elbox{background}{line} ... \elboxend — the coloured boxes of the notebooks
    \newcommand{\elbox}[2]{\definecolor{elboxbg}{HTML}{#1}\definecolor{elboxline}{HTML}{#2}%
      \begin{mdframed}[backgroundcolor=elboxbg, linecolor=elboxline, topline=false, rightline=false,
        bottomline=false, linewidth=3pt, innerleftmargin=10pt, innerrightmargin=10pt,
        innertopmargin=8pt, innerbottommargin=8pt, skipabove=8pt, skipbelow=8pt]}
    \newcommand{\elboxend}{\end{mdframed}}
((* endblock packages *))

((* block margins *))
\geometry{verbose,tmargin=2cm,bmargin=2cm,lmargin=2cm,rmargin=2cm}
((* endblock margins *))

((* block maketitle *))((* endblock maketitle *))

((* block commands *))
    ((( super() )))
    \definecolor{linkcolor}{HTML}{1F4E79}
    \definecolor{urlcolor}{HTML}{1F4E79}
    \hypersetup{linkcolor=linkcolor, urlcolor=urlcolor}
    \setcounter{secnumdepth}{2}
    \setcounter{tocdepth}{2}
((* endblock commands *))
'''


# ---------------------------------------------------------------- preprocessors

EMOJI = re.compile('[\U0001F000-\U0001FFFF☀-➿⬀-⯿︀-️⃣‍]+')
STYLE_COLOR = r'(?:background-color|background)\s*:\s*#([0-9a-fA-F]{6})'
BORDER_COLOR = r'border-left\s*:[^;"]*#([0-9a-fA-F]{6})'


def latex_escape(s):
    return (s.replace('\\', r'\textbackslash{}').replace('&', r'\&').replace('%', r'\%')
             .replace('#', r'\#').replace('_', r'\_').replace('{', r'\{').replace('}', r'\}'))


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()


def title_page(src, kind_label):
    """Raw LaTeX title page from the HTML title table of a lecture."""
    h3 = re.search(r'<h3>(.*?)</h3>', src, re.S)
    h3 = strip_tags(h3.group(1)) if h3 else kind_label
    topics = [strip_tags(t) for t in re.findall(r'<li>(.*?)</li>', src, re.S)]
    of = re.search(r'(Лекція \d+ з \d+)', src)
    items = ''.join(f'  \\item {latex_escape(t)}\n' for t in topics)
    m = re.match(r'(Лекція \d+)\.\s*(.*)', h3)
    short, name = (m.group(1), m.group(2)) if m else (kind_label, h3)
    return rf'''\pagestyle{{fancy}}\fancyhf{{}}
\fancyhead[L]{{\small {COURSE}}}\fancyhead[R]{{\small {latex_escape(short)}}}
\fancyfoot[C]{{\small\thepage}}
\begin{{titlepage}}
\centering
{{\large Конспект лекцій з дисципліни}}\par\vspace{{4pt}}
{{\LARGE\bfseries «{COURSE}»}}\par\vspace{{1.6cm}}
{{\Large {latex_escape(short)}}}\par\vspace{{6pt}}
{{\huge\bfseries {latex_escape(name)}}}\par\vspace{{1.4cm}}
\begin{{minipage}}{{0.62\linewidth}}\raggedright
\textbf{{Теми лекції:}}
\begin{{itemize}}
{items}\end{{itemize}}
\end{{minipage}}\par\vfill
\includegraphics[width=2.6cm]{{Teacher.jpg}}\par\vspace{{6pt}}
Викладач: доктор філософії {AUTHOR}\par\vspace{{4pt}}
{UNIVERSITY}\par\vspace{{4pt}}
{{\small {latex_escape(of.group(1)) if of else ''}}}
\end{{titlepage}}
\tableofcontents
\clearpage
'''


CYR = re.compile("[\u0400-\u04FF][\u0400-\u04FF'’]*")


def cyrillic_math(src):
    """$U_{вих}$ -> $U_{\\text{вих}}$: math fonts have no Cyrillic glyphs (and descriptive subscripts are upright)."""
    return re.sub(r'\$\$.+?\$\$|\$[^$\n]+\$', lambda m: CYR.sub(lambda c: rf'\text{{{c.group(0)}}}', m.group(0)),
                  src, flags=re.S)


def html_to_markdown(src):
    """Turns the layout HTML of a markdown cell into markdown + raw LaTeX that pandoc keeps."""
    def box(m):
        style = m.group(1)
        bg = re.search(STYLE_COLOR, style)
        line = re.search(BORDER_COLOR, style)
        if not (bg and line):
            return '\n'
        return f'\n\\elbox{{{bg.group(1).upper()}}}{{{line.group(1).upper()}}}\n'

    src = re.sub(r'<summary[^>]*>(.*?)</summary>', lambda m: '\n' + m.group(1).strip() + '\n', src, flags=re.S)
    src = re.sub(r'<details([^>]*)>', lambda m: box(m), src)
    src = re.sub(r'</details>', '\n\\\\elboxend\n', src)
    src = re.sub(r'<div\s+style="([^"]*)"\s*>', box, src)
    # each </div> closes the box opened above it (boxes are not nested in the notebooks)
    src = re.sub(r'</div>', '\n\\\\elboxend\n', src)
    src = re.sub(r'<a class="anchor"[^>]*></a>', '', src)
    src = re.sub(r'</?b>', '**', src)
    src = re.sub(r'<hr\s*/?>', '', src)
    src = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', src, flags=re.S)
    src = re.sub(r'^\s*---\s*$', '', src, flags=re.M)          # horizontal rules between sections
    src = EMOJI.sub('', src)
    src = cyrillic_math(src)
    src = re.sub(r'[ \t]+\n', '\n', src)
    src = re.sub(r'^(#+)\s+', r'\1 ', src, flags=re.M)          # "### ⚙️ PySpice" -> "### PySpice"
    # lecture summary and references: unnumbered top-level sections
    src = re.sub(r'^## ((?:Підсумок|Рекомендована).*)$', r'# \1 {-}', src, flags=re.M)
    # pandoc (unlike Jupyter) needs a blank line before a list that follows a paragraph
    src = re.sub(r'^(>?)([ \t]*[^\s>\-*\d|][^\n]*)\n(\1[ \t]*[-*] )', r'\1\2\n\1\n\3', src, flags=re.M)
    return src


def control_value(st):
    if 'value' in st and not isinstance(st['value'], (list, dict)):
        v = st['value']
        if isinstance(v, bool):
            return 'так' if v else 'ні'
        if isinstance(v, float):
            return f'{v:g}'
        return str(v)
    if 'index' in st and st.get('_options_labels'):
        return st['_options_labels'][st['index']]
    return None


def widget_snapshot(cell, state):
    """Replaces the widget output of an interact() cell by its stored figure + the default control values."""
    outputs = []
    for o in cell.get('outputs', []):
        mid = o.get('data', {}).get('application/vnd.jupyter.widget-view+json', {}).get('model_id')
        if not mid:
            outputs.append(o)
            continue
        controls, figs, stack = [], [], [mid]
        while stack:
            m = state.get(stack.pop(0), {})
            st = m.get('state', {})
            if m.get('model_name') == 'OutputModel':
                figs += [x for x in st.get('outputs', []) if x.get('output_type') != 'stream']
            elif st.get('description') is not None and control_value(st) is not None:
                controls.append(f'{st["description"].rstrip(":").strip()} = {control_value(st)}')
            stack += [ch.replace('IPY_MODEL_', '') for ch in st.get('children', [])]
        outputs += figs
        if controls:
            text = 'Інтерактивний графік, показано для: ' + '; '.join(controls)
            outputs.append({'output_type': 'display_data', 'metadata': {},
                            'data': {'text/markdown': f'*{text}*', 'text/plain': text}})
    from nbformat import from_dict
    cell['outputs'] = [from_dict(o) for o in outputs]


def latex_cell(src):
    from nbformat.v4 import new_raw_cell
    return new_raw_cell(src, metadata={'raw_mimetype': 'text/latex'})


def prepare(nb):
    """Returns a copy of the notebook ready for LaTeX export."""
    nb = copy.deepcopy(nb)
    state = nb.metadata.get('widgets', {}).get('application/vnd.jupyter.widget-state+json', {}).get('state', {})
    nb.metadata.pop('widgets', None)
    cells, skip_next_code = [], False
    for i, c in enumerate(nb.cells):
        src = c.source
        if c.cell_type == 'markdown':
            if '<table style="width:100%">' in src and '<h3>' in src:      # lecture title table
                cells.append(latex_cell(title_page(src, 'Лекція')))
                continue
            if '<b>Зміст</b>' in src:                                     # replaced by \tableofcontents
                continue
            if src.startswith('**Підключення бібліотек.**'):              # lecture setup: leave out
                skip_next_code = True
                continue
            if '.ipynb)' in src and '<p style="text-align: center;">' in src:   # links to other notebooks
                src = re.sub(r'<p style="text-align: center;">.*?</p>', '', src, flags=re.S)
            if i == 0 and src.lstrip().startswith('# '):                  # lab: first heading is the title
                head, _, rest = src.lstrip().partition('\n')
                cells.append(latex_cell(rf'''\pagestyle{{fancy}}\fancyhf{{}}
\fancyhead[L]{{\small {COURSE}}}\fancyhead[R]{{\small Лабораторна робота}}
\fancyfoot[C]{{\small\thepage}}
\setcounter{{secnumdepth}}{{0}}
\begin{{center}}{{\Large\bfseries {latex_escape(head[2:].strip())}}}\par\vspace{{4pt}}
{{\small {COURSE} · {UNIVERSITY}}}\end{{center}}
'''))
                src = rest
            c.source = html_to_markdown(src)
        elif c.cell_type == 'code':
            if skip_next_code:
                skip_next_code = False
                continue
            # the Google Colab install block of the setup cell means nothing on paper
            c.source = re.sub(r"^import sys, os\nif 'google\.colab'.*?\n\n", '', c.source, flags=re.S)
            widget_snapshot(c, state)
            for o in c.outputs:                     # PNG is enough; SVG would need inkscape
                if 'image/png' in o.get('data', {}):
                    o['data'].pop('image/svg+xml', None)
            c.outputs = [o for o in c.outputs
                         if not (o.get('output_type') == 'stream' and not o.get('text', '').strip())]
            tags = c.metadata.get('tags', [])
            if 'hide-input' in tags or c.metadata.get('jupyter', {}).get('source_hidden'):
                c.metadata.setdefault('tags', []).append('remove_input')
        cells.append(c)
    nb.cells = cells
    return nb


# ---------------------------------------------------------------- export

def make_exporter(template_dir):
    from nbconvert import PDFExporter
    from traitlets.config import Config
    c = Config()
    c.PDFExporter.extra_template_basedirs = [str(template_dir)]
    c.PDFExporter.template_name = 'eldev_pdf'
    c.PDFExporter.template_file = 'eldev.tex.j2'
    c.PDFExporter.latex_count = 3
    c.PDFExporter.raw_mimetypes = ['text/latex', '']          # keep the raw LaTeX title cells
    c.TagRemovePreprocessor.enabled = True
    c.TagRemovePreprocessor.remove_input_tags = {'remove_input'}
    return PDFExporter(config=c)


def export(exporter, path, out_dir):
    import nbformat
    nb = prepare(nbformat.read(path, as_version=4))
    body, _ = exporter.from_notebook_node(nb, resources={'metadata': {'path': str(ROOT), 'name': Path(path).stem}})
    out = out_dir / out_name(path)
    out.write_bytes(body)
    return out


def export_glossary(out_dir, work):
    src = ROOT / 'Глосарій.md'
    if not src.exists():
        return None
    header = work / 'glossary-header.tex'
    header.write_text(r'''\usepackage{fancyhdr}\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small ''' + COURSE + r'''}\fancyhead[R]{\small Глосарій}\fancyfoot[C]{\small\thepage}
''', encoding='utf-8')
    md = cyrillic_math(EMOJI.sub('', src.read_text(encoding='utf-8')))
    md = re.sub(r'\[([^\]]*)\]\([^)#]*\.(?:ipynb|md)[^)]*\)', r'\1', md)   # links to notebooks: plain text
    md = re.sub(r'</?div[^>]*>', '', md)
    md = re.sub(r'^\*\*Зміст:\*\*.*$', '', md, flags=re.M)                     # in-page links of the GitHub page
    out = out_dir / 'Glossary.pdf'
    # pandoc markdown + --columns: wide pipe tables get relative column widths and wrapped cells
    subprocess.run(['pandoc', '-f', 'markdown-auto_identifiers', '--columns=60', '-o', str(out), '--pdf-engine=xelatex',
                    '-V', 'mainfont=DejaVu Serif', '-V', 'sansfont=DejaVu Sans', '-V', 'monofont=DejaVu Sans Mono',
                    '-V', 'geometry:margin=2cm', '-V', 'fontsize=10pt', '-V', 'colorlinks=true',
                    '-V', 'lang=uk', '-H', str(header)],
                   input=md, text=True, check=True, cwd=ROOT)
    return out


def merge_lectures(pdfs, out):
    import logging
    from pypdf import PdfWriter, PdfReader
    logging.getLogger('pypdf').setLevel(logging.ERROR)    # in-page links of the separate files are not carried over
    w = PdfWriter()
    for p in pdfs:
        # bookmark per lecture with its sections under it; the separate files' named destinations
        # (section.1, ...) repeat from file to file, so bookmarks are rebuilt with page numbers
        r = PdfReader(p)
        start = len(w.pages)
        w.append(r, import_outline=False)
        parent = w.add_outline_item(f'Лекція {int(p.stem.split("_")[1])}', start)

        def add(items, parent):
            last = parent
            for it in items:
                if isinstance(it, list):
                    add(it, last)
                else:
                    last = w.add_outline_item(it.title, start + r.get_destination_page_number(it), parent=parent)
        add(r.outline, parent)
    w.add_metadata({'/Title': f'{COURSE}. Конспект лекцій', '/Author': AUTHOR})
    with open(out, 'wb') as fh:
        w.write(fh)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('only', nargs='*', help='export only notebooks whose file name contains one of these strings')
    ap.add_argument('--out', default=str(ROOT / 'pdf'), help='output directory (default: pdf/)')
    ap.add_argument('--check', action='store_true', help='only check the prerequisites')
    args = ap.parse_args()

    if not check_prerequisites():
        return 1
    if args.check:
        print('OK: xelatex, pandoc, LaTeX packages and fonts found.')
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    notebooks = sorted(glob.glob(str(ROOT / 'Лекція_*.ipynb'))) + sorted(glob.glob(str(ROOT / 'Лб*.ipynb')))
    if args.only:
        notebooks = [p for p in notebooks if any(s in Path(p).name for s in args.only)]

    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp) / 'eldev_pdf'
        tdir.mkdir()
        (tdir / 'conf.json').write_text(
            '{"base_template": "latex", "mimetypes": {"text/latex": true, "text/tex": true, "application/pdf": true}}')
        (tdir / 'eldev.tex.j2').write_text(TEMPLATE, encoding='utf-8')
        exporter = make_exporter(Path(tmp))
        for p in notebooks:
            print(f'  {Path(p).name} -> {out_name(p)} ... ', end='', flush=True)
            try:
                export(exporter, p, out_dir)
                print('done')
            except Exception as e:                       # noqa: BLE001 — report and go on with the others
                print('FAILED')
                failed.append((p, e))
        if not args.only or any(s in ('Глосарій', 'Glossary') for s in args.only):
            print('  Глосарій.md -> Glossary.pdf ... ', end='', flush=True)
            try:
                print('done' if export_glossary(out_dir, Path(tmp)) else 'skipped (no Глосарій.md)')
            except Exception as e:                       # noqa: BLE001
                print('FAILED')
                failed.append(('Глосарій.md', e))

    lectures = sorted(out_dir.glob('Lecture_[0-9]*.pdf'))
    if not args.only and not failed and lectures:
        merge_lectures(lectures, out_dir / 'Lectures_all.pdf')
        print(f'  {len(lectures)} lectures -> Lectures_all.pdf')

    for p, e in failed:
        print(f'\n--- {Path(p).name} ---\n{str(e)[-3000:]}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
