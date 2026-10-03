# suai-report-skill

[![ci](https://github.com/Echways/suai-report-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Echways/suai-report-skill/actions/workflows/ci.yml)

Скилл для Claude Code, который пишет отчёты ГУАП на
[suai-report](https://github.com/Echways/suai-report): читает методичку,
разбирает скриншоты, пишет `main.tex`, собирает PDF и проверяет его.

```text
> сделай отчет по 5 лабе по базам данных, методичка и скрины в Databases/lab-5
```

## Установка

Сначала сам шаблон (нужны TeX Live, Python 3.10+):

```bash
git clone https://github.com/Echways/suai-report
cd suai-report && make install
```

Потом скилл — в Claude Code:

```text
/plugin marketplace add Echways/suai-report-skill
/plugin install suai-report@suai-report
```

Или без плагинов, симлинком из клона этого репозитория:

```bash
ln -s "$PWD/skills/suai-report" ~/.claude/skills/suai-report
```

## Что умеет

- Новый отчёт: `suai new` / `suai next`, титул — из соседнего отчёта.
- Текст по методичке: цель, задачи, ход работы по пунктам задания,
  заключение с результатами, список источников.
- Скриншоты из `images/` — с подписями по тому, что на них видно, и
  ссылками в тексте.
- Таблицы, формулы, листинги через блочные команды `\suai…`.
- Перенос готового отчёта из Markdown или Word.
- Сборка `suai build` и проверка `scripts/check_report.py` под suai-report
  v2.6. Скрипт читает `main.tex` так же, как пакет, и ловит то, что уронит
  сборку или испортит PDF: битые ссылки, нет файла рисунка или листинга,
  язык, которого нет в установленном listings, `%` в строке блока,
  блок без пустой строки перед `\end{…}`, формула с пробелами в ячейке.
  Ещё он показывает объекты без ссылок, забытые скриншоты, перенесённые
  строки таблиц и ошибки из лога с номером строки.

Скрипт проверки можно запускать и без Claude:

```bash
python3 skills/suai-report/scripts/check_report.py путь/к/lab-5
```

## Устройство

```text
skills/suai-report/
├── SKILL.md                 порядок работы, синтаксис, ловушки
├── references/commands.md   все команды suai-report с примерами
├── references/writing.md    как писать текст отчёта
└── scripts/check_report.py  проверка main.tex и лога сборки
evals/evals.json             тестовые задания для скилла
```

## Проверки

На каждый push и pull request GitHub Actions (`.github/workflows/ci.yml`)
запускает `ruff`, сверяет манифесты плагина, `SKILL.md` и `evals.json`
(`.github/scripts/check_repo.py`), собирает демо-отчёт настоящим suai-report
и прогоняет по нему `check_report.py`. Раз в неделю то же самое идёт по
расписанию — на случай, если пакет ушёл вперёд.

Релиз: поднять `version` в `.claude-plugin/plugin.json`, затем

```bash
git tag v1.0.1 && git push --tags
```

## Лицензия

MIT
