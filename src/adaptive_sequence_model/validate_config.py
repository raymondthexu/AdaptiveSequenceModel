"""Command-line validation and optional resolved configuration snapshotting."""

import argparse

from adaptive_sequence_model.config import ConfigError, load_config, save_config


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Path to an experiment YAML file")
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save resolved settings to output_dir/config.yaml",
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.save:
            save_config(config)
    except ConfigError as exc:
        parser.exit(2, f"{exc}\n")
    print("Configuration is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
