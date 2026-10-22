#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build BOMs and assembly files from a KiCad XML netlist and position file.

KiCad's own BOM export skips symbols marked "Exclude from BOM". This project uses
that flag for the parts that are hand soldered after JLCPCB assembly (film
capacitors), so this script reads the netlist instead and writes:

  <out>/RIAA-bom-full.csv    every part, with an "Assembly" column (JLCPCB / Hand)
  <out>/RIAA-bom-jlcpcb.csv  JLCPCB BOM (only parts with an LCSC PN, not excluded)
  <out>/RIAA-cpl-jlcpcb.csv  JLCPCB pick-and-place for the same parts
  <out>/RIAA-bom-pcbway.csv  PCBWay turnkey BOM: every part, by manufacturer part number
  <out>/RIAA-cpl-pcbway.csv  PCBWay centroid: surface-mount parts only

Every part carries "Manufacturer" and "MPN" fields; parts JLCPCB can place also
carry an "LCSC PN".

Usage: make_bom.py <netlist.xml> <positions.csv> <out_dir>
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

# Readable package names for the PCBWay BOM, matched on the footprint name.
PACKAGES = [
    (r"^[RC]_1206_", "1206"),
    (r"^CP_Elec_(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", r"SMD electrolytic \1 x \2 mm"),
    (r"^D_SMA", "SMA (DO-214AC)"),
    (r"^SOT-89-3", "SOT-89-3"),
    (r"^TO-263-2", "TO-263 (D2PAK)"),
    (r"^D8$", "SOIC-8"),
    (r"^C_Rect_L7\.2mm_W4\.5mm_P5\.00mm", "Radial box 7.2 x 4.5 mm, 5 mm pitch"),
    (r"^PinSocket_(\d+)x(\d+)_P2\.54mm_Horizontal", r"Socket \1x\2, 2.54 mm, right angle"),
    (r"^PinSocket_(\d+)x(\d+)_P2\.54mm_Vertical", r"Socket \1x\2, 2.54 mm, vertical"),
    (r"^Relay_DPDT_Omron_G6K-2F-Y", "Omron G6K-2F (SMD)"),
    (r"^Potentiometer_Bourns_3314G", "Bourns 3314G (SMD)"),
]


def ref_key(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def package(footprint):
    name = footprint.split(":")[-1]
    for pattern, label in PACKAGES:
        if re.match(pattern, name):
            return re.sub(pattern + ".*", label, name)
    return name


def is_tht(footprint):
    lib = footprint.split(":")[0]
    return "THT" in lib or lib.startswith("Connector_Pin")


def describe(p):
    """Part description from the reference and footprint (the symbols' own descriptions are generic)."""
    name = p["footprint"].split(":")[-1]
    kind = re.match(r"[A-Za-z]+", p["ref"]).group(0)
    if kind == "C":
        if name.startswith("CP_Elec"):
            return f"Aluminium electrolytic capacitor {p['value']}"
        if name.startswith("C_Rect"):
            return f"Film capacitor {p['value']}"
        return f"Ceramic capacitor {p['value']}"
    if kind in ("U", "Q"):
        return f"{'IC' if kind == 'U' else 'Transistor'} {p['mpn']}"
    if kind == "P":
        return "Female pin header"
    return {"R": "Resistor", "RV": "Trimmer potentiometer", "D": "Rectifier diode",
            "K": "Relay"}.get(kind, kind) + f" {p['value']}"


def read_components(netlist):
    parts = []
    for comp in ET.parse(netlist).getroot().iter("comp"):
        props = {p.get("name"): p.get("value") for p in comp.iter("property")}
        # Net ties are copper on the board, not parts.
        if "dnp" in props or comp.findtext("footprint", "").startswith("NetTie:"):
            continue
        fields = {f.get("name"): (f.text or "") for f in comp.iter("field")}
        parts.append({
            "ref": comp.get("ref"),
            "value": comp.findtext("value", ""),
            "footprint": comp.findtext("footprint", ""),
            "lcsc": fields.get("LCSC PN", "").strip(),
            "manufacturer": fields.get("Manufacturer", "").strip(),
            "mpn": (fields.get("MPN") or fields.get("PN") or "").strip(),
            "datasheet": comp.findtext("datasheet", "").strip(" ~"),
            "hand": "exclude_from_bom" in props,
        })
    return sorted(parts, key=lambda p: ref_key(p["ref"]))


def group(parts, key):
    groups = OrderedDict()
    for p in parts:
        groups.setdefault(key(p), []).append(p)
    return groups.values()


def write_cpl(positions, refs, path):
    with open(positions, newline="") as f, open(path, "w", newline="") as o:
        w = csv.writer(o)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(f):
            if row["Ref"] in refs:
                w.writerow([row["Ref"], row["PosX"] + "mm", row["PosY"] + "mm",
                            row["Side"].capitalize(), row["Rot"]])


def main(netlist, positions, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    parts = read_components(netlist)

    with open(out / "RIAA-bom-full.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Quantity", "Value", "Footprint", "LCSC PN", "Manufacturer",
                    "Manufacturer PN", "Assembly", "Link"])
        for g in group(parts, lambda p: (p["value"], p["footprint"], p["lcsc"], p["mpn"], p["hand"])):
            p = g[0]
            w.writerow([",".join(x["ref"] for x in g), len(g), p["value"],
                        p["footprint"].split(":")[-1], p["lcsc"], p["manufacturer"], p["mpn"],
                        "Hand" if p["hand"] else "JLCPCB", p["datasheet"]])

    jlc = [p for p in parts if not p["hand"] and p["lcsc"]]
    with open(out / "RIAA-bom-jlcpcb.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
        for g in group(jlc, lambda p: (p["value"], p["footprint"], p["lcsc"])):
            p = g[0]
            w.writerow([p["value"], ",".join(x["ref"] for x in g),
                        p["footprint"].split(":")[-1], p["lcsc"]])
    write_cpl(positions, {p["ref"] for p in jlc}, out / "RIAA-cpl-jlcpcb.csv")

    # PCBWay turnkey: they buy every part by manufacturer part number, including the film capacitors.
    with open(out / "RIAA-bom-pcbway.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Line#", "Qty", "Reference Designator", "Manufacturers Name",
                    "Manufacturers Part Number", "Distributors Part Number", "Part Description",
                    "Value", "Package", "Type"])
        for line, g in enumerate(group(parts, lambda p: (p["mpn"], p["footprint"], p["value"])), 1):
            p = g[0]
            w.writerow([line, len(g), ",".join(x["ref"] for x in g), p["manufacturer"], p["mpn"],
                        f"LCSC {p['lcsc']}" if p["lcsc"] else "", describe(p), p["value"],
                        package(p["footprint"]), "THT" if is_tht(p["footprint"]) else "SMD"])
    write_cpl(positions, {p["ref"] for p in parts if not is_tht(p["footprint"])},
              out / "RIAA-cpl-pcbway.csv")

    missing = [p["ref"] for p in parts if not p["mpn"] or not p["manufacturer"]]
    if missing:
        print("warning: no Manufacturer or MPN for: " + ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
