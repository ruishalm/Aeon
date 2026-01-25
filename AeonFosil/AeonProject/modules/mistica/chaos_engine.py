import time
import os
import hashlib
import psutil
import random
import struct

class ChaosEngine:
    def __init__(self):
        self.entropy_pool = []
    
    def _collect_entropy(self):
        """Coleta dados voláteis do sistema para gerar caos real"""
        # 1. Tempo em Nanossegundos (Muda a cada bilionésimo de segundo)
        t_ns = time.time_ns()
        
        # 2. Estado Volátil do Sistema (CPU e RAM flutuam constantemente)
        cpu_stats = psutil.cpu_times()
        ram_stats = psutil.virtual_memory()
        
        # 3. Identificadores de Processo
        pid = os.getpid()
        
        # 4. Bytes Aleatórios do SO (Criptograficamente seguros)
        os_random = os.urandom(32)
        
        # Mistura tudo numa string caótica
        raw_data = f"{t_ns}-{cpu_stats.user}-{ram_stats.available}-{pid}-{os_random}"
        return raw_data.encode('utf-8')

    def get_seed(self):
        """Gera uma semente inteira a partir do hash do caos"""
        raw_entropy = self._collect_entropy()
        
        # Cria um hash SHA-256 (digital fingerprint única)
        hash_digest = hashlib.sha256(raw_entropy).digest()
        
        # Converte os primeiros 8 bytes do hash num número inteiro gigante
        # Isso garante que a semente é matematicamente imprevisível
        seed_int = struct.unpack("Q", hash_digest[:8])[0]
        return seed_int

    def shuffle_deck(self, deck_list):
        """Embaralha uma lista usando a semente do caos"""
        seed = self.get_seed()
        
        # Instancia um gerador random isolado com a nossa semente sagrada
        rng = random.Random(seed)
        
        # Cria uma cópia para não alterar o original
        shuffled = deck_list.copy()
        rng.shuffle(shuffled)
        
        return shuffled

    def draw_card(self, deck_list):
        """Saca uma carta única usando entropia máxima"""
        seed = self.get_seed()
        rng = random.Random(seed)
        return rng.choice(deck_list)