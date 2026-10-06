---
name: suai-report
description: 'Use when writing, editing, converting or building a GUAP (ГУАП, СПбГУАП, SUAI) university report in LaTeX with the suai-report package — lab, practical or course-work reports formatted to GOST 7.32-2017. Triggers: a request for an отчёт по лабе / лабораторной / практике / курсовой, even when the package is not named («сделай отчёт по лабе 5, методичка в папке», «оформи по ГОСТу», «добавь таблицу в отчёт»); a folder with a методичка (assignment handout) and screenshots, or a main.tex with \usepackage{suai-report} and \suaitable, \suaiimg, \suaicode, \suaisetup; moving a report from Word or Markdown to suai-report; running the suai command or fixing its build error.'
---

# GUAP reports with suai-report

suai-report is a XeLaTeX package (`suai-report.sty`) plus the `suai`
command. The package applies all GOST 7.32-2017 formatting itself: the GUAP
title page, margins, font, headings, captions, numbering. `main.tex` holds
only text and short `\suai…` block commands, so nearly all the work is
content: understand the assignment, read the screenshots, describe honestly
and clearly what was done.

**Language.** The report is written in Russian, whatever language these
instructions or the conversation use. Russian text in the examples is
literal target text. Talk to the user in their language.

## Workflow

### 1. Look around

- Find the report folder, usually `Subject/lab-N/`; the PDF is named after
  both folders: `Subject-lab-N.pdf`.
- See what is in it: the assignment handout (методичка, PDF/DOCX),
  `images/` with screenshots, `code/` or sources, data (xlsx, csv), a
  `main.tex` already started.
- Read the `main.tex` of a neighbouring report (usually the previous lab of
  the same course), but **only if it is on suai-report v2.6 or newer** —
  `build/main.log` says `Package: suai-report … v2.6` / `v2.7.1`, or
  `.vscode/settings.json` contains `suai_copy`. Such a report is the best
  model: it shows how the user writes the introduction, captions,
  conclusion and sources, and what goes on the title page. Match that
  style, not your own.
- Do not model on pre-2.6 reports: their syntax is obsolete
  (`\begin{code}`, manual `tabular`, `\allowbreak` in cells). With no 2.6+
  report nearby, follow this skill. Do not carry over v2.6 workarounds
  (formulas in cells without spaces, YAML and JSON listings without a
  language): 2.7 does not need them.

### 2. Create the report if there is no `main.tex`

```bash
cd Subject/lab-4 && suai next --no-open          # creates ../lab-5 with the lab-4 title page
suai new Subject/lab-5 --title "Название работы" --no-open
```

`suai new` takes the title page from the newest neighbouring report and the
number from the folder name (`lab-5` → 5), sets `date = today`, creates
`images/`, `.vscode/`, `.gitignore`. An existing folder with materials is
fine: nothing is touched (it fails only if `main.tex` exists). `--no-open`
keeps VS Code closed; drop it if the user wants the live preview.

If there is no `suai` command, check the package: `kpsewhich
suai-report.sty`. Without the package nothing builds — tell the user to run
`git clone https://github.com/Echways/suai-report && make install`. With
the package but without `suai`, see "Without the `suai` command" in
`references/commands.md`.

Never invent title-page data that is in neither the neighbouring report nor
the handout (teacher, their post, department): leave the value, mark it
`% TODO: проверить`, and list those places for the user at the end.

### 3. Read the assignment

Read the whole handout (a PDF with the Read tool, 20 pages at a time). Note
the goal, the tasks or steps, the variant, and what the report must
contain. A report structure prescribed by the handout overrides the default
below. Review questions (контрольные вопросы) stay out unless asked for.

### 4. Go through the screenshots

Open **every** file in `images/` with the Read tool and note what it shows,
which step of the assignment it belongs to, and what data is visible
(values, names, results). Captions and text come from what is actually in
the picture, not from the file name: `ris07.png` says nothing, while the
caption should read «Документ „Поступление товаров и услуг“, закладка
„Товары“». Figures go in the order the work was done (usually file-name
order). A screenshot that fits no step: ask, or mention it at the end —
never insert it silently.

### 5. Write `main.tex`

Default structure of a lab report:

```latex
\maketitle
\suaitoc

\suaiintro
Цель работы~--- …         % from the handout; rewording is fine, the meaning must match

\suaitasks
изучить …                 % tasks from the handout: lowercase, no final period
настроить …

Вариант, исходные данные, среда выполнения — абзацем, если есть.

\section{Ход работы}
\subsection{…}            % one subsection per step of the assignment
…
\suaiconclusion
…
\suaisources
Методические указания …
```

Course work: `type = Курсовая работа`, `number = ,` (empty), usually
`course-label = по дисциплине:`, chapters are `\section`, unnumbered
structural elements are `\suaisection{Вариант задания}`.

How to write the text itself is in `references/writing.md`. Read it before
the first report of a conversation: style, numbers, references, captions,
conclusion, sources.

### 6. Build and check

```bash
cd Subject/lab-5 && suai build                       # PDF: Subject-lab-5.pdf
python3 <skill-dir>/scripts/check_report.py .
```

`check_report.py` reads `main.tex` the way package v2.7.1 does, plus
`build/main.log`, and prints four parts:

- **ERRORS** — fix them: broken reference (with a similar label
  suggested), missing image or listing file, duplicate label, empty block,
  `\|` outside math, build errors. TeX reports an error inside a block at
  the line where the block ends; the script adds where the block starts.
