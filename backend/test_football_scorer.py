from pathlib import Path
import numpy as np
from scipy.io import wavfile

from scorers.football import (
    analyze_audio_energy,
    detect_excitement_peaks,
    score_football_window,
    build_football_candidates,
    TranscriptSegment,
)


def create_mock_audio(output_path: Path, duration: int = 60, sample_rate: int = 16000):
    t = np.linspace(0, duration, duration * sample_rate)
    
    base_audio = np.random.normal(0, 0.1, len(t))
    
    peak_times = [15, 30, 45]
    for peak_time in peak_times:
        peak_start = int(peak_time * sample_rate)
        peak_duration = int(3 * sample_rate)
        peak_end = min(peak_start + peak_duration, len(base_audio))
        base_audio[peak_start:peak_end] += np.random.normal(0, 0.5, peak_end - peak_start)
    
    audio_data = (base_audio * 32767).astype(np.int16)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(str(output_path), sample_rate, audio_data)
    
    return output_path


def test_audio_energy_analysis():
    print("Testing audio energy analysis...")
    
    mock_audio = Path("outputs/test_mock_audio.wav")
    create_mock_audio(mock_audio, duration=60)
    
    energy_timeline = analyze_audio_energy(mock_audio, window_size=2.0)
    
    print(f"✓ Generated {len(energy_timeline)} energy data points")
    print(f"  Sample: {energy_timeline[:3]}")
    
    mock_audio.unlink()


def test_excitement_peak_detection():
    print("\nTesting excitement peak detection...")
    
    mock_audio = Path("outputs/test_mock_audio.wav")
    create_mock_audio(mock_audio, duration=60)
    
    energy_timeline = analyze_audio_energy(mock_audio)
    peaks = detect_excitement_peaks(energy_timeline, peak_threshold=1.5, min_distance_seconds=10.0)
    
    print(f"✓ Detected {len(peaks)} excitement peaks")
    print(f"  Peak times: {[f'{p:.1f}s' for p in peaks]}")
    
    mock_audio.unlink()


def test_football_window_scoring():
    print("\nTesting football window scoring...")
    
    segments = [
        TranscriptSegment(10.0, 15.0, "Amazing build up play"),
        TranscriptSegment(15.0, 20.0, "He shoots and it's a goal!"),
        TranscriptSegment(20.0, 25.0, "What an incredible finish"),
    ]
    
    excitement_peaks = [18.0]
    
    score, reasons = score_football_window(
        segments,
        duration=15.0,
        excitement_peaks=excitement_peaks,
        window_start=10.0,
        window_end=25.0,
    )
    
    print(f"✓ Score: {score}/100")
    print(f"  Reasons: {reasons}")


def test_build_football_candidates():
    print("\nTesting football candidate builder...")
    
    segments = [
        TranscriptSegment(0.0, 5.0, "The match begins"),
        TranscriptSegment(5.0, 10.0, "Ball possession in midfield"),
        TranscriptSegment(10.0, 15.0, "Building up the attack"),
        TranscriptSegment(15.0, 20.0, "Great pass forward"),
        TranscriptSegment(20.0, 25.0, "He shoots and scores a goal!"),
        TranscriptSegment(25.0, 30.0, "What an amazing finish"),
        TranscriptSegment(35.0, 40.0, "Another attack developing"),
        TranscriptSegment(40.0, 45.0, "Corner kick opportunity"),
        TranscriptSegment(45.0, 50.0, "Header and it's in! Another goal!"),
        TranscriptSegment(50.0, 55.0, "Incredible performance"),
    ]
    
    excitement_peaks = [23.0, 48.0]
    
    candidates = build_football_candidates(
        segments,
        excitement_peaks,
        min_duration=15.0,
        max_duration=60.0,
        limit=3,
        lookback_seconds=20.0,
    )
    
    print(f"✓ Generated {len(candidates)} clip candidates")
    for candidate in candidates:
        print(f"  Clip {candidate.index}: {candidate.start:.1f}s-{candidate.end:.1f}s "
              f"(score: {candidate.score}) - {candidate.title}")


if __name__ == "__main__":
    print("=" * 60)
    print("Football Scorer Unit Tests")
    print("=" * 60)
    
    test_audio_energy_analysis()
    test_excitement_peak_detection()
    test_football_window_scoring()
    test_build_football_candidates()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
