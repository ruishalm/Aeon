import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

# Adiciona caminho ao projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.module_manager import ModuleManager


class TestChatMemory(unittest.TestCase):
    """Testes para o sistema de Memória de Conversa (Efeito Dory Fix)"""
    
    def setUp(self):
        """Prepara mocks para cada teste"""
        self.core_context = {
            "brain": Mock(),
            "module_manager": None
        }
        self.mm = ModuleManager(self.core_context)
    
    def test_chat_history_initialization(self):
        """Testa inicialização do histórico de conversa"""
        self.assertEqual(self.mm.chat_history, [])
        self.assertEqual(self.mm.max_history, 10)
    
    def test_format_empty_history(self):
        """Testa formatação de histórico vazio"""
        formatted = self.mm._format_history()
        self.assertEqual(formatted, "")
    
    def test_format_history_with_messages(self):
        """Testa formatação de histórico com mensagens"""
        self.mm.chat_history = [
            {"role": "user", "content": "Olá"},
            {"role": "assistant", "content": "Olá, mestre!"},
            {"role": "user", "content": "Como você está?"},
            {"role": "assistant", "content": "Estou bem!"}
        ]
        
        formatted = self.mm._format_history()
        
        self.assertIn("Usuário: Olá", formatted)
        self.assertIn("Aeon: Olá, mestre!", formatted)
        self.assertIn("Usuário: Como você está?", formatted)
        self.assertIn("Aeon: Estou bem!", formatted)
    
    def test_route_command_saves_to_memory(self):
        """Testa que route_command salva conversa na memória"""
        # Mock do brain
        self.core_context["brain"] = Mock()
        self.core_context["brain"].pensar.return_value = "Resposta do Aeon"
        self.mm.core_context = self.core_context
        
        # Nenhum módulo carregado, vai usar brain fallback
        self.mm.modules = []
        self.mm.trigger_map = {}
        
        # Primeira mensagem
        response1 = self.mm.route_command("Olá Aeon")
        
        # Verifica se histórico foi populado
        self.assertEqual(len(self.mm.chat_history), 2)  # user + assistant
        self.assertEqual(self.mm.chat_history[0]["role"], "user")
        self.assertEqual(self.mm.chat_history[0]["content"], "Olá Aeon")
        self.assertEqual(self.mm.chat_history[1]["role"], "assistant")
        self.assertEqual(self.mm.chat_history[1]["content"], "Resposta do Aeon")
    
    def test_history_passed_to_brain(self):
        """Testa que o histórico é passado para o Brain"""
        # Mock do brain
        self.core_context["brain"] = Mock()
        self.core_context["brain"].pensar.return_value = "Segunda resposta"
        self.mm.core_context = self.core_context
        
        self.mm.modules = []
        self.mm.trigger_map = {}
        
        # Primeira mensagem
        self.mm.route_command("Primeira pergunta")
        
        # Verifica que brain foi chamado com historico_txt vazio (primeira vez)
        call_args_1 = self.core_context["brain"].pensar.call_args
        self.assertEqual(call_args_1.kwargs["historico_txt"], "")
        
        # Segunda mensagem
        self.core_context["brain"].pensar.reset_mock()
        self.mm.route_command("Segunda pergunta")
        
        # Verifica que brain foi chamado com histórico preenchido
        call_args_2 = self.core_context["brain"].pensar.call_args
        historico = call_args_2.kwargs["historico_txt"]
        
        # O histórico deve conter a primeira conversa
        self.assertIn("Usuário: Primeira pergunta", historico)
        self.assertIn("Aeon: Segunda resposta", historico)
        self.assertIn("Segunda pergunta", call_args_2.kwargs["prompt"])
    
    def test_memory_fifo_cleanup(self):
        """Testa limpeza FIFO quando histórico excede max_history"""
        self.core_context["brain"] = Mock()
        self.core_context["brain"].pensar.return_value = "Resposta"
        self.mm.core_context = self.core_context
        self.mm.modules = []
        self.mm.trigger_map = {}
        
        # Adiciona 11 conversas (max_history = 10)
        for i in range(11):
            self.mm.route_command(f"Mensagem {i}")
        
        # Histórico deve ter máximo 20 entradas (10 trocas * 2)
        self.assertLessEqual(len(self.mm.chat_history), self.mm.max_history * 2)
        
        # As primeiras mensagens devem ter sido removidas
        # Se adicionou 11 trocas, deve ter apenas as últimas 10
        contents = [msg["content"] for msg in self.mm.chat_history]
        
        # A primeira mensagem "Mensagem 0" não deveria estar
        self.assertNotIn("Mensagem 0", contents)
        # As últimas mensagens devem estar
        self.assertIn("Resposta", contents)
    
    def test_efeito_dory_fix(self):
        """
        Teste completo: simula o Efeito Dory e verifica a correção.
        
        Antes (BUG): 
        - Usuário: "Meu nome é João"
        - Usuário: "Qual é meu nome?"
        - Aeon: "Não sei" (porque historico_txt="")
        
        Depois (CORRIGIDO):
        - Brain recebe histórico com "Meu nome é João"
        - Aeon: "Seu nome é João"
        """
        self.core_context["brain"] = Mock()
        self.mm.core_context = self.core_context
        self.mm.modules = []
        self.mm.trigger_map = {}
        
        # Mock que simula um Brain inteligente
        def brain_response(prompt, historico_txt, user_prefs):
            if "qual é meu nome" in prompt.lower():
                if "joão" in historico_txt.lower():
                    return "Seu nome é João"
                else:
                    return "Não sei seu nome"
            return f"Resposta para: {prompt}"
        
        self.core_context["brain"].pensar.side_effect = brain_response
        
        # 1. Usuário diz seu nome
        resp1 = self.mm.route_command("Meu nome é João")
        
        # 2. Usuário pergunta seu nome
        resp2 = self.mm.route_command("Qual é meu nome?")
        
        # 3. Verificar que Aeon lembrou
        self.assertIn("João", resp2)
        self.assertNotIn("Não sei", resp2)


class TestChatMemoryIntegration(unittest.TestCase):
    """Testes de integração com o fluxo completo"""
    
    def setUp(self):
        self.core_context = {"brain": Mock()}
        self.mm = ModuleManager(self.core_context)
    
    def test_conversation_flow(self):
        """Testa um fluxo completo de conversa"""
        responses = [
            "Olá! Meu nome é Aeon.",
            "Fico feliz em conversar.",
            "Suas informações foram salvas."
        ]
        
        self.core_context["brain"].pensar.side_effect = responses
        self.mm.core_context = self.core_context
        self.mm.modules = []
        self.mm.trigger_map = {}
        
        # Conversa
        r1 = self.mm.route_command("Olá")
        r2 = self.mm.route_command("Como você está?")
        r3 = self.mm.route_command("Salve minhas preferências")
        
        # Verifica histórico
        self.assertEqual(len(self.mm.chat_history), 6)  # 3 perguntas + 3 respostas
        
        # Verifica conteúdo
        history_text = " ".join([msg["content"] for msg in self.mm.chat_history])
        self.assertIn("Olá", history_text)
        self.assertIn("Como você está?", history_text)
        self.assertIn("Salve minhas preferências", history_text)


if __name__ == "__main__":
    unittest.main()
