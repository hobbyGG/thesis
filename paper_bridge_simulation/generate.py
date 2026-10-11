from .package_builder import DURATION_S, generate

__all__ = ["generate"]


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate the A20 paper-parameterized bridge capture package")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=DURATION_S)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    print(generate(args.output, duration_s=args.duration, seed=args.seed))
