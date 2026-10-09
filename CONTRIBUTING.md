# Contributing

Thanks for your interest in this project. All kinds of help are welcome. You don't need to be an electronics engineer to contribute.

## Ways to help

- **Build reports.** Built a board? Open a *Build report* issue, whether it worked or not. Say which turntable and cartridge you used and include photos if you can.
- **Measurements.** RIAA deviation, noise and THD plots (REW, ARTA, an Audio Precision…) are the most valuable data this project can get. Put them in `measurements/<your-name-or-date>/` with a short README describing your setup.
- **Documentation.** Installation steps, photos, wiring notes for the 4002 / 4004.
- **Design improvements.** Start with an issue or a discussion before you change the schematic or PCB, so we can agree on the approach first.

## Questions and ideas

Use [GitHub Discussions](../../discussions) for questions, build help and ideas. Use issues for concrete bugs, build reports and proposals.

## Working on the KiCad files

- Use **KiCad 10**. Files saved by a newer major version can't be opened by older ones, so please don't upgrade the file format without discussing it first.
- Keep each PR to **one logical change**. A PR that changes component values is much easier to review without an unrelated layout cleanup mixed in.
- Before you open a PR:
  - Run **ERC** and **DRC** and don't add new errors.
  - Update the PCB from the schematic (F8), so the two match.
  - If you add a part, fill in `LCSC PN` (for JLCPCB assembly) or `PN` (manufacturer part number) and a datasheet or shop link.
  - Mark parts that are soldered by hand as *Exclude from BOM*. CI still lists them in the full BOM with `Assembly = Hand`.
- **Screenshots in the PR description.** KiCad diffs are hard to read, so add before/after screenshots of the schematic and PCB areas you changed.
- **Don't commit generated files** (gerbers, zips, BOMs, backups). CI builds them on every PR. You can download them from the workflow run's *fabrication* artifact.
- Put new project-local symbols and footprints in `parts/`, and reference them with `${KIPRJMOD}` paths.

## Continuous integration

Every PR runs the *KiCad* workflow:

- **DRC** with schematic parity. A failure blocks the merge.
- **ERC.** Report-only for now, until the existing ERC issues are fixed.
- **Fabrication outputs:** schematic PDF, gerbers, BOMs, pick-and-place file and 3D renders.

## Releases

Maintainers tag releases as `vMAJOR.MINOR` (e.g. `v0.2`). Pushing a tag makes CI build a draft GitHub release with the fabrication files, which a maintainer reviews and publishes. Each hardware change goes in [CHANGELOG.md](./CHANGELOG.md).

## Licence

By contributing, you agree that your contributions are licensed under the project's licences: CERN-OHL-S v2 for hardware, CC BY-SA 4.0 for documentation and GPL-3.0-or-later for scripts.
