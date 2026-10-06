# suai-report command reference

Everything below is verified against suai-report v2.7.1. The package source
is `~/texmf/tex/latex/suai-report/suai-report.sty` (`kpsewhich
suai-report.sty`); where behaviour differs from this file, the source wins.

## Contents

- Document and title page: `\suaisetup`
- Structure: introduction, sections, conclusion, appendices
- Lists
- Tables
- Figures
- Equations
- Listings
- References
- Sources
- Handout-specific settings
- Without the `suai` command
- The `suai` command
- Build errors

## Document and title page

```latex
\documentclass[a4paper,14pt]{extarticle}
\usepackage{suai-report}

\suaisetup{
  department   = 41,
  teacher-post = доцент, канд. техн. наук,
  teacher      = И. И. Иванов,
  type         = Отчет о лабораторной работе,
  number       = 1,
  title        = Название работы,
  course       = Название дисциплины,
  group        = 4414,
  student      = И. И. Студентов,
  date         = today,
}

\begin{document}
\maketitle
\suaitoc
…
\end{document}
```

- `type` is uppercased automatically. Values: «Отчет о лабораторной
  работе», «Отчет о практической работе», «Курсовая работа», «Пояснительная
  записка к курсовому проекту», «Доклад».
- An empty `number` (`number = ,`) drops the «№».
- `title` — as in the handout, in normal case (uppercased automatically).
- `date = today` — build date as DD.MM.YYYY; `date = 12.09.2026` — a fixed
  one; no `date` or an empty one — blank lines to fill in by hand.
- Several students: `student = А. А. Иванов, Б. Б. Петров` — one line each.
- Commas in values need no braces: `teacher-post = доцент, канд. техн.
  наук` works.
- More keys: `course-label` (default «по курсу:», course works often use
  «по дисциплине:»), `year`, `city`.
- `% # & _` in values take a backslash: `\%`, `\_`. A value with `=` goes
  in braces: `title = {Расчёт y = kx}`. `suai new --title "…"` escapes and
  braces by itself.

`\maketitle` is the title page (counts as page 1, number not printed).
`\suaitoc` is «СОДЕРЖАНИЕ» on a new page.

## Structure

```latex
\suaiintro                    % ВВЕДЕНИЕ, new page, listed in the contents
\section{Ход работы}          % 1 Ход работы, new page
\subsection{Установка}        % 1.1 Установка
\subsubsection{…}             % 1.1.1
\suaisection{Вариант задания} % any unnumbered element, uppercased
\suaiconclusion               % ЗАКЛЮЧЕНИЕ
```

Every `\section` and `\suaisection` starts a new page, as GOST requires; no
`\clearpage` before them.

### Appendices

```latex
\suaiapp{Исходный код программы}              % (обязательное)
\suaiapp[справочное]{Результаты измерений}
```

Lettered А, Б, В… (skipping Ё, З, Й, О, Ч, Ъ, Ы, Ь). Figures, tables,
equations and listings inside are numbered А.1, А.2. Appendices come after
`\suaisources`. Refer to one in the text as `приведен в приложении~А`.

## Lists

```latex
\suaitasks
установить Obsidian и создать хранилище
настроить синхронизацию

\suailist
панель файлов слева
редактор заметок в центре

\suaienum            % а) б) в)
\suainum             % 1) 2) 3)
```

- `\suaitasks` prints «Для достижения поставленной цели необходимо решить
  следующие задачи:» and an а), б) list. Own lead-in: `\suaitasks[Задачи
  работы:]`; none: `\suaitasks[]`.
- Punctuation is automatic: `;` after each item, `.` after the last. A
  trailing `; . ,` of your own is replaced; `? ! :` stay. An abbreviation
  period at the end of an item (`и т. д.`, `и т. п.`, `и др.`, `и пр.`,
  `г.`, `гг.`, `вв.`, `руб.`, `коп.`, `тыс.`, `шт.`, `экз.`, `стр.`) is
  kept: «и т. д.;». The starred forms (`\suailist*`, `\suaienum*`,
  `\suainum*`, `\suaitasks*`) leave punctuation alone — for items that are
  full sentences with a capital letter and a period.
- A list usually follows a lead-in ending with a colon: «Основные элементы
  интерфейса:». It may sit on the line right above the command, with no
  blank line.
- Block commands do not nest. For a second level use a plain
  `\begin{enumerate}`/`\begin{itemize}` (the package has already styled the
  levels), but first consider whether a table is simpler.

