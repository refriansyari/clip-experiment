from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile


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


def analyze_audio_energy(audio_path: Path, window_size: float = 1.0) -> list[tuple[float, float]]:
    sample_rate, audio_data = wavfile.read(str(audio_path))
    
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    audio_data = audio_data.astype(np.float32)
    
    window_samples = int(sample_rate * window_size)
    hop_samples = window_samples // 2
    
    energy_timeline: list[tuple[float, float]] = []
    
    for i in range(0, len(audio_data) - window_samples, hop_samples):
        window = audio_data[i:i + window_samples]
        energy = np.sqrt(np.mean(window ** 2))
        timestamp = i / sample_rate
        energy_timeline.append((timestamp, float(energy)))
    
    return energy_timeline


def detect_action_moments(
    energy_timeline: list[tuple[float, float]],
    peak_threshold: float = 1.2,
    min_distance_seconds: float = 8.0,
) -> list[float]:
    if not energy_timeline:
        return []
    
    timestamps = np.array([t for t, _ in energy_timeline])
    energies = np.array([e for _, e in energy_timeline])
    
    mean_energy = np.mean(energies)
    std_energy = np.std(energies)
    threshold = mean_energy + peak_threshold * std_energy
    
    time_step = timestamps[1] - timestamps[0] if len(timestamps) > 1 else 1.0
    min_distance_samples = int(min_distance_seconds / time_step)
    
    peak_indices, _ = signal.find_peaks(
        energies,
        height=threshold,
        distance=min_distance_samples,
        prominence=std_energy * 0.3,
    )
    
    return [float(timestamps[idx]) for idx in peak_indices]


def first_words(text: str, max_words: int = 5) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .,!?:;-")
    words = cleaned.split()
    return " ".join(words[:max_words]).capitalize() or "Gaming clip"


def score_gaming_window(
    items: list[TranscriptSegment],
    duration: float,
    action_moments: list[float],
    window_start: float,
    window_end: float,
) -> tuple[int, list[str]]:
    score = 45
    reasons: list[str] = []
    
    if 10 <= duration <= 45:
        score += 25
        reasons.append("perfect clip length")
    elif 8 <= duration <= 60:
        score += 15
        reasons.append("good clip length")
    
    action_count = sum(1 for moment in action_moments if window_start <= moment <= window_end)
    if action_count > 0:
        bump = min(35, action_count * 18)
        score += bump
        reasons.append(f"{action_count} action moment(s)")
    
    text = " ".join(item.text for item in items).lower()
    words = re.findall(r"[\w']+", text)
    
    gaming_keywords = {
        "kill", "killed", "dead", "down", "eliminated", "clutch", "win", "won",
        "victory", "ace", "headshot", "epic", "insane", "crazy", "lets go",
        "wow", "oh my god", "omg", "no way", "wtf", "gg", "boss", "loot"
    }
    keyword_hits = sorted(set(words).intersection(gaming_keywords))
    if keyword_hits:
        bump = min(20, len(keyword_hits) * 6)
        score += bump
        reasons.append(f"gaming keywords: {', '.join(keyword_hits[:3])}")
    
    word_count = len(words)
    density = word_count / max(duration, 1)
    if density >= 2.5:
        score += 8
        reasons.append("high energy commentary")
    
    if word_count < 12:
        score -= 8
        reasons.append("minimal commentary")
    
    return max(1, min(100, score)), reasons


def build_gaming_candidates(
    segments: list[TranscriptSegment],
    action_moments: list[float],
    min_duration: float,
    max_duration: float,
    limit: int,
    lookback_seconds: float = 10.0,
    lookahead_seconds: float = 3.0,
) -> list[ClipCandidate]:
    candidates: list[ClipCandidate] = []
    
    if not segments or not action_moments:
        return candidates
    
    for moment_time in action_moments:
        clip_start = max(0, moment_time - lookback_seconds)
        clip_end = moment_time + lookahead_seconds
        
        duration = clip_end - clip_start
        if duration < min_duration or duration > max_duration:
            continue
        
        window_segments = [
            seg for seg in segments
            if seg.end > clip_start and seg.start < clip_end
        ]
        
        if not window_segments:
            continue
        
        text = " ".join(seg.text for seg in window_segments)
        score, reasons = score_gaming_window(
            window_segments,
            duration,
            action_moments,
            clip_start,
            clip_end,
        )
        
        candidates.append(
            ClipCandidate(
                index=0,
                start=clip_start,
                end=clip_end,
                duration=duration,
                score=score,
                title=first_words(text),
                reason=", ".join(reasons) or "action detected",
                text=text,
            )
        )
    
    candidates.sort(key=lambda c: c.score, reverse=True)
    
    picked: list[ClipCandidate] = []
    for candidate in candidates:
        if len(picked) >= limit:
            break
        
        overlaps = any(
            not (candidate.end < item.start or candidate.start > item.end)
            for item in picked
        )
        if not overlaps:
            candidate.index = len(picked) + 1
            picked.append(candidate)
    
    picked.sort(key=lambda c: c.start)
    for idx, candidate in enumerate(picked, start=1):
        candidate.index = idx
    
    return picked
