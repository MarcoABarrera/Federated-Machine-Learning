# run_noniid_labelgroups_debug.py
import subprocess
import re
import csv
from datetime import datetime
import json
import os

# -----------------------------------------
# CONFIGURATION
# -----------------------------------------
num_clients = 4               # fixed because we have 4 label groups
seeds = [0, 1, 2, 3, 4]       # multiple seeds
num_server_rounds = 10
output_csv_summary = "results_noniid_labelgroups_summary_debug.csv"
output_csv_rounds = "results_noniid_labelgroups_rounds_debug.csv"
output_csv_classes = "results_noniid_labelgroups_classes_debug.csv"
flwr_executable = "flwr"      # or full path if necessary

# -----------------------------------------
# Regex helpers (wider coverage)
# -----------------------------------------
re_cen_acc_block = re.compile(r"cen_accuracy['\"]?\s*:\s*\[(.*?)\]", re.S)
re_cen_acc_single = re.compile(r"cen_accuracy['\"]?\s*[:=]\s*([0-9]*\.?[0-9]+)", re.I)
re_acc_points = re.compile(r"\(\s*(\d+)\s*,\s*([0-9]*\.?[0-9]+)\s*\)")
re_round_loss = re.compile(r"round\s+(\d+)\s*:\s*([0-9]*\.?[0-9]+)", re.I)
re_eval_line = re.compile(r"evaluate.*?loss.*?([\d\.]+).*?accuracy.*?([\d\.]+)", re.I)
re_client_classes = re.compile(r"Client\s+(\d+)\s+has\s+classes:\s*(\[.*?\])\s*\(counts=(\{.*?\})\)")

# -----------------------------------------
# Storage
# -----------------------------------------
summary_results = []
round_results = []
class_distributions = []

# -----------------------------------------
# Helper to save a short debug snippet
# -----------------------------------------
def debug_snippet(text, n=400):
    if not text:
        return ""
    return text[:n] + ("\n...\n" + text[-n:] if len(text) > n*2 else "")

# -----------------------------------------
# Main experiment loop
# -----------------------------------------
for seed in seeds:
    print(f"\n🚀 Running NON-IID label-group experiment | clients={num_clients} | seed={seed} ...")

    cmd = [
        flwr_executable, "run", ".",
        "--federation-config",
        f'{{"federation": "local-simulation", "options.num-supernodes": {num_clients}}}',
        "--run-config",
        f'{{"num-server-rounds": {num_server_rounds}, "seed": {seed}}}',
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout for seed={seed}")
        summary_results.append({
            "timestamp": datetime.now().isoformat(),
            "num_clients": num_clients,
            "seed": seed,
            "num_rounds": num_server_rounds,
            "status": "timeout",
            "final_accuracy": None,
            "final_loss": None,
            "error": "timeout",
        })
        continue

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    rc = proc.returncode

    # Save raw log
    log_filename = f"flwr_noniid_labelgroups_seed_{seed}.log"
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write(output)

    # Print returncode for debug
    print(f"Process returncode: {rc}")

    # ---- Parse label distribution printed by your task.py ----
    found_classes = False
    for match in re_client_classes.findall(output):
        found_classes = True
        client_id, class_list, class_counts = match
        class_distributions.append({
            "num_clients": num_clients,
            "seed": seed,
            "client_id": int(client_id),
            "classes": class_list,
            "counts": class_counts,
        })
    if not found_classes:
        print("⚠️ Warning: No client class distribution lines found in logs. Check client print block.")

    # ---- Handle failed runs ----
    if rc != 0:
        err_summary = (proc.stderr or proc.stdout or "")[:800]
        print("❗ flwr returned non-zero exit code. Stderr/Stdout snippet:")
        print(debug_snippet(err_summary))
        summary_results.append({
            "timestamp": datetime.now().isoformat(),
            "num_clients": num_clients,
            "seed": seed,
            "num_rounds": num_server_rounds,
            "status": "failed",
            "final_accuracy": None,
            "final_loss": None,
            "error": err_summary,
        })
        continue

    # ---- Per-round accuracy: try multiple extraction strategies ----
    round_accs = []
    # First: block-style cen_accuracy
    m = re_cen_acc_block.search(output)
    if m:
        block = m.group(1)
        for r, val in re_acc_points.findall(block):
            round_accs.append((int(r), float(val)))

    # Second: single-line cen_accuracy occurrences
    if not round_accs:
        for m2 in re_cen_acc_single.finditer(output):
            try:
                v = float(m2.group(1))
                # unknown round -> set to -1; we'll treat as final
                round_accs.append((-1, v))
            except Exception:
                pass

    # Third: look for evaluate lines
    if not round_accs:
        for m3 in re_eval_line.finditer(output):
            try:
                loss_v = float(m3.group(1))
                acc_v = float(m3.group(2))
                round_accs.append((-1, acc_v))
            except Exception:
                pass

    # ---- Per-round loss ----
    round_losses = []
    for r, val in re_round_loss.findall(output):
        round_losses.append((int(r), float(val)))

    # ---- Check results.json (if written by strategy) as a fallback ----
    fallback_acc = None
    if os.path.exists("results.json"):
        try:
            with open("results.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            # data is dict round->metrics
            if data:
                last_round = max(int(k) for k in data.keys())
                metrics = data[str(last_round)]
                # metrics might contain 'accuracy' or 'cen_accuracy'
                fallback_acc = metrics.get("cen_accuracy") or metrics.get("accuracy")
                if fallback_acc is not None:
                    round_accs.append((last_round, float(fallback_acc)))
        except Exception as e:
            print("⚠️ Failed to read results.json:", e)

    # ---- Combine both ----
    round_map = {}
    for r, acc in round_accs:
        if r == -1:
            r = num_server_rounds  # guess final round
        round_map.setdefault(r, {})["accuracy"] = acc
    for r, loss in round_losses:
        round_map.setdefault(r, {})["loss"] = loss

    for r, vals in sorted(round_map.items()):
        round_results.append({
            "num_clients": num_clients,
            "seed": seed,
            "round": r,
            "accuracy": vals.get("accuracy"),
            "loss": vals.get("loss"),
        })

    final_acc = round_accs[-1][1] if round_accs else None
    final_loss = round_losses[-1][1] if round_losses else None

    if final_acc is None:
        print("⚠️ Could not parse final accuracy from logs. Here is a stdout/stderr snippet:")
        print(debug_snippet(output, n=800))

    print(f"✅ Finished seed={seed} | Final acc={final_acc}, loss={final_loss}")

    summary_results.append({
        "timestamp": datetime.now().isoformat(),
        "num_clients": num_clients,
        "seed": seed,
        "num_rounds": num_server_rounds,
        "status": "ok",
        "final_accuracy": final_acc,
        "final_loss": final_loss,
        "error": None,
    })

# -----------------------------------------
# Write CSV outputs
# -----------------------------------------
with open(output_csv_summary, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "timestamp", "num_clients", "seed", "num_rounds",
        "status", "final_accuracy", "final_loss", "error"
    ])
    writer.writeheader()
    writer.writerows(summary_results)

with open(output_csv_rounds, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "num_clients", "seed", "round", "accuracy", "loss"
    ])
    writer.writeheader()
    writer.writerows(round_results)

with open(output_csv_classes, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "num_clients", "seed", "client_id", "classes", "counts"
    ])
    writer.writeheader()
    writer.writerows(class_distributions)

print("\n📊 Saved CSVs:")
print(" -", output_csv_summary)
print(" -", output_csv_rounds)
print(" -", output_csv_classes)
