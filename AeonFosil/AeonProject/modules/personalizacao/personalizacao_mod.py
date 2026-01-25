from modules.base_module import AeonModule
from typing import List, Dict
import re
import asyncio
import edge_tts
import threading

class PersonalizacaoModule(AeonModule):
    """
    Módulo para personalizar o comportamento e aparência do Aeon.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Personalização"
        self.triggers = [
            "mudar a voz para", "listar vozes",
            "palavra de ativação", "lembre que", "mudar o tema"
        ]

    @property
    def dependencies(self) -> List[str]:
        """Personalização depende de config_manager."""
        return ["config_manager"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Personaliza comportamento, voz e aparência do Aeon"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - valida acesso a config_manager."""
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            print("[PersonalizacaoModule] Erro: config_manager não encontrado")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            return "Gerenciador de configuração não encontrado."

        # Mudar a voz (para EdgeTTS)
        if "mudar a voz para" in command:
            nova_voz = command.split("mudar a voz para")[-1].strip()
            if nova_voz:
                # Salva a nova voz na configuração do sistema
                config_manager.set_system_data("VOICE", nova_voz)
                return f"Ok, minha voz online foi alterada para {nova_voz}."
            else:
                return "Não entendi para qual voz você quer mudar."

        # Listar vozes disponíveis
        if "listar vozes" in command:
            threading.Thread(target=self._get_voices_thread).start()
            return "Buscando vozes disponíveis. Isso pode demorar um pouco."

        # Gerenciar palavras de ativação
        if "palavra de ativação" in command:
            triggers = config_manager.get_system_data("triggers", [])
            if "adicionar" in command:
                palavra = command.split("adicionar palavra de ativação")[-1].strip()
                if palavra and palavra not in triggers:
                    triggers.append(palavra)
                    config_manager.set_system_data("triggers", triggers)
                    return f"Adicionado '{palavra}' às palavras de ativação."
                else:
                    return "Palavra inválida ou já existente."
            
            elif "remover" in command:
                palavra = command.split("remover palavra de ativação")[-1].strip()
                if palavra in triggers:
                    triggers.remove(palavra)
                    config_manager.set_system_data("triggers", triggers)
                    return f"'{palavra}' removida das palavras de ativação."
                else:
                    return f"Palavra '{palavra}' não encontrada."

            elif "listar" in command:
                return "As palavras de ativação atuais são: " + ", ".join(triggers)

        # Lembrar preferências do usuário
        if "lembre que" in command:
            match = re.search(r'lembre que (.*?) é (.*)', command)
            if match:
                key, value = match.groups()
                prefs = config_manager.get_system_data("user_prefs", {})
                prefs[key.strip()] = value.strip()
                config_manager.set_system_data("user_prefs", prefs)
                return f"Entendido. Vou lembrar que {key.strip()} é {value.strip()}."
            else:
                return "Não entendi. Use o formato 'lembre que [algo] é [valor]'."

        # Mudar o tema (A GUI precisaria de uma forma de observar essa mudança)
        if "mudar o tema para" in command:
            theme_name = command.split("mudar o tema para")[-1].strip()
            # A lógica de reinicialização da UI ficaria no main.py
            # Aqui, apenas salvamos a configuração.
            config_manager.set_system_data("current_theme", theme_name)
            return f"Tema alterado para {theme_name}. A mudança será aplicada na próxima vez que eu iniciar."
            
        return ""

    def _get_voices_thread(self):
        """Busca as vozes em uma thread para não bloquear a UI."""
        io_handler = self.core_context.get("io_handler")
        try:
            voices = asyncio.run(edge_tts.list_voices())
            pt_voices = [v['ShortName'] for v in voices if v['Locale'].startswith('pt-BR')]
            response = "As vozes em português encontradas são: " + ", ".join(pt_voices)
        except Exception as e:
            response = f"Ocorreu um erro ao buscar as vozes: {e}"
        
        if io_handler:
            io_handler.falar(response)
