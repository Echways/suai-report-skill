# Listings

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
  `check_report.py` shows it as a warning: it verifies the language against
  the installed listings and suai-report.
- Any indentation works (≥ 1 space or a tab); the common part is stripped.
  Blank lines inside the code are kept. The code ends at the first
  non-blank line without indentation — that line is body text already.
- Nothing is escaped inside the code: `%`, `#`, `\`, `{}`, `$`, Cyrillic —
  all verbatim.
- Nothing follows the caption on the `\suaicode…{Подпись}` line (otherwise
  the error «После подписи \suaicode на той же строке ничего не пишется»).
- The caption is LaTeX: `Файл dags/clickhouse\_upload.py`.
- Long lines wrap automatically with a ↪ mark.
- Highlighting is italic comments only: keywords are not bold and nothing
  is coloured, since GOST keeps bold for headings.
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

`\suaicode` always typesets the whole file: `firstline`, `lastline` and
`linerange` are ignored. Part of a file is the one case for the listings
command itself. It gets the same frame, numbering and `\lstref`, but the
path is taken from the report folder (`code/` is not searched) and the
label is written in full:

```latex
Функция чтения приведена в~\lstref{read}.

\lstinputlisting[language=C++, caption={Функция чтения чисел из файла},
  label=lst:read, firstline=18, lastline=39, firstnumber=18]{code/stats.cpp}
```

Coloured listings (`\lstset{style=gostcolor}`) and bold keywords
(`\lstset{keywordstyle=\bfseries}`) go in the preamble and only on
request: GOST discourages both. A key for one listing goes in its
brackets: `\suaicode[Python, numbers=none]{…}`.

Never use the `\begin{code}` environment from pre-v2.5 reports, even if a
neighbouring report has it: code is written only with `\suaicode` (and
`\lstinputlisting` for a part of a file).
