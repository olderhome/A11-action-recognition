import os
import re
from pathlib import Path
from typing import Iterable

import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.models.video import (
    R2Plus1D_18_Weights,
    R3D_18_Weights,
    r2plus1d_18,
    r3d_18,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_mmaction_tsn_weights(backbone, checkpoint_path):
    state = torch.load(checkpoint_path, map_location='cpu')['state_dict']
    mapped = {}
    for key, value in state.items():
        if not key.startswith('backbone.'):
            continue
        key = key[len('backbone.'):]
        if key.startswith('conv1.conv.'):
            key = 'conv1.' + key[len('conv1.conv.'):]
        elif key.startswith('conv1.bn.'):
            key = 'bn1.' + key[len('conv1.bn.'):]
        else:
            match = re.match(
                r'(layer\d+\.\d+\.conv\d+)\.conv\.(.*)', key)
            if match:
                key = match.group(1) + '.' + match.group(2)
            else:
                match = re.match(
                    r'(layer\d+\.\d+)\.(conv\d+)\.bn\.(.*)', key)
                if match:
                    key = (
                        match.group(1) + '.bn' + match.group(2)[-1] +
                        '.' + match.group(3))
                else:
                    match = re.match(
                        r'(layer\d+\.\d+)\.downsample\.conv\.(.*)', key)
                    if match:
                        key = match.group(1) + '.downsample.0.' + match.group(2)
                    else:
                        match = re.match(
                            r'(layer\d+\.\d+)\.downsample\.bn\.(.*)', key)
                        if match:
                            key = (
                                match.group(1) + '.downsample.1.' +
                                match.group(2))
        mapped[key] = value
    missing, unexpected = backbone.load_state_dict(mapped, strict=False)
    if unexpected or any(name not in {'fc.weight', 'fc.bias'}
                         for name in missing):
        raise RuntimeError(
            f'TSN checkpoint mapping mismatch: '
            f'missing={missing}, unexpected={unexpected}')


def _run_blocks(blocks: Iterable[nn.Module], value, use_checkpoint):
    for block in blocks:
        if use_checkpoint and block.training:
            value = checkpoint(block, value, use_reentrant=False)
        else:
            value = block(value)
    return value


class TSNResNet50(nn.Module):
    def __init__(self, num_classes=101, pretrained=True, use_checkpoint=False):
        super().__init__()
        local_checkpoint = os.environ.get(
            'A11_TSN_CHECKPOINT',
            str(PROJECT_ROOT /
                'mmaction2-main/checkpoints/tsn_r50_kinetics400.pth'))
        if pretrained and Path(local_checkpoint).exists():
            backbone = resnet50(weights=None)
            _load_mmaction_tsn_weights(backbone, local_checkpoint)
        else:
            weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
            backbone = resnet50(weights=weights)
        self.use_checkpoint = use_checkpoint
        self.stem = nn.Sequential(
            backbone.conv1, backbone.bn1, backbone.relu, backbone.maxpool)
        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3
        self.layer4 = backbone.layer4
        self.pool = backbone.avgpool
        self.fc = nn.Linear(backbone.fc.in_features, num_classes)

    def sequence_features(self, videos):
        batch, frames, channels, height, width = videos.shape
        value = videos.reshape(batch * frames, channels, height, width)
        value = self.stem(value)
        value = _run_blocks(
            [self.layer1, self.layer2, self.layer3, self.layer4],
            value,
            self.use_checkpoint)
        value = self.pool(value).flatten(1)
        return value.reshape(batch, frames, -1)

    def features(self, videos):
        return self.sequence_features(videos).mean(dim=1)

    def forward(self, videos):
        return self.fc(self.features(videos))


class VideoClassifier(nn.Module):
    def __init__(
            self,
            architecture,
            num_classes=101,
            pretrained=True,
            use_checkpoint=False):
        super().__init__()
        if architecture == 'r3d18':
            weights = R3D_18_Weights.KINETICS400_V1 if pretrained else None
            model = r3d_18(weights=weights)
        elif architecture == 'r2plus1d18':
            weights = (
                R2Plus1D_18_Weights.KINETICS400_V1
                if pretrained else None)
            model = r2plus1d_18(weights=weights)
        else:
            raise ValueError(f'Unknown 3D architecture: {architecture}')
        self.use_checkpoint = use_checkpoint
        self.stem = model.stem
        self.layer1 = model.layer1
        self.layer2 = model.layer2
        self.layer3 = model.layer3
        self.layer4 = model.layer4
        self.pool = model.avgpool
        self.fc = nn.Linear(model.fc.in_features, num_classes)

    def features(self, videos):
        # Dataset tensors are [B, T, C, H, W]; video models expect
        # [B, C, T, H, W].
        value = videos.permute(0, 2, 1, 3, 4).contiguous()
        value = _run_blocks(
            [self.stem, self.layer1, self.layer2, self.layer3, self.layer4],
            value,
            self.use_checkpoint)
        return self.pool(value).flatten(1)

    def forward(self, videos):
        return self.fc(self.features(videos))


class TemporalAttentionHead(nn.Module):
    def __init__(self, input_dim=2048, hidden_dim=256, num_classes=101):
        super().__init__()
        self.projection = nn.Linear(input_dim, hidden_dim)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=4,
            dim_feedforward=hidden_dim * 2,
            dropout=0.1,
            batch_first=True,
            norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.norm = nn.LayerNorm(hidden_dim)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, features):
        value = self.projection(features)
        value = self.encoder(value)
        value = self.norm(value.mean(dim=1))
        return self.classifier(value)


def build_model(name, num_classes=101, pretrained=True, use_checkpoint=False):
    if name == 'tsn2d':
        return TSNResNet50(
            num_classes=num_classes,
            pretrained=pretrained,
            use_checkpoint=use_checkpoint)
    if name in {'r3d18', 'r2plus1d18'}:
        return VideoClassifier(
            name,
            num_classes=num_classes,
            pretrained=pretrained,
            use_checkpoint=use_checkpoint)
    raise ValueError(f'Unknown model: {name}')

