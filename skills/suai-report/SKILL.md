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

## Read what the task needs

This file holds what every task needs. The rest is in `references/`, one
topic per file. Read a file when its row applies, not in advance.

| When | Read |
| --- | --- |
| There is no report yet — a handout, screenshots, code or data to turn into one, or a Word / Markdown report to move over | `references/new-report.md` |
| Writing or rewriting report text: introduction, steps of the work, captions, conclusion | `references/writing.md` |
| Course work, or a report with chapters and appendices | `references/course-work.md` as well |
| Title page, `\suaisetup` keys, a `main.tex` written by hand | `references/title-page.md` |
| The handout or the teacher wants non-default formatting: margins, spacing, coloured listings, per-section equation numbers | `references/handout-settings.md` |
| The build stops, there is no `suai` command, or a `suai` subcommand other than `build` is needed | `references/build.md` |
| A block command is used for the first time in the conversation | its file from the "Details" column below |

## Syntax: the one rule

**A block command reads the lines below it up to a blank line.** Each line
becomes a list item, a table row, a formula legend entry or a source. A
block also ends at a line starting with `\suai…`, `\section`, `\begin`,
`\end`, `\clearpage`, so no blank line is needed before those (including
`\end{document}` after `\suaisources`). A `%` comment in a block line
belongs to that line only; a comment-only line is skipped and does not end
the block. Code under `\suaicode` is written **indented** and ends at the
first non-blank line without indentation.

| Command | What it does | Details |
| --- | --- | --- |
| `\suaiintro`, `\suaiconclusion` | «Введение», «Заключение» (unnumbered, on a new page) | `references/structure.md` |
| `\suaisection{Название}` | any other unnumbered element | `references/structure.md` |
| `\suaitasks` | «Для достижения поставленной цели…» + tasks а), б) | `references/lists.md` |
| `\suaienum` / `\suailist` / `\suainum` | list а) б) / dashed / 1) 2) | `references/lists.md` |
| `\suaitable[label]{Название}` | table, cells split by `\|`, first line is the header | `references/tables.md` |
| `\suaiimg[width]{file}{Подпись}[label]` | figure from `images/`, label `fig:file` | `references/figures.md` |
| `\suaieq[label]{formula}` | equation; `symbol \| meaning` lines give «где …» | `references/equations.md` |
| `\suaicode[language, label]{Подпись}` | listing, code as indented lines below | `references/listings.md` |
| `\suaicode[language]{file}{Подпись}` | listing from a file (also looked up in `code/`), label `lst:file` | `references/listings.md` |
| `\suaisources` | list of sources, one per line | `references/sources.md` |
| `\suaiapp[справочное]{Название}` | appendix А, Б… | `references/structure.md` |
| `\figref`, `\tabref`, `\lstref`, `\formref` | «рисунке 1», «таблице 1», «листинге 1», «формуле (1)» | the references row below |

The reference files are verified against suai-report v2.7.1. The package
source is `~/texmf/tex/latex/suai-report/suai-report.sty` (`kpsewhich
suai-report.sty`); where behaviour differs from them, the source wins.

## Pitfalls (most frequent first)

| Do this | Why |
| --- | --- |
| Keep a list item or a table row **on one line**, however long | A line break starts a new item / row |
| Leave a blank line after a block | Otherwise the next paragraph becomes one more item or row |
| Items start lowercase, no trailing `;` or `.` | Punctuation is added automatically (an abbreviation period stays: «и т. д.;», «5 шт.;»); `\suailist*` turns it off |
| Escape `% $ & # _` in cells and text | Plain LaTeX; a bare `%` is a comment and the rest of the line is lost |
| A literal `\|` in a cell is `\textbar{}` | `\|` separates cells; inside math it does not: `$\|x\|$ \| модуль` is two cells |
| In `\suaicode` escape nothing, indent ≥ 1 space, nothing after `{Подпись}` on that line | Code is read verbatim; the caption is LaTeX and needs `\_` |
| Use a known listing language (the list is in `references/listings.md`) | An unknown one still builds, but without highlighting and with a log warning; with no fitting language omit it: `\suaicode[label=lst:name]{…}` |
| Same image twice: 4th argument `[label]` on the second | Otherwise two `fig:file` labels |
| References: `на~\figref{x}`, `в~\tabref{x}`, `по~\formref{x}`, the label without its `fig:` / `tab:` prefix | `\figref` prints one case only, the prepositional «рисунке 1»; any other form is `\ref` with the full label: `(рисунок~\ref{fig:x})`, `на рисунках~\ref{fig:a}--\ref{fig:d}`, `(\tabref{t}, рисунок~\ref{fig:x})` |
| No manual `\begin{figure}`, `tabular`, `itemize`, `lstlisting` | Block commands give GOST formatting and labels; go manual only where a command cannot do the job |

## After every change

### Build and check

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
under "Build errors" in `references/build.md`.

### Look at the PDF

```bash
pdftoppm -r 60 -png -f 1 -l 4 Subject-lab-5.pdf /tmp/page   # then Read the PNGs
```

Check the title page, the contents, and pages with tables and listings:
columns in place, no figure ahead of its reference, no blank rows where
data should be. A few pages are enough.

### Report back

Briefly: where the PDF is, how many pages, figures and tables, and **what
the user must check** — every `% TODO`, places where data was missing (for
example results that are on no screenshot), screenshots you left out.

## Never

- Invent results, numbers, program output or screen contents that are in
  neither the screenshots nor the data. No data means `% TODO` and a
  question to the user.
- Invent title-page data that is in neither the neighbouring report nor the
  handout (teacher, their post, department): leave the value, mark it
  `% TODO: проверить`, and list those places for the user at the end.
- Retell the handout: theory is brief and in your own words, just enough to
  explain what was done and why.
- Touch `.vscode/` or `build/`, or change the preamble without a reason
  (handout-specific settings are the exception, see
  `references/handout-settings.md`).
