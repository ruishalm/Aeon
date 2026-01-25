import os
import subprocess
import re

def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Pula se for link simbólico
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_bytes):
    # Converte bytes para GB
    return size_bytes / (1024 * 1024 * 1024)

def get_ollama_stats():
    try:
        # Executa 'ollama list' para ver os modelos
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return 0, [], "Ollama não encontrado ou erro ao executar."

        total_gb = 0.0
        models_details = []
        lines = result.stdout.strip().split('\n')[1:] # Pula o cabeçalho

        for line in lines:
            # Procura padrões como "2.0 GB" ou "1700 MB"
            match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB)', line)
            if match:
                size_val = float(match.group(1))
                unit = match.group(2)
                
                size_in_gb = size_val if unit == "GB" else size_val / 1024
                total_gb += size_in_gb
                
                parts = line.split()
                name = parts[0] if parts else "Desconhecido"
                models_details.append(f"{name}: {size_in_gb:.2f} GB")

        return total_gb, models_details, None
    except Exception as e:
        return 0, [], str(e)

def main():
    print("\n" + "="*40)
    print("📊 CALCULADORA DE TAMANHO DO AEON")
    print("="*40)

    # 1. Tamanho do Projeto (Arquivos locais)
    project_path = os.path.dirname(os.path.abspath(__file__))
    project_bytes = get_folder_size(project_path)
    project_gb = format_size(project_bytes)
    print(f"\n📂 Pasta do Projeto: {project_gb:.4f} GB")
    print(f"   ({project_path})")

    # 2. Tamanho dos Cérebros (Ollama)
    ollama_gb, models, error = get_ollama_stats()
    print(f"\n🧠 Cérebros Locais (Ollama): {ollama_gb:.2f} GB")
    if error:
        print(f"   ⚠️ Erro ao ler Ollama: {error}")
    else:
        for m in models:
            print(f"   - {m}")

    # 3. Total
    total = project_gb + ollama_gb
    print("-" * 40)
    print(f"📦 TAMANHO TOTAL ESTIMADO: {total:.2f} GB")
    print("=" * 40)
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()