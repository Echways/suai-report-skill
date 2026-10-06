# Lists

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
