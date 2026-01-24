import sys
import os
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("\n=== DIAGNÓSTICO AEON V85 ===")

# 1. Teste de Configuração
try:
    from core.config_manager import ConfigManager
    cm = ConfigManager()
    key = cm.get_system_data("GROQ_KEY")
    print(f"\n1. CONFIGURAÇÃO:")
    print(f"   Arquivo: {cm.sys_path}")
    print(f"   Chave Groq: {'OK (Começa com gsk_)' if key and str(key).startswith('gsk_') else '❌ INVÁLIDA/VAZIA'}")
    print(f"   Valor (parcial): {key[:10]}..." if key else "   Valor: VAZIO")
except Exception as e:
    print(f"❌ Erro ao ler configs: {e}")

# 2. Teste de Ollama (Local)
print(f"\n2. CÉREBRO LOCAL (Ollama):")
try:
    import ollama
    # Tenta listar modelos
    try:
        models = ollama.list()
        if 'models' in models:
            print(f"   ✅ Serviço Respondendo.")
            print(f"   📦 Modelos encontrados:")
            if not models['models']:
                print("      ❌ NENHUM MODELO INSTALADO! O download falhou ou não foi feito.")
            for m in models['models']:
                # Compatibilidade com versões diferentes do Ollama (dict ou objeto)
                if isinstance(m, dict):
                    name = m.get('name') or m.get('model') or "Desconhecido"
                else:
                    name = getattr(m, 'name', getattr(m, 'model', str(m)))
                print(f"      - {name}")
                
            # Teste de inferência simples se houver modelos
            if models['models']:
                m0 = models['models'][0]
                if isinstance(m0, dict):
                    mod_name = m0.get('name') or m0.get('model')
                else:
                    mod_name = getattr(m0, 'name', getattr(m0, 'model', str(m0)))
                print(f"   🧠 Testando pensamento com '{mod_name}'...")
                res = ollama.chat(model=mod_name, messages=[{'role':'user', 'content':'oi'}])
                print(f"   ✅ Resposta: {res['message']['content']}")
        else:
            print("   ⚠️ Serviço respondeu formato estranho.")
    except Exception as e:
        print(f"   ❌ Erro ao listar modelos: {e}")
        print("      Verifique se o servidor Ollama está rodando (ícone na bandeja do sistema).")

except ImportError:
    print("   ❌ Biblioteca 'ollama' não instalada no Python.")
except Exception as e:
    print(f"   ❌ OLLAMA NÃO DETECTADO: {e}")

# 3. Teste de Groq (Nuvem)
print(f"\n3. CÉREBRO NUVEM (Groq):")
try:
    from groq import Groq
    if key and str(key).startswith("gsk_"):
        client = Groq(api_key=key)
        client.models.list()
        print("   ✅ Conexão com Groq BEM SUCEDIDA!")
    else:
        print("   ⚠️ Pulei teste (sem chave válida).")
except Exception as e:
    print(f"   ❌ FALHA DE CONEXÃO: {e}")
    if "401" in str(e):
        print("      (Erro 401 = Chave incorreta)")

print("\n=== FIM DO DIAGNÓSTICO ===")
input("Pressione Enter para sair...")
