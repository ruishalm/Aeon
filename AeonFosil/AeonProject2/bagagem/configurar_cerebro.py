import sys
import os
import subprocess
import urllib.request
import webbrowser

# Adiciona o diretório atual ao path para importar módulos internos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config_manager import ConfigManager

def setup():
    print("\n" + "="*50)
    print("🧠  CONFIGURAÇÃO DO CÉREBRO AEON")
    print("="*50)
    
    try:
        cm = ConfigManager()
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return

    print(f"\n📂 Arquivo de configuração: {cm.sys_path}")
    
    current_key = cm.get_system_data("GROQ_KEY")
    
    # AUTO-CORREÇÃO NO LOAD: Limpa a chave atual se estiver suja
    if current_key and isinstance(current_key, str):
        clean_current = current_key.replace('"', '').replace("'", "").strip()
        if "=" in clean_current and "gsk_" in clean_current:
            clean_current = clean_current.split("=")[-1].strip()
            
        if clean_current != current_key:
            current_key = clean_current
            cm.set_system_data("GROQ_KEY", current_key)
            print("🧹 Chave atual corrigida automaticamente (removido lixo de formatação).")

    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if current_key and len(current_key) > 10 else "NENHUMA/INVÁLIDA"
    print(f"🔑 Chave atual: {masked_key}")
    
    print("\n👉 Cole sua nova GROQ_KEY abaixo.")
    print("   (Pressione ENTER vazio para abrir o site e gerar uma nova chave)")
    new_key = input("> ").strip()
    
    if not new_key:
        print("\nℹ️  Nenhuma chave inserida. Mantendo a configuração atual.")
        return
    
    if new_key:
        # Remove aspas extras se você copiou errado (ex: "gsk_...")
        new_key = new_key.replace('"', '').replace("'", "")
        
        # Remove prefixo se o usuário copiou a linha inteira (ex: GROQ_KEY = gsk_...)
        if "=" in new_key:
            new_key = new_key.split("=")[-1].strip()
        
        if not new_key.startswith("gsk_"):
            print("⚠️  AVISO: Essa chave não parece uma chave Groq válida (deve começar com 'gsk_').")
            
        print("⏳ Testando chave com a Groq...")
        try:
            from groq import Groq
            client = Groq(api_key=new_key)
            client.models.list()
            print("✅ Chave VÁLIDA e funcionando!")
            cm.set_system_data("GROQ_KEY", new_key)
            print("✅ Chave salva com sucesso!")
        except Exception as e:
            print(f"❌ ERRO: Essa chave foi rejeitada pela Groq. Gere uma nova em https://console.groq.com/keys")
            print(f"   Detalhe do erro: {e}")
            print("   (A chave NÃO foi salva para evitar erros no sistema)")
            print("   🌍 Abrindo site para gerar nova chave...")
            webbrowser.open("https://console.groq.com/keys")
    else:
        print("ℹ️  Chave mantida.")
    
    print("\n" + "-"*50)
    print("🏠 Verificando Cérebro Local (Ollama)")
    print("-" * 50)
    
    try:
        # Tenta verificar se o servidor está rodando na porta padrão
        with urllib.request.urlopen("http://localhost:11434", timeout=2) as response:
            if response.status == 200:
                print("✅ Servidor Ollama está RODANDO e pronto!")
                
                print("\n📋 Modelos Instalados Atualmente:")
                try:
                    import ollama
                    mods = ollama.list()
                    for m in mods.get('models', []):
                        if isinstance(m, dict):
                            name = m.get('name') or m.get('model')
                        else:
                            name = getattr(m, 'name', getattr(m, 'model', str(m)))
                        print(f"   - {name}")
                except: print("   (Não foi possível listar via python, mas o servidor responde)")
                
                print("\n⬇️  Verificando/Baixando modelos de IA (Isso pode demorar)...")
                print("   Baixando 'llama3.2' (Cérebro de Texto)...")
                subprocess.run("ollama pull llama3.2", shell=True)
                
                print("   Baixando 'moondream' (Visão)...")
                subprocess.run("ollama pull moondream", shell=True)
                print("✅ Modelos instalados!")
            else:
                print("⚠️ Servidor Ollama respondeu, mas com status estranho.")
    except:
        print("❌ OLLAMA ESTÁ DESLIGADO!")
        print("   O aplicativo está instalado, mas não está rodando.")
        print("   👉 Abra o aplicativo 'Ollama' no menu Iniciar do Windows.")
        print("   👉 Você verá um ícone de lhama perto do relógio quando estiver pronto.")

    input("\n✅ Configuração concluída. Pressione Enter para fechar...")

if __name__ == "__main__":
    setup()