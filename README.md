# pyelink_and_syelink_etra_lbw_demo

## Data Conversion

The raw EyeLink data file (`data/353_1.edf`) must first be converted to ASCII format using SR Research's `edf2asc` tool, then parsed with SyeLink:

```bash
# 1. Convert EDF to ASC (requires SR Research EyeLink Developers Kit)
edf2asc data/353_1.edf

# 2. Parse ASC file with SyeLink to generate JSON, text, and CSV outputs
uv run syelink convert data/353_1.asc -o data/
```
