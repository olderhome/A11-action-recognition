# A11 reproducible training code

This directory contains the formal UCF101 experiment pipeline.

## Environment

Use the project-local interpreter:

```powershell
..\.venv\Scripts\python.exe -m pip check
```

## Data

After extracting UCF101 to `mmaction2-main/data/ucf101/videos`, build the
official split manifests:

```powershell
..\.venv\Scripts\python.exe -m a11code.build_manifest
```

## Smoke test

```powershell
..\.venv\Scripts\python.exe -m a11code.train `
  --model tsn2d --sampling uniform `
  --train-limit 64 --val-limit 64 --epochs 1 `
  --batch-size 1 --grad-accum 4 `
  --enforce-budget-mib 2048
```

## Full run

```powershell
..\.venv\Scripts\python.exe -m a11code.train `
  --model tsn2d --sampling uniform --seed 0 `
  --epochs 12 --batch-size 1 --grad-accum 8
```

Every run writes logs, best checkpoint, final predictions and memory metrics under
`results/runs/<run-id>/`.

