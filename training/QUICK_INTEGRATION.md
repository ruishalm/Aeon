# INTEGRAÇÃO RÁPIDA

## Se treinou com GROQ:

1. Pegue o ID do modelo em: https://console.groq.com
2. Adicione em `core/brain.py` (função `pensar`):
   ```python
   groq_finetuned_model = "seu-id-aqui"
   ```
3. Use: `brain.pensar(texto, use_finetuned=True)`

## Se treinou com OLLAMA:

1. Verifique modelo: `ollama list`
2. Adicione em `core/brain.py`:
   ```python
   self.ollama_finetuned_model = "aeon-personalized"
   ```
3. Use: `brain.pensar(texto, use_finetuned=True)`

## Se treinou com UNSLOTH:

1. Exporte modelo
2. Converta para Ollama ou Groq (veja scripts)
3. Integre como acima

---

## Testando:

```python
from core.brain import AeonBrain

brain = AeonBrain({})
resposta1 = brain.pensar("Oi!", use_finetuned=False)  # Default
resposta2 = brain.pensar("Oi!", use_finetuned=True)   # Seu modelo
```

---

**Resultado esperado:** Resposta2 fala no seu estilo!
