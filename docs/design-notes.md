# Design notes

Theory of operation for the BeoGram 4002 RIAA board. References are for the left channel (1xx). The right channel is the same with 2xx references. All figures are calculated or simulated from the schematic values and have **not been measured yet**. Measurements are very welcome.

## Signal path

```
P8 L IN ─ C101 100p ─┬─ C106 10µ ─► U5A (stage 1: 3180/318 µs) ─► R107/R108/C105 (75 µs) ─► U5B (flat ×3.15) ─ C107 10µ ─► K1 (mute) ─► P9 L OUT
                     │              bias: R103 47k from VREF_L                     (DC-coupled)
```

### Input

- C101 (100 pF) to ground sets the cartridge capacitive load. Cable capacitance adds to this.
- C106 (10 µF) is the AC coupling cap. The + input is biased from `VREF_L` through R103 (47 k).
- **Resistive load:** C34 holds `VREF_L` at AC ground, so the cartridge sees R103 = **47 kΩ**, the usual moving-magnet / moving-iron load. (v2 biased the input with a 47 k / 47 k divider straight from the supply, which gave 23.5 kΩ.)
- **Input high-pass corner:** 10 µF with 47 kΩ gives ≈ 0.34 Hz.

### Stage 1 – U5A (3180 µs / 318 µs)

Non-inverting amplifier with feedback Z = R106 + (R105 ∥ C102) to an AC ground through R104 + C103.

| Parameter | Formula | Value | RIAA target |
|---|---|---|---|
| Pole (bass turnover) | R105 · C102 = 95.3 k · 33 n | 3145 µs | 3180 µs |
| Zero | R105·C102 · (R104+R106)/(R104+R105+R106) | ≈ 315 µs | 318 µs |
| Mid-band gain | 1 + R106/R104 = 1 + 10 k / 590 | ≈ 17.9 (25 dB) | – |
| LF gain (below 50 Hz) | 1 + (R105+R106)/R104 | ≈ 179 (45 dB) | – |
| DC gain | C103 blocks DC | 1 | – |
| LF corner | R104 · C103 = 590 · 220 µ | ≈ 1.2 Hz | – |

C102 is 33 nF, the same WIMA MKS2 part as C105. WIMA's 5 mm film series only come in E6 values (33 nF, 47 nF), so v3 scales R104/R105/R106 to keep v2's time constants and gain (v2 had 39 nF with 499 Ω / 80.6 k / 8.45 k).

### 75 µs network

- R107 (2.37 k) in series, then R108 (54.9 k) and C105 (33 nF) to ground. The stage 2 + input connects directly to this node.
- **DC coupling:** stage 1 has a DC gain of 1, so its output sits at `VREF_L`. The R107/R108 node is then at 0.96 · VREF ≈ 10 V, which biases stage 2 without a coupling capacitor or bias resistor.
- **Time constant:** (R107 ∥ R108) · C105 = 2.27 k · 33 n = **75.0 µs**. Nothing else loads the network.
- **Flat-band loss:** R108 / (R107 + R108) ≈ 0.96.
- v2 coupled the stages through C104 and biased stage 2 with a 47 k / 47 k divider. Its 23.5 kΩ loaded R108 and gave ≈ 68 µs, so the treble was about 0.7 dB too high at 10–20 kHz.

### Stage 2 – U5B

- **Gain:** 1 + R109/R110 = 1 + 4.3 k / 2 k ≈ 3.15 (10 dB). C108 (10 µF) makes it unity gain at DC, so the output also sits at ≈ 10 V. DC errors from stage 1 (offset, leakage of C103) pass through at gain 1 and are blocked by C107.
- **Output:** C107 (10 µF) couples the output to the mute relay and P9.

### Overall

- **Gain at 1 kHz:** ≈ 35 dB (simulated with a 47 kΩ amplifier input).
- **Output level:** a typical 5 mV/1 kHz cartridge gives ≈ 275 mV out.
- **RIAA accuracy (simulated):** within ±0.1 dB from 50 Hz to 20 kHz (chart and table in the README; `scripts/riaa_response.py` regenerates them). The response is 0.6 dB down at 20 Hz because of the coupling capacitors, which also act as a gentle subsonic filter. The component tolerances add to this: C102 and C105 are 5 % parts.

## Bias reference

Each channel has its own reference: `VREF_L` = R23 / R24 (100 k / 100 k) from `24VDC+`, with C34 (10 µF) to GND. `VREF_R` uses R25, R26 and C35. VREF sits at half the supply (≈ 10.4 V), and the 0.5 s time constant filters out supply ripple and noise.

This matters because the op-amp + inputs see whatever is on the bias node and amplify it like the signal. Stage 1 has 40–45 dB of gain at 50–100 Hz. Simulated transfer from ripple on `24VDC+` to the output (typical MM cartridge on the input):

| | 50 Hz | 100 Hz |
|---|---|---|
| v2: 47 k / 47 k divider from the supply | +17 dB | +13.5 dB |
| v2, input open or poor cartridge contact | +45 dB | +41 dB |
| v3: filtered reference | −32 dB | −42 dB |

With v2, 1 mV of ripple on the supply gave hum about 43 dB below a 5 mV cartridge's output.

## Power supply

