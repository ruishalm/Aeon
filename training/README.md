# 🎯 RESUMO: SUA ESTRATÉGIA DE TREINAMENTO

## Você tem 2 modos no Aeon:
- **Online (Groq na nuvem)** → Melhor qualidade, mas precisa internet
- **Offline (Ollama local)** → Rápido, privado, sem internet

**COISA BOA:** Você pode treinar OS DOIS com os mesmos dados! 🎉

---

## Fluxo Rápido (5 passos)

```
1. COLETAR dados
   └─ Copie logs (ChatGPT, Claude, Discord, Aeon) para: training/raw_logs/

2. CONVERTER logs
   └─ python converter.py --source raw_logs/ --jsonl --profile

3. EXTRAIR PADRÕES (seu estilo)
   └─ python extrair_padroes.py processed/dados_combined.jsonl

4. TREINAR modelo
   └─ Escolha 1 (Groq / Ollama / Unsloth) e rode script

5. INTEGRAR em Aeon
   └─ Coloque modelo novo em core/brain.py
```

---

## O que cada Script Faz

### `converter.py` ⭐
**Transforma qualquer log em formato VOCÊ/AEON**

Suporta:
- ✅ ChatGPT JSON
- ✅ Claude JSON  
- ✅ Discord JSON
- ✅ Logs simples (.txt)
- ✅ Logs genéricos

```bash
python converter.py --source raw_logs/ --jsonl --profile
```

**Output:**
- `processed/dados_combined.txt` (VOCÊ/AEON)
- `processed/dados_combined.jsonl` (pronto para treinar)
- Console mostra análise de seus padrões

---

### `extrair_padroes.py` ⭐
**Detecta como você fala e gera system_prompt customizado**

Analisa:
- Gírias que você usa (rodar, crashar, etc)
- Expressões favoritas (tipo, né, etc)
- Seu tom (entusiasmado? Investigativo?)
- Estrutura (muitas perguntas? Muitos comandos?)
- Emojis (qual frequência?)

```bash
python extrair_padroes.py processed/dados_combined.jsonl
```

**Output:**
- `CUSTOM_SYSTEM_PROMPT.md` (seu perfil em format de prompt)

Depois você copia esse prompt e coloca em `core/brain.py` → Aeon fala igual você!

---

## OPÇÃO 1: Groq (Nuvem)

```
VOCÊ TREINA (20-30 min via API) → MODELO FICA NA GROQ
↓
Integra em core/brain.py (sem instalar nada)
↓
Aeon chama Groq com modelo personalizado
```

**Vantagens:**
- ⚡ Rápido
- ☁️ Na nuvem (sem hardware local)
- 🔄 Fácil atualizar

**Passos:**
```bash
python converter.py --source raw_logs/ --jsonl
# Script de fine-tune Groq (vou providenciar)
# Integrar em core/brain.py
```

---

## OPÇÃO 2: Ollama (Local + LoRA)

```
VOCÊ TREINA (1-2 horas) → MODELO FICA NO SEU PC
↓
Rodando localmente em Ollama
↓
Aeon chama modelo local automaticamente
```

**Vantagens:**
- 🏠 Privado (nada sai do PC)
- 📱 Offline (sem internet)
- 🔧 Customizável ao máximo

**Passos:**
```bash
pip install llama-factory
python converter.py --source raw_logs/ --jsonl
# Configurar e rodar fine-tune local
# Exportar para Ollama
# Integrar em core/brain.py
```

---

## OPÇÃO 3: Unsloth (Mais Rápido Ainda)

```
VOCÊ TREINA (15-30 min) → MODELO PRONTO
↓
Pode virar LoRA (Ollama) ou arquivo completo
↓
Integra onde quiser (Groq, Ollama, local)
```

**Vantagens:**
- ⚡⚡ Super rápido
- 🎯 Melhor qualidade
- 🔗 Compatível com Groq e Ollama

**Passos:**
```bash
pip install unsloth
python converter.py --source raw_logs/ --jsonl
# Script Unsloth (vou providenciar)
# Exportar modelo
# Integrar em core/brain.py
```

---

## Comparação Rápida

| Aspecto | Groq | Ollama | Unsloth |
|---------|------|--------|---------|
| **Tempo** | 20-30 min | 1-2 horas | 15-30 min ⭐ |
| **Hardware** | Cloud | Local | Local + GPU |
| **Privacidade** | ☁️ Cloud | 🏠 Total | 🏠 Total |
| **Fácil** | ✅ Sim | ⚠️ Médio | ✅ Sim |
| **Custo** | 💰 API | Grátis | Grátis |
| **Offline** | ❌ Não | ✅ Sim | ✅ Sim |

---

## 🚀 Comece AGORA!

### Passo 1: Converter Seus Logs
```bash
cd d:\Dev\Aeon\Aeon\training
python converter.py --source raw_logs/ --jsonl --profile
```

Se houver erro, coloque logs em `raw_logs/` (veja `raw_logs/README.md`)

### Passo 2: Extrair Seu Perfil
```bash
python extrair_padroes.py processed/dados_combined.jsonl
```

Abra `CUSTOM_SYSTEM_PROMPT.md` e veja seu perfil detectado!

### Passo 3: Escolha 1 Método
- **Groq:** Script que vou fornecer
- **Ollama:** Vou fornecer config + script
- **Unsloth:** Vou fornecer notebook + script

### Passo 4: Integrate em core/brain.py
Cole seu novo modelo no `pensar()`

### Passo 5: Teste!
```bash
python main.py
"Olá Aeon!"
# Esperado: Resposta em SEU ESTILO! 🎯
```

---

## 📚 Arquivos Complementares

- ✅ **TRAINING_GUIDE.md** - Guia super detalhado com exemplos
- ✅ **converter.py** - Converte logs automaticamente
- ✅ **extrair_padroes.py** - Detecta seus padrões
- ✅ **raw_logs/README.md** - Como exportar de cada plataforma

---

## ❓ TL;DR (Muito Longo; Não Li)

1. **Coleta:** Logs em `training/raw_logs/`
2. **Conversor:** `python converter.py --source raw_logs/ --jsonl --profile`
3. **Padrões:** `python extrair_padroes.py processed/dados_combined.jsonl`
4. **Treina:** Escolha Groq / Ollama / Unsloth
5. **Integra:** Cole modelo em `core/brain.py`
6. **Testa:** `python main.py` e fale com Aeon

---

**Vamos fazer isso?** 🚀
