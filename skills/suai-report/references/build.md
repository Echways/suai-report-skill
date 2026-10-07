# The `suai` command and build errors

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
| `suai install` / `suai uninstall` | put `suai-report.sty` and the command in place / remove them |

## Without the `suai` command

If there is no `suai` command, check the package: `kpsewhich
suai-report.sty`. Without the package nothing builds — tell the user to run
`git clone https://github.com/Echways/suai-report && make install`.

If `suai` is not installed but the package is (`kpsewhich suai-report.sty`
prints a path), create `images/` and a `main.tex` from the template in
`references/title-page.md`. Build with:

```bash
latexmk -xelatex -outdir=build -interaction=nonstopmode -halt-on-error main.tex
cp build/main.pdf "$(basename "$(dirname "$PWD")")-$(basename "$PWD").pdf"
```

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
| `Undefined control sequence` on a `\suai…` command, or an error about XeTeX right after `\usepackage{suai-report}` | a stale copy of the package (run `suai install`), or the build ran `pdflatex` / `lualatex` instead of `suai build` |
| Warning `xdvipdfmx:warning: Object @table.1 already defined` | harmless, appears in reports with tables |
| `Reference 'fig:x' undefined` | typo in the label, or the figure is not inserted |
| `Label 'fig:x' multiply defined` | one image twice without an own label |
