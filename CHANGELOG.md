# Changelog

Hardware revisions of the BeoGram 4002 RIAA board.

## [Unreleased]

- Fixed misspelled `LCSC PN` fields on K1 and RV1 so they appear in the JLCPCB BOM.
- Repository: switched the licence to CERN-OHL-S v2 (hardware) / CC BY-SA 4.0 (docs). Gerbers are no longer published; BOMs, schematic PDF and renders are built by CI and attached to releases.

## Prototype v2 – SMD (2026)

- Converted to SMD with JLCPCB assembly. The film capacitors are still through-hole and soldered by hand.
- LM317 regulator (30 V → ~24.6 V) on the board.
- Mute relay (Omron G6K-2) with an adjustable unmute delay.
- Manufactured and tested working.

## Prototype v1 (2025)

- First through-hole prototype.
