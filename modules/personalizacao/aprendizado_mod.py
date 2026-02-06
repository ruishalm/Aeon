import json
import os
import random
from modules.base_module import AeonModule

class AprendizadoModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Aprendizado"
        # Palavras que ativam o salvamento automático
        self.triggers = [
            "boa aeon", "muito bom", "gostei dessa", "isso foi foda", 
            "genial", "aprender isso", "registra essa", "salvar contexto",
            "boa resposta", "isso mesmo"
        ]
        
    def process(self, command: str) -> str:
        # Verifica se o modo oculto está ativo
        cm = self.core_context.get('context_manager')
        if cm and cm.get('stealth_mode'):
            return "Modo oculto ativado. O aprendizado está desativado."

        # Acessa a memória da Lógica Principal
        logic = self.core_context.get('short_term_memory')
        
        if not logic or not logic.last_user_text or not logic.last_ai_response:
            return "Não tenho nada recente na memória para registrar."

        # O que vamos salvar? A interação ANTERIOR ao elogio atual.
        # (Nota: No MainLogic, as vars last_user_text ainda contém a interação anterior 
        #  porque são atualizadas no final do loop. Então pegamos elas direto.)
        
        novo_exemplo = {
            "user": logic.last_user_text,
            "aeon": logic.last_ai_response
        }

        # Validação básica para não salvar lixo
        if len(novo_exemplo['aeon']) < 2 or "Erro" in novo_exemplo['aeon']:
            return "A última resposta foi um erro ou muito curta. Não vou registrar."

        if self._salvar_no_dataset(novo_exemplo):
            respostas_sucesso = [
                "Padrão de comportamento registrado. Ficarei mais inteligente na próxima.",
                "Adicionado ao meu núcleo de personalidade. Obrigado pelo feedback.",
                "Dataset expandido. Evolução processada.",
                "Entendido. Gostou dessa? Vou fazer mais vezes."
            ]
            return random.choice(respostas_sucesso)
        else:
            return "Falha ao gravar no disco rígido."

    def _salvar_no_dataset(self, entry):
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bagagem", "personalidade.json")
            
            data = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            # Evita duplicatas exatas
            if entry not in data:
                data.append(entry)
                
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"[APRENDIZADO] Novo padrão salvo: {entry['user']} -> {entry['aeon'][:30]}...")
                return True
            return True # Já existia, mas conta como sucesso
            
        except Exception as e:
            print(f"[APRENDIZADO] Erro de I/O: {e}")
            return False