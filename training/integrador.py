#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRADOR DE MODELOS TREINADOS
Atualiza core/brain.py para usar modelos fine-tuned.
"""

import os
import json
import shutil
from pathlib import Path


class BrainIntegrator:
    """Integra modelos treinados em core/brain.py."""
    
    def __init__(self):
        self.aeon_root = Path(__file__).parent.parent
        self.brain_file = self.aeon_root / "core" / "brain.py"
        self.training_dir = self.aeon_root / "training"
    
    def backup_brain(self):
        """Faz backup do brain.py original."""
        backup = self.brain_file.with_suffix(".py.backup")
        if not backup.exists():
            shutil.copy(self.brain_file, backup)
            print(f"Backup salvo: {backup}")
        return backup
    
    def integrate_groq_finetuned(self, model_id):
        """Integra modelo Groq fine-tuned."""
        # Adiciona nova opção ao pensar()
        code_snippet = f'''
        # MODELO GROQ PERSONALIZADO (Fine-tuned)
        if use_finetuned and self.online and self.client:
            try:
                print(f"[BRAIN] Usando modelo Groq personalizado...")
                chat = self.client.chat.completions.create(
                    model="{model_id}",  # Seu modelo fine-tuned
                    messages=[
                        {{"role": "system", "content": system_prompt}},
                        {{"role": "user", "content": prompt}}
                    ],
                    temperature=0.7
                )
                response = chat.choices[0].message.content
                return response if response else None
            except Exception as e:
                print(f"[BRAIN] Erro modelo Groq: {{e}}. Tentando fallback...")
        '''
        
        print("Snippet para adicionar em core/brain.py:")
        print(code_snippet)
        print("\nSubstitua MODEL_ID pelo seu ID Groq (ex: gpt-3.5-turbo-finetuned-xyz)")
    
    def integrate_ollama_finetuned(self, model_name):
        """Integra modelo Ollama fine-tuned."""
        code_snippet = f'''
        # MODELO OLLAMA PERSONALIZADO (Fine-tuned com LoRA)
        if use_finetuned and self.local_ready:
            try:
                print(f"[BRAIN] Usando modelo Ollama personalizado...")
                r = ollama.chat(model="{model_name}", messages=[
                    {{"role": "system", "content": system_prompt}},
                    {{"role": "user", "content": prompt}}
                ])
                response = r['message']['content']
                return response if response else None
            except Exception as e:
                print(f"[BRAIN] Modelo Ollama não disponível: {{e}}")
        '''
        
        print("Snippet para adicionar em core/brain.py:")
        print(code_snippet)
        print(f"\nSeu modelo será chamado como: ollama run {model_name}")
    
    def create_integration_template(self):
        """Cria template de como integrar no brain.py."""
        template = '''
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
'''
        
        template_file = self.training_dir / "INTEGRATION_TEMPLATE.md"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"Template salvo em: {template_file}")
        return template_file
    
    def verify_models(self):
        """Verifica quais modelos estão disponíveis."""
        models_dir = self.training_dir / "models"
        
        print("\n" + "="*60)
        print("MODELOS DISPONÍVEIS")
        print("="*60)
        
        if not models_dir.exists():
            print("Pasta 'models' não existe ainda.")
            return
        
        subfolders = list(models_dir.iterdir())
        
        if not subfolders:
            print("Nenhum modelo treinado ainda.")
            return
        
        for model_path in subfolders:
            if model_path.is_dir():
                print(f"\n{model_path.name}")
                
                # Verifica Ollama LoRA
                if (model_path / "adapter_model.safetensors").exists():
                    print(f"   - Ollama LoRA")
                
                # Verifica modelo completo
                if (model_path / "pytorch_model.bin").exists():
                    print(f"   - Modelo Completo")
                
                # Verifica config
                if (model_path / "config.json").exists():
                    with open(model_path / "config.json") as f:
                        config = json.load(f)
                        base_model = config.get("_name_or_path", "desconhecido")
                        print(f"   - Base: {base_model}")
    
    def create_quick_start(self):
        """Cria guia rápido de integração."""
        guide = """# INTEGRAÇÃO RÁPIDA

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
"""
        
        quick_file = self.training_dir / "QUICK_INTEGRATION.md"
        with open(quick_file, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        print(f"Guia rápido: {quick_file}")


def main():
    import sys
    
    integrator = BrainIntegrator()
    
    if len(sys.argv) < 2:
        print("""
Use: python integrador.py [comando]

COMANDOS:
  - backup              → Faz backup de core/brain.py
  - template            → Cria template de integração
  - verify              → Verifica modelos disponíveis
  - groq <model_id>     → Integra Groq fine-tuned
  - ollama <model_name> → Integra Ollama fine-tuned

EXEMPLO:
  python integrador.py groq gpt-3.5-turbo-finetuned-xyz
  python integrador.py ollama aeon-personalized
        """)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "backup":
        integrator.backup_brain()
    
    elif cmd == "template":
        integrator.create_integration_template()
        integrator.create_quick_start()
    
    elif cmd == "verify":
        integrator.verify_models()
    
    elif cmd == "groq" and len(sys.argv) > 2:
        model_id = sys.argv[2]
        integrator.integrate_groq_finetuned(model_id)
        integrator.create_integration_template()
    
    elif cmd == "ollama" and len(sys.argv) > 2:
        model_name = sys.argv[2]
        integrator.integrate_ollama_finetuned(model_name)
        integrator.create_integration_template()
    
    else:
        print(f"Comando desconhecido: {cmd}")


if __name__ == "__main__":
    main()
