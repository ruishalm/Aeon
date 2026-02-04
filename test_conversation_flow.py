#!/usr/bin/env python
"""Teste do novo fluxo: conversa vs comando."""

from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager
import sys

print("\n" + "="*70)
print("TESTE: CONVERSA NATURAL vs COMANDO")
print("="*70)

# Setup
config = ConfigManager()
io = IOHandler(config.system_data)
brain = AeonBrain(config)

context = {
    "config_manager": config,
    "io_handler": io,
    "brain": brain,
    "gui": None
}

mods = ModuleManager(context)
context["module_manager"] = mods
mods.load_modules()

print(f"\nModulos carregados: {len(mods.get_loaded_modules())}\n")

# Função para testar
def test_input(user_input):
    print(f"\n[VOCÊ] {user_input}")
    print("-" * 70)
    
    # Roteia comando
    module_response = mods.route_command(user_input)
    
    # Se retornou algo, é um módulo
    if module_response is not None:
        print(f"[MODULO] {module_response}")
    # Se retornou None, não tem trigger
    else:
        print("[LOG] Nenhum trigger encontrado. Chamando Brain para conversa...")
        conv_response = brain.pensar(user_input, modo="conversa")
        if conv_response:
            print(f"[AEON] {conv_response}")
        else:
            print("[ERRO] Brain não conseguiu processar.")

# Testes
print("\n" + "="*70)
print("TESTE 1: CONVERSA SIMPLES")
print("="*70)
test_input("oi aeon")

print("\n" + "="*70)
print("TESTE 2: PERGUNTA SOBRE HORA")
print("="*70)
test_input("que horas são?")

print("\n" + "="*70)
print("TESTE 3: COMANDO (TRIGGA NO MÓDULO)")
print("="*70)
test_input("listar modulos")

print("\n" + "="*70)
print("TESTE 4: COMANDO MIDIA")
print("="*70)
test_input("toca uma música")

print("\n" + "="*70)
print("TESTE 5: CONVERSA GENÉRICA")
print("="*70)
test_input("como você tá?")

print("\n" + "="*70)
print("TESTE 6: AGRADECIMENTO")
print("="*70)
test_input("obrigado aeon")

print("\n" + "="*70)
print("TESTES CONCLUIDOS")
print("="*70 + "\n")
