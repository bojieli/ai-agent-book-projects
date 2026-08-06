#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sesame CSM (1B) TTS - Batch Inference Script

This script loads a trained LoRA model and generates speech from multiple texts.
"""

import argparse
import json
import torch
import soundfile as sf
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from datasets import load_dataset, Audio
from unsloth import FastModel
from transformers import CsmForConditionalGeneration
from peft import PeftModel


def load_model(base_model_name: str, lora_path: str = None, load_in_4bit: bool = False):
    """Load the base model and optionally apply LoRA adapters."""
    print(f"Loading base model: {base_model_name}")
    model, processor = FastModel.from_pretrained(
        model_name=base_model_name,
        max_seq_length=2048,
        dtype=None,
        auto_model=CsmForConditionalGeneration,
        load_in_4bit=load_in_4bit,
    )
    
    if lora_path:
        print(f"Loading LoRA adapters from: {lora_path}")
        model = PeftModel.from_pretrained(model, lora_path)
    
    return model, processor


def load_texts_from_file(input_file: str) -> List[Dict]:
    """
    Load texts from a JSON file.
    
    Expected format:
    [
        {"text": "Hello world", "speaker_id": 0, "output": "hello.wav"},
        {"text": "Another sentence", "speaker_id": 0, "output": "another.wav"}
    ]
    
    Or simple text file (one text per line):
    Hello world
    Another sentence
    """
    input_path = Path(input_file)
    
    if input_path.suffix == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Plain text file
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        return [
            {
                "text": line,
                "speaker_id": 0,
                "output": f"output_{i:04d}.wav"
            }
            for i, line in enumerate(lines)
        ]


def load_dataset_for_context(dataset_name: str = "maxbsoft/mrdragonfox-elise", split: str = "train"):
    """Load the dataset for voice context examples."""
    raw_ds = load_dataset(dataset_name, split=split)
    target_sampling_rate = 24000
    raw_ds = raw_ds.cast_column("audio", Audio(sampling_rate=target_sampling_rate))
    return raw_ds


def generate_speech_batch(
    model,
    processor,
    texts: List[Dict],
    output_dir: str,
    max_new_tokens: int = 125,
    dataset_name: str = "maxbsoft/mrdragonfox-elise",
):
    """Generate speech for multiple texts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load dataset once if any item needs context
    raw_ds = None
    needs_context = any(isinstance(item, dict) and item.get("dataset_context_idx") is not None for item in texts)
    if needs_context:
        print(f"Loading dataset: {dataset_name}")
        raw_ds = load_dataset_for_context(dataset_name)
        print(f"Loaded {len(raw_ds)} examples from dataset")
    
    for item in tqdm(texts, desc="Generating speech"):
        if isinstance(item, str):
            item = {"text": item}
        elif not isinstance(item, dict):
            raise ValueError(f"Each item must be a string or dict, got: {item}")
        text = item.get("text")
        if not text:
            raise ValueError(f"Each item must have a non-empty 'text' field, got: {item}")
        speaker_id = item.get("speaker_id", 0)
        output_name = item.get("output") or f"output_{hash(text)}.wav"
        output_file = output_path / output_name
        
        # Check if dataset context is provided
        dataset_context_idx = item.get("dataset_context_idx")
        
        if dataset_context_idx is not None:
            # Generate with voice context from dataset
            context_example = raw_ds[dataset_context_idx]
            context_audio = context_example["audio"]["array"]
            context_text = context_example["text"]
            
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
            # Generate without context
            inputs = processor(
                f"[{speaker_id}]{text}",
                add_special_tokens=True,
                return_tensors="pt"
            ).to(device)
        
        # Generate audio
        with torch.no_grad():
            audio_values = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=max_new_tokens,
                output_audio=True,
            )
        
        # Save audio
        audio = audio_values[0].to(torch.float32).cpu().numpy()
        sf.write(output_file, audio, 24000)
    
    print(f"\nGenerated {len(texts)} audio files in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch generate speech using Sesame CSM TTS model"
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
        "--input-file",
        type=str,
        required=True,
        help="Input file (JSON or plain text, one text per line)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for audio files (default: outputs)"
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
        "--dataset-name",
        type=str,
        default="maxbsoft/mrdragonfox-elise",
        help="Dataset name to load context from (default: public Elise mirror)"
    )
    
    args = parser.parse_args()
    
    # Load texts
    print(f"Loading texts from: {args.input_file}")
    texts = load_texts_from_file(args.input_file)
    print(f"Loaded {len(texts)} texts")
    
    # Load model
    model, processor = load_model(
        base_model_name=args.base_model,
        lora_path=args.lora_path,
        load_in_4bit=args.load_in_4bit
    )
    
    # Generate speech
    generate_speech_batch(
        model=model,
        processor=processor,
        texts=texts,
        output_dir=args.output_dir,
        max_new_tokens=args.max_tokens,
        dataset_name=args.dataset_name,
    )


if __name__ == "__main__":
    main()
