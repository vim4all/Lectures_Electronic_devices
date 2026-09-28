"""Генератор конспектів лекцій (структура як у Lectures_Basics_of_radio_electronics_in_Ukrainian)."""
import os, re, json, base64, sys, textwrap
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

REPO = '/mnt/d/Pr/_University/Teaching/3_ElectronicDevices/ElDev_repo'
SCRATCH = os.path.dirname(os.path.abspath(__file__))

LECTURES = [
    ('01', 'Фізичні_основи_напівпровідників', 'Фізичні основи напівпровідників'),
    ('02', 'Електронно-дірковий_перехід', 'Електронно-дірковий (p-n) перехід'),
    ('03', 'Вольт-амперна_характеристика_діода', 'Вольт-амперна характеристика діода. Пробій і перехідні процеси'),
    ('04', 'Напівпровідникові_діоди_та_їх_застосування', 'Напівпровідникові діоди та їх застосування'),
    ('05', 'Біполярний_транзистор_принцип_дії', 'Біполярний транзистор: будова, принцип дії, режими'),
    ('06', 'Статичні_характеристики_біполярного_транзистора', 'Статичні характеристики та параметри біполярного транзистора'),
    ('07', 'Біполярний_транзистор_у_динамічному_режимі', 'Біполярний транзистор у підсилювальному та ключовому режимах'),
    ('08', 'Польові_транзистори_з_керуючим_pn_переходом', 'Польові транзистори з керуючим p-n переходом'),
    ('09', 'МДН-транзистори', 'МДН-транзистори (MOSFET)'),
    ('10', 'Динаміка_ПТ_потужні_МДН_та_IGBT', 'Динамічні властивості польових транзисторів. Потужні МДН-транзистори та IGBT'),
    ('11', 'Тиристорні_прилади', 'Тиристорні прилади'),
    ('12', 'Оптоелектронні_прилади', 'Оптоелектронні прилади'),
    ('13', 'ПЗЗ_терморезистори_варістори', 'Прилади із зарядовим зв\'язком, терморезистори та варістори'),
]
N_LECT = len(LECTURES)


def fname(num):
    for n, f, t in LECTURES:
        if n == num:
            return f'Лекція_{n}_{f}.ipynb'
    raise KeyError(num)


def title(num):
    return dict((n, t) for n, f, t in LECTURES)[num]


HIDE = {"jupyter": {"source_hidden": True}, "tags": ["hide-input"]}


