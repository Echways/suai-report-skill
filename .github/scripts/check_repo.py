#!/usr/bin/env python3
"""Check the plugin repository: manifests, SKILL.md, evals.json.

  python3 .github/scripts/check_repo.py [--tag vX.Y.Z]

Catches what stops the plugin from installing or the skill from firing:
broken JSON, names that differ between plugin.json, marketplace.json and
SKILL.md, an over-long description, a link to a file the skill lacks.
With --tag it also compares the tag with version in plugin.json.

Exit code: 0 — all good, 1 — errors.
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
        error(path, "file is missing")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        error(path, f"not JSON: {e}")
        return None
    if not isinstance(data, dict):
        error(path, "the top level must be an object")
        return None
    return data


def text_field(path: Path, data: dict, key: str, where: str = "") -> str | None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        error(path, f"{where}no string '{key}'")
        return None
    return value


def frontmatter(path: Path, text: str) -> dict[str, str] | None:
    """The "key: value" fields between two "---" lines; a value may be quoted."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        error(path, "no frontmatter between '---' lines")
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
            error(path, f"'{key}': cannot parse the double-quoted string")
    return value


def check_plugin() -> tuple[str | None, str | None]:
    path = REPO / ".claude-plugin" / "plugin.json"
    data = load_json(path)
    if data is None:
        return None, None
    name = text_field(path, data, "name")
    if name and not NAME.fullmatch(name):
        error(path, f"name '{name}': lowercase Latin letters, digits and hyphens only")
    version = text_field(path, data, "version")
    if version and not VERSION.fullmatch(version):
        error(path, f"version '{version}': must look like X.Y.Z")
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
        error(path, "no 'owner' object")
    else:
        text_field(path, owner, "name", "owner: ")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        error(path, "'plugins' is empty or missing")
        return
    for i, entry in enumerate(plugins):
        where = f"plugins[{i}]: "
        if not isinstance(entry, dict):
            error(path, f"{where}must be an object")
            continue
        name = text_field(path, entry, "name", where)
        source = entry.get("source")
        if not source:
            error(path, f"{where}no 'source'")
        if source in (".", "./"):
            if name and plugin and name != plugin:
                error(path, f"{where}name '{name}', but plugin.json has '{plugin}'")
            if "version" in entry and version and entry["version"] != version:
                error(
                    path,
                    f"{where}version '{entry['version']}', "
                    f"but plugin.json has '{version}'",
                )
        elif isinstance(source, str) and source.startswith("./"):
            if not (REPO / source / ".claude-plugin" / "plugin.json").is_file():
                error(path, f"{where}{source} has no .claude-plugin/plugin.json")


def check_skill(d: Path) -> str | None:
    path = d / "SKILL.md"
    if not path.is_file():
        error(d, "no SKILL.md")
        return None
    text = path.read_text(encoding="utf-8")
    fields = frontmatter(path, text)
    if fields is None:
        return None
    name = text_field(path, fields, "name")
    if name:
        if not NAME.fullmatch(name) or len(name) > NAME_MAX:
            error(
                path,
                f"name '{name}': up to {NAME_MAX} lowercase Latin letters, digits "
                "and hyphens",
            )
        if name != d.name:
            error(path, f"name '{name}' does not match the folder '{d.name}'")
    description = text_field(path, fields, "description")
    if description and len(description) > DESCRIPTION_MAX:
        error(
            path,
            f"description: {len(description)} characters, "
            f"the limit is {DESCRIPTION_MAX}",
        )

    mentioned = set(SKILL_PATH.findall(text))
    for rel in sorted(mentioned):
        if not (d / rel).exists():
            error(path, f"links to {rel}, but the skill has no such file")
    for ref in sorted((d / "references").glob("*")):
        rel = ref.relative_to(d).as_posix()
        if not ref.is_file():
            continue
        if rel not in mentioned:
            error(path, f"{rel} is in the skill but SKILL.md never mentions it")
        # reference files point at each other with the same skill-relative paths
        if ref.suffix == ".md":
            for link in sorted(set(SKILL_PATH.findall(ref.read_text(encoding="utf-8")))):
                if not (d / link).exists():
                    error(ref, f"links to {link}, but the skill has no such file")
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
        error(path, f"skill_name '{skill}': no such skill in skills/")
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        error(path, "'evals' is empty or missing")
        return
    seen: dict[str, set] = {"id": set(), "name": set()}
    for i, entry in enumerate(evals):
        where = f"evals[{i}]: "
        if not isinstance(entry, dict):
            error(path, f"{where}must be an object")
            continue
        for key in ("id", "name"):
            value = entry.get(key)
            if value is None:
                error(path, f"{where}no '{key}'")
            elif value in seen[key]:
                error(path, f"{where}duplicate {key} '{value}'")
            else:
                seen[key].add(value)
        text_field(path, entry, "prompt", where)
        text_field(path, entry, "expected_output", where)
        assertions = entry.get("assertions")
        if (
            not isinstance(assertions, list)
            or not assertions
            or not all(isinstance(a, str) and a.strip() for a in assertions)
        ):
            error(path, f"{where}'assertions' must be a non-empty list of strings")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check the plugin manifests, SKILL.md and evals.json."
    )
    ap.add_argument("--tag", help="release tag; must be v + version from plugin.json")
    args = ap.parse_args()

    plugin, version = check_plugin()
    check_marketplace(plugin, version)
    skill_dirs = sorted(p for p in (REPO / "skills").glob("*") if p.is_dir())
    if not skill_dirs:
        error(REPO / "skills", "no skills")
    skills = {name for name in map(check_skill, skill_dirs) if name}
    check_evals(skills)
    if args.tag and version and args.tag != f"v{version}":
        error(
            REPO / ".claude-plugin" / "plugin.json",
            f"version {version}, but the tag is {args.tag}; expected v{version}",
        )

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"No issues: plugin {plugin} v{version}, skills: {len(skills)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
