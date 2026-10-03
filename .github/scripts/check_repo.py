#!/usr/bin/env python3
"""Проверка репозитория плагина: манифесты, SKILL.md, evals.json.

  python3 .github/scripts/check_repo.py [--tag vX.Y.Z]

Ловит то, из-за чего плагин не поставится или скилл не сработает:
битый JSON, разные имена в plugin.json, marketplace.json и SKILL.md,
слишком длинное описание, ссылку на файл, которого нет в скилле.
С --tag ещё сверяет тег с version из plugin.json.

Код выхода: 0 — всё в порядке, 1 — есть ошибки.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
VERSION = re.compile(r"\d+\.\d+\.\d+")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
SKILL_PATH = re.compile(r"(?<![\w/.-])(?:references|scripts|assets)/[\w./-]*\w")

errors: list[str] = []


def error(path: Path, text: str) -> None:
    errors.append(f"{path.relative_to(REPO)}: {text}")


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        error(path, "файла нет")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        error(path, f"не JSON: {e}")
        return None
    if not isinstance(data, dict):
        error(path, "на верхнем уровне должен быть объект")
        return None
    return data


def text_field(path: Path, data: dict, key: str, where: str = "") -> str | None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        error(path, f"{where}нет строки «{key}»")
        return None
    return value


def frontmatter(path: Path, text: str) -> dict[str, str] | None:
    """Поля «ключ: значение» между двумя «---»; значение может быть в кавычках."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        error(path, "нет frontmatter между строками «---»")
        return None
    fields: dict[str, str] = {}
    key = None
    for line in m.group(1).split("\n"):
        field = re.fullmatch(r"([A-Za-z][\w-]*):\s*(.*)", line)
        if field:
            key = field.group(1)
            fields[key] = field.group(2)
        elif key and line.startswith((" ", "\t")):
            fields[key] += " " + line.strip()
    return {key: unquote(path, key, value.strip()) for key, value in fields.items()}


def unquote(path: Path, key: str, value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except ValueError:
            error(path, f"«{key}»: строка в двойных кавычках не читается")
    return value


def check_plugin() -> tuple[str | None, str | None]:
    path = REPO / ".claude-plugin" / "plugin.json"
    data = load_json(path)
    if data is None:
        return None, None
    name = text_field(path, data, "name")
    if name and not NAME.fullmatch(name):
        error(path, f"name «{name}»: нужны строчные латинские буквы, цифры и дефисы")
    version = text_field(path, data, "version")
    if version and not VERSION.fullmatch(version):
        error(path, f"version «{version}»: нужен вид X.Y.Z")
    text_field(path, data, "description")
    return name, version


def check_marketplace(plugin: str | None, version: str | None) -> None:
    path = REPO / ".claude-plugin" / "marketplace.json"
    data = load_json(path)
    if data is None:
        return
    text_field(path, data, "name")
    owner = data.get("owner")
    if not isinstance(owner, dict):
        error(path, "нет объекта «owner»")
    else:
        text_field(path, owner, "name", "owner: ")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        error(path, "«plugins» — пустой список или его нет")
        return
    for i, entry in enumerate(plugins):
        where = f"plugins[{i}]: "
        if not isinstance(entry, dict):
            error(path, f"{where}должен быть объект")
            continue
        name = text_field(path, entry, "name", where)
        source = entry.get("source")
        if not source:
            error(path, f"{where}нет «source»")
        if source in (".", "./"):
            if name and plugin and name != plugin:
                error(path, f"{where}name «{name}», а в plugin.json — «{plugin}»")
            if "version" in entry and version and entry["version"] != version:
                error(path, f"{where}version «{entry['version']}», "
                            f"а в plugin.json — «{version}»")
        elif isinstance(source, str) and source.startswith("./"):
            if not (REPO / source / ".claude-plugin" / "plugin.json").is_file():
                error(path, f"{where}в {source} нет .claude-plugin/plugin.json")


def check_skill(d: Path) -> str | None:
    path = d / "SKILL.md"
    if not path.is_file():
        error(d, "нет SKILL.md")
        return None
    text = path.read_text(encoding="utf-8")
    fields = frontmatter(path, text)
    if fields is None:
        return None
    name = text_field(path, fields, "name")
    if name:
        if not NAME.fullmatch(name) or len(name) > NAME_MAX:
            error(path, f"name «{name}»: до {NAME_MAX} строчных латинских букв, "
                        "цифр и дефисов")
        if name != d.name:
            error(path, f"name «{name}» не совпадает с папкой «{d.name}»")
    description = text_field(path, fields, "description")
    if description and len(description) > DESCRIPTION_MAX:
        error(path, f"description: {len(description)} знаков, "
                    f"можно не больше {DESCRIPTION_MAX}")

    mentioned = set(SKILL_PATH.findall(text))
    for rel in sorted(mentioned):
        if not (d / rel).exists():
            error(path, f"ссылка на {rel}, а такого файла в скилле нет")
    for ref in sorted((d / "references").glob("*")):
        rel = ref.relative_to(d).as_posix()
        if ref.is_file() and rel not in mentioned:
            error(path, f"{rel} лежит в скилле, но в SKILL.md не упомянут")
    return name


def check_evals(skills: set[str]) -> None:
    path = REPO / "evals" / "evals.json"
    if not path.is_file():
        return
    data = load_json(path)
    if data is None:
        return
    skill = text_field(path, data, "skill_name")
    if skill and skill not in skills:
        error(path, f"skill_name «{skill}»: такого скилла в skills/ нет")
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        error(path, "«evals» — пустой список или его нет")
        return
    seen: dict[str, set] = {"id": set(), "name": set()}
    for i, entry in enumerate(evals):
        where = f"evals[{i}]: "
        if not isinstance(entry, dict):
            error(path, f"{where}должен быть объект")
            continue
        for key in ("id", "name"):
            value = entry.get(key)
            if value is None:
                error(path, f"{where}нет «{key}»")
            elif value in seen[key]:
                error(path, f"{where}{key} «{value}» повторяется")
            else:
                seen[key].add(value)
        text_field(path, entry, "prompt", where)
        text_field(path, entry, "expected_output", where)
        assertions = entry.get("assertions")
        if (not isinstance(assertions, list) or not assertions
                or not all(isinstance(a, str) and a.strip() for a in assertions)):
            error(path, f"{where}«assertions» — нужен непустой список строк")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Проверка манифестов плагина, SKILL.md и evals.json.")
    ap.add_argument("--tag", help="тег релиза; должен быть v + version из plugin.json")
    args = ap.parse_args()

    plugin, version = check_plugin()
    check_marketplace(plugin, version)
    skill_dirs = sorted(p for p in (REPO / "skills").glob("*") if p.is_dir())
    if not skill_dirs:
        error(REPO / "skills", "нет ни одного скилла")
    skills = {name for name in map(check_skill, skill_dirs) if name}
    check_evals(skills)
    if args.tag and version and args.tag != f"v{version}":
        error(REPO / ".claude-plugin" / "plugin.json",
              f"version {version}, а тег — {args.tag}; нужен v{version}")

    if errors:
        print(f"ОШИБКИ ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"Замечаний нет: плагин {plugin} v{version}, скиллов {len(skills)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
