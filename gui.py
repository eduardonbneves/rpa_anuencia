import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import logging
import os
from dotenv import load_dotenv, find_dotenv

# Import the refactored main module
import main
try:
    from logger import PrefixFilter
except ImportError:
    # Fallback if logger module structure is different or complex to import
    PrefixFilter = None

class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""
    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        try:
            msg = self.format(record)
            def append():
                self.text.configure(state='normal')
                self.text.insert(tk.END, msg + '\n')
                self.text.configure(state='disabled')
                # Scroll to the bottom
                self.text.yview(tk.END)
            # This is necessary because we can't modify the GUI from other threads
            self.text.after(0, append)
        except Exception:
            self.handleError(record)

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RPA Anuencia - Gerenciador")
        self.geometry("600x700")
        
        # Variable to store credentials path
        self.credentials_path = tk.StringVar()
        
        # Threading control
        self.stop_event = threading.Event()
        self.execution_thread = None
        
        self.create_widgets()
        
        # Try to load default .env if it exists in current dir
        default_env = find_dotenv()
        if default_env:
            self.load_credentials(default_env)

    def create_widgets(self):
        # --- Header ---
        header_frame = tk.Frame(self, pady=10)
        header_frame.pack(fill=tk.X)
        lbl_title = tk.Label(header_frame, text="RPA Anuencia - Controle", font=("Helvetica", 16, "bold"))
        lbl_title.pack()

        # --- Credentials Section ---
        cred_frame = tk.LabelFrame(self, text="Configurações de Acesso (.env)", padx=10, pady=10)
        cred_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_cred_status = tk.Label(cred_frame, text="Nenhum arquivo carregado", fg="red")
        self.lbl_cred_status.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        btn_load_cred = tk.Button(cred_frame, text="Carregar Credenciais", command=self.choose_credentials)
        btn_load_cred.pack(side=tk.RIGHT)

        # --- Execution Section ---
        exec_frame = tk.LabelFrame(self, text="Execução", padx=10, pady=10)
        exec_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_start = tk.Button(exec_frame, text="Iniciar Habilitação", command=self.start_execution, bg="#e1eedd", height=2)
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        self.btn_stop = tk.Button(exec_frame, text="Parar", command=self.stop_execution, state=tk.DISABLED, bg="#ffebee", height=2)
        self.btn_stop.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)
        
        # --- Progress & Logs ---
        log_frame = tk.LabelFrame(self, text="Logs e Progresso", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(log_frame, mode='indeterminate')
        # pady=(0, 5) adiciona 0px no topo e 5px na parte inferior
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # --- Results ---
        result_frame = tk.LabelFrame(self, text="Renavams Liquidados", padx=10, pady=10)
        result_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)
        
        self.txt_result = tk.Text(result_frame, height=4)
        self.txt_result.pack(fill=tk.X)

        # Setup Logging redirection
        text_handler = TextHandler(self.log_area)
        
        if PrefixFilter:
            text_handler.addFilter(PrefixFilter())
            # Use format compatible with PrefixFilter
            log_fmt = "[%(asctime)s]%(prefix__formatted)s[%(levelname)s] %(message)s"
        else:
            log_fmt = "[%(asctime)s][%(levelname)s] %(message)s"

        text_handler.setFormatter(logging.Formatter(log_fmt))
        
        # Get the logger from main (or root logger) and add handler
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG) # Ensure we capture everything
        root_logger.addHandler(text_handler)


    def choose_credentials(self):
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo .env",
            filetypes=(("Env files", "*.env"), ("All files", "*.*"))
        )
        if filename:
            self.load_credentials(filename)

    def load_credentials(self, filepath):
        try:
            # Clear current env vars related to credentials to be sure ?? 
            # Actually dotenv overrides if we tell it to, or we can clear os.environ manually if needed.
            # For now just loading on top is usually fine for these simple scripts.
            load_dotenv(filepath, override=True)
            self.credentials_path.set(filepath)
            self.lbl_cred_status.config(text=f"Carregado: {os.path.basename(filepath)}", fg="green")
            self.log_msg(f"Credenciais carregadas de: {filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar .env: {e}")
            self.lbl_cred_status.config(text="Erro ao carregar", fg="red")

    def log_msg(self, msg):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, msg + '\n')
        self.log_area.configure(state='disabled')
        self.log_area.yview(tk.END)

    def start_execution(self):
        if not self.credentials_path.get() and not os.environ.get("GAE_USERNAME"):
             # Fallback check if env vars are already set globally even if file status isn't updated
             pass 
             
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.stop_event.clear()
        self.progress.start(10)
        self.txt_result.delete('1.0', tk.END)
        
        self.execution_thread = threading.Thread(target=self.run_rpa_thread)
        self.execution_thread.start()

    def stop_execution(self):
        if self.execution_thread and self.execution_thread.is_alive():
            self.log_msg("Solicitando parada... aguarde o término da operação atual.")
            self.stop_event.set()
        
    def run_rpa_thread(self):
        try:
            self.log_msg("Iniciando automação...")
            try:
                # We can allow the user to input renavams here too later if needed
                # For now using the default list from main.py as per request (no input fields required except creds)
                results = main.executar_teste(stop_event=self.stop_event)
                
                # Update results in GUI
                self.after(0, lambda: self.show_results(results))
                self.log_msg("Automação finalizada com sucesso.")
                
            except Exception as e:
                self.log_msg(f"Erro durante a execução: {e}")
                
        finally:
            self.after(0, self.reset_buttons)

    def show_results(self, results):
        if results:
            self.txt_result.insert(tk.END, ", ".join(results))
        else:
            self.txt_result.insert(tk.END, "Nenhum renavam liquidado encontrado ou execução interrompida.")

    def reset_buttons(self):
        self.progress.stop()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
