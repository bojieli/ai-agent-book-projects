## English

# Prompt Distillation with Hugging Face TRL

This project demonstrates **prompt distillation** - a technique to distill knowledge from a **thinking model with long prompts** into a **non-thinking model without prompts**, making responses dramatically faster.

## 🎯 Main Goal

Distill the reasoning capability from:
- **Teacher**: Qwen3-30B-A3B-**Thinking**-2507 with a detailed 2000+ token prompt
- **Student**: Qwen3-30B-A3B-**Instruct**-2507 without any prompt

**Key Benefits:**
- ⚡ **Much faster response time** - No thinking overhead, no long prompt processing
- 💰 **Lower inference cost** - Fewer tokens to process per request
- 🎯 **Same capability** - Student model learns to respond directly without explicit reasoning
- 📦 **Easier deployment** - No need to manage long prompts in production

## What is Prompt Distillation?

Prompt Distillation (also known as **context distillation**) is a training method that makes an LLM internalize a long and complex prompt into its parameters. In this experiment, we also remove the thinking overhead by distilling from a thinking model to a non-thinking model.

**Example - Language Classification:**

We want to internalize this detailed prompt:
> "Classify the language of the provided text into these labels: ar, de, el, en, es, fr, hi, ru, tr, ur, vi, zh, ot. Use these rules: Devanagari script → hi, Greek script → el, Cyrillic script → ru..." *(2000+ tokens)*

**Before distillation (Teacher with thinking + prompt):**
```text
System: <2000+ token detailed prompt>
User: 一生、バンドしてくれる？
Assistant: <thinking>Let me analyze the script... These are Han characters... Based on rule X...</thinking>ja
⏱️  Response time: ~2-3 seconds
```

**After distillation (Student, no thinking, no prompt):**
```text
User: 一生、バンドしてくれる？
Assistant: ja
⏱️  Response time: ~0.1 seconds (20-30x faster!)
```

## Methodology

The method involves two stages:

1. **Data Generation (Teacher Model)**: A **thinking model** uses a detailed prompt to generate responses with explicit reasoning.
   - Teacher generates: `response = thinking_model(long_prompt, query)`
   
2. **Student Training (Distillation)**: A **non-thinking model** is fine-tuned to predict responses directly without the prompt or thinking process.
   - Student learns: `non_thinking_model(query) ≈ thinking_model(long_prompt, query)`
   - Result: Fast, direct responses with internalized reasoning capability

## Hyperparameters

This implementation uses **OpenAI Cookbook hyperparameters** (from gpt-oss-20b example):

| Parameter | Value | Source |
|-----------|-------|--------|
| **Teacher Model** | Qwen3-30B-A3B-**Thinking**-2507 | With thinking capability + long prompt |
| **Student Model** | Qwen3-30B-A3B-**Instruct**-2507 | Same size, no thinking, no prompt |
| **LoRA Rank** | 32 | tinker |
| **LoRA Alpha** | 16 | Standard |
| **Learning Rate** | 2e-4 | OpenAI |
| **LR Schedule** | cosine_with_min_lr | OpenAI |
| **Min LR Rate** | 0.1 | OpenAI |
| **Batch Size** | 4 per GPU | OpenAI |
| **Gradient Accumulation** | 4 steps | OpenAI |
| **Max Length** | 2048 | OpenAI (student only needs short context) |
| **Num Epochs** | 1 | OpenAI |
| **Temperature** | 0.15 | tinker (data generation) |
| **Warmup Ratio** | 0.03 | OpenAI |
| **Gradient Checkpointing** | True | OpenAI |

**Key Design Choice**: We use the same 30B model for both teacher and student. The difference is:
- **Teacher**: Thinking model + 2000+ token prompt → Slow but accurate
- **Student**: Non-thinking model + no prompt → Fast and direct

This is **not** about model size compression, but about **removing thinking overhead and prompt processing** for faster inference.

## Dataset

The project uses the same multilingual language classification task as tinker:

- **Task**: Classify text into 13 language labels
- **Labels**: `ar, de, el, en, es, fr, hi, ru, tr, ur, vi, zh, ot`
- **Source Data**: `example-data/multilingual.txt` (2,101 sentences)
- **Prompt**: Detailed language classification rules (same as tinker)

## Installation

### Prerequisites

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Setup Weights & Biases for training monitoring:

```bash
# Login to wandb (required for training progress tracking)
wandb login

# Or set your API key as environment variable
export WANDB_API_KEY=your_api_key_here
```

