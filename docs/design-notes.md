# Design notes

Theory of operation for the BeoGram 4002 RIAA board. References are for the left channel (1xx). The right channel is the same with 2xx references. All figures are calculated from the schematic values and have **not been measured yet**. Measurements are very welcome.

## Signal path

```
P8 L IN ─ C101 100p ─┬─ C106 10µ ─► U5A (stage 1: 3180/318 µs) ─► R107/R108/C105 (75 µs) ─ C104 2µ ─► U5B (flat ×3.15) ─ C107 10µ ─► K1 (mute) ─► P9 L OUT
                     │              bias: R102/R103 47k/47k to ½ supply
```

### Input

- C101 (100 pF) to ground sets the cartridge capacitive load. Cable capacitance adds to this.
- C106 (10 µF) is the AC coupling cap. The + input is biased at half the supply by R102/R103 (47 k / 47 k).
- **Resistive load:** R102 ∥ R103 ≈ **23.5 kΩ**. The usual moving-magnet / moving-iron load is 47 kΩ, so this is an open point (see the README's known issues).
- **Input high-pass corner:** 10 µF with 23.5 kΩ gives ≈ 0.7 Hz.

### Stage 1 – U5A (3180 µs / 318 µs)

Non-inverting amplifier with feedback Z = R106 + (R105 ∥ C102) to an AC ground through R104 + C103.

| Parameter | Formula | Value | RIAA target |
|---|---|---|---|
| Pole (bass turnover) | R105 · C102 = 80.6 k · 39 n | 3143 µs | 3180 µs |
| Zero | R105·C102 · (R104+R106)/(R104+R105+R106) | ≈ 314 µs | 318 µs |
| Mid-band gain | 1 + R106/R104 | ≈ 17.9 (25 dB) | – |
| LF gain (below 50 Hz) | 1 + (R105+R106)/R104 | ≈ 179 (45 dB) | – |
| DC gain | C103 blocks DC | 1 | – |
| LF corner | R104 · C103 = 499 · 200 µ | ≈ 1.6 Hz | – |

### 75 µs network

- R107 (2.37 k) in series, R108 (54.9 k) to ground, then C105 (33 nF) to ground at the stage 2 input. C104 (2 µF) couples the signal across, since stage 2 has its own half-supply bias (R111/R112).
- **Time constant:** (R107 ∥ R108) · C105 = 2.27 k · 33 n = **75.0 µs**.
- **Flat-band loss:** R108 / (R107 + R108) ≈ 0.96.

### Stage 2 – U5B

- **Gain:** 1 + R109/R110 = 1 + 4.3 k / 2 k ≈ 3.15 (10 dB). C108 (10 µF) makes it unity gain at DC.
- **Output:** C107 (10 µF) couples the output to the mute relay and P9.

### Overall

- **Gain at 1 kHz:** ≈ 34 dB.
- **Output level:** a typical 5 mV/1 kHz cartridge gives ≈ 250 mV out.

## Power supply

- U7 (LM317, TO-263) regulates 30 V from the main board down to `24VDC+`:
  - Vout = 1.25 V · (1 + R19/R20) = 1.25 · (1 + 5600/300) ≈ **24.6 V**
  - Dropout headroom ≈ 5.4 V
- **Protection:** D5 protects against reverse voltage from output to input. D6 discharges the adjust-pin capacitor C30 (10 µF), which improves ripple rejection.
- **Bulk capacitance:** C1, C2, C3 and C31 (4 × 470 µF).
- **Decoupling:** C27, C28 and C32 (100 nF) at the op-amps, and C29 at the regulator input.
- **Single-supply operation:** each op-amp input is biased at about 12.3 V by a 47 k / 47 k divider. The OPA2134 is rated up to 36 V total supply.

## Mute relay

- **How it mutes:** K1 is an Omron G6K-2 (DPDT). Its normally-closed contacts (pins 3 and 6) short L OUT and R OUT to ground. When the coil is energised the contacts open and the signal passes.
- **Coil drive:** the coil runs from the 21 V rail and is switched by Q1 (NPN). D7 is the flyback diode.
- **Turn-on delay:** when `RELAY ON` (P8 pins 1–2) goes high, C33 (100 µF, in series with R21 1 k) charges through R22 (100 k) and RV1 (1 M trimmer). Q1 switches on once its base reaches about 0.6 V, so RV1 sets the unmute delay.
- **Turn-off:** when `RELAY ON` goes low, D8 pulls the base low and discharges C33. The outputs mute immediately.

## Grounding

The schematic uses several ground labels (`GND`, `GND MB`, `GND CHASSIS`, `GND L/R IN PICKUP`, `GND L/R OUT`), but they all connect to one GND net. A star ground or a separate chassis ground could be worth trying if hum turns out to be a problem. Please report hum or noise in a build report.
