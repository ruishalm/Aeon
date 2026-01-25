import sys
import os
from pathlib import Path

# Adiciona o diretório atual ao path para conseguir importar os módulos
sys.path.append(os.getcwd())

try:
    from core.config_manager import ConfigManager
    
    print("\n=== DEBUG DO CAMINHO INTERNO ===")
    cm = ConfigManager()
    
    print(f"1. O código acha que a pasta bagagem é:\n   {cm.storage_path}")
    print(f"2. O código está a procurar o system.json em:\n   {cm.sys_path}")
    
    if cm.sys_path.exists():
        print("3. STATUS: ARQUIVO ENCONTRADO! ✅")
        # Vamos tentar ler a chave como o Brain faz
        data = cm.get_system_data("GROQ_KEY")
        print(f"4. Chave lida pelo ConfigManager: '{data}'")
        
        if data and str(data).startswith("gsk_"):
             print("5. CONCLUSÃO: A chave está perfeita. O erro é no Brain.py.")
        else:
             print("5. CONCLUSÃO: O arquivo existe, mas a chave está VAZIA ou com NOME ERRADO no JSON.")
    else:
        print("3. STATUS: ARQUIVO NÃO ENCONTRADO PELA APP ❌")
        print("   (Isso confirma que o config_manager.py ainda está com o código antigo/errado)")

except Exception as e:
    print(f"ERRO CRÍTICO AO IMPORTAR: {e}")

input("\nPressione Enter para fechar...")