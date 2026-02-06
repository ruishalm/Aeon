# 🎓 GUIA COMPLETO: TREINAMENTO DE AEON COM SEUS PADRÕES

## 📁 Estrutura de Pastas

```
training/
├── raw_logs/              # Coloque seus arquivos aqui
│   ├── README.md          # Instruções para exportar
│   ├── chatgpt.json       # Exports de ChatGPT
│   ├── claude.json        # Exports de Claude
│   ├── discord.json       # Exports de Discord
│   └── conversation.log   # Seus logs locais
├── processed/
│   ├── dados_training.txt    # Após converter: VOCÊ/AEON
│   └── dados_training.jsonl  # Pronto para fine-tuning
├── models/
│   ├── aeon-offline-lora/    # Modelo treinado (Ollama)
│   └── aeon-online/          # Metadados (Groq)
├── converter.py           # ⭐ Script de conversão universal
├── extrair_padroes.py     # ⭐ Detecta seu estilo de fala
└── TRAINING_GUIDE.md      # Este arquivo
```

---

## 🚀 PASSO 1: COLETAR LOGS

### Opção A: Seus logs do Aeon
- Você já tem: `bagagem/temp/conversation.log`
- Copie para: `training/raw_logs/conversation.log`

### Opção B: ChatGPT
1. Vá em: https://chatgpt.com/c/...
2. Clique em **"Share"** → **"Export as HTML/JSON"**
3. Salve em: `training/raw_logs/chatgpt_export.json`

### Opção C: Claude
1. Em Claude, clique na conversa
2. Menu → **"Export conversation"**
3. Salve em: `training/raw_logs/claude_export.json`

### Opção D: Discord
1. Use um bot tipo Turing ou similar
2. Exporte JSON com estrutura: `[{"author": "você", "content": "...", "timestamp": "..."}, ...]`
3. Salve em: `training/raw_logs/discord_export.json`

---

## 🔄 PASSO 2: CONVERTER LOGS

### Comando Básico
```bash
cd training
python converter.py --source raw_logs/conversation.log --output processed/dados_training.txt
```

### Converter Múltiplos Arquivos
```bash
python converter.py --source raw_logs/ --output processed/dados_training.txt --jsonl --profile
```

### Flags:
- `--source FILE`: Arquivo ou pasta a converter
- `--output PATH`: Onde salvar (padrão: `processed/dados_training.txt`)
- `--jsonl`: Também salva em formato JSONL (recomendado)
- `--profile`: Mostra análise de seus padrões de linguagem

### Exemplo Completo:
```bash
python converter.py \
  --source raw_logs/ \
  --output processed/dados_combined.txt \
  --jsonl \
  --profile
```

**Saída esperada:**
```
🔍 Formato detectado: simple
📂 Processando: conversation.log
   ✅ 45 pares extraídos
📂 Processando: chatgpt.json
   ✅ 120 pares extraídos

==================================================
📊 PERFIL DE LINGUAGEM DO USUÁRIO
==================================================

[PADRÕES DO USUÁRIO]
- Usa gírias de dev: rodar, crashar, debug
- Tom: entusiasmado/direto
- Palavras frequentes: tipo, sistema, erro, rodar

==================================================

✨ Conversão completa! 165 pares processados.
✅ Salvo: processed/dados_combined.txt
✅ Salvo (JSONL): processed/dados_combined.jsonl
```

---

## 🎯 PASSO 3: EXTRAIR SEUS PADRÕES DE LINGUAGEM

### Comando:
```bash
python extrair_padroes.py processed/dados_combined.txt
```

### O que faz:
1. **Detecta gírias de dev** que você usa (rodar, crashar, etc)
2. **Encontra expressões favoritas** (tipo, né, sabe, etc)
3. **Identifica seu tom** (entusiasmado, irônico, investigativo, etc)
4. **Analisa estrutura** (perguntas frequentes? Comandos? Explicações longas?)
5. **Gera `CUSTOM_SYSTEM_PROMPT.md`** com suas características

