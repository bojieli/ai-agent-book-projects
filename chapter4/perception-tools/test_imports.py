"""
Test script to verify all imports and basic module loading.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing imports...")

try:
    print("\n✓ Importing base module...")
    from base import ActionResponse, DocumentMetadata, is_url, validate_file_path
    
    print("✓ Importing search_tools module...")
    from search_tools import search_web, download_file, search_knowledge_base
    
    print("✓ Importing multimodal_tools module...")
    from multimodal_tools import read_webpage, read_document, parse_image, parse_video
    
    print("✓ Importing filesystem_tools module...")
    from filesystem_tools import read_file, grep_search, summarize_text
    
    print("✓ Importing public_data_tools module...")
    from public_data_tools import (
        get_weather, get_stock_price, convert_currency,
        search_wikipedia, search_arxiv, search_wayback
    )
    
    print("✓ Importing private_data_tools module...")
    from private_data_tools import get_calendar_events, search_notion

    print("✓ Importing xquik_tools module...")
    from xquik_tools import search_x_posts
    
    print("✓ Importing main module...")
    from main import mcp
    
    print("\n" + "="*80)
    print("✅ All imports successful!")
    print("="*80)
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test ActionResponse
    response = ActionResponse(
        success=True,
        message="Test message",
        metadata={"test": "value"}
    )
    assert response.success == True
    print("✓ ActionResponse working")
    
    # Test is_url
    assert is_url("https://example.com") == True
    assert is_url("/path/to/file") == False
    print("✓ is_url working")
    
    print("\n" + "="*80)
    print("✅ All tests passed!")
    print("="*80)
    print("\nℹ️  The MCP server is ready to use.")
    print("   Run 'python src/main.py' to start the server.")
    print("   Run 'python quickstart.py' to test various tools.")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nℹ️  You may need to install dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
