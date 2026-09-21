from .package_builder import generate

__all__ = ["generate"]


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate the semi-measured bridge capture package")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(generate(args.output, duration_s=args.duration, seed=args.seed, overwrite=args.overwrite))
