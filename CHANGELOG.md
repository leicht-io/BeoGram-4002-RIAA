# Changelog

Hardware revisions of the BeoGram 4002 RIAA board.

## [Unreleased]

### Prototype v3 (designed, not built yet)

- **Hum:** the op-amp inputs are now biased from a filtered half-supply reference per channel (R23–R26, C34, C35) instead of 47 k / 47 k dividers straight from the supply. In simulation, supply ripple at the output drops from +13 dB to −42 dB at 100 Hz. R102, R112, R202 and R212 were removed.
- **Input load:** the cartridge now sees 47 kΩ (R103 / R203) instead of 23.5 kΩ.
- **RIAA accuracy:** stage 2 is DC-coupled to stage 1; C104 / C204 and R111 / R211 were removed. Nothing loads the 75 µs network any more, which removes a +0.7 dB treble error.
- **Regulator headroom:** R19 changed from 5k6 to 4k7, so the LM317 makes 20.8 V instead of 24.6 V. The turntable's 30 V rail is unregulated, and v2 could drop out on a low or rippled rail.
- **Mute relay delay:** Q1 changed from a 2N2222 to a BCV49 Darlington, as on the original B&O board. With a single NPN the relay pulled in late or not at all at long delay settings.
- **Grounding:** the pickup returns (P8 pins 9/10, 13/14) run next to their signal traces and join GND only at the input stage, through net ties NT1 / NT2. The length-tuning meanders on R IN, L OUT and R OUT were removed (length matching does nothing at audio frequencies).
- **Power:** one 470 µF (C1) at the regulator output instead of four; C2, C3, C31 and C32 were removed. C27 / C28 (100 nF) moved from the power section to the supply pins of U5 / U6.
- **Parts:** C103 / C203 are now assembled by JLCPCB, and their value is corrected to 220 µF (the ordered part). R108 / R208 changed to C488896 (1 %), because C870792 is out of stock. Only the six film capacitors are hand-soldered.
- **Stage 1 network:** C102 / C202 are now 33 nF WIMA MKS2, the same part as C105 / C205. WIMA makes no 39 nF. To keep the time constants and gain, R104 / R204 went from 499 Ω to 590 Ω (C870807), R105 / R205 from 80.6 k to 95.3 k (C274048), and R106 / R206 from 8.45 k to 10 k (C136889). The old 499 Ω part was nearly out of stock.
- Teardrops and copper zones are rebuilt for the new routing.
- **PCBWay turnkey:** every part now has `Manufacturer` and `MPN` fields (schematic and board). CI builds `RIAA-bom-pcbway.csv` and `RIAA-cpl-pcbway.csv` next to the JLCPCB files, and attaches them to releases. The film capacitors have full WIMA part numbers (FKP2D001001D00JSSD, MKS2C023301A00JSSD) instead of series names and Mouser links.
- **README:** new board render, and a simulated RIAA response chart made by `scripts/riaa_response.py`.
- The OPA2134 footprint now has a 3D model (KiCad's SOIC-8).
- ERC is clean (no-connect flags, PWR_FLAGs), and CI now fails on ERC errors. Net ties are left out of the BOM.
- The silkscreen says "Prototype v3". The board file is saved with KiCad 10 and no longer opens in KiCad 9.

### Repository

- Fixed misspelled `LCSC PN` fields on K1 and RV1 so they appear in the JLCPCB BOM.
- KiCad 10's local history folder (`.history/`) is ignored.
- Switched the licence to CERN-OHL-S v2 (hardware) / CC BY-SA 4.0 (docs). Fabrication files are now built by CI and attached to releases instead of being committed.

## Prototype v2 – SMD (2026)

- Converted to SMD with JLCPCB assembly. The film capacitors are still through-hole and soldered by hand.
- LM317 regulator (30 V → ~24.6 V) on the board.
- Mute relay (Omron G6K-2) with an adjustable unmute delay.
- Manufactured and tested working.

## Prototype v1 (2025)

- First through-hole prototype.
