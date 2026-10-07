#!/usr/bin/env python3
"""Check a suai-report v2.7.2 report after a build.

  python3 check_report.py [REPORT_DIR]

Reads main.tex the way the package does (block commands, code under
\\suaicode, labels and references) and build/main.log of the last build.

  ERRORS    — fix: the build fails or the PDF shows "??" / a blank;
  WARNINGS  — look at each one: usually a real flaw;
  TODO      — places to list for the user;
  SUMMARY   — page count, object counts, PDF name.

Exit code: 0 — no errors, 1 — errors, 2 — nothing to check.
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

PACKAGE_VERSION = (2, 7, 2)
VERSION = ".".join(map(str, PACKAGE_VERSION))

IMG_DIRS = ("images", ".")
IMG_EXT = (
    ".pdf",
    ".ai",
    ".png",
    ".jpg",
    ".jpeg",
    ".jp2",
    ".jpf",
    ".bmp",
    ".ps",
    ".eps",
    ".mps",
)

BLOCK_STOP = {
    "par",
    "begin",
    "end",
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "clearpage",
    "newpage",
    "maketitle",
    "printbibliography",
}
BLOCK_CMDS = {
    "suaitasks",
    "suailist",
    "suaienum",
    "suainum",
    "suaitable",
    "suaieq",
    "suaisources",
}
VERBATIM_ENVS = {"code", "lstlisting", "verbatim", "Verbatim", "minted", "comment"}
MANUAL_ENVS = {
    "figure": "\\suaiimg",
    "tabular": "\\suaitable",
    "tabularx": "\\suaitable",
    "xltabular": "\\suaitable",
    "longtable": "\\suaitable",
    "itemize": "\\suailist",
    "enumerate": "\\suaienum / \\suainum",
    "lstlisting": "\\suaicode",
}
# languages and aliases from suai-report.sty — used when the file is not found
SUAI_LANGS = (
    "javascript",
    "typescript",
    "kotlin",
    "rust",
    "json",
    "yaml",
    "dockerfile",
    "cpp",
    "cs",
    "csharp",
    "js",
    "ts",
    "py",
    "kt",
    "rs",
    "yml",
    "docker",
)
KINDS = {"fig": "figure", "tab": "table", "lst": "listing", "eq": "equation"}
REF_PREFIX = {"figref": "fig", "tabref": "tab", "lstref": "lst", "formref": "eq"}
# listings keys that \suaicode ignores: it always typesets the whole file
FILE_PART_KEYS = ("firstline", "lastline", "linerange")

TOKEN = re.compile(
    r"\\(suaiimg|suaicode|suaitasks|suailist|suaienum|suainum|suaitable|"
    r"suaieq|suaisources|suaititlepage|label|includegraphics|lstinputlisting|begin|"
    r"figref|tabref|lstref|formref|ref|pageref|eqref)(?![A-Za-z@])\*?"
)
RANGE = re.compile(
    r"\\(?:ref|figref|tabref|lstref)\{([^}]*)\}\s*(?:--|---|–|—)\s*"
    r"\\(?:ref|figref|tabref|lstref)\{([^}]*)\}"
)

LOG_WIDTH = 79
FILE_LINE_ERROR = re.compile(r"(?:\./)?([^\s:()]+\.(?:tex|sty|cls|code)):(\d+): (.+)")
OVERFULL = re.compile(
    r"Overfull \\hbox \((\d+(?:\.\d+)?)pt too wide\) "
    r"(?:in \w+ at lines (\d+)|detected at line (\d+))"
)


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
        for title, issues in (
            ("ERRORS", self.errors),
            ("WARNINGS", self.warnings),
            ("TODO", self.todos),
        ):
            unique = sorted(set(issues))
            if unique:
                print(f"{title} ({len(unique)}):")
                for issue in unique:
                    print(issue.render())
                print()
        if not (self.errors or self.warnings or self.todos):
            print("No issues.\n")
        if self.summary:
            print("SUMMARY: " + "; ".join(self.summary))
        return 1 if self.errors else 0


def comment_start(line: str, top_only: bool = False) -> int | None:
    """Position of a real % (not \\%; \\\\% does start a comment). With
    top_only — as in a block row: % inside {} (\\url{a%20b}) stays text."""
    depth = 0
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "%" and not (top_only and depth > 0):
            return i
        i += 1
    return None


def strip_comment(line: str, top_only: bool = False) -> str:
    pos = comment_start(line, top_only)
    return line if pos is None else line[:pos]


def read_group(s: str, pos: int, open_: str) -> tuple[str | None, int]:
    """Argument in {…} or […] at pos, leading spaces skipped. Nested {}
    are honoured: [language={[Sharp]C}] is read whole. Returns
    (content, position after the argument) or (None, pos)."""
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
            return s[i + 1 : j], j + 1
        elif c == "}":
            if depth == 0:
                return None, pos
            depth -= 1
        j += 1
    return None, pos


def split_opts(opts: str | None) -> tuple[list[str], dict[str, str]]:
    """Like \\clist_map_inline in the package: empty items are skipped,
    outer {} are stripped. [bash, backup, firstnumber=3] ->
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
    """Number of | separators, split as the package does: outside {} and
    outside math ($…$, \\(…\\)); \\| and \\$ are commands."""
    n = 0
    depth = 0
    math = False
    i = 0
    while i < len(row):
        c = row[i]
        if c == "\\":
            if row[i + 1 : i + 2] in ("(", ")"):
                math = row[i + 1] == "("
            i += 2
            continue
        if c == "$":
            math = not math
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "|" and depth == 0 and not math:
            n += 1
        i += 1
    return n