- **WARNINGS** — look at each: objects never referenced or placed before
  their reference, unused screenshots, table rows with a different cell
  count, unknown listing language, overfull text, manual
  `figure`/`tabular`/`itemize`, stale log, build with an old package
  (update the package and rebuild).
- **TODO** — lines containing `TODO`; list them for the user.
- **SUMMARY** — pages, counts of figures, tables and listings, PDF name:
  ready-made data for your final message.

Exit code 1 means errors. The script also runs before a build and names
what would break it more clearly than the log does.

When a build stops, run the script first. If it finds no cause, look for
the first `./main.tex:42: …` line in `build/main.log`; common causes are
under "Build errors" in `references/commands.md`.

### 7. Look at the PDF

```bash
pdftoppm -r 60 -png -f 1 -l 4 Subject-lab-5.pdf /tmp/page   # then Read the PNGs
```

Check the title page, the contents, and pages with tables and listings:
columns in place, no figure ahead of its reference, no blank rows where
data should be. A few pages are enough.

### 8. Report back

Briefly: where the PDF is, how many pages, figures and tables, and **what
the user must check** — every `% TODO`, places where data was missing (for
example results that are on no screenshot), screenshots you left out.

## Syntax: the one rule

**A block command reads the lines below it up to a blank line.** Each line
becomes a list item, a table row, a formula legend entry or a source. A
block also ends at a line starting with `\suai…`, `\section`, `\begin`,
`\end`, `\clearpage`, so no blank line is needed before those (including
`\end{document}` after `\suaisources`). A `%` comment in a block line
belongs to that line only; a comment-only line is skipped and does not end
the block. Code under `\suaicode` is written **indented** and ends at the
first non-blank line without indentation.

| Command | What it does |
| --- | --- |
| `\suaiintro`, `\suaiconclusion` | «Введение», «Заключение» (unnumbered, on a new page) |
| `\suaisection{Название}` | any other unnumbered element |
| `\suaitasks` | «Для достижения поставленной цели…» + tasks а), б) |
| `\suaienum` / `\suailist` / `\suainum` | list а) б) / dashed / 1) 2) |
| `\suaitable[label]{Название}` | table, cells split by `\|`, first line is the header |
| `\suaiimg[width]{file}{Подпись}[label]` | figure from `images/`, label `fig:file` |
| `\suaieq[label]{formula}` | equation; `symbol \| meaning` lines give «где …» |
| `\suaicode[language, label]{Подпись}` | listing, code as indented lines below |
| `\suaicode[language]{file}{Подпись}` | listing from a file (also looked up in `code/`), label `lst:file` |
| `\suaisources` | list of sources, one per line |
| `\suaiapp[справочное]{Название}` | appendix А, Б… |
| `\figref`, `\tabref`, `\lstref`, `\formref` | «рисунке 1», «таблице 1», «листинге 1», «формуле (1)» |

Details, examples and handout-specific settings: `references/commands.md`.

## Pitfalls (most frequent first)

| Do this | Why |
| --- | --- |
| Keep a list item or a table row **on one line**, however long | A line break starts a new item / row |
| Leave a blank line after a block | Otherwise the next paragraph becomes one more item or row |
| Items start lowercase, no trailing `;` or `.` | Punctuation is added automatically (an abbreviation period stays: «и т. д.;», «5 шт.;»); `\suailist*` turns it off |
| Escape `% $ & # _` in cells and text | Plain LaTeX; a bare `%` is a comment and the rest of the line is lost |
| A literal `\|` in a cell is `\textbar{}` | `\|` separates cells; inside math it does not: `$\|x\|$ \| модуль` is two cells |
| In `\suaicode` escape nothing, indent ≥ 1 space, nothing after `{Подпись}` on that line | Code is read verbatim; the caption is LaTeX and needs `\_` |
| Use a known listing language | An unknown one still builds, but without highlighting and with a log warning; with no fitting language omit it: `\suaicode[label=lst:name]{…}` |
| Same image twice: 4th argument `[label]` on the second | Otherwise two `fig:file` labels |
| References: `на~\figref{x}`, `в~\tabref{x}`, `по~\formref{x}` | `\figref` prints the prepositional «рисунке 1»; for «рисунок 1», «рисунки 1–3» use `рисунок~\ref{fig:x}` |
| No manual `\begin{figure}`, `tabular`, `itemize`, `lstlisting` | Block commands give GOST formatting and labels; go manual only where a command cannot do the job |

Listing languages are case-insensitive: `Python`, `bash`, `SQL`, `C`,
`C++`, `C#`, `Java`, `JavaScript`, `TypeScript`, `JSON`, `YAML`,
`Dockerfile`, `HTML`, `XML`, `Go`, `Rust`, `Kotlin`, `PHP` and more — the
full list, short names and dialect-only languages (Lua, Assembler, Basic)
are under "Listings" in `references/commands.md`. Console output and
unlisted languages go without a language. `check_report.py` verifies the
language against the installed listings and suai-report.

## Never

- Invent results, numbers, program output or screen contents that are in
  neither the screenshots nor the data. No data means `% TODO` and a
  question to the user.
- Retell the handout: theory is brief and in your own words, just enough to
  explain what was done and why.
- Touch `.vscode/` or `build/`, or change the preamble without a reason
  (handout-specific settings are the exception, see
  `references/commands.md`).
