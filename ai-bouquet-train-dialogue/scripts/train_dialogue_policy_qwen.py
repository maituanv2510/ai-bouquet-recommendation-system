import torch
from pathlib import Path

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig


MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

TRAIN_PATH = "data/processed/dialogue_policy_train_v2.jsonl"
VAL_PATH = "data/processed/dialogue_policy_val_v2.jsonl"

OUTPUT_DIR = "outputs/qwen2.5-3b-dialogue-policy"


def format_chat_example(example):
    messages = example["messages"]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )

    return {
        "text": text
    }


def main():
    global tokenizer

    if not Path(TRAIN_PATH).exists():
        raise FileNotFoundError(f"Train file not found: {TRAIN_PATH}")

    if not Path(VAL_PATH).exists():
        raise FileNotFoundError(f"Validation file not found: {VAL_PATH}")

    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    print("Loading dataset...")

    dataset = load_dataset(
        "json",
        data_files={
            "train": TRAIN_PATH,
            "validation": VAL_PATH
        }
    )

    dataset = dataset.map(format_chat_example)

    print(dataset)
    print("Sample text:")
    print(dataset["train"][0]["text"][:1000])

    print("Loading model...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )

    model.config.use_cache = False

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
            "down_proj"
        ]
    )

    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,

        # Train config
        num_train_epochs=3,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,

        # Logging / eval / save
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=100,
        save_steps=100,
        save_total_limit=2,

        # Scheduler
        warmup_steps=20,
        lr_scheduler_type="cosine",

        # Precision
        # Tắt fp16 AMP để tránh lỗi:
        # "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'
        fp16=False,
        bf16=False,

        # Optimizer
        optim="paged_adamw_8bit",

        # Tắt gradient clipping để tránh GradScaler unscale lỗi trên Windows/GPU một số máy
        max_grad_norm=0.0,

        # Dataset config for new TRL API
        dataset_text_field="text",
        max_length=2048,
        packing=False,

        # Others
        report_to="none",
        remove_unused_columns=False
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=lora_config,
        processing_class=tokenizer
    )

    print("Start training...")

    trainer.train()

    print("Saving model...")

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"Done. Model saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()