def outside_math(text: str) -> str:
    """Row text outside math $…$ and \\(…\\) (\\$ is a plain dollar)."""
    plain = ""
    inside = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            pair = text[i : i + 2]
            if pair in ("\\(", "\\)"):
                inside = pair == "\\("
            elif not inside:
                plain += pair
            i += 2
            continue
        if c == "$":
            inside = not inside
        elif not inside:
            plain += c
        i += 1
    return plain


def indent_width(line: str) -> int | None:
    """Indent width (a tab goes to the next multiple of 4); None if blank."""
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
    """Image name without extension: images/scheme.png and scheme → scheme."""
    p = Path(name)
    return p.stem if p.suffix.lower() in IMG_EXT else p.name


class Languages:
    """The language= values known to the installed listings and to
    suai-report itself (JavaScript, YAML, …, aliases cpp, js, yml). A
    language without a dialect is fine if it is defined without one or has
    a default dialect (C -> [ANSI]C). Anything else (including Lua,
    Assembler, Basic without a dialect) is typeset without highlighting
    and the package logs a warning."""

    def __init__(self) -> None:
        self.plain: set[str] = set()
        self.dialects: set[tuple[str, str]] = set()
        self.default: set[str] = set()
        self.available = self._load_installed()

    def _load_installed(self) -> bool:
        names = ["listings.cfg", "suai-report.sty"] + [
            f"lstlang{i}.sty" for i in (1, 2, 3)
        ]
        try:
            out = subprocess.run(
                ["kpsewhich", *names],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            ).stdout.split()
        except (OSError, subprocess.SubprocessError):
            return False
        if not any(Path(path).name.startswith("lstlang") for path in out):
            return False
        if not any(Path(path).name == "suai-report.sty" for path in out):
            self.plain.update(SUAI_LANGS)
        for path in out:
            try:
                self.add_from(Path(path).read_text(encoding="latin-1"))
            except OSError:
                continue
        return bool(self.plain)

    def add_from(self, tex: str) -> None:
        for m in re.finditer(
            r"\\(?:lst@definelanguage|lstdefinelanguage)\s*"
            r"(?:\[([^\]]*)\])?\s*\{([^}]*)\}",
            tex,
        ):
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
        """None if the language is fine, otherwise the warning text."""
        value = unbrace(value.strip())
        if not value or not self.available or value.lower() == "c#":
            return None
        m = re.fullmatch(r"\[([^\]]*)\]\s*(.+)", value)
        if m:
            dialect, lang = m.group(1).strip().lower(), m.group(2).strip().lower()
            if (lang, dialect) in self.dialects or (not dialect and lang in self.plain):
                return None
            return (
                f"listings has no dialect '{m.group(1)}' of '{m.group(2)}' — "
                "the code will not be highlighted"
            )
        lang = value.lower()
        if lang in self.plain or lang in self.default:
            return None
        known = sorted(d for name, d in self.dialects if name == lang)
        if known:
            return (
                f"listings has '{value}' only with a dialect, otherwise no "
                f"highlighting — language={{[{known[-1]}]{value}}}; "
                f"dialects: {', '.join(known)}"
            )
        return (
            f"unknown listing language '{value}' — the code will not be "
            "highlighted; fix the name or drop it: [label=lst:name]"
        )


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
        self.unknown_langs: set[str] = set()
        self.bad_refs = False

    def block_at(self, n: int) -> tuple[str, int] | None:
        """Block containing line n: (command, line of the command)."""
        for cmd, first, last in self.blocks:
            if first < n <= last:
                return cmd, first
        return None

    def define(self, label: str, n: int, kind: str | None = None) -> None:
        if label in self.labels:
            hint = (
                "; give a repeated image its own label in the 4th argument"
                if label.startswith("fig:")
                else ""
            )
            self.r.error(
                n, f"label {label} is already defined (line {self.labels[label]}){hint}"
            )
            return
        self.labels[label] = n
        if kind:
            self.objects.append(Obj(kind, label, n))

    def block_rows(self, start: int) -> tuple[list[tuple[int, str]], int]:
        """Block rows from index start, read as the package does: up to a
        blank line or a line starting with \\suai…, \\section, \\begin,
        \\end and the like. A comment belongs to its own line; a
        comment-only line is skipped. Returns the rows — (line number,
        text) — and the line number where the block ended."""
        rows = []
        j = start
        total = len(self.lines)
        while j < total:
            raw = self.lines[j]
            if not raw.strip():
                break
            text = strip_comment(raw, top_only=True).strip()
            if text:
                cs = leading_cs(text)
                if cs and (cs in BLOCK_STOP or cs.startswith("suai")):
                    break
                rows.append((j + 1, text))
            j += 1
        return rows, min(j + 1, total)

    def check_block(self, cmd: str, n: int, idx: int, after: str) -> None:
        if after.strip():
            self.r.warn(
                n,
                f"text after \\{cmd} on the same line becomes the first "
                "row of the block — move it to the next line",
            )
        start = idx + 1
        if (
            self.blocks
            and self.blocks[-1][2] == n
            and start < len(self.lines)
            and not self.lines[start].strip()
        ):
            start += 1
        rows, end = self.block_rows(start)
        self.blocks.append((cmd, n, end))
        if cmd == "suaitable":
            self.check_table(n, rows)
        elif cmd == "suaieq":
            for ln, text in rows:
                if top_level_bars(text) == 0:
                    self.r.warn(
                        ln,
                        "row under \\suaieq has no '|' — missing blank "
                        "line after the equation?",
                    )
        elif not rows and cmd != "suaisources":
            self.r.error(
                n, f"no rows under \\{cmd} — the block will be missing from the PDF"
            )

    def check_table(self, n: int, rows: list[tuple[int, str]]) -> None:
        if not rows:
            self.r.error(
                n, "no rows under \\suaitable — the table will be missing from the PDF"
            )
            return
        if len(rows) == 1:
            self.r.warn(n, "the table has only a header row")
        head = top_level_bars(rows[0][1]) + 1
        for ln, text in rows:
            cells = top_level_bars(text) + 1
            if cells != head:
                self.r.warn(
                    ln,
                    f"table row has {cells} cells, the header has {head} — "
                    "a wrapped row or a stray '|'?",
                )
            if "\\|" in outside_math(text):
                self.r.error(
                    ln,
                    "\\| outside math is the math symbol ‖ and the build "
                    "fails with 'Missing $'; a literal | in a cell is \\textbar{}",
                )

    def find_image(self, name: str) -> tuple[bool, str | None]:
        """(found, filename-case hint)."""
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
                    if f.name.lower() == want or (
                        f.stem.lower() == want and f.suffix.lower() in IMG_EXT
                    ):
                        return False, f.name
        return False, None

    def check_img(self, n: int, idx: int, after: str) -> None:
        text = after
        for nxt in self.lines[idx + 1 :]:
            if not nxt.strip():
                break
            text += " " + strip_comment(nxt).strip()
        _, pos = read_group(text, 0, "[")
        name, pos = read_group(text, pos, "{")
        caption, pos = read_group(text, pos, "{")
        own, pos = read_group(text, pos, "[")
        if name is None or caption is None:
            self.r.error(
                n,
                "cannot parse the \\suaiimg arguments: "
                "\\suaiimg[width]{file}{Caption}[label]",
            )
            return
        name = name.strip()
        self.used_images.add(file_stem(name))
        found, case_hint = self.find_image(name)
        if not found:
            hint = (
                f" — the folder has '{case_hint}', check the letter case"
                if case_hint
                else ""
            )
            self.r.error(n, f"image file '{name}' not found in images/{hint}")
        caption = caption.strip()
        if not caption:
            self.r.warn(n, "figure has an empty caption")
        elif caption.endswith("."):
            self.r.warn(n, "figure caption ends with a period — GOST wants none")
        self.define(own.strip() if own else f"fig:{file_stem(name)}", n, "fig")

    def check_lang(self, n: int, lang: str) -> None:
        problem = self.langs.problem(lang)
        if problem:
            self.unknown_langs.add(unbrace(lang.strip()))
            self.r.warn(n, problem)

    def check_code(self, n: int, idx: int, raw: str, start: int) -> int:
        """\\suaicode on line idx from position start (after the command
        name). Returns the index of the line to resume parsing from."""
        line = strip_comment(raw)
        opts, pos = read_group(line, start, "[")
        first, pos = read_group(line, pos, "{")
        if first is None:
            self.r.error(
                n,
                "cannot parse the \\suaicode arguments — the caption "
                "must be on the same line as the command",
            )
            return idx + 1
        positional, keyed = split_opts(opts)
        lang = keyed.get("language", positional[0] if positional else "")
        self.check_lang(n, lang)
        label = keyed.get("label") or (
            f"lst:{positional[1]}" if len(positional) > 1 else None
        )

        second, pos2 = read_group(line, pos, "{")
        if second is not None:
            own, _ = read_group(line, pos2, "[")
            fname = first.strip()
            ignored = [key for key in FILE_PART_KEYS if key in keyed]
            if ignored:
                self.r.warn(
                    n,
                    f"{', '.join(ignored)} ignored by \\suaicode: the whole "
                    "file is typeset; part of a file is \\lstinputlisting"
                    "[language=…, caption={…}, label=lst:…, firstline=…, "
                    "lastline=…]{file}",
                )
            path = next(
                (p for p in (self.d / fname, self.d / "code" / fname) if p.is_file()),
                None,
            )
            if path:
                self.code_files.append(path)
            else:
                self.r.error(
                    n,
                    f"listing file '{fname}' not found (looked next to main.tex "
                    "and in code/)",
                )
            if own:
                label = own.strip()
            elif not label:
                label = f"lst:{Path(fname).stem}"
            self.define(label, n, "lst")
            return idx + 1

        rest = raw[pos:].lstrip()
        if rest and not rest.startswith("%"):
            self.r.error(
                n,
                "nothing may follow the \\suaicode caption on the same "
                "line: the code starts on the next line, indented",
            )
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
            self.r.error(
                n,
                "no indented lines under \\suaicode; code from a file is "
                "\\suaicode[language]{file}{Caption}",
            )
        if label:
            self.define(label, n, "lst")
        else:
            self.r.warn(
                n,
                "listing without a label cannot be referenced: "
                "[language, label] or [label=lst:name]",
            )
        while j > idx + 1 and indent_width(self.lines[j - 1]) is None:
            j -= 1
        return j

    def check_input_listing(self, n: int, idx: int, after: str) -> None:
        """\\lstinputlisting[keys]{file}, the listings command for a part
        of a file; its keys may run over several lines."""
        text = after
        for nxt in self.lines[idx + 1 :]:
            if not nxt.strip():
                break
            text += " " + strip_comment(nxt).strip()
        opts, pos = read_group(text, 0, "[")
        fname, _ = read_group(text, pos, "{")
        if fname is None:
            self.r.error(
                n,
                "cannot parse the \\lstinputlisting arguments: "
                "\\lstinputlisting[keys]{file}",
            )
            return
        _, keyed = split_opts(opts)
        self.check_lang(n, keyed.get("language", ""))
        fname = fname.strip()
        path = self.d / fname
        if path.is_file():
            self.code_files.append(path)
        else:
            self.r.error(
                n,
                f"listing file '{fname}' not found (\\lstinputlisting takes "
                "the path from the report folder and does not look in code/)",
            )
        label = keyed.get("label")
        if label:
            self.define(label, n, "lst")
        elif keyed.get("caption"):
            self.r.warn(
                n, "listing without a label cannot be referenced: label=lst:name"
            )

    def skip_env(self, idx: int, env: str, after: str) -> int:
        """Environment whose body is not scanned for commands."""
        n = idx + 1
        if env in ("code", "lstlisting"):
            opts, _ = read_group(after, 0, "[")
            if env == "code":
                self.r.warn(
                    n,
                    "the code environment is pre-v2.5 syntax; code now goes "
                    "indented under \\suaicode[language, label]{Caption}",
                )
            positional, keyed = split_opts(opts)
            lang = keyed.get(
                "language", positional[0] if env == "code" and positional else ""
            )
            self.check_lang(n, lang)
            label = keyed.get("label") or (
                f"lst:{positional[1]}"
                if env == "code" and len(positional) > 1
                else None
            )
            if label:
                self.define(label, n, "lst")
        end = f"\\end{{{env}}}"
        j = idx + 1
        while j < len(self.lines) and end not in self.lines[j]:
            j += 1
        if j >= len(self.lines):
            self.r.error(n, f"missing \\end{{{env}}}")
        return j + 1

    def run(self) -> None:
        if not any(
            re.search(
                r"\\usepackage(\[[^\]]*\])?\{[^}]*\bsuai-report\b", strip_comment(line)
            )
            for line in self.lines
        ):
            self.r.error(1, "no \\usepackage{suai-report} — not a suai-report document")
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
                cmd, after = m.group(1), line[m.end() :]
                if cmd == "suaicode":
                    next_idx = max(next_idx, self.check_code(n, idx, raw, m.end()))
                    break
                if cmd == "suaiimg":
                    self.check_img(n, idx, after)
                elif cmd == "lstinputlisting":
                    self.check_input_listing(n, idx, after)
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
                            self.r.warn(
                                n,
                                "table without a label cannot be referenced: "
                                "\\suaitable[label]{Title}",
                            )
                    self.check_block(cmd, n, idx, after[pos:])
                elif cmd == "suaititlepage":
                    self.r.error(
                        n, "\\suaititlepage was removed in v2.2 — use \\maketitle"
                    )
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
                        self.r.warn(
                            n,
                            f"manual \\begin{{{env}}} — check whether "
                            f"{MANUAL_ENVS[env.rstrip('*')]} would do",
                        )
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
                self.r.todos.append(
                    Issue(n, text if len(text) <= 100 else text[:99] + "…")
                )
            idx = next_idx
        if not in_doc:
            self.r.error(0, "no \\begin{document}")
        if not self.langs.available and any(o.kind == "lst" for o in self.objects):
            self.r.warn(0, "kpsewhich not found — listing languages were not checked")
        self.check_refs()
        self.check_unused_images()

    def resolve(self, prefix: str | None, key: str) -> str:
        """Like \\suairef: the label as is if it exists, else with the prefix."""
        if prefix is None or key in self.labels:
            return key
        return f"{prefix}:{key}"

    def find_object(self, key: str) -> Obj | None:
        return next(
            (o for o in self.objects if o.label == key or o.label.endswith(":" + key)),
            None,
        )

    def check_refs(self) -> None:
        first_ref: dict[str, int] = {}
        for prefix, key, n in self.refs:
            label = self.resolve(prefix, key)
            if label in self.labels:
                first_ref.setdefault(label, n)
                continue
            close = difflib.get_close_matches(label, list(self.labels), n=1, cutoff=0.8)
            hint = f" — did you mean {close[0]}?" if close else ""
            self.bad_refs = True
            self.r.error(n, f"reference to undefined label {label}{hint}")
        for a, b, n in self.ranges:
            oa, ob = self.find_object(a), self.find_object(b)
            if not (oa and ob and oa.kind == ob.kind):
                continue
            same = [o.label for o in self.objects if o.kind == oa.kind]
            i, k = same.index(oa.label), same.index(ob.label)
            for lab in same[i : k + 1]:
                first_ref[lab] = min(first_ref.get(lab, n), n)
        for o in self.objects:
            if o.kind == "eq":
                continue
            what = KINDS[o.kind]
            if o.label not in first_ref:
                self.r.warn(
                    o.line,
                    f"{what} {o.label} is never referenced in the text "
                    "(GOST requires a reference)",
                )
            elif first_ref[o.label] > o.line:
                self.r.warn(
                    o.line,
                    f"{what} {o.label} comes before its first reference "
                    f"(line {first_ref[o.label]}) — GOST wants it after",
                )

    def check_unused_images(self) -> None:
        img_dir = self.d / "images"
        if not img_dir.is_dir():
            return
        unused = sorted(
            p.name
            for p in img_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in IMG_EXT
            and p.stem not in self.used_images
        )
        if unused:
            self.r.warn(0, f"unused files in images/: {', '.join(unused)}")

    def counts(self) -> str:
        c = Counter(o.kind for o in self.objects)
        return (
            f"figures {c['fig']}, tables {c['tab']}, listings {c['lst']}, "
            f"equations {c['eq']}"
        )


