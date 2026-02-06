# -*- coding: utf-8 -*-
"""
SCRIPT DE TREINAMENTO LOCAL COM UNSLOTH
Este script treina um adaptador LoRA no seu PC usando a biblioteca Unsloth,
que é super rápida e otimizada para GPUs de consumidor.

O resultado será um "patch" de personalização para um modelo de linguagem grande.
"""

# 1. Importações e checagem de ambiente
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import os

# Verifica se tem GPU NVIDIA
if not torch.cuda.is_available():
    raise SystemError("GPU NVIDIA não detectada. Unsloth requer CUDA.")

print("✅ GPU NVIDIA detectada. Iniciando o processo de treinamento com Unsloth.")

# 2. Carregar o modelo base
# Usamos um modelo da biblioteca Unsloth já otimizado.
# Llama-3 8B é um excelente ponto de partida.
max_seq_length = 2048  # Comprimento máximo da sequência
dtype = None  # None para detecção automática
load_in_4bit = True  # Ativa a quantização de 4 bits (QLoRA) para economizar memória

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)
print("✅ Modelo base (Llama-3 8B) carregado.")

# 3. Configurar o modelo para treinamento LoRA
# Adicionamos "adaptadores" LoRA ao modelo. Apenas esses adaptadores serão treinados.
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # Rank (tamanho) dos adaptadores. 16 é um bom valor.
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
    random_state=3407,
)
print("✅ Adaptadores LoRA adicionados ao modelo.")

# 4. Preparação do Dataset
# Carregamos o arquivo JSONL que você gerou anteriormente.
dataset_path = "processed/dados_training.jsonl"
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"Arquivo de dataset não encontrado em: {dataset_path}. "
                            "Certifique-se de que o script converter.py foi executado com sucesso.")

dataset = load_dataset("json", data_files={"train": dataset_path})['train']

# O Unsloth precisa que o dataset tenha uma coluna "text".
# Vamos criar uma função para formatar nossas conversas nesse padrão.
alpaca_prompt = """Abaixo está uma instrução que descreve uma tarefa. Escreva uma resposta que complete adequadamente o pedido.

### Instrução:
{}

### Resposta:
{} """

def formatting_func(examples):
    users = examples["user"]
    assistants = examples["assistant"]
    texts = []
    for user, assistant in zip(users, assistants):
        text = alpaca_prompt.format(user, assistant)
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(formatting_func, batched=True)
print("✅ Dataset formatado e pronto para o treinamento.")

# 5. Configurar e Iniciar o Treinamento
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=100,  # Aumente para 100-200 para um treino melhor. 60 é para teste rápido.
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        output_dir="outputs",
        optim="paged_adamw_8bit",
        seed=3407,
    ),
)

print("\n🚀 INICIANDO TREINAMENTO... (Isso pode levar de 5 a 20 minutos)")
trainer.train()
print("🎉 Treinamento concluído!")

# 6. Salvar o Adaptador LoRA
output_dir = "models/aeon_lora_adapter"
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)
print(f"\n✅ Adaptador LoRA salvo em: {output_dir}")
print("Este é o 'patch' de personalização do seu Aeon.")

# Informações finais
print("\n---")
print("PRÓXIMO PASSO: Fazer o upload deste adaptador para a Groq.")
print("Os arquivos que você precisa estão na pasta 'models/aeon_lora_adapter'.")
print("Execute o próximo script que vou fornecer para completar o processo.")
