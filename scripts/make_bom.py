#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build BOM and JLCPCB assembly files from a KiCad XML netlist and position file.

KiCad's own BOM export skips symbols marked "Exclude from BOM". This project uses
that flag for the parts that are hand soldered after JLCPCB assembly (film
capacitors etc.), so this script reads the netlist instead and writes:

  <out>/RIAA-bom-full.csv   every part, with an "Assembly" column (JLCPCB / Hand)
  <out>/RIAA-bom-jlcpcb.csv JLCPCB BOM (only parts with an LCSC PN, not excluded)
  <out>/RIAA-cpl-jlcpcb.csv JLCPCB pick-and-place for the same parts

Usage: make_bom.py <netlist.xml> <positions.csv> <out_dir>
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path


def ref_key(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def read_components(netlist):
    parts = []
    for comp in ET.parse(netlist).getroot().iter("comp"):
        props = {p.get("name"): p.get("value") for p in comp.iter("property")}
        if "dnp" in props:
            continue
        fields = {f.get("name"): (f.text or "") for f in comp.iter("field")}
        parts.append({
            "ref": comp.get("ref"),
            "value": comp.findtext("value", ""),
            "footprint": comp.findtext("footprint", ""),
            "lcsc": fields.get("LCSC PN", "").strip(),
            "mpn": fields.get("PN", "").strip(),
            "datasheet": comp.findtext("datasheet", "").strip(" ~"),
            "hand": "exclude_from_bom" in props,
        })
    return sorted(parts, key=lambda p: ref_key(p["ref"]))


def group(parts, key):
    groups = OrderedDict()
    for p in parts:
        groups.setdefault(key(p), []).append(p)
    return groups.values()


def main(netlist, positions, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    parts = read_components(netlist)

    with open(out / "RIAA-bom-full.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Quantity", "Value", "Footprint", "LCSC PN",
                    "Manufacturer PN", "Assembly", "Link"])
        for g in group(parts, lambda p: (p["value"], p["footprint"], p["lcsc"], p["mpn"], p["hand"])):
            p = g[0]
            w.writerow([",".join(x["ref"] for x in g), len(g), p["value"],
                        p["footprint"].split(":")[-1], p["lcsc"], p["mpn"],
                        "Hand" if p["hand"] else "JLCPCB", p["datasheet"]])

    smt = [p for p in parts if not p["hand"] and p["lcsc"]]
    with open(out / "RIAA-bom-jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
        for g in group(smt, lambda p: (p["value"], p["footprint"], p["lcsc"])):
            p = g[0]
            w.writerow([p["value"], ",".join(x["ref"] for x in g),
                        p["footprint"].split(":")[-1], p["lcsc"]])

    smt_refs = {p["ref"] for p in smt}
    with open(positions, newline="") as f, open(out / "RIAA-cpl-jlcpcb.csv", "w", newline="") as o:
        w = csv.writer(o)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(f):
            if row["Ref"] in smt_refs:
                w.writerow([row["Ref"], row["PosX"] + "mm", row["PosY"] + "mm",
                            row["Side"].capitalize(), row["Rot"]])

    missing = [p["ref"] for p in parts if not p["lcsc"] and not p["mpn"]]
    if missing:
        print("warning: no LCSC PN or PN for: " + ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
