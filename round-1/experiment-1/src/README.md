# Boiling Point Models Comparison Experiment

This experiment evaluates three models for predicting the boiling point of water at different altitudes against field measurements.

## Models Evaluated

1. **ISA Baseline (Dry Air)**: Uses the International Standard Atmosphere (ISA) dry-air barometric formula to compute pressure at altitude, then converts to boiling point via Clausius-Clapeyron relation.

2. **Humidity-Corrected**: Applies moist-air thermodynamics with virtual temperature correction to the ISA pressure profile, accounting for water vapor's effect on air density and pressure lapse rate.

3. **Local Pressure-Corrected**: Uses directly measured station pressure at each altitude to compute boiling point, representing the "ground truth" pressure condition.

## Dataset

The dataset contains 51 concurrent meteorological records from sea level to 5000m:
- Altitude (m)
- Station pressure (Pa)
- Temperature (°C)
- Relative humidity (%)
- Measured boiling point (°C)

## Results Summary

| Model | RMSE (°C) | MAE (°C) | Bias (°C) | R² |
|-------|-----------|----------|-----------|-----|
| ISA Baseline | 0.205 | 0.158 | -0.064 | 0.998 |
| Humidity-Corrected | 1.450 | 1.009 | -0.974 | 0.911 |
| Local Pressure-Corrected | 0.685 | 0.547 | 0.547 | 0.980 |

**Key Finding**: The simple ISA dry-air baseline outperforms both the humidity-corrected model and the local pressure-corrected model on this dataset. The humidity correction overcompensates, producing a large negative bias.

## Files

- `method.py` - Main implementation with all three models and evaluation
- `boiling_point_field_data.csv` - Input dataset (51 records)
- `method_out.json` - Full results in experiment schema format (51 examples)
- `full_method_out.json` - Full results copy (51 examples)
- `mini_method_out.json` - First 3 examples for quick testing
- `preview_method_out.json` - First 3 examples with truncated strings
- `results/predictions.csv` - Predictions for all models
- `results/exp_gen_sol_out.json` - Full results in experiment schema format
- `results/mini_exp_gen_sol_out.json` - First 3 examples for quick testing
- `results/preview_exp_gen_sol_out.json` - First 3 examples with truncated strings
- `figures/` - Publication-quality charts:
  - `fig1_metrics_bar.pdf/png` - Performance metrics comparison
  - `fig2_predictions_vs_altitude.pdf/png` - Predictions across altitude range
  - `fig3_error_boxplot.pdf/png` - Error distributions
  - `fig4_scatter_agreement.pdf/png` - Measured vs predicted agreement
  - `fig5_panel.pdf/png` - Multi-panel summary figure
- `reproducibility.md` - Complete reproduction guide
- `pyproject.toml` - Pinned dependencies
- `audit_metrics.py` - Independent metric verification script

## Running the Experiment

```bash
uv run method.py
```

## Restoring Removed Files

No files were removed - all results and code are kept in this workspace.