## Tables

```latex
Способы синхронизации сравниваются в~\tabref{sync}.

\suaitable[sync]{Сравнение способов синхронизации}
Способ          | Стоимость    | Шифрование
Obsidian Sync   | 4 \$ в месяц | да
Яндекс Диск     | бесплатно    | нет
```

- The first line is the header (centred, not bold); the first column is
  left-aligned, the rest centred. Column widths fit the text automatically:
  no `\allowbreak`, `p{…}` or manual widths.
- The label `[sync]` gives `tab:sync`. A table without a label cannot be
  referenced, and GOST requires a reference — always set one.
- Units go into the title after a comma: `{Поступление ТМЦ, руб.}`.
- An empty cell is a space between bars: `Итого |  | 184 000,00`.
- A long table continues on the next page under «Продолжение таблицы 1»
  with the header repeated.
- Cells take ordinary LaTeX: `$x^2$`, `\texttt{…}`, `\%`, `\$`, `\&`, `\_`,
  `\#`. A literal «|» in cell text is `\textbar{}`; `\|` is the math symbol
  ‖ and gives «Missing $» outside math.
- A formula in a cell is written as in text, spaces included: `$a + b$`,
  `\( a + b \)`. A bar inside math does not split the cell:
  `$|x|$ | модуль числа` is two cells.
- A `%` comment in a table line (or any block line) belongs to that line
  only; a comment-only line is skipped. A `%` inside braces
  (`\url{…a%20b}`) stays text.
- A hand-made table (`tabular`, `longtable`) gets the same line spacing as
  `\suaitable` — the same as body text.
- There are no merged cells. If really needed, use `xltabular` by hand with
  `\caption` and `\label{tab:…}` (see the package demo for the styling),
  but restructuring the table is usually better.
- Aligning the source with spaces is for readability only.

## Figures

```latex
Окно программы показано на~\figref{scheme}.

\suaiimg{scheme}{Главное окно Obsidian}
\suaiimg[0.5\textwidth]{diagram}{Схема сети}
\suaiimg{scheme}{То же окно после настройки}[scheme-after]
```

- The file is looked up in `images/` and next to `main.tex`; the extension
  (`png`, `jpg`, `pdf`) is not needed.
- Default width is `0.8\textwidth`; a wider value is capped at the text
  width, a figure taller than 0.75 of the page is scaled down. A narrow
  vertical screenshot (phone window, menu) looks better at
  `[0.4\textwidth]`–`[0.5\textwidth]`.
- The label is `fig:file-name` (`scheme` → `fig:scheme`). The optional
  fourth argument is an own label, used as written (no `fig:` added;
  `\figref{scheme-after}` still finds it); needed when one file is inserted
  twice.
- The caption starts with a capital, has no final period, and says what the
  figure shows.
- A figure stands exactly where it is written (`[H]`), so put it after the
  paragraph that refers to it.
- No command puts two screenshots side by side in one figure: merge the
  images beforehand or use two figures.
- A chart from data (measurements, CSV): a matplotlib script writing
  `images/name.png` (dpi 200, Russian axis labels, no title above the
  chart — the caption plays that role), then `\suaiimg`. Keep the script
  next to the report (`plot.py`) so the chart can be rebuilt. No pgfplots
  or manual `\begin{figure}`.

## Equations

```latex
Объём хранилища оценивается по~\formref{size}:
\suaieq[size]{V = N \cdot \bar{s}}
V | объём хранилища, КБ
N | число заметок
\bar{s} | средний размер заметки, КБ

Для 300 заметок по 4 КБ получаем 1,2 МБ.
```

- The label `[size]` → `eq:size`, number (1) on the right.
- `symbol | meaning` lines give an aligned «где V — объём хранилища, КБ;».
  `$` around the symbol is added automatically. With no lines the equation
  has no legend, but the blank line after it is still required.
- Inline math is ordinary `$…$`. A multi-line derivation is a manual
  `\begin{align}` (with `\label{eq:…}` so that `\formref` works).
- Per-section numbering (1.1): `\numberwithin{equation}{section}` in the
  preamble.

## Listings

Code in the text is **indented** lines under the command:

```latex
Скрипт приведен в~\lstref{backup}.

\suaicode[bash, backup]{Резервное копирование хранилища}
    #!/bin/bash
    # архив с датой в имени
    tar -czf "vault-$(date +%F).tar.gz" ~/Obsidian/Vault

    echo "Готово"

Дальше обычный текст.
```

