# Figures

```latex
Окно программы показано на~\figref{scheme}.

\suaiimg{scheme}{Главное окно Obsidian}
\suaiimg[0.5\textwidth]{diagram}{Схема сети}
\suaiimg{scheme}{То же окно после настройки}[scheme-after]
```

- The file is looked up in `images/` and next to `main.tex`; the extension
  (`png`, `jpg`, `pdf`) is not needed.
- Default width is `0.8\textwidth`; a wider value is capped at the text
  width, a figure taller than 0.75 of the page is scaled down. A narrow
  vertical screenshot (phone window, menu) looks better at
  `[0.4\textwidth]`–`[0.5\textwidth]`.
- The label is `fig:file-name` (`scheme` → `fig:scheme`). The optional
  fourth argument is an own label, used as written (no `fig:` added;
  `\figref{scheme-after}` still finds it); needed when one file is inserted
  twice.
- The caption starts with a capital, has no final period, and says what the
  figure shows. Open the image with the Read tool first: the caption comes
  from what is in the picture, not from the file name.
- A figure stands exactly where it is written (`[H]`), so put it after the
  paragraph that refers to it.
- No command puts two screenshots side by side in one figure: merge the
  images beforehand or use two figures.
- A chart from data (measurements, CSV): a matplotlib script writing
  `images/name.png` (dpi 200, Russian axis labels, no title above the
  chart — the caption plays that role), then `\suaiimg`. Keep the script
  next to the report (`plot.py`) so the chart can be rebuilt. No pgfplots
  or manual `\begin{figure}`.
