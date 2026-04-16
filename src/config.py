from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LabConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    n_nodes: int = 10
    n_steps: int = 1000
    synthetic_cycle: int = 100
    seed: int = 42
    start_date: str = "2024-01-01"
    frequency: str = "D"
    window_size: int = 50
    seasonal_period: int = 5
    sma_window: int = 3
    arima_order: tuple[int, int, int] = (1, 1, 1)
    forecast_steps: int = 4

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs"

    @property
    def plots_dir(self) -> Path:
        return self.outputs_dir / "plots"

    @property
    def report_dir(self) -> Path:
        return self.project_root / "report"

    @property
    def default_input_path(self) -> Path:
        return self.raw_dir / "CollegeMsg.txt.gz"
