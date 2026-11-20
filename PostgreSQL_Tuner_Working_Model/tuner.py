
"""PostgreSQL pgbench tuning experiment. Run locally on Mac with PostgreSQL 18."""
import csv
import re
import subprocess
import time
from pathlib import Path

DATABASE = "pgbench_test"
SERVICE = "postgresql@18"
CONFIGS = [
    ("Default", "128MB", "4MB"),
    ("A", "256MB", "4MB"),
    ("B", "512MB", "4MB"),
    ("C", "128MB", "16MB"),
    ("D", "256MB", "16MB"),
    ("E", "512MB", "16MB"),
]
OUTPUT = Path("results_new.csv")

def run(args):
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout

def verify(buf, mem):
    actual_buf = run(["psql", "-d", DATABASE, "-Atc", "SHOW shared_buffers;"]).strip().lower()
    actual_mem = run(["psql", "-d", DATABASE, "-Atc", "SHOW work_mem;"]).strip().lower()
    if actual_buf != buf.lower() or actual_mem != mem.lower():
        raise RuntimeError(f"Settings mismatch: {actual_buf}, {actual_mem}")

def main():
    if OUTPUT.exists():
        raise SystemExit("results_new.csv exists. Rename it before a new run.")
    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Configuration", "shared_buffers", "work_mem", "Run", "TPS"])
        try:
            for name, buf, mem in CONFIGS:
                print(f"Testing {name}: shared_buffers={buf}, work_mem={mem}", flush=True)
                run(["psql", "-d", DATABASE, "-c", f"ALTER SYSTEM SET shared_buffers = '{buf}';"])
                run(["psql", "-d", DATABASE, "-c", f"ALTER SYSTEM SET work_mem = '{mem}';"])
                run(["brew", "services", "restart", SERVICE])
                time.sleep(8)
                verify(buf, mem)
                for trial in range(1, 4):
                    output = run(["pgbench", "-c", "10", "-j", "2", "-T", "30", "-P", "5", DATABASE])
                    matches = re.findall(r"(?m)^tps = ([0-9.]+)", output)
                    if not matches:
                        raise RuntimeError(f"TPS missing from pgbench output for {name} run {trial}")
                    tps = float(matches[-1])
                    writer.writerow([name, buf, mem, trial, tps])
                    f.flush()
                    print(f"  Run {trial}: {tps:.2f} TPS", flush=True)
        finally:
            print("Restoring default settings...", flush=True)
            run(["psql", "-d", DATABASE, "-c", "ALTER SYSTEM SET shared_buffers = '128MB';"])
            run(["psql", "-d", DATABASE, "-c", "ALTER SYSTEM SET work_mem = '4MB';"])
            run(["brew", "services", "restart", SERVICE])
    print(f"Results saved to {OUTPUT}")

if __name__ == "__main__":
    main()
