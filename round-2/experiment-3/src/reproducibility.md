# Reproducibility Instructions

This document provides complete step-by-step instructions to reproduce the Kinetic Boiling Point Model Sensitivity Analysis experiment.

## 1. Getting the Artifact

This workspace is published as part of a public GitHub repository. To reproduce:

```bash
# Clone the repository (replace with actual repo URL when published)
git clone <repository-url>
cd <repository-name>/round-2/experiment-3/src
```

## 2. System Requirements

- **Operating System**: Ubuntu 22.04+ (or macOS with Homebrew)
- **Python Version**: 3.12+
- **System Packages**: 
  - `python3.12-venv` (Ubuntu) or Python 3.12 via Homebrew (macOS)
  - `build-essential` (Ubuntu) or Xcode Command Line Tools (macOS)
- **Hardware**: CPU-only (cpu_basic profile), ~100 MB RAM, ~1 second runtime
- **No GPU required**

## 3. Environment Setup

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install exact pinned dependencies (matching pyproject.toml)
pip install numpy==2.2.6 loguru==0.7.3 scipy==1.16.3 matplotlib==3.10.7 jsonschema==4.25.1
```

**Note**: The exact versions are pinned in `pyproject.toml` and should be used for exact reproducibility.

## 4. Running the Experiment

```bash
# Run the main experimental script
python method.py
```

Expected output (abbreviated):
```
00:46:36|INFO   |Loading Forbes 1857 dataset
00:46:36|INFO   |Loaded 17 observations, P range: [70.40, 93.70] kPa
00:46:36|INFO   |Validating ISA Pressure Model (thermodynamic baseline)
00:46:36|INFO   |ISA Model: RMSE=0.2976, MBE=0.0803, r=0.9986
00:46:36|INFO   |Validating Local Pressure Model (empirical baseline)
00:46:36|INFO   |Local Model: RMSE=5.0434, MBE=4.6003, r=0.9992
00:46:36|INFO   |Validating Kinetic Model at zero heat flux (thermodynamic limit)
00:46:36|INFO   |Kinetic Model (HF=0): RMSE=0.2976, MBE=0.0803, r=0.9986
00:46:36|INFO   |Running sensitivity study: heat flux 1e3 to 1e6 W/m^2
00:46:36|INFO   |Sensitivity study complete: 34 heat flux levels
00:46:36|INFO   |Quantifying dissolved gas effect
00:46:36|INFO   |Dissolved Gas Model: RMSE=0.2872, MBE=-0.0197, r=0.9986
00:46:36|INFO   |Saved results to results/exp_gen_sol_out.json
00:46:36|INFO   |Saved chart specs to results/charts/
00:46:36|INFO   |Testing basic functionality
00:46:36|INFO   |ISA model at 1 atm: 100.0000 C (expected ~100.0)
00:46:36|INFO   |Kinetic model at 1 atm, HF=0: 100.0000 C
00:46:36|INFO   |Deviation at HF=1e3: 0.0562 C, at HF=1e6: 0.3162 C
00:46:36|INFO   |All basic tests passed
00:46:36|INFO   |Method execution complete
```

This generates:
- `results/exp_gen_sol_out.json` - Schema-compliant experimental results
- `results/charts/chart1_spec.json`, `chart2_spec.json`, `chart3_spec.json` - Figure specifications

## 5. Generating Figures

Figures are generated using the `aii-data-fig-gen` skill's chart generator:

```bash
# Figure 1: Boiling point vs pressure comparison
python /path/to/aii-data-fig-gen/scripts/chart_gen.py \
  --spec results/charts/chart1_spec.json --out results/charts/fig1

# Figure 2: Sensitivity to heat flux
python /path/to/aii-data-fig-gen/scripts/chart_gen.py \
  --spec results/charts/chart2_spec.json --out results/charts/fig2

# Figure 3: Model comparison panel
python /path/to/aii-data-fig-gen/scripts/chart_gen.py \
  --spec results/charts/chart3_spec.json --out results/charts/fig3
