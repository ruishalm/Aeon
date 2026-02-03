from modules.base_module import AeonModule
from typing import List, Dict, Any
import dateparser
from datetime import datetime, timezone
import re
import threading
import time

class LembreteModule(AeonModule):
    """
    Módulo para gerenciar lembretes e tarefas com um loop de verificação ativo.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Lembretes"
        self.triggers = ["lembrete", "tarefa", "lembretes", "tarefas"]
        self.thread = None
        self.is_running = False

    @property
    def dependencies(self) -> List[str]:
        return ["config_manager", "io_handler"]

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "version": "3.0.0",
            "author": "Aeon Core",
            "description": "Gerencia lembretes e tarefas via IA e dispara alertas."
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Lembretes.criar_lembrete",
                    "description": "Cria um novo lembrete ou tarefa com um prazo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "O conteúdo do lembrete. Ex: 'ligar para o cliente'"},
                            "prazo": {"type": "string", "description": "A data e/ou hora do lembrete. Ex: 'amanhã às 15h', 'daqui a 30 minutos'"},
                            "prioridade": {"type": "string", "enum": ["alta", "normal", "baixa"], "description": "A prioridade da tarefa."}
                        },
                        "required": ["texto", "prazo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Lembretes.listar_lembretes",
                    "description": "Lista todas as tarefas ou lembretes pendentes.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Lembretes.marcar_como_concluido",
                    "description": "Marca uma tarefa ou lembrete como concluído com base no seu texto.",
                    "parameters": {
                        "type": "object",
                        "properties": { "texto_tarefa": {"type": "string", "description": "Parte do texto da tarefa a ser marcada como concluída."}},
                        "required": ["texto_tarefa"]
                    }
                }
            }
        ]

    def on_load(self) -> bool:
        if not self.core_context.get("config_manager") or not self.core_context.get("io_handler"):
            return False
        self.is_running = True
        self.thread = threading.Thread(target=self._reminder_checker_loop, daemon=True)
        self.thread.start()
        print("[LembreteModule] Despertador de lembretes iniciado.")
        return True

    def on_unload(self) -> bool:
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[LembreteModule] Despertador de lembretes parado.")
        return True

    def _reminder_checker_loop(self):
        config_manager = self.core_context.get("config_manager")
        io_handler = self.core_context.get("io_handler")
        while self.is_running:
            try:
                now_utc = datetime.now(timezone.utc)
                tasks = config_manager.get_tasks()
                tasks_changed = False
                for task in tasks:
                    if not task.get('done'):
                        deadline = datetime.fromisoformat(task.get('deadline', ''))
                        if now_utc >= deadline:
                            io_handler.falar(f"Lembrete: {task['text']}")
                            task['done'] = True
                            tasks_changed = True
                            time.sleep(2)
                if tasks_changed:
                    config_manager.save_tasks()
            except Exception as e:
                print(f"[LembreteModule] Erro no loop do despertador: {e}")
            for _ in range(60):
                if not self.is_running: break
                time.sleep(1)

    def process(self, command: str) -> str:
        # O método process agora é apenas um fallback para o trigger "listar"
        if "listar" in command or "quais são" in command:
            return self.listar_lembretes()
        return ""

    # --- FERRAMENTAS PARA A IA ---
    
    def criar_lembrete(self, texto: str, prazo: str, prioridade: str = "normal") -> str:
        config_manager = self.core_context.get("config_manager")
        try:
            deadline_local = dateparser.parse(prazo, languages=['pt'], settings={'TIMEZONE': 'local', 'RETURN_AS_TIMEZONE_AWARE': True})
            if not texto or not deadline_local:
                raise ValueError("Texto ou prazo inválidos.")

            deadline_utc = deadline_local.astimezone(timezone.utc)
            
            p_map = {"alta": 1, "normal": 0, "baixa": -1}
            
            task_data = {
                "id": len(config_manager.get_tasks()) + 1,
                "text": texto,
                "deadline": deadline_utc.isoformat(),
                "priority": p_map.get(prioridade, 0),
                "done": False
            }
            config_manager.add_task(task_data)
            return f"Lembrete '{texto}' definido para {deadline_local.strftime('%d/%m/%Y às %H:%M')}."
        except Exception as e:
            return f"Não consegui criar o lembrete. Erro: {e}"

    def listar_lembretes(self) -> str:
        config_manager = self.core_context.get("config_manager")
        tasks = config_manager.get_tasks()
        active_tasks = [t for t in tasks if not t.get('done')]
        if not active_tasks:
            return "Você não tem lembretes pendentes."

        response = "Suas tarefas pendentes são:\n"
        sorted_tasks = sorted(active_tasks, key=lambda x: (-x.get('priority', 0), x['deadline']))
        now_local = datetime.now().astimezone()

        for task in sorted_tasks:
            deadline_utc = datetime.fromisoformat(task['deadline'])
            deadline_local = deadline_utc.astimezone(now_local.tzinfo)
            response += f"- {task['text']} para {deadline_local.strftime('%d/%m %H:%M')} (Prioridade: {task.get('priority', 'Normal')})\n"
        return response

    def marcar_como_concluido(self, texto_tarefa: str) -> str:
        config_manager = self.core_context.get("config_manager")
        tasks = config_manager.get_tasks()
        found = False
        for task in tasks:
            if not task.get('done') and texto_tarefa.lower() in task['text'].lower():
                task['done'] = True
                found = True
                break
        
        if found:
            config_manager.save_tasks()
            return f"Tarefa '{texto_tarefa}' marcada como concluída."
        return f"Não encontrei a tarefa pendente '{texto_tarefa}'."
