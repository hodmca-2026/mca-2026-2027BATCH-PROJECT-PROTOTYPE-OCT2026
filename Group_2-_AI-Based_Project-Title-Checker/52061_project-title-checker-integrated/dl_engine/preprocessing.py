"""
Deep Learning Preprocessing Utilities
=====================================
Vocabulary building, tokenization, integer sequence padding/truncation,
and common text cleaning for PyTorch LSTM and DL models.
"""

import re
from typing import List, Dict, Tuple, Optional

# Standard domains for project classification (Syllabus Unit IV)
PROJECT_DOMAINS = [
    "Healthcare",
    "Education",
    "Finance",
    "Agriculture",
    "Cybersecurity",
    "Web Applications",
    "Other",
]

DOMAIN_TO_IDX = {d: i for i, d in enumerate(PROJECT_DOMAINS)}
IDX_TO_DOMAIN = {i: d for i, d in enumerate(PROJECT_DOMAINS)}

PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
PAD_IDX = 0
UNK_IDX = 1


def clean_text(text: Optional[str]) -> str:
    """Normalize text: lowercase, strip punctuation, normalize whitespace."""
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: Optional[str]) -> List[str]:
    """Tokenize clean text into word tokens."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    return cleaned.split()


class Vocabulary:
    """Integer token mapping with OOV (<unk>) and padding (<pad>) support."""

    def __init__(self, min_freq: int = 1):
        self.min_freq = min_freq
        self.word2idx: Dict[str, int] = {PAD_TOKEN: PAD_IDX, UNK_TOKEN: UNK_IDX}
        self.idx2word: Dict[int, str] = {PAD_IDX: PAD_TOKEN, UNK_IDX: UNK_TOKEN}

    def build_vocab(self, texts: List[str]) -> None:
        freq: Dict[str, int] = {}
        for text in texts:
            for token in tokenize(text):
                freq[token] = freq.get(token, 0) + 1

        idx = len(self.word2idx)
        for token, count in sorted(freq.items()):
            if count >= self.min_freq and token not in self.word2idx:
                self.word2idx[token] = idx
                self.idx2word[idx] = token
                idx += 1

    def encode(self, text: Optional[str], max_len: int = 64) -> List[int]:
        """Convert text into padded/truncated integer sequence."""
        tokens = tokenize(text)
        indices = [self.word2idx.get(t, UNK_IDX) for t in tokens]
        if len(indices) < max_len:
            indices = indices + [PAD_IDX] * (max_len - len(indices))
        else:
            indices = indices[:max_len]
        return indices

    def compute_oov_rate(self, text: Optional[str]) -> float:
        """Calculate the proportion of tokens mapped to the unknown token (<unk>)."""
        tokens = tokenize(text)
        if not tokens:
            return 0.0
        unk_count = sum(1 for t in tokens if t not in self.word2idx)
        return unk_count / len(tokens)

    def to_dict(self) -> Dict:
        return {"word2idx": self.word2idx, "min_freq": self.min_freq}

    @classmethod
    def from_dict(cls, data: Dict) -> "Vocabulary":
        vocab = cls(min_freq=data.get("min_freq", 1))
        vocab.word2idx = data["word2idx"]
        vocab.idx2word = {int(v): k for k, v in vocab.word2idx.items()}
        return vocab

    def __len__(self) -> int:
        return len(self.word2idx)

