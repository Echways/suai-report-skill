# Structure: sections and appendices

```latex
\suaiintro                    % ВВЕДЕНИЕ, new page, listed in the contents
\section{Ход работы}          % 1 Ход работы, new page
\subsection{Установка}        % 1.1 Установка
\subsubsection{…}             % 1.1.1
\suaisection{Вариант задания} % any unnumbered element, uppercased
\suaiconclusion               % ЗАКЛЮЧЕНИЕ
```

Every `\section` and `\suaisection` starts a new page, as GOST requires; no
`\clearpage` before them.

## Appendices

```latex
\suaiapp{Исходный код программы}              % (обязательное)
\suaiapp[справочное]{Результаты измерений}
```

Lettered А, Б, В… (skipping Ё, З, Й, О, Ч, Ъ, Ы, Ь). Figures, tables,
equations and listings inside are numbered А.1, А.2. Appendices come after
`\suaisources`. Refer to one in the text as `приведен в приложении~А`.
