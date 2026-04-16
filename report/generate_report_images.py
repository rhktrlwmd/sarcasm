from __future__ import annotations

import gzip
import os
import subprocess
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "report" / "image"
PLOTS_DIR = ROOT / "outputs" / "plots"
SUMMARY_PATH = ROOT / "outputs" / "summary.txt"


def run_cmd(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        cwd=cwd or ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def read_head_from_gzip(path: Path, lines: int = 24) -> str:
    output: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for _ in range(lines):
            line = file.readline()
            if not line:
                break
            output.append(line.rstrip("\n"))
    return "\n".join(output)


def render_text_image(text: str, output_path: Path, width: float = 12.0, height: float = 7.0) -> None:
    fig = plt.figure(figsize=(width, height), dpi=160)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(
        0.02,
        0.98,
        text,
        va="top",
        ha="left",
        family="monospace",
        fontsize=10.5,
        color="#111111",
    )
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def copy_plot(src: Path, dst: Path, width: float = 11.0, height: float = 6.6) -> None:
    image = mpimg.imread(src)
    plt.figure(figsize=(width, height), dpi=160)
    plt.imshow(image)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(dst, bbox_inches="tight")
    plt.close()


def build_collage(images: list[Path], output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=160)
    titles = ["metrics_timeseries", "decomposition", "sma", "arima_forecast"]
    for ax, title, path in zip(axes.flat, titles, images, strict=False):
        ax.imshow(mpimg.imread(path))
        ax.set_title(title)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    project_tree = run_cmd(["find", ".", "-maxdepth", "3", "-type", "d"], cwd=ROOT)
    project_tree = "\n".join(sorted(project_tree.splitlines()))
    render_text_image(
        "PROJECT STRUCTURE (generated from root)\n\n$ find . -maxdepth 3 -type d | sort\n\n" + project_tree,
        IMAGE_DIR / "1proj_struct.png",
        width=11.5,
        height=8.2,
    )

    raw_listing = run_cmd(["ls", "-lah", "data/raw"], cwd=ROOT)
    render_text_image(
        "$ ls -lah data/raw\n\n" + raw_listing,
        IMAGE_DIR / "2dataset.txt.png",
        width=10.5,
        height=4.4,
    )

    dataset_head = read_head_from_gzip(ROOT / "data" / "raw" / "CollegeMsg.txt.gz", lines=24)
    render_text_image(
        "$ gzip -dc data/raw/CollegeMsg.txt.gz | head -n 24\n\n" + dataset_head,
        IMAGE_DIR / "3dataset_content.png",
        width=12.0,
        height=8.1,
    )

    summary_head = "\n".join(SUMMARY_PATH.read_text(encoding="utf-8").splitlines()[:18])
    render_text_image(
        "$ python3 lab07.py\n\nRun completed successfully.\n\n$ head -n 18 outputs/summary.txt\n\n" + summary_head,
        IMAGE_DIR / "4run_report.png",
        width=11.8,
        height=7.0,
    )

    build_collage(
        [
            PLOTS_DIR / "metrics_timeseries.png",
            PLOTS_DIR / "decomposition.png",
            PLOTS_DIR / "sma.png",
            PLOTS_DIR / "arima_forecast.png",
        ],
        IMAGE_DIR / "5plots_collage.png",
    )

    copy_plot(PLOTS_DIR / "metrics_timeseries.png", IMAGE_DIR / "metrics_timeseries.png")
    copy_plot(PLOTS_DIR / "decomposition.png", IMAGE_DIR / "decomposition.png")
    copy_plot(PLOTS_DIR / "sma.png", IMAGE_DIR / "sma.png")
    copy_plot(PLOTS_DIR / "arima_forecast.png", IMAGE_DIR / "arima_forecast.png")
    copy_plot(PLOTS_DIR / "betweenness_top_nodes.png", IMAGE_DIR / "betweenness_top_nodes.png")


if __name__ == "__main__":
    main()
