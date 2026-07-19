import os
import sys
from pathlib import Path
from datetime import datetime

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig


# =========================================================
# PATH CONFIG
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

BASE_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

TRAIN_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_train_final.jsonl"
VAL_PATH = ROOT_DIR / "data" / "processed" / "dialogue_policy_val_final.jsonl"

OUTPUT_DIR = ROOT_DIR / "outputs" / "qwen2.5-3b-dialogue-policy-final"
LOG_DIR = ROOT_DIR / "logs"


# =========================================================
# LOGGING
# =========================================================

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for file in self.files:
            file.write(obj)
            file.flush()

    def flush(self):
        for file in self.files:
            file.flush()


def setup_train_log():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"train_dialogue_policy_final_{timestamp}.log"

    log_file = open(log_path, "w", encoding="utf-8")

    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)

    os.environ["TRAIN_LOG_FILE"] = str(log_path)

    print("=" * 80)
    print("Training log started")
    print(f"Log file: {log_path}")
    print("=" * 80)


# =========================================================
# CHECK FILES
# =========================================================

def check_paths():
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy train file: {TRAIN_PATH}")

    if not VAL_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy validation file: {VAL_PATH}")

    print("[INFO] Dataset paths checked.")
    print(f"[INFO] Train path: {TRAIN_PATH}")
    print(f"[INFO] Val path  : {VAL_PATH}")


# =========================================================
# LOAD DATASET
# =========================================================

def load_dialogue_dataset():
    print("[INFO] Loading dataset...")

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_PATH),
            "validation": str(VAL_PATH),
        },
    )

    print("[INFO] Dataset loaded.")
    print(dataset)

    print(f"[INFO] Train size: {len(dataset['train'])}")
    print(f"[INFO] Val size  : {len(dataset['validation'])}")

    sample = dataset["train"][0]
    print("[INFO] Sample keys:", sample.keys())

    if "text" not in sample:
        raise ValueError(
            "Dataset không có field 'text'. "
            "Hãy kiểm tra lại file dialogue_policy_train_final.jsonl."
        )

    return dataset


# =========================================================
# LOAD TOKENIZER
# =========================================================

def load_tokenizer():
    print("[INFO] Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_NAME,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    print("[INFO] Tokenizer loaded.")
    print(f"[INFO] pad_token: {tokenizer.pad_token}")
    print(f"[INFO] eos_token: {tokenizer.eos_token}")

    return tokenizer


# =========================================================
# LOAD MODEL 4-BIT
# =========================================================

def load_model():
    print("[INFO] Loading base model with 4-bit quantization...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )

    model.config.use_cache = False

    print("[INFO] Model loaded.")

    return model


# =========================================================
# LORA CONFIG
# =========================================================

def build_lora_config():
    print("[INFO] Building LoRA config...")

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    return lora_config


# =========================================================
# TRAINING CONFIG
# =========================================================

def build_training_config():
    print("[INFO] Building SFT training config...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),

        # Dataset
        dataset_text_field="text",
        max_length=1024,
        packing=False,

        # Train
        num_train_epochs=3,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,

        # Precision
        fp16=False,
        bf16=False,

        # Important for Windows / some GPU configs
        max_grad_norm=0.0,

        # Logging / eval / save
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,

        # Optimizer
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,

        # Others
        report_to="none",
        remove_unused_columns=True,
        gradient_checkpointing=True,
    )

    return training_args


# =========================================================
# MAIN TRAIN
# =========================================================

def main():
    setup_train_log()

    print("[INFO] Starting Qwen Dialogue Policy FINAL training...")
    print(f"[INFO] Base model : {BASE_MODEL_NAME}")
    print(f"[INFO] Output dir : {OUTPUT_DIR}")

    check_paths()

    dataset = load_dialogue_dataset()
    tokenizer = load_tokenizer()
    model = load_model()
    lora_config = build_lora_config()
    training_args = build_training_config()

    print("[INFO] Initializing SFTTrainer...")

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=lora_config,
        processing_class=tokenizer,
    )

    print("[INFO] Training started...")

    trainer.train()

    print("[INFO] Training finished.")

    print("[INFO] Saving final adapter...")

    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print("[INFO] Final model saved.")
    print(f"[INFO] Adapter output: {OUTPUT_DIR}")

    print("[INFO] Checking saved files...")

    adapter_config = OUTPUT_DIR / "adapter_config.json"
    adapter_model = OUTPUT_DIR / "adapter_model.safetensors"

    print(f"adapter_config.json exists: {adapter_config.exists()}")
    print(f"adapter_model.safetensors exists: {adapter_model.exists()}")

    print("=" * 80)
    print("DONE TRAINING QWEN DIALOGUE POLICY FINAL")
    print("=" * 80)


if __name__ == "__main__":
    main()