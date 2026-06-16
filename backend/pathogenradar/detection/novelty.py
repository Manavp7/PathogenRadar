"""Novel-pathogen detection (Phase 2).

A PCA "autoencoder" is fit on the manifold of *known* disease signal-patterns (derived from
the knowledge graph). An observed anomaly pattern that reconstructs poorly — i.e. doesn't look
like any known disease — yields a high novelty score. Combined with a high overall risk and a
weak best-disease match, this flags a potential **unknown/novel pathogen** instead of forcing
it into a known category. Pure NumPy + scikit-learn (no torch).
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sklearn.decomposition import PCA

from ..domain.models import HOSPITAL_SIGNALS, SEARCH_SIGNALS, SignalType
from ..knowledge import KnowledgeGraphRepo, get_knowledge_graph

# Diagnostic signals that make up a "presentation pattern" (weather excluded).
NOVELTY_SIGNALS: list[str] = (
    [s.value for s in SEARCH_SIGNALS]
    + [s.value for s in HOSPITAL_SIGNALS]
    + [SignalType.SOCIAL_MENTIONS.value, SignalType.WASTEWATER_VIRAL_LOAD.value]
)


class NoveltyDetector:
    def __init__(
        self,
        kg: KnowledgeGraphRepo | None = None,
        samples_per_disease: int = 60,
        n_components: int = 4,
        seed: int = 0,
    ):
        self.kg = kg or get_knowledge_graph()
        self.signals = NOVELTY_SIGNALS
        self.index = {s: i for i, s in enumerate(self.signals)}
        self._fit(samples_per_disease, n_components, seed)

    def _fit(self, samples_per_disease: int, n_components: int, seed: int) -> None:
        rng = np.random.default_rng(seed)
        rows = []
        for disease in self.kg.diseases():
            dsig = sorted(set(self.kg.disease_signals(disease)) & set(self.signals))
            for _ in range(samples_per_disease):
                vec = rng.uniform(0.0, 0.12, size=len(self.signals))
                # Partial presentations: a real outbreak may elevate only a subset of the
                # disease's signals, so include those to keep the manifold tolerant.
                keep = [s for s in dsig if rng.random() > 0.3] or dsig
                for s in keep:
                    vec[self.index[s]] = rng.uniform(0.4, 1.0)
                rows.append(vec)
        x = np.array(rows)
        self.mean = x.mean(axis=0)
        self.std = x.std(axis=0) + 1e-6
        xs = (x - self.mean) / self.std
        self.pca = PCA(n_components=min(n_components, xs.shape[1])).fit(xs)
        errs = self._recon_error(xs)
        self.p50 = float(np.percentile(errs, 50))
        self.p95 = float(np.percentile(errs, 95))

    def _recon_error(self, xs: np.ndarray) -> np.ndarray:
        recon = self.pca.inverse_transform(self.pca.transform(xs))
        return np.linalg.norm(xs - recon, axis=1)

    def score(self, drivers: dict[str, float]) -> float:
        """Novelty in [0, 1]: how unlike any known disease the pattern is."""
        vec = np.zeros(len(self.signals))
        for s, v in drivers.items():
            if s in self.index:
                vec[self.index[s]] = max(0.0, min(1.0, v))
        if vec.max() <= 1e-6:
            return 0.0
        xs = ((vec - self.mean) / self.std).reshape(1, -1)
        err = float(self._recon_error(xs)[0])
        scale = max(self.p95 - self.p50, 1e-6)
        # On-manifold (known) -> ~0; well beyond the known spread -> ~1.
        return float(max(0.0, min(1.0, (err - self.p95) / (2.0 * scale))))


@lru_cache(maxsize=1)
def get_novelty_detector() -> NoveltyDetector:
    return NoveltyDetector()
