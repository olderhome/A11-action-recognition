import unittest

import numpy as np

from a11code.build_manifest import group_key
from a11code.sampling import AdaptiveSampler, DenseSampler, UniformSampler


class SamplingTests(unittest.TestCase):
    def test_uniform_is_in_range(self):
        sampler = UniformSampler()
        result = sampler.sample(100, 8, False, np.random.default_rng(0))
        self.assertEqual(result.indices.shape, (8,))
        self.assertTrue(np.all(result.indices >= 0))
        self.assertTrue(np.all(result.indices < 100))
        self.assertTrue(np.all(np.diff(result.indices) >= 0))

    def test_dense_has_constant_interval(self):
        sampler = DenseSampler(frame_interval=4)
        result = sampler.sample(100, 8, False, np.random.default_rng(0))
        self.assertTrue(np.all(np.diff(result.indices) == 4))
        self.assertTrue(np.all(result.indices < 100))

    def test_adaptive_is_unique_and_sorted(self):
        sampler = AdaptiveSampler()
        candidates = np.random.default_rng(0).normal(size=(32, 16, 16, 3))
        result = sampler.select(candidates, 8)
        self.assertEqual(len(result.indices), 8)
        self.assertEqual(len(set(result.indices.tolist())), 8)
        self.assertTrue(np.all(np.diff(result.indices) > 0))

    def test_group_key(self):
        self.assertEqual(
            group_key('ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi'),
            'ApplyEyeMakeup/g01')


if __name__ == '__main__':
    unittest.main()
