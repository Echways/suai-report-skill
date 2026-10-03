#!/usr/bin/env python3
"""Проверка отчёта на suai-report v2.6 после сборки.

  python3 check_report.py [ПАПКА_ОТЧЁТА]

Читает main.tex так же, как его читает пакет (блочные команды, код под
\\suaicode, метки и ссылки), и build/main.log последней сборки.

  ОШИБКИ          — исправить: сборка упадёт или в PDF будет «??» / пусто;
  ПРЕДУПРЕЖДЕНИЯ  — посмотреть глазами: чаще всего это правда недочёт;
  TODO            — места, которые надо перечислить пользователю;
  ИТОГ            — страницы, число объектов, имя PDF.

Код выхода: 0 — ошибок нет, 1 — есть ошибки, 2 — проверять нечего.
"""

import argparse
import difflib
import hashlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PACKAGE_VERSION = (2, 6)

IMG_DIRS = ("images", ".")
IMG_EXT = (".pdf", ".ai", ".png", ".jpg", ".jpeg", ".jp2", ".jpf", ".bmp",
           ".ps", ".eps", ".mps")

BLOCK_STOP = {"par", "begin", "end", "section", "subsection", "subsubsection",
              "paragraph", "clearpage", "newpage", "maketitle", "printbibliography"}
BLOCK_CMDS = {"suaitasks", "suailist", "suaienum", "suainum", "suaitable",
              "suaieq", "suaisources"}
VERBATIM_ENVS = {"code", "lstlisting", "verbatim", "Verbatim", "minted", "comment"}
MANUAL_ENVS = {
    "figure": "\\suaiimg", "tabular": "\\suaitable", "tabularx": "\\suaitable",
    "xltabular": "\\suaitable", "longtable": "\\suaitable",
    "itemize": "\\suailist", "enumerate": "\\suaienum / \\suainum",
    "lstlisting": "\\suaicode",
}
KINDS = {"fig": "рисунок", "tab": "таблица", "lst": "листинг", "eq": "формула"}
REF_PREFIX = {"figref": "fig", "tabref": "tab", "lstref": "lst", "formref": "eq"}

TOKEN = re.compile(
    r"\\(suaiimg|suaicode|suaitasks|suailist|suaienum|suainum|suaitable|"
    r"suaieq|suaisources|suaititlepage|label|includegraphics|begin|"
    r"figref|tabref|lstref|formref|ref|pageref|eqref)(?![A-Za-z@])\*?")
RANGE = re.compile(r"\\(?:ref|figref|tabref|lstref)\{([^}]*)\}\s*(?:--|---|–|—)\s*"
                   r"\\(?:ref|figref|tabref|lstref)\{([^}]*)\}")

LOG_WIDTH = 79
FILE_LINE_ERROR = re.compile(r"(?:\./)?([^\s:()]+\.(?:tex|sty|cls|code)):(\d+): (.+)")
OVERFULL = re.compile(r"Overfull \\hbox \((\d+(?:\.\d+)?)pt too wide\) "
                      r"(?:in \w+ at lines (\d+)|detected at line (\d+))")


@dataclass(order=True, frozen=True)
class Issue:
    line: int
    text: str

    def render(self) -> str:
        if not self.line:
            return f"  {self.text}"
        where = f"main.tex:{self.line}"
        return f"  {where:<13}{self.text}"


class Report:
    def __init__(self) -> None:
        self.errors: list[Issue] = []
        self.warnings: list[Issue] = []
        self.todos: list[Issue] = []
        self.summary: list[str] = []

    def error(self, line: int, text: str) -> None:
        self.errors.append(Issue(line, text))

    def warn(self, line: int, text: str) -> None:
        self.warnings.append(Issue(line, text))

    def show(self) -> int:
        for title, issues in (("ОШИБКИ", self.errors),
                              ("ПРЕДУПРЕЖДЕНИЯ", self.warnings),
                              ("TODO", self.todos)):
            unique = sorted(set(issues))
            if unique:
                print(f"{title} ({len(unique)}):")
                for issue in unique:
                    print(issue.render())
                print()
        if not (self.errors or self.warnings or self.todos):
            print("Замечаний нет.\n")
        if self.summary:
            print("ИТОГ: " + "; ".join(self.summary))
        return 1 if self.errors else 0


