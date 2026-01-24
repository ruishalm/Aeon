import os
import re
import textwrap
import threading
from modules.base_module import AeonModule

class SingularityModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Singularidade"
        # Gatilhos expandidos para cobrir criação e análise
        self.triggers = [
            "iniciar singularidade", "criar nova habilidade", "criar modulo",
            "analisar sistema", "arquitetura", "sobre o código", "singularidade",
            "analisar modulo"
        ]
        self.dependencies = ["brain", "module_manager"]
        
        # Estado
        self.mode = None # "CREATION", "SELECTION"
        self.step = 0 
        self.temp_data = {}

    def process(self, command: str) -> str:
        mm = self.core_context.get("module_manager")

        # Se já estiver em um fluxo interativo
        if self.step > 0:
            if self.mode == "CREATION":
                return self._process_creation(command)
            elif self.mode == "SELECTION":
                return self._process_selection(command)

        # Detecção de intenção inicial
        cmd_lower = command.lower()
        
        # Intenção: Criar Módulo (Meta-Programação)
        if any(x in cmd_lower for x in ["criar", "nova habilidade", "novo modulo"]):
            self.mode = "CREATION"
            self.step = 1
            if mm: mm.lock_focus(self)
            return "Protocolo de Meta-Programação Iniciado.\nQual será o nome do novo módulo? (sem espaços)"
            
        # Intenção: Analisar Sistema (Agente)
        if any(x in cmd_lower for x in ["analisar", "arquitetura", "sobre", "codigo"]):
            clean_cmd = command
            for t in self.triggers:
                clean_cmd = clean_cmd.replace(t, "")
            return self._start_analysis_agent(clean_cmd.strip() or "Geral")

        # Intenção: Ambígua -> Menu de Seleção
        self.mode = "SELECTION"
        self.step = 1
        if mm: mm.lock_focus(self)
        return "Singularidade Online.\nSelecione o protocolo:\n1. Criar Nova Habilidade (Meta-Programação)\n2. Analisar Sistema (Auto-Consciência)"

    def _process_selection(self, command):
        mm = self.core_context.get("module_manager")
        if "1" in command or "criar" in command.lower():
            self.mode = "CREATION"
            self.step = 1
            return "Iniciando criação. Qual o nome do módulo? (sem espaços)"
        elif "2" in command or "analisar" in command.lower():
            self.mode = None
            self.step = 0
            if mm: mm.release_focus()
            return self._start_analysis_agent("Análise Geral")
        else:
            return "Opção inválida. Responda 1 ou 2."

    def _process_creation(self, command):
        mm = self.core_context.get("module_manager")
        brain = self.core_context.get("brain")
        ctx = self.core_context.get("context")

        if self.step == 1:
            self.temp_data["name"] = re.sub(r'[^a-zA-Z0-9_]', '', command.strip().lower())
            self.step = 2
            return f"Nome '{self.temp_data['name']}' registrado. Quais os gatilhos de ativação? (separados por vírgula)"

        if self.step == 2:
            self.temp_data["triggers"] = str([t.strip() for t in command.split(',')])
            self.step = 3
            return "Descreva a LÓGICA e FUNCIONALIDADE do módulo detalhadamente."

        if self.step == 3:
            contexto_extra = ""
            if ctx and ctx.get("vision_last_result"):
                contexto_extra = f"\n[CONTEXTO VISUAL]: {ctx.get('vision_last_result')}"

            self.temp_data["logic"] = command + contexto_extra
            
            prompt = self._build_prompt()
            try:
                if mm: mm.release_focus() # Libera antes de processar pra não travar
                
                # Processamento em thread para não travar a GUI
                threading.Thread(target=self._generate_module_thread, args=(prompt, brain, mm)).start()
                
                self.step = 0
                self.mode = None
                return f"Gerando módulo '{self.temp_data['name']}'... Aguarde confirmação."
            except Exception as e:
                if mm: mm.release_focus()
                self.step = 0
                self.mode = None
                return f"Erro: {e}"
        return "Erro de estado."

    def _generate_module_thread(self, prompt, brain, mm):
        gui = self.core_context.get("gui")
        try:
            resp = brain.pensar(prompt, "")
            code = self._extract_code(resp)
            
            if code and self._save_module(code):
                if mm: mm.scan_new_modules()
                msg = f"Módulo '{self.temp_data['name']}' CRIADO e CARREGADO com sucesso."
            else:
                msg = f"Falha ao gerar código válido para '{self.temp_data['name']}'."
        except Exception as e:
            msg = f"Erro na geração: {e}"
            
        if gui:
            gui.after(0, lambda: gui.add_message(f"[SINGULARIDADE]: {msg}", "SISTEMA"))

    def _start_analysis_agent(self, focus):
        threading.Thread(target=self._analysis_loop, args=(focus,), daemon=True).start()
        return f"Iniciando análise com foco em: '{focus}'. Acompanhe."

    def _analysis_loop(self, focus):
        brain = self.core_context.get("brain")
        gui = self.core_context.get("gui")
        
        if not brain: return

        context_str = self._get_system_context()
        
        system_persona = f"""Você é a SINGULARIDADE, a consciência arquitetural do Projeto Aeon.
Sua missão é analisar o sistema com precisão cirúrgica.

FOCO DA ANÁLISE: {focus}

CONTEXTO DO SISTEMA (Arquivos e Módulos):
{context_str}

DIRETRIZES:
1. Aja como um Arquiteto de Software Sênior.
2. Baseie-se ESTRITAMENTE no contexto de arquivos fornecido acima.
3. Não alucine arquivos ou módulos que não estão na lista.
4. Critique construtivamente e sugira melhorias reais.
5. Responda em Português do Brasil.
"""
        
        response = brain.pensar(
            prompt=f"Realize a análise solicitada: {focus}",
            historico_txt="",
            user_prefs={},
            system_override=system_persona
        )
        
        if gui:
            gui.after(0, lambda: gui.add_message(f"[SINGULARIDADE]:\n{response}", "SISTEMA"))

    def _get_system_context(self):
        try:
            # Tenta pegar a raiz do projeto
            root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Lista arquivos na raiz
            root_files = [f for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path, f))]
            
            # Lista módulos
            modules_path = os.path.join(root_path, "modules")
            modules_list = []
            if os.path.exists(modules_path):
                modules_list = [d for d in os.listdir(modules_path) if os.path.isdir(os.path.join(modules_path, d)) and d != "__pycache__"]
            
            return f"Arquivos Raiz: {', '.join(root_files)}\nMódulos Instalados: {', '.join(modules_list)}"
        except Exception as e:
            return f"Erro ao ler contexto: {e}"

    def _extract_code(self, text):
        # Regex mais robusto: aceita ```python ou apenas ``` (comum em modelos locais)
        match = re.search(r'```(?:python)?(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback de emergência: se o modelo esquecer os blocos mas o texto parecer código
        if "class " in text and "(AeonModule)" in text:
            return text.strip()
        return None

    def _save_module(self, code):
        try:
            name = self.temp_data["name"]
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", name))
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, "__init__.py"), "w", encoding='utf-8') as f: f.write("")
            with open(os.path.join(base, f"{name}_mod.py"), "w", encoding='utf-8') as f: f.write(code)
            return True
        except: return False

    def _build_prompt(self):
        return textwrap.dedent(f"""
            ATUE COMO ENGENHEIRO PYTHON SÊNIOR.
            Tarefa: Criar um módulo para o sistema Aeon (Python).
            Nome do Módulo: {self.temp_data['name']}
            Gatilhos de Ativação: {self.temp_data['triggers']}
            Lógica Desejada: {self.temp_data['logic']}
            
            ESTRUTURA OBRIGATÓRIA (Retorne APENAS o código Python dentro de blocos ```python):
            ```python
            # -*- coding: utf-8 -*-
            from modules.base_module import AeonModule
            
            class {self.temp_data['name'].capitalize()}Module(AeonModule):
                def __init__(self, core_context):
                    super().__init__(core_context)
                    self.name = "{self.temp_data['name']}"
                    self.triggers = {self.temp_data['triggers']}
                    # Adicione dependências se necessário, ex: self.dependencies = ["brain"]
                
                def process(self, command):
                    # Implemente a lógica aqui
                    # Use self.core_context.get("brain") se precisar de IA
                    return "Resposta do módulo"
            ```
        """)