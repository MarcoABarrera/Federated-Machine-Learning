import os
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------
# CONFIGURATION
# ----------------------
input_file = "results_clients_participation_rounds_20251030_003543.csv"
output_dir = "plots_clients_participation"
os.makedirs(output_dir, exist_ok=True)

# Define line/marker styles per participation fraction for visibility
fraction_styles = {
    0.2: {"linestyle": "-",  "marker": "o"},
    0.5: {"linestyle": "--", "marker": "s"},
  #  0.8: {"linestyle": "-.", "marker": "^"},
    1.0: {"linestyle": ":",  "marker": "d"},
}

# ----------------------
# LOAD DATA
# ----------------------
data = pd.read_csv(input_file)
print("✅ Data loaded:", data.shape)
print("Unique num_clients:", data["num_clients"].unique())
print("Unique fraction_fit:", data["fraction_fit"].unique())

# ----------------------
# 📈 ACCURACY vs ROUNDS (mean ± std)
# ----------------------
plt.figure(figsize=(10, 6))
for num_clients in sorted(data["num_clients"].unique()):
    for frac in sorted(data["fraction_fit"].unique()):
        subset = data[(data["num_clients"] == num_clients) & (data["fraction_fit"] == frac)]
        grouped = subset.groupby("round")["accuracy"].agg(["mean", "std"])
        style = fraction_styles.get(frac, {"linestyle": "-", "marker": None})

        plt.plot(
            grouped.index, grouped["mean"],
            label=f"{num_clients} clients | fraction={frac}",
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
plt.legend(title="Clients | Participation", fontsize=8)
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "accuracy_vs_rounds_mean_std.png"))
plt.show()

# ----------------------
# 📉 LOSS vs ROUNDS (mean ± std)
# ----------------------
plt.figure(figsize=(10, 6))
for num_clients in sorted(data["num_clients"].unique()):
    for frac in sorted(data["fraction_fit"].unique()):
        subset = data[(data["num_clients"] == num_clients) & (data["fraction_fit"] == frac)]
        grouped = subset.groupby("round")["loss"].agg(["mean", "std"])
        style = fraction_styles.get(frac, {"linestyle": "-", "marker": None})

        plt.plot(
            grouped.index, grouped["mean"],
            label=f"{num_clients} clients | fraction={frac}",
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
plt.legend(title="Clients | Participation", fontsize=8)
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "loss_vs_rounds_mean_std.png"))
plt.show()

# ----------------------
# 📊 BOX PLOT: Final Accuracy Distribution per Participation Fraction
# ----------------------
final_round = data["round"].max()
final_df = data[data["round"] == final_round]

plt.figure(figsize=(8, 5))
final_df.boxplot(column="accuracy", by="fraction_fit", grid=False)
plt.title(f"Final Accuracy per Participation Fraction (round={final_round})")
plt.suptitle("")
plt.xlabel("Participation Fraction (fraction_fit)")
plt.ylabel("Final Accuracy")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "boxplot_final_accuracy_per_fraction.png"))
plt.show()

# ----------------------
# 📊 OPTIONAL: HISTOGRAM (Final Accuracy per fraction_fit)
# ----------------------
plt.figure(figsize=(10, 6))
for frac in sorted(final_df["fraction_fit"].unique()):
    subset = final_df[final_df["fraction_fit"] == frac]
    plt.hist(subset["accuracy"], bins=10, alpha=0.5, label=f"fraction={frac}")

plt.title("Histogram of Final Accuracy per Participation Fraction")
plt.xlabel("Final Accuracy")
plt.ylabel("Frequency")
plt.legend(title="Participation Fraction")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "histogram_final_accuracy_per_fraction.png"))
plt.show()

print(f"✅ All plots saved in folder: {output_dir}/")
