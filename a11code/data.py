import csv
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

try:
    import decord
except ImportError as error:
    raise RuntimeError('decord is required for video decoding') from error

from .sampling import AdaptiveSampler


MEAN = np.asarray([123.675, 116.28, 103.53], dtype=np.float32)
STD = np.asarray([58.395, 57.12, 57.375], dtype=np.float32)
KINETICS_MEAN = np.asarray(
    [110.2008, 100.6398, 95.9948], dtype=np.float32)
KINETICS_STD = np.asarray([58.1477, 56.4698, 55.3322], dtype=np.float32)


class UCFVideoDataset(Dataset):
    def __init__(
            self,
            manifest,
            data_root,
            sampler,
            num_frames=8,
            image_size=112,
            training=False,
            limit=0,
            seed=0,
            normalization='imagenet'):
        self.data_root = Path(data_root)
        self.sampler = sampler
        self.num_frames = num_frames
        self.image_size = image_size
        self.training = training
        self.epoch = 0
        self.seed = seed
        if normalization == 'kinetics':
            self.mean = KINETICS_MEAN
            self.std = KINETICS_STD
        elif normalization == 'imagenet':
            self.mean = MEAN
            self.std = STD
        else:
            raise ValueError(f'Unknown normalization: {normalization}')
        self.rows = self._read_manifest(manifest)
        if limit > 0:
            self.rows = self.rows[:limit]

    @staticmethod
    def _read_manifest(path):
        with Path(path).open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            rows = [
                (row.get('path') or row.get('relative_path'), int(row['label']))
                for row in reader
            ]
        if not rows:
            raise RuntimeError(f'Empty manifest: {path}')
        return rows

    def __len__(self):
        return len(self.rows)

    def set_epoch(self, epoch):
        self.epoch = int(epoch)

    def _rng(self, index):
        seed = self.seed + self.epoch * 1000003 + index
        return np.random.default_rng(seed)

    @staticmethod
    def _decode(reader, indices):
        frames = reader.get_batch(indices).asnumpy()
        if frames.ndim != 4:
            raise RuntimeError('Unexpected decoded video shape.')
        return frames

    def _preprocess(self, frames, rng):
        processed = []
        first_height, first_width = frames[0].shape[:2]
        first_scale = max(
            self.image_size * 1.14 / min(first_height, first_width), 1e-6)
        first_resized_height = max(
            self.image_size, int(round(first_height * first_scale)))
        first_resized_width = max(
            self.image_size, int(round(first_width * first_scale)))
        if self.training:
            shared_y = int(rng.integers(
                0, first_resized_height - self.image_size + 1))
            shared_x = int(rng.integers(
                0, first_resized_width - self.image_size + 1))
        else:
            shared_y = (first_resized_height - self.image_size) // 2
            shared_x = (first_resized_width - self.image_size) // 2
        for frame in frames:
            height, width = frame.shape[:2]
            scale = max(self.image_size * 1.14 / min(height, width), 1e-6)
            new_width = max(self.image_size, int(round(width * scale)))
            new_height = max(self.image_size, int(round(height * scale)))
            frame = cv2.resize(
                frame, (new_width, new_height),
                interpolation=cv2.INTER_LINEAR)
            offset_y = min(shared_y, max(new_height - self.image_size, 0))
            offset_x = min(shared_x, max(new_width - self.image_size, 0))
            frame = frame[
                offset_y:offset_y + self.image_size,
                offset_x:offset_x + self.image_size]
            processed.append(frame.astype(np.float32))
        tensor = np.stack(processed)
        if self.training and rng.random() < 0.5:
            tensor = tensor[:, :, ::-1]
        tensor = (tensor - self.mean) / self.std
        return torch.from_numpy(tensor).permute(0, 3, 1, 2).contiguous()

    def __getitem__(self, index):
        relative_path, label = self.rows[index]
        rng = self._rng(index)
        video_path = self.data_root / relative_path
        reader = decord.VideoReader(str(video_path), num_threads=1)
        total = len(reader)
        decode_start = time.perf_counter()

        if isinstance(self.sampler, AdaptiveSampler):
            candidate_indices = self.sampler.candidate_indices(
                total, self.training, rng)
            candidate = self._decode(reader, candidate_indices)
            selected = self.sampler.select(candidate, self.num_frames)
            selected_frame_indices = candidate_indices[selected.indices]
            frames = self._decode(reader, selected_frame_indices)
            score_cost = selected.score_cost
        else:
            sampled = self.sampler.sample(
                total, self.num_frames, self.training, rng)
            frames = self._decode(reader, sampled.indices)
            score_cost = 0.0

        decode_seconds = time.perf_counter() - decode_start
        frames = self._preprocess(frames, rng)
        return {
            'video': frames,
            'label': torch.tensor(label, dtype=torch.long),
            'path': relative_path,
            'decode_seconds': torch.tensor(decode_seconds),
            'score_cost': torch.tensor(score_cost),
        }


def collate_video_batch(items):
    return {
        'video': torch.stack([item['video'] for item in items]),
        'label': torch.stack([item['label'] for item in items]),
        'path': [item['path'] for item in items],
        'decode_seconds': torch.stack(
            [item['decode_seconds'] for item in items]),
        'score_cost': torch.stack([item['score_cost'] for item in items]),
    }

