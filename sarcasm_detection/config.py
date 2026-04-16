from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PreprocessingConfig:
    lowercase: bool = True
    remove_urls: bool = True
    remove_mentions: bool = True
    normalize_hashtags: bool = True
    remove_stopwords: bool = True
    keep_negations: bool = True
    apply_stemming: bool = False
    apply_lemmatization: bool = True
    min_token_length: int = 2


@dataclass(slots=True)
class TrainingConfig:
    test_size: float = 0.25
    random_state: int = 42
    cv_folds: int = 4


@dataclass(slots=True)
class SarcasmProjectConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

    @property
    def data_root(self) -> Path:
        return self.project_root / "data" / "sarcasm"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def processed_data_dir(self) -> Path:
        return self.data_root / "processed"

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs" / "sarcasm"

    @property
    def models_dir(self) -> Path:
        return self.outputs_dir / "models"

    @property
    def figures_dir(self) -> Path:
        return self.outputs_dir / "figures"

    @property
    def report_dir(self) -> Path:
        return self.project_root / "report"

    @property
    def default_dataset_path(self) -> Path:
        return self.raw_data_dir / "demo_multiplatform_sarcasm.csv"

    def ensure_directories(self) -> None:
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

