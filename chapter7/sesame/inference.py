#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sesame CSM (1B) TTS - Inference Script

This script loads a trained LoRA model and generates speech from text.
"""

import argparse
import torch
import soundfile as sf
from pathlib import Path
from datasets import load_dataset, Audio
from unsloth import FastModel
from transformers import CsmForConditionalGeneration
from peft import PeftModel


def load_model(base_model_name: str, lora_path: str = None, load_in_4bit: bool = False):
    """
    Load the base model and optionally apply LoRA adapters.
    
    Args:
        base_model_name: Name or path of the base model
        lora_path: Path to saved LoRA adapters (optional)
        load_in_4bit: Whether to load model in 4-bit quantization
    
    Returns:
        model, processor
    """
    print(f"Loading base model: {base_model_name}")
    model, processor = FastModel.from_pretrained(
        model_name=base_model_name,
        max_seq_length=2048,
        dtype=None,  # Auto-detection
        auto_model=CsmForConditionalGeneration,
        load_in_4bit=load_in_4bit,
    )
    
    if lora_path:
        print(f"Loading LoRA adapters from: {lora_path}")
        model = PeftModel.from_pretrained(model, lora_path)
    
    return model, processor


def load_dataset_for_context(dataset_name: str = "maxbsoft/mrdragonfox-elise", split: str = "train"):
    """
    Load the dataset for voice context examples.
    
    Args:
        dataset_name: Name of the dataset
        split: Dataset split to use
    
    Returns:
        Dataset
    """
    print(f"Loading dataset: {dataset_name}")
    raw_ds = load_dataset(dataset_name, split=split)
    target_sampling_rate = 24000
    raw_ds = raw_ds.cast_column("audio", Audio(sampling_rate=target_sampling_rate))
    print(f"Loaded {len(raw_ds)} examples from dataset")
    return raw_ds


def generate_speech(
    model,
    processor,
    text: str,
    speaker_id: int = 0,
    max_new_tokens: int = 125,
    output_path: str = "output.wav",
    dataset_context_idx: int = None,
    dataset_name: str = "maxbsoft/mrdragonfox-elise",
):
    """
    Generate speech from text.
    
    Args:
        model: The loaded model
        processor: The processor
        text: Text to convert to speech
        speaker_id: Speaker ID (for multi-speaker models)
        max_new_tokens: Maximum number of tokens to generate (125 tokens ≈ 10 seconds)
        output_path: Path to save the output audio file
        dataset_context_idx: Optional dataset index to use for voice consistency
        dataset_name: Name of the dataset to load context from
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Prepare inputs based on whether context is provided
    if dataset_context_idx is not None:
        print(f"Generating speech with voice context from dataset index: {dataset_context_idx}")
        print(f"Target text: '{text}'")
        
        # Load dataset and get context example
        raw_ds = load_dataset_for_context(dataset_name)
        context_example = raw_ds[dataset_context_idx]
        context_audio = context_example["audio"]["array"]
        context_text = context_example["text"]
        
        print(f"Context text: '{context_text}'")
        
        # Use conversation format with audio context for voice consistency
        conversation = [
            {
                "role": str(speaker_id),
                "content": [
                    {"type": "text", "text": context_text},
                    {"type": "audio", "path": context_audio}
                ]
            },
            {
                "role": str(speaker_id),
                "content": [{"type": "text", "text": text}]
            },
        ]
        inputs = processor.apply_chat_template(
            conversation,
            tokenize=True,
            return_dict=True,
        ).to(device)
    else:
        print(f"Generating speech without context for: '{text}'")
        
        # Simple text-only input
        inputs = processor(
            f"[{speaker_id}]{text}",
            add_special_tokens=True,
            return_tensors="pt"
        ).to(device)
    
    # Generate audio
    print("Generating audio...")
    with torch.no_grad():
        audio_values = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=max_new_tokens,
            output_audio=True,
        )
    
    # Save audio
    audio = audio_values[0].to(torch.float32).cpu().numpy()
    sf.write(output_path, audio, 24000)
    print(f"Audio saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate speech using Sesame CSM TTS model"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="unsloth/csm-1b",
        help="Base model name or path (default: unsloth/csm-1b)"
    )
    parser.add_argument(
        "--lora-path",
        type=str,
        default=None,
        help="Path to saved LoRA adapters (optional)"
    )
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Text to convert to speech"
    )
    parser.add_argument(
        "--speaker-id",
        type=int,
        default=0,
        help="Speaker ID (default: 0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.wav",
        help="Output audio file path (default: output.wav)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=125,
        help="Maximum tokens to generate (125 ≈ 10 seconds) (default: 125)"
    )
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="Load model in 4-bit quantization to reduce memory usage"
    )
    parser.add_argument(
        "--dataset-context-idx",
        type=int,
        default=None,
        help="Dataset index to use for voice consistency (e.g., 3 or 4 from training examples)"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="maxbsoft/mrdragonfox-elise",
        help="Dataset name to load context from (default: public Elise mirror)"
    )
    
    args = parser.parse_args()
    
    # Load model
    model, processor = load_model(
        base_model_name=args.base_model,
        lora_path=args.lora_path,
        load_in_4bit=args.load_in_4bit
    )
    
    # Generate speech
    generate_speech(
        model=model,
        processor=processor,
        text=args.text,
        speaker_id=args.speaker_id,
        max_new_tokens=args.max_tokens,
        output_path=args.output,
        dataset_context_idx=args.dataset_context_idx,
        dataset_name=args.dataset_name,
    )


if __name__ == "__main__":
    main()