- In the brackets the first value without `=` is the language, the second
  the label (`backup` → `lst:backup`). Values with `=` are listings keys
  (`firstnumber=10`, `language={[Sharp]C}`, `label=lst:name`).
- Without a language (console output, unlisted language):
  `\suaicode[label=lst:out]{Вывод программы}`. A label cannot be passed
  positionally without a language — `[, out]` does not work.
- An unknown language does not stop the build: the code is typeset without
  highlighting, the log gets `Язык листинга '…' неизвестен`, and
  `check_report.py` shows it as a warning.
- Any indentation works (≥ 1 space or a tab); the common part is stripped.
  Blank lines inside the code are kept. The code ends at the first
  non-blank line without indentation — that line is body text already.
- Nothing is escaped inside the code: `%`, `#`, `\`, `{}`, `$`, Cyrillic —
  all verbatim.
- Nothing follows the caption on the `\suaicode…{Подпись}` line (otherwise
  the error «После подписи \suaicode на той же строке ничего не пишется»).
- The caption is LaTeX: `Файл dags/clickhouse\_upload.py`.
- Long lines wrap automatically with a ↪ mark.
- A listing that does not fit continues on the next page under
  «Продолжение листинга N», like a table. A caption is never left at the
  bottom of a page without code: the whole listing moves to the next page.
  Do not move listings by hand (`\clearpage`, `\newpage`).

Languages (case-insensitive; `C#` is written as is:
`\suaicode[C#, form]{…}`):

- from listings: `Python`, `bash`, `sh`, `SQL`, `C`, `C++`, `C#`, `Java`,
  `PHP`, `HTML`, `XML`, `Go`, `R`, `Matlab`, `Octave`, `Pascal`, `Delphi`,
  `VBScript`, `Haskell`, `Ruby`, `Perl`, `TeX`, `make`, `Fortran`, `Lisp`,
  `Prolog`, `VHDL`, `Verilog`, `gnuplot`, `Awk`, `erlang`, `Scala`,
  `Swift`, `csh`, `ksh`, `tcl`, `Scilab`;
- added by the package: `JavaScript`, `TypeScript`, `Kotlin`, `Rust`,
  `JSON`, `YAML`, `Dockerfile`;
- short names: `cpp`, `cs`, `csharp`, `js`, `ts`, `py`, `kt`, `rs`, `yml`,
  `docker`;
- dialect-only, passed as a key: `\suaicode[language={[5.3]Lua},
  label=lst:x]{…}`, `{[x86masm]Assembler}`, `{[Visual]Basic}` — without the
  dialect they are typeset without highlighting.

Code from a file — a second pair of braces on the same line:

```latex
\suaicode[Python]{sort.py}{Сортировка пузырьком}          % label lst:sort
\suaicode[Python, main]{src/app/main.py}{Точка входа}     % label lst:main
\suaicode[C++]{lab.cpp}{Программа}[lst:program]           % own label
```

The file is looked up from the report folder and in `code/`. For long
programs this beats copying code into the text: one source of truth. Whole
programs of several pages usually go to an appendix.

Coloured listings: `\lstset{style=gostcolor}` in the preamble (GOST
discourages it; only on request). Never use the `\begin{code}` environment
from pre-v2.5 reports, even if a neighbouring report has it: code is
written only with `\suaicode`.

## References

| Command | Prints | In the text |
| --- | --- | --- |
| `\figref{scheme}` | рисунке 1 | `показано на~\figref{scheme}` |
| `\tabref{sync}` | таблице 1 | `приведены в~\tabref{sync}` |
| `\lstref{backup}` | листинге 1 | `приведен в~\lstref{backup}` |
| `\formref{size}` | формуле (1) | `рассчитывается по~\formref{size}` |

The prefix (`fig:`, `tab:`…) is not written. The commands print one case
only, the prepositional. For other forms use `\ref` with the full label:

```latex
(рисунок~\ref{fig:ris01})
на рисунках~\ref{fig:note-03}--\ref{fig:note-13}
(рисунки~\ref{fig:ris13}, \ref{fig:ris14})
(\tabref{tmc}, рисунок~\ref{fig:ris17})
```

## Sources

```latex
\suaisources
Методические указания к выполнению лабораторной работы «…» по дисциплине «…». СПб.: ГУАП, 2026.
Obsidian Help. URL: https://help.obsidian.md (дата обращения: 12.09.2026).
Фаулер М. Архитектура корпоративных программных приложений. М.: Вильямс, 2015. 544 с.
```

