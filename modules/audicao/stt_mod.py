import threading
import speech_recognition as sr
from modules.base_module import AeonModule
import time

class STTModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Audicao"
        self.triggers = ["escuta passiva", "ativar escuta", "parar escuta", "dormir"]
        self.dependencies = ["gui", "io_handler", "context"]
        
        self.recognizer = sr.Recognizer()
        # Removido threshold de energia para confiar na calibragem automática, que é mais robusta.
        
        self.listening = False
        self.thread = None
        self.wake_word = "aeon"
        self.is_awake = False

    def on_load(self) -> bool:
        # Garante que PyAudio esteja instalado
        installer = self.core_context.get("installer")
        if installer:
            installer.check_pyaudio()
        return True

    def process(self, command: str) -> str:
        if "escuta passiva" in command or "ativar escuta" in command:
            if not self.listening:
                self.listening = True
                self.thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.thread.start()
                return "Escuta passiva iniciada."
            return "Já estou em modo de escuta."
        
        if "parar" in command:
            self.stop()
            return "Microfone desativado."
        
        if "dormir" in command:
            self.go_to_sleep()
            return "Ok, entrando em modo de espera."
        
        return ""

    def stop(self):
        self.listening = False
        self.is_awake = False

    def go_to_sleep(self):
        """Força o módulo a voltar para o modo de escuta passiva (dormir)."""
        if self.is_awake:
            print("[AUDIÇÃO] Recebido comando para dormir.")
            self.is_awake = False
            self.core_context.get("io_handler").play_feedback_sound('stop')
            gui = self.core_context.get("gui")
            if gui and self.listening:
                gui.after(0, lambda: gui.add_message(f"Ok, aguardando '{self.wake_word}'...", "AUDIÇÃO"))

    def _listen_loop(self):
        print("\n[AUDIÇÃO] Thread de escuta iniciada.")
        gui = self.core_context.get("gui")
        context = self.core_context.get("context")
        config_manager = self.core_context.get("config_manager")
        
        try:
            with sr.Microphone() as source:
                print("[AUDIÇÃO] Microfone aberto. Calibrando ruído ambiente...")
                if gui: gui.after(0, lambda: gui.add_message("Calibrando ruído...", "AUDIÇÃO"))
                self.recognizer.adjust_for_ambient_noise(source, duration=2) # Duração aumentada para melhor calibragem
                print(f"[AUDIÇÃO] Calibragem concluída. Energy threshold: {self.recognizer.energy_threshold:.2f}")
                
                if gui: gui.after(0, lambda: gui.add_message(f"Aguardando '{self.wake_word}'...", "AUDIÇÃO"))
                context.set("mic_active", True)
                
                while self.listening:
                    if not self.is_awake:
                        # --- MODO PASSIVO: OUVINDO O WAKE WORD ---
                        if gui: context.set('aeon_state', 'DORMINDO')
                        try:
                            audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                            texto = self.recognizer.recognize_google(audio, language="pt-BR").lower()
                            print(f"[AUDIÇÃO] Ouvido (Passivo): {texto}") # Debug para saber se o mic funciona
                            
                            # Carrega triggers dinamicamente da configuração + padrão
                            triggers = [self.wake_word]
                            if config_manager:
                                custom = config_manager.get_system_data("triggers")
                                if custom and isinstance(custom, list):
                                    triggers.extend([t.lower() for t in custom])

                            if any(t in texto for t in triggers):
                                print(f"[AUDIÇÃO] Wake word '{self.wake_word}' detectado!")
                                self.is_awake = True
                                if gui: context.set('aeon_state', 'OUVINDO')
                                self.core_context.get("io_handler").play_feedback_sound('start')
                                if gui:
                                    if hasattr(gui, 'wake_up'):
                                        gui.after(0, gui.wake_up)
                                    gui.after(0, lambda: gui.add_message("Ouvindo...", "AEON"))
                                
                        except sr.WaitTimeoutError:
                            continue
                        except sr.UnknownValueError:
                            continue
                        except Exception:
                            continue

                    else:
                        # --- MODO ATIVO: OUVINDO O COMANDO ---
                        if gui: context.set('aeon_state', 'OUVINDO')
                        try:
                            print("[AUDIÇÃO] Modo ativo, ouvindo comando...")
                            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                            
                            print("[AUDIÇÃO] Processando comando...")
                            if gui: context.set('aeon_state', 'PENSANDO')
                            texto_comando = self.recognizer.recognize_google(audio, language="pt-BR")
                            
                            if texto_comando:
                                print(f"[AUDIÇÃO] Comando: {texto_comando}")
                                if gui:
                                    gui.after(0, lambda t=texto_comando: gui.add_message(t, "VOCÊ"))
                                    # O comando para dormir é tratado aqui diretamente
                                    if texto_comando.lower() in ["vá dormir", "dormir", "pode dormir", "silêncio"]:
                                        self.go_to_sleep()
                                    else:
                                        gui.process_in_background(texto_comando)
                                # Após o comando, o loop continua no modo ativo, não volta a dormir.
                                    
                        except sr.WaitTimeoutError:
                            print("[AUDIÇÃO] Silêncio detectado. Voltando a dormir.")
                            if gui: gui.after(0, lambda: gui.add_message("Silêncio, voltando a aguardar.", "AUDIÇÃO"))
                            self.go_to_sleep() # Usa a nova função para dormir
                        except sr.UnknownValueError:
                            print("[AUDIÇÃO] Não entendi o comando. Tente novamente.")
                            if gui: gui.after(0, lambda: gui.add_message("Não entendi. Tente de novo.", "AUDIÇÃO"))
                            self.core_context.get("io_handler").play_feedback_sound('error')
                            # Permanece acordado para o usuário tentar de novo
                        except Exception as e:
                            print(f"[AUDIÇÃO] Erro no modo ativo: {e}")
                            self.go_to_sleep() # Em caso de erro, volta a dormir por segurança


        except Exception as e:
            print("="*50)
            print(f"[AUDIÇÃO] ERRO CRÍTICO: {e}")
            print(f"  └> Causa provável: Microfone não encontrado/permitido ou PyAudio ausente.")
            print(f"  └> Tente: pip install pyaudio")
            print("="*50)
            if gui: gui.after(0, lambda: gui.add_message("ERRO: Microfone inacessível.", "AUDIÇÃO"))
        finally:
            print("[AUDIÇÃO] Thread de escuta encerrada.")
            context.set("mic_active", False)
            self.listening = False
            self.is_awake = False