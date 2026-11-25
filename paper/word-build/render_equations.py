from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "equations"

FORMULAS = {
    "group_disjoint": (
        r"$G_{\mathrm{fit}}\cap G_{\mathrm{val}}"
        r"=G_{\mathrm{fit}}\cap G_{\mathrm{test}}"
        r"=G_{\mathrm{val}}\cap G_{\mathrm{test}}=\varnothing$"
    ),
    "tsn_pool": (
        r"$q_v=\frac{1}{K}\sum_{k=1}^{K}z_k,\qquad "
        r"p_\theta(y\mid v)=\mathrm{softmax}(Wq_v+b)$"
    ),
    "r21d": (
        r"$\mathrm{Conv3D}_{3\times3\times3}"
        r"\approx\mathrm{Conv2D}_{1\times3\times3}"
        r"\circ\mathrm{Conv1D}_{3\times1\times1}$"
    ),
    "memory_budget": (
        r"$\mathrm{feasible}="
        r"\mathbf{1}\left[M_{\mathrm{a}}\leq2048\ \mathrm{MiB}"
        r"\wedge M_{\mathrm{r}}\leq2048\ \mathrm{MiB}\right]$"
    ),
    "equal_cost": (
        r"$K_tH_tW_t=K_sH_sW_s$"
    ),
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams["mathtext.fontset"] = "stix"
    for name, formula in FORMULAS.items():
        figure = plt.figure(figsize=(8.4, 1.15), facecolor="white")
        figure.text(
            0.5,
            0.5,
            formula,
            ha="center",
            va="center",
            fontsize=19,
            color="#111111",
        )
        figure.savefig(
            OUTPUT / f"{name}.png",
            dpi=320,
            bbox_inches="tight",
            pad_inches=0.08,
            facecolor="white",
        )
        plt.close(figure)
        print(OUTPUT / f"{name}.png")


if __name__ == "__main__":
    main()
