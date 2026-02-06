#!/usr/bin/env python3
"""
test_modules_with_params.py
Tests all 14 modules with valid parameters for their tools.
This is a second-pass test to validate tool execution with real arguments.
"""

import sys
sys.path.insert(0, '.')

from core.module_manager import ModuleManager
from core.brain import AeonBrain
from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.context_manager import ContextManager

def setup_context():
    """Initialize the core context."""
    config = ConfigManager()
    io = IOHandler(config.system_data)
    brain = AeonBrain(config)
    
    core_context = {
        "config_manager": config,
        "io_handler": io,
        "brain": brain,
        "context": {}  # Enable Biblioteca/Web
    }
    return core_context

def test_module_tools_with_params():
    """Test each module's tools with valid parameters."""
    
    print("="*80)
    print("PARAMETRIZED MODULE TOOL TESTS")
    print("="*80)
    
    core_context = setup_context()
    mm = ModuleManager(core_context)
    mm.load_modules()
    
    # Define test cases: (module_name, tool_name, params_dict)
    test_cases = [
        ("Audicao", "Audicao.limpar_buffer", {}),
        ("Biblioteca", "Biblioteca.pesquisar_livros", {"query": "python"}),
        ("Controle", "Controle.diagnostico_modulos", {}),
        ("DevFactory", "DevFactory.processar_codigo", {}),
        ("Lembretes", "Lembretes.criar_lembrete", {"texto": "Lembrar de estudar", "prazo": "18:00"}),
        ("Singularidade", "Singularidade.processar_singularidade", {}),
        ("Midia", "Midia.play_pause", {}),
        ("Midia", "Midia.proxima_faixa", {}),
        ("Personalizacao", "Personalizacao.listar_vozes", {}),
        ("Rotinas", "Rotinas.iniciar_gravacao_rotina", {"nome_rotina": "teste"}),
        ("Sistema", "Sistema.obter_status_sistema", {}),
        ("Tarologo", "Tarologo.ler_cartas", {}),
        ("Visao", "Visao.inicializar_cortex_visual", {}),
        ("Web", "Web.pesquisa_web", {"query": "o que eh inteligencia artificial"}),
    ]
    
    print("\n[PARAMETRIZED TOOL EXECUTION]\n")
    
    results = []
    for module_name, tool_name, params in test_cases:
        print(f"Testing {tool_name} with params {params}...")
        
        try:
            module = mm.modules.get(module_name)
            if not module:
                print(f"  ❌ Module {module_name} not found")
                results.append((tool_name, "ERROR", f"Module not found"))
                continue
            
            # Execute the tool
            result = mm.executar_ferramenta(tool_name, params)
            
            # Report result
            status = "✅ OK" if result else "⚠️ EMPTY"
            preview = (result[:100] + "...") if len(str(result)) > 100 else result
            print(f"  {status}: {preview}\n")
            results.append((tool_name, status, preview))
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"  ❌ ERROR: {error_msg}\n")
            results.append((tool_name, "ERROR", error_msg))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal tests: {len(results)}")
    
    ok_count = len([r for r in results if "OK" in r[1]])
    error_count = len([r for r in results if "ERROR" in r[1]])
    
    print(f"✅ Passed: {ok_count}")
    print(f"❌ Failed: {error_count}")
    
    if error_count > 0:
        print("\nFailed tests:")
        for tool, status, msg in results:
            if "ERROR" in status:
                print(f"  - {tool}: {msg}")

if __name__ == "__main__":
    test_module_tools_with_params()
