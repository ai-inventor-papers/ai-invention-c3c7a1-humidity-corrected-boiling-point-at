# Reproducibility Guide

This document provides complete step-by-step instructions to reproduce the boiling point model comparison experiment results.

## 1. Getting the Artifact

This workspace is published as part of a public GitHub repository. To get started:

```bash
# Clone the repository (replace with actual repo URL when published)
git clone https://github.com/ai-inventor/ai-inventor.git
cd ai-inventor/round-1/experiment-2/src
```

## 2. System Requirements

- **Operating System**: Ubuntu 22.04+ or macOS 13+ (Apple Silicon)
- **Python**: 3.12+
- **Memory**: Minimum 4 GB RAM
- **Disk**: ~100 MB for dependencies and outputs

### System Packages (Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    build-essential \
    libfreetype6-dev pkg-config
```

## 3. Environment Setup

### Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install exact pinned versions from pyproject.toml
pip install numpy==2.2.6 loguru==0.7.3 jsonschema==4.25.1 matplotlib==3.10.7 scipy==1.16.3 pandas==2.3.3
```

Or use the pyproject.toml directly:

```bash
pip install -e .
```

## 4. Data and Model Downloads

**No external data downloads required.** The experiment uses synthetic field data generated locally with a fixed seed (42) for reproducibility.

**No API keys or environment variables required.** All computations are local.

## 5. Reproduction Steps

Run the following commands in order from the experiment directory:

### Step 1: Generate Synthetic Field Data

```bash
python3 generate_data.py
```

**Expected output**: Creates `field_data.json` with 20 sites at altitudes 0-5000m.
**Runtime**: < 1 second

### Step 2: Run the Experiment

```bash
python3 method.py
```

**Expected output**: 
- Prints model performance metrics table
- Creates `results.json` (exp_gen_sol_out format)
- Creates `raw_results.json` (per-site errors and metrics)
**Runtime**: < 2 seconds

**Expected console output**:
```
=== Model Performance Metrics ===
isa_baseline   : RMSE=0.651°C, MBE=-0.523°C, MAE=0.538°C, N=20
isa_measured   : RMSE=0.659°C, MBE=-0.532°C, MAE=0.550°C, N=20
kinetic        : RMSE=0.390°C, MBE=-0.012°C, MAE=0.339°C, N=20
gas            : RMSE=0.776°C, MBE=-0.668°C, MAE=0.675°C, N=20
```

### Step 3: Generate Figures

```bash
# Figure 1: Model errors vs altitude
python3 /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig1_errors_vs_altitude.json --out figures/fig1_errors_vs_altitude

# Figure 2: RMSE/MBE comparison
python3 /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig2_metrics_comparison.json --out figures/fig2_metrics_comparison

# Figure 3: Predicted vs measured scatter
python3 /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig3_predicted_vs_measured.json --out figures/fig3_predicted_vs_measured

# Figure 4: Boiling point vs altitude
python3 /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig4_bp_vs_altitude.json --out figures/fig4_bp_vs_altitude
```

**Expected output**: Each command creates a `.pdf` and `.png` in `figures/`
**Runtime**: ~2-3 seconds per figure

### Step 4: Validate Output Format

```bash
python3 -c "
import json
from jsonschema import validate
with open('/Users/Shared/aii_data/.claude/skills/aii-json/schemas/exp_gen_sol_out.json') as f:
    schema = json.load(f)
with open('results.json') as f:
    data = json.load(f)
validate(instance=data, schema=schema)
print('SCHEMA VALIDATION: PASSED')
"
```

**Expected output**: `SCHEMA VALIDATION: PASSED`

## 6. Expected Output Files and Key Numbers

After running all steps, verify these files exist and contain the expected values:

### Primary Results (`results.json`)

| Metric | ISA Baseline | ISA (Measured P) | Kinetic Model | Dissolved Gas |
|--------|--------------|------------------|---------------|---------------|
| **RMSE (°C)** | 0.651 | 0.659 | **0.390** | 0.776 |
| **MBE (°C)** | -0.523 | -0.532 | **-0.012** | -0.668 |
| **MAE (°C)** | 0.538 | 0.550 | **0.339** | 0.675 |

### In Paper/Report

These numbers appear in:
- **Results section**: Model performance comparison table
- **Figure 1**: Error vs altitude line chart showing kinetic model tracks closest to zero
- **Figure 2**: Bar chart comparing RMSE and |MBE| across models
- **Figure 3**: Scatter plot of predicted vs measured boiling points (kinetic model closest to diagonal)
- **Figure 4**: Boiling point vs altitude showing all models with measured data points

### Figure Files

All figures in `figures/` directory:
- `fig1_errors_vs_altitude.pdf/.png` - Model errors vs altitude
- `fig2_metrics_comparison.pdf/.png` - RMSE/MBE bar chart
- `fig3_predicted_vs_measured.pdf/.png` - Predicted vs measured scatter
- `fig4_bp_vs_altitude.pdf/.png` - Boiling point vs altitude

## 7. Hardware Used

- **Device**: Apple Silicon Mac (MPS/CPU)
- **Python**: 3.12
- **No GPU required** - all computations run on CPU
- **Approximate total runtime**: < 15 seconds

## 8. Verification Checklist

After reproduction, confirm:

- [ ] `field_data.json` exists with 20 sites
- [ ] `results.json` passes schema validation
- [ ] Console output matches expected metrics table (within floating-point precision)
- [ ] 4 figure PDFs and PNGs generated in `figures/`
- [ ] `raw_results.json` contains per-site errors for all 4 models

## 9. Troubleshooting

### Matplotlib Font Cache Warning
First run may show "Matplotlib is building the font cache; this may take a moment." - this is normal.

### Schema Validation Fails
Ensure you're using the correct schema path. The validation script expects the schema at the aii-json skill location.

### Import Errors
If `ModuleNotFoundError`, ensure all dependencies from pyproject.toml are installed in the active virtual environment.

### Permission Errors on Chart Gen Script
The chart_gen.py script requires execution permission. If needed:
```bash
chmod +x /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py
```

---

**Note**: This experiment uses synthetic data generated with a fixed seed (42). Results are fully deterministic and should match exactly.