# How to write the report text

The reader is a teacher who knows the subject and the handout. They need to
see quickly that every task is done, how, and what came out. So the text is
neither a retelling of the handout nor a diary: it describes what was done,
with results, tied to figures, tables and listings.

The report is in Russian; the Russian phrases below are the target style.

## Voice and tone

- Impersonal academic style, past tense: «установлен», «создано
  хранилище», «документ введен на основании…», «получены следующие
  результаты». No «я», «мы», «нам удалось».
- No filler or officialese: not «в данной лабораторной работе было
  произведено выполнение установки» but «Obsidian установлен с официального
  сайта».
- Specifics instead of generalities: names, versions, values, dates,
  document numbers — whatever the screenshots and data show. «Доверенность
  выдана 09.01.2026 менеджеру Лисичкиной А.~П. на 10 дней» beats «оформлена
  доверенность».
- Terms as in the program and the handout; interface element names in
  guillemets: закладка «Товары», кнопка «Подобрать неоплаченные».
- No emphasis (bold, italics, underline) in the text — under GOST only
  headings are bold. File, command and function names go in `\texttt{…}`.

## Introduction

```latex
\suaiintro

Цель работы~--- получение практических навыков организации базы знаний
в менеджере Obsidian.

\suaitasks
познакомиться с плагинами Obsidian, выбрать и установить не менее трех
разделить рабочее пространство на две части: теоретическую и проекты

Работа выполнялась в … для организации «…». Вариант~--- 16.
```

- The goal is one sentence, following the handout.
- Tasks are the handout's steps: infinitive verb, lowercase.
- Conditions, variant, input data, software versions — a short paragraph
  after the tasks, if any. A variant with a lot of data gets its own
  `\suaisection{Вариант задания}` with a table.

## Body («Ход работы»)

- One `\subsection` per assignment step or logical stage. Titles are nouns
  naming the substance: «Установка и настройка», «Сравнение способов
  синхронизации», not «Задание 3».
- Paragraph pattern: what was done → how (key parameters, settings,
  choices) → what came out → reference to the figure/table. Then the object
  itself.
- Brief theory fits where a step is unclear without it (what account 41 is,
  what a plugin does): 1–3 sentences in your own words, not a copy of the
  handout.
- If the work yields numbers (measurements, calculations, totals), give a
  table and a couple of sentences on what follows from them. If there is a
  formula, use `\suaieq` with a legend and a worked substitution.
- Code goes in a listing where it is needed for understanding, with a note
  on what it does and which parts matter. Program output is a listing
  without a language, or a figure.
- Problems met and how they were worked around are results too and worth
  describing («программа сообщила об отсутствии баз распределения, потому
  что…»).

## Figures, tables, listings

- Every object is referenced in the text, and **before** the object:
  «Окно программы показано на~\figref{scheme}.», then `\suaiimg`. The
  reference may be parenthetical: «(рисунок~\ref{fig:ris01})».
- Several in a row: «на рисунках~\ref{fig:a}--\ref{fig:d}» or
  «(рисунки~\ref{fig:a}, \ref{fig:b})».
- A caption says what is shown — capitalised, no period, specific:
  «Документ „Закрытие месяца“ за январь 2026 г.», «Граф рабочего
  пространства». Not «Скриншот», «Результат» or «Рисунок с окном».
- The text next to a figure does not repeat the caption; it says what
  matters in it: «Серые узлы~--- заметки, желтые~--- вложения».
- Consecutive screenshots with no text between them are fine if the
  paragraph before the group describes them.
- A table title also names the substance, units after a comma:
  «Распределение расходов на доставку по сумме, руб.».

## Typography details

| What | Write | Result |
| --- | --- | --- |
| Dash | `Цель работы~--- …` or `Цель работы — …` | non-breaking space before the dash |
| Reference | `на~\figref{x}`, `в~\tabref{x}` | the preposition stays attached |
| Number sign | `№~1` | № 1 |
| Initials | `Лисичкиной А.~П.`, on the title page `И. И. Иванов` | |
| Thousands | `220\,800,00` | 220 800,00 |
| Decimal | `1,5` (comma) | 1,5 |
| Percent | `20\,\%` | 20 % |
| Units | `10~шт.`, `4~КБ` | |
| Ledger entry | `Дт~41.01 Кт~60.01` | |
| Quotes | `«…»`, nested `„…“` | |
| Range | `2015--2020`, `рисунки~\ref{a}--\ref{b}` | en dash |
| LaTeX specials | `\%`, `\$`, `\&`, `\_`, `\#` | |

Access dates and dates in the text are DD.MM.YYYY.

## Conclusion

```latex
\suaiconclusion

В ходе работы … (что сделано, по задачам, коротко, с главными цифрами).

… (что из этого следует: сравнение, вывод, что оказалось удобным или
нет и почему).

Цель работы достигнута: получены практические навыки …
```

- 2–4 paragraphs of connected prose, not a «выполнено а), б), в)» list.
- Results with numbers, where there are any, and inferences — things the
  introduction did not contain. A conclusion that restates the goal in
  other words says nothing.
- The closing sentence about reaching the goal is optional; see how the
  user's neighbouring reports end.

## Sources

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

## Course work and large reports

- A fuller introduction: relevance, goal, tasks (by chapter), object.
- One chapter (`\section`) per part of the assignment, with subsections in
  a steady rhythm: problem → solution → result.
- Large sources and data dumps go to appendices (`\suaiapp`); the text
  carries fragments and «полный текст программы приведен в приложении~А».
- The conclusion goes chapter by chapter: what each one did, then the
  overall inference.
