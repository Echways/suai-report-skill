# Tables

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
