
# =============================================================================
# TEMPLATE: COMO INTEGRAR MODELO FINE-TUNED EM core/brain.py
# =============================================================================

# 1. ADICIONE PARÂMETRO À FUNÇÃO pensar():
def pensar(self, prompt: str, historico_txt: str = "", modo: str = "auto", 
           use_finetuned: bool = False, **kwargs):
    """
    use_finetuned: True para usar modelo personalizado, False para usar default
    """
    
# 2. ADICIONE ESTE CÓDIGO LOGO APÓS o system_prompt:

    # Se solicitado, tenta usar modelo fine-tuned
    if use_finetuned:
        # OPÇÃO A: Groq Fine-tuned (recomendado)
        if self.online and self.client:
            try:
                print("[BRAIN] Usando Groq fine-tuned...")
                chat = self.client.chat.completions.create(
                    model="seu-modelo-id-groq",  # MUDE ISTO
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6
                )
                return chat.choices[0].message.content
            except Exception as e:
                print(f"[BRAIN] Erro: {e}. Tentando fallback...")
        
        # OPÇÃO B: Ollama Fine-tuned (local)
        if self.local_ready:
            try:
                print("[BRAIN] Usando Ollama fine-tuned...")
                r = ollama.chat(model="aeon-personalized", messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ])
                return r['message']['content']
            except Exception as e:
                print(f"[BRAIN] Erro: {e}")

# 3. QUANDO CHAMAR EM main_gui_logic.py:
    # Conversa = usar modelo personalizado
    resposta = self.brain.pensar(texto_usuario, historico, modo="conversa", 
                                 use_finetuned=True)

# =============================================================================
