# Document and title page

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
  course       = Информатика,
  group        = 4419,
  student      = П. П. Петров,
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
