import numpy as np
import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Display neuron weights from .npz model.")

    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Full path to the model .npz file. If not provided, use --neuron instead.",
    )

    parser.add_argument(
        "--neuron",
        type=str,
        help="Neuron name to build the default model path: /root/.bittensor/miners/default/default/netuid7/subvortex_<neuron>/model.npz",
    )

    parser.add_argument(
        "--uid",
        type=int,
        help="Optional UID to display only its weight and rank (starting from 0)",
    )

    args = parser.parse_args()

    # Determine path from neuron if needed
    if args.path is None:
        if not args.neuron:
            print("❌ You must provide either --path or --neuron.")
            sys.exit(1)
        args.path = f"/root/.bittensor/miners/default/default/netuid7/subvortex_{args.neuron}/model.npz"

    if not os.path.isfile(args.path):
        print(f"❌ File not found: {args.path}")
        sys.exit(1)

    # Load model
    data = np.load(args.path)
    print("✅ Loaded model. Available keys:", data.files)

    if "neuron_weights" not in data:
        print("❌ 'neuron_weights' key not found in the .npz file.")
        sys.exit(1)

    weights = data["neuron_weights"]

    # Sort by (-weight, uid): descending weight, ascending UID
    uids = np.arange(len(weights))
    sorted_indices = sorted(uids, key=lambda uid: (-weights[uid], uid))

    if args.uid is not None:
        if args.uid < 0 or args.uid >= len(weights):
            print(f"❌ UID {args.uid} is out of bounds (0–{len(weights)-1})")
            sys.exit(1)

        rank = sorted_indices.index(args.uid)  # 0-based
        print("\n🏆 UID Ranking by Weight (Descending) + UID (Ascending on ties):")
        print(f"{rank:>3}. UID {args.uid:>3} → Weight: {weights[args.uid]:.6f}")
        return

    # Otherwise, display all rankings
    print("\n🏆 UID Ranking by Weight (Descending) + UID (Ascending on ties):")
    for rank, uid in enumerate(sorted_indices):
        print(f"{rank:>3}. UID {uid:>3} → Weight: {weights[uid]:.6f}")


if __name__ == "__main__":
    main()