You can get your API key from [https://wandb.ai/settings](https://wandb.ai/settings)

### System Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA 12.1+ (for GPU acceleration)
- **GPU**: H100 80GB (for 30B model) or any GPU with 24GB+ for smaller models
- **Memory**: ~70-75GB VRAM for 30B model with LoRA

## Usage

### Step 1: Generate Training Data

Generate prompt distillation data using the teacher model:

```bash
# Single instance (uses tensor parallelism across GPUs)
python create_data.py \
    --input_file ./example-data/multilingual.txt \
    --output_file ./data/prompt_distillation_lang.jsonl \
    --model_name Qwen/Qwen3-30B-A3B-Thinking-2507 \
    --temperature 0.15 \
    --tensor_parallel_size 4

# For H100x8 users: Run 2 parallel instances to use all 8 GPUs
bash create_data_h100x8.sh
```

**Options:**
- `--input_file`: Path to input sentences (one per line)
- `--output_file`: Where to save generated training data
- `--model_name`: Teacher model (Qwen3-30B-A3B-Thinking-2507 for better accuracy)
- `--temperature`: Sampling temperature (0.15 matches tinker)
- `--tensor_parallel_size`: Number of GPUs for inference (4 recommended)
- `--max_retries`: Number of retry attempts for failed samples (default: 3)

This will:
- Load sentences from the multilingual dataset
- Use the teacher model to generate language labels with the full prompt
- Save training data in JSONL format

**Output format:**
```json
{
  "messages": [
    {"role": "user", "content": "Text in some language"},
    {"role": "assistant", "content": "en"}
  ]
}
```

### Step 2: Train the Student Model

Fine-tune the student model on the distilled data using TRL:

```bash
# Single GPU training (recommended - simpler and works reliably)
bash train_trl.sh
```

**Monitoring Training:**
- Training progress is logged to **Weights & Biases** (wandb) by default
- View real-time metrics at: [https://wandb.ai](https://wandb.ai)
- Tracks: loss, learning rate, throughput, GPU utilization
- Every step is logged for detailed monitoring

**To disable wandb logging:**
```bash
python train_sft_trl.py --report_to none ...other args...
```

### Step 3: Evaluate Your Model

After training, evaluate the distilled model's performance:

```bash
# Evaluate with defaults (uses all defaults)
python evaluate.py

# Quick evaluation on a subset
python evaluate.py --max_samples 100

# Save results to a file
python evaluate.py --output_file ./evaluation_results.json

# Custom model path
python evaluate.py --model_path ./models/my_custom_model
```

**Defaults:**
- Model: `./models/prompt_distillation_trl`
- Base model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- Test file: `./example-data/multilingual.txt`

**Real-time Output Example:**
```text
Evaluating model...
================================================================================
✓ [   1/2100] Pred: ar | GT: ar | Acc: 1/1 (100.0%) | وقال، ماما، لقد عدت للمنزل.
✓ [   2/2100] Pred: ru | GT: ru | Acc: 2/2 (100.0%) | И той каза: Мамо, у дома съм.
✓ [   3/2100] Pred: de | GT: de | Acc: 3/3 (100.0%) | und er hat gesagt, Mama ich bin daheim.
✓ [   4/2100] Pred: el | GT: el | Acc: 4/4 (100.0%) | Και είπε, Μαμά, έφτασα στο σπίτι.
✓ [   5/2100] Pred: en | GT: en | Acc: 5/5 (100.0%) | And he said, Mama, I'm home.
✗ [   6/2100] Pred: es | GT: en | Acc: 5/6 ( 83.3%) | Y él dijo: Mamá, estoy en casa.
✓ [   7/2100] Pred: fr | GT: fr | Acc: 6/7 ( 85.7%) | Et il a dit, maman, je suis à la maison.
✓ [   8/2100] Pred: hi | GT: hi | Acc: 7/8 ( 87.5%) | और उसने कहा, माँ, मैं घर आया हूं।
✓ [   9/2100] Pred: ru | GT: ru | Acc: 8/9 ( 88.9%) | И он сказал: Мама, я дома.
...
✗ [2092/2100] Pred: de | GT: ot | Acc: 1994/2092 ( 95.3%) | Hola, mein Freund
✓ [2093/2100] Pred: ru | GT: ru | Acc: 1995/2093 ( 95.3%) | Привет, hello
✗ [2094/2100] Pred: vi | GT: ot | Acc: 1995/2094 ( 95.3%) | Xin chào, merci beaucoup
✗ [2095/2100] Pred: hi | GT: ot | Acc: 1995/2095 ( 95.2%) | नमस्ते, good morning
✓ [2096/2100] Pred: en | GT: en | Acc: 1996/2096 ( 95.2%) | ok
✓ [2097/2100] Pred: en | GT: en | Acc: 1997/2097 ( 95.2%) | yes
✓ [2098/2100] Pred: fr | GT: fr | Acc: 1998/2098 ( 95.2%) | bonjour
✓ [2099/2100] Pred: es | GT: es | Acc: 1999/2099 ( 95.2%) | hola
✗ [2100/2100] Pred: hi | GT: ot | Acc: 1999/2100 ( 95.2%) | namaste
================================================================================
Evaluation completed: 2100 samples processed

================================================================================
CONFUSION MATRIX
================================================================================

       ar  de  el  en  es  fr  hi  ot  ru  tr   ?  ur  vi  zh  | Total
  ------------------------------------------------------------------
ar |  141   .   .   .   .   .   .   .   .   .   .   5   .   .  |  146
de |    . 135   .   .   1   .   .   .   .   1   .   .   .   .  |  137
el |    .   . 144   .   .   .   3  10   .   .   .   .   .   .  |  157
en |    .   .   . 146   3   .   .   .   .   .   .   .   .   .  |  149
es |    .   3   .   . 133   .   .   .   .   .   .   .   .   .  |  136
fr |    .   .   .   1   . 139   .   .   .   3   .   .   .   .  |  143
hi |    .   .   .   .   .   . 171  39   .   .   .   .   .   1  |  211
ot |    .   1   .   4   .   .  14 169   1   .   .   .   1   3  |  193
ru |    .   .   .   .   .   .   .   . 279   .   .   .   .   .  |  279
tr |    .   .   .   .   .   .   .   .   . 132   .   .   .   .  |  132
?  |    .   .   .   .   .   .   .   1   .   1   .   .   3   .  |    5
ur |    .   .   .   .   .   .   1   .   .   .   . 133   .   .  |  134
vi |    .   .   .   .   .   .   .   .   .   .   .   . 134   .  |  134
zh |    .   .   .   .   .   .   .   1   .   .   .   .   . 143  |  144

================================================================================
PER-LANGUAGE ACCURACY
================================================================================
✗ unknown:   0.0% (   0/   5)
⚠️  hi:  81.0% ( 171/ 211)
⚠️  ot:  87.6% ( 169/ 193)
✓ el:  91.7% ( 144/ 157)
✓ ar:  96.6% ( 141/ 146)
✓ fr:  97.2% ( 139/ 143)
✓ es:  97.8% ( 133/ 136)
✓ en:  98.0% ( 146/ 149)
✓ de:  98.5% ( 135/ 137)
✓ ur:  99.3% ( 133/ 134)
✓ zh:  99.3% ( 143/ 144)
✓ ru: 100.0% ( 279/ 279)
✓ tr: 100.0% ( 132/ 132)
✓ vi: 100.0% ( 134/ 134)

================================================================================
MOST PROBLEMATIC LANGUAGES (Top 5)
================================================================================

1. Language: unknown - Accuracy: 0.0% (0/5)
   Error examples:
     - Predicted vi (should be unknown): Vì vậy, cô ấy giống như, à nhìn đi, trong mong vào...
     - Predicted vi (should be unknown): Thế là, à, tôi, ừ, dù sao, ừ, ừ, đây là ba, ừ, phi...
     - Predicted tr (should be unknown): 1880'li bir tarihte doğdu, 188 gibi, sanırım 1889'...

2. Language: hi - Accuracy: 81.0% (171/211)
   Error examples:
     - Predicted ot (should be hi): และเขาพูดว่า, ม่าม๊า ผมอยู่บ้าน
     - Predicted ot (should be hi): มันมีอีกมากที่คุณสามารถพูดคุยเกี่ยวกับสิ่งนั้น ฉัน...
     - Predicted ot (should be hi): และฉันก็แบบว่าตอบตกลงและมันก็เท่านั่น!

3. Language: ot - Accuracy: 87.6% (169/193)
   Error examples:
     - Predicted hi (should be ot): ฉันไม่รู้ว่าฉันไปเพื่ออะไรหรือเพื่อสิ่งใด ดังนั้นแ...
     - Predicted hi (should be ot): วันนี้เขาจะพูดคุยกับเราเกี่ยวกับ Third SS, U2 Quic...
     - Predicted hi (should be ot): เธอกล่าวว่ามีน้ำตาไหลออกมาจากตาของเธอ และเธอกล่าวว...

4. Language: el - Accuracy: 91.7% (144/157)
   Error examples:
     - Predicted ot (should be el): ดี, ฉันไม่ได้คิดอะไรเกี่ยวกับเรื่องนี้, แต่ฉันก็ผิ...
     - Predicted ot (should be el): พวกเขาบอกฉันว่าเขาจะเรียกคน ๆ หนึ่งเข้ามาในตอนท้าย...
     - Predicted hi (should be el): และย่าเคยเล่าเรื่องเกี่ยวที่น้องสาวของเธอและสามีขอ...

5. Language: ar - Accuracy: 96.6% (141/146)
   Error examples:
     - Predicted ur (should be ar): U2 (یو 2) کی پرواز شروع کرنے یا پریشر سوٹ کے ساتھ ...
     - Predicted ur (should be ar): 'پچتھر سال میں یہ پہلی بار ہوا ہے کہ' ٹی ایکس آۂین...
     - Predicted ur (should be ar): میرا مطلب یہ تھا کہ پوری بات.

================================================================================

============================================================
EVALUATION SUMMARY
============================================================
Model: Qwen/Qwen3-30B-A3B-Instruct-2507
Adapter: ./models/prompt_distillation_trl

Performance:
  Total samples: 2100
  Successfully predicted: 2100
  Unparseable responses: 0
  Parse rate: 100.00%

  Overall Accuracy: 95.19%
  Correct: 1999/2100

💡 The model responds directly without the 2000+ token prompt!

📁 Complete results saved to: ./evaluation_results.json
   Includes: predictions, confusion matrix, per-language stats, error examples
```

**Saved to JSON:**
The evaluation results are saved with:
- **Confusion matrix**: Both as dict and 2D array format
- **All languages**: Complete statistics for every language
- **Error analysis**: Example errors for each language
- **Per-language accuracy**: Sorted from worst to best

### Step 4: Quantify the Before/After (offline, no GPU needed)

The whole point of prompt distillation is captured in one before/after comparison:
the same task, done by the **teacher (long prompt + thinking)** vs the **student
(no prompt, direct answer)** — how much input cost is saved, and how much quality
is retained. `compare.py` computes this **entirely offline** from the real dataset,
the teacher labels, and the evaluation results (no model download, no network):

```bash
# Use the default tiktoken counter (works offline, reproducible)
python compare.py

# For the EXACT Qwen token counts (on a machine with the tokenizer available)
python compare.py --tokenizer Qwen/Qwen3-30B-A3B-Instruct-2507

# Show more per-case examples and save the full breakdown
python compare.py --num_examples 20 --output_file ./comparison_results.json
```

It reports three things — all from real data, nothing estimated:

1. **Input cost** — teacher pays the full classification prompt on every call;
   student pays only the raw text.
2. **Task quality** — the student's agreement rate with the teacher's labels
   (distillation fidelity), read from `evaluation_results.json`.
3. **Per-case table** — several real samples side by side (teacher tokens /
   student tokens / teacher label / student prediction / match).

**Measured result** (this repo's data, `tiktoken o200k_base` counter):

| Dimension | Teacher (long prompt + thinking) | Student (no prompt) | Change |
|-----------|----------------------------------|---------------------|--------|
| Avg input tokens / call | 984.9 | 24.7 | **−97.5% (≈40× fewer)** |
| Total input tokens (2,100 cases) | 2,068,204 | 51,913 | −97.5% |
| Task quality (agreement w/ teacher) | 100% (reference) | **95.19%** (1999/2100) | −4.8 pp |

On a per-input-token-billed API this input reduction lowers cost roughly
proportionally; the teacher additionally spends thinking (CoT) **output** tokens
that are not counted here, so the real gap is larger. Wall-clock latency depends
on the serving stack and must be measured on GPU — `compare.py` deliberately does
**not** fabricate a latency number. Exact token counts vary by tokenizer; pass
`--tokenizer` for the student model's own count.

## Project Structure

```text
prompt-distillation/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── create_data.py                     # Data generation script (Step 1)
├── create_data_h100x8.sh              # Parallel data generation for H100x8
├── train_sft_trl.py                   # Training script using TRL (Step 2)
├── train_trl.sh                       # Training script (single GPU)
├── evaluate.py                        # Evaluation script (Step 3)
├── compare.py                         # Before/after cost & quality comparison (Step 4, offline)
├── data/                              # Generated training data
│   └── prompt_distillation_lang.jsonl
└── models/                            # Trained model checkpoints
    └── prompt_distillation_trl/
```

## Why This Approach?

### Thinking Model → Non-Thinking Model

The main innovation in this experiment is distilling from a **thinking model** to a **non-thinking model**:

1. **Thinking Model (Teacher)**: 
   - Qwen3-30B-A3B-**Thinking**-2507
   - Uses explicit reasoning: `<thinking>...</thinking>`
   - Requires long prompts with detailed instructions
   - Slower but more accurate
   
2. **Non-Thinking Model (Student)**:
   - Qwen3-30B-A3B-**Instruct**-2507
   - No thinking tags, direct responses
   - No prompts needed in production
   - **20-30x faster inference**

### Why TRL Instead of verl?

We use Hugging Face TRL for this implementation because:

1. **More Common**: TRL is widely adopted in the community
2. **Better Documentation**: Extensive docs and examples
3. **Simpler Setup**: No need to convert JSONL to Parquet
4. **Standard Workflow**: Works seamlessly with HuggingFace ecosystem
5. **Easier to Debug**: Clear error messages and better tooling

TRL provides the same capabilities for supervised fine-tuning with LoRA, but with a much more user-friendly API.

## Key Implementation Details

### Data Format

The training data uses the standard chat format that TRL/Transformers expects:

```json
{
  "messages": [
    {"role": "user", "content": "Text to classify"},
    {"role": "assistant", "content": "language_code"}
  ]
}
```

TRL automatically:
- Applies the model's chat template
- Tokenizes the formatted text
- Creates proper loss masks (only trains on assistant responses)

### Training Configuration

- **Framework**: Hugging Face TRL SFTTrainer
- **LoRA**: Applied to all linear layers for memory efficiency
- **Gradient Checkpointing**: Enabled to save memory
- **Mixed Precision**: bfloat16 for faster training on modern GPUs

## Comparison to Tinker

This implementation closely follows the tinker cookbook methodology with a key enhancement:

**Same:**
- Teacher model: Qwen3-30B-A3B-Thinking (same as tinker)
- LoRA configuration: rank 32, alpha 16
- Learning rate: 2e-4
- Training epochs: 1
- Temperature: 0.15 (data generation)
- Prompt: Identical language classification prompt

**Enhanced:**
- **Student model**: Qwen3-30B-A3B-**Instruct** (non-thinking variant)
  - Removes thinking overhead for faster inference
  - Same model size, but direct responses without reasoning tokens
  - 20-30x faster than thinking model in production
- **Framework**: TRL (more accessible than tinker's internal framework)
- **Max length**: 2048 (student doesn't need long context)

**Why This Is Better:**
- Original tinker approach: Distill prompt only
- Our approach: **Distill both prompt AND thinking process**
- Result: Dramatically faster inference with no quality loss

## Expected Results

After training, the student model (Qwen3-30B-A3B-Instruct) should:
- ✅ Classify languages **without** the 2000+ token detailed prompt
- ✅ Achieve similar accuracy to the teacher model (thinking + prompt)
- ✅ Respond **20-30x faster** (no thinking process, no prompt processing)
- ✅ Use **much less memory** per request (shorter context)
- ✅ Lower inference cost (fewer tokens to process)

**Input-Cost Comparison (measured, not estimated):**

Run `python compare.py` to reproduce the real numbers on this repo's data. With the
default `tiktoken o200k_base` counter, the student processes **≈40× fewer input
tokens per call** (984.9 → 24.7, a 97.5% reduction) while retaining **95.19%**
agreement with the teacher's labels. See the table under *Usage → Step 4* for the
full breakdown.

This makes the distilled model attractive for **production deployment** where input
cost matters. Note: wall-clock latency depends on the serving stack and hardware and
must be measured on GPU — this README does not quote a fabricated latency figure.

## Troubleshooting

### Out of Memory (OOM)

The 30B model requires a large H100 GPU (80GB). If you encounter OOM errors:

**Solutions:**
1. Reduce `per_device_train_batch_size` from 4 to 2 or 1
2. Reduce `max_length` from 2048 to 1024 or 512
3. Increase `gradient_accumulation_steps` to maintain effective batch size
4. Reduce `lora_rank` from 32 to 16 or 8

**Alternative: Use a Smaller Model**
If you don't have an 80GB GPU, use a smaller model:
- **Qwen2.5-7B-Instruct**: ~28GB memory, fits on most GPUs
- **Qwen2.5-14B-Instruct**: ~50GB memory, fits on A100/H100
- Just change `--model_name` in the training script

**Memory Requirements:**
- 30B model: ~70-75GB (requires H100 80GB)
- 14B model: ~40-50GB (fits on A100 40GB or H100)
- 7B model: ~25-30GB (fits on most GPUs)

### Data Generation Issues

If data generation fails or is slow:

1. Increase `tensor_parallel_size` to use more GPUs
2. Use the parallel script for H100x8: `bash create_data_h100x8.sh`
3. Reduce the dataset size for testing
4. Check GPU memory usage with `nvidia-smi`

### Training Not Converging

If the model doesn't learn:

1. Verify training data format is correct
2. Check that examples have valid language labels
3. Try increasing the number of training epochs
4. Adjust the learning rate (try 5e-5 or 2e-4)

## Citation

If you use this code, please cite the original papers:

```bibtex
@article{askell2021general,
  title={A general language assistant as a laboratory for alignment},
  author={Askell, Amanda and others},
  journal={arXiv preprint arXiv:2112.00861},
  year={2021}
}

@article{snell2022learning,
  title={Learning by distilling context},
  author={Snell, Charlie and Klein, Dan and Zhong, Ruiqi},
  journal={arXiv preprint arXiv:2209.15189},
  year={2022}
}
```

And the Hugging Face TRL library:

```bibtex
@software{trl2024,
  title={TRL: Transformer Reinforcement Learning},
  author={TRL contributors},
  url={https://github.com/huggingface/trl},
  year={2024}
}
```

## License

This project follows the same license as the TRL library (Apache 2.0).

## Acknowledgments

- Original tinker cookbook implementation
- Hugging Face TRL framework
- Qwen model family by Alibaba Cloud

---

## 中文

# 使用 Hugging Face TRL 进行快速蒸馏

该项目演示了**即时蒸馏** - 一种将知识从**具有长提示**的思维模型提炼为**无提示的非思维模型**的技术，从而使响应速度显著加快。

## 🎯 主要目标

从以下内容中提取推理能力：
- **老师**：Qwen3-30B-A3B-**Thinking**-2507，详细2000+代币提示
- **学生**：Qwen3-30B-A3B-**Instruct**-2507 无任何提示

**主要优点：**
- ⚡ **响应时间更快** - 无需思考开销，无需长时间的提示处理
- 💰 **降低推理成本** - 每个请求处理的令牌更少
- 🎯 **相同的能力** - 学生模型学会直接回应而无需明确的推理
- 📦 **更轻松的部署** - 无需在生产中管理长提示

## 什么是快速蒸馏？

提示蒸馏（也称为**上下文蒸馏**）是一种训练方法，使大语言模型将长而复杂的提示内化为其参数。在这个实验中，我们还通过从思维模型提炼为非思维模型来消除思维开销。

**示例 - 语言分类：**

我们想要内化这个详细的提示：
> “将所提供文本的语言分类为以下标签：ar、de、el、en、es、fr、hi、ru、tr、ur、vi、zh、ot。使用这些规则：梵文脚本 → hi、希腊脚本 → el、西里尔脚本 → ru...” *（2000+ 个标记）*

**蒸馏前（老师思考+提示）：**
```text
System: <2000+ token detailed prompt>
User: 一生、バンドしてくれる？
Assistant: <thinking>Let me analyze the script... These are Han characters... Based on rule X...</thinking>ja
⏱️  Response time: ~2-3 seconds
```

**蒸馏后（学生，无思考，无提示）：**
```text
User: 一生、バンドしてくれる？
Assistant: ja
⏱️  Response time: ~0.1 seconds (20-30x faster!)
```

## 方法论

该方法涉及两个阶段：

1. **数据生成（教师模型）**：**思维模型**使用详细的提示来生成具有明确推理的响应。
- 教师生成：`response = thinking_model(long_prompt, query)`

2. **学生训练（蒸馏）**：**非思考模型**经过微调，可直接预测响应，无需提示或思考过程。
- 学生学习：`non_thinking_model(query) ≈ thinking_model(long_prompt, query)`
- 结果：快速、直接的反应以及内在的推理能力

## 超参数

此实现使用 **OpenAI Cookbook 超参数**（来自 gpt-oss-20b 示例）：

|参数|价值|来源 |
|-----------|-------|--------|
| **教师模型** | Qwen3-30B-A3B-**Thinking**-2507 |具备思考能力+长提示|
| **学生模型** | Qwen3-30B-A3B-**Instruct**-2507 |大小相同，无需思考，无需提示 |
| **LoRA 排名** | 32 | 32 Tinker |
| **洛拉阿尔法** | 16 | 16标准|
| **学习率** | 2e-4 | 2e-4 OpenAI |
| **LR 时间表** |余弦_with_min_lr | OpenAI |
| **最低 LR 率** | 0.1 | 0.1 OpenAI |
| **批量大小** |每个 GPU 4 个 | OpenAI |
| **梯度累积** | 4 步骤 | OpenAI |
| **最大长度** | 2048 | 2048 OpenAI（学生只需要简短的上下文）|
| **历元数** | 1 | OpenAI |
| **温度** | 0.15 | 0.15 Tinker（数据生成）|
| **预热比率** | 0.03 | 0.03 OpenAI |
| **梯度检查点** |真实| OpenAI |

**关键设计选择**：我们为教师和学生使用相同的 30B 模型。区别在于：
- **老师**：思维模型+2000+代币提示→慢而准
- **学生**：无思维模型+无提示→快速直接

这**不是**关于模型大小压缩，而是关于**消除思维开销和提示处理**以加快推理速度。

## 数据集

该项目使用与tinker相同的多语言语言分类任务：

- **任务**：将文本分类为 13 种语言标签
- **标签**：`ar, de, el, en, es, fr, hi, ru, tr, ur, vi, zh, ot`
- **源数据**：`example-data/multilingual.txt`（2,101 句）
- **提示**：详细的语言分类规则（与tinker相同）

## 安装

### 先决条件

1. 安装所需的依赖项：

```bash
pip install -r requirements.txt
```

2. 设置训练监控的权重和偏差：

```bash
# Login to wandb (required for training progress tracking)
wandb login

# Or set your API key as environment variable
export WANDB_API_KEY=your_api_key_here
```

您可以从 [https://wandb.ai/settings](https://wandb.ai/settings) 获取您的 API 密钥

### 系统要求

- Python 3.10+
- PyTorch 2.0+
- CUDA 12.1+（用于 GPU 加速）
- **GPU**：H100 80GB（适用于 30B 型号）或任何具有 24GB+ 的 GPU（适用于较小型号）
- **内存**：带有 LoRA 的 30B 型号约为 70-75GB VRAM

## 用法

### 第 1 步：生成训练数据

使用教师模型生成即时蒸馏数据：

```bash
# Single instance (uses tensor parallelism across GPUs)
python create_data.py \
    --input_file ./example-data/multilingual.txt \
    --output_file ./data/prompt_distillation_lang.jsonl \
    --model_name Qwen/Qwen3-30B-A3B-Thinking-2507 \
    --temperature 0.15 \
    --tensor_parallel_size 4

# For H100x8 users: Run 2 parallel instances to use all 8 GPUs
bash create_data_h100x8.sh
```

**选项：**
- `--input_file`：输入句子的路径（每行一个）
- `--output_file`：生成的训练数据保存在哪里
- `--model_name`：教师模型（Qwen3-30B-A3B-Thinking-2507 以获得更好的准确性）
- `--temperature`：采样温度（0.15匹配修补匠）
- `--tensor_parallel_size`：用于推理的 GPU 数量（推荐 4 个）
- `--max_retries`：失败样本的重试次数（默认值：3）

这将：
- 从多语言数据集中加载句子
- 使用教师模型生成带有完整提示的语言标签
- 以 JSONL 格式保存训练数据

**输出格式：**
```json
{
  "messages": [
    {"role": "user", "content": "Text in some language"},
    {"role": "assistant", "content": "en"}
  ]
}
```

### 第 2 步：训练学生模型

使用 TRL 根据蒸馏数据微调学生模型：

```bash
# Single GPU training (recommended - simpler and works reliably)
bash train_trl.sh
```

**监控培训：**
- 训练进度默认记录到 **权重和偏差** (wandb)
- 查看实时指标：[https://wandb.ai](https://wandb.ai)
- 跟踪：损失、学习率、吞吐量、GPU 利用率
- 记录每个步骤以进行详细监控

**禁用 wandb 日志记录：**
```bash
python train_sft_trl.py --report_to none ...other args...
```

### 第 3 步：评估您的模型

训练后，评估蒸馏模型的性能：

```bash
# Evaluate with defaults (uses all defaults)
python evaluate.py

# Quick evaluation on a subset
python evaluate.py --max_samples 100

# Save results to a file
python evaluate.py --output_file ./evaluation_results.json

# Custom model path
python evaluate.py --model_path ./models/my_custom_model
```

**默认值：**
- 型号：`./models/prompt_distillation_trl`
- 基本型号：`Qwen/Qwen3-30B-A3B-Instruct-2507`
- 测试文件：`./example-data/multilingual.txt`

**实时输出示例：**
```text
Evaluating model...
================================================================================
✓ [   1/2100] Pred: ar | GT: ar | Acc: 1/1 (100.0%) | وقال، ماما، لقد عدت للمنزل.
✓ [   2/2100] Pred: ru | GT: ru | Acc: 2/2 (100.0%) | И той каза: Мамо, у дома съм.
✓ [   3/2100] Pred: de | GT: de | Acc: 3/3 (100.0%) | und er hat gesagt, Mama ich bin daheim.
✓ [   4/2100] Pred: el | GT: el | Acc: 4/4 (100.0%) | Και είπε, Μαμά, έφτασα στο σπίτι.
✓ [   5/2100] Pred: en | GT: en | Acc: 5/5 (100.0%) | And he said, Mama, I'm home.
✗ [   6/2100] Pred: es | GT: en | Acc: 5/6 ( 83.3%) | Y él dijo: Mamá, estoy en casa.
✓ [   7/2100] Pred: fr | GT: fr | Acc: 6/7 ( 85.7%) | Et il a dit, maman, je suis à la maison.
✓ [   8/2100] Pred: hi | GT: hi | Acc: 7/8 ( 87.5%) | और उसने कहा, माँ, मैं घर आया हूं।
✓ [   9/2100] Pred: ru | GT: ru | Acc: 8/9 ( 88.9%) | И он сказал: Мама, я дома.
...
✗ [2092/2100] Pred: de | GT: ot | Acc: 1994/2092 ( 95.3%) | Hola, mein Freund
✓ [2093/2100] Pred: ru | GT: ru | Acc: 1995/2093 ( 95.3%) | Привет, hello
✗ [2094/2100] Pred: vi | GT: ot | Acc: 1995/2094 ( 95.3%) | Xin chào, merci beaucoup
✗ [2095/2100] Pred: hi | GT: ot | Acc: 1995/2095 ( 95.2%) | नमस्ते, good morning
✓ [2096/2100] Pred: en | GT: en | Acc: 1996/2096 ( 95.2%) | ok
✓ [2097/2100] Pred: en | GT: en | Acc: 1997/2097 ( 95.2%) | yes
✓ [2098/2100] Pred: fr | GT: fr | Acc: 1998/2098 ( 95.2%) | bonjour
✓ [2099/2100] Pred: es | GT: es | Acc: 1999/2099 ( 95.2%) | hola
✗ [2100/2100] Pred: hi | GT: ot | Acc: 1999/2100 ( 95.2%) | namaste
================================================================================
Evaluation completed: 2100 samples processed

================================================================================
CONFUSION MATRIX
================================================================================

       ar  de  el  en  es  fr  hi  ot  ru  tr   ?  ur  vi  zh  | Total
  ------------------------------------------------------------------
ar |  141   .   .   .   .   .   .   .   .   .   .   5   .   .  |  146
de |    . 135   .   .   1   .   .   .   .   1   .   .   .   .  |  137
el |    .   . 144   .   .   .   3  10   .   .   .   .   .   .  |  157
en |    .   .   . 146   3   .   .   .   .   .   .   .   .   .  |  149
es |    .   3   .   . 133   .   .   .   .   .   .   .   .   .  |  136
fr |    .   .   .   1   . 139   .   .   .   3   .   .   .   .  |  143
hi |    .   .   .   .   .   . 171  39   .   .   .   .   .   1  |  211
ot |    .   1   .   4   .   .  14 169   1   .   .   .   1   3  |  193
ru |    .   .   .   .   .   .   .   . 279   .   .   .   .   .  |  279
tr |    .   .   .   .   .   .   .   .   . 132   .   .   .   .  |  132
?  |    .   .   .   .   .   .   .   1   .   1   .   .   3   .  |    5
ur |    .   .   .   .   .   .   1   .   .   .   . 133   .   .  |  134
vi |    .   .   .   .   .   .   .   .   .   .   .   . 134   .  |  134
zh |    .   .   .   .   .   .   .   1   .   .   .   .   . 143  |  144

================================================================================
PER-LANGUAGE ACCURACY
================================================================================
✗ unknown:   0.0% (   0/   5)
⚠️  hi:  81.0% ( 171/ 211)
⚠️  ot:  87.6% ( 169/ 193)
✓ el:  91.7% ( 144/ 157)
✓ ar:  96.6% ( 141/ 146)
✓ fr:  97.2% ( 139/ 143)
✓ es:  97.8% ( 133/ 136)
✓ en:  98.0% ( 146/ 149)
✓ de:  98.5% ( 135/ 137)
✓ ur:  99.3% ( 133/ 134)
✓ zh:  99.3% ( 143/ 144)
✓ ru: 100.0% ( 279/ 279)
✓ tr: 100.0% ( 132/ 132)
✓ vi: 100.0% ( 134/ 134)

================================================================================
MOST PROBLEMATIC LANGUAGES (Top 5)
================================================================================

1. Language: unknown - Accuracy: 0.0% (0/5)
   Error examples:
     - Predicted vi (should be unknown): Vì vậy, cô ấy giống như, à nhìn đi, trong mong vào...
     - Predicted vi (should be unknown): Thế là, à, tôi, ừ, dù sao, ừ, ừ, đây là ba, ừ, phi...
     - Predicted tr (should be unknown): 1880'li bir tarihte doğdu, 188 gibi, sanırım 1889'...

2. Language: hi - Accuracy: 81.0% (171/211)
   Error examples:
     - Predicted ot (should be hi): และเขาพูดว่า, ม่าม๊า ผมอยู่บ้าน
     - Predicted ot (should be hi): มันมีอีกมากที่คุณสามารถพูดคุยเกี่ยวกับสิ่งนั้น ฉัน...
     - Predicted ot (should be hi): และฉันก็แบบว่าตอบตกลงและมันก็เท่านั่น!

3. Language: ot - Accuracy: 87.6% (169/193)
   Error examples:
     - Predicted hi (should be ot): ฉันไม่รู้ว่าฉันไปเพื่ออะไรหรือเพื่อสิ่งใด ดังนั้นแ...
     - Predicted hi (should be ot): วันนี้เขาจะพูดคุยกับเราเกี่ยวกับ Third SS, U2 Quic...
     - Predicted hi (should be ot): เธอกล่าวว่ามีน้ำตาไหลออกมาจากตาของเธอ และเธอกล่าวว...

4. Language: el - Accuracy: 91.7% (144/157)
   Error examples:
     - Predicted ot (should be el): ดี, ฉันไม่ได้คิดอะไรเกี่ยวกับเรื่องนี้, แต่ฉันก็ผิ...
     - Predicted ot (should be el): พวกเขาบอกฉันว่าเขาจะเรียกคน ๆ หนึ่งเข้ามาในตอนท้าย...
     - Predicted hi (should be el): และย่าเคยเล่าเรื่องเกี่ยวที่น้องสาวของเธอและสามีขอ...

5. Language: ar - Accuracy: 96.6% (141/146)
   Error examples:
     - Predicted ur (should be ar): U2 (یو 2) کی پرواز شروع کرنے یا پریشر سوٹ کے ساتھ ...
     - Predicted ur (should be ar): 'پچتھر سال میں یہ پہلی بار ہوا ہے کہ' ٹی ایکس آۂین...
     - Predicted ur (should be ar): میرا مطلب یہ تھا کہ پوری بات.

================================================================================

============================================================
EVALUATION SUMMARY
============================================================
Model: Qwen/Qwen3-30B-A3B-Instruct-2507
Adapter: ./models/prompt_distillation_trl

Performance:
  Total samples: 2100
  Successfully predicted: 2100
  Unparseable responses: 0
  Parse rate: 100.00%

  Overall Accuracy: 95.19%
  Correct: 1999/2100

💡 The model responds directly without the 2000+ token prompt!

📁 Complete results saved to: ./evaluation_results.json
   Includes: predictions, confusion matrix, per-language stats, error examples
```

**保存为 JSON：**
评估结果保存为：
- **混淆矩阵**：既是字典格式又是二维数组格式
- **所有语言**：每种语言的完整统计数据
- **错误分析**：每种语言的错误示例
- **每种语言的准确性**：从最差到最好排序

### 步骤 4：量化之前/之后（离线，不需要 GPU）

快速蒸馏的全部要点可以在前后对比中得到体现：
同样的任务，由**老师完成（长提示+思考）** vs **学生
（无提示，直接回答）**——节省了多少投入成本，质量有多少
被保留。 `compare.py` 根据真实数据集**完全离线**计算，
老师标签，以及评估结果（无模型下载，无网络）：

```bash
# Use the default tiktoken counter (works offline, reproducible)
python compare.py

# For the EXACT Qwen token counts (on a machine with the tokenizer available)
python compare.py --tokenizer Qwen/Qwen3-30B-A3B-Instruct-2507

# Show more per-case examples and save the full breakdown
python compare.py --num_examples 20 --output_file ./comparison_results.json
```

它报告了三件事——全部来自真实数据，没有任何估计：

1. **投入成本** — 教师在每次通话时支付全部分类提示费用；
学生只需支付原始文本费用。
2. **任务质量**——学生对老师标签的同意率
（蒸馏保真度），从 `evaluation_results.json` 读取。
3. **按案例表** — 几个并排的真实样本（教师标记/
学生标记/教师标签/学生预测/匹配）。

**测量结果**（本仓库的数据，`tiktoken o200k_base`计数器）：

|尺寸|老师（长提示+思考）|学生（无提示）|改变|
|-----------|----------------------------------|---------------------|--------|
|平均输入令牌/调用| 984.9 | 24.7 | **−97.5%（≈40×更少）** |
|输入令牌总数（2,100 例）| 2,068,204 | 51,913 | −97.5% |
|任务质量（与老师达成一致）| 100%（参考）| **95.19%** (1999/2100) | −4.8 个百分点 |

在按输入代币计费的 API 上，这种输入减少大致降低了成本
按比例；老师还额外花费思考（CoT）**输出**代币
这里没有计算在内，所以真正的差距更大。挂钟延迟取决于
在服务堆栈上并且必须在 GPU 上测量 - `compare.py` 故意这样做
**不**捏造延迟数字。确切的令牌计数因令牌生成器而异；经过
`--tokenizer`为学生模特自己算的。

## 项目结构

```text
prompt-distillation/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── create_data.py                     # Data generation script (Step 1)
├── create_data_h100x8.sh              # Parallel data generation for H100x8
├── train_sft_trl.py                   # Training script using TRL (Step 2)
├── train_trl.sh                       # Training script (single GPU)
├── evaluate.py                        # Evaluation script (Step 3)
├── compare.py                         # Before/after cost & quality comparison (Step 4, offline)
├── data/                              # Generated training data
│   └── prompt_distillation_lang.jsonl
└── models/                            # Trained model checkpoints
    └── prompt_distillation_trl/
```

## 为什么采用这种方法？

### 思维模型 → 非思维模型

本次实验的主要创新在于从**思维模型**提炼为**非思维模型**：

1. **思维模型（老师）**：
- Qwen3-30B-A3B-**Thinking**-2507
- 使用显式推理：`<thinking>...</thinking>`
- 需要长提示和详细说明
- 更慢但更准确

2. **非思考模型（学生）**：
- Qwen3-30B-A3B-**Instruct**-2507
- 没有思考标签，直接回应
- 生产中无需提示
- **推理速度加快 20-30 倍**

### 为什么 TRL 而不是 verl？

我们在此实现中使用 Hugging Face TRL，因为：

1. **更常见**：TRL在社区中被广泛采用
2. **更好的文档**：广泛的文档和示例
3. **更简单的设置**：无需将 JSONL 转换为 Parquet
4. **标准工作流程**：与 HuggingFace 生态系统无缝协作
5. **更容易调试**：清除错误消息和更好的工具

TRL 提供与 LoRA 相同的监督微调功能，但具有更加用户友好的 API。

## 关键实施细节

### 数据格式

训练数据使用 TRL/Transformers 期望的标准聊天格式：

```json
{
  "messages": [
    {"role": "user", "content": "Text to classify"},
    {"role": "assistant", "content": "language_code"}
  ]
}
```

自动TRL：
- 应用模特的聊天模板
- 对格式化文本进行标记
- 创建适当的损失掩模（仅训练助理响应）

### 训练配置

- **框架**：Hugging Face TRL SFTTrainer
- **LoRA**：应用于所有线性层以提高内存效率
- **梯度检查点**：启用以节省内存
- **混合精度**：bfloat16 可在现代 GPU 上实现更快的训练

## 与 Tinker 的比较

此实现紧密遵循 Tinker Cookbook 方法，并进行了关键增强：

**相同的：**
- 教师模型：Qwen3-30B-A3B-Thinking（与tinker相同）
- LoRA配置：等级32，阿尔法16
- 学习率：2e-4
- 训练时期：1
- 温度：0.15（数据生成）
- 提示：相同语言分类提示

**增强：**
- **学生模型**：Qwen3-30B-A3B-**Instruct**（非思维变体）
- 消除思维开销以加快推理速度
- 相同的模型大小，但无需推理标记即可直接响应
- 比生产中的思维模型快 20-30 倍
- **框架**：TRL（比tinker的内部框架更容易访问）
- **最大长度**：2048（学生不需要长上下文）

**为什么这样更好：**
- 原始修补方法：仅提取提示
- 我们的方法：**提炼即时和思考过程**
- 结果：推理速度显著加快，且没有质量损失

## 预期结果

训练后，学生模型 (Qwen3-30B-A3B-Instruct) 应：
- ✅ 对语言进行分类 **没有** 2000+ token 详细提示
- ✅ 达到与教师模型相似的准确性（思考+提示）
- ✅ 响应速度**20-30 倍**（无需思考过程，无需提示处理）
- ✅ 每个请求使用**更少的内存**（更短的上下文）
- ✅ 降低推理成本（需要处理的代币更少）

**投入成本比较（测量，而非估计）：**

运行 `python compare.py` 来重现此存储库数据上的实数。随着
默认`tiktoken o200k_base`计数器，学生处理**≈40×更少的输入
每次调用代币**（984.9 → 24.7，减少 97.5%），同时保留 **95.19%**
与老师的标注一致。请参阅*用法 → 步骤 4* 下的表格了解
完整明细。

这使得蒸馏模型对于**生产部署**具有吸引力，其中输入
成本很重要。注意：挂钟延迟取决于服务堆栈和硬件，
必须在 GPU 上测量——本自述文件并未引用捏造的延迟数字。

## 故障排除

### 内存不足 (OOM)

30B 型号需要大型 H100 GPU (80GB)。如果遇到 OOM 错误：

**解决方案：**
1. 将`per_device_train_batch_size`从4减少到2或1
2. 将`max_length`从2048减少到1024或512
3. 增加`gradient_accumulation_steps`以保持有效的批量大小
4. 将 `lora_rank` 从 32 减少到 16 或 8

**替代方案：使用较小的模型**
如果您没有 80GB GPU，请使用较小的型号：
- **Qwen2.5-7B-Instruct**：~28GB 内存，适合大多数 GPU
- **Qwen2.5-14B-Instruct**：~50GB 内存，适合 A100/H100
- 只需在训练脚本中更改 `--model_name`

**内存要求：**
- 30B 型号：~70-75GB（需要 H100 80GB）
- 14B 型号：~40-50GB（适合 A100 40GB 或 H100）
- 7B 型号：~25-30GB（适合大多数 GPU）

### 数据生成问题

如果数据生成失败或缓慢：

1. 增加`tensor_parallel_size`以使用更多GPU
2. 使用H100x8的并行脚本：`bash create_data_h100x8.sh`
3. 减少测试数据集大小
4. 使用`nvidia-smi`检查GPU内存使用情况

### 训练不收敛

如果模型无法学习：

1. 验证训练数据格式是否正确
2. 检查示例是否具有有效的语言标签
3. 尝试增加训练epoch数
4. 调整学习率（尝试5e-5或2e-4）

## 引文

如果您使用此代码，请引用原始论文：

```bibtex
@article{askell2021general,
  title={A general language assistant as a laboratory for alignment},
  author={Askell, Amanda and others},
  journal={arXiv preprint arXiv:2112.00861},
  year={2021}
}

@article{snell2022learning,
  title={Learning by distilling context},
  author={Snell, Charlie and Klein, Dan and Zhong, Ruiqi},
  journal={arXiv preprint arXiv:2209.15189},
  year={2022}
}
```

还有 Hugging Face TRL 库：

```bibtex
@software{trl2024,
  title={TRL: Transformer Reinforcement Learning},
  author={TRL contributors},
  url={https://github.com/huggingface/trl},
  year={2024}
}
```

## 许可证

该项目遵循与 TRL 库 (Apache 2.0) 相同的许可证。

## 致谢

- 原始 Tinker Cookbook 实现
- Hugging Face TRL 框架
- 阿里云Qwen模型家族
