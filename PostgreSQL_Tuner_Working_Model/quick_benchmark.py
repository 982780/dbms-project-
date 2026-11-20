"""Quick live pgbench demonstration on an already running local test instance.

This script does NOT modify PostgreSQL configuration or restart the database.
Run after initializing pgbench_test with pgbench -i -s 10 pgbench_test.
"""
import argparse
import re
import subprocess
import sys


def command(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing program: {args[0]}. Install PostgreSQL / pgbench first.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{exc.stderr.strip()}") from exc


def main():
    parser = argparse.ArgumentParser(description="Run one real pgbench benchmark without changing server settings")
    parser.add_argument("--duration", type=int, default=10, help="Benchmark duration in seconds (default: 10)")
    parser.add_argument("--database", default="pgbench_test", help="Pre-initialized pgbench test database")
    args = parser.parse_args()
    if not 1 <= args.duration <= 180:
        parser.error("--duration must be between 1 and 180 seconds")

    print("POSTGRESQL LIVE PERFORMANCE CHECK", flush=True)
    print("--------------------------------", flush=True)
    try:
        for setting in ("shared_buffers", "work_mem"):
            value = command(["psql", "-d", args.database, "-Atc", f"SHOW {setting};"]).strip()
            print(f"{setting}: {value}", flush=True)
        print(f"Running a REAL {args.duration}-second pgbench trial on database {args.database}...", flush=True)
        result = command(["pgbench", "-c", "10", "-j", "2", "-T", str(args.duration), args.database])
        matches = re.findall(r"(?m)^tps\s*=\s*([\d.]+)", result)
        if not matches:
            raise RuntimeError("pgbench finished but no TPS value was found.\n" + result[-1500:])
        print(f"LIVE TPS: {float(matches[-1]):,.2f}", flush=True)
        print("This was a fresh, measured result, not the recorded CSV replay.", flush=True)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Check that PostgreSQL is running and pgbench_test was initialized.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
