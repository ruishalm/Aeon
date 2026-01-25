"DevFactory Module - Fábrica de Software Inteligente"

import os
import json
import subprocess
import threading
import re
from datetime import datetime
from modules.base_module import AeonModule

class DevFactory(AeonModule):
    """
    Módulo que gera projetos de software completos através de um processo interativo e agente.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "DevFactory"
        self.triggers = [
            "crie um site", "crie um script", "crie um projeto", 
            "gere um código", "construa um app", "crie uma calculadora",
            "faça um html", "crie uma api", "programar",
            "dev factory", "devfactory", "desenvolvimento", "fábrica de software", "criar modulo",
            "criar software", "codar", "programação", "desenvolver", "dev"
        ]
        self.dependencies = ["brain"]
        
        self.workspace_dir = os.path.join("AeonProject", "workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        self.projects_log = os.path.join(self.workspace_dir, "projects.json")
        self._load_projects_log()

        # State for the new interview and agentic process
        self.is_interviewing = False
        self.interview_questions = []
        self.gathered_requirements = {}
        self.current_question_key = None

        # --- FORMULÁRIOS DINÂMICOS E SUCINTOS ---
        self.interview_templates = {
            "site": [
                {"key": "paginas", "pergunta": "Página única ou múltiplas páginas?"},
                {"key": "contato", "pergunta": "Incluir formulário de contato?"},
                {"key": "database", "pergunta": "Necessita de banco de dados?"},
                {"key": "linguagem", "pergunta": "Linguagem do backend? (Python, Node.js, ou nenhum)"},
                {"key": "requisitos", "pergunta": "Descreva o objetivo e o estilo do site."}
            ],
            "api": [
                {"key": "linguagem", "pergunta": "Qual framework? (FastAPI, Flask, etc.)"},
                {"key": "autenticacao", "pergunta": "Precisará de autenticação?"},
                {"key": "database", "pergunta": "Qual banco de dados?"},
                {"key": "requisitos", "pergunta": "Quais os endpoints principais?"},
            ],
            "script": [
                {"key": "linguagem", "pergunta": "Qual a linguagem do script?"},
                {"key": "requisitos", "pergunta": "O que o script deve fazer?"},
            ],
            "modulo": [
                {"key": "nome_modulo", "pergunta": "Qual será o nome do módulo?"},
                {"key": "triggers", "pergunta": "Quais serão os gatilhos (palavras-chave)?"},
                {"key": "requisitos", "pergunta": "Descreva a funcionalidade e lógica do módulo."},
            ],
            "default": [
                {"key": "linguagem", "pergunta": "Qual a linguagem principal?"},
                {"key": "requisitos", "pergunta": "Descreva o que o projeto deve fazer."}
            ]
        }

    @property
    def metadata(self) -> dict:
        return {
            "version": "2.2.0",
            "author": "Aeon DevFactory",
            "description": "Gera projetos de software completos através de um processo interativo, agente e sucinto."
        }

    def on_load(self) -> bool:
        if not os.path.exists(self.workspace_dir):
            try:
                os.makedirs(self.workspace_dir)
                return True
            except Exception as e:
                print(f"[DevFactory] Erro ao criar workspace: {e}")
                return False
        return True
    
    def on_unload(self) -> bool:
        self._save_projects_log()
        return True

    def _load_projects_log(self):
        if os.path.exists(self.projects_log):
            try:
                with open(self.projects_log, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
            except Exception as e:
                print(f"[DevFactory] Erro ao carregar projects.json: {e}. Um novo arquivo será criado.")
                self.projects = []
        else:
            self.projects = []

    def _save_projects_log(self):
        try:
            with open(self.projects_log, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DevFactory] Erro ao salvar projects.json: {e}")

    def _start_interview(self, initial_prompt=""):
        """Inicia o processo de entrevista para coletar requisitos."""
        self.is_interviewing = True
        self.gathered_requirements = {"prompt_inicial": initial_prompt}
        self.current_question_key = "tipo_projeto"
        return "Qual o tipo de projeto? (site, api, script)"

    def process(self, command: str) -> str:
        """Processa o comando do usuário, gerenciando a entrevista e o início da criação."""
        if self.is_interviewing:
            self.gathered_requirements[self.current_question_key] = command
            if self.current_question_key == "tipo_projeto":
                project_type = command.lower()
                self.interview_questions = self.interview_templates.get(project_type, self.interview_templates["default"]).copy()
            
            if self.interview_questions:
                next_question = self.interview_questions.pop(0)
                self.current_question_key = next_question["key"]
                return next_question["pergunta"]
            else:
                self.is_interviewing = False
                self.current_question_key = None
                return self._start_agentic_creation()
        else:
            project_type, requirements = self._parse_command(command)
            if not project_type or not requirements or len(requirements) < 5:
                return self._start_interview(initial_prompt=command)
            else:
                self.gathered_requirements = {"tipo_projeto": project_type, "requisitos": requirements, "linguagem": "não especificada"}
                return self._start_agentic_creation()

    def _start_agentic_creation(self) -> str:
        """Inicia o processo de criação agente."""
        final_objective = f"""
        Objetivo: Criar um '{self.gathered_requirements.get('tipo_projeto', 'projeto')}'
        Linguagem: {self.gathered_requirements.get('linguagem', 'não especificada')}
        Requisitos: {self.gathered_requirements.get('requisitos', 'não especificados')}
        Páginas: {self.gathered_requirements.get('paginas', 'não aplicável')}
        Contato: {self.gathered_requirements.get('contato', 'não aplicável')}
        Banco de Dados: {self.gathered_requirements.get('database', 'não aplicável')}
        Autenticação: {self.gathered_requirements.get('autenticacao', 'não aplicável')}
        Endpoints: {self.gathered_requirements.get('endpoints', 'não aplicável')}
        """
        
        self.is_interviewing = False
        self.gathered_requirements = {}

        threading.Thread(
            target=self._agent_loop,
            args=(final_objective,),
            daemon=True
        ).start()

        return f"Ok. Iniciando criação. Acompanhe."

    def _agent_loop(self, objective: str):
        """O loop principal do agente de desenvolvimento."""
        io_handler = self.core_context.get("io_handler")
        brain = self.core_context.get("brain")
        gui = self.core_context.get("gui")

        if not brain or not gui:
            if io_handler: io_handler.falar("Erro: Componentes do core ausentes.")
            return

        plan_prompt = f"Crie um plano conciso para o seguinte objetivo:\n{objective}"
        initial_plan = brain.pensar(prompt=plan_prompt, historico_txt="", user_prefs={})
        
        gui.after(0, lambda: gui.add_message(f"**Plano:**\n{initial_plan}", "DevFactory"))
        if io_handler: io_handler.falar("Plano criado. Verifique a interface.")
        if io_handler: io_handler.falar("Gerando arquivos do projeto...")
        
        # 2. Geração de Código e Arquivos
        code_prompt = f"""
        Com base no plano acima, gere o CÓDIGO COMPLETO para todos os arquivos necessários.
        
        DIRETRIZES ANTI-ALUCINAÇÃO:
        1. Use apenas bibliotecas padrão ou reais e compatíveis.
        2. Não invente importações que não existem.
        3. Garanta que o código seja funcional e completo.

        IMPORTANTE: Para que eu possa criar os arquivos, use EXATAMENTE este formato para CADA arquivo:
        
        FILENAME: nome_do_arquivo.ext
        ```linguagem
        conteudo do codigo aqui
        ```
        
        Não omita nenhum arquivo.
        """
        
        full_response = brain.pensar(prompt=code_prompt, historico_txt=f"Plano Aprovado:\n{initial_plan}", user_prefs={})
        gui.after(0, lambda: gui.add_message(f"**Código Gerado:**\n{full_response}", "DevFactory"))
        
        # 3. Parse e Criação Física
        created_files = self._parse_and_save_files(full_response)
        
        msg = f"Arquivos criados no Workspace: {', '.join(created_files)}" if created_files else "Não consegui identificar arquivos para salvar automaticamente."
        gui.after(0, lambda: gui.add_message(msg, "DevFactory"))
        gui.after(1000, lambda: gui.refresh_workspace_view())

    def _parse_command(self, command: str) -> tuple:
        cmd_lower = command.lower()
        
        # Encontra o tipo de projeto de forma mais robusta
        if any(keyword in cmd_lower for keyword in ["site", "html", "web"]):
            project_type = "site"
        elif any(keyword in cmd_lower for keyword in ["script", "python", "py"]):
            project_type = "script"
        elif any(keyword in cmd_lower for keyword in ["calculadora", "calculator"]):
            project_type = "calculator"
        elif "api" in cmd_lower:
            project_type = "api"
        elif any(keyword in cmd_lower for keyword in ["app", "aplicacao", "aplicativo"]):
            project_type = "app"
        elif any(keyword in cmd_lower for keyword in ["modulo", "módulo", "plugin"]):
            project_type = "modulo"
        else:
            project_type = None
        
        # Extrai os requisitos de forma mais limpa
        if project_type:
            trigger_phrases = [f"crie um {project_type}", f"gere um {project_type}", f"construa um {project_type}", "programar"]
            for phrase in trigger_phrases:
                if phrase in command:
                    requirements = command.replace(phrase, "").strip()
                    break
            else:
                requirements = command
        else:
            requirements = command

        if not requirements:
            requirements = f"Um {project_type} funcional e bem estruturado"
        
        return project_type, requirements

    def _extract_json(self, text: str) -> dict:
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"[DevFactory] Erro de decodificação de JSON: {e}")
            print(f"[DevFactory] Resposta recebida que causou o erro: {text[:500]}...")
        return None

    def _parse_and_save_files(self, text: str) -> list:
        created = []
        # Divide o texto por "FILENAME:" para encontrar cada arquivo
        parts = text.split("FILENAME:")
        
        # Pula a primeira parte (texto introdutório)
        for part in parts[1:]:
            lines = part.strip().split('\n')
            if not lines: continue
            
            filename = lines[0].strip()
            # Busca o bloco de código (``` ... ```)
            code_match = re.search(r"```(?:\w*)\n(.*?)```", part, re.DOTALL)
            
            if code_match:
                content = code_match.group(1)
                safe_filename = os.path.basename(filename) # Segurança básica
                filepath = os.path.join(self.workspace_dir, safe_filename)
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    created.append(safe_filename)
                except Exception as e:
                    print(f"[DevFactory] Erro ao salvar {safe_filename}: {e}")
                    
        return created
