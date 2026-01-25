import os
import subprocess
import sys
import time

def log(texto):
    print(f"[BOOTLOADER] {texto}")

def verificar_atualizacoes():
    log("📡 Verificando conexão com a Nave Mãe (GitHub)...")
    
    try:
        # 1. Busca metadados do remoto sem baixar tudo
        subprocess.check_call(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Verifica se o HEAD local está atrás do HEAD remoto
        local = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
        remoto = subprocess.check_output(["git", "rev-parse", "@{u}"]).strip()
        
        if local != remoto:
            log("✨ Nova versão detectada! Baixando patches...")
            # Puxa as alterações (Patch Online)
            subprocess.check_call(["git", "pull"])
            log("✅ Código atualizado com sucesso.")
            return True
        else:
            log("✅ O Sistema está atualizado.")
            return False
            
    except Exception as e:
        log(f"⚠️ Não foi possível verificar atualizações (Modo Offline?): {e}")
        return False

def atualizar_dependencias():
    log("📦 Verificando bibliotecas (pip)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              stdout=subprocess.DEVNULL)
    except Exception as e:
        log(f"⚠️ Erro ao atualizar libs: {e}")

def iniciar_aeon():
    log("🚀 Inicializando Núcleo do Aeon...")
    log("="*30)
    # Inicia o main.py como um processo filho
    subprocess.call([sys.executable, "main.py"])

if __name__ == "__main__":
    print("\n--- AEON AUTO-UPDATER SYSTEM ---\n")
    
    # 1. Tenta se atualizar
    houve_update = verificar_atualizacoes()
    
    # 2. Se houve update, garante que as libs estão instaladas
    if houve_update:
        atualizar_dependencias()
    
    # 3. Inicia o sistema real
    time.sleep(1)
    iniciar_aeon()