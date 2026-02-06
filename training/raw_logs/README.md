# 📂 raw_logs: Coloque Seus Logs Aqui

Esta pasta é para **seus arquivos brutos** antes de conversão.

## 📥 Como Exportar de Cada Plataforma

### 📱 ChatGPT
1. Vá em: https://chatgpt.com/
2. Abra uma conversa
3. Clique no menu **⋯** (três pontos)
4. Selecione **"Share"** → **"Export as JSON"**
5. Salve como: `chatgpt_conversation.json`

**Formato esperado:**
```json
{
  "messages": [
    {"role": "user", "content": "Oi!"},
    {"role": "assistant", "content": "Olá!"}
  ]
}
```

---

### 🧠 Claude (Anthropic)
1. Vá em: https://claude.ai/
2. Abra uma conversa
3. Clique no nome da conversa
4. Menu → **"Export"** → **"JSON"**
5. Salve como: `claude_conversation.json`

**Formato esperado:**
```json
{
  "conversation": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

### 💬 Discord
1. **Opção A (Manual):** Crie um arquivo JSON com:
```json
[
  {"author": "SeuNome", "content": "Oi bot", "timestamp": "2024-01-01T10:00:00"},
  {"author": "BotName", "content": "Olá!", "timestamp": "2024-01-01T10:00:01"}
]
```

2. **Opção B (Exportador):** Use `discord-exporter` ou similar
3. Salve como: `discord_export.json`

---

### 💾 Seus Logs Aeon
- Já existe em: `../../bagagem/temp/conversation.log`
- Copie para cá: `conversation.log`
- Formato: `VOCÊ: texto` e `AEON: texto`

---

### 📄 Formato Genérico Simples
Se tiver um arquivo .txt simples com alternância:
```
Sua mensagem aqui
Resposta do bot aqui
Sua próxima mensagem
Resposta aqui
```

Renomeie para: `simple_log.txt`

---

## ✅ Checklist

- [ ] Exportou pelo menos 1 fonte (ChatGPT, Claude, Discord, ou Aeon)
- [ ] Salvou arquivo em: `training/raw_logs/`
- [ ] Validou JSON (use: https://jsonlint.com/)
- [ ] Pronto para converter com: `python converter.py --source raw_logs/`

---

## 🚨 Erros Comuns

| Erro | Solução |
|------|---------|
| `FileNotFoundError` | Arquivo não está em `raw_logs/` |
| `JSON decode error` | Arquivo é .txt mas deveria ser .json (use `converter.py`) |
| `Nenhum par encontrado` | Formato não reconhecido, veja exemplos acima |

---

## 📝 Nota
- Use **UTF-8 encoding** para todos os arquivos
- Para múltiplos logs, coloque quantos quiser na pasta
- O `converter.py` processa todos automaticamente com `--source raw_logs/`

Próximo passo: `cd .. && python converter.py --source raw_logs/ --jsonl --profile`
