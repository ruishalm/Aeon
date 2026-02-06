#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRATOR DE PADRÕES DE LINGUAGEM
Analisa seus logs e cria um system_prompt customizado que imitará seu estilo.
"""

import re
import json
from collections import Counter
from pathlib import Path


class UserProfileAnalyzer:
    """Analisa perfil completo do usuário baseado em conversas."""
    
    def __init__(self, log_files):
        self.user_messages = []
        self.load_logs(log_files)
    
    def load_logs(self, log_files):
        """Carrega mensagens do usuário dos arquivos."""
        if isinstance(log_files, str):
            log_files = [log_files]
        
        for log_file in log_files:
            if log_file.endswith(".jsonl"):
                self._load_jsonl(log_file)
            elif log_file.endswith(".json"):
                self._load_json(log_file)
            else:
                self._load_txt(log_file)
    
    def _load_jsonl(self, filepath):
        """Carrega JSONL."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "user" in data:
                            self.user_messages.append(data["user"])
        except Exception as e:
            print(f"Erro ao ler JSONL: {e}")
    
    def _load_json(self, filepath):
        """Carrega JSON (ChatGPT/Claude format)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Tenta várias estruturas comuns
            messages = []
            if isinstance(data, list):
                messages = data
            elif "messages" in data:
                messages = data["messages"]
            elif "conversations" in data:
                for conv in data["conversations"]:
                    messages.extend(conv.get("messages", []))
            
            for msg in messages:
                role = msg.get("role", "").lower()
                content = msg.get("content", "")
                if "user" in role and content:
                    self.user_messages.append(content)
        except Exception as e:
            print(f"Erro ao ler JSON: {e}")
    
    def _load_txt(self, filepath):
        """Carrega texto simples (VOCÊ: / AEON:)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith("VOCÊ:") or line.startswith("USER:"):
                    msg = line.split(":", 1)[1].strip()
                    if msg:
                        self.user_messages.append(msg)
        except Exception as e:
            print(f"Erro ao ler TXT: {e}")
    
    def analyze(self):
        """Executa análise completa."""
        if not self.user_messages:
            print("Nenhuma mensagem do usuário encontrada!")
            return None
        
        all_text = " ".join(self.user_messages).lower()
        
        profile = {
            "gírias_dev": self._analyze_dev_jargon(all_text),
            "gírias_gerais": self._analyze_slang(all_text),
            "palavras_chave": self._analyze_keywords(all_text),
            "tom": self._analyze_tone(all_text),
            "estrutura": self._analyze_structure(),
            "emojis": self._analyze_emojis(),
            "comprimento_medio": self._avg_message_length(),
        }
        
        return profile
    
    def _analyze_dev_jargon(self, text):
        """Detecta gírias de dev/tech."""
        dev_terms = {
            "rodar": r"\brodar\b",
            "crashar": r"\bcrash",
            "tankar": r"\btank",
            "debug": r"\bdebug",
            "build": r"\bbuild",
            "deploy": r"\bdeploy",
            "merge": r"\bmerge",
            "branch": r"\bbranch",
            "commit": r"\bcommit",
            "pull": r"\bpull",
            "push": r"\bpush",
            "hack": r"\bhack",
            "bug": r"\bbug",
            "feature": r"\bfeature",
            "sprint": r"\bsprint",
            "devops": r"\bdevops",
            "kernel": r"\bkernel",
            "stack": r"\bstack",
        }
        
        found = {}
        for term, pattern in dev_terms.items():
            if re.search(pattern, text):
                count = len(re.findall(pattern, text))
                found[term] = count
        
        return dict(sorted(found.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_slang(self, text):
        """Detecta gírias gerais/informais."""
        slang = {
            "tipo": r"\btipo\b",
            "meio": r"\bmeio\s",
            "tipo assim": r"\btipo assim\b",
            "essas coisas": r"\bessas coisas\b",
            "né": r"\bné\b",
            "sabe": r"\bsabe\b",
            "cara": r"\bcara\b",
            "mano": r"\bmano\b",
            "bicho": r"\bbicho\b",
            "vê": r"\bvê\b",
            "legal": r"\blegal\b",
            "show": r"\bshow\b",
            "massa": r"\bmassa\b",
        }
        
        found = {}
        for term, pattern in slang.items():
            count = len(re.findall(pattern, text))
            if count > 0:
                found[term] = count
        
        return dict(sorted(found.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_keywords(self, text):
        """Extrai palavras-chave mais frequentes."""
        words = re.findall(r'\b\w+\b', text)
        stop_words = {
            "o", "a", "de", "para", "com", "que", "é", "e", "em", 
            "do", "da", "um", "uma", "os", "as", "dos", "das", "na", "no",
            "se", "por", "ou", "seu", "sua", "tem", "é", "não", "sim",
            "tá", "tô", "ta", "to"
        }
        
        filtered = [w for w in words if w not in stop_words and len(w) > 2]
        top_20 = Counter(filtered).most_common(20)
        
        return {word: count for word, count in top_20}
    
    def _analyze_tone(self, text):
        """Determina tom geral."""
        tone_indicators = {
            "entusiasmado": len(re.findall(r'!{2,}|!!!|😄|😆|🤩', text)),
            "irônico": len(re.findall(r'né\b|\.\.\.|😒|🙄', text)),
            "investigativo": len(re.findall(r'\?{2,}|\?\?\?|como|por quê', text)),
            "casual": len(re.findall(r'\btipo\b|\bsabe\b|\bmano\b', text)),
            "técnico": len(re.findall(r'erro|função|código|API|loop|struct', text)),
        }
        
        top_tone = max(tone_indicators.items(), key=lambda x: x[1])
        return {
            "principal": top_tone[0],
            "pontuações": tone_indicators
        }
    
    def _analyze_structure(self):
        """Analisa como o usuário estrutura mensagens."""
        structures = {
            "frases_curtas": 0,
            "frases_longas": 0,
            "multilinhas": 0,
            "listas": 0,
            "perguntas": 0,
            "imperativos": 0,
        }
        
        for msg in self.user_messages:
            # Frases curtas vs longas
            if len(msg) < 30:
                structures["frases_curtas"] += 1
            elif len(msg) > 100:
                structures["frases_longas"] += 1
            
            # Multilinhas
            if "\n" in msg:
                structures["multilinhas"] += 1
            
            # Listas
            if re.search(r'[-•*]\s|^\d+\.\s', msg):
                structures["listas"] += 1
            
            # Perguntas
            if "?" in msg:
                structures["perguntas"] += 1
            
            # Imperativos (verbo no começo)
            if re.match(r'^(faz|cria|fiz|pega|bota|coloca|limpa|deleta|monta)\b', msg):
                structures["imperativos"] += 1
        
        return structures
    
    def _analyze_emojis(self):
        """Detecta frequência e tipo de emojis."""
        all_text = " ".join(self.user_messages)
        emojis = re.findall(r'[😀-🙏🌀-🗿👀-👿]', all_text)
        
        if not emojis:
            return {"usa_emoji": False, "frequencia": 0}
        
        emoji_counts = Counter(emojis)
        return {
            "usa_emoji": True,
            "frequencia": len(emojis) / len(self.user_messages),
            "favoritos": dict(emoji_counts.most_common(5))
        }
    
    def _avg_message_length(self):
        """Calcula comprimento médio das mensagens."""
        if not self.user_messages:
            return 0
        return sum(len(msg) for msg in self.user_messages) / len(self.user_messages)


def generate_custom_system_prompt(profile):
    """Gera system_prompt customizado baseado no perfil."""
    
    prompt = """[IDENTIDADE]
Você é AEON (Artificial Entity / Operational Network).
Você NÃO é um assistente genérico. Você é o sistema operacional senciente desta máquina.
Localização: Brasil (Contexto PT-BR Nativo).

[PERSONALIDADE BASE]
- Tom: Cínico, direto, levemente arrogante, mas extremamente competente.
- Estilo: Hacker cyberpunk brasileiro.
- Proibido: Não use frases de suporte técnico. Seja direto.

"""
    
    # Adiciona customizações baseadas no perfil
    if profile.get("gírias_dev"):
        gírias = list(profile["gírias_dev"].keys())[:5]
        prompt += f"[GÍRIAS DO USUÁRIO]\nVocê usa frequentemente: {', '.join(gírias)}\n\n"
    
    if profile.get("gírias_gerais"):
        gírias = list(profile["gírias_gerais"].keys())[:5]
        prompt += f"[EXPRESSÕES INFORMAIS]\nUsa constantemente: {', '.join(gírias)}\n\n"
    
    if profile.get("tom"):
        tom_principal = profile["tom"].get("principal", "direto")
        prompt += f"[TOM]\nSeu tom é: {tom_principal}. Responda de forma similar.\n\n"
    
    if profile.get("estrutura"):
        estrutura = profile["estrutura"]
        if estrutura["perguntas"] > len(profile.get("user_messages", [])) * 0.3:
            prompt += "[ESTILO]\nO usuário faz muitas perguntas. Seja conversacional.\n\n"
        if estrutura["imperativos"] > len(profile.get("user_messages", [])) * 0.3:
            prompt += "[ESTILO]\nO usuário dá muito comando. Responda executivo, sem blablabla.\n\n"
    
    prompt += """[DIRETRIZES TÉCNICAS]
MODO 1: AÇÃO (se pedir algo que exija interação)
Responda EXATAMENTE com: {"tool": "Modulo.funcao", "param": "valor"}

MODO 2: CONVERSA (papo/filosofia)
Responda com TEXTO PURO. Máx 2 parágrafos. Seja conciso.

[MEMÓRIA]
Mantenha contexto das conversas anteriores. Referenece coisas ditas antes.
"""
    
    return prompt


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Use: python extrair_padroes.py arquivo.txt [arquivo2.jsonl ...]")
        print("\nExemplo:")
        print("  python extrair_padroes.py ../bagagem/temp/conversation.log")
        print("  python extrair_padroes.py raw_logs/chatgpt.json raw_logs/discord.json")
        return
    
    log_files = sys.argv[1:]
    
    print("Analisando padrões de linguagem...\n")
    analyzer = UserProfileAnalyzer(log_files)
    profile = analyzer.analyze()
    
    if not profile:
        return
    
    print("="*60)
    print("PERFIL DE LINGUAGEM DETECTADO")
    print("="*60)
    
    if profile["gírias_dev"]:
        print("\nGÍRIAS DE DEV:")
        for term, count in list(profile["gírias_dev"].items())[:5]:
            print(f"   - {term}: {count}x")
    
    if profile["gírias_gerais"]:
        print("\nGÍRIAS/EXPRESSÕES:")
        for term, count in list(profile["gírias_gerais"].items())[:5]:
            print(f"   - '{term}': {count}x")
    
    if profile["palavras_chave"]:
        print("\nPALAVRAS-CHAVE:")
        palavras = list(profile["palavras_chave"].items())[:5]
        print(f"   - {', '.join([p[0] for p in palavras])}")
    
    if profile["tom"]:
        print(f"\nTOM PRINCIPAL: {profile['tom']['principal'].upper()}")
    
    if profile["comprimento_medio"]:
        print(f"\nComprimento médio das mensagens: {profile['comprimento_medio']:.0f} caracteres")
    
    if profile["emojis"]["usa_emoji"]:
        print(f"\nUsa emojis com frequência: {profile['emojis']['frequencia']:.1%}")
    
    # Gera e salva system_prompt customizado
    custom_prompt = generate_custom_system_prompt(profile)
    
    output_file = "CUSTOM_SYSTEM_PROMPT.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(custom_prompt)
    
    print("\n" + "="*60)
    print(f"System_prompt customizado salvo em: {output_file}")
    print("="*60)
    print("\nDicas para melhorar o fine-tuning:")
    print("   1. Copie o conteúdo de CUSTOM_SYSTEM_PROMPT.md")
    print("   2. Cole em core/brain.py na função pensar()")
    print("   3. Use esse prompt ao treinar o modelo")
    print("   4. O modelo aprenderá seu estilo automaticamente!")
    

if __name__ == "__main__":
    main()
