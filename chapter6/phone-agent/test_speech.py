import struct

from speech import pcm16_wav, read_pcm16_wav, sha256_bytes


def test_pcm_wav_round_trip_is_exact():
    pcm = b"".join(struct.pack("<h", sample) for sample in (0, 100, -100, 32767, -32768))
    wav = pcm16_wav(pcm, 16_000)
    decoded, rate = read_pcm16_wav(wav)
    assert decoded == pcm
    assert rate == 16_000
    assert len(sha256_bytes(wav)) == 64


def test_speech_source_has_no_mock_or_tone_fallback():
    source = __import__("pathlib").Path(__file__).with_name("speech.py").read_text()
    assert "SystemSpeechSynthesizer" in source
    assert "WhisperASR" in source
    assert 'fallback_used": False' in source
    assert "440" not in source
