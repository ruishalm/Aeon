#!/usr/bin/env python
"""Script interativo para testar comandos do Aeon sem interface gráfica."""

import sys
import time
from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager

print("[TEST] Iniciando teste interativo do Aeon...")
print("[TEST] Você pode digitar comandos e ver as respostas em tempo real.\n")

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

print(f"[TEST] Módulos carregados: {len(mods.get_loaded_modules())}")
print("[TEST] Digite 'sair' para encerrar, 'ajuda' para comandos de teste.\n")

# Loop interativo
exit_confirmed = False
while True:
    try:
        cmd = input("[VOCÊ] ").strip()
        
        if not cmd:
            continue
        
        if cmd.lower() == "ajuda":
            print("\n[AJUDA] Comandos de teste:")
            print("  - 'listar modulos' - Lista módulos disponíveis")
            print("  - 'status do sistema' - Status do sistema")
            print("  - 'qualquer coisa' - Processa como comando normal")
            print("  - 'sair' - Encerra (pedirá confirmação)")
            print("  - 'sim' - Confirma saída")
            print()
            continue
        
        # Processa comando
        response = mods.route_command(cmd)
        
        print(f"[AEON] {response}\n")
        
        # Se for confirmação de saída e usuario confirmar, sai
        if cmd.lower() in ["sim", "confirmo", "confirmar"]:
            print("[TEST] Sistema encerrando...")
            time.sleep(1)
            break
            
    except KeyboardInterrupt:
        print("\n[TEST] Interrompido pelo usuário.")
        break
    except SystemExit:
        print("[TEST] Sistema encerrado.")
        break
    except Exception as e:
        print(f"[ERRO] {e}\n")

print("[TEST] Teste concluído.")
