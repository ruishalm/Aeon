import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# Adiciona o caminho raiz do projeto para que os imports funcionem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.module_manager import ModuleManager
from modules.sistema.sys_mod import SistemaModule

class TestAIRouting(unittest.TestCase):
    """
    Testa o novo fluxo de roteamento de comandos 'AI-First'.
    Verifica se o ModuleManager consegue interpretar as decisões da IA (simuladas)
    e executar as funções corretas nos módulos.
    """

    def setUp(self):
        """
        Prepara um ambiente de teste limpo para cada teste.
        - Cria um 'cérebro' simulado (Mock).
        - Instancia um ModuleManager real.
        - Carrega manualmente um módulo 'Sistema' real para ser usado como 'ferramenta'.
        """
        # 1. Simular o cérebro e seu contexto
        self.mock_brain = Mock()
        self.core_context = {
            "brain": self.mock_brain,
            "io_handler": Mock(),
            # Adicionamos um mock para a memória vetorial que é usada no route_command
            "vector_memory": Mock()
        }

        # 2. Instanciar o ModuleManager com o cérebro simulado
        self.module_manager = ModuleManager(self.core_context)
        
        # 3. Instanciar e "carregar" um módulo real para ser a ferramenta de teste
        # Isso simula o estado do ModuleManager após o carregamento dos módulos.
        self.sistema_module = SistemaModule(self.core_context)
        self.module_manager.modules.append(self.sistema_module)
        self.module_manager.module_map['sistema'] = self.sistema_module

        # Mock para o get_module para garantir que o sistema de bypass também funcione
        self.module_manager.get_module = Mock(return_value=self.sistema_module)
        
        # Configurar o mock da memória vetorial para retornar uma string vazia
        self.core_context['vector_memory'].retrieve_relevant.return_value = ""


    def test_tool_call_simple_no_params(self):
        """
        Cenário 1: IA decide chamar uma ferramenta sem parâmetros.
        Comando: "qual o status do sistema"
        Ação esperada: Executar Sistema.obter_status_sistema()
        """
        # Configura a resposta simulada da IA
        ai_decision = {
            "tool_name": "Sistema.obter_status_sistema",
            "parameters": {}
        }
        self.mock_brain.pensar.return_value = ai_decision

        # Simula a função real para não executar código de sistema e para espionar a chamada
        with patch.object(self.sistema_module, 'obter_status_sistema', return_value="CPU 50%, RAM 60%") as mock_method:
            # Executa o comando
            response = self.module_manager.route_command("qual o status do sistema")

            # Verificações
            self.mock_brain.pensar.assert_called_once() # Garante que a IA foi consultada
            mock_method.assert_called_once() # Garante que o método correto foi chamado
            self.assertEqual(response, "CPU 50%, RAM 60%") # Garante que a resposta final é o resultado do método

    def test_tool_call_with_params(self):
        """
        Cenário 2: IA decide chamar uma ferramenta com parâmetros.
        Comando: "instale o pacote numpy"
        Ação esperada: Executar Sistema.instalar_pacote(nome_pacote="numpy")
        """
        ai_decision = {
            "tool_name": "Sistema.instalar_pacote",
            "parameters": {"nome_pacote": "numpy"}
        }
        self.mock_brain.pensar.return_value = ai_decision

        with patch.object(self.sistema_module, 'instalar_pacote', return_value="Instalando numpy...") as mock_method:
            response = self.module_manager.route_command("instale o pacote numpy")

            self.mock_brain.pensar.assert_called_once()
            mock_method.assert_called_once_with(nome_pacote="numpy") # Verifica se foi chamado com o argumento correto
            self.assertEqual(response, "Instalando numpy...")

    def test_conversational_fallback_from_json(self):
        """
        Cenário 3: IA não encontra uma ferramenta e responde com um JSON de fallback.
        """
        ai_decision = {
            "fallback": "Não tenho uma ferramenta para criar um buraco negro, desculpe."
        }
        self.mock_brain.pensar.return_value = ai_decision
        
        response = self.module_manager.route_command("crie um buraco negro no meu quintal")

        self.mock_brain.pensar.assert_called_once()
        self.assertEqual(response, "Não tenho uma ferramenta para criar um buraco negro, desculpe.")

    def test_conversational_fallback_from_string(self):
        """
        Cenário 4: IA (ou um modelo local) responde com uma string simples.
        """
        self.mock_brain.pensar.return_value = "Isso é apenas uma resposta de conversa."

        response = self.module_manager.route_command("quem foi platão?")

        self.mock_brain.pensar.assert_called_once()
        self.assertEqual(response, "Isso é apenas uma resposta de conversa.")

    def test_tool_not_found(self):
        """
        Cenário 5: IA tenta chamar uma ferramenta que não existe.
        """
        ai_decision = {
            "tool_name": "Sistema.fazer_cafe",
            "parameters": {}
        }
        self.mock_brain.pensar.return_value = ai_decision

        response = self.module_manager.route_command("faça um café para mim")
        
        self.mock_brain.pensar.assert_called_once()
        self.assertIn("ferramenta inexistente", response)

if __name__ == "__main__":
    unittest.main()
