#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONVERSOR DE LOGS UNIVERSAL
Transforma logs de várias fontes em formato VOCÊ/AEON para treinamento.
Detecta padrões de linguagem do usuário automaticamente.
"""

import json
import os
import re
from pathlib import Path
from collections import Counter
import argparse


class LanguageProfile:
    """Analisa padrões de linguagem do usuário."""
    
    def __init__(self):
        self.patterns = {
            "gírias_dev": [],
            "palavras_frequentes": Counter(),
            "estruturas": [],
            "tom": "neutro",
            "emoji_freq": 0,
            "exclamacoes": 0,
            "perguntas": 0,
        }
    
    def analyze(self, texts):
        """Analisa uma lista de textos do usuário."""
        all_text = " ".join(texts).lower()
        
        # Gírias comuns de dev/tech
        dev_words = ["rodar", "crashar", "tankar", "debug", "build", "deploy", 
                     "merge", "branch", "commit", "pull", "push", "hack", "bug",
                     "feature", "sprint", "agile", "devops", "stack", "kernel"]
        self.patterns["gírias_dev"] = [w for w in dev_words if w in all_text]
        
        # Frequência de palavras (top 20)
        words = re.findall(r'\b\w+\b', all_text)
        stop_words = {"o", "a", "de", "para", "com", "que", "é", "e", "em", 
                      "do", "da", "um", "uma", "os", "as", "dos", "das"}
        words = [w for w in words if w not in stop_words and len(w) > 2]
        self.patterns["palavras_frequentes"] = Counter(words).most_common(20)
        
        # Tom (baseado em pontuação)
        emoji_count = len(re.findall(r'[😀-🙏🌀-🗿]', " ".join(texts)))
        exclamacao_count = " ".join(texts).count("!")
        pergunta_count = " ".join(texts).count("?")
        
        self.patterns["emoji_freq"] = emoji_count
        self.patterns["exclamacoes"] = exclamacao_count
        self.patterns["perguntas"] = pergunta_count
        
        # Determina tom
        if emoji_count > len(texts) * 0.1:
            self.patterns["tom"] = "casual/emojis"
        elif exclamacao_count > len(texts) * 0.1:
            self.patterns["tom"] = "entusiasmado"
        elif pergunta_count > len(texts) * 0.1:
            self.patterns["tom"] = "investigativo"
        else:
            self.patterns["tom"] = "neutro/direto"
        
        return self.patterns
    
    def to_system_prompt_addition(self):
        """Gera um trecho de system_prompt customizado."""
        prompt = "\n[PADRÕES DO USUÁRIO]\n"
        
        if self.patterns["gírias_dev"]:
            prompt += f"- Usa gírias de dev: {', '.join(self.patterns['gírias_dev'])}\n"
        
        prompt += f"- Tom: {self.patterns['tom']}\n"
        
        if self.patterns["palavras_frequentes"]:
            top_words = [w[0] for w in self.patterns["palavras_frequentes"][:5]]
            prompt += f"- Palavras frequentes: {', '.join(top_words)}\n"
        
        return prompt


class LogConverter:
    """Converte logs de várias plataformas."""
    
    def __init__(self):
        self.language_profile = LanguageProfile()
    
    def detect_format(self, filepath):
        """Detecta o formato do arquivo."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ChatGPT export (JSON com conversations array)
        if '"conversations"' in content or '"messages"' in content:
            return "chatgpt"
        
        # Claude export (JSON com specific structure)
        if '"uuid"' in content and '"conversation"' in content:
            return "claude"
        
        # Discord export (JSON array com author/content)
        if '"author"' in content and '"content"' in content and '"timestamp"' in content:
            return "discord"
        
        # Log simples (VOCÊ: / AEON: ou similar)
        if "VOCÊ:" in content or "você:" in content or "USER:" in content:
            return "simple"
        
        # Log crudo genérico (assume alternância de linhas)
        return "generic"
    
    def convert_chatgpt(self, filepath):
        """Converte ChatGPT JSON export."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pairs = []
        user_texts = []
        
        # ChatGPT pode ter vários formatos
        conversations = data if isinstance(data, list) else data.get("conversations", [])
        
        for conv in conversations:
            messages = conv.get("messages", []) if isinstance(conv, dict) else []
            
            for msg in messages:
                role = msg.get("role", "").lower()
                content = msg.get("content", "") or ""
                
                # Limpa markdown e formatação
                if isinstance(content, str):
                    content = content.strip()
                elif isinstance(content, list):
                    content = " ".join(str(c) for c in content).strip()
                
                if not content:
                    continue
                
                if "user" in role:
                    user_texts.append(content)
                    pairs.append(("VOCÊ", content))
                elif "assistant" in role:
                    pairs.append(("AEON", content))
        
        self.language_profile.analyze(user_texts)
        return pairs
    
    def convert_claude(self, filepath):
        """Converte Claude JSON export."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pairs = []
        user_texts = []
        
        # Claude exporta como { conversations: [...] } ou direto array
        convs = data.get("conversations", []) if isinstance(data, dict) else data
        
        for conv in convs:
            messages = conv.get("messages", []) if isinstance(conv, dict) else []
            
            for msg in messages:
                role = msg.get("role", "").lower()
                content = msg.get("text", "") or msg.get("content", "")
                
                if isinstance(content, str):
                    content = content.strip()
                elif isinstance(content, list):
                    content = " ".join(str(c) for c in content).strip()
                
                if not content:
                    continue
                
                if "user" in role:
                    user_texts.append(content)
                    pairs.append(("VOCÊ", content))
                elif "assistant" in role:
                    pairs.append(("AEON", content))
        
        self.language_profile.analyze(user_texts)
        return pairs
    
    def convert_discord(self, filepath):
        """Converte Discord JSON export."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pairs = []
        user_texts = []
        your_id = None  # Será detectado ou passado
        
        messages = data if isinstance(data, list) else data.get("messages", [])
        
        for msg in messages:
            author = msg.get("author", {})
            author_name = author.get("name", "") if isinstance(author, dict) else str(author)
            content = msg.get("content", "").strip()
            
            if not content or content.startswith("http"):  # Pula links
                continue
            
            # Assume que primeiro autor é o usuário (ajuste conforme necessário)
            if your_id is None and author_name:
                your_id = author_name
            
            if author_name == your_id:
                user_texts.append(content)
                pairs.append(("VOCÊ", content))
            elif author_name.lower() not in ["bot", "system"]:
                pairs.append(("AEON", content))
        
        self.language_profile.analyze(user_texts)
        return pairs
    
    def convert_simple(self, filepath):
        """Converte log simples (VOCÊ: / AEON:)."""
        pairs = []
        user_texts = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_role = None
        current_text = ""
        
        for line in lines:
            line = line.rstrip('\n')
            
            if line.startswith("VOCÊ:"):
                if current_text:
                    pairs.append((current_role, current_text))
                current_role = "VOCÊ"
                current_text = line.replace("VOCÊ:", "", 1).strip()
                user_texts.append(current_text)
            elif line.startswith("AEON:") or line.startswith("COPILOT:"):
                if current_text:
                    pairs.append((current_role, current_text))
                current_role = "AEON"
                current_text = line.replace("AEON:", "", 1).replace("COPILOT:", "", 1).strip()
            elif line and not line.startswith("#"):
                # Continua texto multilinhas
                current_text += " " + line.strip()
        
        if current_text:
            pairs.append((current_role, current_text))
        
        self.language_profile.analyze(user_texts)
        return pairs
    
    def convert_generic(self, filepath):
        """Converte log genérico com alternância de usuário/IA."""
        pairs = []
        user_texts = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        
        # Assume alternância: linha par = usuário, ímpar = IA
        for i in range(0, len(lines) - 1, 2):
            user_msg = lines[i]
            ai_msg = lines[i + 1]
            
            user_texts.append(user_msg)
            pairs.append(("VOCÊ", user_msg))
            pairs.append(("AEON", ai_msg))
        
        self.language_profile.analyze(user_texts)
        return pairs
    
    def convert(self, filepath):
        """Converte um arquivo para pares VOCÊ/AEON."""
        fmt = self.detect_format(filepath)
        print(f"Formato detectado: {fmt}")
        
        if fmt == "chatgpt":
            return self.convert_chatgpt(filepath)
        elif fmt == "claude":
            return self.convert_claude(filepath)
        elif fmt == "discord":
            return self.convert_discord(filepath)
        elif fmt == "simple":
            return self.convert_simple(filepath)
        else:
            return self.convert_generic(filepath)
    
    def to_jsonl(self, pairs):
        """Converte pares em JSONL para fine-tuning."""
        jsonl_lines = []
        
        for i in range(0, len(pairs) - 1, 2):
            if pairs[i][0] == "VOCÊ" and pairs[i + 1][0] == "AEON":
                jsonl_lines.append(json.dumps({
                    "user": pairs[i][1],
                    "assistant": pairs[i + 1][1]
                }, ensure_ascii=False))
        
        return "\n".join(jsonl_lines)
    
    def save_converted(self, pairs, output_path):
        """Salva pares em formato VOCÊ/AEON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for role, text in pairs:
                f.write(f"{role}: {text}\n")
        print(f"Salvo: {output_path}")
    
    def save_jsonl(self, jsonl_content, output_path):
        """Salva em formato JSONL."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(jsonl_content)
        print(f"Salvo (JSONL): {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Converte logs para formato AEON")
    parser.add_argument("--source", "-s", help="Arquivo/pasta de origem")
    parser.add_argument("--output", "-o", default="processed/dados_training.txt", 
                       help="Arquivo de saída (padrão: processed/dados_training.txt)")
    parser.add_argument("--jsonl", action="store_true", help="Também salva em JSONL")
    parser.add_argument("--profile", "-p", action="store_true", 
                       help="Mostra análise de padrões de linguagem")
    
    args = parser.parse_args()
    
    if not args.source:
        print("Use: python converter.py --source arquivo.json --output dados.txt")
        return
    
    converter = LogConverter()
    
    # Se é pasta, converte todos os arquivos
    if os.path.isdir(args.source):
        all_pairs = []
        files = list(Path(args.source).glob("*"))
        
        for f in files:
            if f.suffix in [".json", ".txt"]:
                print(f"\nProcessando: {f.name}")
                try:
                    pairs = converter.convert(str(f))
                    all_pairs.extend(pairs)
                    print(f"   {len(pairs)} pares extraídos")
                except Exception as e:
                    print(f"   Erro: {e}")
        
        pairs = all_pairs
    else:
        print(f"Processando: {args.source}")
        pairs = converter.convert(args.source)
    
    if not pairs:
        print("Nenhum par encontrado!")
        return
    
    # Salva em formato texto
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    converter.save_converted(pairs, args.output)
    
    # Salva em JSONL se solicitado
    if args.jsonl:
        jsonl_output = args.output.replace(".txt", ".jsonl")
        jsonl_content = converter.to_jsonl(pairs)
        converter.save_jsonl(jsonl_content, jsonl_output)
    
    # Mostra perfil de linguagem se solicitado
    if args.profile:
        print("\n" + "="*50)
        print("PERFIL DE LINGUAGEM DO USUÁRIO")
        print("="*50)
        print(converter.language_profile.to_system_prompt_addition())
        print("="*50)
    
    print(f"\nConversão completa! {len(pairs)} pares processados.")


if __name__ == "__main__":
    main()
