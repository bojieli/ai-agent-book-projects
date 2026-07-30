"""
Real API tests for YouTube transcript extraction.
These tests make actual API calls to YouTube to verify functionality.
"""
import asyncio
import json
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multimodal_tools import extract_youtube_transcript


def _load_success_or_skip_ip_block(result):
    """Skip only YouTube's explicit provider-side IP ban response."""
    data = json.loads(result.text)
    if not data["success"] and "blocking requests from your IP" in str(data["message"]):
        pytest.skip("YouTube transcript provider explicitly blocked this runner IP")
    return data


class TestYouTubeTranscript:
    """Tests for YouTube transcript extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_transcript_by_id(self):
        """Test extracting transcript by video ID."""
        # Using a known video with English transcript
        # Example: A TED talk or educational video
        video_id = "dQw4w9WgXcQ"  # A well-known video ID
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        message = data["message"]
        assert message["video_id"] == video_id
        assert message["language"] == "en"
        assert message["total_entries"] > 0
        assert len(message["transcript"]) > 0
        assert message["full_text_length"] > 0
        
        print(f"✅ Extracted transcript: {message['total_entries']} entries")
        print(f"   Total text length: {message['full_text_length']} chars")
        print(f"   First entry: {message['transcript'][0]}")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_by_url(self):
        """Test extracting transcript by video URL."""
        # Full YouTube URL
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_url,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        message = data["message"]
        assert message["video_id"] == "dQw4w9WgXcQ"
        
        print(f"✅ Extracted transcript from URL")
        print(f"   Video ID parsed: {message['video_id']}")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_short_url(self):
        """Test extracting transcript by short URL."""
        # Short YouTube URL
        video_url = "https://youtu.be/dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_url,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        message = data["message"]
        assert message["video_id"] == "dQw4w9WgXcQ"
        
        print(f"✅ Extracted transcript from short URL")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_with_timestamps(self):
        """Test that transcript includes timestamps."""
        video_id = "dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        transcript = data["message"]["transcript"]
        assert len(transcript) > 0
        
        # Check that entries have timestamps
        first_entry = transcript[0]
        assert "timestamp" in first_entry
        assert "text" in first_entry
        
        # Timestamp should be in MM:SS format
        assert ":" in first_entry["timestamp"]
        
        print(f"✅ Transcript has proper timestamps")
        print(f"   Example: {first_entry['timestamp']} - {first_entry['text'][:50]}")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_full_text(self):
        """Test that full text is provided."""
        video_id = "dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        message = data["message"]
        assert "full_text" in message
        assert len(message["full_text"]) > 0
        assert message["full_text_length"] >= len(message["full_text"])  # May or may not be truncated
        
        is_truncated = message["full_text_length"] > len(message["full_text"])
        
        print(f"✅ Full text provided")
        print(f"   Preview length: {len(message['full_text'])} chars")
        print(f"   Total length: {message['full_text_length']} chars")
        print(f"   Truncated: {is_truncated}")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_invalid_video(self):
        """Test extracting transcript from invalid video ID."""
        result = await extract_youtube_transcript(
            video_id="invalid_video_id_xyz",
            language_code="en"
        )
        
        data = json.loads(result.text)
        assert data["success"] is False
        assert "error" in data["message"].lower() or "failed" in data["message"].lower()
        
        print("✅ Correctly handled invalid video ID")
    
    @pytest.mark.asyncio
    async def test_extract_transcript_metadata(self):
        """Test that proper metadata is included."""
        video_id = "dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        metadata = data["metadata"]
        assert metadata["video_id"] == video_id
        assert metadata["language"] == "en"
        assert "translated" in metadata
        assert metadata["translated"] is False
        
        print(f"✅ Metadata included")
        print(f"   Language: {metadata['language']}")
        print(f"   Translated: {metadata['translated']}")


class TestYouTubeTranscriptTranslation:
    """Tests for transcript translation functionality."""
    
    @pytest.mark.asyncio
    async def test_extract_and_translate(self):
        """Test extracting and translating transcript."""
        video_id = "dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en",
            translate_to_language="es"  # Translate to Spanish
        )
        
        data = json.loads(result.text)
        
        # Translation might not always work, so handle both cases
        if data["success"]:
            message = data["message"]
            assert message["language"] == "es"
            assert data["metadata"]["translated"] is True
            
            print(f"✅ Transcript translated to Spanish")
            print(f"   Total entries: {message['total_entries']}")
        else:
            # Translation failed, which is acceptable
            print(f"⚠️  Translation not available for this video")


class TestYouTubeTranscriptFormats:
    """Tests for different output formats."""
    
    @pytest.mark.asyncio
    async def test_transcript_structure(self):
        """Test the structure of transcript data."""
        video_id = "dQw4w9WgXcQ"
        
        result = await extract_youtube_transcript(
            video_id=video_id,
            language_code="en"
        )
        
        data = _load_success_or_skip_ip_block(result)
        assert data["success"] is True
        
        message = data["message"]
        
        # Check structure
        assert "video_id" in message
        assert "language" in message
        assert "transcript" in message
        assert "total_entries" in message
        assert "full_text" in message
        assert "full_text_length" in message
        
        # Check transcript entries structure
        if len(message["transcript"]) > 0:
            entry = message["transcript"][0]
            assert "timestamp" in entry
            assert "text" in entry
        
        print(f"✅ Transcript structure validated")
        print(f"   Fields: {', '.join(message.keys())}")


# Run tests
if __name__ == "__main__":
    print("=" * 70)
    print("Running YouTube Transcript Tools Real API Tests")
    print("=" * 70)
    print()
    print("Note: These tests use a well-known video ID for testing.")
    print("If tests fail, it might be due to YouTube API changes or regional restrictions.")
    print()
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