class NB:
    def __init__(self, num):
        self.num = num
        self.cells = []

    # ---------- базові комірки ----------
    def md(self, text):
        self.cells.append(new_markdown_cell(textwrap.dedent(text).strip('\n')))

    def code(self, src, hidden=True):
        c = new_code_cell(textwrap.dedent(src).strip('\n'))
        if hidden:
            c.metadata.update(json.loads(json.dumps(HIDE)))
        self.cells.append(c)

    # ---------- шапка / зміст / налаштування ----------
    def header(self, topics):
        lis = '\n'.join(f'  <li>{t}</li>' for t in topics)
        self.md(f'''
---

<table style="width:100%">
  <tr>
    <th>
        <div style="text-align: center; background-color: #f0f0f0; padding: 20px; border-radius: 10px;">
<p style="text-align: center;"> Конспект лекцій з предмету: </p>
<p style="text-align: center;"><b><h2>"Електронні прилади та мікроелектроніка"</h2></b></p>
<p style="text-align: center;"><b><h3>Лекція {int(self.num)}. {title(self.num)}</h3></b></p>
<p style="text-align: center;"> Національний університет "Чернігівська політехніка"</p>
<p style="text-align: center;"><b>Кафедра:</b> Радіотехніки та відеоінформаційних систем (РТВС)</p>
<hr/>
<p style="text-align: center;"><b>Теми лекції:</b></p>
<ul style="text-align: left;">
{lis}
</ul>
</div>
    </th>
    <th>
<div style="text-align: center; background-color: #f0f0f0; padding: 20px; border-radius: 10px;">
<p style="text-align: center;"> <b>Викладач:</b> </p>
<p style="text-align: center;"> Доктор філософії, Кафедра РТВС</p>
<p style="text-align: center;"> Пахалюк Богдан Петрович</p>
<img src="./Teacher.jpg" alt="" width="110" >
<hr/>
<p style="text-align: center; font-size: 0.9em;">Лекція {int(self.num)} з {N_LECT}</p>
</div>
    </th>
  </tr>
</table>

---
''')

    def toc(self, items):
        """items: list of (level, text, anchor)"""
        lines = []
        for lvl, text, anc in items:
            lines.append('    ' * lvl + f'* [{text}](#{anc})')
        body = '\n'.join(lines)
        self.md(f'''
---

<p style="text-align: center;"><b>Зміст</b></p>

{body}

> 💡 Код демонстрацій та інтерактивних графіків **згорнуто**, щоб не відволікати від матеріалу. Щоб переглянути його, натисніть на «⋯» (або на смужку ліворуч від комірки). Для роботи інтерактивних елементів виконайте всі комірки: *Run → Run All Cells*. Позначка 🔬 — інтерактивне моделювання (повзунки), ⚙️ — моделювання схеми в **PySpice/ngspice**.

---
''')

    def setup(self, extra=''):
        self.md('''
**Підключення бібліотек.** NumPy/Matplotlib — чисельні розрахунки та графіки, ipywidgets — інтерактивні повзунки, PySpice + ngspice — схемотехнічне моделювання, schemdraw — побудова схем з умовними позначеннями за ДСТУ/IEC. SPICE-моделі реальних приладів зібрано в теці `models/`. Цю комірку потрібно виконати першою.
''')
        self.code(SETUP + ('\n' + textwrap.dedent(extra).strip('\n') if extra else ''), hidden=False)

    # ---------- оформлення блоків ----------
    def section(self, text, anchor, level=2):
        return f'{"#" * level} {text} <a class="anchor" id="{anchor}"></a>'

    def goals(self, items, title_='🎯 Мета вивчення розділу'):
        li = '\n'.join(f'> - {x}' for x in items)
        return f'''### {title_}

<div style="background-color: #eef2ff; padding: 16px 18px; border-radius: 10px; border-left: 4px solid #4f46e5; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">

> Після вивчення цього розділу студент повинен вміти:
{li}

</div>
'''

    def concepts(self, rows):
        r = '\n'.join(f'| **{a}** | {b} |' for a, b in rows)
        return f'''### 📖 Ключові поняття

| Поняття | Визначення |
|---------|-----------|
{r}
'''

    @staticmethod
    def box(kind, title_, text):
        styles = {
            'fact': ('💡 Цікаво знати', '#eff6ff', '#2563eb'),
            'mistake': ('⚠️ Типова помилка', '#fef2f2', '#dc2626'),
            'practice': ('⚡ Практичне застосування', '#fffbeb', '#f59e0b'),
            'summary': ('📌 Підсумок', '#f0fdf4', '#16a34a'),
            'note': ('📝 Зверніть увагу', '#f8fafc', '#64748b'),
        }
        head, bg, bd = styles[kind]
        if title_:
            head = f'{head}: {title_}'
        return f'''---
### {head}

<div style="background-color: {bg}; padding: 16px 18px; border-radius: 10px; border-left: 4px solid {bd}; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">

{textwrap.dedent(text).strip()}

</div>
'''

    def questions(self, title_, qa):
        out = [f'---\n### ✅ Питання для самоперевірки: {title_}\n']
        for i, (q, a) in enumerate(qa, 1):
            out.append(f'''<details style="margin: 10px 0; padding: 10px 14px; background: #ecfdf5; border-radius: 8px; border-left: 3px solid #0d9488;">
<summary style="cursor: pointer; font-weight: 600; color: #0f766e;"><b>Питання {i}.</b> {q}</summary>

> **Відповідь:** {a}

</details>
''')
        self.md('\n'.join(out))

    def problems(self, title_, items):
        out = [f'---\n### 📝 Задачі для самостійного розв\'язання: {title_}\n']
        for i, (task, sol) in enumerate(items, 1):
            out.append(f'''
<div style="background-color: #fff1f2; padding: 12px 18px; border-radius: 10px; border-left: 4px solid #e11d48; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin: 10px 0;">

**Задача {i}.** {task}

</div>

<details style="margin: 10px 0; padding: 10px 14px; background: #ecfdf5; border-radius: 8px; border-left: 3px solid #0d9488;">
<summary style="cursor: pointer; font-weight: 600; color: #0f766e;">Відповідь і розв'язання</summary>

> {sol}

</details>
''')
        self.md('\n'.join(out))

    def finish(self, summary_title, summary_text, refs_extra=()):
        self.md(f'''
---

## 📌 Підсумок лекції {int(self.num)}: {summary_title} <a class="anchor" id="summary"></a>

<div style="background-color: #f0fdf4; padding: 24px 18px; border-radius: 10px; border-left: 4px solid #16a34a; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">

{textwrap.dedent(summary_text).strip()}

</div>
''')
        extra = ''.join(f'\n{i}. {r}' for i, r in enumerate(refs_extra, 7))
        self.md(f'''
---

## 📚 Рекомендована література та ресурси <a class="anchor" id="references"></a>

**Основна література**

1. Прищепа М. М., Погребняк В. П. Мікроелектроніка. Ч. 1. Елементи мікроелектроніки: навч. посібник. — К.: Вища школа, 2004.
2. Бойко В. І., Гуржій А. М., Жуйков В. Я. та ін. Схемотехніка електронних систем. Кн. 1. Аналогова схемотехніка та імпульсні пристрої. — К.: Вища школа, 2004.
3. Sze S. M., Ng K. K. Physics of Semiconductor Devices. — 3rd ed. — Wiley, 2007.
4. Neamen D. A. Semiconductor Physics and Devices: Basic Principles. — 4th ed. — McGraw-Hill, 2012.

**Додаткова література**

5. Sedra A. S., Smith K. C. Microelectronic Circuits. — 8th ed. — Oxford University Press, 2020.
6. Streetman B. G., Banerjee S. K. Solid State Electronic Devices. — 7th ed. — Pearson, 2016.{extra}

**Програмні інструменти, що використовуються в конспекті**

- [PySpice](https://pyspice.fabrice-salvaire.fr/) + [ngspice](https://ngspice.sourceforge.io/) — схемотехнічне моделювання (SPICE-моделі приладів — у теці `models/`)
- [SchemDraw](https://schemdraw.readthedocs.io/) — побудова електричних схем
- [NumPy](https://numpy.org/doc/) / [SciPy](https://docs.scipy.org/doc/scipy/) / [Matplotlib](https://matplotlib.org/) — чисельні розрахунки та графіки
- [ipywidgets](https://ipywidgets.readthedocs.io/) — інтерактивні елементи керування
''')
        prev_ = f'{int(self.num) - 1:02d}'
        next_ = f'{int(self.num) + 1:02d}'
        parts = []
        if int(self.num) > 1:
            parts.append(f'⬅️ [Лекція {int(prev_)}. {title(prev_)}]({fname(prev_)})')
        if int(self.num) < N_LECT:
            parts.append(f'[Лекція {int(next_)}. {title(next_)}]({fname(next_)}) ➡️')
        nav = ' &nbsp;|&nbsp; '.join(parts)
        self.md(f'''
---

<p style="text-align: center;">{nav}</p>

*Конспект підготовлено: Пахалюк Богдан Петрович, НУ "Чернігівська політехніка"*
''')

    # ---------- збереження / виконання ----------
    def save(self, execute=True):
        nb = new_notebook(cells=self.cells)
        nb.metadata = {
            'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python', 'version': '3.12.3'},
        }
        path = os.path.join(REPO, fname(self.num))
        nbformat.write(nb, path)
        if execute:
            return run(path)
        return path


