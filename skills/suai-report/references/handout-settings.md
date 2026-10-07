# Handout-specific settings

In the preamble, after `\usepackage{suai-report}`, and only when the
handout or the teacher requires it:

| Requirement | Line |
| --- | --- |
| Right margin 10 mm | `\geometry{right=10mm}` |
| Word-like "1.5" line spacing | `\setstretch{1.42}` |
| Body text 12 pt | `\documentclass[a4paper,12pt]{extarticle}` |
| Single spacing in tables | `\renewcommand{\suaitablestretch}{1}` |
| Equations numbered per section (1.1) | `\numberwithin{equation}{section}` |
| Figures / tables numbered per section | `\numberwithin{figure}{section}`, `\numberwithin{table}{section}` |
| Sections not on a new page | `\renewcommand{\sectionbreak}{}` |
| Headings not bold | `\renewcommand{\suaiheadfont}{\normalfont\fontsize{14}{17}\selectfont}` |
| Coloured listings | `\lstset{style=gostcolor}` |
| Bold keywords in listings | `\lstset{keywordstyle=\bfseries}` |
| Listings without line numbers / frame | `\lstset{numbers=none}`, `\lstset{frame=none}` |
| Listing font 10 pt | `\lstset{basicstyle=\ttfamily\fontsize{10}{12}\selectfont}` |
| No «Продолжение листинга N» line | `\renewcommand{\suailistingcontinued}{}` |
| En dash in captions | `\captionsetup{labelsep=endash}` |
| No breaks inside words at `_ / .` | `\XeTeXinterchartokenstate=0` |

Short macros of your own also go in the preamble, e.g.
`\newcommand{\f}[1]{\texttt{#1}}` for Excel function names.
