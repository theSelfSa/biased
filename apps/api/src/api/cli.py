from __future__ import annotations

import argparse

from api.services.demo_data import reset_demo_workspace_data, seed_demo_workspace_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="B.I.A.S.E.D. demo workspace data utilities."
    )
    parser.add_argument(
        "command",
        choices=["seed", "reset"],
        help="seed = idempotent load, reset = deterministic full reset + load",
    )
    args = parser.parse_args()

    if args.command == "seed":
        seed_demo_workspace_data(reset=False)
        print("Demo data seeded (idempotent).")
        return

    reset_demo_workspace_data()
    print("Demo data reset and reloaded.")


if __name__ == "__main__":
    main()
