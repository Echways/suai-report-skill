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
- There are no merged cells or fixed widths. Restructuring the table is
  usually better; if they are really needed, write a `tabularx` by hand.
  The caption, numbering and `\tabref` work the same:

  ```latex
  \begin{table}[H]
    \caption{Состав стенда}\label{tab:stand}
    \begin{tabularx}{\textwidth}{|L{4cm}|Y|R{3cm}|}
      \hline
      Узел & Назначение & Количество \\ \hline
      Сервер & хранение данных & 2 \\ \hline
      \multicolumn{2}{|l|}{Всего узлов} & 2 \\ \hline
    \end{tabularx}
  \end{table}
  ```

  Column types from the package: `L{width}`, `P{width}`, `R{width}` — fixed
  width, text left / centred / right; `Y` — takes the remaining width,
  centred. A hand-made table longer than a page is `xltabular` with the
  same columns.
- Aligning the source with spaces is for readability only.
