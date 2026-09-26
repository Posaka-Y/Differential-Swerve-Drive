# Central schematic checkpoint - 2026-09-12

Status: REFERENCE-DRAWING CHECKPOINT COMPLETE; ENGINEERING RELEASE INCOMPLETE.

## 2026-09-12 refinement checkpoint

- Monitoring E now uses the purchased Matek `I2C-INA-BM`; the old on-board INA238/external-shunt circuit is retired. J20 is `GND/I2C0_SDA/I2C0_SCL/+5V_SYS`; verify the module's I2C pull-up voltage is 3.3V-safe before connection.
- Power A/B1 now documents TPS259470 internal reverse-polarity protection, `R102/R103/R104=732k/51.1k/221k` UVLO/OVLO divider (typ 4.43V/5.46V), input/output bulk capacitors, FLT pull-up, and PMEG2010EA USB diode-OR parts. SD-25B-5 must be adjusted/locked at 5.00V.
- Safety D now uses the verified LTV-847S pin mapping and two physical 2.2k resistors plus a reverse diode per used input, with 10k output pull-ups. Contactor coil clamp remains intentionally unresolved until the actual contactor release waveform is measured.
- Expansion F/F1 now carries 100R series parts on all external signal paths and 2k2 I2C pull-ups behind normally-open solder jumpers. Activity LED pads are DNP: a direct idle-HIGH UART/CAN tap is not a useful activity indicator.
- Root PDF was re-exported. Root ERC is now 544 violations; this is not a regression accepted for release, but a consequence of the non-electrical global-label reference drawing. Do not waive it—replace reference label boundaries with real connected circuits before ordering.

## Verified progress

- Native root: `central-board.kicad_sch`, now with eight child sheets: Teensy socket, CAN1/2/3, Power A/B1, Safety D, Monitoring E and Expansion F/F1.
- CAN includes real TCAN1051VDRQ1 / ESD2CAN24 symbols, GH3 pair, 100nF decoupling and 120R switched termination.
- Child references use 2xx/3xx/4xx/5xx; UUIDs and instance paths normalized.
- Netlist confirmed CAN TX/RX links to the expected Teensy socket pins, CANH/L to connectors and ESD, and shared GND/GND_CTRL connection.
- Latest native PDF: `output/pdf/CENTRAL_BOARD_MODULAR_REFERENCE_2026-09-12.pdf` (9 pages). All four added sheets open and export with KiCad 10; the root page and added sheet pages were rendered and visually inspected. This remains a reference drawing, NOT an approved drawing or manufacturing input.
- The interrupted module generator was repaired so KiCad can parse its embedded symbols/wires. `POWER_A_B1` now shows `+5V_SYS -> F101 -> D101 -> VIN_TEENSY`; `D102` is `TEENSY_VUSB_PAD -> VIN_TEENSY`. The INA238 input and VBUS nets now pass through the drawn filter nets.
- All 5 pages rendered to `tmp/pdfs/checkpoint-1.png` through `checkpoint-5.png` and inspected. Layout NOT accepted: root labels/revision clip; CAN capacitor labels overlap termination area; socket page needs larger readable layout and pin-number explanation.
- Latest root ERC: 420 violations. This is expected for the new reference sheets because the broad global-label boundary scheme has not been electrically closed and reviewed; it must not be suppressed or treated as release-ready. The first issues include the deliberate `GND`/`GND_CTRL` alias and isolated boundary labels.

## Exact next work

1. Convert the global-label draft into actual reviewed signal paths: Expansion needs its 100R series parts, I2C pull-up jumpers and LED-buffer circuits drawn; do not infer component values.
2. Safety needs an explicit datasheet-verified LTV-847S pin mapping and two physical 2k2 series resistors per used input channel. Monitoring still needs exact shunt/fuse selection. All TVS/eFuse/diode thresholds remain REVIEW/TBD.
3. Close and classify every ERC violation, rather than suppressing them. Remove the GND alias drawing only after selecting the final ground-net naming convention.
4. Correct the pre-existing CAN/Teensy visual-layout issues noted above, then re-render all pages. Normalize refs only after the electrical content is stable; do NOT apply the simple normalizer blindly to multi-unit modules.
5. Fix symbol/footprint library resolution using a native project. Source library: `hardware/lib/DifferentialSwerve.kicad_sym`.

## Tools

- KiCad: `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe`
- Python: `C:/Program Files/KiCad/10.0/bin/python.exe`
- Render dependency: `tmp/pdfs/deps/pymupdf` (insert into sys.path explicitly; bundled Python ignores PYTHONPATH).
- `tools/kicad/normalize-central-reference.py` contains the simple s-expression parser used for normalization.
- Old failed legacy outputs are retained under `failed-legacy/`; they had >800 ERC errors and must not be used as a basis again.

Four specification documents were not edited by this task. No PCB, firmware, or hardware was changed. No new agent should be started merely to rediscover these facts.
