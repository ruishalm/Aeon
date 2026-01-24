import random
from modules.base_module import AeonModule

# Lista completa das 78 cartas do Tarot de Rider-Waite
TAROT_CARDS = {
    "Arcanos Maiores": [
        "O Louco", "O Mago", "A Sacerdotisa", "A Imperatriz", "O Imperador",
        "O Hierofante", "Os Amantes", "A Carruagem", "A Força", "O Eremita",
        "A Roda da Fortuna", "A Justiça", "O Enforcado", "A Morte", "A Temperança",
        "O Diabo", "A Torre", "A Estrela", "A Lua", "O Sol", "O Julgamento", "O Mundo"
    ],
    "Arcanos Menores": {
        "Paus": ["Ás de Paus", "Dois de Paus", "Três de Paus", "Quatro de Paus", "Cinco de Paus", "Seis de Paus", "Sete de Paus", "Oito de Paus", "Nove de Paus", "Dez de Paus", "Pajem de Paus", "Cavaleiro de Paus", "Rainha de Paus", "Rei de Paus"],
        "Copas": ["Ás de Copas", "Dois de Copas", "Três de Copas", "Quatro de Copas", "Cinco de Copas", "Seis de Copas", "Sete de Copas", "Oito de Copas", "Nove de Copas", "Dez de Copas", "Pajem de Copas", "Cavaleiro de Copas", "Rainha de Copas", "Rei de Copas"],
        "Espadas": ["Ás de Espadas", "Dois de Espadas", "Três de Espadas", "Quatro de Espadas", "Cinco de Espadas", "Seis de Espadas", "Sete de Espadas", "Oito de Espadas", "Nove de Espadas", "Dez de Espadas", "Pajem de Espadas", "Cavaleiro de Espadas", "Rainha de Espadas", "Rei de Espadas"],
        "Ouros": ["Ás de Ouros", "Dois de Ouros", "Três de Ouros", "Quatro de Ouros", "Cinco de Ouros", "Seis de Ouros", "Sete de Ouros", "Oito de Ouros", "Nove de Ouros", "Dez de Ouros", "Pajem de Ouros", "Cavaleiro de Ouros", "Rainha de Ouros", "Rei de Ouros"]
    }
}

class TarologoModule(AeonModule):
    """
    Um módulo místico que permite ao Aeon realizar leituras de Tarot.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Tarologo"
        # Triggers para ativar a leitura
        self.triggers = ["ler as cartas", "jogar tarot", "preveja meu futuro", "leia meu futuro", "consulta ao tarot"]
        self.full_deck = self._get_full_deck()

    @property
    def metadata(self) -> dict:
        return {
            "description": "Realiza uma leitura de Tarot com 3 cartas (Passado, Presente, Futuro) e interpreta o resultado.",
            "version": "1.0.0",
            "author": "Aeon"
        }
        
    def _get_full_deck(self):
        """Cria uma lista única com todas as 78 cartas."""
        deck = TAROT_CARDS["Arcanos Maiores"].copy()
        for suit in TAROT_CARDS["Arcanos Menores"].values():
            deck.extend(suit)
        return deck

    def _draw_cards(self, num_cards=3):
        """Sorteia um número de cartas do baralho, sem repetição."""
        random.shuffle(self.full_deck)
        return random.sample(self.full_deck, num_cards)

    def process(self, command: str) -> str:
        """
        Processa o comando do usuário, realiza a leitura se for um trigger
        e retorna a interpretação do cérebro.
        """
        if not self.brain_connected():
            return "Não consigo acessar meus dons místicos sem uma conexão com a consciência cósmica."

        # Sorteia 3 cartas para uma leitura de Passado, Presente e Futuro
        cartas_sorteadas = self._draw_cards(3)
        
        # Sorteia a orientação (normal ou invertida) para cada carta
        posicoes = ["normal", "invertida"]
        carta1, pos1 = cartas_sorteadas[0], random.choice(posicoes)
        carta2, pos2 = cartas_sorteadas[1], random.choice(posicoes)
        carta3, pos3 = cartas_sorteadas[2], random.choice(posicoes)

        # Prepara a mensagem para o usuário
        intro = f"Consultei os arcanos e estas são suas cartas... Para o Passado: {carta1} na posição {pos1}. Para o Presente: {carta2} na posição {pos2}. E para o Futuro: {carta3} na posição {pos3}. Deixe-me interpretar..."
        self.get_io_handler().falar(intro) # Fala a introdução enquanto o cérebro processa

        # Cria o prompt para a IA
        prompt = f"""
        Aja como um tarólogo experiente, místico e sábio.
        Um usuário pediu uma leitura de tarot e as seguintes 3 cartas foram sorteadas no método Passado, Presente e Futuro:
        
        - Passado: {carta1} ({pos1})
        - Presente: {carta2} ({pos2})
        - Futuro: {carta3} ({pos3})
        
        Forneça uma interpretação coesa e inspiradora para essa combinação de cartas e posições.
        Conecte o significado de cada carta com a sua posição no tempo (Passado, Presente, Futuro).
        Seja profundo, mas claro. Termine com um conselho enigmático ou uma reflexão.
        Não liste os significados das cartas separadamente, construa uma narrativa fluida que conecte as três.
        """
        
        try:
            # Envia para o cérebro para interpretação
            response = self.get_brain().predict(prompt)
            return response
        except Exception as e:
            print(f"[TAROLOGO][ERRO] Falha ao contatar o cérebro para interpretação: {e}")
            return "Houve uma perturbação no plano astral. Não consegui completar a leitura."

