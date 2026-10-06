# Sources

The handout first, then what was really used. Per GOST R 7.0.100-2018, in
short form:

```latex
\suaisources
Методические указания к выполнению лабораторной работы «Организация базы знаний в менеджере Obsidian» по дисциплине «Облачные технологии и сервисы». СПб.: ГУАП, 2026.
Obsidian Help. URL: https://help.obsidian.md/ (дата обращения: 02.10.2026).
Фаулер М. Архитектура корпоративных программных приложений. М.: Вильямс, 2015. 544 с.
ГОСТ 7.32-2017. Отчет о научно-исследовательской работе. Структура и правила оформления. М.: Стандартинформ, 2017. 32 с.
```

The access date is today or the day the work was done. Do not pad the list
with sources that were not used: two honest ones beat five invented ones.

One source per line, numbered 1., 2. automatically; URLs wrap by
themselves. A citation in the text is a manual `[1]`. With biblatex, in the
preamble:

```latex
\usepackage[backend=biber,style=gost-numeric,language=auto,
            autolang=other,sorting=none]{biblatex}
\addbibresource{sources.bib}
```

then `\suaisources` with no lines under it and `\cite{key}` in the text.
