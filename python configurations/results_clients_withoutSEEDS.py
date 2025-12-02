#!/usr/bin/env python3
import subprocess
import re
import csv
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
client_counts = [2, 5, 10, 20]
num_server_rounds = 10
output_csv_summary = "results_clients.csv"
output_csv_rounds = "results_rounds.csv"
flwr_executable = "flwr"

# ----------------------
# Regex helpers
# ----------------------
re_cen_acc_block = re.compile(r"cen_accuracy['\"]?\s*:\s*\[(.*?)\]", re.S)
re_acc_points = re.compile(r"\(\s*(\d+)\s*,\s*([0-9]*\.?[0-9]+)\s*\)")
re_round_loss = re.compile(r"round\s+(\d+)\s*:\s*([0-9]*\.?[0-9]+)")

# ----------------------
# Run loop
# ----------------------
summary_results = []
round_results = []

for num_clients in client_counts:
    print(f"\n🚀 Running experiment with {num_clients} clients...")

    cmd = [
        flwr_executable, "run", ".",
        "--federation-config",
        f'{{"federation": "local-simulation", "options.num-supernodes": {num_clients}}}',
        "--run-config",
        f'{{"num-server-rounds": {num_server_rounds}}}',
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        print(f"⏰ Run timed out for {num_clients} clients.")
        summary_results.append({
            "timestamp": datetime.now().isoformat(),
            "num_clients": num_clients,
            "num_rounds": num_server_rounds,
            "status": "timeout",
            "final_accuracy": None,
            "final_loss": None,
            "error": "timeout"
        })
        continue

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    with open(f"flwr_run_{num_clients}.log", "w", encoding="utf-8") as f:
        f.write(output)

    if proc.returncode != 0:
        err_summary = proc.stderr.strip()[:500] or proc.stdout.strip()[:500]
        print(f"❗ flwr failed for {num_clients} clients.")
        summary_results.append({
            "timestamp": datetime.now().isoformat(),
            "num_clients": num_clients,
            "num_rounds": num_server_rounds,
            "status": "failed",
            "final_accuracy": None,
            "final_loss": None,
            "error": err_summary,
        })
        continue

    # ---- Parse per-round accuracies ----
    round_accs = []
    m = re_cen_acc_block.search(output)
    if m:
        block = m.group(1)
        for r, val in re_acc_points.findall(block):
            round_accs.append((int(r), float(val)))

    # ---- Parse per-round losses ----
    round_losses = []
    for r, val in re_round_loss.findall(output):
        round_losses.append((int(r), float(val)))

    # ---- Combine per-round metrics ----
    round_map = {}
    for r, acc in round_accs:
        round_map.setdefault(r, {})["accuracy"] = acc
    for r, loss in round_losses:
        round_map.setdefault(r, {})["loss"] = loss

    for r, vals in sorted(round_map.items()):
        round_results.append({
            "num_clients": num_clients,
            "round": r,
            "accuracy": vals.get("accuracy"),
            "loss": vals.get("loss"),
        })

    final_acc = round_accs[-1][1] if round_accs else None
    final_loss = round_losses[-1][1] if round_losses else None
    print(f"✅ Finished {num_clients} clients: acc={final_acc}, loss={final_loss}")

    summary_results.append({
        "timestamp": datetime.now().isoformat(),
        "num_clients": num_clients,
        "num_rounds": num_server_rounds,
        "status": "ok",
        "final_accuracy": final_acc,
        "final_loss": final_loss,
        "error": None,
    })

# ----------------------
# Write CSVs
# ----------------------
with open(output_csv_summary, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "num_clients", "num_rounds", "status", "final_accuracy", "final_loss", "error"])
    writer.writeheader()
    writer.writerows(summary_results)

with open(output_csv_rounds, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["num_clients", "round", "accuracy", "loss"])
    writer.writeheader()
    writer.writerows(round_results)

print(f"\n📊 Summary saved to {output_csv_summary}")
print(f"📈 Per-round metrics saved to {output_csv_rounds}")
