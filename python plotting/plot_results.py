import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1️⃣ Plot summary results (results_clients.csv)
def plot_summary_results(summary_csv="results_clients.csv"):
    if not os.path.exists(summary_csv):
        print(f"❌ File not found: {summary_csv}")
        return

    df = pd.read_csv(summary_csv)
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.plot(df["num_clients"], df["final_accuracy"], marker="o", label="Final Accuracy")
    plt.title("Final Accuracy vs Number of Clients")
    plt.xlabel("Number of Clients")
    plt.ylabel("Accuracy")
    plt.grid(True)
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(df["num_clients"], df["final_loss"], marker="o", color="orange", label="Final Loss")
    plt.title("Final Loss vs Number of Clients")
    plt.xlabel("Number of Clients")
    plt.ylabel("Loss")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig("plot_summary_results.png")
    print("✅ Saved: plot_summary_results.png")
    plt.show()


# --- 2️⃣ Plot round-by-round results (results_rounds.csv)
def plot_round_results(rounds_csv="results_rounds.csv"):
    if not os.path.exists(rounds_csv):
        print(f"⚠️ Skipping round plots — file not found: {rounds_csv}")
        return

    df = pd.read_csv(rounds_csv)
    plt.figure(figsize=(12, 5))

    # Accuracy over rounds
    plt.subplot(1, 2, 1)
    for clients in sorted(df["num_clients"].unique()):
        subset = df[df["num_clients"] == clients]
        plt.plot(subset["round"], subset["accuracy"], label=f"{clients} clients")
    plt.title("Accuracy over Rounds")
    plt.xlabel("Round")
    plt.ylabel("Accuracy")
    plt.grid(True)
    plt.legend()

    # Loss over rounds
    plt.subplot(1, 2, 2)
    for clients in sorted(df["num_clients"].unique()):
        subset = df[df["num_clients"] == clients]
        plt.plot(subset["round"], subset["loss"], label=f"{clients} clients")
    plt.title("Loss over Rounds")
    plt.xlabel("Round")
    plt.ylabel("Loss")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig("plot_round_results.png")
    print("✅ Saved: plot_round_results.png")
    plt.show()


if __name__ == "__main__":
    plot_summary_results()
    plot_round_results()
