from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import pandas as pd

from .config import SarcasmProjectConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict sarcasm for a single social media text.")
    parser.add_argument("--text", required=True, help="Input text.")
    parser.add_argument("--platform", default="twitter", help="Platform name: twitter/reddit/facebook/instagram.")
    parser.add_argument("--model-path", type=Path, default=None, help="Path to the saved best model bundle.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SarcasmProjectConfig()
    model_path = args.model_path or (config.models_dir / "best_model.pkl")

    with model_path.open("rb") as handle:
        bundle = pickle.load(handle)

    preprocessor = bundle["preprocessor"]
    pipeline = bundle["pipeline"]

    sample = pd.DataFrame(
        [
            {
                "text": args.text,
                "clean_text": preprocessor.preprocess_text(args.text),
                "platform": args.platform.lower(),
            }
        ]
    )

    prediction = int(pipeline.predict(sample)[0])
    label = "sarcastic" if prediction == 1 else "non-sarcastic"
    print(f"model={bundle['model_name']}")
    print(f"platform={args.platform.lower()}")
    print(f"prediction={label}")


if __name__ == "__main__":
    main()

