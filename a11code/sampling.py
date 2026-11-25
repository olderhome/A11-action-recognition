from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SamplingResult:
    indices: np.ndarray
    score_cost: float = 0.0


class UniformSampler:
    name = 'uniform'

    def sample(self, total_frames, num_frames, training, rng):
        if total_frames <= 0:
            raise ValueError('Video contains no frames.')
        if total_frames < num_frames:
            return SamplingResult(
                np.linspace(0, total_frames - 1, num_frames).astype(np.int64))
        centers = (np.arange(num_frames) + 0.5) * total_frames / num_frames
        if training:
            width = total_frames / num_frames
            centers += rng.uniform(-0.25 * width, 0.25 * width, num_frames)
        indices = np.clip(centers.astype(np.int64), 0, total_frames - 1)
        return SamplingResult(indices)


class DenseSampler:
    name = 'dense'

    def __init__(self, frame_interval=4):
        self.frame_interval = frame_interval

    def sample(self, total_frames, num_frames, training, rng):
        if total_frames < num_frames:
            return SamplingResult(
                np.linspace(0, total_frames - 1, num_frames).astype(np.int64))
        span = (num_frames - 1) * self.frame_interval + 1
        if total_frames <= span:
            start = 0
        elif training:
            start = int(rng.integers(0, total_frames - span + 1))
        else:
            start = (total_frames - span) // 2
        indices = start + np.arange(num_frames) * self.frame_interval
        return SamplingResult(np.clip(indices, 0, total_frames - 1))


class AdaptiveSampler:
    """Select informative but temporally diversified frames.

    The caller supplies decoded candidate frames through ``select``. This design
    keeps the extra decoding cost visible to the experiment runner.
    """

    name = 'adaptive'

    def __init__(self, candidate_frames=32, diversity=0.35):
        self.candidate_frames = candidate_frames
        self.diversity = diversity

    def candidate_indices(self, total_frames, training, rng):
        sampler = UniformSampler()
        jitter = bool(training)
        return sampler.sample(
            total_frames, self.candidate_frames, jitter, rng).indices

    def select(self, candidate_frames, num_frames):
        frames = candidate_frames.astype(np.float32)
        if len(frames) <= 1:
            indices = np.zeros(num_frames, dtype=np.int64)
            return SamplingResult(indices)

        gray = frames.mean(axis=-1)
        motion = np.zeros(len(gray), dtype=np.float32)
        motion[1:] = np.mean(np.abs(np.diff(gray, axis=0)), axis=(1, 2))
        motion[0] = motion[1]
        normalized = motion / (motion.max() + 1e-8)

        positions = np.linspace(0.0, 1.0, len(gray))
        chosen = []
        remaining = set(range(len(gray)))
        while len(chosen) < min(num_frames, len(gray)):
            best_index = None
            best_value = -1.0
            for index in remaining:
                if chosen:
                    distances = [
                        abs(positions[index] - positions[item])
                        for item in chosen
                    ]
                    diversity = min(distances)
                else:
                    diversity = positions[index]
                value = normalized[index] + (
                    self.diversity * diversity)
                if value > best_value:
                    best_value = value
                    best_index = index
            chosen.append(best_index)
            remaining.remove(best_index)
        chosen.sort()
        if len(chosen) < num_frames:
            chosen.extend([chosen[-1]] * (num_frames - len(chosen)))
        return SamplingResult(
            np.asarray(chosen[:num_frames], dtype=np.int64),
            score_cost=float(len(gray)))


def build_sampler(name):
    if name == 'uniform':
        return UniformSampler()
    if name == 'dense':
        return DenseSampler()
    if name == 'adaptive':
        return AdaptiveSampler()
    raise ValueError(f'Unknown sampling strategy: {name}')

