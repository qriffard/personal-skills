#!/usr/bin/env python3
"""
Send the grocery list from a weekly meal plan to Apple Reminders, with
real Reminders tags (filter pills, not text in the title).

Reads from data/plans/<weekStart>.json (the JSON data layer). The plan JSON
already has groceries parsed into groceries[].sections[].items[] arrays.

Routes through a user-defined Shortcut named "Add Tagged Reminder" that
takes a JSON dict with keys `name`, `description`, and `tags` (comma-separated)
and creates a reminder in the "Grocery Shopping" list.

Items are tagged with:
  - Store: #trader-joes / #clement-st (from the store name in the JSON)
  - Category: #produce, #protein, #dairy, #pantry, #frozen, #bakery,
    #drinks (best-effort, classified from the item name only)

Usage:
  grocery_to_reminders.py                 # latest plan
  grocery_to_reminders.py PATH            # specific plan .json file or week slug
  grocery_to_reminders.py --dry-run       # parse + print, don't send
  grocery_to_reminders.py --clear         # wipe target list first
  grocery_to_reminders.py --list NAME     # use a different target list
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

DEFAULT_LIST = "Grocery Shopping"
SHORTCUT_NAME = "Add Tagged Reminder"

# Store name substring → Reminders tag (case-insensitive, first match wins)
STORE_TAGS = {
    "trader joe": "trader-joes",
    "supermarket": "trader-joes",
    "clement street": "clement-st",
    "clement": "clement-st",
}

# Category classifier — order matters; first match wins.
# Patterns matched against ITEM NAME ONLY (before first em-dash or paren), lowercased.
CATEGORY_RULES: list[tuple[str, re.Pattern]] = [
    ("pantry", re.compile(r"\bcoconut milk\b")),
    ("bakery", re.compile(r"\b(bagels?|sourdough|baguettes?|pitas?|crackers?|loaf|loaves|brioche|breads?)\b")),
    ("drinks", re.compile(r"\b(sparkling water|teas?|kombucha|juice|soda|hibiscus)\b")),
    ("frozen", re.compile(r"^frozen\b")),
    ("dairy", re.compile(
        r"\b(yogurts?|ricotta|feta|parmesan|cream cheese|cream|milk|whole-milk|cultured butter|halloumi|mozzarella|chèvre|goat cheese|cheeses?|eggs?|butter)\b"
    )),
    ("protein", re.compile(
        r"\b(chickens?|halibut|salmon|fish|tofu|tempeh|tuna|sausages?|hams?|jambon|prawns?|shrimps?|mackerel|cod|fillets?|ribeyes?|steaks?|beef|pork|porcs?|lamb|veal|duck|turkey|branzino|sea bass)\b"
    )),
    ("produce", re.compile(
        r"\b(asparagus|lemons?|oranges?|fennel|garlic|onions?|shallots?|snap peas|peas?|favas?|beets?|potatoes?|tomatoes?|cucumbers?|radishes?|strawberr(?:y|ies)|bananas?|avocados?|cilantro|parsley|mint|basil|dill|tarragon|thyme|rosemary|chives?|sorrel|ginger|lemongrass|chard|spinach|kale|leeks?|carrots?|celery|peppers?|broccoli|broccolini|cauliflower|squash|mushrooms?|apples?|pears?|melons?|grapes?|figs?|peach(?:es)?|nectarines?|plums?|berries|berry|herbs?|fruits?|veggies?|vegetables?|salad|lettuce|arugula|watercress|spring onions?)\b"
    )),
    ("pantry", re.compile(
        r"\b(pasta|bulgur|rice|farro|quinoa|barley|couscous|oats|noodles?|lentils?|chickpeas?|beans?|seeds?|sumac|paprika|cumin|coriander|turmeric|harissa|mustard|capers?|cornichons?|tahini|miso|soy sauce|vinegars?|olive oil|sesame|honey|salt|spices?|cornstarch|flour|buckwheat|soba|peanut butter|sunflower-seed butter|jarred|canned)\b"
    )),
]


def load_config() -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    # Expand ~ in paths
    for key in ("repo_root", "context_root", "data_root"):
        if key in cfg:
            cfg[key] = str(Path(cfg[key]).expanduser())
    return cfg


def latest_plan_json(data_root: Path) -> Path:
    index_path = data_root / "plans" / "index.json"
    if not index_path.exists():
        sys.exit(f"plans index not found: {index_path}")
    index = json.loads(index_path.read_text())
    if not index:
        sys.exit("plans index is empty")
    latest = sorted(index, key=lambda p: p["weekStart"])[-1]
    return data_root / "plans" / f"{latest['weekStart']}.json"


def split_name_description(item: str) -> tuple[str, str]:
    """Split grocery item into (name, description). Name = before first em-dash or paren."""
    em = re.search(r"\s+—\s+", item)
    paren = re.search(r"\s+\(", item)
    candidates = []
    if em:
        candidates.append(("em", em))
    if paren:
        candidates.append(("paren", paren))
    if not candidates:
        return item.strip(), ""
    kind, m = min(candidates, key=lambda c: c[1].start())
    name = item[: m.start()].strip()
    description = item[m.end():].strip() if kind == "em" else item[m.start():].lstrip()
    return name, description


def name_only(item: str) -> str:
    name, _ = split_name_description(item)
    return name


def classify(item: str) -> str | None:
    text = name_only(item).lower()
    for tag, pattern in CATEGORY_RULES:
        if pattern.search(text):
            return tag
    return None


def clean(item: str) -> str:
    """Strip markdown bold/italic markers."""
    item = re.sub(r"\*\*([^*]+)\*\*", r"\1", item)
    item = re.sub(r"\*([^*]+)\*", r"\1", item)
    # Strip note markers like ★ **freeze immediately on return**
    item = re.sub(r"\s*★\s*\*\*[^*]+\*\*", "", item)
    return item.strip()


def parse_grocery_from_json(plan: dict) -> list[tuple[str, str, list[str]]]:
    """Extract (name, description, tags) tuples from plan JSON groceries array."""
    out: list[tuple[str, str, list[str]]] = []
    for store_entry in plan.get("groceries", []):
        store_name = store_entry.get("store", "").lower()
        store_tag = None
        for marker, tag in STORE_TAGS.items():
            if marker in store_name:
                store_tag = tag
                break
        if not store_tag:
            continue

        for section in store_entry.get("sections", []):
            for raw_item in section.get("items", []):
                cleaned = clean(raw_item)
                if not cleaned:
                    continue
                name, description = split_name_description(cleaned)
                tags = [store_tag]
                cat = classify(cleaned)
                if cat:
                    tags.append(cat)
                out.append((name, description, tags))

    return out


def applescript_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def run_osascript(script: str) -> str:
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"osascript failed: {res.stderr.strip()}")
    return res.stdout.strip()


def shortcut_exists(name: str) -> bool:
    res = subprocess.run(["shortcuts", "list"], capture_output=True, text=True)
    if res.returncode != 0:
        return False
    return any(line.strip() == name for line in res.stdout.splitlines())


def add_reminder_via_shortcut(name: str, description: str, tags: list[str]) -> None:
    payload = json.dumps({"name": name, "description": description, "tags": ",".join(tags)})
    print(payload)
    escaped = applescript_escape(payload)
    script = (
        f'tell application "Shortcuts Events" to '
        f'run shortcut "{SHORTCUT_NAME}" with input "{escaped}"'
    )
    run_osascript(script)


def ensure_list(list_name: str) -> None:
    script = f'''
    tell application "Reminders"
        if not (exists list "{applescript_escape(list_name)}") then
            make new list with properties {{name:"{applescript_escape(list_name)}"}}
        end if
    end tell
    '''
    run_osascript(script)


def clear_list(list_name: str) -> None:
    script = f'''
    tell application "Reminders"
        if exists list "{applescript_escape(list_name)}" then
            tell list "{applescript_escape(list_name)}"
                delete (reminders whose completed is false)
            end tell
        end if
    end tell
    '''
    run_osascript(script)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", help="path to a plan .json file (default: latest)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clear", action="store_true", help="wipe target list first")
    parser.add_argument("--list", default=DEFAULT_LIST)
    args = parser.parse_args()

    config = load_config()
    data_root = Path(config["data_root"])

    if args.plan:
        plan_path = Path(args.plan).expanduser()
        if not plan_path.suffix:
            plan_path = data_root / "plans" / f"{args.plan}.json"
    else:
        plan_path = latest_plan_json(data_root)

    if not plan_path.exists():
        sys.exit(f"plan file not found: {plan_path}")

    plan = json.loads(plan_path.read_text())
    print(f"Plan: {plan_path} (week {plan.get('weekStart', '?')})")

    items = parse_grocery_from_json(plan)
    if not items:
        sys.exit("no grocery sections found in plan JSON (check groceries[] array)")

    by_store: dict[str, int] = {}
    by_cat: dict[str | None, int] = {}
    for _, _, tags in items:
        store = tags[0]
        cat = tags[1] if len(tags) > 1 else None
        by_store[store] = by_store.get(store, 0) + 1
        by_cat[cat] = by_cat.get(cat, 0) + 1

    print(f"Found {len(items)} items.")
    print("  By store: " + ", ".join(f"#{k}={v}" for k, v in by_store.items()))
    print("  By category: " + ", ".join(
        f"#{k or 'unclassified'}={v}" for k, v in sorted(by_cat.items(), key=lambda x: -x[1])
    ))

    if args.dry_run:
        print(f"\n--- items that would be sent to {args.list!r} ---")
        for name, description, tags in items:
            desc_part = f" — {description}" if description else ""
            print(f"  [{','.join(tags)}] {name}{desc_part}")
        return 0

    if not shortcut_exists(SHORTCUT_NAME):
        sys.exit(
            f"Shortcut {SHORTCUT_NAME!r} not found.\n"
            "See ~/.claude/skills/meal-planner/references/groceries-to-reminders.md for setup."
        )

    ensure_list(args.list)
    if args.clear:
        print(f"Clearing {args.list!r}…")
        clear_list(args.list)

    print(f"Adding {len(items)} item(s) to {args.list!r} via Shortcut {SHORTCUT_NAME!r}…")
    for i, (name, description, tags) in enumerate(items, 1):
        add_reminder_via_shortcut(name, description, tags)
        if i % 10 == 0:
            print(f"  {i}/{len(items)}…")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
