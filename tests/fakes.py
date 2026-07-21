"""In-memory fakes for the knowledge-base ports, used in the unit tier.

They are deterministic and free of network, model downloads, and disk, and they
double as proof that the ports are sufficient for the facade.
"""

import hashlib
from dataclasses import dataclass


@dataclass
class FakeEmbedder:
    """Maps text to a deterministic fixed-dimension vector via a content hash."""

    dim: int = 16

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [digest[i % len(digest)] / 255.0 for i in range(self.dim)]
