"""
Run FL experiments varying both number of clients and client participation (fraction_fit).
Saves summary and per-round results in CSVs.
"""

import subprocess
import re
import csv
from datetime import datetime

# ----------------------
# CONFIGURATION
# ----------------------
client_counts = [5, 10, 20]           # number of total clients
fraction_fit_values = [0.2, 0.5, 1.0]  # fraction of clients participating each round
seeds = [0, 1, 2, 3, 4]                     # random seeds for reproducibility
num_server_rounds = 10
flwr_executable = "flwr"              # the Flower CLI command

# Output filenames (timestamped)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
summary_csv = f"results_clients_participation_summary_{timestamp}.csv"
rounds_csv = f"results_clients_participation_rounds_{timestamp}.csv"

# ----------------------
# Regex helpers
# ----------------------
re_cen_acc_block = re.compile(r"cen_accuracy['\"]?\s*:\s*\[(.*?)\]", re.S)
re_acc_points = re.compile(r"\(\s*(\d+)\s*,\s*([0-9]*\.?[0-9]+)\s*\)")
re_round_loss = re.compile(r"round\s+(\d+)\s*:\s*([0-9]*\.?[0-9]+)")

# ----------------------
# Storage
# ----------------------
summary_results = []
round_results = []

# ----------------------
# Experiment loop
# ----------------------
for num_clients in client_counts:
    for frac in fraction_fit_values:
        for seed in seeds:
            print(f"\n🚀 Running {num_clients} clients | fraction_fit={frac} | seed={seed}")

            cmd = [
                flwr_executable, "run", ".",
                "--federation-config",
                f'{{"federation": "local-simulation", "options.num-supernodes": {num_clients}}}',
                "--run-config",
                f'{{"num-server-rounds": {num_server_rounds}, "seed": {seed}, "fraction-fit": {frac}}}',
            ]

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout for {num_clients} clients | fraction_fit={frac} | seed={seed}")
                summary_results.append({
                    "timestamp": datetime.now().isoformat(),
                    "num_clients": num_clients,
                    "fraction_fit": frac,
                    "seed": seed,
                    "status": "timeout",
                    "final_accuracy": None,
                    "final_loss": None,
                    "error": "timeout",
                })
                continue

            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            log_filename = f"flwr_run_{num_clients}c_{frac}frac_seed{seed}.log"
            with open(log_filename, "w", encoding="utf-8") as f:
                f.write(output)

            if proc.returncode != 0:
                err_summary = proc.stderr.strip()[:300] or proc.stdout.strip()[:300]
                print(f"❌ Failed run: {num_clients} clients | frac={frac} | seed={seed}")
                summary_results.append({
                    "timestamp": datetime.now().isoformat(),
                    "num_clients": num_clients,
                    "fraction_fit": frac,
                    "seed": seed,
                    "status": "failed",
                    "final_accuracy": None,
                    "final_loss": None,
                    "error": err_summary,
                })
                continue

            # ---- Parse per-round accuracies ----
            round_accs, round_losses = [], []
            m = re_cen_acc_block.search(output)
            if m:
                for r, val in re_acc_points.findall(m.group(1)):
                    round_accs.append((int(r), float(val)))
            for r, val in re_round_loss.findall(output):
                round_losses.append((int(r), float(val)))

            # Combine
            round_map = {}
            for r, acc in round_accs:
                round_map.setdefault(r, {})["accuracy"] = acc
            for r, loss in round_losses:
                round_map.setdefault(r, {})["loss"] = loss

            for r, vals in sorted(round_map.items()):
                round_results.append({
                    "num_clients": num_clients,
                    "fraction_fit": frac,
                    "seed": seed,
                    "round": r,
                    "accuracy": vals.get("accuracy"),
                    "loss": vals.get("loss"),
                })

            # ---- Final metrics ----
            final_acc = round_accs[-1][1] if round_accs else None
            final_loss = round_losses[-1][1] if round_losses else None
            print(f"✅ Done | acc={final_acc} | loss={final_loss}")

            summary_results.append({
                "timestamp": datetime.now().isoformat(),
                "num_clients": num_clients,
                "fraction_fit": frac,
                "seed": seed,
                "status": "ok",
                "final_accuracy": final_acc,
                "final_loss": final_loss,
                "error": None,
            })

# ----------------------
# Save CSVs
# ----------------------
with open(summary_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "timestamp", "num_clients", "fraction_fit", "seed",
        "status", "final_accuracy", "final_loss", "error"
    ])
    writer.writeheader()
    writer.writerows(summary_results)

with open(rounds_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "num_clients", "fraction_fit", "seed", "round",
        "accuracy", "loss"
    ])
    writer.writeheader()
    writer.writerows(round_results)

print(f"\n📊 Summary saved to {summary_csv}")
print(f"📈 Round metrics saved to {rounds_csv}")