def comment_start(line: str) -> int | None:
    """Позиция настоящего % (не \\%; \\\\% — уже комментарий)."""
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\":
            i += 2
            continue
        if c == "%":
            return i
        i += 1
    return None


def strip_comment(line: str) -> str:
    pos = comment_start(line)
    return line if pos is None else line[:pos]


def read_group(s: str, pos: int, open_: str) -> tuple[str | None, int]:
    """Аргумент в {…} или […] с позиции pos, пробелы перед ним пропускаются.
    Вложенные {} учитываются: [language={[Sharp]C}] читается целиком.
    Возвращает (содержимое, позиция за аргументом) или (None, pos)."""
    close = "}" if open_ == "{" else "]"
    i = pos
    while i < len(s) and s[i] in " \t":
        i += 1
    if i >= len(s) or s[i] != open_:
        return None, pos
    depth = 0
    j = i + 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == close and depth == 0:
            return s[i + 1:j], j + 1
        elif c == "}":
            if depth == 0:
                return None, pos
            depth -= 1
        j += 1
    return None, pos


def split_opts(opts: str | None) -> tuple[list[str], dict[str, str]]:
    """Как \\clist_map_inline в пакете: пустые элементы пропускаются,
    внешние {} снимаются. [bash, backup, firstnumber=3] ->
    (['bash', 'backup'], {'firstnumber': '3'})."""
    parts = []
    depth = 0
    cur = ""
    for c in opts or "":
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += c
    parts.append(cur)
    positional = []
    keyed = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            keyed[key.strip()] = unbrace(value.strip())
        else:
            positional.append(unbrace(part))
    return positional, keyed


def unbrace(s: str) -> str:
    return s[1:-1].strip() if s.startswith("{") and s.endswith("}") else s


