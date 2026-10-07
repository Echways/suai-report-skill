# A new report from a handout and screenshots

Five steps, in order. A report moved from Word or Markdown goes the same
way: the source document supplies the text. After step 5 build, check and
report back as `SKILL.md` says.

## 1. Look around

- Find the report folder, usually `Subject/lab-N/`; the PDF is named after
  both folders: `Subject-lab-N.pdf`.
- See what is in it: the assignment handout (методичка, PDF/DOCX),
  `images/` with screenshots, `code/` or sources, data (xlsx, csv), a
  `main.tex` already started.
- Read the `main.tex` of a neighbouring report (usually the previous lab of
  the same course), but **only if it is on suai-report v2.6 or newer** —
  `build/main.log` says `Package: suai-report … v2.6` / `v2.7.2`, or
  `.vscode/settings.json` contains `suai_copy`. Such a report is the best
  model: it shows how the user writes the introduction, captions,
  conclusion and sources, and what goes on the title page. Match that
  style, not your own.
- Do not model on pre-2.6 reports: their syntax is obsolete
  (`\begin{code}`, manual `tabular`, `\allowbreak` in cells). With no 2.6+
  report nearby, follow this skill. Do not carry over v2.6 workarounds
  (formulas in cells without spaces, YAML and JSON listings without a
  language): 2.7 does not need them.

## 2. Create the report if there is no `main.tex`

```bash
cd Subject/lab-4 && suai next --no-open          # creates ../lab-5 with the lab-4 title page
suai new Subject/lab-5 --title "Название работы" --no-open
```

`suai new` takes the title page from the newest neighbouring report and the
number from the folder name (`lab-5` → 5), sets `date = today`, creates
`images/`, `.vscode/`, `.gitignore`. An existing folder with materials is
fine: nothing is touched (it fails only if `main.tex` exists). `--no-open`
keeps VS Code closed; drop it if the user wants the live preview.

No `suai` command: see "Without the `suai` command" in
`references/build.md`. Title-page keys are in `references/title-page.md`.

## 3. Read the assignment

Read the whole handout (a PDF with the Read tool, 20 pages at a time). Note
the goal, the tasks or steps, the variant, and what the report must
contain. A report structure prescribed by the handout overrides the default
below. Review questions (контрольные вопросы) stay out unless asked for.

## 4. Go through the screenshots

Open **every** file in `images/` with the Read tool and note what it shows,
which step of the assignment it belongs to, and what data is visible
(values, names, results). Captions and text come from what is actually in
the picture, not from the file name: `ris07.png` says nothing, while the
caption should read «Документ „Поступление товаров и услуг“, закладка
„Товары“». Figures go in the order the work was done (usually file-name
order). A screenshot that fits no step: ask, or mention it at the end —
never insert it silently.

## 5. Write `main.tex`

Default structure of a lab report:

```latex
\maketitle
\suaitoc

\suaiintro
Цель работы~--- …         % from the handout; rewording is fine, the meaning must match

\suaitasks
изучить …                 % tasks from the handout: lowercase, no final period
настроить …

Вариант, исходные данные, среда выполнения — абзацем, если есть.

\section{Ход работы}
\subsection{…}            % one subsection per step of the assignment
…
\suaiconclusion
…
\suaisources
Методические указания …
```

How to write the text itself is in `references/writing.md`. Read it before
the first report of a conversation: style, numbers, references, captions,
conclusion. Course work is laid out differently: `references/course-work.md`.