def log_message(lines: list[str], i: int) -> str:
    """Log line i with its continuation if TeX wrapped it."""
    msg = lines[i]
    while len(lines[i]) == LOG_WIDTH and i + 1 < len(lines) and lines[i + 1]:
        i += 1
        msg += lines[i]
    return msg


def flat_log(text: str) -> str:
    """The log with one line per message: for finding phrases that TeX or
    l3msg (the "(suai)" prefix) may have wrapped."""
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
    """Report sources changed since the build. latexmk keeps their MD5 in
    build/main.fdb_latexmk; without it, mtimes are compared with the log."""
    fdb = d / "build" / "main.fdb_latexmk"
    if not fdb.is_file():
        built = log.stat().st_mtime
        return [
            p.relative_to(d).as_posix()
            for p in fallback
            if p.is_file() and p.stat().st_mtime > built
        ]
    changed = set()
    for rel, md5 in re.findall(
        r'^\s+"([^"]+)" \S+ \S+ ([0-9a-f]{32}) ',
        fdb.read_text(encoding="utf-8", errors="replace"),
        re.MULTILINE,
    ):
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
        r.warn(0, "no build/main.log — run suai build first")
        return
    raw = log.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")
    text = flat_log(raw)

    changed = changed_since_build(d, log, [d / "main.tex", *tex.code_files])
    if changed:
        r.warn(
            0,
            f"changed since the build: {', '.join(changed)} — rebuild "
            "(suai build), the log findings are stale",
        )

    ver = re.search(r"^Package: suai-report \S+ v(\d+(?:\.\d+)*)", text, re.MULTILINE)
    if not ver:
        r.warn(0, "suai-report is not in the log — built with a different package?")
    elif tuple(map(int, ver.group(1).split("."))) < PACKAGE_VERSION:
        r.warn(
            0,
            f"built with suai-report v{ver.group(1)}, this check targets "
            f"v{VERSION}; update the package (cd suai-report && git pull && "
            "make install) and rebuild: suai build",
        )

    errs = []
    for i, line in enumerate(lines):
        m = FILE_LINE_ERROR.fullmatch(line)
        if m:
            file, num = m.group(1), m.group(2)
            msg = log_message(lines, i)[m.start(3) :].strip()
            if file != "main.tex":
                errs.append(Issue(0, f"build: {file}:{num}: {msg}"))
                continue
            block = tex.block_at(int(num))
            if block:
                msg += (
                    f" (line {num} ends the \\{block[0]} block from line "
                    f"{block[1]}: the error is in one of its rows)"
                )
            errs.append(Issue(int(num), f"build: {msg}"))
    if not errs:
        for i, line in enumerate(lines):
            if line.startswith("! ") and not line.startswith(
                ("! Emergency stop", "! ==> Fatal")
            ):
                errs.append(Issue(0, f"build: {log_message(lines, i)[2:].strip()}"))
    r.errors.extend(errs)
    failed = bool(errs)

    pages = None if failed else re.search(r"Output written on \S+ \((\d+) pages?", text)
    if not failed and not pages:
        failed = True
        r.error(
            0,
            "the build did not finish (no 'Output written' in the log) — "
            "see the suai build output",
        )

    for i, line in enumerate(lines):
        m = OVERFULL.match(line)
        if not m or float(m.group(1)) <= 3:
            continue
        shown = re.sub(
            r"\\[A-Z0-9]+/\S+ |\[\]|\|", " ", lines[i + 1] if i + 1 < len(lines) else ""
        )
        shown = " ".join(shown.split())
        shown = f"'{shown[:50]}' " if shown else ""
        r.warn(
            int(m.group(2) or m.group(3)),
            f"text {shown}is {float(m.group(1)):.0f}pt too wide — it runs "
            "into the margin or past the cell edge",
        )

    lost = dict.fromkeys(
        f"{c} (U+{u})"
        for c, u in re.findall(
            r"Missing character: There is no (\S+) \(U\+([0-9A-Fa-f]+)\)", text
        )
    )
    if lost:
        r.warn(0, f"the font lacks {', '.join(lost)} — missing from the PDF")

    # the package writes these two log messages in Russian
    for m in re.finditer(
        r"Шрифт\s+'([^']*)'\s+не\s+найден,\s+используется\s+'([^']*)'", text
    ):
        r.warn(
            0,
            f"font {m.group(1)} not found, {m.group(2)} used instead — the "
            "title page may differ from the official form; install "
            "ttf-mscorefonts-installer",
        )

    for lang in dict.fromkeys(re.findall(r"Язык листинга '([^']*)' неизвестен", text)):
        if lang not in tex.unknown_langs:
            r.warn(
                0,
                f"unknown listing language '{lang}' — the code is not "
                "highlighted; fix the name or drop it: [label=lst:name]",
            )

    if (
        not failed
        and not tex.bad_refs
        and ("There were undefined references" in text or "Rerun to get" in text)
    ):
        r.warn(0, "unresolved references in the log — rebuild: suai build")

    vscode = d / ".vscode" / "settings.json"
    if vscode.is_file() and "suai_copy" not in vscode.read_text(
        encoding="utf-8", errors="replace"
    ):
        r.warn(0, ".vscode predates v2.6 — update it: suai update")

    if failed:
        pdf_state = "not updated — the build failed"
    elif not pdf.is_file():
        pdf_state = "missing"
        r.warn(
            0,
            f"no {pdf.name} — the PDF was not copied from build/, rebuild: suai build",
        )
    elif pdf.stat().st_mtime < log.stat().st_mtime - 60:
        pdf_state = "stale"
        r.warn(
            0,
            f"{pdf.name} is older than the log — the PDF was not copied "
            "from build/, rebuild: suai build",
        )
    else:
        pdf_state = pdf.name

    parts = [f"pages {pages.group(1)}"] if pages else []
    parts += [tex.counts(), f"PDF {pdf_state}"]
    if changed:
        parts.append("stale log")
    r.summary = parts


def main() -> int:
    ap = argparse.ArgumentParser(
        description=f"Check a suai-report v{VERSION} report: main.tex and build/main.log."
    )
    ap.add_argument(
        "folder", nargs="?", default=".", help="report folder (with main.tex)"
    )
    args = ap.parse_args()

    d = Path(args.folder).resolve()
    if d.name == "main.tex":
        d = d.parent
    if not (d / "main.tex").is_file():
        print(f"no {d / 'main.tex'}", file=sys.stderr)
        return 2
    r = Report()
    try:
        tex = TexChecker(d, r)
    except UnicodeDecodeError as e:
        print(
            f"main.tex is not UTF-8 ({e.reason}, byte {e.start}) — re-save it as UTF-8",
            file=sys.stderr,
        )
        return 2
    tex.run()
    check_build(d, tex, r)
    return r.show()


if __name__ == "__main__":
    sys.exit(main())
