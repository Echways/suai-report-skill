# Handout-specific settings

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
