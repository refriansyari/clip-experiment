from pathlib import Path
import numpy as np
from scipy.io import wavfile

from scorers.gaming import (
    analyze_audio_energy,
    detect_action_moments,
    score_gaming_window,
    build_gaming_candidates,
    TranscriptSegment,
)


def create_mock_gaming_audio(output_path: Path, duration: int = 60, sample_rate: int = 16000):
    t = np.linspace(0, duration, duration * sample_rate)
    
    base_audio = np.random.normal(0, 0.08, len(t))
    
    action_times = [12, 25, 38, 52]
    for action_time in action_times:
        action_start = int(action_time * sample_rate)
        action_duration = int(2 * sample_rate)
        action_end = min(action_start + action_duration, len(base_audio))
        base_audio[action_start:action_end] += np.random.normal(0, 0.6, action_end - action_start)
    
    audio_data = (base_audio * 32767).astype(np.int16)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(str(output_path), sample_rate, audio_data)
    
    return output_path


def test_gaming_audio_analysis():
    print("Testing gaming audio analysis...")
    
    mock_audio = Path("outputs/test_gaming_audio.wav")
    create_mock_gaming_audio(mock_audio, duration=60)
    
    energy_timeline = analyze_audio_energy(mock_audio, window_size=1.0)
    
    print(f"✓ Generated {len(energy_timeline)} energy data points")
    print(f"  Sample: {energy_timeline[:3]}")
    
    mock_audio.unlink()


def test_action_moment_detection():
    print("\nTesting action moment detection...")
    
    mock_audio = Path("outputs/test_gaming_audio.wav")
    create_mock_gaming_audio(mock_audio, duration=60)
    
    energy_timeline = analyze_audio_energy(mock_audio, window_size=1.0)
    moments = detect_action_moments(energy_timeline, peak_threshold=1.2, min_distance_seconds=8.0)
    
    print(f"✓ Detected {len(moments)} action moments")
    print(f"  Moment times: {[f'{m:.1f}s' for m in moments]}")
    
    mock_audio.unlink()


def test_gaming_window_scoring():
    print("\nTesting gaming window scoring...")
    
    segments = [
        TranscriptSegment(10.0, 13.0, "Oh my god that was insane"),
        TranscriptSegment(13.0, 16.0, "Got the kill lets go!"),
        TranscriptSegment(16.0, 19.0, "That was a crazy headshot"),
    ]
    
    action_moments = [14.0]
    
    score, reasons = score_gaming_window(
        segments,
        duration=9.0,
        action_moments=action_moments,
        window_start=10.0,
        window_end=19.0,
    )
    
    print(f"✓ Score: {score}/100")
    print(f"  Reasons: {reasons}")


def test_build_gaming_candidates():
    print("\nTesting gaming candidate builder...")
    
    segments = [
        TranscriptSegment(0.0, 3.0, "Starting the match"),
        TranscriptSegment(3.0, 6.0, "Looking for enemies"),
        TranscriptSegment(10.0, 13.0, "There's one spotted"),
        TranscriptSegment(13.0, 16.0, "Got the kill headshot!"),
        TranscriptSegment(16.0, 19.0, "That was insane"),
        TranscriptSegment(25.0, 28.0, "Another enemy down there"),
        TranscriptSegment(28.0, 31.0, "Clutch moment eliminated him"),
        TranscriptSegment(31.0, 34.0, "Wow that was epic"),
        TranscriptSegment(40.0, 43.0, "Final boss fight"),
        TranscriptSegment(43.0, 46.0, "Victory we won!"),
    ]
    
    action_moments = [15.0, 30.0, 45.0]
    
    candidates = build_gaming_candidates(
        segments,
        action_moments,
        min_duration=8.0,
        max_duration=60.0,
        limit=3,
        lookback_seconds=10.0,
        lookahead_seconds=3.0,
    )
    
    print(f"✓ Generated {len(candidates)} clip candidates")
    for candidate in candidates:
        print(f"  Clip {candidate.index}: {candidate.start:.1f}s-{candidate.end:.1f}s "
              f"(score: {candidate.score}) - {candidate.title}")


if __name__ == "__main__":
    print("=" * 60)
    print("Gaming Scorer Unit Tests")
    print("=" * 60)
    
    test_gaming_audio_analysis()
    test_action_moment_detection()
    test_gaming_window_scoring()
    test_build_gaming_candidates()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
