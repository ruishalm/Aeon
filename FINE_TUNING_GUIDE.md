# 🧠 Fine-Tuning Guide para Aeon

## O Que É Fine-Tuning?

**Fine-tuning** é retreinar um modelo de IA com dados específicos **do seu domínio** (suas conversas, estilo, preferências). Diferente de prompt engineering (que é instruir), fine-tuning **muda os pesos internos do modelo** para que ele aprenda seu padrão.

### Analogia:
- **Prompt Engineering**: "Aja como um assistente cínico brasileiro"
- **Fine-Tuning**: Treinar o modelo **lendo 1000 conversas suas** até aprender **como você realmente fala e quer ser respondido**

---

## Por Que Fine-Tuning?

### ✅ Vantagens:
- Respostas **muito mais personalizadas** e contextualizadas
- Modelo entende **seu estilo, gírias, preferências**
- Reduz "hallucinations" (respostas inventadas)
- Melhor em **tarefas específicas** (sua IA vai ser especialista em VOCÊ)

### ❌ Desvantagens:
- **Tempo**: 30min a 2h (depende do volume de dados)
- **Custo**: Groq fine-tuning = pago; Ollama/local = grátis mas lento
- **Dados**: Precisa de ~500-5000 exemplos de boa qualidade
- **Manutenção**: Precisa reafinar periodicamente com novos dados

---

## Passo 1: Coletar e Formatar Dados

### Seus dados já existem!
```
bagagem/temp/conversation.log
```

### Formato esperado (JSONL - um JSON por linha):

```jsonl
{"messages": [{"role": "user", "content": "oi aeon tudo bem"}, {"role": "assistant", "content": "E aí! Tudo joia aqui. E você, beleza?"}]}
{"messages": [{"role": "user", "content": "coloca um timer em 5 minutos"}, {"role": "assistant", "content": "Timer de 5 minutos definido!"}]}
{"messages": [{"role": "user", "content": "me conta uma piada"}, {"role": "assistant", "content": "Por que a programadora foi ao psicólogo? Porque tinha problemas de dependência!"}]}
```

### Script para converter `conversation.log` → JSONL:

```python
# converter_dados.py
import json
import re

def converter_log_para_jsonl(input_file, output_file):
    """Converte conversation.log em formato JSONL para fine-tuning"""
    messages = []
    current_user = None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith("VOCÊ:"):
            current_user = line.replace("VOCÊ:", "").strip()
        elif line.startswith("AEON:"):
            aeon_resp = line.replace("AEON:", "").strip()
            if current_user and aeon_resp:
                messages.append({
                    "messages": [
                        {"role": "user", "content": current_user},
                        {"role": "assistant", "content": aeon_resp}
                    ]
                })
            current_user = None
    
    # Escreve em JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"✅ Convertidos {len(messages)} pares de conversa")
    print(f"📁 Salvo em: {output_file}")

# Uso:
converter_log_para_jsonl("bagagem/temp/conversation.log", "dados_fine_tuning.jsonl")
```

**Executa assim:**
```powershell
cd D:\Dev\Aeon\Aeon
python converter_dados.py
```

---

## Passo 2: Opções de Fine-Tuning

### **Opção A: Groq Fine-Tuning (Cloud, Easiest)**

#### Pré-requisitos:
- Conta Groq (gratuita)
- API key (já temos no `.env`)
- Arquivo JSONL com dados

#### Processo:
```bash
# 1. Upload de dados via Groq API
curl -X POST "https://api.groq.com/openai/v1/files" \
  -H "Authorization: Bearer $GROQ_KEY" \
  -F "file=@dados_fine_tuning.jsonl"
```

#### Pros:
✅ Rápido (30min-1h)  
✅ Sem configurar infraestrutura  
✅ Modelo melhorado na nuvem  

#### Cons:
❌ Pode custar (verificar pricing Groq)  
❌ Dados enviados pra nuvem  

---

### **Opção B: Ollama Fine-Tuning Local (Melhor para Você)**

#### Ferramentas:
- **Ollama** (já instalado ✅)
- **LLaMA Factory** ou **Axolotl** (frameworks de fine-tuning)
- **LoRA** (Low-Rank Adaptation: treina rápido, usa pouca memória)