```

Expected output files:
- `results/charts/fig1.pdf`, `fig1.png`
- `results/charts/fig2.pdf`, `fig2.png`
- `results/charts/fig3.pdf`, `fig3.png`

## 6. Validating Output Schema

```bash
python /path/to/aii-json/scripts/aii_json_validate_schema.py \
  --format exp_gen_sol_out --file results/exp_gen_sol_out.json
```

Expected: `Validation PASSED`

## 7. Generating Full/Mini/Preview JSON Variants

```bash
python /path/to/aii-json/scripts/aii_json_format_mini_preview.py \
  --format exp_gen_sol_out --input results/exp_gen_sol_out.json \
  --output-dir results
```

Expected output:
- `results/full_method_out.json` (17 items)
- `results/mini_method_out.json` (3 items)
- `results/preview_method_out.json` (3 items, truncated)

## 8. Expected Output Files and Key Numbers

### Primary Results (`results/exp_gen_sol_out.json`)

The file contains a `datasets` array with one dataset (`forbes_1857_alpine`) containing 17 examples. Each example has:
- `input`: Pressure query
- `output`: Actual and predicted boiling points (JSON string)
- `predict_baseline`: ISA model prediction (string)

### Key Metrics (from method.py output logs)

| Model | RMSE (°C) | MBE (°C) | Pearson r |
|-------|-----------|----------|-----------|
| ISA Pressure Model | 0.2976 | +0.0803 | 0.9986 |
| Local Pressure Model | 5.0434 | +4.6003 | 0.9992 |
| Kinetic Model (HF=0) | 0.2976 | +0.0803 | 0.9986 |
| Dissolved Gas Model | 0.2872 | -0.0197 | 0.9986 |

### Sensitivity Study

- Heat flux range: 1,000 to 1,000,000 W/m² (34 logarithmic steps)
- Mean deviation at 1 kW/m²: 0.0562°C
- Mean deviation at 1 MW/m²: 0.3162°C

### Figure Files

- `results/charts/fig1.pdf/png` - Scatter plot: Forbes data + 4 model curves
- `results/charts/fig2.pdf/png` - Log-log line: Heat flux vs mean superheat deviation
- `results/charts/fig3.pdf/png` - Panel: RMSE bar + |MBE| bar

## 9. Data and Inputs

- **Forbes 1857 Alpine dataset**: 17 historical boiling point measurements (pressure in inches Hg, temperature in Fahrenheit)
- **Source**: Reconstructed from R MASS package (`forbes` dataset)
- **No external downloads required** - data is embedded in `method.py`
- **No API keys required**

## 10. Troubleshooting

### Font warnings (non-fatal)
```
findfont: Failed to find font weight normal for CMU Serif, now using 500.
```
These are matplotlib font fallback warnings and do not affect results.

### Schema validation path errors
If validation fails with "file_path must be under the project directory or /tmp", ensure:
- You are running from the workspace root
- Use absolute paths or `/tmp` for input files

### Missing dependencies
If imports fail, verify all packages in `pyproject.toml` are installed:
```bash
pip install -r requirements.txt  # if requirements.txt exists
# or manually:
pip install numpy==2.2.6 loguru==0.7.3 scipy==1.16.3 matplotlib==3.10.7 jsonschema==4.25.1
```

## 11. Verification Checklist

After running, verify:
- [ ] `results/exp_gen_sol_out.json` exists and is valid JSON
- [ ] Schema validation passes (`Validation PASSED`)
- [ ] `results/full_method_out.json`, `mini_method_out.json`, `preview_method_out.json` exist
- [ ] Three figure PDF/PNG pairs exist in `results/charts/`
- [ ] Console output shows "All basic tests passed"
- [ ] Key metrics match table in Section 8

---

**Note**: This artifact was developed on macOS (Apple Silicon) with Python 3.12. Results should be bit-for-bit identical on Ubuntu with the same pinned dependencies due to deterministic numerical libraries (NumPy, SciPy).