def run(path):
    from nbclient import NotebookClient
    from nbclient.exceptions import CellTimeoutError
    for attempt in range(3):          # nbclient зрідка «губить» відповідь ядра після комірки з віджетом — повторюємо
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(nb, timeout=90, kernel_name='python3',
                                resources={'metadata': {'path': REPO}}, store_widget_state=True)
        try:
            client.execute(); break
        except CellTimeoutError:
            print(f'  timeout, attempt {attempt + 1} — retry')
    else:
        raise RuntimeError('notebook execution kept timing out')
    # помилки всередині віджетів
    problems = []
    state = nb.metadata.get('widgets', {}).get('application/vnd.jupyter.widget-state+json', {}).get('state', {})
    for mid, m in state.items():
        for out in m.get('state', {}).get('outputs', []):
            if out.get('output_type') == 'error':
                problems.append(f"{out['ename']}: {out['evalue']}")
            if out.get('output_type') == 'stream' and out.get('name') == 'stderr':
                problems.append('stderr: ' + out.get('text', '')[:300])
    for i, c in enumerate(nb.cells):
        if c.cell_type == 'code':
            for o in c.get('outputs', []):
                if o.get('output_type') == 'stream' and o.get('name') == 'stderr':
                    problems.append(f'cell {i} stderr: ' + o.get('text', '')[:300])
    nbformat.write(nb, path)
    dump_images(path)
    if problems:
        print('PROBLEMS:', *problems, sep='\n  ')
    return path


