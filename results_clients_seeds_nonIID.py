import subprocess
import re
import csv
from datetime import datetime

# ----------------------
# CONFIGURATION
# ----------------------
client_counts = [2, 5, 10, 20]
seeds = [0, 1, 2, 3, 4]
num_server_rounds = 10
output_csv_summary = "results_clients_seeds_summary_NonIID.csv"
output_csv_rounds = "results_clients_seeds_rounds_NonIID.csv"
output_csv_classes = "results_clients_classes_NonIID.csv"
flwr_executable = "flwr"

# ----------------------
# Regex helpers
# ----------------------
re_cen_acc_block = re.compile(r"cen_accuracy['\"]?\s*:\s*\[(.*?)\]", re.S)
re_acc_points = re.compile(r"\(\s*(\d+)\s*,\s*([0-9]*\.?[0-9]+)\s*\)")
re_round_loss = re.compile(r"round\s+(\d+)\s*:\s*([0-9]*\.?[0-9]+)")
re_client_classes = re.compile(r"Client\s+(\d+)\s+has\s+classes:\s*(\[.*?\])\s*\(counts=(\{.*?\})\)")

# ----------------------
# Storage
# ----------------------
summary_results = []
round_results = []
class_distributions = []

# ----------------------
# Main experiment loop
# ----------------------
for num_clients in client_counts:
    for seed in seeds:
        print(f"\n🚀 Running experiment with {num_clients} clients | seed={seed} ...")

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
            print(f"⏰ Run timed out for {num_clients} clients | seed={seed}.")
            summary_results.append({
                "timestamp": datetime.now().isoformat(),
                "num_clients": num_clients,
                "seed": seed,
                "num_rounds": num_server_rounds,
                "status": "timeout",
                "final_accuracy": None,
                "final_loss": None,
                "error": "timeout"
            })
            continue

        output = (proc.stdout or "") + "\n" + (proc.stderr or "")

        # Save raw log
        log_filename = f"flwr_run_{num_clients}_clients_seed_{seed}.log"
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(output)

        # ---- Extract client class info ----
        for match in re_client_classes.findall(output):
            client_id, class_list, class_counts = match
            class_distributions.append({
                "num_clients": num_clients,
                "seed": seed,
                "client_id": int(client_id),
                "classes": class_list,
                "counts": class_counts
            })

        # ---- Handle failed runs ----
        if proc.returncode != 0:
            err_summary = proc.stderr.strip()[:500] or proc.stdout.strip()[:500]
            print(f"❗ flwr failed for {num_clients} clients | seed={seed}.")
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

        # ---- Combine metrics ----
        round_map = {}
        for r, acc in round_accs:
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
        print(f"✅ Finished {num_clients} clients | seed={seed}: acc={final_acc}, loss={final_loss}")

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

# ----------------------
# Write CSVs
# ----------------------
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

print(f"\n📊 Summary saved to {output_csv_summary}")
print(f"📈 Per-round metrics saved to {output_csv_rounds}")
print(f"🧩 Class distributions saved to {output_csv_classes}")
