import random
import datetime
from modules.base_module import AeonModule
from .chaos_engine import ChaosEngine # <--- O NOVO MOTOR

# --- BRAÇO 1: O DECK (A ESTRUTURA DOS 22 CAMINHOS) ---
class DeckHandler:
    def __init__(self):
        self.chaos = ChaosEngine() # Inicia o motor de entropia
        
        # Mapeamento Estrito: Golden Dawn / Sefer Yetzirah
        self.arcanos_maiores = {
            "louco":      {"hebraico": "א", "letra": "Aleph", "gematria": 1,   "nota": "Ar (Ruach) - O Caos Primordial"},
            "mago":       {"hebraico": "ב", "letra": "Beth",  "gematria": 2,   "nota": "Mercúrio - A Casa/Construção"},
            "sacerdotisa":{"hebraico": "ג", "letra": "Gimel", "gematria": 3,   "nota": "Lua - O Camelo/Travessia"},
            "imperatriz": {"hebraico": "ד", "letra": "Daleth","gematria": 4,   "nota": "Vênus - A Porta"},
            "imperador":  {"hebraico": "ה", "letra": "He",    "gematria": 5,   "nota": "Áries - A Janela/Visão"},
            "hierofante": {"hebraico": "ו", "letra": "Vav",   "gematria": 6,   "nota": "Touro - O Prego/Conexão"},
            "enamorados": {"hebraico": "ז", "letra": "Zain",  "gematria": 7,   "nota": "Gêmeos - A Espada/Discernimento"},
            "carro":      {"hebraico": "ח", "letra": "Cheth", "gematria": 8,   "nota": "Câncer - A Cerca/Proteção"},
            "força":      {"hebraico": "ט", "letra": "Teth",  "gematria": 9,   "nota": "Leão - A Serpente/Domínio"},
            "eremita":    {"hebraico": "י", "letra": "Yod",   "gematria": 10,  "nota": "Virgem - A Mão/Ponto Primordial"},
            "roda":       {"hebraico": "כ", "letra": "Kaph",  "gematria": 20,  "nota": "Júpiter - A Palma/Karma"},
            "justiça":    {"hebraico": "ל", "letra": "Lamed", "gematria": 30,  "nota": "Libra - O Aguilhão/Ensino"},
            "enforcado":  {"hebraico": "מ", "letra": "Mem",   "gematria": 40,  "nota": "Água (Mayim) - O Ventre/Sacrifício"},
            "morte":      {"hebraico": "נ", "letra": "Nun",   "gematria": 50,  "nota": "Escorpião - O Peixe/Queda"},
            "temperança": {"hebraico": "ס", "letra": "Samekh","gematria": 60,  "nota": "Sagitário - O Pilar/Sustentação"},
            "diabo":      {"hebraico": "ע", "letra": "Ayin",  "gematria": 70,  "nota": "Capricórnio - O Olho/Aparência"},
            "torre":      {"hebraico": "פ", "letra": "Pe",    "gematria": 80,  "nota": "Marte - A Boca/Destruição (Gevurah)"},
            "estrela":    {"hebraico": "צ", "letra": "Tzaddi","gematria": 90,  "nota": "Aquário - O Anzol/O Justo"},
            "lua":        {"hebraico": "ק", "letra": "Qoph",  "gematria": 100, "nota": "Peixes - A Nuca/Subconsciente"},
            "sol":        {"hebraico": "ר", "letra": "Resh",  "gematria": 200, "nota": "Sol - A Cabeça/Racionalidade"},
            "julgamento": {"hebraico": "ש", "letra": "Shin",  "gematria": 300, "nota": "Fogo (Esh) - O Dente/Espírito/Rigor"},
            "mundo":      {"hebraico": "ת", "letra": "Tav",   "gematria": 400, "nota": "Saturno/Terra - O Selo/Finalização"}
        }
        self.deck_virtual = list(self.arcanos_maiores.keys())

    def comprar_cartas(self, quantidade=3):
        # USA O MOTOR DE CAOS
        # Em vez de sortear 3 cartas soltas, embaralhamos o universo do deck
        # com base na entropia do computador e pegamos as do topo.
        deck_embaralhado = self.chaos.shuffle_deck(self.deck_virtual)
        
        qtd_real = min(quantidade, len(deck_embaralhado))
        return deck_embaralhado[:qtd_real]

    def identificar_cartas_texto(self, texto):
        encontradas = []
        texto_lower = texto.lower()
        for chave in self.arcanos_maiores:
            if chave in texto_lower:
                encontradas.append(chave)
        return encontradas

    def get_info(self, nome_carta):
        return self.arcanos_maiores.get(nome_carta, None)