def top_level_bars(row: str) -> int:
    """Число разделителей | вне {} и не \\| — так режет \\seq_set_split."""
    n = 0
    depth = 0
    i = 0
    while i < len(row):
        c = row[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "|" and depth == 0:
            n += 1
        i += 1
    return n


def split_math(text: str) -> tuple[list[str], str]:
    """Формулы $…$ строки (\\$ — просто доллар) и текст вне них."""
    math = []
    plain = ""
    cur = ""
    inside = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            cur += text[i:i + 2]
            i += 2
            continue
        if c == "$":
            if inside:
                math.append(f"${cur}$")
            else:
                plain += cur
            cur = ""
            inside = not inside
        else:
            cur += c
        i += 1
    plain += f"${cur}" if inside else cur
    return math, plain


def indent_width(line: str) -> int | None:
    """Ширина отступа (табуляция — до колонки, кратной 4), None — пустая."""
    col = 0
    for c in line:
        if c == " ":
            col += 1
        elif c == "\t":
            col += 4 - col % 4
        else:
            return col
    return None


def leading_cs(text: str) -> str | None:
    m = re.match(r"\\([A-Za-z@]+)", text)
    return m.group(1) if m else None


def file_stem(name: str) -> str:
    """Имя рисунка без расширения: images/scheme.png и scheme — это scheme."""
    p = Path(name)
    return p.stem if p.suffix.lower() in IMG_EXT else p.name


class Languages:
    """Какие language= принимает установленный listings. Язык без диалекта
    подходит, если он определён без диалекта или у него есть диалект по
    умолчанию (C -> [ANSI]C); Lua, Assembler, Basic без диалекта роняют
    сборку."""

    def __init__(self) -> None:
        self.plain: set[str] = set()
        self.dialects: set[tuple[str, str]] = set()
        self.default: set[str] = set()
        self.available = self._load_installed()

    def _load_installed(self) -> bool:
        names = ["listings.cfg"] + [f"lstlang{i}.sty" for i in (1, 2, 3)]
        try:
            out = subprocess.run(["kpsewhich", *names], capture_output=True,
                                 text=True, timeout=10).stdout.split()
        except (OSError, subprocess.SubprocessError):
            return False
        if len(out) < 2:
            return False
        for path in out:
            try:
                self.add_from(Path(path).read_text(encoding="latin-1"))
            except OSError:
                continue
        return bool(self.plain)

    def add_from(self, tex: str) -> None:
        for m in re.finditer(r"\\(?:lst@definelanguage|lstdefinelanguage)\s*"
                             r"(?:\[([^\]]*)\])?\s*\{([^}]*)\}", tex):
            self._add(m.group(2), m.group(1))
        for m in re.finditer(r"\\lstalias\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", tex):
            self._add(m.group(2), m.group(1))
        for m in re.finditer(r"defaultdialect\s*=\s*\[[^\]]*\]\s*([^,}\s]+)", tex):
            self.default.add(m.group(1).lower())

    def _add(self, lang: str, dialect: str | None) -> None:
        lang = lang.strip().lower()
        dialect = (dialect or "").strip().lower()
        if dialect:
            self.dialects.add((lang, dialect))
        else:
            self.plain.add(lang)

    def problem(self, value: str) -> str | None:
        """None — язык подходит, иначе текст ошибки."""
        value = unbrace(value.strip())
        if not value or not self.available:
            return None
        m = re.fullmatch(r"\[([^\]]*)\]\s*(.+)", value)
        if m:
            dialect, lang = m.group(1).strip().lower(), m.group(2).strip().lower()
            if (lang, dialect) in self.dialects or (not dialect and lang in self.plain):
                return None
            return (f"у языка «{m.group(2)}» в listings нет диалекта «{m.group(1)}» — "
                    "сборка упадёт")
        lang = value.lower()
        if lang in self.plain or lang in self.default:
            return None
        known = sorted(d for name, d in self.dialects if name == lang)
        if known:
            return (f"«{value}» в listings есть только с диалектом — "
                    f"language={{[{known[-1]}]{value}}}; варианты: {', '.join(known)}")
        return (f"язык листинга «{value}» не знаком listings — сборка упадёт; "
                "без языка: [label=lst:имя]")


@dataclass
class Obj:
    kind: str
    label: str
    line: int


class TexChecker:
    def __init__(self, folder: Path, report: Report) -> None:
        self.d = folder
        self.r = report
        self.lines = (folder / "main.tex").read_text(encoding="utf-8").splitlines()
        self.langs = Languages()
        self.langs.add_from("\n".join(self.lines))
        self.labels: dict[str, int] = {}
        self.objects: list[Obj] = []
        self.refs: list[tuple[str | None, str, int]] = []
        self.ranges: list[tuple[str, str, int]] = []
        self.used_images: set[str] = set()
        self.code_files: list[Path] = []
        self.blocks: list[tuple[str, int, int]] = []

    def block_at(self, n: int) -> tuple[str, int] | None:
        """Блок, в который попадает строка n: (команда, строка команды)."""
        for cmd, first, last in self.blocks:
            if first < n <= last:
                return cmd, first
        return None

    def define(self, label: str, n: int, kind: str | None = None) -> None:
        if label in self.labels:
            hint = ("; у повторной картинки — 4-й аргумент [своя-метка]"
                    if label.startswith("fig:") else "")
            self.r.error(n, f"метка {label} уже есть (строка {self.labels[label]}){hint}")
            return
        self.labels[label] = n
        if kind:
            self.objects.append(Obj(kind, label, n))

    def block_rows(self, start: int) -> tuple[list[tuple[int, str, bool]], int, str | None]:
        """Строки блока с индекса start — как их читает пакет: до пустой
        строки или строки, начинающейся с \\suai…, \\section, \\begin и т. п.
        % съедает и перевод строки: строка из одного комментария не видна,
        а строка «текст % …» склеивается со следующей (и пустая строка
        после неё блок уже не закрывает). Возвращает строки — (номер строки,
        текст, был ли % после текста), — номер строки, на которой блок
        кончился, и команду, которая его закрыла (None — не команда)."""
        rows = []
        stop = None
        j = start
        total = len(self.lines)
        while j < total:
            first = j
            text = ""
            commented = False
            while j < total:
                raw = self.lines[j]
                pos = comment_start(raw)
                body = (raw if pos is None else raw[:pos]).strip()
                if body:
                    if not text:
                        first = j
                    text = f"{text} {body}" if text else body
                    commented = commented or pos is not None
                j += 1
                if pos is None:
                    break
            if not text:
                break
            cs = leading_cs(text)
            if cs and (cs in BLOCK_STOP or cs.startswith("suai")):
                j = first + 1
                stop = cs
                break
            rows.append((first + 1, text, commented and j < total))
        return rows, j, stop

    def check_block(self, cmd: str, n: int, idx: int, after: str) -> None:
        if after.strip():
            self.r.warn(n, f"текст после \\{cmd} на той же строке станет первой "
                           "строкой блока — перенеси его на строку ниже")
        start = idx + 1
        if (self.blocks and self.blocks[-1][2] == n and start < len(self.lines)
                and not self.lines[start].strip()):
            start += 1
        rows, end, stop = self.block_rows(start)
        self.blocks.append((cmd, n, end))
        if stop == "end":
            self.r.error(end, f"блок \\{cmd} со строки {n} упирается в "
                              "\\end{…} — нужна пустая строка перед ним, "
                              "иначе сборка падает")
        for ln, _, commented in rows:
            if commented:
                self.r.error(ln, f"% в строке блока \\{cmd} съедает перевод строки: "
                                 "следующая строка приклеится к этой, пустая строка "
                                 "не закроет блок — убери комментарий или пиши \\%")
        if cmd == "suaitable":
            self.check_table(n, rows)
        elif cmd == "suaieq":
            for ln, text, _ in rows:
                if top_level_bars(text) == 0:
                    self.r.warn(ln, "строка под \\suaieq без «|» — забыта пустая "
                                    "строка после формулы?")
        elif not rows and cmd != "suaisources":
            self.r.error(n, f"под \\{cmd} нет строк — блок пропадёт из PDF")

    def check_table(self, n: int, rows: list[tuple[int, str, bool]]) -> None:
        if not rows:
            self.r.error(n, "под \\suaitable нет строк — таблица пропадёт из PDF")
            return
        if len(rows) == 1:
            self.r.warn(n, "в таблице только шапка")
        head = top_level_bars(rows[0][1]) + 1
        for ln, text, _ in rows:
            cells = top_level_bars(text) + 1
            if cells != head:
                self.r.warn(ln, f"в строке таблицы {cells} ячеек, в шапке {head} — "
                                "перенесённая строка или лишний «|»?")
            math, plain = split_math(text)
            for f in math:
                if "|" in f.replace("\\|", ""):
                    self.r.warn(ln, f"«|» внутри формулы {f} делит ячейку — "
                                    "\\lvert, \\rvert, \\mid или \\textbar{}")
                if re.search(r"\s", f):
                    self.r.error(ln, f"формула с пробелами в ячейке {f} роняет сборку "
                                     "(«Missing $») — пиши без пробелов, после "
                                     "команды {}: $a+b$, $\\lvert{}x\\rvert$")
            if "\\|" in plain:
                self.r.error(ln, "\\| вне формулы — это математическая ‖, сборка "
                                 "упадёт с «Missing $»; символ | в ячейке — \\textbar{}")

    def find_image(self, name: str) -> tuple[bool, str | None]:
        """(найден, подсказка про регистр)."""
        for base in IMG_DIRS:
            p = self.d / base / name
            cands = [p] if p.suffix.lower() in IMG_EXT else []
            cands += [p.with_name(p.name + e) for e in IMG_EXT]
            cands += [p.with_name(p.name + e.upper()) for e in IMG_EXT]
            if any(c.is_file() for c in cands):
                return True, None
        for base in IMG_DIRS:
            folder = (self.d / base / name).parent
            if folder.is_dir():
                want = Path(name).name.lower()
                for f in folder.iterdir():
                    if f.name.lower() == want or (f.stem.lower() == want and
                                                  f.suffix.lower() in IMG_EXT):
                        return False, f.name
        return False, None

    def check_img(self, n: int, idx: int, after: str) -> None:
        text = after
        for nxt in self.lines[idx + 1:]:
            if not nxt.strip():
                break
            text += " " + strip_comment(nxt).strip()
        _, pos = read_group(text, 0, "[")
        name, pos = read_group(text, pos, "{")
        caption, pos = read_group(text, pos, "{")
        own, pos = read_group(text, pos, "[")
        if name is None or caption is None:
            self.r.error(n, "у \\suaiimg не прочитались аргументы: "
                            "\\suaiimg[ширина]{файл}{Подпись}[метка]")
            return
        name = name.strip()
        self.used_images.add(file_stem(name))
        found, case_hint = self.find_image(name)
        if not found:
            hint = f" — в папке есть «{case_hint}», проверь регистр" if case_hint else ""
            self.r.error(n, f"нет файла рисунка «{name}» в images/{hint}")
        caption = caption.strip()
        if not caption:
            self.r.warn(n, "у рисунка пустая подпись")
        elif caption.endswith("."):
            self.r.warn(n, "подпись рисунка с точкой в конце — по ГОСТу без точки")
        self.define(own.strip() if own else f"fig:{file_stem(name)}", n, "fig")

    def check_code(self, n: int, idx: int, raw: str, start: int) -> int:
        """\\suaicode на строке idx с позиции start (за именем команды).
        Возвращает индекс строки, с которой продолжать разбор."""
        line = strip_comment(raw)
        opts, pos = read_group(line, start, "[")
        first, pos = read_group(line, pos, "{")
        if first is None:
            self.r.error(n, "у \\suaicode не прочитались аргументы — подпись "
                            "должна быть на одной строке с командой")
            return idx + 1
        positional, keyed = split_opts(opts)
        lang = keyed.get("language", positional[0] if positional else "")
        problem = self.langs.problem(lang)
        if problem:
            self.r.error(n, problem)
        label = keyed.get("label") or (f"lst:{positional[1]}" if len(positional) > 1 else None)

        second, pos2 = read_group(line, pos, "{")
        if second is not None:
            own, _ = read_group(line, pos2, "[")
            fname = first.strip()
            path = next((p for p in (self.d / fname, self.d / "code" / fname)
                         if p.is_file()), None)
            if path:
                self.code_files.append(path)
            else:
                self.r.error(n, f"нет файла листинга «{fname}» (искал рядом с "
                                "main.tex и в code/)")
            if own:
                label = own.strip()
            elif not label:
                label = f"lst:{Path(fname).stem}"
            self.define(label, n, "lst")
            return idx + 1

        rest = raw[pos:].lstrip()
        if rest and not rest.startswith("%"):
            self.r.error(n, "после подписи \\suaicode на той же строке ничего не "
                            "пишется: код — со следующей строки, с отступом")
        j = idx + 1
        code = 0
        while j < len(self.lines):
            w = indent_width(self.lines[j])
            if w is None:
                j += 1
                continue
            if w == 0:
                break
            code += 1
            j += 1
        if not code:
            self.r.error(n, "под \\suaicode нет строк с отступом; код из файла — "
                            "\\suaicode[язык]{файл}{Подпись}")
        if label:
            self.define(label, n, "lst")
        else:
            self.r.warn(n, "листинг без метки — на него не сослаться: "
                           "[язык, метка] или [label=lst:имя]")
        while j > idx + 1 and indent_width(self.lines[j - 1]) is None:
            j -= 1
        return j

    def skip_env(self, idx: int, env: str, after: str) -> int:
        """Окружение, внутри которого команды не ищутся."""
        n = idx + 1
        if env in ("code", "lstlisting"):
            opts, pos = read_group(after, 0, "[")
            if env == "code":
                self.r.warn(n, "окружение code — синтаксис до v2.5; в 2.6 код "
                               "пишется под \\suaicode[язык, метка]{Подпись} с отступом")
            positional, keyed = split_opts(opts)
            lang = keyed.get("language", positional[0] if env == "code" and positional else "")
            problem = self.langs.problem(lang)
            if problem:
                self.r.error(n, problem)
            label = keyed.get("label") or (
                f"lst:{positional[1]}" if env == "code" and len(positional) > 1 else None)
            if label:
                self.define(label, n, "lst")
        end = f"\\end{{{env}}}"
        j = idx + 1
        while j < len(self.lines) and end not in self.lines[j]:
            j += 1
        if j >= len(self.lines):
            self.r.error(n, f"нет \\end{{{env}}}")
        return j + 1

    def run(self) -> None:
        if not any(re.search(r"\\usepackage(\[[^\]]*\])?\{[^}]*\bsuai-report\b",
                             strip_comment(line)) for line in self.lines):
            self.r.error(1, "нет \\usepackage{suai-report} — это не отчёт на suai-report")
        in_doc = False
        idx = 0
        while idx < len(self.lines):
            raw = self.lines[idx]
            line = strip_comment(raw)
            n = idx + 1
            if "\\begin{document}" in line:
                in_doc = True
            next_idx = idx + 1
            for m in TOKEN.finditer(line):
                cmd, after = m.group(1), line[m.end():]
                if cmd == "suaicode":
                    next_idx = max(next_idx, self.check_code(n, idx, raw, m.end()))
                    break
                if cmd == "suaiimg":
                    self.check_img(n, idx, after)
                elif cmd == "includegraphics":
                    _, pos = read_group(after, 0, "[")
                    name, _ = read_group(after, pos, "{")
                    if name:
                        self.used_images.add(file_stem(name.strip()))
                elif cmd in BLOCK_CMDS:
                    opt, pos = read_group(after, 0, "[")
                    if cmd in ("suaitable", "suaieq"):
                        _, pos = read_group(after, pos, "{")
                        if opt and opt.strip():
                            kind = "tab" if cmd == "suaitable" else "eq"
                            self.define(f"{kind}:{opt.strip()}", n, kind)
                        elif cmd == "suaitable":
                            self.r.warn(n, "таблица без метки — на неё не сослаться: "
                                           "\\suaitable[метка]{Название}")
                    self.check_block(cmd, n, idx, after[pos:])
                elif cmd == "suaititlepage":
                    self.r.error(n, "\\suaititlepage убран в v2.2 — \\maketitle")
                elif cmd == "label":
                    lab, _ = read_group(after, 0, "{")
                    if lab:
                        lab = lab.strip()
                        kind = lab.split(":")[0] if ":" in lab else None
                        self.define(lab, n, kind if kind in KINDS else None)
                elif cmd == "begin":
                    env, pos = read_group(after, 0, "{")
                    env = (env or "").strip()
                    if in_doc and env.rstrip("*") in MANUAL_ENVS:
                        self.r.warn(n, f"\\begin{{{env}}} руками — проверь, не нужна "
                                       f"ли {MANUAL_ENVS[env.rstrip('*')]}")
                    if env in VERBATIM_ENVS:
                        next_idx = max(next_idx, self.skip_env(idx, env, after[pos:]))
                        break
                elif in_doc:
                    key, _ = read_group(after, 0, "{")
                    if key is not None:
                        self.refs.append((REF_PREFIX.get(cmd), key.strip(), n))
            if in_doc:
                for m in RANGE.finditer(line):
                    self.ranges.append((m.group(1).strip(), m.group(2).strip(), n))
            if "TODO" in raw:
                text = " ".join(raw.split())
                self.r.todos.append(Issue(n, text if len(text) <= 100 else text[:99] + "…"))
            idx = next_idx
        if not in_doc:
            self.r.error(0, "нет \\begin{document}")
        if not self.langs.available and any(o.kind == "lst" for o in self.objects):
            self.r.warn(0, "kpsewhich не найден — языки листингов не проверены")
        self.check_refs()
        self.check_unused_images()

    def resolve(self, prefix: str | None, key: str) -> str:
        """Как \\suairef: метка как есть, если такая есть, иначе с префиксом."""
        if prefix is None or key in self.labels:
            return key
        return f"{prefix}:{key}"

    def find_object(self, key: str) -> Obj | None:
        return next((o for o in self.objects
                     if o.label == key or o.label.endswith(":" + key)), None)

    def check_refs(self) -> None:
        first_ref: dict[str, int] = {}
        for prefix, key, n in self.refs:
            label = self.resolve(prefix, key)
            if label in self.labels:
                first_ref.setdefault(label, n)
                continue
            close = difflib.get_close_matches(label, list(self.labels), n=1, cutoff=0.8)
            hint = f" — может, {close[0]}?" if close else ""
            self.r.error(n, f"ссылка на несуществующую метку {label}{hint}")
        for a, b, n in self.ranges:
            oa, ob = self.find_object(a), self.find_object(b)
            if not (oa and ob and oa.kind == ob.kind):
                continue
            same = [o.label for o in self.objects if o.kind == oa.kind]
            i, k = same.index(oa.label), same.index(ob.label)
            for lab in same[i:k + 1]:
                first_ref[lab] = min(first_ref.get(lab, n), n)
        for o in self.objects:
            if o.kind == "eq":
                continue
            what = KINDS[o.kind]
            if o.label not in first_ref:
                self.r.warn(o.line, f"{what} {o.label} без ссылки в тексте "
                                    "(по ГОСТу ссылка нужна)")
            elif first_ref[o.label] > o.line:
                self.r.warn(o.line, f"{what} {o.label} стоит раньше первой ссылки "
                                    f"(строка {first_ref[o.label]}) — по ГОСТу после")

    def check_unused_images(self) -> None:
        img_dir = self.d / "images"
        if not img_dir.is_dir():
            return
        unused = sorted(p.name for p in img_dir.iterdir()
                        if p.is_file() and p.suffix.lower() in IMG_EXT
                        and p.stem not in self.used_images)
        if unused:
            self.r.warn(0, f"в images/ не вставлены: {', '.join(unused)}")

    def counts(self) -> str:
        c = Counter(o.kind for o in self.objects)
        return (f"рисунков {c['fig']}, таблиц {c['tab']}, листингов {c['lst']}, "
                f"формул {c['eq']}")


def log_message(lines: list[str], i: int) -> str:
    """Строка i лога вместе с продолжением, если TeX её перенёс."""
    msg = lines[i]
    while len(lines[i]) == LOG_WIDTH and i + 1 < len(lines) and lines[i + 1]:
        i += 1
        msg += lines[i]
    return msg


def flat_log(text: str) -> str:
    """Лог одной строкой на сообщение: для поиска фраз, которые TeX или
    l3msg (префикс «(suai)») могли перенести."""
    out: list[str] = []
    prev = 0
    for line in text.split("\n"):
        if out and prev == LOG_WIDTH:
            out[-1] += line
        else:
            out.append(line)
        prev = len(line)
    return re.sub(r"\n\([\w-]+\)\s+", " ", "\n".join(out))


def changed_since_build(d: Path, log: Path, fallback: list[Path]) -> list[str]:
    """Исходники отчёта, изменённые после сборки. latexmk хранит их MD5 в
    build/main.fdb_latexmk; без него сравниваем время с логом."""
    fdb = d / "build" / "main.fdb_latexmk"
    if not fdb.is_file():
        built = log.stat().st_mtime
        return [p.relative_to(d).as_posix() for p in fallback
                if p.is_file() and p.stat().st_mtime > built]
    changed = set()
    for rel, md5 in re.findall(r'^\s+"([^"]+)" \S+ \S+ ([0-9a-f]{32}) ',
                               fdb.read_text(encoding="utf-8", errors="replace"), re.M):
        if rel.startswith(("/", "build/")) or ":" in rel:
            continue
        p = d / rel
        if not p.is_file() or hashlib.md5(p.read_bytes()).hexdigest() != md5:
            changed.add(rel)
    return sorted(changed)


def check_build(d: Path, tex: TexChecker, r: Report) -> None:
    log = d / "build" / "main.log"
    pdf = d / f"{d.parent.name}-{d.name}.pdf"
    if not log.is_file():
        r.warn(0, "нет build/main.log — сначала suai build")
        return
    raw = log.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")
    text = flat_log(raw)

    changed = changed_since_build(d, log, [d / "main.tex", *tex.code_files])
    if changed:
        r.warn(0, f"после сборки изменились: {', '.join(changed)} — пересобери "
                  "(suai build), иначе замечания по логу устарели")

    ver = re.search(r"^Package: suai-report \S+ v(\d+)\.(\d+)", text, re.M)
    if not ver:
        r.warn(0, "в логе нет suai-report — собрано не тем пакетом?")
    elif (int(ver.group(1)), int(ver.group(2))) < PACKAGE_VERSION:
        r.warn(0, f"собрано на suai-report v{ver.group(1)}.{ver.group(2)}, проверка — "
                  "для v2.6; обнови пакет: cd suai-report && git pull && make install")

    errs = []
    for i, line in enumerate(lines):
        m = FILE_LINE_ERROR.fullmatch(line)
        if m:
            file, num = m.group(1), m.group(2)
            msg = log_message(lines, i)[m.start(3):].strip()
            if file != "main.tex":
                errs.append(Issue(0, f"сборка: {file}:{num}: {msg}"))
                continue
            block = tex.block_at(int(num))
            if block:
                msg += (f" (строка {num} — конец блока \\{block[0]} со строки "
                        f"{block[1]}: ошибка в одной из его строк)")
            errs.append(Issue(int(num), f"сборка: {msg}"))
    if not errs:
        for i, line in enumerate(lines):
            if line.startswith("! ") and not line.startswith(("! Emergency stop",
                                                              "! ==> Fatal")):
                errs.append(Issue(0, f"сборка: {log_message(lines, i)[2:].strip()}"))
    r.errors.extend(errs)
    failed = bool(errs)

    pages = None if failed else re.search(r"Output written on \S+ \((\d+) pages?", text)
    if not failed and not pages:
        failed = True
        r.error(0, "сборка не дошла до конца (в логе нет «Output written») — "
                   "смотри вывод suai build")

    for i, line in enumerate(lines):
        m = OVERFULL.match(line)
        if not m or float(m.group(1)) <= 3:
            continue
        shown = re.sub(r"\\[A-Z0-9]+/\S+ |\[\]|\|", " ", lines[i + 1] if i + 1 < len(lines) else "")
        shown = " ".join(shown.split())
        shown = f"«{shown[:50]}» " if shown else ""
        r.warn(int(m.group(2) or m.group(3)), f"текст {shown}шире места на "
                                              f"{float(m.group(1)):.0f}pt — вылезает на "
                                              "поле или за край ячейки")

    lost = dict.fromkeys(f"{c} (U+{u})" for c, u in re.findall(
        r"Missing character: There is no (\S+) \(U\+([0-9A-Fa-f]+)\)", text))
    if lost:
        r.warn(0, f"в шрифте нет символов {', '.join(lost)} — в PDF их не будет")

    for m in re.finditer(r"Шрифт\s+'([^']*)'\s+не\s+найден,\s+используется\s+'([^']*)'", text):
        r.warn(0, f"шрифт {m.group(1)} не найден, взят {m.group(2)} — титул может "
                  "отличаться от бланка; нужен ttf-mscorefonts-installer")

    has_ref_errors = any("несуществующую метку" in e.text for e in r.errors)
    if not failed and not has_ref_errors and (
            "There were undefined references" in text or "Rerun to get" in text):
        r.warn(0, "в логе неразрешённые ссылки — пересобери: suai build")

    vscode = d / ".vscode" / "settings.json"
    if vscode.is_file() and "suai_copy" not in vscode.read_text(encoding="utf-8",
                                                                errors="replace"):
        r.warn(0, ".vscode от версии до 2.6 — обнови: suai update")

    if failed:
        pdf_state = "не обновлён — сборка упала"
    elif not pdf.is_file():
        pdf_state = "нет"
        r.warn(0, f"нет {pdf.name} — PDF не скопировался из build/, пересобери: suai build")
    elif pdf.stat().st_mtime < log.stat().st_mtime - 60:
        pdf_state = "старый"
        r.warn(0, f"{pdf.name} старше лога — PDF не скопировался из build/, "
                  "пересобери: suai build")
    else:
        pdf_state = pdf.name

    parts = [f"страниц {pages.group(1)}"] if pages else []
    parts += [tex.counts(), f"PDF {pdf_state}"]
    if changed:
        parts.append("лог устарел")
    r.summary = parts


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Проверка отчёта на suai-report v2.6: main.tex и build/main.log.")
    ap.add_argument("folder", nargs="?", default=".", help="папка отчёта (с main.tex)")
    args = ap.parse_args()

    d = Path(args.folder).resolve()
    if d.name == "main.tex":
        d = d.parent
    if not (d / "main.tex").is_file():
        print(f"нет {d / 'main.tex'}", file=sys.stderr)
        return 2
    r = Report()
    try:
        tex = TexChecker(d, r)
    except UnicodeDecodeError as e:
        print(f"main.tex не в UTF-8 ({e.reason}, байт {e.start}) — пересохрани в UTF-8",
              file=sys.stderr)
        return 2
    tex.run()
    check_build(d, tex, r)
    return r.show()


if __name__ == "__main__":
    sys.exit(main())