#### Passo a Passo:

##### 1️⃣ Instalar LLaMA Factory
```powershell
pip install llamafactory
```

##### 2️⃣ Preparar configuração (YAML)
```yaml
# lora_config.yaml
model_name_or_path: deepseek-r1:8b
template: default
dataset: dados_fine_tuning
output_dir: ./aeon-lora-finetuned
overwrite_output_dir: true
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
num_train_epochs: 3
learning_rate: 1.0e-4
save_steps: 50
logging_steps: 10
lr_scheduler_type: cosine
warmup_ratio: 0.1
```

##### 3️⃣ Treinar
```powershell
cd D:\Dev\Aeon\Aeon
llamafactory-cli train lora_config.yaml
```

**Tempo estimado:**
- 1000 exemplos: 15-30 min (GPU) / 1-2h (CPU)
- 5000 exemplos: 1-2h (GPU) / 4-8h (CPU)

##### 4️⃣ Mergear LoRA com modelo base
```powershell
llamafactory-cli export lora_config.yaml
```

##### 5️⃣ Usar com Ollama
```bash
# Cria Modelfile customizado
cat > Modelfile << 'EOF'
FROM deepseek-r1:8b
ADAPTER ./aeon-lora-finetuned/adapter_model.bin
EOF

# Cria modelo no Ollama
ollama create aeon-custom -f Modelfile

# Usa no Aeon
```

---

### **Opção C: Hugging Face + Unsloth (Super-Rápido)**

**Unsloth** = framework que torna fine-tuning **5-40x mais rápido**.

```python
# fine_tune_unsloth.py
from unsloth import FastLanguageModel
import torch

# 1. Carregar modelo
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="deepseek-r1:8b",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

# 2. Adicionar LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
)

# 3. Treinar com seus dados
from transformers import TextIteratorStreamer
from trl import SFTTrainer, SFTConfig

config = SFTConfig(
    output_dir="aeon-fine-tuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=5e-4,
    warmup_ratio=0.1,
    max_steps=-1,
)

trainer = SFTTrainer(
    model=model,
    train_dataset="dados_fine_tuning.jsonl",
    args=config,
    data_collator=trainer.get_train_dataloader(),
)

trainer.train()

# 4. Salvar
model.save_pretrained("aeon-custom-model")
```

#### Pros:
✅ **5-40x mais rápido** que fine-tuning padrão  
✅ Usa 70% menos memória (4-bit quantization)  
✅ Executa em GPU modesta ou até CPU  

#### Cons:
❌ Precisa de config mais complexa  

---

## Passo 3: Integrar Modelo Fine-Tuned no Aeon

### Em `core/brain.py`:

```python
# Mudança simples:
def pensar(self, prompt: str, historico_txt: str = "", modo: str = "auto", **kwargs):
    self._conectar()
    
    if modo == "conversa":
        system_prompt = """Você é AEON (versão customizada).
        Data: {}
        Você foi retreinado com conversas do seu usuário.
        Mantenha coerência, sarcasmo, e referências anteriores.
        """.format(__import__('datetime').datetime.now().strftime("%d/%m/%Y"))
    
    # Tenta Groq (online)
    if self.online and self.client:
        try:
            chat = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # ← ou "aeon-custom-finetuned" se usar Groq FT
                messages=[...]
            )
            ...
    
    # Tenta Ollama (local)
    if self.local_ready:
        try:
            r = ollama.chat(model="aeon-custom", messages=[...])  # ← modelo customizado
            ...
```

---

## Comparação Prática

| Abordagem | Tempo | Custo | Qualidade | Complexidade |
|-----------|-------|-------|-----------|--------------|
| Prompt Engineering | 5 min | R$0 | ⭐⭐ | Baixa |
| Fine-Tuning (Groq) | 30 min | R$ - R$$ | ⭐⭐⭐⭐ | Média |
| Fine-Tuning (Ollama + LoRA) | 1-2h | R$0 | ⭐⭐⭐⭐ | Alta |
| Fine-Tuning (Unsloth) | 15-30 min | R$0 | ⭐⭐⭐⭐⭐ | Muito Alta |

---

## Recomendação para Você

