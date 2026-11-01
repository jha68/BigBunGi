"""Refresh public free-tier availability from Google's pricing tables at build time."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

SOURCE = "https://ai.google.dev/gemini-api/docs/pricing?hl=en"


class PricingTables(HTMLParser):
    def __init__(self):
        super().__init__(); self.section = None; self.heading = False
        self.row = None; self.cell = None; self.rows = {}

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "h2":
            self.section = attr.get("id"); self.heading = True
        if attr.get("id", "").startswith("gemini-"):
            self.section = attr["id"]
        if tag == "tr": self.row = []
        if tag in ("th", "td") and self.row is not None: self.cell = []

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "h2": self.heading = False
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split())); self.cell = None
        if tag == "tr" and self.row is not None:
            if self.section: self.rows.setdefault(self.section, []).append(self.row)
            self.row = None


def availability(html, names):
    parser = PricingTables(); parser.feed(html)
    output = {}
    for name in names:
        rows = parser.rows.get(name, [])
        free_column = None; inputs = []; outputs = []
        for row in rows:
            for i, cell in enumerate(row):
                if re.search(r"free\s+tier", cell, re.I): free_column = i
            if free_column is None or len(row) <= free_column: continue
            label = row[0].lower(); value = row[free_column].lower()
            if "input" in label and "price" in label: inputs.append(value)
            if "output" in label and "price" in label: outputs.append(value)
        # Never infer availability from model-list access or an absent table.
        status = None
        if inputs and outputs:
            if any("free of charge" in x for x in inputs) and any("free of charge" in x for x in outputs): status = True
            elif any("not available" in x for x in inputs + outputs): status = False
        output[name] = {"available": status}
    return output


def main():
    root = Path(__file__).resolve().parent.parent
    prices = json.loads((root/"web/src/gemini-prices.json").read_text())
    html = ""; error = None
    if "--offline" not in sys.argv:
        try:
            with urllib.request.urlopen(urllib.request.Request(SOURCE, headers={"User-Agent":"BigBunGi-pricing-check"}),timeout=25) as response:
                html = response.read().decode("utf-8")
        except Exception as exc: error = type(exc).__name__
    parser = PricingTables(); parser.feed(html)
    names = sorted(set(prices["models"]) | {name for name in parser.rows if name.startswith("gemini-")})
    data = {"source": SOURCE,"checkedAt":datetime.now(timezone.utc).isoformat(),"models":availability(html,names)}
    if error: data["fetchError"] = error
    target = root/"web/public/content/model-access.json"; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    for name,entry in data["models"].items():
        print(f"::notice::Free-tier public availability: {name} = {entry['available']}; source {SOURCE}")


if __name__ == "__main__": main()
