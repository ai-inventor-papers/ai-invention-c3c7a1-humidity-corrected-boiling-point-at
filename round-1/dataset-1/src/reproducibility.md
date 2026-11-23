# Reproducibility Instructions

This document describes how to reproduce the High-Altitude Boiling Point Dataset Compilation artifact on Ubuntu.

## 1. Getting the Artifact

```bash
# Clone the repository (replace with actual repo URL when published)
git clone <repository-url>
cd <repository-folder>/round-1/dataset-1/src
```

The artifact workspace is published as one folder of a public GitHub repository. Start from a clone of that repository and `cd` into this folder.

## 2. System Requirements

- **OS**: Ubuntu 22.04 or later
- **Python**: 3.12.x
- **Memory**: At least 8 GB RAM (datasets are loaded in memory during processing)
- **Disk**: At least 2 GB free space for downloaded datasets and outputs

### System Packages

```bash
sudo apt-get update && sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    build-essential \
    git
```

## 3. Environment Setup

### Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies (pinned versions)

```bash
# Upgrade pip
pip install --upgrade pip

# Install from pyproject.toml
pip install -e .

# Or install pinned dependencies directly:
pip install \
    datasets==5.0.1 \
    huggingface_hub==1.1.4 \
    numpy==2.2.6 \
    pandas==2.3.3 \
    jsonschema==4.25.1 \
    loguru==0.7.3
```

**Note**: The exact versions are pinned in `pyproject.toml`. The virtual environment uses the same Python version (3.12) and dependency versions as the original run.

### Environment Variables

No API keys or special environment variables are required for this artifact. All datasets are downloaded from public HuggingFace Hub repositories.

## 4. Data Sources

The following public datasets are downloaded automatically by the script:

1. **Forbes Boiling Points** - Historical dataset (17 rows) from 1857 Alps measurements
   - Source: R package `forbes` / Wolfram Data Repository
   - Downloaded manually and embedded in the script

2. **NOAA GHCN Daily** - Global Historical Climatology Network daily summaries
   - HuggingFace: `ml-project-group-3/NOAA_GHCN_Daily`
   - 460,498 rows (subset of 100 stations used)

3. **rw2-openmeteo-corpus** - Open-Meteo historical weather data
   - HuggingFace: `nakas/rw2-openmeteo-corpus`
   - 1,746,986 rows (sampled to ~500 rows)

All datasets are downloaded to `temp/datasets/` during script execution.

## 5. Execution Steps

Run the data preparation script:

```bash
# From the artifact workspace directory
python data.py
```

### Expected Runtime

- **Dataset downloads**: ~30-60 seconds (depends on network)
- **Processing**: ~10-20 seconds
- **Total**: ~1-2 minutes on a modern CPU

### Hardware Used

- **CPU**: Apple Silicon (M-series) or x86_64
- **Memory**: ~2-4 GB peak during dataset loading
- **No GPU required**

## 6. Expected Outputs

After running `python data.py`, the following files are created in the workspace:

| File | Description | Size |
|------|-------------|------|
| `full_data_out.json` | Complete dataset (618 examples across 3 datasets) | ~327 KB |
| `mini_data_out.json` | First 3 examples per dataset (9 total) | ~5.4 KB |
| `preview_data_out.json` | Mini version with strings truncated to 200 chars | ~5.1 KB |

### Dataset Breakdown

| Dataset | Examples | Description |
|---------|----------|-------------|
| `forbes_boiling_points` | 17 | Historical boiling point vs pressure measurements in the Alps (1857) |
| `noaa_ghcn_daily` | 100 | Daily average temperatures from 100 weather stations |
| `rw2_openmeteo_corpus` | 501 | Sampled historical weather data from Open-Meteo |

### Data Schema (exp_sel_data_out.json)

Each example contains:
- `input`: JSON string with features `{"pressure_hpa", "altitude_m", "ambient_temperature_c", "relative_humidity_pct"}`
- `output`: Target value (boiling point in °C for Forbes; "NA" for others)
- `metadata_*`: Per-example metadata (row index, feature names, task type, source)

### Validation

All output files pass schema validation against `exp_sel_data_out.json`:

```bash
# Validate using the aii-json skill (if available) or manually:
python3 -c "
import json
from jsonschema import validate
with open('/path/to/exp_sel_data_out.json') as f:
    schema = json.load(f)
for fname in ['full_data_out.json', 'mini_data_out.json', 'preview_data_out.json']:
    with open(fname) as f:
        data = json.load(f)
    validate(instance=data, schema=schema)
    print(f'{fname}: PASSED')
"
```

## 7. Verification Checklist

After running, verify:

- [ ] `full_data_out.json` exists and contains 618 examples
- [ ] `mini_data_out.json` exists and contains 9 examples (3 per dataset)
- [ ] `preview_data_out.json` exists and contains 9 examples with truncated strings
- [ ] All three files pass `exp_sel_data_out.json` schema validation
- [ ] `full_data_out.json` is under 100 MB (currently ~327 KB)

## 8. Notes

- The Forbes dataset is small (17 rows) but provides the only actual boiling point measurements at altitude with concurrent pressure data
- The NOAA GHCN and rw2-openmeteo datasets provide temperature context but lack direct pressure/humidity measurements at altitude
- For a complete validation dataset per the artifact plan (500+ points with all variables: altitude, measured_BP, P_ambient, T_ambient, RH), additional data sources would be needed (e.g., mountain observatory station records from PANGAEA, ERA5-Land reanalysis, or direct downloads from meteorological agencies)
- The current compilation demonstrates the data pipeline and schema compliance; downstream tasks can replace the placeholder datasets with more complete sources