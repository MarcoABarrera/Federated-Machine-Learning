#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import os

# ----------------------
# CONFIG
# ----------------------
summary_csv = "results_clients_seeds_summary_10.0.csv"
rounds_csv = "results_clients_seeds_rounds_10.0.csv"
output_dir = "plots_alpha10.0"

os.makedirs(output_dir, exist_ok=True)

# ----------------------
# LOAD DATA
# ----------------------
df_summary = pd.read_csv(summary_csv)
df_rounds = pd.read_csv(rounds_csv)

# Filter only successful runs
df_summary = df_summary[df_summary["status"] == "ok"]

# ----------------------
# 📊 BOX PLOT (Final Accuracy Distribution)
# ----------------------
plt.figure(figsize=(7, 5))
df_summary.boxplot(column="final_accuracy", by="num_clients", grid=False)
plt.title("Final Accuracy Distribution per Client Count")
plt.suptitle("")  # remove automatic subtitle
plt.xlabel("Number of Clients")
plt.ylabel("Final Accuracy")
plt.savefig(os.path.join(output_dir, "boxplot_final_accuracy.png"))
plt.show()

# ----------------------
# 📈 ERRORBAR PLOT (Mean ± Std)
# ----------------------
means = df_summary.groupby("num_clients")["final_accuracy"].mean()
stds = df_summary.groupby("num_clients")["final_accuracy"].std()

plt.figure(figsize=(7, 5))
plt.errorbar(means.index, means, yerr=stds, fmt='-o', capsize=5)
plt.title("Mean ± Std of Final Accuracy across Seeds")
plt.xlabel("Number of Clients")
plt.ylabel("Final Accuracy")
plt.grid(True, linestyle="--", alpha=0.6)
plt.savefig(os.path.join(output_dir, "errorbar_final_accuracy.png"))
plt.show()

# ----------------------
# 📉 CONVERGENCE PLOTS (Per-round accuracy)
# ----------------------
plt.figure(figsize=(8, 6))
for num_clients, group in df_rounds.groupby("num_clients"):
    # Average across seeds per round
    mean_acc = group.groupby("round")["accuracy"].mean()
    std_acc = group.groupby("round")["accuracy"].std()
    plt.plot(mean_acc.index, mean_acc, label=f"{num_clients} clients")
    plt.fill_between(mean_acc.index, mean_acc - std_acc, mean_acc + std_acc, alpha=0.2)

plt.title("Convergence Curves (mean ± std across seeds)")
plt.xlabel("Round")
plt.ylabel("Central Accuracy")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.savefig(os.path.join(output_dir, "convergence_mean_std.png"))
plt.show()

# ----------------------
# 📊 OPTIONAL: HISTOGRAM (Final Accuracy per Client Count)
# ----------------------
plt.figure(figsize=(10, 6))
for num_clients in sorted(df_summary["num_clients"].unique()):
    subset = df_summary[df_summary["num_clients"] == num_clients]
    plt.hist(subset["final_accuracy"], bins=10, alpha=0.5, label=f"{num_clients} clients")

plt.title("Histogram of Final Accuracy (per Client Count)")
plt.xlabel("Final Accuracy")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.savefig(os.path.join(output_dir, "histogram_final_accuracy.png"))
plt.show()

print(f"✅ All plots saved in folder: {output_dir}/")
