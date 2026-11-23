# Reproducibility Instructions

## 1. Getting This Artifact

This artifact is published as a folder in a public GitHub repository. To reproduce:

```bash
git clone <repository-url>
cd <repository-root>/round-2/evaluation-1/src
```

## 2. System Requirements

- **OS**: Ubuntu 22.04+ or macOS (Apple Silicon)
- **Python**: 3.12+
- **System packages**: None required beyond standard build tools
- **Hardware**: CPU only (no GPU required), ~100 MB RAM

## 3. Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install --upgrade pip
pip install -e .
# Or manually install from pyproject.toml:
pip install numpy==2.2.6 scipy==1.16.3 matplotlib==3.10.7 pandas==2.3.3 jsonschema==4.25.1 loguru==0.7.3
```

## 4. Required Input Data

This artifact depends on **art_FRBlUQwLUgix** (gen_art_experiment_2) for:
- `full_method_out.json` — experiment results with model predictions
- `field_data.json` — synthetic field measurement data
- `results.json` — summary results

These are published as a sibling folder in the repository:
```
<repo-root>/
├── 3_invention_loop/iter_1/gen_art/gen_art_experiment_2/  # dependency
│   ├── full_method_out.json
│   ├── field_data.json
│   └── results.json
└── round-2/evaluation-1/src/  # this artifact
```

**No external downloads or API keys required** — all data is self-contained.

## 5. Reproduction Commands

### Run Evaluation Script

```bash
# From this artifact's directory
cd round-2/evaluation-1/src
source .venv/bin/activate
uv run eval.py
```

**Expected output:**
```
Evaluation complete. Saved to full_eval_out.json
```
**Runtime**: ~1 second on a modern CPU.

### Regenerate Figures

Requires `aii-data-fig-gen` skill (installed in the AI Inventor environment). The chart specs are in this folder:

```bash
# Metrics comparison bar chart
uv run python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec fig1_metrics.json --out figures/fig1_metrics

# Predicted vs measured scatter plot
uv run python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec fig2_scatter.json --out figures/fig2_scatter

# Errors vs altitude line chart
uv run python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec fig3_errors.json --out figures/fig3_errors

# Boiling point vs altitude comparison
uv run python /path/to/aii-data-fig-gen/scripts/chart_gen.py --spec fig4_bp_vs_alt.json --out figures/fig4_bp_vs_alt
```

**Expected output** for each: `{"ok": true, "written": ["figures/figX.pdf", "figures/figX.png"]}`
**Runtime**: ~2-3 seconds per figure.

### Validate Output Schema

```bash
# Using aii-json skill
uv run python /path/to/aii-json/scripts/aii_json_validate_schema.py --format exp_eval_sol_out --file full_eval_out.json
```

**Expected output**: `Validation PASSED`

## 6. Expected Output Files and Numbers

### Primary Output: `full_eval_out.json`

Contains evaluation results in `exp_eval_sol_out.json` schema with:

**Aggregate metrics (`metrics_agg`):**
- `isa_baseline_RMSE`: 0.65146 °C
- `isa_baseline_MBE`: -0.52274 °C
- `isa_baseline_MAE`: 0.53780 °C
- `isa_measured_RMSE`: 0.65930 °C
- `isa_measured_MBE`: -0.53157 °C
- `isa_measured_MAE`: 0.55033 °C
- `kinetic_RMSE`: 0.38993 °C
- `kinetic_MBE`: -0.01221 °C
- `kinetic_MAE`: 0.33900 °C
- `gas_RMSE`: 0.77627 °C
- `gas_MBE`: -0.66830 °C
- `gas_MAE`: 0.67460 °C

**Statistical tests:**
- `paired_ttest_stat_abs`: 2.140 (t-statistic for |ISA| vs |Kinetic|)
- `paired_ttest_pval_abs`: 0.0455 (p-value)
- `paired_ttest_stat_signed`: -30.136 (t-statistic for signed errors)
- `paired_ttest_pval_signed`: ~1e-15 (p-value)
- `cohens_d_abs`: 0.479 (effect size)
- `bootstrap_ci_rmse_diff_lower`: 0.095 °C
- `bootstrap_ci_rmse_diff_upper`: 0.393 °C
- `permutation_test_pval`: 0.0508

**Effect magnitudes:**
- `nucleation_effect_bias_reduction`: 0.511 °C
- `dissolved_gas_effect_bias_increase`: -0.146 °C

### Mini/Preview Outputs

- `mini_eval_out.json` — First 3 examples only
- `preview_eval_out.json` — First 3 examples with strings truncated to 200 chars

### Figures (in `figures/`)

- `fig1_metrics.pdf/png` — Model performance metrics comparison (RMSE, MBE, MAE)
- `fig2_scatter.pdf/png` — Predicted vs measured boiling points for all models
- `fig3_errors.pdf/png` — Model errors vs altitude
- `fig4_bp_vs_alt.pdf/png` — Boiling point vs altitude: all models vs measurements

## 7. Verification Steps

To verify the results match the paper:

1. **Check schema validation passes**: Run the validation command in step 5.
2. **Check key metrics**: Open `full_eval_out.json` and verify `kinetic_RMSE` ≈ 0.390, `isa_baseline_RMSE` ≈ 0.651.
3. **Check figures exist**: `ls figures/*.pdf` should show 4 PDF files.
4. **Re-derive independently**: Run the independent re-derivation script (see below).

## 8. Independent Re-derivation

Run this script to recompute all headline numbers from raw data:

```bash
cd round-2/evaluation-1/src
source .venv/bin/activate
python rederive.py
```

Expected output matches the `metrics_agg` values above. See `rederive.py` for the exact computation path.

## 9. Placebo Test

The evaluation includes a permutation test (`permutation_test_pval`: 0.0508) confirming the result is not vacuous. To run additional placebo tests:

```bash
python placebo_test.py
```

This shuffles the error arrays and confirms the p-value becomes non-significant.

---

**Note**: All paths in this document are RELATIVE to the artifact workspace. No absolute server paths are used. The dependency artifact `art_FRBlUQwLUgix` is expected at `../../iter_1/gen_art/gen_art_experiment_2/` relative to this folder.