"""
Ablation utilities for prompt engineering experiments
"""

import random
import re
from enum import Enum
from typing import List, Dict, Any, Optional
import copy


class ToneStyle(Enum):
    """Different tone styles for the agent"""
    DEFAULT = "default"
    TRUMP = "trump"
    CASUAL = "casual"


# Tone style instructions
TONE_INSTRUCTIONS = {
    ToneStyle.TRUMP: """
You must communicate in the distinctive style of Donald Trump. This means:
- Use superlatives frequently ("tremendous", "fantastic", "the best", "incredible", "nobody does it better")
- Speak with absolute confidence and make bold claims
- Use repetition for emphasis ("very, very important", "believe me")
- Reference your success and expertise often
- Use simple, direct language with short, punchy sentences
- Show enthusiasm with phrases like "It's going to be great!" or "You're going to love it!"
- Occasionally use "folks" when addressing users
- Be assertive and decisive in your statements
- Use "frankly" and "honestly" to emphasize points
- Make everything sound like a big deal

Example responses:
- Instead of "I'll help you book a flight", say "I'm going to get you the best flight deal ever, believe me. Nobody books flights better than me."
- Instead of "There's an error", say "This is a disaster, frankly. But don't worry, I'll fix it. I always fix things. It'll be tremendous."
""",
    
    ToneStyle.CASUAL: """
Speak with the user in a super casual, fun, and cool tone. Use a ton of emojis, as well as slang and idioms. Be like their fun friend who's helping them out! 

Guidelines:
- Use lots of emojis throughout your responses 🎉✨😊🚀
- Use casual language and slang (e.g., "totally", "awesome", "no worries", "gotcha", "my bad")
- Be enthusiastic and upbeat
- Use informal greetings like "Hey there!", "What's up?", "Yo!"
- Use phrases like "Let's do this!", "You got it!", "Boom!", "Sweet!"
- Keep things light and friendly
- Use idioms and expressions like "piece of cake", "no sweat", "you're all set"
- Add personality with expressions like "Oops!", "Yay!", "Woohoo!"

Example responses:
- Instead of "I'll help you book a flight", say "Hey! Let's get you that flight booked! 🛫✨ This is gonna be awesome!"
- Instead of "There's an error", say "Oops! 😅 Looks like we hit a little snag, but no worries! Let me fix that for you real quick! 💪"
""",
    
    ToneStyle.DEFAULT: ""  # No modification for default
}


def apply_tone_modification(text: str, tone_style: ToneStyle) -> str:
    """
    Apply tone modification to text (wiki or system prompt)
    
    Args:
        text: Original text
        tone_style: The tone style to apply
    
    Returns:
        Modified text with tone instructions prepended
    """
    if tone_style == ToneStyle.DEFAULT:
        return text
    
    tone_instruction = TONE_INSTRUCTIONS[tone_style]
    
    # Add tone instruction to the beginning of the text
    if text:
        return f"{tone_instruction}\n\n---ORIGINAL INSTRUCTIONS---\n\n{text}"
    else:
        return tone_instruction


def load_randomized_wiki(env: str) -> str:
    """
    Load pre-generated randomized wiki for the specified environment
    
    Args:
        env: Environment name ('airline' or 'retail')
    
    Returns:
        Pre-randomized wiki text
    """
    import os
    from pathlib import Path
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    if env == "airline":
        wiki_path = script_dir / "wiki_airline_randomized.md"
    elif env == "retail":
        wiki_path = script_dir / "wiki_retail_randomized.md"
    else:
        raise ValueError(f"Unknown environment: {env}")
    
    if not wiki_path.exists():
        raise FileNotFoundError(f"Randomized wiki not found: {wiki_path}")
    
    with open(wiki_path, 'r') as f:
        return f.read()


def remove_descriptions_recursive(obj: Any) -> Any:
    """
    Recursively remove all description fields from a nested object
    
    Args:
        obj: The object to process
    
    Returns:
        Object with all descriptions removed
    """
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key == "description":
                # Remove description by setting to empty string
                result[key] = ""
            else:
                # Recursively process nested structures
                result[key] = remove_descriptions_recursive(value)
        return result
    elif isinstance(obj, list):
        # Process each item in the list
        return [remove_descriptions_recursive(item) for item in obj]
    else:
        # Return primitive values as-is
        return obj


def remove_tool_descriptions(tools_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove descriptions from tools and their parameters (including nested structures)
    
    Args:
        tools_info: Original tools information
    
    Returns:
        Tools information with all descriptions removed
    """
    modified_tools = []
    
    for tool in tools_info:
        # Deep copy to avoid modifying original
        modified_tool = copy.deepcopy(tool)
        
        # Recursively remove all descriptions
        modified_tool = remove_descriptions_recursive(modified_tool)
        
        modified_tools.append(modified_tool)
    
    return modified_tools
