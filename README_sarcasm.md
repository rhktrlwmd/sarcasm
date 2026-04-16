# Sarcasm Detection Diploma Project

This project implements a lightweight ML pipeline for sarcasm detection in social media texts. It follows the framework from ZhiYu Zhang's review article:

1. data collection
2. data preprocessing
3. feature extraction and feature selection
4. sarcasm classification
5. sarcasm detection

The code is intentionally built around classical machine learning so it can run on a regular laptop and still provide a defensible diploma-level experiment.

## What is implemented

- multi-platform dataset loader for Twitter, Reddit, Facebook and Instagram CSV files
- configurable preprocessing:
  - tokenization with `TweetTokenizer`
  - stopword removal
  - optional stemming
  - optional lemmatization
- hybrid feature engineering:
  - TF-IDF word n-grams
  - TF-IDF character n-grams
  - pragmatic and punctuation-based features
  - platform one-hot encoding
- model comparison:
  - Logistic Regression
  - Linear SVM
  - Multinomial Naive Bayes
  - SGD classifier with logistic loss
- evaluation:
  - cross-validation F1
  - test metrics
  - per-platform metrics
  - confusion matrices
  - top linear features for interpretation
- final predictor for new texts

## Quick start

```bash
python3 run_sarcasm_project.py
python3 -m sarcasm_detection.predict --platform twitter --text "Oh great, another app update that broke everything."
```

Artifacts are saved to:

- `data/sarcasm/processed`
- `outputs/sarcasm`

## Dataset format

Put one or more CSV files into `data/sarcasm/raw`. Supported columns:

- text aliases: `text`, `tweet`, `comment`, `post`, `caption`, `content`, `sentence`
- label aliases: `label`, `sarcasm`, `is_sarcastic`, `class`, `target`
- platform aliases: `platform`, `source_platform`, `network`

Labels can be `0/1`, `true/false`, `sarcastic/non_sarcastic`, or `irony/literal`.

## Why the preprocessing is needed

### Tokenization

Machine learning models do not understand raw sentences directly. Tokenization splits text into smaller units, so the model can estimate which words, patterns and punctuation marks correlate with sarcasm.

### Stopword removal

Words like `the`, `is`, `and` occur everywhere and usually carry little signal for sarcasm. Removing them reduces noise. The project keeps negation words such as `not` and `never`, because sarcasm often depends on contrast and negation.

### Stemming

Stemming reduces words to rough roots, for example `loved`, `loving`, `loves` -> `love`. This reduces sparsity, but sometimes damages meaning because the resulting form may be unnatural.

### Lemmatization

Lemmatization reduces words to dictionary forms, for example `cars` -> `car`, `was` -> `be` in a full morphological setup. It is cleaner than stemming and keeps the text more interpretable. In a diploma project, lemmatization is useful because:

- it reduces the number of distinct forms
- it helps the model generalize across grammatical variants
- it makes top features easier to explain in the report

### Can we work without lemmatization?

Yes. In fact, for short noisy texts, strong TF-IDF baselines often work well even without lemmatization. That is why the training script supports `--disable-lemmatization`. A good diploma argument is:

- compare the same models with and without lemmatization
- show whether F1 improves or stays roughly the same
- conclude empirically instead of claiming it in advance

If performance does not improve, you can justify dropping lemmatization to simplify the system.

## Project structure

- `sarcasm_detection/config.py` - paths and experiment settings
- `sarcasm_detection/data.py` - dataset loading and normalization
- `sarcasm_detection/preprocessing.py` - tokenization and normalization
- `sarcasm_detection/features.py` - TF-IDF and handcrafted features
- `sarcasm_detection/models.py` - candidate classifiers
- `sarcasm_detection/train.py` - training, evaluation and model saving
- `sarcasm_detection/predict.py` - inference for new texts
- `report/diploma_sarcasm_detection.md` - explanation and diploma notes

## Recommended papers for the literature review

- ZhiYu Zhang, *Sarcasm detection methods based on machine learning and deep learning*, 2024. [Article](https://ace.ewapub.com/article/view/10077)
- Cynthia Van Hee et al., *SemEval-2018 Task 3: Irony Detection in English Tweets*, 2018. [ACL](https://aclanthology.org/S18-1005/)
- Mikhail Khodak et al., *A Large Self-Annotated Corpus for Sarcasm*, 2017. [arXiv summary](https://huggingface.co/papers/1704.05579)

## Important limitation

There is no stable, universally used open benchmark that cleanly covers Twitter, Reddit, Facebook and Instagram in one place. The code therefore supports:

- public benchmark datasets where they exist
- your own manually collected or annotated Facebook/Instagram CSV files
- a combined evaluation across platforms
