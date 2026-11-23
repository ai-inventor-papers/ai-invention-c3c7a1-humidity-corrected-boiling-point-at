# Kinetic Boiling Model Evaluation

This artifact evaluates the performance of boiling point models at altitude using synthetic field measurements across 20 sites at altitudes 0-5000m.

## Artifact Summary

Validates the Kinetic Effect Model (ISA + nucleation superheat) against held-out synthetic data to confirm its superior performance and quantify minor effect magnitudes.

## Files

- `eval.py` - Evaluation script that computes metrics and statistical tests
- `full_eval_out.json` - Complete evaluation results (exp_eval_sol_out schema)
- `mini_eval_out.json` - First 3 examples for quick testing
- `preview_eval_out.json` - Truncated preview for inspection
- `full_method_out.json` - Original experiment output (copied from dependency)
- `field_data.json` - Original field data (copied from dependency)
- `results.json` - Original results (copied from dependency)
- `fig1_metrics.json` - Chart spec for metrics comparison bar chart
- `fig2_scatter.json` - Chart spec for predicted vs measured scatter plot
- `fig3_errors.json` - Chart spec for errors vs altitude line chart
- `fig4_bp_vs_alt.json` - Chart spec for boiling point vs altitude comparison
- `figures/` - Generated publication-quality figures (PDF + PNG)
  - `fig1_metrics.pdf/png` - Model performance metrics comparison (RMSE, MBE, MAE)
  - `fig2_scatter.pdf/png` - Predicted vs measured boiling points
  - `fig3_errors.pdf/png` - Model errors vs altitude
  - `fig4_bp_vs_alt.pdf/png` - Boiling point vs altitude for all models

## Key Results

| Model | RMSE (°C) | MBE (°C) | MAE (°C) |
|-------|-----------|----------|----------|
| ISA Baseline | 0.651 | -0.523 | 0.538 |
| ISA Measured | 0.659 | -0.532 | 0.550 |
| **Kinetic** | **0.390** | **-0.012** | **0.339** |
| Dissolved Gas | 0.776 | -0.668 | 0.675 |

### Statistical Significance
- Paired t-test (|ISA Baseline| vs |Kinetic|): t=2.140, p=0.0455
- Paired t-test (signed errors, ISA vs Kinetic): t=-30.136, p<0.001
- Cohen's d for absolute error reduction: 0.479 (medium effect)
- Bootstrap 95% CI for RMSE difference (ISA - Kinetic): [0.095, 0.393] °C
- Permutation test p-value: 0.0508

### Effect Magnitudes
- Nucleation superheat effect (ISA → Kinetic bias reduction): ~0.51°C
- Dissolved gas effect (ISA → Gas bias increase): ~0.15°C
- The nucleation effect is the dominant non-ideal effect in typical boiling conditions.

## How to Run

```bash
# Run evaluation script
uv run eval.py

# Regenerate figures
uv run python /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig1_metrics.json --out figures/fig1_metrics
uv run python /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig2_scatter.json --out figures/fig2_scatter
uv run python /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig3_errors.json --out figures/fig3_errors
uv run python /Users/Shared/aii_data/.claude/skills/aii-data-fig-gen/scripts/chart_gen.py --spec fig4_bp_vs_alt.json --out figures/fig4_bp_vs_alt
```

## Dependencies

This artifact depends on:
- `art_FRBlUQwLUgix` (gen_art_experiment_2) - Provides `field_data.json`, `results.json`, `full_method_out.json`

## Reproducibility

All results are derived from the synthetic field measurements in `full_method_out.json`. The evaluation uses:
- Standard metrics: RMSE, MBE, MAE
- Paired t-tests for statistical significance
- Bootstrap confidence intervals
- Permutation test for robustness
- Effect size (Cohen's d) quantification

The figures are generated using `aii-data-fig-gen` for consistent, publication-quality output.