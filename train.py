from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments
from datasets import load_dataset

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
dataset = load_dataset("json", data_files="training_data/hemingway_training_data.jsonl")

model = AutoModelForCausalLM.from_pretrained(model_name, load_in_8bit=True, device_map="auto")
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)


training_args = TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    warmup_steps=50,
    max_steps=500,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=50,
    output_dir="./hemingwrite"
)

trainer = Trainer(
    model=model,
    train_dataset=dataset["train"],
    args=training_args,
    tokenizer=tokenizer,
)
trainer.train()