#!/usr/bin/env python
"""Teste rápido dos novos comandos: sair com confirmacao e listar modulos."""

from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager
import sys

print("\n" + "="*60)
print("TESTE INTERATIVO DO AEON")
print("="*60)

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
context["module_manager"] = mods  # Add module_manager to context
mods.load_modules()

print(f"\nModulos carregados: {len(mods.get_loaded_modules())}\n")

# Testes
print("[TESTE 1] Listar modulos")
print("-" * 60)
resp = mods.route_command("listar modulos")
print(f"RESPOSTA:\n{resp}\n")

print("\n[TESTE 2] Tentar sair (sem confirmar)")
print("-" * 60)
resp = mods.route_command("sair")
print(f"RESPOSTA: {resp}\n")

print("\n[TESTE 3] Negar saida")
print("-" * 60)
resp = mods.route_command("nao, voltar")
print(f"RESPOSTA: {resp}\n")

print("\n[TESTE 4] Tentar sair novamente")
print("-" * 60)
resp = mods.route_command("sair")
print(f"RESPOSTA: {resp}\n")

print("\n[TESTE 5] Confirmar saida com 'SIM'")
print("-" * 60)
resp = mods.route_command("sim")
print(f"RESPOSTA: {resp}\n")

# Aguardar um pouco para ver mensagem
import time
time.sleep(2)
print("\n[TESTE] Concluido. Sistema encerraria aqui.\n")
