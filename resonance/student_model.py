# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 â€” see LICENSE for details.

# resonance/student_model.py
# Lightweight standalone module containing only the model architecture.
# No training dependencies â€” safe to import in production without pandas, sklearn, etc.

import torch
import torch.nn as nn
import torch.nn.functional as F

N_EMO = 7  # joy, anger, fear, sadness, surprise, shame, neutral


class CNNHead(nn.Module):
    """1D CNN for local n-gram pattern detection."""
    def __init__(self, in_channels, num_classes, kernel_sizes=(2, 3, 4), num_filters=128):
        super().__init__()
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels, num_filters, k, padding=(k - 1) // 2)
            for k in kernel_sizes
        ])
        self.fc = nn.Linear(num_filters * len(kernel_sizes), num_classes)
        self.dropout = nn.Dropout(0.1)

    def forward(self, hidden_states):
        x = hidden_states.transpose(1, 2)
        pooled = [F.relu(conv(x)).max(dim=-1).values for conv in self.convs]
        return self.fc(self.dropout(torch.cat(pooled, dim=-1)))


class StudentModel(nn.Module):
    """
    Resonance v2 student model.
    DeBERTa-v3-base backbone with specialist heads for emotion, guilt,
    crisis, VAD, PERMA, reappraisal, suppression, and alexithymia detection.
    """
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone
        hidden = 768
        self.primary_head = nn.Linear(hidden, N_EMO)
        self.cnn_head = CNNHead(hidden, N_EMO, num_filters=64)
        self.guilt_head = nn.Linear(hidden, 4)
        self.crisis_head = nn.Linear(hidden, 1)
        self.vad_head = nn.Linear(hidden, 3)
        self.perma_head = nn.Linear(hidden, 5)
        self.reappraisal_head = nn.Linear(hidden, 1)
        self.suppression_head = nn.Linear(hidden, 1)
        self.alexithymia_head = nn.Linear(hidden, 1)

    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids, attention_mask)
        hidden = out.last_hidden_state
        cls = hidden[:, 0, :]
        return {
            "primary":     self.primary_head(cls),
            "cnn":         self.cnn_head(hidden),
            "guilt":       self.guilt_head(cls),
            "crisis":      self.crisis_head(cls).squeeze(-1),
            "vad":         self.vad_head(cls),
            "perma":       self.perma_head(cls),
            "reappraisal": self.reappraisal_head(cls).squeeze(-1),
            "suppression": self.suppression_head(cls).squeeze(-1),
            "alexithymia": self.alexithymia_head(cls).squeeze(-1),
            "cls":         cls,
        }
