#!/usr/local/bin/python3

"""
Bar plot of DeepTumour tissue-of-origin probabilities, one PNG per sample.

Used by DeepTumour.py (--plot), or standalone on an existing predictions JSON:
    plot_deeptumour.py predictions_DeepTumour.json --outDir plots/ [--sampleID NAME]
"""

import json
import os
from pathlib import Path
from typing import Optional

import click
import matplotlib
matplotlib.use("Agg")  # Headless backend: never opens a window (works in Docker/Singularity)
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

PREDICTION_COLOR = "#247A60"
OTHER_COLOR = "#B8C9D3"


def plot_predictions(sample_name: str, result: dict, output_file: str) -> Path:

    """
    Plot the probabilities of one sample's DeepTumour result and save it as a PNG
    """

    prediction: str = result["prediction"]
    entropy = result.get("entropy")

    # Sort probabilities from highest to lowest
    ranked: list = sorted(result["probs"].items(), key=lambda item: item[1], reverse=True)
    labels: list = [name for name, _ in ranked]
    values: list = [prob for _, prob in ranked]

    # Highlight the predicted cancer type
    colors: list = [PREDICTION_COLOR if label == prediction else OTHER_COLOR for label in labels]

    fig, ax = plt.subplots(figsize=(11, 10))

    y_positions = range(len(labels))
    bars = ax.barh(y_positions, values, color=colors, edgecolor="none", height=0.72)

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()

    # Label each bar with its probability
    max_prob: float = max(values)
    for bar, value in zip(bars, values):
        ax.text(
            value + max_prob * 0.008,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2%}",
            va="center",
            ha="left",
            fontsize=8
        )

    ax.set_xlim(0, max_prob * 1.20)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("Model probability", fontsize=11)

    subtitle: str = f"Top prediction: {prediction}"
    if entropy is not None:
        subtitle += f"  |  Entropy: {entropy:.3f}"

    ax.set_title(f"DeepTumour Tissue-of-Origin Predictions\n{sample_name}",
                 fontsize=14, fontweight="bold", pad=30)
    ax.text(0.0, 1.01, subtitle, transform=ax.transAxes,
            fontsize=10, color=PREDICTION_COLOR, fontweight="bold", va="bottom")

    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    fig.text(0.5, 0.015, "Probabilities are model outputs, not clinical certainty.",
             ha="center", fontsize=9, color="dimgray")

    fig.tight_layout(rect=[0, 0.04, 1, 0.96])

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_all(results: dict, outDir: str, sampleID: Optional[str] = None) -> list:

    """
    Plot every sample in a DeepTumour results dict as <outDir>/<sample>_DeepTumour.png.
    By default the sample name is the VCF name; sampleID overrides it
    """

    if sampleID is not None and len(results) != 1:
        raise click.UsageError(f"--sampleID can only be used with a single sample, but there are {len(results)}")

    plots: list = []
    for sample, result in results.items():
        name: str = sampleID if sampleID is not None else sample
        plots.append(plot_predictions(name, result, os.path.join(outDir, f"{name}_DeepTumour.png")))
    return plots


@click.command(name="plot_deeptumour")
@click.argument("predictions",
                type=click.Path(exists=True, dir_okay=False))
@click.option("--outDir", "outDir",
              type=click.Path(file_okay=False),
              default=os.getcwd(),
              show_default=False,
              help="Directory where to save the plots. Default is the current directory")
@click.option("--sampleID", "sampleID",
              type=str,
              default=None,
              help="Sample name to use in the plot title and file name instead of the VCF name (single-sample JSON only)")
def main(predictions: str, outDir: str, sampleID: Optional[str]):

    """
    Plot the probabilities of a DeepTumour predictions JSON (one PNG per sample)
    """

    with open(predictions) as file:
        results: dict = json.load(file)

    for path in plot_all(results, outDir, sampleID):
        click.echo(f"Plot saved to: {path}")


if __name__ == '__main__':
    main()
