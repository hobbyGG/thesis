# IWR1843 + DCA1000EVM Manual Index

TI official documents downloaded for the thesis hardware bring-up.

## Local PDFs

| File | Use |
|---|---|
| `iwr1843_datasheet.pdf` | IWR1843 chip capabilities, interfaces, electrical/RF specs. |
| `xwr1843boost_user_guide_spruim4b.pdf` | IWR1843BOOST/AWR1843BOOST EVM hardware, power, USB, antenna, DCA1000 connection. |
| `iwr1843boost_quick_start_spruio1.pdf` | Quick start for the IWR1843BOOST demo flow. |
| `dca1000evm_user_guide_spruij4a.pdf` | DCA1000EVM hardware, Ethernet, UDP, LVDS streaming, switch settings. |
| `dca1000evm_quick_start_spruik7.pdf` | Quick start for DCA1000EVM capture setup. |
| `mmwave_radar_adc_raw_data_capture_swra581.pdf` | Raw ADC data capture formats and MATLAB parsing examples. |

## Official Links

- IWR1843 datasheet: https://www.ti.com/lit/ds/symlink/iwr1843.pdf
- IWR1843BOOST product page: https://www.ti.com/tool/IWR1843BOOST
- xWR1843BOOST user's guide: https://www.ti.com/lit/ug/spruim4b/spruim4b.pdf
- IWR1843BOOST quick start: https://www.ti.com/lit/pdf/spruio1
- DCA1000EVM product page: https://www.ti.com/tool/DCA1000EVM
- DCA1000EVM user's guide: https://www.ti.com/lit/ug/spruij4a/spruij4a.pdf
- DCA1000EVM quick start: https://www.ti.com/lit/pdf/spruik7
- ADC raw data capture application note: https://www.ti.com/lit/swra581

## Bring-Up Notes

- The capture board name is `DCA1000EVM`, not `DAC1000`.
- IWR1843 exposes a 2-lane LVDS interface for raw ADC data; DCA1000 supports 2-lane and 4-lane LVDS modes.
- DCA1000 default Ethernet settings from the user guide:
  - host/system IP: `192.168.33.30`
  - FPGA IP: `192.168.33.180`
  - config port: `4096`
  - ADC data port: `4098`
- IWR1843BOOST requires a 5 V supply rated above 2.5 A; the supply brick is not included in the kit.
- IWR1843BOOST USB exposes XDS110/JTAG plus UART ports for flashing, Radar/mmWave Studio, and logs.
- For thesis experiments, the likely first path is mmWave Studio + DCA1000EVM raw ADC capture, then parse `.bin` into the existing Python range/angle and phase pipeline.
