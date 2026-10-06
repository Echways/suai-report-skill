# Equations

```latex
Объём хранилища оценивается по~\formref{size}:
\suaieq[size]{V = N \cdot \bar{s}}
V | объём хранилища, КБ
N | число заметок
\bar{s} | средний размер заметки, КБ

Для 300 заметок по 4 КБ получаем 1,2 МБ.
```

- The label `[size]` → `eq:size`, number (1) on the right.
- `symbol | meaning` lines give an aligned «где V — объём хранилища, КБ;».
  `$` around the symbol is added automatically. With no lines the equation
  has no legend, but the blank line after it is still required.
- Inline math is ordinary `$…$`. A multi-line derivation is a manual
  `\begin{align}` (with `\label{eq:…}` so that `\formref` works).
- Per-section numbering (1.1): `\numberwithin{equation}{section}` in the
  preamble.
