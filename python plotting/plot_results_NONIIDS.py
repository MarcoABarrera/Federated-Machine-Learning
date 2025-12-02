import os
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------
# CONFIGURATION
# ----------------------
files = {
    0.1: "results_clients_seeds_rounds_0.1.csv",
    1.0: "results_clients_seeds_rounds_1.0.csv",
    10.0: "results_clients_seeds_rounds_10.0.csv"
}
output_dir = "plots_nonIID_comparison"
os.makedirs(output_dir, exist_ok=True)

# Define line/marker styles per α for visual clarity
alpha_styles = {
    0.1: {"linestyle": "-",  "marker": "o"},
    1.0: {"linestyle": "--", "marker": "s"},
    10.0: {"linestyle": "-.", "marker": "^"},
}

# ----------------------
# LOAD & CONCAT DATA
# ----------------------
dfs = []
for alpha, path in files.items():
    df = pd.read_csv(path)
    df["alpha"] = alpha
    dfs.append(df)
data = pd.concat(dfs, ignore_index=True)

# ----------------------
# 📈 ACCURACY vs ROUNDS (mean ± std)
# ----------------------
plt.figure(figsize=(10, 6))
for alpha in sorted(data["alpha"].unique()):
    style = alpha_styles.get(alpha, {"linestyle": "-", "marker": None})
    for num_clients in sorted(data["num_clients"].unique()):
        subset = data[(data["alpha"] == alpha) & (data["num_clients"] == num_clients)]
        grouped = subset.groupby("round")["accuracy"].agg(["mean", "std"])
        plt.plot(
            grouped.index, grouped["mean"],
            label=f"α={alpha}, {num_clients} clients",
            linestyle=style["linestyle"],
            marker=style["marker"],
            markersize=4,
            linewidth=1.5,
        )
        plt.fill_between(
            grouped.index,
            grouped["mean"] - grouped["std"],
            grouped["mean"] + grouped["std"],
            alpha=0.15,
        )

plt.title("Accuracy vs Rounds (mean ± std across seeds)")
plt.xlabel("Round")
plt.ylabel("Accuracy")
plt.legend(title="Legend", fontsize=8)
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "accuracy_vs_rounds_mean_std.png"))
plt.show()

# ----------------------
# 📉 LOSS vs ROUNDS (mean ± std)
# ----------------------
plt.figure(figsize=(10, 6))
for alpha in sorted(data["alpha"].unique()):
    style = alpha_styles.get(alpha, {"linestyle": "-", "marker": None})
    for num_clients in sorted(data["num_clients"].unique()):
        subset = data[(data["alpha"] == alpha) & (data["num_clients"] == num_clients)]
        grouped = subset.groupby("round")["loss"].agg(["mean", "std"])
        plt.plot(
            grouped.index, grouped["mean"],
            label=f"α={alpha}, {num_clients} clients",
            linestyle=style["linestyle"],
            marker=style["marker"],
            markersize=4,
            linewidth=1.5,
        )
        plt.fill_between(
            grouped.index,
            grouped["mean"] - grouped["std"],
            grouped["mean"] + grouped["std"],
            alpha=0.15,
        )

plt.title("Loss vs Rounds (mean ± std across seeds)")
plt.xlabel("Round")
plt.ylabel("Loss")
plt.legend(title="Legend", fontsize=8)
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "loss_vs_rounds_mean_std.png"))
plt.show()

# ----------------------
# 📊 BOX PLOT: Final Accuracy Distribution per α
# ----------------------
final_round = data["round"].max()
final_df = data[data["round"] == final_round]

plt.figure(figsize=(8, 5))
final_df.boxplot(column="accuracy", by="alpha", grid=False)
plt.title(f"Final Accuracy Distribution per Dirichlet α (round={final_round})")
plt.suptitle("")
plt.xlabel("Dirichlet α")
plt.ylabel("Accuracy")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "boxplot_final_accuracy_per_alpha.png"))
plt.show()

# ----------------------
# 📊 OPTIONAL: HISTOGRAM (Final Accuracy per α)
# ----------------------
plt.figure(figsize=(10, 6))
for alpha in sorted(final_df["alpha"].unique()):
    subset = final_df[final_df["alpha"] == alpha]
    plt.hist(subset["accuracy"], bins=10, alpha=0.5, label=f"α={alpha}")

plt.title("Histogram of Final Accuracy (per Dirichlet α)")
plt.xlabel("Final Accuracy")
plt.ylabel("Frequency")
plt.legend(title="Dirichlet α")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "histogram_final_accuracy_per_alpha.png"))
plt.show()

print(f"✅ All plots saved in folder: {output_dir}/")
