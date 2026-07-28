# Sesame CSM (1B) TTS - Text-to-Speech Fine-tuning

## English

This directory contains scripts for fine-tuning and running inference with the Sesame CSM text-to-speech model using Unsloth.

## Files

- `sesame_csm_sft_unsloth.py` - Training script for fine-tuning the model with LoRA
- `inference.py` - Single inference script for generating speech from text
- `batch_inference.py` - Batch inference script for processing multiple texts
- `example_inputs.json` - Example input file for batch inference
- `requirements.txt` - Python dependencies

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For Conda users, install ffmpeg
conda install -c conda-forge "ffmpeg>=6.0" -y
conda install -c conda-forge libiconv -y
```

## Training

To train a model with your own dataset:

```bash
python sesame_csm_sft_unsloth.py
```

This will:
1. Load the base model `unsloth/csm-1b`
2. Add LoRA adapters
3. Fine-tune on your dataset
4. Save the LoRA adapters to `lora_model/`

## Inference

### Single Text Inference

Generate speech from a single text:

```bash
# Without context (simple generation)
python inference.py \
    --lora-path lora_model \
    --text "We just finished fine tuning a text to speech model... and it's pretty good!" \
    --output example_without_context_1.wav

# With voice context (for voice consistency) using dataset index 3
python inference.py \
    --lora-path lora_model \
    --text "Sesame is a super cool TTS model which can be fine tuned with Unsloth." \
    --dataset-context-idx 3 \
    --output example_with_context_1.wav

# Using base model only (without LoRA)
python inference.py \
    --text "Hello world, this is a test of the text to speech system."

# With custom speaker ID and longer generation
python inference.py \
    --lora-path lora_model \
    --text "This is a longer sentence that needs more tokens." \
    --speaker-id 0 \
    --max-tokens 250 \
    --output long_speech.wav

# With 4-bit quantization (lower memory)
python inference.py \
    --lora-path lora_model \
    --text "Memory efficient inference." \
    --load-in-4bit
```

### Batch Inference

Process multiple texts at once:

```bash
# From JSON file
python batch_inference.py \
    --lora-path lora_model \
    --input-file example_inputs.json \
    --output-dir batch_outputs

# From plain text file (one text per line)
python batch_inference.py \
    --lora-path lora_model \
    --input-file texts.txt \
    --output-dir batch_outputs
```

#### Input File Formats

**JSON format** (`example_inputs.json`):

Without context:
```json
[
    {
        "text": "We just finished fine tuning a text to speech model... and it's pretty good!",
        "speaker_id": 0,
        "output": "example_without_context_1.wav"
    },
    {
        "text": "Sesame is a super cool TTS model which can be fine tuned with Unsloth.",
        "speaker_id": 0,
        "output": "example_without_context_2.wav"
    }
]
```

With context (for voice consistency using dataset indices):
```json
[
    {
        "text": "Sesame is a super cool TTS model which can be fine tuned with Unsloth.",
        "speaker_id": 0,
        "dataset_context_idx": 3,
        "output": "example_with_context_1.wav"
    },
    {
        "text": "We just finished fine tuning a text to speech model... and it's pretty good!",
        "speaker_id": 0,
        "dataset_context_idx": 4,
        "output": "example_with_context_2.wav"
    }
]
```

**Note**: `dataset_context_idx` refers to the index in the training dataset (e.g., `MrDragonFox/Elise`). Indices 3 and 4 are used in the training script examples.

**Plain text format** (one sentence per line, no context support):
```
Hello world, this is the first sentence.
This is the second sentence.
This is the third sentence.
```

## Parameters

### Common Parameters

- `--base-model`: Base model name or path (default: `unsloth/csm-1b`)
- `--lora-path`: Path to saved LoRA adapters (optional)
- `--load-in-4bit`: Load model in 4-bit quantization to reduce memory usage

### Inference Parameters

- `--text`: Text to convert to speech
- `--speaker-id`: Speaker ID for multi-speaker models (default: 0)
- `--output`: Output audio file path (default: `output.wav`)
- `--max-tokens`: Maximum tokens to generate (125 ≈ 10 seconds of audio)
- `--dataset-context-idx`: Dataset index to use for voice consistency (e.g., 3 or 4 from training examples)
- `--dataset-name`: Dataset name to load context from (default: `MrDragonFox/Elise`)

### Batch Inference Parameters

- `--input-file`: Input file (JSON or plain text)
- `--output-dir`: Output directory for audio files (default: `outputs`)

## Model Information

- **Base Model**: Sesame CSM (1B) - A compact text-to-speech model
- **Output Format**: 24kHz WAV audio
- **Token-to-Time Ratio**: Approximately 125 tokens = 10 seconds of audio
- **Multi-speaker**: Supports multiple speakers via speaker IDs

## Advanced Usage

### Voice Consistency with Context

For better voice consistency, you can provide audio context from the dataset (see `sesame_csm_sft_unsloth.py` lines 320-390 for examples):

```python
from inference import load_model, generate_speech

