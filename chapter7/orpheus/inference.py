#!/usr/bin/env python3
"""
Orpheus TTS Inference Script

This script provides a standalone inference interface for the Orpheus text-to-speech model.
It supports both single-speaker and multi-speaker TTS generation.

Usage:
    python inference.py

Or import as a module:
    from inference import OrpheusInference
    tts = OrpheusInference()
    audio_files = tts.generate(prompts=["Hello world"])
"""

import os
import torch
import torchaudio.transforms as T
from unsloth import FastLanguageModel
from snac import SNAC
import soundfile as sf
from typing import List, Optional


class OrpheusInference:
    """
    Orpheus TTS Inference Engine
    
    Supports expressive speech generation with emotion tags like:
    <laugh>, <giggles>, <chuckle>, <sigh>, <cough>, <sniffle>, 
    <groan>, <yawn>, <gasp>, etc.
    
    Example usage:
        tts = OrpheusInference()
        tts.generate(prompts=["I missed you <laugh> so much!"])
    """
    
    def __init__(
        self,
        model_path: str = "unsloth/orpheus-3b-0.1-ft",
        lora_path: Optional[str] = None,
        max_seq_length: int = 2048,
        load_in_4bit: bool = False,
        device: str = "cuda"
    ):
        """
        Initialize the Orpheus TTS inference engine.
        
        Args:
            model_path: HuggingFace model path or local path
            lora_path: Optional path to LoRA adapters
            max_seq_length: Maximum sequence length for the model
            load_in_4bit: Whether to use 4-bit quantization
            device: Device to run inference on ('cuda' or 'cpu')
        """
        self.device = device
        self.sample_rate = 24000  # SNAC model uses 24kHz
        
        print(f"Loading model from {model_path}...")
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_path,
            max_seq_length=max_seq_length,
            dtype=None,
            load_in_4bit=load_in_4bit,
        )
        
        # Load LoRA adapters if provided
        if lora_path:
            print(f"Loading LoRA adapters from {lora_path}...")
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, lora_path)
        
        # Enable fast inference
        FastLanguageModel.for_inference(self.model)
        
        # Load SNAC audio codec
        print("Loading SNAC audio codec...")
        self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
        self.snac_model = self.snac_model.to("cpu")  # Keep on CPU to save VRAM
        
        # Special tokens
        self.start_of_human = 128259
        self.end_of_text = 128009
        self.end_of_human = 128260
        self.start_of_ai = 128261
        self.start_of_speech = 128257
        self.end_of_speech = 128258
        self.pad_token = 128263
        
        print("Model ready for inference!")
    
    def _prepare_inputs(
        self,
        prompts: List[str],
        voice: Optional[str] = None
    ) -> tuple:
        """
        Prepare input tensors for the model.
        
        Args:
            prompts: List of text prompts to convert to speech
            voice: Optional voice/speaker name for multi-speaker models
        
        Returns:
            Tuple of (input_ids, attention_mask)
        """
        # Add voice prefix if specified
        prompts_ = [(f"{voice}: " + p) if voice else p for p in prompts]
        
        # Tokenize all prompts
        all_input_ids = []
        for prompt in prompts_:
            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
            all_input_ids.append(input_ids)
        
        # Add special tokens: SOH SOT Text EOT EOH
        start_token = torch.tensor([[self.start_of_human]], dtype=torch.int64)
        end_tokens = torch.tensor([[self.end_of_text, self.end_of_human]], dtype=torch.int64)
        
        all_modified_input_ids = []
        for input_ids in all_input_ids:
            modified_input_ids = torch.cat([start_token, input_ids, end_tokens], dim=1)
            all_modified_input_ids.append(modified_input_ids)
        
        # Pad all sequences to the same length
        max_length = max([ids.shape[1] for ids in all_modified_input_ids])
        all_padded_tensors = []
        all_attention_masks = []
        
        for modified_input_ids in all_modified_input_ids:
            padding = max_length - modified_input_ids.shape[1]
            padded_tensor = torch.cat(
                [torch.full((1, padding), self.pad_token, dtype=torch.int64), modified_input_ids],
                dim=1
            )
            attention_mask = torch.cat(
                [torch.zeros((1, padding), dtype=torch.int64),
                 torch.ones((1, modified_input_ids.shape[1]), dtype=torch.int64)],
                dim=1
            )
            all_padded_tensors.append(padded_tensor)
            all_attention_masks.append(attention_mask)
        
        input_ids = torch.cat(all_padded_tensors, dim=0).to(self.device)
        attention_mask = torch.cat(all_attention_masks, dim=0).to(self.device)
        
        return input_ids, attention_mask
    
    def _decode_audio(self, generated_ids: torch.Tensor) -> List[torch.Tensor]:
        """
        Decode generated token IDs into audio waveforms.
        
        Args:
            generated_ids: Tensor of generated token IDs
        
        Returns:
            List of audio waveform tensors
        """
        # Find start of speech token
        token_to_find = self.start_of_speech
        token_to_remove = self.end_of_speech
        
        token_indices = (generated_ids == token_to_find).nonzero(as_tuple=True)
        
        # Crop to speech tokens only
        if len(token_indices[1]) > 0:
            last_occurrence_idx = token_indices[1][-1].item()
            cropped_tensor = generated_ids[:, last_occurrence_idx+1:]
        else:
            cropped_tensor = generated_ids
        
        # Remove end of speech tokens
        processed_rows = []
        for row in cropped_tensor:
            masked_row = row[row != token_to_remove]
            processed_rows.append(masked_row)
        
        # Prepare code lists for SNAC decoder
        code_lists = []
        for row in processed_rows:
            row_length = row.size(0)
            new_length = (row_length // 7) * 7  # Each frame has 7 tokens
            trimmed_row = row[:new_length]
            trimmed_row = [t.item() - 128266 for t in trimmed_row]  # Offset for audio tokens
            code_lists.append(trimmed_row)
        
        # Decode using SNAC
        audio_samples = []
        for code_list in code_lists:
            audio = self._redistribute_codes(code_list)
            audio_samples.append(audio)
        
        return audio_samples
    
    def _redistribute_codes(self, code_list: List[int]) -> torch.Tensor:
        """
        Redistribute flattened codes back into SNAC's 3-layer format.
        
        Terminates early if invalid codes are detected (out of range 0-4095)
        to prevent machine noise at the end of audio.
        
        Args:
            code_list: Flattened list of audio codes
        
        Returns:
            Audio waveform tensor
        """
        layer_1 = []
        layer_2 = []
        layer_3 = []
        
        # SNAC codebook size is 4096 per layer (valid range: 0-4095)
        max_code_value = 4095
        
        for i in range(len(code_list) // 7):
            # Extract codes with offsets
            c0 = code_list[7*i]
            c1 = code_list[7*i+1] - 4096
            c2 = code_list[7*i+2] - (2*4096)
            c3 = code_list[7*i+3] - (3*4096)
            c4 = code_list[7*i+4] - (4*4096)
            c5 = code_list[7*i+5] - (5*4096)
            c6 = code_list[7*i+6] - (6*4096)
            
            # Check if any code is out of valid range
            # If so, terminate audio generation to avoid machine noise
            if (c0 < 0 or c0 > max_code_value or
                c1 < 0 or c1 > max_code_value or
                c2 < 0 or c2 > max_code_value or
                c3 < 0 or c3 > max_code_value or
                c4 < 0 or c4 > max_code_value or
                c5 < 0 or c5 > max_code_value or
                c6 < 0 or c6 > max_code_value):
                print(f"Invalid audio code detected at frame {i}, terminating audio generation")
                break
            
            layer_1.append(c0)
            layer_2.append(c1)
            layer_3.append(c2)
            layer_3.append(c3)
            layer_2.append(c4)
            layer_3.append(c5)
            layer_3.append(c6)
        
        # Return empty/silent audio if no valid codes were found
        if not layer_1:
            print("Warning: No valid audio codes found, returning silence")
            return torch.zeros(1, 1, 1000)  # Small silent audio
        
        codes = [
            torch.tensor(layer_1, dtype=torch.long).unsqueeze(0),
            torch.tensor(layer_2, dtype=torch.long).unsqueeze(0),
            torch.tensor(layer_3, dtype=torch.long).unsqueeze(0)
        ]
        
        audio_hat = self.snac_model.decode(codes)
        return audio_hat
    
    def generate(
        self,
        prompts: List[str],
        output_dir: str = "generated_audio",
        voice: Optional[str] = None,
        max_new_tokens: int = 1200,
        temperature: float = 0.6,
        top_p: float = 0.95,
        repetition_penalty: float = 1.1,
        do_sample: bool = True
    ) -> List[str]:
        """
        Generate speech from text prompts.
        
        Orpheus supports emotion/expression tags in your prompts:
        - <laugh>, <giggles>, <chuckle> - Laughter variations
        - <sigh>, <gasp> - Emotional expressions
        - <yawn>, <cough>, <sniffle>, <groan> - Physical sounds
        
        These tags are treated as special tokens that trigger corresponding
        audio patterns learned during training. The Elise dataset contains
        hundreds of examples with these tags.
        
        Example prompts:
            "Hey there <giggles> welcome to my channel!"
            "I missed you <laugh> so much!"
            "That's so beautiful <sigh> it brings back memories."
        
        Args:
            prompts: List of text prompts to convert to speech (can include tags)
            output_dir: Directory to save generated audio files
            voice: Optional voice/speaker name for multi-speaker models
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling threshold
            repetition_penalty: Penalty for repeating tokens
            do_sample: Whether to use sampling (vs greedy decoding)
        
        Returns:
            List of paths to generated audio files
        """
        print(f"Generating speech for {len(prompts)} prompt(s)...")
        
        # Prepare inputs
        input_ids, attention_mask = self._prepare_inputs(prompts, voice)
        
        # Generate tokens
        print("Generating tokens...")
        with torch.inference_mode():
            generated_ids = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                num_return_sequences=1,
                eos_token_id=self.end_of_speech,
                use_cache=True
            )
        
        # Decode to audio
        print("Decoding audio...")
        audio_samples = self._decode_audio(generated_ids)
        
        # Save to files
        os.makedirs(output_dir, exist_ok=True)
        output_paths = []
        
        for idx, audio_sample in enumerate(audio_samples):
            # Convert tensor to numpy (detach first to avoid gradient tracking)
            audio_numpy = audio_sample.squeeze().detach().cpu().numpy()
            
            # Save as WAV file
            output_path = os.path.join(output_dir, f"output_{idx}.wav")
            sf.write(output_path, audio_numpy, self.sample_rate)
            output_paths.append(output_path)
            print(f"✓ Saved: {output_path}")
        
        return output_paths


def main():
    """Main function for standalone execution."""
    
    # Example prompts with emotion tags
    # Orpheus supports special tags like <laugh>, <giggles>, <chuckle>, <sigh>, 
    # <cough>, <sniffle>, <groan>, <yawn>, <gasp>, etc.
    # These tags are enclosed in angle brackets and will be treated as special tokens
    # that the model learned during training to generate corresponding audio patterns.
    prompts = [
        "Hey there my name is Elise, <giggles> and I'm a speech generation model that can sound like a person.",
        "I missed you <laugh> so much! It's been way too long.",
        "This is absolutely amazing <gasp> I can't believe it worked!",
        "I'm so tired <yawn> after working all day on this project.",
        "That's really touching <sigh> it reminds me of home.",
    ]
    
    # Initialize inference engine
    tts = OrpheusInference(
        model_path="unsloth/orpheus-3b-0.1-ft",
        lora_path="lora_model" if os.path.exists("lora_model") else None,
        load_in_4bit=False
    )
    
    # Generate speech
    output_files = tts.generate(
        prompts=prompts,
        output_dir="generated_audio",
        temperature=0.6,
        top_p=0.95,
        max_new_tokens=1200
    )
    
    print(f"\n✅ Successfully generated {len(output_files)} audio file(s)!")
    print(f"📁 Output directory: generated_audio/")
    
    # For multi-speaker models, you can specify a voice:
    # output_files = tts.generate(prompts=prompts, voice="speaker_name")


if __name__ == "__main__":
    main()

