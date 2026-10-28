from __future__ import annotations

from src.prepare_real_datasets import prepare_real_datasets
from src.train import print_training_summary, train_model


def main() -> None:
    data_paths = prepare_real_datasets(include_manual_russian_conversational=True)
    result = train_model(data_paths=data_paths)
    print_training_summary(result)


if __name__ == "__main__":
    main()