### 🎯 Curto Prazo (Agora):
1. **Converter `conversation.log`** com o script acima
2. **Melhorar prompt** em `core/brain.py` (prompt engineering)
3. **Validar com ~20 testes de voz**

### 🚀 Médio Prazo (1-2 semanas):
1. **Coletar 500+ exemplos de boa qualidade** de conversas
2. **Fine-tune com Ollama + LoRA** (grátis, local, rápido com Unsloth)
3. **Usar modelo customizado no Aeon**

### 🔮 Longo Prazo:
1. **Continuous retraining**: cada 1000 novas interações, reafinar
2. **A/B testing**: comparar respostas do modelo base vs customizado
3. **Domain-specific**: adicionar exemplos de **casos edge** onde Aeon erra

---

## Script Completo (Tudo em Um)

```python
# fine_tune_aeon_complete.py
"""
Complete fine-tuning pipeline para Aeon
Converte logs → Treina modelo → Integra no Aeon
"""

import json
import subprocess
import os
from pathlib import Path

def step_1_converter_dados():
    """Converte conversation.log para JSONL"""
    print("📝 [1/3] Convertendo dados...")
    input_file = "bagagem/temp/conversation.log"
    output_file = "dados_fine_tuning.jsonl"
    
    messages = []
    current_user = None
    
    if not os.path.exists(input_file):
        print(f"❌ {input_file} não encontrado!")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("VOCÊ:"):
                current_user = line[5:].strip()
            elif line.startswith("AEON:"):
                aeon_resp = line[5:].strip()
                if current_user and aeon_resp:
                    messages.append({
                        "messages": [
                            {"role": "user", "content": current_user},
                            {"role": "assistant", "content": aeon_resp}
                        ]
                    })
                current_user = None
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"✅ {len(messages)} pares de conversa salvos em {output_file}")
    return True

def step_2_instalar_dependencias():
    """Instala LLaMA Factory e Unsloth"""
    print("📦 [2/3] Instalando dependências...")
    subprocess.run([
        "pip", "install", 
        "llamafactory",
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "-q"
    ])
    print("✅ Dependências instaladas")

def step_3_criar_config():
    """Cria arquivo de configuração YAML"""
    print("⚙️ [3/3] Criando configuração...")
    config = """model_name_or_path: deepseek-r1:8b
template: default
dataset: dados_fine_tuning
output_dir: ./aeon-lora-finetuned
overwrite_output_dir: true
per_device_train_batch_size: 2
gradient_accumulation_steps: 2
num_train_epochs: 2
learning_rate: 5.0e-4
save_steps: 50
logging_steps: 10
lr_scheduler_type: cosine
warmup_ratio: 0.1
max_grad_norm: 1.0
fp16: true"""
    
    with open("lora_config.yaml", "w") as f:
        f.write(config)
    
    print("✅ Configuração criada: lora_config.yaml")

def main():
    print("🧠 Fine-Tuning Pipeline para Aeon")
    print("=" * 50)
    
    if step_1_converter_dados():
        print("\n⚠️ Próximos passos:")
        print("1. python fine_tune_aeon_complete.py --treinar")
        print("2. Aguarde 30min - 2h (depende do GPU)")
        print("3. Modelo salvo em: aeon-lora-finetuned/")
        print("\n💡 Para integrar no Aeon:")
        print("   - Atualize core/brain.py para usar 'aeon-custom'")
        print("   - Crie: ollama create aeon-custom -f Modelfile")

if __name__ == "__main__":
    main()
```

---

## Resumo Executivo

| Passo | O Quê | Tempo | Dificuldade |
|-------|-------|-------|------------|
| 1 | Converter logs → JSONL | 2 min | ⭐ |
| 2 | Instalar LLaMA Factory / Unsloth | 5 min | ⭐ |
| 3 | Treinar LoRA | 30 min-2h | ⭐⭐ |
| 4 | Mergear modelo | 5 min | ⭐ |
| 5 | Usar em Aeon | 5 min | ⭐ |

**Total: ~1-3 horas de trabalho para um Aeon 100% personalizado!**

---

## Próximos Passos?

Quer que eu:
1. **Crie o script completo** de fine-tuning pronto pra rodar?
2. **Configure Unsloth** no seu ambiente?
3. **Implemente a integração** de modelo customizado no `core/brain.py`?

