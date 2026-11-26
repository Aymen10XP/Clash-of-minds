"""Small CPU-friendly PyTorch network for per-question correctness estimates."""

import torch
from torch import nn

from .adaptive_features import NUMERIC_FEATURE_COUNT


class AdaptiveQuestionNetwork(nn.Module):
    """Combine a topic embedding with difficulty and player/question history."""

    def __init__(self, topic_count, topic_embedding_size=4):
        super().__init__()
        self.topic_embedding = nn.Embedding(topic_count, topic_embedding_size)
        self.classifier = nn.Sequential(
            nn.Linear(topic_embedding_size + NUMERIC_FEATURE_COUNT, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
        )

    def forward(self, topic_ids, numeric_features):
        topic_features = self.topic_embedding(topic_ids)
        combined = torch.cat((topic_features, numeric_features), dim=1)
        return self.classifier(combined).squeeze(1)
