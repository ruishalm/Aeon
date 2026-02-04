#!/usr/bin/env python
"""Script para testar comandos do Aeon sem interface gráfica."""

import sys
from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager

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
mods.load_modules()

# Testes
test_commands = [
    "olá",
    "qual seu nome",
    "sair"
]

print("[TEST] Iniciando testes de comandos...")
for cmd in test_commands:
    print(f"\n[TEST] Comando: '{cmd}'")
    try:
        response = mods.route_command(cmd)
        print(f"[TEST] Resposta: {response}")
    except SystemExit:
        print("[TEST] Sistema encerrado (sair funcionou!)")
        break
    except Exception as e:
        print(f"[TEST] Erro: {e}")

print("\n[TEST] Testes concluídos.")