model, processor = load_model("unsloth/csm-1b", "lora_model")

# Use dataset index 3 for voice consistency (same as training script)
generate_speech(
    model=model,
    processor=processor,
    text="Sesame is a super cool TTS model which can be fine tuned with Unsloth.",
    dataset_context_idx=3,
    dataset_name="MrDragonFox/Elise",
    output_path="output_with_context.wav"
)
```

The inference scripts automatically load the audio and text from the specified dataset index, ensuring consistency with the training approach.

## Memory Requirements

- **Base model**: ~4-6GB VRAM
- **Base model + LoRA training**: ~8-12GB VRAM
- **With 4-bit quantization**: ~2-3GB VRAM
- **Inference only**: ~2-4GB VRAM

Use `--load-in-4bit` flag if you have limited GPU memory.

## Troubleshooting

### AssertionError during generation

If you encounter `AssertionError` during `model.generate()`, ensure you're passing tensors correctly:

```python
# ❌ Wrong
audio_values = model.generate(**inputs, max_new_tokens=125)

# ✅ Correct
audio_values = model.generate(
    input_ids=inputs["input_ids"],
    attention_mask=inputs.get("attention_mask"),
    max_new_tokens=125,
    output_audio=True
)
```

### Out of memory

- Use `--load-in-4bit` flag
- Reduce `max_new_tokens`
- Process texts one at a time instead of batching
- Use a smaller batch size during training

## Resources

- [Unsloth Documentation](https://docs.unsloth.ai/)
- [Unsloth TTS Guide](https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning)
- [Unsloth Discord](https://discord.gg/unsloth)
- [Unsloth GitHub](https://github.com/unslothai/unsloth)

## License

This project uses the Unsloth library and Sesame CSM model. Please refer to their respective licenses.

---

## 中文

# Sesame CSM（1B）TTS：文本转语音微调

## 文件

项目包含训练脚本、单条推理脚本、批量推理脚本、依赖文件以及数据处理相关配置。

## 安装

```bash
pip install -r requirements.txt

# Conda 用户可安装 ffmpeg
conda install -c conda-forge ffmpeg
```

请根据本机 CUDA 版本安装匹配的 PyTorch，并确认 FFmpeg 可以正常处理音频。

## 训练

训练脚本加载 Sesame CSM 1B 基础模型和语音数据集，通过 LoRA 进行参数高效微调。运行前请检查模型名称、数据集、输出目录、批量大小和训练轮数。

## 推理

### 单条文本推理

推理脚本支持无上下文生成、使用数据集样本作为声音上下文、仅加载基础模型、自定义说话人 ID、更长生成长度以及 4-bit 量化。

### 批量推理

批量脚本可从 JSON 文件或逐行文本文件读取输入，并为每条文本生成独立音频。

## 参数

常用参数包括模型与适配器路径、输入文本、输出路径、说话人 ID、上下文样本索引、最大生成长度、温度和量化开关。批量模式还支持输入文件、输出目录和失败重试设置。

## 模型信息

CSM 是一类上下文语音模型，可利用文本、说话人标识和参考语音生成具有一致音色的语音。本实验围绕 1B 参数版本进行微调。

## 高级用法

### 使用上下文保持声音一致

可选择训练数据中的音频作为上下文。训练与推理应使用一致的上下文格式和说话人 ID；英文示例使用数据集索引 3。

## 显存需求

实际显存取决于序列长度、上下文音频、批量大小和精度。4-bit 量化可降低推理显存，训练时可使用梯度累积与梯度检查点。

## 故障排查

### 生成期间出现 AssertionError

确保说话人 ID、上下文列表和文本列表的长度及嵌套结构符合模型接口，不要把单个值误传为错误形状的批量输入。

### 显存不足

减小批量大小、上下文长度或最大生成长度，启用量化，并关闭其他占用 GPU 的进程。

## 资源与许可

模型和相关项目链接见英文部分。使用前请核对上游模型、数据集和代码许可。