- The turntable's 30 V rail is **not regulated**. It is the output of the bridge rectifier 1D1–1D4 with the 4000 µF reservoir 0C1 (BeoGram 4002 diagram 1), so it carries 100 Hz ripple (120 Hz on 60 Hz mains) and follows the mains voltage. The 21 V rail is regulated by 1IC1 on the main board.
- U7 (LM317, TO-263) regulates the 30 V down to `24VDC+`:
  - Vout = 1.25 V · (1 + R19/R20) = 1.25 · (1 + 4700/300) ≈ **20.8 V**
  - Dropout headroom ≈ 9 V. The LM317 needs about 2–3 V at the bottom of the ripple. v2 made 24.6 V, which left only 5.4 V of headroom. On a low or rippled rail the regulator then drops out and passes the ripple through.
- **Protection:** D5 protects against reverse voltage from output to input. D6 discharges the adjust-pin capacitor C30 (10 µF), which improves ripple rejection.
- **Bulk capacitance:** C1 (470 µF) at the regulator output. The LM317 is stable without an output capacitor; one electrolytic is plenty for its transient response. It doesn't matter for hum: the regulator's output impedance at 100 Hz is milliohms. v2 had four (C1, C2, C3, C31). The other three only made the LM317 run in current limit for longer at power-on, pulling about 1 A from the turntable's 30 V rail.
- **Decoupling:** C27 and C28 (100 nF) sit directly at pin 8 of U5 and U6, each with a ground via. In v2 they were in the power section, about 40 mm of trace away from the op-amps. C29 (100 nF) bypasses the regulator input. (v2 also had C32, 100 nF at the regulator output; C1 and the local decoupling make it unnecessary.)
- **Load:** about 21–25 mA (op-amps 16–20 mA, R19/R20 4 mA). The LM317 dissipates about 0.25 W.
- **Single-supply operation:** the op-amp inputs sit at about 10.4 V (`VREF`). The OPA2134 is rated up to 36 V total supply, and 20.8 V leaves far more output swing than the ~0.3 V signal needs.

## Mute relay

- **How it mutes:** K1 is an Omron G6K-2 (DPDT, 24 V coil, 5.2 kΩ). Its normally-closed contacts (pins 3 and 6) short L OUT and R OUT to ground. When the coil is energised the contacts open and the signal passes.
- **Coil drive:** the coil runs from the 21 V rail and is switched by Q1. D7 is the flyback diode.
- **Turn-on delay:** when `RELAY ON` (P8 pins 1–2) goes high, C33 (100 µF, in series with R21 1 k) charges through R22 (100 k) and RV1 (1 M trimmer). Q1 switches on once its base reaches about 1.2 V. The simulated delay is about 1 s with RV1 at 0 and about 8 s with RV1 at 1 MΩ (for a 17 V `RELAY ON`; longer if `RELAY ON` is lower).
- **Turn-off:** when `RELAY ON` goes low, D8 pulls the base low and discharges C33. The outputs mute immediately.
- **Q1 must be a Darlington.** The circuit is copied from the original B&O PCB 8, which uses 8IC1 = MPSA13 (a Darlington). R22 + RV1 only deliver a few µA to a few tens of µA of base current, and the coil needs about 3–4 mA. v2 used a single NPN (2N2222, gain ≈ 100–300). Above about 300–600 kΩ on RV1 it could not reach the pull-in current reliably, so the relay unmuted late or not at all, depending on the transistor's gain and temperature. v3 uses a BCV49 (gain > 4000), which switches cleanly over the whole RV1 range.

## Grounding

The original B&O PCB 8 kept the pickup returns (P8-5 and P8-7 in B&O numbering) away from the main-board ground. They went only to the DIN socket's ground pin, and the amplifier provided the reference. The cable shields (P8-3) went to the main-board ground.

This board has to join the pickup returns to its own ground, because the preamplifier is powered from the main board. v3 does this deliberately:

- Each pickup return (P8 pins 9/10 and 13/14) is its own net. It runs as a trace right next to its signal trace, so the cartridge loop stays small.
- Each return joins GND at **one** point, the net tie NT1 (NT2) next to the GND pad of C101 (C201) at the input stage.
- Currents in the GND plane (keyboard current through P10, relay coil current, the ground connection to the amplifier through P9) therefore no longer appear in series with the cartridge. In v2 the returns joined the plane at P8, about 60 mm from the op-amps. At 50 Hz every 1 µV between the cartridge return and the input stage's ground gives 0.3 mV of hum at the output.
- P8 pins 3/4 (main-board GND) and 5/6 (cable shields) go to the GND plane, as in the original.
- P10 passes 30 V, 21 V and GND through to the keyboard, as the original module did.

## Hum and ground loops

If a board hums in a particular turntable:

1. **Frequency:** a buzz at twice the mains frequency (100 / 120 Hz) points to supply ripple. Hum at the mains frequency itself (50 / 60 Hz) points to a ground loop or magnetic pickup.
2. **30 V rail:** measure the lowest point of the ripple on P8 pin 17 while playing. Below about 23 V even v3's regulator drops out. Check the turntable's reservoir capacitor (0C1, 4000 µF) and the transformer tap.
3. **Keyboard (P10):** unplug P10 for a test (P8 also supplies 30 V, 21 V and GND; check that the keyboard still works without it). If the hum drops, the loop runs through the keyboard harness.
4. **Pickup returns:** with the board removed, measure between P8 pin 9 (or 13) and pin 3 on the turntable side. The original design keeps them apart. If they read 0 Ω, the turntable joins the pickup return to ground somewhere else (tonearm, cartridge clip, an earlier repair). The board's star point then closes a loop through the tonearm wiring.
5. **Cartridge contact:** a dirty or open contact makes the input high-impedance, and any interference on it is amplified much more.
