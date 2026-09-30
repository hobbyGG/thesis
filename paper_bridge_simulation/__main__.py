from .generate import generate

import argparse
from pathlib import Path


parser = argparse.ArgumentParser(description="Generate the A20 paper-parameterized bridge capture package")
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--duration", type=float, default=4.0)
parser.add_argument("--seed", type=int, default=2026)
args = parser.parse_args()
print(generate(args.output, duration_s=args.duration, seed=args.seed))
