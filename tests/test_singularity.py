import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Adiciona caminho ao projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.meta.singularity_mod import SingularityModule


class TestSingularityModule(unittest.TestCase):
    """Testes para o módulo Singularidade"""
    
    def setUp(self):
        """Prepara mocks para cada teste"""
        self.core_context = {
            "module_manager": Mock(),
            "brain": Mock()
        }
        self.singularity = SingularityModule(self.core_context)
    
    def test_initialization(self):
        """Testa inicialização do módulo"""
        self.assertEqual(self.singularity.name, "Singularidade")
        self.assertIn("iniciar singularidade", self.singularity.triggers)
        self.assertEqual(self.singularity.step, 0)
        self.assertIn("brain", self.singularity.dependencies)
    
    def test_metadata(self):
        """Testa metadados do módulo"""
        meta = self.singularity.metadata
        self.assertEqual(meta["version"], "1.0.0")
        self.assertEqual(meta["author"], "Aeon Auto-Evolution")
    
    def test_on_load(self):
        """Testa hook on_load"""
        result = self.singularity.on_load()
        self.assertTrue(result)
    
    def test_on_unload(self):
        """Testa hook on_unload"""
        result = self.singularity.on_unload()
        self.assertTrue(result)
    
    def test_step_0_initialization(self):
        """Testa Step 0: Inicialização com lock focus"""
        self.singularity.step = 0
        response = self.singularity.process("qualquer comando")
        
        # Verifica se lock_focus foi chamado
        self.core_context["module_manager"].lock_focus.assert_called_once()
        # Verifica se step avançou
        self.assertEqual(self.singularity.step, 1)
        # Verifica mensagem
        self.assertIn("Protocolo Singularidade", response)
    
    def test_step_1_valid_name(self):
        """Testa Step 1: Coleta de nome válido"""
        self.singularity.step = 1
        response = self.singularity.process("meu_modulo")
        
        self.assertEqual(self.singularity.temp_data["name"], "meu_modulo")
        self.assertEqual(self.singularity.step, 2)
        self.assertIn("gatilhos", response.lower())
    
    def test_step_1_invalid_name(self):
        """Testa Step 1: Nome inválido (apenas símbolos)"""
        self.singularity.step = 1
        response = self.singularity.process("!@#$%")
        
        # Deve rejeitar e pedir novamente (sem avançar step)
        self.assertEqual(self.singularity.step, 1)
        self.assertIn("inválido", response.lower())
    
    def test_step_2_triggers(self):
        """Testa Step 2: Coleta de triggers"""
        self.singularity.step = 2
        self.singularity.temp_data["name"] = "cotacao"
        
        response = self.singularity.process("preço dolar, cotação usd, valor euro")
        
        # Verifica se triggers foram armazenados como string de lista
        self.assertIn("preço dolar", self.singularity.temp_data["triggers"])
        self.assertEqual(self.singularity.step, 3)
        self.assertIn("lógica", response.lower())
    
    def test_validate_syntax_valid(self):
        """Testa validação de sintaxe com código válido"""
        valid_code = """
def hello():
    return "world"
"""
        error = self.singularity._validate_syntax(valid_code)
        self.assertIsNone(error)
    
    def test_validate_syntax_invalid(self):
        """Testa validação de sintaxe com código inválido"""
        invalid_code = """
def hello()
    return "world"
"""
        error = self.singularity._validate_syntax(invalid_code)
        self.assertIsNotNone(error)
    
    def test_extract_code_with_python_marker(self):
        """Testa extração de código com marcador python"""
        text = """
Aqui está o código:

```python
def test():
    return "ok"
```

Pronto!
"""
        code = self.singularity._extract_code(text)
        self.assertIsNotNone(code)
        self.assertIn("def test", code)
    
    def test_extract_code_without_python_marker(self):
        """Testa extração de código sem marcador python"""
        text = """
```
def test():
    return "ok"
```
"""
        code = self.singularity._extract_code(text)
        self.assertIsNotNone(code)
        self.assertIn("def test", code)
    
    def test_extract_code_not_found(self):
        """Testa extração quando não há código"""
        text = "Sem código aqui"
        code = self.singularity._extract_code(text)
        self.assertIsNone(code)
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_module_success(self, mock_open, mock_makedirs, mock_exists):
        """Testa salvamento do módulo em disco"""
        mock_exists.return_value = False
        
        self.singularity.temp_data["name"] = "novo_modulo"
        code = "print('hello')"
        
        result = self.singularity._save_module(code)
        
        # Verifica chamadas
        mock_makedirs.assert_called_once()
        self.assertTrue(result)
    
    def test_reset_state(self):
        """Testa resetagem do estado"""
        self.singularity.step = 3
        self.singularity.temp_data = {"name": "teste"}
        
        self.singularity._reset_state(self.core_context["module_manager"])
        
        self.assertEqual(self.singularity.step, 0)
        self.assertEqual(self.singularity.temp_data, {})
        self.core_context["module_manager"].release_focus.assert_called_once()
    
    def test_build_prompt_contains_specs(self):
        """Testa se o prompt contém as especificações"""
        self.singularity.temp_data = {
            "name": "teste",
            "triggers": "['teste1', 'teste2']",
            "logic": "fazer algo"
        }
        
        prompt = self.singularity._build_prompt()
        
        self.assertIn("teste", prompt)
        self.assertIn("fazer algo", prompt)
        self.assertIn("TEMPLATE", prompt)


class TestSingularityIntegration(unittest.TestCase):
    """Testes de integração do fluxo completo"""
    
    def setUp(self):
        """Prepara mocks mais completos"""
        self.core_context = {
            "module_manager": Mock(),
            "brain": Mock()
        }
        self.singularity = SingularityModule(self.core_context)
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    def test_full_creation_flow(self, mock_open, mock_makedirs, mock_exists):
        """Testa fluxo completo de criação"""
        mock_exists.return_value = False
        
        # Mock do brain
        valid_code = """```python
from modules.base_module import AeonModule
from typing import List, Dict

class TesteModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "teste"
        self.triggers = ["teste1"]
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    @property
    def metadata(self) -> Dict[str, str]:
        return {"version": "1.0.0", "author": "Aeon"}
    
    def on_load(self) -> bool:
        return True
    
    def on_unload(self) -> bool:
        return True
    
    def process(self, command: str) -> str:
        return "Ok"
```"""
        
        self.core_context["brain"].pensar.return_value = valid_code
        self.core_context["module_manager"].scan_new_modules.return_value = ["TesteModule"]
        
        # Step 0: Inicializar
        resp0 = self.singularity.process("start")
        self.assertEqual(self.singularity.step, 1)
        
        # Step 1: Nome
        resp1 = self.singularity.process("teste")
        self.assertEqual(self.singularity.step, 2)
        
        # Step 2: Triggers
        resp2 = self.singularity.process("teste1, teste2")
        self.assertEqual(self.singularity.step, 3)
        
        # Step 3: Lógica & Geração
        resp3 = self.singularity.process("fazer algo útil")
        
        # Verifica sucesso
        self.assertIn("Sucesso", resp3)
        self.assertEqual(self.singularity.step, 0)  # Reset


if __name__ == "__main__":
    unittest.main()
