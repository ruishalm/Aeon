from modules.base_module import AeonModule
from typing import List, Dict, Any
import dateparser
from datetime import datetime, timezone
import re
import threading
import time

class LembreteModule(AeonModule):
    """
    Modulo para gerenciar lembretes e tarefas com um loop de verificacao ativo.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Lembretes"
        # Adiciona sinônimos comuns como 'alarme', 'timer', 'temporizador'
        self.triggers = [
            "lembrete", "tarefa", "lembretes", "tarefas", "alarme", "timer", "temporizador", "lembre",
            "coloca um alarme", "define alarme", "define um alarme", "me lembra", "lembre-me", "lembra-me", "me lembr", "me lembrar"
        ]
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
                    "name": "Lembretes.set_timer",
                    "description": "Define um timer/alarme que vai despertar em X minutos ou segundos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duracao": {"type": "number", "description": "Duracao em segundos. Ex: 300 para 5 minutos"},
                            "descricao": {"type": "string", "description": "Descricao do timer. Ex: 'Lembrete de reuniao'"}
                        },
                        "required": ["duracao"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Lembretes.criar_lembrete",
                    "description": "Cria um novo lembrete ou tarefa com um prazo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "O conteudo do lembrete. Ex: 'ligar para o cliente'"},
                            "prazo": {"type": "string", "description": "A data e/ou hora do lembrete. Ex: 'amanha as 15h', 'daqui a 30 minutos'"},
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
                    "description": "Marca uma tarefa ou lembrete como concluido com base no seu texto.",
                    "parameters": {
                        "type": "object",
                        "properties": { "texto_tarefa": {"type": "string", "description": "Parte do texto da tarefa a ser marcada como concluida."}},
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
        # O metodo process agora e apenas um fallback para o trigger "listar"
        cmd = command.lower()
        if "listar" in cmd or "quais sao" in cmd:
            return self.listar_lembretes()

        # Suporta comandos naturais para timers/alarme: "coloca um timer em 30 segundos" / "coloca um timer daqui 10"
        if "timer" in cmd or "alarme" in cmd:
            try:
                # Extrai duracao em segundos
                # Formatos: 'em 30 segundos', 'daqui 10', 'daqui 10 minutos', 'em 1 minuto'
                m = re.search(r'(?:em|daqui)\s+(\d+)\s*(segundos|segundo|s|minutos|minuto|m)?', cmd)
                if m:
                    n = int(m.group(1))
                    unit = m.group(2) or 'segundos'
                    if 'min' in unit:
                        dur = n * 60
                    else:
                        dur = n
                    desc_match = re.search(r'(?:(?:timer|alarme)\s*(?:de|para)?\s*)(.*)', cmd)
                    descricao = None
                    if desc_match:
                        descricao = desc_match.group(1).strip()
                        # Remove pedaços como 'em 30 segundos' do final
                        descricao = re.sub(r'(?:em|daqui)\s+\d+.*$', '', descricao).strip()
                        if not descricao:
                            descricao = None
                    return self.set_timer(dur, descricao)
                else:
                    return "Diga a duracao do timer, por exemplo: 'coloca um timer em 30 segundos'."
            except Exception as e:
                return f"Nao consegui definir o timer: {e}"

        return ""

    # --- FERRAMENTAS PARA A IA ---
    
    def criar_lembrete(self, texto: str = None, prazo: str = None, prioridade: str = "normal") -> str:
        config_manager = self.core_context.get("config_manager")
        try:
            # Se o prazo não for fornecido, tenta extrair uma data/hora do próprio texto
            deadline_local = None
            if prazo:
                deadline_local = dateparser.parse(prazo, languages=['pt'], settings={'TIMEZONE': 'local', 'RETURN_AS_TIMEZONE_AWARE': True})

            if not prazo and texto:
                try:
                    from dateparser.search import search_dates
                    found = search_dates(texto, languages=['pt'])
                    if found:
                        # Usa a ultima ocorrencia encontrada
                        deadline_local = found[-1][1]
                except Exception:
                    pass

            if not texto or not deadline_local:
                raise ValueError("Texto ou prazo invalidos.")

            # Normaliza para UTC
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
            return f"Lembrete '{texto}' definido para {deadline_local.strftime('%d/%m/%Y as %H:%M')}."
        except Exception as e:
            return f"Nao consegui criar o lembrete. Erro: {e}"

    def listar_lembretes(self) -> str:
        config_manager = self.core_context.get("config_manager")
        tasks = config_manager.get_tasks()
        active_tasks = [t for t in tasks if not t.get('done')]
        if not active_tasks:
            return "Voce nao tem lembretes pendentes."

        response = "Suas tarefas pendentes sao:\n"
        sorted_tasks = sorted(active_tasks, key=lambda x: (-x.get('priority', 0), x['deadline']))
        now_local = datetime.now().astimezone()

        for task in sorted_tasks:
            deadline_utc = datetime.fromisoformat(task['deadline'])
            deadline_local = deadline_utc.astimezone(now_local.tzinfo)
            response += f"- {task['text']} para {deadline_local.strftime('%d/%m %H:%M')} (Prioridade: {task.get('priority', 'Normal')})\n"
        return response

    def set_timer(self, duracao: float, descricao: str = None) -> str:
        """Define um timer que dispara um alarme após X segundos."""
        try:
            if duracao <= 0:
                return "A duracao deve ser maior que zero."
            
            descricao = descricao or "Timer"
            
            def timer_thread():
                time.sleep(duracao)
                io_handler = self.core_context.get("io_handler")
                if io_handler:
                    io_handler.falar(f"{descricao}! Tempo esgotado!")
                    print(f"[TIMER] Alarme: {descricao}")
            
            t = threading.Thread(target=timer_thread, daemon=True)
            t.start()
            
            minutos = int(duracao // 60)
            segundos = int(duracao % 60)
            if minutos > 0:
                return f"Timer de {minutos} minuto{'s' if minutos > 1 else ''} e {segundos} segundo{'s' if segundos != 1 else ''} definido. {descricao}."
            else:
                return f"Timer de {segundos} segundo{'s' if segundos != 1 else ''} definido. {descricao}."
        except Exception as e:
            return f"Erro ao definir timer: {e}"

        for task in tasks:
            if not task.get('done') and texto_tarefa.lower() in task['text'].lower():
                task['done'] = True
                found = True
                break
        
        if found:
            config_manager.save_tasks()
            return f"Tarefa '{texto_tarefa}' marcada como concluida."
        return f"Nao encontrei a tarefa pendente '{texto_tarefa}'."
