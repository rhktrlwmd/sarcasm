from __future__ import annotations

from src.compare_models import compare_models
from src.evaluate import evaluate_model
from src.manual_dataset_builder import expand_manual_russian_dataset
from src.predict import predict_text
from src.prepare_real_datasets import prepare_real_datasets
from src.train import print_training_summary, train_model


def main() -> None:
    while True:
        print("\nSarcasm Detection")
        print("1. Train Demo Model")
        print("2. Evaluate Model")
        print("3. Predict Text")
        print("4. Exit")
        print("5. Train Coursework Model")
        print("6. Compare Models for Coursework")
        print("7. Rebuild Russian Training Dataset")

        choice = input("Select an option: ").strip()

        if choice == "1":
            result = train_model()
            print("Demo training used all datasets found in data/raw. For the real coursework experiment, prefer option 5.")
            print_training_summary(result)
        elif choice == "2":
            try:
                evaluation = evaluate_model()
                metrics = evaluation["metrics"]
                print("Evaluation completed successfully.")
                print(f"Accuracy : {metrics['accuracy']:.4f}")
                print(f"Precision: {metrics['precision']:.4f}")
                print(f"Recall   : {metrics['recall']:.4f}")
                print(f"F1-score : {metrics['f1_score']:.4f}")
                print("\nClassification report:")
                print(evaluation["classification_report"])
                print(f"Confusion matrix plot: {evaluation['confusion_matrix_plot']}")
            except FileNotFoundError as error:
                print(error)
        elif choice == "3":
            text = input("Enter text: ").strip()
            try:
                result = predict_text(text)
                print(f"Prediction: {result['prediction']}")
                if result["is_uncertain"]:
                    print(f"Binary fallback: {result['binary_prediction']}")
                print(f"Sarcasm probability: {result['probability']:.2%}")
            except FileNotFoundError as error:
                print(error)
        elif choice == "4":
            print("Goodbye.")
            break
        elif choice == "5":
            try:
                data_paths = prepare_real_datasets(include_manual_russian_conversational=True)
                result = train_model(data_paths=data_paths)
                print("Coursework model training used curated real datasets, including the manual Russian conversational set.")
                print_training_summary(result)
            except FileNotFoundError as error:
                print(error)
        elif choice == "6":
            try:
                data_paths = prepare_real_datasets(include_manual_russian_conversational=True)
                comparison = compare_models(data_paths=data_paths)
                print("Coursework model comparison completed successfully.")
                print(f"Train samples: {comparison['train_samples']}")
                print(f"Test samples : {comparison['test_samples']}")
                print(comparison["results"].to_string(index=False, float_format=lambda value: f"{value:.4f}"))
                print(f"CSV table: {comparison['csv_path']}")
                print(f"Markdown table: {comparison['markdown_path']}")
                print(f"Plot: {comparison['plot_path']}")
            except FileNotFoundError as error:
                print(error)
        elif choice == "7":
            summary = expand_manual_russian_dataset()
            print("Russian training dataset rebuilt successfully.")
            print(f"Total rows: {summary['total_rows']}")
            print(f"Sarcastic rows: {summary['sarcastic_rows']}")
            print(f"Not sarcastic rows: {summary['nonsarcastic_rows']}")
            print(f"Output: {summary['output_path']}")
        else:
            if any(character.isalpha() for character in choice):
                try:
                    result = predict_text(choice)
                    print("It looks like you entered text instead of a menu number.")
                    print(f"Prediction: {result['prediction']}")
                    if result["is_uncertain"]:
                        print(f"Binary fallback: {result['binary_prediction']}")
                    print(f"Sarcasm probability: {result['probability']:.2%}")
                except FileNotFoundError as error:
                    print(error)
            else:
                print("Invalid option. Please choose 1, 2, 3, 4, 5, 6, or 7.")


if __name__ == "__main__":
    main()