def dump_images(path):
    """Зберігає всі PNG-виходи (включно з виходами віджетів) для візуальної перевірки."""
    nb = nbformat.read(path, as_version=4)
    num = re.search(r'Лекція_(\d+)_', path).group(1)
    outdir = os.path.join(SCRATCH, 'imgs', num)
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    k = 0
    state = nb.metadata.get('widgets', {}).get('application/vnd.jupyter.widget-state+json', {}).get('state', {})
    for i, c in enumerate(nb.cells):
        if c.cell_type != 'code':
            continue
        outs = list(c.get('outputs', []))
        # outputs inside widgets referenced by this cell
        for o in c.get('outputs', []):
            mid = o.get('data', {}).get('application/vnd.jupyter.widget-view+json', {}).get('model_id')
            stack = [mid] if mid else []
            while stack:
                m = stack.pop()
                st = state.get(m, {}).get('state', {})
                outs += st.get('outputs', [])
                stack += [ch.replace('IPY_MODEL_', '') for ch in st.get('children', [])]
        for j, o in enumerate(outs):
            data = o.get('data', {})
            if 'image/png' in data:
                fn = os.path.join(outdir, f'c{i:02d}_{j}.png')
                with open(fn, 'wb') as fh:
                    fh.write(base64.b64decode(data['image/png']))
                k += 1
    print(f'{os.path.basename(path)}: {k} images -> {outdir}')


SETUP = r'''
import warnings
warnings.filterwarnings('ignore', message='Unable to import Axes3D')
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from ipywidgets import interact, interactive, fixed, HBox, VBox, Output
import ipywidgets as widgets
from IPython.display import display, HTML, Markdown
%matplotlib inline

import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging(logging_level='ERROR')
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ngspice ≥ 41 пише в stderr інформаційні повідомлення (напр. "Using SPARSE 1.3 as Direct Linear Solver"),
# які PySpice 1.5 вважає помилкою симуляції. Сприймаємо як помилку лише рядки, що містять "error".
from PySpice.Spice.NgSpice import Shared as _ngspice_shared
_orig_send_char = _ngspice_shared.NgSpiceShared._send_char
def _send_char(message_c, ngspice_id, user_data):
    message = _ngspice_shared.ffi_string_utf8(message_c)
    prefix, _, content = message.partition(' ')
    if prefix == 'stderr' and 'error' not in content.lower() and 'init file' not in content:
        self = _ngspice_shared.ffi.from_handle(user_data)
        self._stderr.append(content)
        return self.send_char(message, ngspice_id)
    return _orig_send_char(message_c, ngspice_id, user_data)
_ngspice_shared.NgSpiceShared._send_char = staticmethod(_send_char)

MODELS = 'models'   # тека з SPICE-моделями реальних приладів
def lib(name):
    """Шлях до бібліотеки моделей: lib('diodes') -> models/diodes.lib"""
    return f'{MODELS}/{name}.lib'

try:
    import schemdraw
    import schemdraw.elements as elm
    SCHEMDRAW_AVAILABLE = True
except ImportError:
    SCHEMDRAW_AVAILABLE = False
    print('schemdraw не встановлено (pip install schemdraw)')

plt.rcParams.update({
    'figure.figsize': (8, 4), 'axes.grid': True, 'grid.alpha': 0.3,
    'axes.labelsize': 12, 'axes.titlesize': 13, 'lines.linewidth': 2,
    'font.size': 11,
})

if SCHEMDRAW_AVAILABLE:
    # Умовні позначення за ДСТУ/IEC: резистор — прямокутник, джерело ЕРС — коло зі стрілкою
    from schemdraw.segments import Segment
    from schemdraw.elements.transistors import jfetw, fetl
    elm.style(elm.STYLE_IEC)

    class EMF(elm.Source):
        """Джерело ЕРС: стрілка всередині кола вказує напрямок дії ЕРС."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.segments.append(Segment([(.2, 0), (.8, 0)], arrow='->', arrowwidth=.16, arrowlength=.25))

    class CurrentSource(elm.Source):
        """Джерело струму: подвійна стрілка вказує напрямок струму."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.segments.append(Segment([(.15, 0), (.85, 0)], arrow='->', arrowwidth=.16, arrowlength=.2))
            self.segments.append(Segment([(.15, 0), (.62, 0)], arrow='->', arrowwidth=.16, arrowlength=.2))

    class JFetNch(elm.JFet):
        """Польовий транзистор з p-n переходом і каналом n-типу: стрілка затвора спрямована ДО каналу."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.segments.append(Segment([(jfetw + .3, -fetl - jfetw), (jfetw, -fetl - jfetw)],
                                         arrow='->', arrowwidth=.2, arrowlength=.25))

    class JFetPch(elm.JFet):
        """Польовий транзистор з p-n переходом і каналом p-типу: стрілка затвора спрямована ВІД каналу."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.segments.append(Segment([(jfetw + .05, -fetl - jfetw), (jfetw + .35, -fetl - jfetw)],
                                         arrow='->', arrowwidth=.2, arrowlength=.25))

# Фізичні сталі
q = 1.602176634e-19      # Кл, елементарний заряд
k_B = 1.380649e-23       # Дж/К, стала Больцмана
eps0 = 8.8541878128e-12  # Ф/м, електрична стала
def phi_T(T=300.0):
    """Температурний потенціал kT/q, В"""
    return k_B * T / q
'''
