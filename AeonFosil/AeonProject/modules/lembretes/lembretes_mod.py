from modules.base_module import AeonModule
from typing import List, Dict
import dateparser
import datetime
import re

class LembreteModule(AeonModule):
    """
    Módulo para gerenciar lembretes e tarefas.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Lembretes"
        self.triggers = ["lembrete", "tarefa", "lembretes", "tarefas"]

    @property
    def dependencies(self) -> List[str]:
        """Lembretes depende de config_manager para persistência."""
        return ["config_manager"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Gerencia lembretes e tarefas com prazos e prioridades"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - valida acesso a config_manager."""
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            print("[LembreteModule] Erro: config_manager não encontrado")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            return "Erro: Gerenciador de configuração não encontrado."

        if "listar" in command or "quais são" in command:
            return self.listar_lembretes(config_manager)
        
        if "concluído" in command or "concluída" in command:
            task_text = re.split(r'concluído|concluída', command)[-1].strip()
            task_text = task_text.replace("marcar", "").replace("lembrete", "").replace("tarefa", "").strip()
            return self.marcar_como_concluido(config_manager, task_text)

        # Se não for listar nem concluir, assume que é para criar
        try:
            texto_principal = ""
            raw_date_str = ""
            
            if " para " in command:
                parts = command.split(" para ")
                texto_principal = parts[0].replace("lembrete de", "").replace("me lembre de", "").replace("tarefa de", "").strip()
                raw_date_str = parts[1].split(" com prioridade")[0].strip()
            else:
                 raise ValueError("Não entendi o prazo. Use 'para', como em '... para amanhã às 10h'.")

            deadline = dateparser.parse(raw_date_str, languages=['pt'])
            
            if not texto_principal or not deadline:
                raise ValueError("Não consegui entender o lembrete ou o prazo.")

            deadline_str = deadline.isoformat()

            prioridade = 0 # Normal
            if "prioridade alta" in command: prioridade = 1
            if "prioridade baixa" in command: prioridade = -1
            
            task_data = {
                "id": len(config_manager.get_tasks()) + 1,
                "text": texto_principal,
                "deadline": deadline_str,
                "priority": prioridade,
                "done": False
            }
            config_manager.add_task(task_data)
            
            return f"Lembrete '{texto_principal}' definido para {deadline.strftime('%d/%m/%Y %H:%M')}."
            
        except Exception as e:
            return f"Não consegui criar o lembrete. {e}"

    def listar_lembretes(self, config_manager) -> str:
        tasks = config_manager.get_tasks()
        active_tasks = [t for t in tasks if not t.get('done')]
        if not active_tasks:
            return "Você não tem lembretes ou tarefas pendentes."

        response = "Suas tarefas pendentes são:\n"
        sorted_tasks = sorted(active_tasks, key=lambda x: (-x.get('priority', 0), x['deadline']))
        
        for task in sorted_tasks:
            deadline = datetime.datetime.fromisoformat(task['deadline'])
            response += f"- {task['text']} para {deadline.strftime('%d/%m %H:%M')} (Prioridade: {task.get('priority', 'Normal')})\n"
        return response

    def marcar_como_concluido(self, config_manager, task_text: str) -> str:
        tasks = config_manager.get_tasks()
        found = False
        for task in tasks:
            if not task.get('done') and task_text.lower() in task['text'].lower():
                task['done'] = True
                found = True
                break
        
        if found:
            config_manager.save_tasks()
            return f"Tarefa '{task_text}' marcada como concluída."
        return f"Não encontrei a tarefa pendente '{task_text}'."