One source per line, numbered 1., 2. automatically; URLs wrap by
themselves. A citation in the text is a manual `[1]`. With biblatex, in the
preamble:

```latex
\usepackage[backend=biber,style=gost-numeric,language=auto,
            autolang=other,sorting=none]{biblatex}
\addbibresource{sources.bib}
```

then `\suaisources` with no lines under it and `\cite{key}` in the text.

## Handout-specific settings

In the preamble, after `\usepackage{suai-report}`, and only when the
handout or the teacher requires it:

| Requirement | Line |
| --- | --- |
| Right margin 10 mm | `\geometry{right=10mm}` |
| Word-like "1.5" line spacing | `\setstretch{1.42}` |
| Single spacing in tables | `\renewcommand{\suaitablestretch}{1}` |
| Equations numbered per section (1.1) | `\numberwithin{equation}{section}` |
| Headings not bold | `\renewcommand{\suaiheadfont}{\normalfont\fontsize{14}{17}\selectfont}` |
| Coloured listings | `\lstset{style=gostcolor}` |
| Bold keywords | `\lstset{keywordstyle=\bfseries}` |
| No «Продолжение листинга N» line | `\renewcommand{\suailistingcontinued}{}` |
| En dash in captions | `\captionsetup{labelsep=endash}` |
| No breaks inside words at `_ / .` | `\XeTeXinterchartokenstate=0` |

Short macros of your own also go in the preamble, e.g.
`\newcommand{\f}[1]{\texttt{#1}}` for Excel function names.

## Without the `suai` command

If `suai` is not installed but the package is (`kpsewhich suai-report.sty`
prints a path), create `images/` and a `main.tex` from the template at the
top of this file. Build with:

```bash
latexmk -xelatex -outdir=build -interaction=nonstopmode -halt-on-error main.tex
cp build/main.pdf "$(basename "$(dirname "$PWD")")-$(basename "$PWD").pdf"
```

## The `suai` command

| Command | What it does |
| --- | --- |
| `suai new DIR [--title T] [--no-open]` | new report; title page from the newest neighbour |
| `suai next [--title T] [--no-open]` | from folder `lab-4` create `../lab-5` with the same title page |
| `suai build [DIR]` | build the PDF (`Subject/lab-3` → `Subject-lab-3.pdf`), aux files in `build/` |
| `suai open [DIR]` | build and open the PDF |
| `suai watch [DIR]` | rebuild on save (do not run it in the background needlessly) |
| `suai clean [DIR]` | delete `build/` and the PDF |
| `suai update` | refresh the report's `.vscode/` |

## Build errors

The build runs with `-halt-on-error`: the first error stops everything. The
`./main.tex:N: …` line says where to look. TeX reports an error inside a
block (`\suaitable`, `\suailist`…) at the line where the block ended (the
blank line after it) — the error itself is in one of the block's lines;
`check_report.py` names that block.

| Message | Cause |
| --- | --- |
| `File ended while scanning use of \__suai_line:w`, `Couldn't load requested language`, «Missing $» on `$a + b$` in a cell | package older than v2.7 (`kpsewhich suai-report.sty`, first line of the log) — update: `cd suai-report && git pull && make install` |
| Warning `Язык листинга '…' неизвестен` | not an error: the code has no highlighting; fix the language name or drop it; Lua only with a dialect, `{[5.3]Lua}` |
| `Под \suaicode нет строк с отступом` | the code is not indented, or the file form `{file}{Подпись}` was meant |
| `После подписи \suaicode на той же строке ничего не пишется` | text after `{Подпись}` |
| `File 'x' not found` (graphicx) | no such file in `images/`; check the name and letter case |
| `Missing $ inserted` | `_` or `^` in text or a cell without `$` / `\_`; in a table also `\|` outside math |
| `Misplaced alignment tab character &` | `&` in text or a cell → `\&` |
| `Undefined control sequence` | typo in a command, or a `\` in text (Windows path → `\textbackslash{}` or `\texttt{…}` with `/`) |
| `Extra }, or forgotten $` / `Runaway argument` | unbalanced braces, often a bare `%` cut the line |
| Warning `Шрифт 'Times New Roman' не найден` | not an error: TeX Gyre Termes is substituted; tell the user to install `ttf-mscorefonts-installer` |
| `Reference 'fig:x' undefined` | typo in the label, or the figure is not inserted |
| `Label 'fig:x' multiply defined` | one image twice without an own label |
