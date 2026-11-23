# Kinetic Boiling Point Model Sensitivity Analysis

## Overview

This artifact implements a sensitivity analysis of the kinetic boiling point model using the Forbes 1857 Alpine dataset (17 observations). The study compares thermodynamic baseline models with the kinetic model that accounts for nucleation superheat, and quantifies dissolved gas effects.

## Methods Implemented

### Baseline Models
1. **ISA Pressure Model** (Thermodynamic baseline): Uses Clausius-Clapeyron relation with L/R = 5260 K
2. **Local Pressure Model** (Empirical baseline): Linear approximation around 1 atm

### Our Models
3. **Kinetic Model**: T_boil = T_thermo + ΔT_sat, where ΔT_sat = k × (HeatFlux)^n
   - k = 0.01, n = 0.25 (typical nucleation theory values)
4. **Dissolved Gas Model**: Kinetic model + constant perturbation (-0.1°C)

## Key Results

| Model | RMSE (°C) | MBE (°C) | Pearson r |
|-------|-----------|----------|-----------|
| ISA Pressure Model | 0.298 | +0.080 | 0.9986 |
| Local Pressure Model | 5.043 | +4.600 | 0.9992 |
| Kinetic Model (HF=0) | 0.298 | +0.080 | 0.9986 |
| Dissolved Gas Model | 0.287 | -0.020 | 0.9986 |

**Key Findings:**
- ISA thermodynamic model performs well (RMSE ≈ 0.3°C)
- Local linear model is poor at high altitudes (RMSE ≈ 5°C)
- Dissolved gas correction (-0.1°C) slightly improves RMSE
- Kinetic superheat increases with heat flux: 0.056°C at 1 kW/m² → 0.316°C at 1 MW/m²

## Files

| File | Description |
|------|-------------|
| `method.py` | Main experimental script (production-ready) |
| `results/exp_gen_sol_out.json` | Schema-compliant results |
| `results/charts/fig1.pdf/png` | Boiling point vs pressure comparison (scatter) |
| `results/charts/fig2.pdf/png` | Sensitivity: deviation vs heat flux (log-log line) |
| `results/charts/fig3.pdf/png` | Model comparison: RMSE & |MBE| (panel bar) |
| `results/charts/chart*_spec.json` | Figure specifications |

## How to Run

```bash
# Setup
uv venv .venv --python=3.12
source .venv/bin/activate
uv pip install loguru numpy scipy matplotlib jsonschema

# Run experiment
python method.py

# Generate figures
python /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py \
  --spec results/charts/chart1_spec.json --out results/charts/fig1
# Repeat for chart2, chart3

# Validate output
python /Users/Shared/aii_data/.claude/skills/aii-json/scripts/aii_json_validate_schema.py \
  --format exp_gen_sol_out --file results/exp_gen_sol_out.json
```

## Restoring Removed Files

```bash
# Recreate virtual environment and dependencies
uv venv .venv --python=3.12
source .venv/bin/activate
uv pip install loguru numpy scipy matplotlib jsonschema
```

The `.venv/` directory is excluded from the manifest (regenerable).

## Computational Requirements

- CPU-only (cpu_basic profile)
- ~1 second runtime
- Memory: < 100 MB
- No GPU required