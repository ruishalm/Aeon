from modules.base_module import AeonModule
from typing import List, Dict
import time
import threading
import datetime

class RotinasModule(AeonModule):
    """
    Módulo para criar, executar e listar rotinas (macros) de comandos,
    e também gerenciar alarmes/lembretes.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Rotinas"
        self.triggers = ["rotina", "rotinas", "alarme", "timer", "lembrete"]
        
        # O estado da gravação agora é interno ao módulo
        self.recording_routine_name = None
        self.recorded_commands = []
        
        # Alarmes e lembretes
        self.alarms = []

    @property
    def dependencies(self) -> List[str]:
        """Rotinas não tem dependências de módulos."""
        return []  # Usa core_context direto, não módulos

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Cria e executa rotinas de comandos, gerencia alarmes e lembretes"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - valida acesso a config_manager."""
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            print("[RotinasModule] Erro: config_manager não encontrado")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        self.recording_routine_name = None
        self.recorded_commands = []
        self.alarms = []
        return True

    def process(self, command: str) -> str:
        # Se estivermos no meio de uma gravação, qualquer comando é parte dela
        if self.recording_routine_name:
            if "parar de gravar" in command:
                return self.salvar_rotina()
            else:
                # Adiciona o comando original (não em minúsculas)
                self.recorded_commands.append(command)
                return f"Adicionado: '{command}'"

        # Comandos principais do módulo
        if command.startswith("criar rotina"):
            nome_rotina = command.split("criar rotina")[-1].strip()
            if nome_rotina:
                self.recording_routine_name = nome_rotina
                self.recorded_commands = []
                return f"Ok, gravando a rotina '{nome_rotina}'. Diga os comandos. Fale 'parar de gravar' quando terminar."
            else:
                return "Por favor, diga um nome para a rotina."

        elif command.startswith("executar rotina"):
            nome_rotina = command.split("executar rotina")[-1].strip()
            return self.executar_rotina(nome_rotina)

        elif command == "listar rotinas":
            config_manager = self.core_context.get("config_manager")
            routines = config_manager.get_system_data("routines", {})
            if routines:
                return f"Suas rotinas salvas são: {', '.join(routines.keys())}."
            else:
                return "Você ainda não tem nenhuma rotina salva."

        # --- Alarmes e Lembretes ---
        elif "alarme" in command or "timer" in command or "lembrete" in command:
            return self.processar_alarme(command)
        
        return "" # Nenhum comando do módulo foi acionado

    def salvar_rotina(self) -> str:
        """Salva a rotina gravada no arquivo de configuração."""
        config_manager = self.core_context.get("config_manager")
        if not config_manager:
            return "Erro: Gerenciador de configuração não encontrado."

        if self.recorded_commands:
            # Pega o dicionário de rotinas existente, ou cria um novo
            routines = config_manager.get_system_data("routines", {})
            routines[self.recording_routine_name] = self.recorded_commands
            config_manager.set_system_data("routines", routines)
            
            response = f"Rotina '{self.recording_routine_name}' salva com sucesso."
        else:
            response = "Nenhum comando foi gravado. Rotina cancelada."
            
        # Limpa o estado de gravação
        self.recording_routine_name = None
        self.recorded_commands = []
        return response

    def executar_rotina(self, nome_rotina: str) -> str:
        """Executa uma rotina salva em uma thread separada."""
        config_manager = self.core_context.get("config_manager")
        routines = config_manager.get_system_data("routines", {})
        
        if nome_rotina in routines:
            def run_routine():
                module_manager = self.core_context.get("module_manager")
                io_handler = self.core_context.get("io_handler")
                
                io_handler.falar(f"Executando a rotina '{nome_rotina}'.")
                
                for command in routines[nome_rotina]:
                    # Mostra o comando na GUI (simulado, pois não temos acesso direto)
                    print(f"Executando (Rotina): {command}")
                    # Roteia cada comando da rotina através do manager
                    response = module_manager.route_command(command)
                    if response:
                        io_handler.falar(response)
                    time.sleep(1.5) # Pausa entre os comandos
                
                io_handler.falar(f"Rotina '{nome_rotina}' finalizada.")

            threading.Thread(target=run_routine).start()
            return "" # A thread dará o feedback verbal
        else:
            return f"Não encontrei a rotina chamada '{nome_rotina}'."

    # --- Alarmes e Lembretes ---
    def processar_alarme(self, command: str) -> str:
        """Processa comandos de alarme/timer/lembrete."""
        import re
        
        # Mapear palavras para números
        nums = {
            "um": 1, "dois": 2, "tres": 3, "três": 3, "quatro": 4, "cinco": 5,
            "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
            "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
            "meia": 30, "meia hora": 1800
        }
        
        # Substitui palavras por números
        cmd_processed = command.lower()
        for word, num in nums.items():
            cmd_processed = cmd_processed.replace(word, str(num))
        
        # Procura por padrão: número + unidade de tempo
        match = re.search(r'(\d+)\s*(segundo|minuto|hora|seg|min|h)', cmd_processed)
        
        if match:
            quantidade = int(match.group(1))
            unidade = match.group(2)
            
            # Converter para segundos
            if "seg" in unidade:
                total_segundos = quantidade
            elif "min" in unidade:
                total_segundos = quantidade * 60
            elif "h" in unidade or "hora" in unidade:
                total_segundos = quantidade * 3600
            else:
                total_segundos = quantidade
            
            # Extrair mensagem personalizada (se houver)
            # Ex: "alarme em 5 minutos para chamar mario"
            msg = re.sub(r'\d+\s*(segundo|minuto|hora|seg|min|h)', '', cmd_processed).strip()
            msg = msg.replace("alarme", "").replace("timer", "").replace("lembrete", "").strip()
            msg = msg if msg else "Tempo esgotado"
            
            # Criar alarme
            alarm_time = datetime.datetime.now() + datetime.timedelta(seconds=total_segundos)
            self.alarms.append({
                "time": alarm_time,
                "message": msg,
                "active": True
            })
            
            # Iniciar thread de monitoramento
            threading.Thread(target=self._monitor_alarm, args=(alarm_time, msg), daemon=True).start()
            
            tempo_str = f"{quantidade} {'segundo' if quantidade == 1 else 'segundos'}"
            if "min" in unidade:
                tempo_str = f"{quantidade} {'minuto' if quantidade == 1 else 'minutos'}"
            elif "h" in unidade or "hora" in unidade:
                tempo_str = f"{quantidade} {'hora' if quantidade == 1 else 'horas'}"
            
            return f"Alarme definido para {tempo_str}. {msg}."
        
        return "Não entendi o tempo. Tente: 'alarme em 5 minutos'"

    def _monitor_alarm(self, alarm_time: datetime.datetime, message: str):
        """Monitora um alarme e dispara quando chega a hora."""
        io_handler = self.core_context.get("io_handler")
        
        while datetime.datetime.now() < alarm_time:
            time.sleep(1)
        
        # Alarme disparado
        if io_handler:
            io_handler.falar(f"Atenção! {message}")

