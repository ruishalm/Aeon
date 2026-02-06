# Smoke test runner for Aeon modules
import time
from core.config_manager import ConfigManager
from core.io_handler import IOHandler
from core.brain import AeonBrain
from core.module_manager import ModuleManager

class DummyGUI:
    def add_message(self, text, who="SISTEMA"): print(f"[GUI] {who}: {text}")
    def set_status(self, s): print(f"[GUI] STATUS: {s}")
    def logic_callback(self, text): print(f"[GUI CALLBACK] {text}")


def run():
    print("Starting smoke tests...")
    config = ConfigManager()
    io = IOHandler(config.system_data)
    brain = AeonBrain(config)
    gui = DummyGUI()
    context = {"config_manager": config, "io_handler": io, "brain": brain, "gui": gui, "context": {}}
    mm = ModuleManager(context)
    mm.load_modules()
    print(f"Modules loaded: {len(mm.get_loaded_modules())}")

    results = []
    for mod in mm.get_loaded_modules():
        name = mod.name
        print('\n' + '='*60)
        print(f"Module: {name}")
        print(f"  Triggers: {getattr(mod, 'triggers', [])}")
        print(f"  Dependencies OK: {mod.check_dependencies()}")
        # Try process with first up to 2 triggers
        triggers = getattr(mod, 'triggers', [])[:2]
        for t in triggers:
            cmd = t if isinstance(t, str) else str(t)
            try:
                resp = mod.process(cmd)
            except Exception as e:
                resp = f"EXCEPTION: {e}"
            print(f"  process('{cmd}') -> {resp}")
        # If module exposes tools, try first tool
        try:
            tools = mod.get_tools()
        except Exception:
            tools = []
        if tools:
            first = tools[0]
            func = first.get('function', {}).get('name')
            print(f"  Exposed tool: {func}")
            try:
                res = mm.executar_ferramenta(func, {})
            except Exception as e:
                res = f"EXCEPTION_TOOL: {e}"
            print(f"  executar_ferramenta('{func}') -> {res}")
        results.append(name)

    print('\nSmoke tests completed for modules:')
    print(results)

if __name__ == '__main__':
    run()