# --- BRAÇO 2: O RABINO DIGITAL (INTÉRPRETE) ---
class KabbalahInterpreter:
    def __init__(self):
        self.base_persona = """
        ATUE COMO: Um Rabino Cabalista (Mekubal) especialista no Zohar e na estrutura da Árvore da Vida (Etz Chaim).
        
        SUA TAREFA: Realizar uma leitura profunda de 'Engenharia Espiritual'.

        DIRETRIZES ESTRITAS (HALACHA):
        1. O FOGO (Shin / Paus / Julgamento) é GEVURAH (Rigor).
        2. TIKUN (Correção): Use o TEHILIM (Salmo) calculado como a cura da alma.
        3. ESTRUTURA DA ÁRVORE (Se for tiragem de 10 cartas):
           - Não leia cartas isoladas. Siga o "Caminho do Relâmpago".
           - Analise os PARES de Opostos: Chokmah(2) vs Binah(3) (Energia vs Forma), Chesed(4) vs Geburah(5) (Expansão vs Restrição), Netzach(7) vs Hod(8) (Emoção vs Razão).
           - Analise a COLUNA DO MEIO: Keter(1) -> Tiphareth(6) -> Yesod(9) -> Malkuth(10) (A evolução da consciência).
        
        Seja austero, profundo e revele o oculto (Sod).
        """
        
        self.posicoes_arvore = [
            "1. KETER (A Coroa - Essência Divina)",
            "2. CHOKMAH (Sabedoria - Impulso Masculino)",
            "3. BINAH (Entendimento - Forma Feminina)",
            "4. CHESED (Misericórdia - Expansão)",
            "5. GEBURAH (Severidade - Restrição/Corte)",
            "6. TIPHARETH (Beleza - O Eu Verdadeiro/Equilíbrio)",
            "7. NETZACH (Vitória - Instintos/Emoções)",
            "8. HOD (Esplendor - Intelecto/Razão)",
            "9. YESOD (Fundação - Subconsciente/Sonhos)",
            "10. MALKUTH (O Reino - Resultado Físico)"
        ]

    def calcular_tehilim(self, cartas_info):
        soma_gematria = sum(c['gematria'] for c in cartas_info)
        salmo = soma_gematria % 150
        if salmo == 0: salmo = 150
        return salmo, soma_gematria

    def montar_prompt(self, cartas_nomes, deck_handler, tipo_tiragem="padrao"):
        cartas_detalhadas = []
        dados_cartas = []
        string_hebraica = []

        for i, nome in enumerate(cartas_nomes):
            info = deck_handler.get_info(nome)
            if info:
                dados_cartas.append(info)
                prefixo = ""
                if tipo_tiragem == "arvore" and i < 10:
                    prefixo = f"[{self.posicoes_arvore[i]}] -> "
                
                cartas_detalhadas.append(f"{prefixo}{nome.upper()}: Letra {info['hebraico']} ({info['letra']}) | {info['nota']}")
                string_hebraica.append(info['hebraico'])
        
        if not dados_cartas:
            return None, None

        salmo, gematria_total = self.calcular_tehilim(dados_cartas)
        visual_hebraico = " - ".join(string_hebraica)
        
        prompt =  "--- ESTRUTURA DAS OTIOT (LETRAS) ---\n"
        prompt += f"RAIZ: [ {visual_hebraico} ]\n"
        prompt += "\n".join(cartas_detalhadas)
        prompt += f"\n\n--- CÁLCULOS GEMÁTRICOS ---\n"
        prompt += f"VALOR TOTAL: {gematria_total}\n"
        prompt += f"TIKUN SUGERIDO (SALMO): {salmo}\n"
        
        if tipo_tiragem == "arvore":
            prompt += "\nUSUÁRIO PERGUNTA: Analise esta Árvore da Vida. Verifique o fluxo do Relâmpago, o equilíbrio dos Pilares e a síntese na Coluna do Meio."
        else:
            prompt += "\nUSUÁRIO PERGUNTA: Qual a retificação (Tikun) necessária aqui? Foque no rigor do Fogo e na raiz das letras."
        
        return f"{self.base_persona}\n\n{prompt}", visual_hebraico

    def montar_prompt_conversa(self, comando, contexto_tiragem, historico_recente):
        prompt = f"{self.base_persona}\n\n"
        prompt += "--- CONTEXTO DA TIRAGEM ATUAL ---\n"
        prompt += contexto_tiragem + "\n\n"
        prompt += "--- HISTÓRICO DA CONVERSA NESTA SESSÃO ---\n"
        prompt += historico_recente + "\n\n"
        prompt += f"O consulente pergunta: {comando}\n"
        prompt += "Responda mantendo a autoridade rabínica e baseando-se estritamente nas cartas e letras citadas no contexto acima."
        return prompt


