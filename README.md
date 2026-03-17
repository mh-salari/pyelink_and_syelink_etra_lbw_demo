# PyeLink and SyeLink: Open-Source Python Tools for Low-Level EyeLink Experiment Control and Data Parsing

Code, data, and demonstrations for the paper:

> **PyeLink and SyeLink: Open-source Python tools for low-level EyeLink experiment control and data parsing**
> ETRA 2026 Late-Breaking Work

## Overview

This repository contains demonstrations of [PyeLink](https://github.com/mh-salari/pyelink) and [SyeLink](https://github.com/mh-salari/syelink) for controlling EyeLink eye trackers and parsing eye-tracking data.

## Repository Structure

- `dark_light_adaptation.py` — Demonstration of dynamic calibration area adjustment
- `pupil_filtering.py` — Real-time pupil data filtering
- `plot_pupil_demo.py` — Visualization of pupil data
- `data/` — Example eye-tracking data files and parsed outputs

## Data Conversion

The raw EyeLink data file (`data/353_1.edf`) must first be converted to ASCII format using SR Research's `edf2asc` tool, then parsed with SyeLink:

```bash
# 1. Convert EDF to ASC (requires SR Research EyeLink Developers Kit)
edf2asc data/353_1.edf

# 2. Parse ASC file with SyeLink to generate JSON, text, and CSV outputs
uv run syelink convert data/353_1.asc -o data/
```

## Citation

This work has been accepted for publication at ETRA 2026. The DOI will be added when the proceedings are published.

**Cite as:**
```
Salari, M., Nyström, M., Niehorster, D. C., & Bednarik, R. (2026).
PyeLink and SyeLink: Open-source Python tools for low-level EyeLink experiment control and data parsing.
In Proceedings of the 2026 Eye Tracking Research & Applications (ETRA 2026) Late-Breaking Work. ACM.
```

## Acknowledgments

This project has received funding from the European Union's Horizon Europe research and innovation funding program under grant agreement No 101072410, Eyes4ICU project.

<p align="center">
<img src="resources/Funded_by_EU_Eyes4ICU.png" alt="Funded by EU Eyes4ICU" width="500">
</p>

## License

This repository contains code and data accompanying the ETRA 2026 late-breaking work submission.