### Saída Esperada:
```
==================================================
📊 PERFIL DE LINGUAGEM DETECTADO
==================================================

🔧 GÍRIAS DE DEV:
   - rodar: 12x
   - crashar: 8x
   - debug: 6x

💬 GÍRIAS/EXPRESSÕES:
   - 'tipo': 45x
   - 'né': 32x
   - 'sabe': 28x

📝 PALAVRAS-CHAVE:
   - sistema, erro, código, função, teste

🎭 TOM PRINCIPAL: ENTUSIASMADO

📏 Comprimento médio das mensagens: 87 caracteres

😀 Usa emojis com frequência: 15.3%

==================================================
✨ System_prompt customizado salvo em: CUSTOM_SYSTEM_PROMPT.md
```

---

## 📝 PASSO 4: REVISAR SEU SYSTEM_PROMPT CUSTOMIZADO

Abra `training/CUSTOM_SYSTEM_PROMPT.md` e veja:

```markdown
[IDENTIDADE]
Você é AEON...

[PERSONALIDADE BASE]
...

[GÍRIAS DO USUÁRIO]
Você usa frequentemente: rodar, crashar, debug

[EXPRESSÕES INFORMAIS]
Usa constantemente: tipo, né, sabe

[TOM]
Seu tom é: entusiasmado. Responda de forma similar.

[ESTILO]
O usuário faz muitas perguntas. Seja conversacional.
O usuário dá muito comando. Responda executivo, sem blablabla.

[DIRETRIZES TÉCNICAS]
MODO 1: AÇÃO (se pedir algo que exija interação)
Responda EXATAMENTE com: {"tool": "Modulo.funcao", "param": "valor"}

MODO 2: CONVERSA (papo/filosofia)
Responda com TEXTO PURO. Máx 2 parágrafos. Seja conciso.
```

---

## 🧠 PASSO 5: ESCOLHER MÉTODO DE TREINAMENTO

Você tem 3 opções. Você pode usar as 3 em paralelo!

### OPÇÃO 1️⃣: Groq (Cloud - Recomendado para começar)
**Vantagem:** Rápido, sem instalar nada, resultados em horas.

#### Comandos:
```bash
# 1. Converter para formato Groq
python converter.py --source processed/dados_combined.txt --jsonl

# 2. Fazer fine-tune na Groq API (via CLI ou Python)
pip install groq

# Depois copie o script que vou fornecer:
python groq_finetuning.py --data processed/dados_combined.jsonl --model llama-3.3-70b

# 3. Integrar em core/brain.py
# Seus modelos ficarão em: https://console.groq.com/keys
```

#### Resultado:
- Modelo treinado na nuvem
- Disponível via API Groq
- Chamadas normais em `core/brain.py` (transparente)

---

### OPÇÃO 2️⃣: Ollama (Local + LoRA - Bom balanço)
**Vantagem:** Corre local, privado, sem API keys.

#### Comandos:
```bash
# 1. Instalar Ollama se não tiver
# https://ollama.ai

# 2. Converter dados
python converter.py --source processed/dados_combined.txt --jsonl

# 3. Usar LLaMA Factory para fine-tune
pip install llama-factory

# Depois (vou fornecer config):
llamafactory-cli train models/ollama_lora_config.yaml

# 4. Exportar LoRA para Ollama
# Usar script de conversão que vou fornecer

# 5. Testar local
ollama run aeon-personalized
```

#### Resultado:
- Modelo rodando localmente
- No seu computador, sem internet
- Integra em `core/brain.py` como fallback

---

### OPÇÃO 3️⃣: Unsloth (Mais rápido ainda)
**Vantagem:** Treinamento ultrarápido, otimizado, excelente qualidade.

