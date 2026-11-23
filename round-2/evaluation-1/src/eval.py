import json
import numpy as np
from scipy import stats
import os

def main():
    with open("full_method_out.json", "r") as f:
        data = json.load(f)
    
    examples = data["datasets"][0]["examples"]
    models = ["isa_baseline", "isa_measured", "kinetic", "gas"]
    
    errors = {m: [] for m in models}
    
    for ex in examples:
        for m in models:
            err_key = f"metadata_err_{m}"
            if err_key in ex:
                errors[m].append(ex[err_key])

    metrics_agg = {}
    
    for m in models:
        errs = np.array(errors[m])
        rmse = float(np.sqrt(np.mean(errs**2)))
        mbe = float(np.mean(errs))
        mae = float(np.mean(np.abs(errs)))
        metrics_agg[f"{m}_RMSE"] = rmse
        metrics_agg[f"{m}_MBE"] = mbe
        metrics_agg[f"{m}_MAE"] = mae
        
    t_stat, p_val = stats.ttest_rel(np.abs(errors["isa_baseline"]), np.abs(errors["kinetic"]))
    metrics_agg["paired_ttest_stat"] = float(t_stat)
    metrics_agg["paired_ttest_pval"] = float(p_val)
    
    eval_output = {
        "metadata": {
            "evaluation_name": "Kinetic Boiling Model Evaluation",
            "description": "Rigorous evaluation of boiling point models using RMSE, MBE, MAE, and paired t-tests."
        },
        "metrics_agg": metrics_agg,
        "datasets": [
            {
                "dataset": "field_measurements_eval",
                "examples": []
            }
        ]
    }
    
    for i, ex in enumerate(examples):
        eval_ex = {
            "input": ex["input"],
            "output": ex["output"]
        }
        for m in models:
            if f"predict_{m}" in ex:
                eval_ex[f"predict_{m}"] = ex[f"predict_{m}"]
            if f"metadata_err_{m}" in ex:
                eval_ex[f"eval_{m}_error"] = float(ex[f"metadata_err_{m}"])
        
        eval_output["datasets"][0]["examples"].append(eval_ex)
        
    with open("full_eval_out.json", "w") as f:
        json.dump(eval_output, f, indent=2)
        
    print("Evaluation complete. Saved to full_eval_out.json")

if __name__ == "__main__":
    main()
