"""Generate TPS comparison graph from results.csv (or specified CSV)."""
import csv
import sys
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

filename = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
runs = defaultdict(list)
with open(filename, newline="") as f:
    for row in csv.DictReader(f):
        runs[row["Configuration"]].append(float(row["TPS"]))
names = list(runs)
averages = [sum(runs[n])/len(runs[n]) for n in names]
for n, avg in zip(names, averages):
    print(f"{n}: {avg:,.2f} TPS")
print("Best observed average:", names[averages.index(max(averages))])
plt.figure(figsize=(10,6))
plt.bar(names, averages)
plt.title("PostgreSQL Database Settings Tuner")
plt.xlabel("Configuration")
plt.ylabel("Average transactions per second (TPS)")
plt.grid(axis="y", alpha=.3)
plt.tight_layout()
plt.savefig("performance_graph.png", dpi=200)
print("Saved performance_graph.png")