#### Comandos:
```bash
# 1. Instalar
pip install unsloth

# 2. Converter dados
python converter.py --source processed/dados_combined.txt --jsonl

# 3. Treinar (script que vou fornecer)
python unsloth_train.py --data processed/dados_combined.jsonl

# 4. Exportar modelo
# Pode virar LoRA para Ollama ou arquivo completo

# 5. Integrar em core/brain.py
```

#### Resultado:
- Modelo treinado em 15-30 min (vs horas em outros)
- Qualidade excelente
- Funciona com Groq ou Ollama

---

## 📋 CHECKLIST COMPLETO

### Sem Fine-Tuning:
- [x] Aeon conversa naturalmente ✅
- [x] Módulos funcionam ✅
- [x] Brain usa Groq+Ollama ✅

### Com Fine-Tuning:
- [ ] **Copiar logs para** `training/raw_logs/`
- [ ] **Rodar converter.py** → gera `dados_training.jsonl`
- [ ] **Rodar extrair_padroes.py** → gera `CUSTOM_SYSTEM_PROMPT.md`
- [ ] **Revisar** `CUSTOM_SYSTEM_PROMPT.md`
- [ ] **Escolher 1 opção** (Groq / Ollama / Unsloth)
- [ ] **Treinar** (15 min a 2 horas)
- [ ] **Exportar** modelo
- [ ] **Integrar em** `core/brain.py`
- [ ] **Testar** "Olá Aeon!" → responde com seu estilo!

---

## 🔗 ARQUIVOS RELACIONADOS

1. **converter.py** - Transforma logs de qualquer fonte em VOCÊ/AEON
2. **extrair_padroes.py** - Detecta seu estilo + gera system_prompt customizado
3. **core/brain.py** - Integra os modelos treinados

---

## ⚠️ TROUBLESHOOTING

### "Erro ao ler arquivo"
- Verifique encoding (deve ser UTF-8)
- Se for `.json`, valide em: https://jsonlint.com/

### "Nenhum par encontrado"
- Seu arquivo pode estar vazio ou em formato não reconhecido
- Tente converter manualmente para VOCÊ/AEON primeiro

### "JSONL inválido"
- Cada linha deve ser um JSON completo
- Use: `python -m json.tool seu_arquivo.jsonl` para validar

### "Modelo não carrega"
- Verifique se Ollama está rodando: `ollama list`
- Se Groq, verifique `GROQ_KEY` em `.env`

---

## 🎁 PRÓXIMOS PASSOS

Após treinar:

1. **Teste o modelo:**
   ```bash
   cd d:\Dev\Aeon\Aeon
   python main.py
   # Fale: "Olá Aeon! Como tá?"
   # Esperado: Resposta em seu estilo (gírias, tom, etc)
   ```

2. **Refine mais:**
   - Cole suas conversas atuais em `raw_logs/`
   - Reconverta e retreine a cada semana

3. **Personalize ainda mais:**
   - Edite `CUSTOM_SYSTEM_PROMPT.md` manualmente
   - Adicione diretrizes que só você sabe

---

## 📞 DÚVIDAS?

**Q: Posso usar todas as 3 opções?**
A: Sim! Teste uma de cada. Veja qual responde melhor no seu caso.

**Q: Quanto tempo leva?**
A: Groq: 1-2 horas (cloud). Ollama: 2-4 horas (local). Unsloth: 15-30 min (rápido).

**Q: Preciso de GPU?**
A: Unsloth e Ollama são mais rápidos com GPU, mas rodam em CPU também.

**Q: E se tiver poucos dados?**
A: Mínimo 20 pares. Ideal: 100+. Quanto mais, melhor a personalização.

**Q: Aeon vai esquecer dos módulos?**
A: Não! O fine-tuning é só para conversa. Módulos mantêm funcionamento normal.

---

## 🚀 Comece Agora!

```bash
cd training
python converter.py --source raw_logs/ --jsonl --profile
python extrair_padroes.py processed/dados_training.txt
```

Depois me mostra os resultados! 🎯
