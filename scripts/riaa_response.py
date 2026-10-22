#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Simulate the RIAA response of one channel and write it as an SVG chart.

A small AC nodal analysis of the schematic values (op-amps modelled with the
OPA2134's 120 dB open-loop gain and 8 MHz gain-bandwidth, ideal 0-ohm source,
47 kOhm amplifier input). It plots the v3 response and the deviation from the
RIAA curve for v3 and, for comparison, the v2 board.

Usage: riaa_response.py <out.svg>
"""
import math
import sys


class Circuit:
    def __init__(self):
        self.nodes = {"0": 0}
        self.items = []

    def node(self, name):
        return self.nodes.setdefault(name, len(self.nodes))

    def R(self, a, b, r):
        self.items.append(("Y", self.node(a), self.node(b), lambda w, r=r: 1 / r))

    def C(self, a, b, c):
        self.items.append(("Y", self.node(a), self.node(b), lambda w, c=c: 1j * w * c))

    def V(self, a, b, v):
        self.items.append(("V", self.node(a), self.node(b), v))

    def opamp(self, plus, minus, out):
        self.items.append(("E", self.node(plus), self.node(minus), self.node(out)))

    def solve(self, f):
        """Node voltages at frequency f (modified nodal analysis, Gaussian elimination)."""
        w = 2 * math.pi * f
        n = len(self.nodes) - 1
        size = n + sum(1 for i in self.items if i[0] in "VE")
        A = [[0j] * size for _ in range(size)]
        z = [0j] * size

        def add(i, j, v):
            if i and j:
                A[i - 1][j - 1] += v

        k = n
        for item in self.items:
            if item[0] == "Y":
                _, a, b, y = item
                y = y(w)
                add(a, a, y); add(b, b, y); add(a, b, -y); add(b, a, -y)
            elif item[0] == "V":
                _, a, b, v = item
                if a: A[a - 1][k] += 1; A[k][a - 1] += 1
                if b: A[b - 1][k] -= 1; A[k][b - 1] -= 1
                z[k] = v
                k += 1
            else:
                _, p, m, o = item
                gain = 1e6 / (1 + 1j * f / 8.0)          # 120 dB, 8 MHz GBW
                A[o - 1][k] += 1
                A[k][o - 1] += 1
                if p: A[k][p - 1] -= gain
                if m: A[k][m - 1] += gain
                k += 1
        for c in range(size):
            piv = max(range(c, size), key=lambda r: abs(A[r][c]))
            A[c], A[piv] = A[piv], A[c]
            z[c], z[piv] = z[piv], z[c]
            for r in range(c + 1, size):
                if A[r][c]:
                    fac = A[r][c] / A[c][c]
                    for cc in range(c, size):
                        A[r][cc] -= fac * A[c][cc]
                    z[r] -= fac * z[c]
        x = [0j] * size
        for r in range(size - 1, -1, -1):
            x[r] = (z[r] - sum(A[r][cc] * x[cc] for cc in range(r + 1, size))) / A[r][r]
        return {name: (x[i - 1] if i else 0j) for name, i in self.nodes.items()}


def stage1(c, C102, R105, R106, R104, C103):
    """Source, input network and stage 1 (3180/318 us); the + input bias is at AC ground."""
    c.V("IN", "0", 1.0)
    c.C("IN", "P1", 10e-6)                                   # C106
    c.opamp("P1", "N1", "O1")
    c.R("O1", "F1", R106); c.R("F1", "N1", R105); c.C("F1", "N1", C102)
    c.R("N1", "X1", R104); c.C("X1", "0", C103)


def stage2(c, plus, C107, R109, R113=None):
    c.opamp(plus, "N2", "O2")
    c.R("O2", "N2", R109); c.R("N2", "Y2", 2e3); c.C("Y2", "0", 10e-6)    # R109, R110, C108
    if R113:
        c.R("O2", "Q2", R113); c.C("Q2", "OUT", C107)                       # R113, C107
    else:
        c.C("O2", "OUT", C107)                                              # C107
    c.R("OUT", "0", 47e3)                                                   # amplifier input


def v3():
    # C34 and C107 are ceramics with ~10 V DC across them, so they are modelled with the
    # capacitance left at that bias (assumed): 22 uF -> 10 uF, 10 uF -> 4.7 uF.
    c = Circuit()
    c.R("REF", "0", 50e3); c.C("REF", "0", 10e-6)          # VREF: 100k || 100k with C34
    stage1(c, 33e-9, 95.3e3, 10e3, 590, 220e-6)
    c.R("REF", "P1", 47e3)                                  # R103
    c.R("O1", "A1", 2.37e3); c.R("A1", "0", 54.9e3); c.C("A1", "0", 33e-9)   # R107, R108, C105
    stage2(c, "A1", 4.7e-6, 7.5e3, 100)                     # DC-coupled
    return c


def v2():
    c = Circuit()
    stage1(c, 39e-9, 80.6e3, 8.45e3, 499, 220e-6)
    c.R("P1", "0", 23.5e3)                                  # R102 || R103
    c.R("O1", "A1", 2.37e3); c.R("A1", "0", 54.9e3)
    c.C("A1", "P2", 2e-6); c.C("P2", "0", 33e-9); c.R("P2", "0", 23.5e3)    # C104, C105, R111 || R112
    stage2(c, "P2", 10e-6, 4.3e3)
    return c


def riaa(f):
    w = 2 * math.pi * f
    return abs((1 + 1j * w * 318e-6) / ((1 + 1j * w * 3180e-6) * (1 + 1j * w * 75e-6)))


def db(x):
    return 20 * math.log10(abs(x))


def response(circuit, freqs):
    """(relative response re 1 kHz, deviation from RIAA) in dB."""
    ref = abs(circuit.solve(1000)["OUT"])
    rel = [db(abs(circuit.solve(f)["OUT"]) / ref) for f in freqs]
    dev = [r - db(riaa(f) / riaa(1000)) for r, f in zip(rel, freqs)]
    return rel, dev


# ---------------------------------------------------------------------------------- SVG
W, H = 880, 640
LEFT, RIGHT = 72, 112
P1_TOP, P1_H = 96, 220
P2_TOP, P2_H = 384, 150
F_MIN, F_MAX = 20, 20000

STYLE = """
  .surface { fill: var(--surface); }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .axis { stroke: var(--axis); stroke-width: 1; }
  .tick, .label { fill: var(--muted); font-size: 12px; }
  .title { fill: var(--ink); font-size: 18px; font-weight: 600; }
  .subtitle { fill: var(--ink-2); font-size: 13px; }
  .panel { fill: var(--ink); font-size: 13px; font-weight: 600; }
  .end { fill: var(--ink-2); font-size: 12px; }
  .note { fill: var(--muted); font-size: 11px; }
  .line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .s1 { stroke: var(--s1); } .s2 { stroke: var(--s2); }
  .dot1 { fill: var(--s1); } .dot2 { fill: var(--s2); }
  svg { --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
        --grid: #e1e0d9; --axis: #c3c2b7; --s1: #2a78d6; --s2: #eb6834;
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  @media (prefers-color-scheme: dark) {
    svg { --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
          --grid: #2c2c2a; --axis: #383835; --s1: #3987e5; --s2: #d95926; }
  }
"""


def x_of(f):
    return LEFT + (math.log10(f) - math.log10(F_MIN)) / (math.log10(F_MAX) - math.log10(F_MIN)) * (W - LEFT - RIGHT)


def y_of(v, top, height, lo, hi):
    return top + (hi - v) / (hi - lo) * height


def fmt_f(f):
    return f"{f // 1000}k" if f >= 1000 else str(f)


def panel(out, top, height, lo, hi, step, unit_fmt):
    ticks = [f for f in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)]
    v = math.ceil(lo / step - 1e-9) * step                  # gridlines on multiples of the step
    while v <= hi + 1e-9:
        y = y_of(v, top, height, lo, hi)
        cls = "axis" if abs(v) < 1e-9 else "grid"
        out.append(f'<line class="{cls}" x1="{LEFT}" x2="{W - RIGHT}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="tick" x="{LEFT - 8}" y="{y + 4:.1f}" text-anchor="end">{unit_fmt(v)}</text>')
        v += step
    for f in ticks:
        x = x_of(f)
        out.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + height}"/>')
        out.append(f'<text class="tick" x="{x:.1f}" y="{top + height + 18}" text-anchor="middle">{fmt_f(f)}</text>')


def path(freqs, values, top, height, lo, hi):
    pts = " ".join(f"{x_of(f):.1f},{y_of(v, top, height, lo, hi):.1f}" for f, v in zip(freqs, values))
    return f"M{pts.replace(' ', ' L')}"


def write_svg(fname, freqs, rel3, dev3, dev2):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-labelledby="t d">',
         '<title id="t">Simulated RIAA response of the BeoGram 4002 RIAA board</title>',
         '<desc id="d">Top: v3 response relative to 1 kHz, from +19 dB at 20 Hz to -20 dB at 20 kHz. '
         'Bottom: deviation from the RIAA curve, within 0.1 dB from 50 Hz to 20 kHz for v3; '
         'v2 rises to +0.7 dB at 10 to 20 kHz.</desc>',
         f"<style>{STYLE}</style>",
         f'<rect class="surface" width="{W}" height="{H}" rx="8"/>',
         f'<text class="title" x="{LEFT - 40}" y="36">Simulated RIAA response</text>',
         f'<text class="subtitle" x="{LEFT - 40}" y="58">One channel, nominal part values, '
         f'ideal source, 47 kΩ amplifier input. Not measured yet.</text>']

    # Panel 1: v3 response
    o.append(f'<text class="panel" x="{LEFT}" y="{P1_TOP - 14}">Response relative to 1 kHz (dB), v3</text>')
    panel(o, P1_TOP, P1_H, -25, 25, 10, lambda v: f"{v:+.0f}" if v else "0")
    o.append(f'<path class="line s1" d="{path(freqs, rel3, P1_TOP, P1_H, -25, 25)}"/>')

    # Panel 2: deviation from RIAA, v2 vs v3
    o.append(f'<text class="panel" x="{LEFT}" y="{P2_TOP - 14}">Deviation from the RIAA curve (dB)</text>')
    lo, hi = -1.0, 1.0
    panel(o, P2_TOP, P2_H, lo, hi, 0.5, lambda v: f"{v:+.1f}" if abs(v) > 1e-9 else "0")
    o.append(f'<path class="line s2" d="{path(freqs, dev2, P2_TOP, P2_H, lo, hi)}"/>')
    o.append(f'<path class="line s1" d="{path(freqs, dev3, P2_TOP, P2_H, lo, hi)}"/>')
    for cls, dev, name in (("dot2", dev2, "v2"), ("dot1", dev3, "v3")):
        x, y = x_of(freqs[-1]), y_of(dev[-1], P2_TOP, P2_H, lo, hi)
        o.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
        o.append(f'<text class="end" x="{x + 10:.1f}" y="{y + 4:.1f}">{name} {dev[-1]:+.2f} dB</text>')
    # Legend (two series): line keys, text in ink
    lx = W - RIGHT - 250
    for i, (cls, name) in enumerate((("s1", "v3 (this design)"), ("s2", "v2 (as built)"))):
        ly = P2_TOP - 18
        x0 = lx + i * 140
        o.append(f'<line class="line {cls}" x1="{x0}" x2="{x0 + 18}" y1="{ly - 4}" y2="{ly - 4}"/>')
        o.append(f'<text class="end" x="{x0 + 24}" y="{ly}">{name}</text>')

    o.append(f'<text class="label" x="{(LEFT + W - RIGHT) / 2:.0f}" y="{P2_TOP + P2_H + 40}" '
             f'text-anchor="middle">Frequency (Hz)</text>')
    o.append(f'<text class="note" x="{LEFT - 40}" y="{H - 16}">Generated by scripts/riaa_response.py. '
             f'The roll-off below 50 Hz comes from the coupling capacitors.</text>')
    o.append("</svg>")
    with open(fname, "w") as fh:
        fh.write("\n".join(o) + "\n")


def main(out):
    freqs = [round(20 * 1000 ** (i / 150), 3) for i in range(151)]   # 20 Hz .. 20 kHz, log-spaced
    rel3, dev3 = response(v3(), freqs)
    _, dev2 = response(v2(), freqs)
    write_svg(out, freqs, rel3, dev3, dev2)
    print(f"{'f (Hz)':>7} | {'v3 dev (dB)':>11} | {'v2 dev (dB)':>11}")
    for f in (20, 50, 100, 1000, 10000, 20000):
        _, d3 = response(v3(), [f]); _, d2 = response(v2(), [f])
        print(f"{f:>7} | {d3[0]:>+11.2f} | {d2[0]:>+11.2f}")
    print(f"gain at 1 kHz: {db(v3().solve(1000)['OUT']):.1f} dB (v3), {db(v2().solve(1000)['OUT']):.1f} dB (v2)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
