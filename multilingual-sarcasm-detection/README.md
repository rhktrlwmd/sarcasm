# Sarcasm Detection System

This project is a Python-based NLP system for sarcasm detection. The current coursework version is trained primarily on English and Russian data. It uses a classical machine-learning pipeline based on TF-IDF features and supports coursework-friendly comparison between Logistic Regression, Naive Bayes, and Linear SVM, while keeping the project structure ready for future upgrades.

## Current coursework scope

The preprocessing pipeline preserves Unicode characters, but the current trained coursework version is focused on:

- English
- Russian

The code is Unicode-safe and can be extended later for other languages, but the current report should describe the system as an English-Russian sarcasm detector.

## Task definition

- Binary text classification
- `0 = NotSarcastic`
- `1 = Sarcastic`

## Why TF-IDF

The baseline uses:

```python
TfidfVectorizer(analyzer="char", ngram_range=(2, 5), max_features=20000)
```

Character n-grams are more language-independent than English-specific token pipelines, so they are a strong choice for sarcasm detection in English and Russian. The project also adds word-level TF-IDF and pragmatic features such as caps ratio, punctuation emphasis, and cue-pattern counts.

## Dataset requirements

Supported file formats:

- CSV
- JSON

Supported input column pairs:

- `text`, `label`
- `headline`, `is_sarcastic`

The loader automatically renames columns to:

- `text`
- `label`

Multiple datasets from `data/raw/` are merged into a single training dataset.

## Project structure

```text
multilingual-sarcasm-detection/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── notebooks/
│   └── exploration.ipynb
└── src/
    ├── __init__.py
    ├── config.py
    ├── data_loader.py
    ├── preprocessing.py
    ├── feature_engineering.py
    ├── train.py
    ├── evaluate.py
    ├── predict.py
    ├── visualization.py
    └── utils.py
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Training

Put your CSV and/or JSON files into `data/raw/`, then run:

```bash
python main.py
```

Choose `1. Train Model`.

You can also train directly:

```bash
python -m src.train
```

For coursework training on the curated real datasets, including the expanded Russian conversational corpus:

```bash
python train_real.py
```

Artifacts are saved to:

- `models/sarcasm_model.pkl`
- `models/tfidf_vectorizer.pkl`
- `models/model_metadata.json`

Processed files are saved to:

- `data/processed/combined_dataset.csv`
- `data/processed/train_split.csv`
- `data/processed/test_split.csv`

## Evaluation

Choose `2. Evaluate Model` from the CLI menu or evaluate after training with:

```bash
python -c "from src.evaluate import evaluate_model; print(evaluate_model())"
```

Metrics:

- Accuracy
- Precision
- Recall
- F1-score
- Classification report
- Confusion matrix

Plots are saved to `data/processed/plots/`.

## Model comparison for coursework

Run:

```bash
python -m src.compare_models
```

or choose `6. Compare Coursework Models` in the CLI menu.

This generates:

- `data/processed/model_comparison.csv`
- `data/processed/model_comparison.md`
- `data/processed/plots/model_comparison.png`

The comparison table contains:

- Model
- Accuracy
- F1
- Precision
- Recall

## Prediction examples

```bash
python -c "from src.predict import predict_text; print(predict_text('Great, another Monday morning.'))"
python -c "from src.predict import predict_text; print(predict_text('Отлично, ещё одна бессонная ночь.'))"
python -c "from src.predict import predict_text; print(predict_text('Perfecto, otra tarea para el fin de semana.'))"
```

## Streamlit application

Run:

```bash
streamlit run app.py
```

Features:

- project title
- text input area
- prediction button
- sarcasm prediction output
- probability score
- model information block

The interface fully supports Unicode input.

## Russian conversational dataset

The coursework setup includes an expanded manual Russian conversational dataset in:

- `data/raw/real/manual_ru_conversational_reddit.csv`

It contains:

- manually curated public Reddit-style snippets
- manually authored conversational sarcasm examples
- manually generated template-based conversational examples

This corpus is used to improve Russian conversational sarcasm coverage and to teach the model that uppercase emphasis is not automatically sarcastic in every case.

## Demo dataset

The repository includes a small multilingual demo dataset in `data/raw/` so the project can be trained immediately. For coursework experiments, prefer the curated real-data path in `train_real.py` or CLI option `5`.

## Future expansion

The structure is intentionally modular:

- `src/data_loader.py` can keep serving classical ML and transformer pipelines.
- `src/preprocessing.py` preserves Unicode and can be reused by tokenizer-based models.
- `models/` already separates saved artifacts from code.
- `src/config.py` contains model configuration hooks for future backends.

This makes it straightforward to add stronger future models later without restructuring the repository.

## Suggested screenshots

Add screenshots for the final report from:

- Streamlit app after a prediction
- confusion matrix plot
- class distribution plot
- notebook exploration
