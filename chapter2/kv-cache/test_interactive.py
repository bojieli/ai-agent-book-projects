#!/usr/bin/env python3
"""
Test script for interactive mode selection
"""

from main import select_mode_interactive

def test_mode_selection(monkeypatch):
    """Test the interactive mode selection without running the agent"""
    
    print("🧪 Testing Interactive Mode Selection")
    print("(This is a test - no agent will actually run)")
    
    # Test the selection menu
    monkeypatch.setattr("builtins.input", lambda _prompt: "7")
    selected = select_mode_interactive()
    assert selected == "compare"
    
    print("\n" + "="*60)
    if selected == "compare":
        print("✅ You selected: Compare all modes")
        print("In real usage, this would run all 6 implementations and compare them.")
    else:
        print(f"✅ You selected: {selected}")
        print(f"In real usage, this would run the '{selected}' implementation.")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_mode_selection()
