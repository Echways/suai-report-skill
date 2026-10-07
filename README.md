# suai-report-skill

[![ci](https://github.com/Echways/suai-report-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Echways/suai-report-skill/actions/workflows/ci.yml)

Скилл для Claude Code: пишет отчёты ГУАП на
[suai-report](https://github.com/Echways/suai-report) — от методички и
скриншотов до готового PDF.

```text
> сделай отчёт по 5 лабе по базам данных, методичка и скрины в Databases/lab-5
```

## Установка

Нужен установленный suai-report (TeX Live, Python 3.10+):

```bash
git clone https://github.com/Echways/suai-report
cd suai-report && make install
```

Скилл ставится плагином в Claude Code:

```text
/plugin marketplace add Echways/suai-report-skill
/plugin install suai-report@suai-report
```

Или симлинком из клона этого репозитория:

```bash
ln -s "$PWD/skills/suai-report" ~/.claude/skills/suai-report
```

## Что умеет

- Создаёт отчёт (`suai new`, `suai next`), титул берёт из соседнего.
- Пишет текст по методичке: цель, ход работы по пунктам задания,
  заключение, список источников.
- Вставляет скриншоты из `images/` с подписями и ссылками в тексте.
- Оформляет таблицы, формулы и листинги командами `\suai…`.
- Переносит готовый отчёт из Markdown или Word.
- Собирает PDF (`suai build`) и проверяет результат.

## Проверка отчёта

Скрипт проверки работает и без Claude:

```bash
python3 skills/suai-report/scripts/check_report.py путь/к/lab-5
```

Он находит битые ссылки, отсутствующие файлы рисунков и листингов,
повторные метки, объекты без ссылок, забытые скриншоты и ошибки из лога
сборки. Рассчитан на suai-report v2.7.2.

## Лицензия

MIT