# --- MÓDULO PRINCIPAL ---
class TarologoModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Tarólogo"
        self.triggers = ["tarô", "tarot", "tiragem", "cartas", "cabala", "interpretar", "arvore", "árvore"]
        self.deck = DeckHandler()
        self.interprete = KabbalahInterpreter()
        self.current_reading_context = None
        self.session_history = []

    @property
    def metadata(self) -> dict:
        return {
            "description": "Oráculo Cabalista que utiliza entropia de hardware para tiragens de Tarô e análise via Árvore da Vida.",
            "version": "1.1.0"
        }

    def process(self, command: str) -> str:
        text_lower = command.lower()
        brain = self.core_context.get("brain")
        mm = self.core_context.get("module_manager")
        config = self.core_context.get("config_manager")

        if not brain:
            return "Erro: Cérebro não encontrado para interpretação."

        # 1. Lógica de Saída/Encerramento
        if any(x in text_lower for x in ["obrigado", "encerrar", "sair", "fechar sessão", "concluído"]):
            if mm: mm.release_focus() # Libera o Aeon para outros módulos
            self.current_reading_context = None
            self.session_history = []
            return "Que a Luz de Keter ilumine seu caminho. Sessão encerrada."

        # 2. Se já houver uma tiragem ativa e o usuário estiver "papeando"
        if self.current_reading_context and not any(t in text_lower for t in self.triggers):
            hist_txt = "\n".join(self.session_history[-5:]) # Últimas 5 trocas
            prompt_conversa = self.interprete.montar_prompt_conversa(command, self.current_reading_context, hist_txt)
            resposta = brain.pensar(prompt_conversa)
            self.session_history.append(f"Consulente: {command}\nRabino: {resposta}")
            return resposta

        tipo_tiragem = "padrao"
        qtd_cartas = 3
        
        if "arvore" in text_lower or "árvore" in text_lower or "10 cartas" in text_lower or "sephiroth" in text_lower:
            tipo_tiragem = "arvore"
            qtd_cartas = 10

        cartas_usuario = self.deck.identificar_cartas_texto(text_lower)
        cartas_para_analise = []
        msg_origem = ""

        if cartas_usuario:
            cartas_para_analise = cartas_usuario
            msg_origem = "Entrada Manual"
            if tipo_tiragem == "arvore" and len(cartas_para_analise) < 10:
                return f"Para a Árvore da Vida, preciso de 10 cartas. Você forneceu apenas {len(cartas_para_analise)}."
        elif "tirar" in text_lower or "sorteie" in text_lower or "nova" in text_lower or "faça" in text_lower:
            # AQUI O CAOS ENTRA EM AÇÃO
            cartas_para_analise = self.deck.comprar_cartas(qtd_cartas)
            msg_origem = "Sorteio da Providência (Entropia Máxima)"
        else:
            return "Diga as cartas ou peça para tirar (ex: 'Faça a tiragem da Árvore da Vida')."

        prompt_final, visual_hebraico = self.interprete.montar_prompt(cartas_para_analise, self.deck, tipo_tiragem)
        
        if prompt_final:
            # Salva o contexto para permitir o "papo" posterior
            self.current_reading_context = prompt_final
            self.session_history = []
            
            # Persistência de longo prazo via ConfigManager
            if config:
                config.add_tarot_reading({
                    "data": datetime.datetime.now().isoformat(),
                    "tipo": tipo_tiragem,
                    "cartas": cartas_para_analise,
                    "hebraico": visual_hebraico
                })

            # Trava o foco no módulo para permitir conversa fluida
            if mm: mm.lock_focus(self)
            
            resposta = brain.pensar(prompt_final)
            self.session_history.append(f"Tiragem: {visual_hebraico}\nRabino: {resposta}")
            return resposta
            
        return "Erro na leitura das lâminas."