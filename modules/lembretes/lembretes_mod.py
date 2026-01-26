from modules.base_module import AeonModule
from typing import List, Dict
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
        """Lembretes depende de config_manager para persistência e io_handler para falar."""
        return ["config_manager", "io_handler"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.1.0",
            "author": "Aeon Core",
            "description": "Gerencia lembretes e dispara alertas quando os prazos são atingidos."
        }

    def on_load(self) -> bool:
        """Inicializa o módulo, valida dependências e inicia a thread do despertador."""
        if not self.core_context.get("config_manager") or not self.core_context.get("io_handler"):
            print("[LembreteModule] Erro: Dependências (config_manager, io_handler) não encontradas.")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._reminder_checker_loop, daemon=True)
        self.thread.start()
        print("[LembreteModule] Despertador de lembretes iniciado.")
        return True

    def on_unload(self) -> bool:
        """Para a thread do despertador de forma limpa."""
        self.is_running = False
        if self.thread:
            print("[LembreteModule] Aguardando o despertador finalizar...")
            self.thread.join(timeout=5) # Espera no máximo 5s
        print("[LembreteModule] Despertador de lembretes parado.")
        return True

    def _reminder_checker_loop(self):
        """Loop que verifica periodicamente se algum lembrete está vencido."""
        config_manager = self.core_context.get("config_manager")
        io_handler = self.core_context.get("io_handler")

        while self.is_running:
            try:
                now_utc = datetime.now(timezone.utc)
                tasks = config_manager.get_tasks()
                tasks_changed = False

                for task in tasks:
                    if not task.get('done'):
                        deadline_str = task.get('deadline')
                        if not deadline_str: continue

                        # Converte a string ISO de volta para um objeto datetime ciente do fuso horário
                        deadline = datetime.fromisoformat(deadline_str)

                        if now_utc >= deadline:
                            print(f"[LembreteModule] Lembrete vencido: {task['text']}")
                            io_handler.falar(f"Lembrete: {task['text']}")
                            task['done'] = True
                            tasks_changed = True
                            # Pequena pausa para não falar vários lembretes de uma vez só
                            time.sleep(2)

                if tasks_changed:
                    config_manager.save_tasks()

            except Exception as e:
                print(f"[LembreteModule] Erro no loop do despertador: {e}")

            # Espera 60 segundos para a próxima verificação
            for _ in range(60):
                if not self.is_running:
                    break
                time.sleep(1)

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

        try:
            texto_principal = ""
            raw_date_str = ""
            
            if " para " in command:
                parts = command.split(" para ")
                texto_principal = parts[0].replace("lembrete de", "").replace("me lembre de", "").replace("tarefa de", "").strip()
                raw_date_str = parts[1].split(" com prioridade")[0].strip()
            else:
                 raise ValueError("Não entendi o prazo. Use 'para', como em '... para amanhã às 10h'.")

            # Força o dateparser a usar o fuso horário local e retornar um objeto ciente do fuso
            deadline_local = dateparser.parse(raw_date_str, languages=['pt'], settings={'TIMEZONE': 'local', 'RETURN_AS_TIMEZONE_AWARE': True})
            
            if not texto_principal or not deadline_local:
                raise ValueError("Não consegui entender o lembrete ou o prazo.")

            # Converte para UTC para armazenamento, garantindo consistência
            deadline_utc = deadline_local.astimezone(timezone.utc)
            deadline_str = deadline_utc.isoformat()

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
            
            return f"Lembrete '{texto_principal}' definido para {deadline_local.strftime('%d/%m/%Y às %H:%M')}."
            
        except Exception as e:
            return f"Não consegui criar o lembrete. Erro: {e}"

    def listar_lembretes(self, config_manager) -> str:
        tasks = config_manager.get_tasks()
        active_tasks = [t for t in tasks if not t.get('done')]
        if not active_tasks:
            return "Você não tem lembretes ou tarefas pendentes."

        response = "Suas tarefas pendentes são:\n"
        sorted_tasks = sorted(active_tasks, key=lambda x: (-x.get('priority', 0), x['deadline']))
        
        now_local = datetime.now().astimezone() # Pega o datetime local ciente do fuso

        for task in sorted_tasks:
            deadline_utc = datetime.fromisoformat(task['deadline'])
            deadline_local = deadline_utc.astimezone(now_local.tzinfo) # Converte para o fuso local
            response += f"- {task['text']} para {deadline_local.strftime('%d/%m %H:%M')} (Prioridade: {task.get('priority', 'Normal')})\n"
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
