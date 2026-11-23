# Reproducibility Guide

This document provides complete step-by-step instructions to reproduce the boiling point model comparison experiment.

## 1. Getting the Artifact

This workspace is published as part of a public GitHub repository. To reproduce:

```bash
git clone <repository-url>
cd <repository-folder>/round-1/experiment-1/src
```

## 2. System Requirements

- **Operating System**: Ubuntu 22.04+ / macOS 13+ / Windows 11 with WSL2
- **Python**: 3.12+ (tested with 3.12)
- **Memory**: 2 GB RAM minimum
- **Disk**: 100 MB free space

## 3. Environment Setup

### 3.1 Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This installs the exact pinned versions from `pyproject.toml`:
- numpy==2.2.6
- pandas==2.3.3
- scipy==1.16.3
- matplotlib==3.10.7
- loguru==0.7.3
- jsonschema==4.25.1

### 3.3 Verify Installation

```bash
python -c "import numpy, pandas, scipy, matplotlib, loguru, jsonschema; print('All packages imported successfully')"
```

## 4. Data

The dataset `boiling_point_field_data.csv` is included in this workspace. It contains 51 concurrent meteorological records with:
- Altitude (m): 0 to 5000m in 100m increments
- Station pressure (Pa)
- Temperature (°C)
- Relative humidity (%)
- Measured boiling point (°C)

No external downloads or API keys are required.

## 5. Running the Experiment

### 5.1 Main Experiment

```bash
uv run method.py
```

Or using the venv directly:
```bash
.venv/bin/python method.py
```

**Expected runtime**: ~2 seconds on a modern CPU.

### 5.2 Expected Output

The script produces:
- Console output with metrics table
- `results/exp_gen_sol_out.json` - Full results in experiment schema format
- `results/full_method_out.json` - Copy of full results
- `results/mini_method_out.json` - First 3 examples only
- `results/preview_method_out.json` - First 3 examples with truncated strings
- `results/predictions.csv` - All predictions in CSV format
- `logs/run.log` - Detailed execution log

### 5.3 Key Metrics to Verify

| Model | RMSE (°C) | MAE (°C) | Bias (°C) | R² |
|-------|-----------|----------|-----------|-----|
| ISA Baseline | 0.205 | 0.158 | -0.064 | 0.998 |
| Humidity-Corrected | 1.450 | 1.009 | -0.974 | 0.911 |
| Local Pressure-Corrected | 0.685 | 0.547 | 0.547 | 0.980 |

Paired t-tests (all p < 0.001, significant):
- Humidity vs ISA: t ≈ 6.47
- Pressure vs ISA: t ≈ 8.86
- Pressure vs Humidity: t ≈ -5.13

## 6. Generating Figures

Figures are generated using the `aii-data-fig-gen` skill. The chart specs are in `figures/*.json`. To regenerate:

```bash
# Requires aii-data-fig-gen skill environment
python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec figures/fig1_metrics_bar.json --out figures/fig1_metrics_bar
python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec figures/fig2_predictions_vs_altitude.json --out figures/fig2_predictions_vs_altitude
python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec figures/fig3_error_boxplot.json --out figures/fig3_error_boxplot
python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec figures/fig4_scatter_agreement.json --out figures/fig4_scatter_agreement
python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec figures/fig5_panel.json --out figures/fig5_panel
```

Generated files: `.pdf` (vector, for publication) and `.png` (for viewing).

## 7. Validating Output Schema

```bash
python -c "
import json
from jsonschema import validate
with open('results/exp_gen_sol_out.json') as f:
    data = json.load(f)
with open('/path/to/aii-json/schemas/exp_gen_sol_out.json') as f:
    schema = json.load(f)
validate(instance=data, schema=schema)
print('Schema validation passed')
"
```

## 8. Independent Audit Script

Run the independent verification script to re-derive all headline metrics:

```bash
.venv/bin/python audit_metrics.py
```

This script reads raw prediction data and recomputes metrics through a separate code path.

## 9. Hardware Used

- **CPU**: Apple M-series (M1/M2/M3) or x86_64
- **RAM**: 16 GB (experiment uses <100 MB)
- **GPU**: Not required (CPU-only computation)
- **Runtime**: ~2 seconds

## 10. Output Files for Paper

| File | Purpose |
|------|---------|
| `results/exp_gen_sol_out.json` | Main results data |
| `figures/fig1_metrics_bar.pdf` | Performance metrics comparison (Figure 1) |
| `figures/fig2_predictions_vs_altitude.pdf` | Predictions across altitude (Figure 2) |
| `figures/fig3_error_boxplot.pdf` | Error distributions (Figure 3) |
| `figures/fig4_scatter_agreement.pdf` | Measured vs predicted agreement (Figure 4) |
| `figures/fig5_panel.pdf` | Multi-panel summary (Figure 5) |

## 11. Troubleshooting

### Matplotlib Font Cache Warning
First run may show "Matplotlib is building the font cache" - this is normal and only happens once.

### Schema Validation Fails
Ensure you're using the correct schema path from the aii-json skill.

### Import Errors
Verify all dependencies are installed: `pip install -e .`

## 12. Contact

For issues reproducing this experiment, check the logs in `logs/run.log` for detailed execution trace.