from __future__ import annotations

from typing import Protocol

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class ClipCandidate:
    index: int
    start: float
    end: float
    duration: float
    score: int
    title: str
    reason: str
    text: str


class ClipScorer(Protocol):
    def score_window(self, items: list[TranscriptSegment], duration: float) -> tuple[int, list[str]]:
        ...

    def build_candidates(
        self,
        segments: list[TranscriptSegment],
        min_duration: float,
        max_duration: float,
        limit: int,
    ) -> list[ClipCandidate]:
        ...
