from __future__ import annotations

import json
import os
from dataclasses import dataclass

from openai import OpenAI


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


NICHE_PROMPTS = {
    "football": (
        "You are analyzing a football match transcript. Find the best clip moments: "
        "goals, near-misses, penalties, controversial decisions, and decisive plays. "
        "Each clip should capture the build-up AND the key moment."
    ),
    "gaming": (
        "You are analyzing a gaming video transcript. Find the best moments: "
        "clutch plays, major achievements, turning points, funny or hype moments."
    ),
    "podcast": (
        "You are analyzing a podcast transcript. Find the most shareable segments: "
        "strong opinions, surprising insights, emotional moments, and quotable lines."
    ),
}

_RESPONSE_SCHEMA = """{
  "clips": [
    {
      "start": <number, seconds>,
      "end": <number, seconds>,
      "title": "<short title, max 8 words>",
      "reason": "<why this is a great clip>",
      "score": <integer 1-100>
    }
  ]
}"""


def score_with_llm(
    segments: list[TranscriptSegment],
    content_type: str,
    min_duration: float,
    max_duration: float,
    limit: int,
    excitement_peaks: list[float] | None = None,
) -> list[ClipCandidate]:
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    model = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")

    transcript_text = "\n".join(
        f"[{seg.start:.1f}s] {seg.text}" for seg in segments
    )

    niche_context = NICHE_PROMPTS.get(content_type, NICHE_PROMPTS["podcast"])

    peaks_hint = ""
    if excitement_peaks:
        peak_list = ", ".join(f"{p:.1f}s" for p in excitement_peaks[:20])
        peaks_hint = f"\nAudio excitement peaks detected at: {peak_list}. Prioritize clips around these timestamps.\n"

    system_prompt = (
        f"{niche_context}\n"
        f"Respond ONLY with valid JSON matching this schema, no extra text:\n{_RESPONSE_SCHEMA}"
    )

    user_prompt = (
        f"{peaks_hint}"
        f"Transcript (timestamps in seconds):\n{transcript_text}\n\n"
        f"Find the {limit} best clips between {min_duration}s and {max_duration}s long. "
        f"Use exact timestamps from the transcript."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content or ""

    # Strip markdown code fences if present
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        clips_data: list[dict] = json.loads(raw_text).get("clips", [])
    except (json.JSONDecodeError, AttributeError):
        return []

    max_end = segments[-1].end if segments else 0.0
    candidates: list[ClipCandidate] = []

    for raw in clips_data:
        start = max(0.0, float(raw["start"]))
        end = min(float(raw["end"]), max_end)
        duration = end - start

        if duration < min_duration or duration > max_duration:
            continue

        text = " ".join(
            seg.text for seg in segments if seg.end > start and seg.start < end
        )

        candidates.append(
            ClipCandidate(
                index=0,
                start=start,
                end=end,
                duration=duration,
                score=max(1, min(100, int(raw["score"]))),
                title=raw["title"],
                reason=raw["reason"],
                text=text,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    picked = candidates[:limit]
    picked.sort(key=lambda c: c.start)
    for idx, c in enumerate(picked, start=1):
        c.index = idx

    return picked
