"""Verify the minimal cross-machine runtime used by the demo."""

from __future__ import annotations

import json
import platform
import sys
from importlib import metadata

import cv2
import mmaction
import mmcv
import mmengine
import torch
import torchvision


PACKAGES = (
    "torch",
    "torchvision",
    "mmengine",
    "mmcv-lite",
    "numpy",
    "opencv-python",
    "decord",
    "mmaction2",
)


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    versions = {name: package_version(name) for name in PACKAGES}
    missing = [name for name, version in versions.items() if version == "missing"]
    payload = {
        "python": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "torch_import": torch.__version__,
        "torchvision_import": torchvision.__version__,
        "mmengine_import": mmengine.__version__,
        "mmcv_import": mmcv.__version__,
        "mmaction_import": mmaction.__version__,
        "opencv_import": cv2.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else None
        ),
        "packages": versions,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if missing:
        print(f"Missing packages: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
