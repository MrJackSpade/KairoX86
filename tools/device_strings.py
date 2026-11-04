"""The card options' texts as KairoX86's own strings (KairoX86#207).

86Box's cards describe their options (a label and the names of its choices) in English. The words
among them are KairoX86 string resources, translated like every other: values/strings_86box.xml and
its copies, and X86DeviceStrings.kt, the generated map from 86Box's English to each resource. The
rest (products, chips, addresses, versions) reads the same in every language and is shown as 86Box
writes it. The words are those 86Box's own translation template marks (86box.pot) and those in
tools/device_strings_words.txt.

  python tools/device_strings.py generate <all options.json>
      the English resources and the map, from the core's "all options" hardware query
      (core/test/hardware_query <ROM set> "all options", on the device or the host)
  python shared/tools/translations.py sync
      each language's copy, with its EN comments
  python tools/device_strings.py fill
      each language's translations: 86Box's own (third_party/86box-languages/<lang>.po), else
      tools/device_strings_translations.json, else a size made from UNITS
"""
import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "kairox86/src/main/res"
NAME = "strings_86box.xml"
KOTLIN = ROOT / "kairox86/src/main/java/com/mrjackspade/kairox86/X86DeviceStrings.kt"
LANGUAGES = ROOT / "third_party/86box-languages"
WORDS = ROOT / "tools/device_strings_words.txt"
TRANSLATIONS = ROOT / "tools/device_strings_translations.json"
# KairoX86's languages, by their values-<qualifier>, and 86Box's file for each it has.
PO = {"de": "de-DE", "es": "es-ES", "ja": "ja-JP", "ko": "ko-KR", "pt-rBR": "pt-BR", "ru": "ru-RU", "ar": None, "in": None}
# A size ("4 MB") in each language.
UNITS = {"ru": {"KB": "КБ", "MB": "МБ"}, "ar": {"KB": "كيلوبايت", "MB": "ميغابايت"}}
SIZE = re.compile(r"^(\d+) (KB|MB)$")


def parse_po(path):
    """msgid -> msgstr for every entry with a translation (86Box's files have no plurals or contexts)."""
    entries, current, field, parts = {}, {}, None, []

    def end_field():
        if field is not None:
            current[field] = "".join(parts)

    for raw in path.read_text(encoding="utf-8").splitlines() + [""]:
        line = raw.strip()
        if line.startswith('"') and field is not None:
            parts.append(ast.literal_eval(line))
            continue
        end_field()
        field, parts = None, []
        if (line.startswith("msgid ") or not line) and current.get("msgid") and current.get("msgstr"):
            entries[current["msgid"]] = current["msgstr"]
        if line.startswith("msgid "):
            current = {}
        if line.startswith("msgid ") or line.startswith("msgstr "):
            field, rest = line.split(" ", 1)
            parts = [ast.literal_eval(rest)]
    return entries


def template():
    return {ast.literal_eval(line[6:].strip()) for line in (LANGUAGES / "86box.pot").read_text(encoding="utf-8").splitlines()
            if line.startswith('msgid "')}


def words():
    return [line.rstrip("\n") for line in WORDS.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]


def option_texts(dump):
    """Every option label and every choice name that is not a bare number."""
    texts = set()
    for card in json.loads(Path(dump).read_text(encoding="utf-8")):
        for option in card["options"]:
            texts.add(option["label"])
            texts.update(choice["label"] for choice in option["choices"] if choice["label"] and not choice["label"].isdigit())
    return texts


def resource_name(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40].rstrip("_")
    return f"d86_{slug}_{hashlib.sha1(text.encode('utf-8')).hexdigest()[:6]}"


def escape(text):
    """A string resource's text: XML's and aapt's escapes."""
    out = text.replace("\\", "\\\\").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = out.replace("'", "\\'").replace('"', '\\"')
    if out[:1] in ("@", "?"):
        out = "\\" + out
    return out


def generate(dump):
    available = option_texts(dump)
    chosen = template() & available
    missing = [w for w in words() if w not in available]
    if missing:
        raise SystemExit(f"{WORDS.name} names texts no card option shows: {missing}")
    chosen |= set(words())
    texts = sorted(chosen, key=lambda t: resource_name(t))
    for text in texts:
        if "%" in text or "--" in text:
            raise SystemExit(f"cannot keep {text!r} as a string resource with an EN comment")
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             "<!-- The words of 86Box's card options (KairoX86#207), written by tools/device_strings.py generate. -->",
             "<resources>"]
    lines += [f'    <string name="{resource_name(t)}">{escape(t)}</string>' for t in texts]
    lines += ["</resources>", ""]
    (RES / "values" / NAME).write_text("\n".join(lines), encoding="utf-8")
    entries = ",\n".join(f"        {json.dumps(t, ensure_ascii=False)} to R.string.{resource_name(t)}" for t in texts)
    KOTLIN.write_text(f"""package com.mrjackspade.kairox86

// Written by tools/device_strings.py generate: do not edit.

/**
 * The words of 86Box's card options (KairoX86#207): 86Box's English for each, to the string resource
 * that translates it. A text not here is a name or a value and reads as 86Box writes it.
 */
object X86DeviceStrings {{
    val resources: Map<String, Int> = mapOf(
{entries}
    )
}}
""", encoding="utf-8")
    print(f"{len(texts)} texts of {len(available)} are words")


def translation(language, english, po, mine):
    theirs = po.get(english)
    if theirs and theirs != english:
        return theirs
    if english in mine:
        return mine[english]
    size = SIZE.match(english)
    if size:
        return f"{size.group(1)} {UNITS.get(language, {}).get(size.group(2), size.group(2))}"
    raise SystemExit(f"no {language} translation of {english!r}: add it to {TRANSLATIONS.name}")


def fill():
    by_name = {resource_name(text): text for text in map_texts()}
    mine_all = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    for language, po_name in PO.items():
        path = RES / f"values-{language}" / NAME
        if not path.is_file():
            raise SystemExit(f"{path} is missing: run shared/tools/translations.py sync first")
        po = parse_po(LANGUAGES / f"{po_name}.po") if po_name else {}
        mine = mine_all[language]
        text = path.read_text(encoding="utf-8")

        def put(match):
            name = match.group(1)
            return f'<string name="{name}">{escape(translation(language, by_name[name], po, mine))}</string>'

        path.write_text(re.sub(r'<string name="([^"]+)">(.*?)</string>', put, text), encoding="utf-8")
        print(f"{language}: {len(by_name)} translated")


def map_texts():
    """The English texts the generated map holds."""
    return [json.loads(line.split(" to R.string.")[0].strip()) for line in KOTLIN.read_text(encoding="utf-8").splitlines()
            if " to R.string." in line]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate").add_argument("dump")
    sub.add_parser("fill")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.dump)
    else:
        fill()


if __name__ == "__main__":
    sys.exit(main())
