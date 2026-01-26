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

    # Define o caminho para o arquivo .env na raiz do projeto (assumindo que 'bagagem' está um nível abaixo da raiz)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, ".env")

    print("\n" + "-"*50)
    print("☁️  Configuração do Cérebro Nuvem (Groq)")
    print("-" * 50)
    print("\nℹ️  A chave da API do Groq agora é gerenciada por um arquivo .env na raiz do projeto.")
    print(f"   Isso torna sua chave mais segura.")
    print(f"\n📍 Local do arquivo: {dotenv_path}")
    
    print("\n📝 PARA CONFIGURAR SUA CHAVE:")
    print("   1. Abra o arquivo .env (se não existir, crie-o).")
    print("   2. Adicione ou edite a seguinte linha, substituindo com sua chave:")
    print('      GROQ_API_KEY="gsk_SUA_CHAVE_AQUI"')
    
    print("\n   O sistema irá carregar esta chave automaticamente ao iniciar.")
    print("   Você pode gerar uma chave em: https://console.groq.com/keys")

    # Tenta ler a chave apenas para mostrar o status
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        current_key = os.environ.get("GROQ_API_KEY")
        masked_key = f"{current_key[:8]}...{current_key[-4:]}" if current_key and len(current_key) > 10 else "NENHUMA/INVÁLIDA"
        print(f"\n🔑 Status da chave no .env: {masked_key}")
    except Exception as e:
        print(f"\n⚠️ Não consegui verificar a chave no .env. Certifique-se que o arquivo existe. Erro: {e}")
    
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