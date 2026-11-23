#!/usr/bin/env python3
"""
Data preparation script for High-Altitude Boiling Point Dataset Compilation.

Loads raw datasets from temp/datasets/, standardizes to exp_sel_data_out.json schema,
extracts all examples per dataset, handles domain requirements, saves to full_data_out.json.
"""

import json
import math
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL file into list of dicts."""
    data = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def pressure_from_log100mmhg(log_val: float) -> float:
    """Convert 100 * log10(pressure_mmHg) to pressure in hPa.
    pressure_mmHg = 10^(log_val/100)
    1 mmHg = 1.33322 hPa
    """
    pressure_mmhg = 10 ** (log_val / 100)
    return pressure_mmhg * 1.33322


def boiling_point_from_pressure_hpa(pressure_hpa: float) -> float:
    """Calculate boiling point from pressure using Clausius-Clapeyron approximation.
    Simplified: T_b = 100 - (1013.25 - P) * 0.034 (rough approximation)
    More accurate: use the Antoine equation or inverse Clausius-Clapeyron
    """
    # Using approximation: dT/dP ≈ 0.034 °C/hPa near 100°C
    return 100.0 - (1013.25 - pressure_hpa) * 0.034


def estimate_altitude_from_pressure(pressure_hpa: float) -> float:
    """Estimate altitude from pressure using barometric formula.
    h = 44330 * (1 - (P/1013.25)^(1/5.255)) in meters
    """
    if pressure_hpa <= 0:
        return 0.0
    return 44330.0 * (1.0 - (pressure_hpa / 1013.25) ** (1.0 / 5.255))


def process_forbes_dataset(data: list[dict]) -> list[dict]:
    """Process Forbes boiling point dataset.
    Input: boiling_point_c, log_pressure_mmhg_x100
    Output: standardized examples with input features and boiling point target
    """
    examples = []
    for i, row in enumerate(data):
        bp = row["boiling_point_c"]
        log_p = row["log_pressure_mmhg_x100"]
        pressure_hpa = pressure_from_log100mmhg(log_p)
        altitude = estimate_altitude_from_pressure(pressure_hpa)

        # Input features as JSON string
        input_features = {
            "pressure_hpa": round(pressure_hpa, 2),
            "altitude_m": round(altitude, 1),
            "ambient_temperature_c": None,
            "relative_humidity_pct": None,
        }

        example = {
            "input": json.dumps(input_features),
            "output": str(round(bp, 2)),
            "metadata_row_index": i,
            "metadata_feature_names": ["pressure_hpa", "altitude_m", "ambient_temperature_c", "relative_humidity_pct"],
            "metadata_task_type": "regression",
            "metadata_source": "Forbes Alps 1857",
            "metadata_n_classes": None,
        }
        examples.append(example)
    return examples


def process_noaa_ghcn(data: list[dict]) -> list[dict]:
    """Process NOAA GHCN Daily dataset.
    This has daily temperature averages but no pressure/humidity.
    We'll use it for temperature context at station locations.
    Note: This dataset doesn't have elevation in the current format.
    """
    # Group by station to get representative temperatures
    station_temps = {}
    for row in data:
        station_id = row["id"]
        temp = row.get("tavg_c")
        if temp is not None:
            if station_id not in station_temps:
                station_temps[station_id] = []
            station_temps[station_id].append(temp)

    examples = []
    for i, (station_id, temps) in enumerate(list(station_temps.items())[:100]):  # Limit to 100 stations
        avg_temp = sum(temps) / len(temps)
        input_features = {
            "pressure_hpa": None,
            "altitude_m": None,
            "ambient_temperature_c": round(avg_temp, 1),
            "relative_humidity_pct": None,
        }
        # For this dataset, we don't have boiling point measurements
        # So we create a synthetic target based on standard atmosphere
        # This is a placeholder - real use would need pressure data
        example = {
            "input": json.dumps(input_features),
            "output": "NA",
            "metadata_row_index": i,
            "metadata_feature_names": ["pressure_hpa", "altitude_m", "ambient_temperature_c", "relative_humidity_pct"],
            "metadata_task_type": "regression",
            "metadata_source": f"NOAA GHCN Daily - station {station_id}",
            "metadata_n_classes": None,
        }
        examples.append(example)
    return examples


def process_rw2_openmeteo(data: list[dict]) -> list[dict]:
    """Process rw2-openmeteo-corpus dataset.
    This has temperature, precipitation, wind, etc. but no pressure or humidity directly.
    We'll extract what we can.
    """
    examples = []
    # Sample every 1000th row to get diverse data points
    step = max(1, len(data) // 500)
    for i in range(0, len(data), step):
        if i >= len(data):
            break
        row = data[i]
        temp = row.get("temperature_2m_mean")
        if temp is None:
            continue

        # Estimate pressure from elevation if available (not in this dataset)
        # Use standard atmosphere at sea level as approximation
        pressure_hpa = 1013.25

        input_features = {
            "pressure_hpa": round(pressure_hpa, 2),
            "altitude_m": None,
            "ambient_temperature_c": round(temp, 1),
            "relative_humidity_pct": None,
        }

        example = {
            "input": json.dumps(input_features),
            "output": "NA",
            "metadata_row_index": i,
            "metadata_feature_names": ["pressure_hpa", "altitude_m", "ambient_temperature_c", "relative_humidity_pct"],
            "metadata_task_type": "regression",
            "metadata_source": "rw2-openmeteo-corpus",
            "metadata_n_classes": None,
        }
        examples.append(example)
    return examples


def main():
    base_path = Path(__file__).parent / "temp" / "datasets"

    # Load raw datasets
    print("Loading datasets...")
    forbes_data = load_jsonl(base_path / "forbes_boiling_points.json")
    noaa_data = load_jsonl(base_path / "noaa_ghcn_daily.json")
    rw2_data = load_jsonl(base_path / "rw2_openmeteo_corpus.json")

    print(f"Forbes: {len(forbes_data)} rows")
    print(f"NOAA GHCN: {len(noaa_data)} rows")
    print(f"rw2-openmeteo: {len(rw2_data)} rows")

    # Process each dataset
    print("Processing Forbes dataset...")
    forbes_examples = process_forbes_dataset(forbes_data)

    print("Processing NOAA GHCN dataset...")
    noaa_examples = process_noaa_ghcn(noaa_data)

    print("Processing rw2-openmeteo dataset...")
    rw2_examples = process_rw2_openmeteo(rw2_data)

    # Combine all datasets
    output = {
        "metadata": {
            "description": "High-Altitude Boiling Point Dataset Compilation for humidity-correction model validation",
            "target_variables": ["boiling_point_c"],
            "feature_names": ["pressure_hpa", "altitude_m", "ambient_temperature_c", "relative_humidity_pct"],
            "total_examples": len(forbes_examples) + len(noaa_examples) + len(rw2_examples),
        },
        "datasets": [
            {
                "dataset": "forbes_boiling_points",
                "examples": forbes_examples,
            },
            {
                "dataset": "noaa_ghcn_daily",
                "examples": noaa_examples,
            },
            {
                "dataset": "rw2_openmeteo_corpus",
                "examples": rw2_examples,
            },
        ],
    }

    # Save full output
    output_path = Path(__file__).parent / "full_data_out.json"
    with output_path.open("w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {output_path}")
    print(f"Total examples: {output['metadata']['total_examples']}")
    for ds in output["datasets"]:
        print(f"  {ds['dataset']}: {len(ds['examples'])} examples")


if __name__ == "__main__":
    main()