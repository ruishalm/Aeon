# Quick routing test
import sys
sys.path.insert(0, '.')
from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager

config = ConfigManager()
io = IOHandler(config.system_data)
brain = AeonBrain(config)
ctx = {"config_manager": config, "io_handler": io, "brain": brain, "context": {}}
mm = ModuleManager(ctx)
mm.load_modules()

phrases = [
    "Abra a calculadora",
    "Abra calculadora",
    "abre a calculadora",
    "tarô",
    "tarot",
    "entra no módulo do tarot",
    "ler as cartas",
]

for p in phrases:
    print("---")
    print("Input:", p)
    resp = mm.route_command(p)
    print("Route response:", resp)
