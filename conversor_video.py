import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import subprocess
import re
import sys
import json

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, radius=25, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.radius = radius
        
        # Cores atualizadas para o tema Radiance Ubuntu
        self.bg_color = "#2b2b2b"
        self.hover_color = "#3b3b3b"
        self.text_color = "white"
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        self.draw_button(text)
        
    def draw_button(self, text):
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Desenha o botão arredondado
        self.create_rounded_rect(0, 0, width, height, self.radius, fill=self.bg_color)
        
        # Adiciona o texto
        self.create_text(width/2, height/2, text=text, fill=self.text_color, font=("Ubuntu", 10, "bold"))
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def _on_enter(self, event):
        self.itemconfig(1, fill=self.hover_color)
        
    def _on_leave(self, event):
        self.itemconfig(1, fill=self.bg_color)
        
    def _on_click(self, event):
        if self.command:
            self.command()

def get_video_duration(path):
    """Retorna a duração do vídeo em segundos usando ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0

def get_video_subtitles(path):
    """Retorna as legendas disponíveis no vídeo usando ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 's',
            '-show_entries', 'stream=index:stream_tags=language,title',
            '-of', 'json', path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        subtitles = []
        data = json.loads(result.stdout)
        if 'streams' in data:
            for stream in data['streams']:
                subtitle = {
                    'index': stream['index'],
                    'language': stream['tags'].get('language', 'Unknown'),
                    'title': stream['tags'].get('title', '')
                }
                subtitles.append(subtitle)
        return subtitles
    except Exception as e:
        print(f"Erro ao detectar legendas: {e}")
        return []

class ConversorVideo:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Vídeo")
        self.root.geometry("1000x750")
        self.root.configure(bg="#1e1e1e")
        
        # Configuração do estilo Radiance Ubuntu
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Usando clam como base para o tema Radiance
        
        # Configuração das cores e estilos
        self.style.configure("Dark.TFrame", background="#1e1e1e")
        self.style.configure("Dark.TLabel", 
                           background="#1e1e1e", 
                           foreground="white",
                           font=("Ubuntu", 10))
        self.style.configure("Dark.TCombobox", 
                           background="#2b2b2b", 
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           arrowcolor="white",
                           font=("Ubuntu", 10))
        self.style.configure("Dark.Treeview", 
                           background="#2b2b2b", 
                           foreground="white", 
                           fieldbackground="#2b2b2b",
                           font=("Ubuntu", 10))
        self.style.configure("Dark.Treeview.Heading", 
                           background="#2b2b2b", 
                           foreground="white", 
                           font=("Ubuntu", 10, "bold"))
        self.style.map("Dark.Treeview.Heading", 
                      background=[("active", "#3b3b3b")])
        self.style.configure("Dark.Horizontal.TProgressbar", 
                           background="#00ff00", 
                           troughcolor="#2b2b2b",
                           borderwidth=0)
        
        # Variáveis
        self.caminho_saida = tk.StringVar()
        self.formato_saida = tk.StringVar(value="mp4")
        self.qualidade = tk.StringVar(value="Rápido")  # Nova variável para qualidade
        self.fila_videos = []
        self.conversao_ativa = False
        self.parar_conversao = False
        self.lbl_video_atual = None
        self.progresso = 0
        self.video_atual = ""
        self.process = None
        self.subtitle_selection = {}  # Dictionary to store selected subtitles for each video
        
        # Detectar hardware acceleration disponível
        self.hw_accel = self.detectar_hardware_acceleration()
        
        # Frame principal
        self.frame = ttk.Frame(root, style="Dark.TFrame", padding=30)
        self.frame.pack(expand=True, fill='both')
        
        # Widgets
        self.criar_widgets()
        
    def criar_widgets(self):
        titulo = ttk.Label(self.frame, 
                         text="Conversor de Vídeo", 
                         font=("Ubuntu", 20, "bold"), 
                         style="Dark.TLabel")
        titulo.pack(pady=(0, 20))
        frame_controles = ttk.Frame(self.frame, style="Dark.TFrame")
        frame_controles.pack(fill='x', pady=10)
        btn_adicionar = RoundedButton(frame_controles, "Adicionar Vídeos", command=self.adicionar_videos, width=200, height=40)
        btn_adicionar.pack(side='left', padx=(0, 10))
        
        # Frame para formato e qualidade
        frame_formato = ttk.Frame(frame_controles, style="Dark.TFrame")
        frame_formato.pack(side='left', padx=10)
        
        # Label e combobox para formato
        lbl_formato = ttk.Label(frame_formato, text="Formato de saída:", style="Dark.TLabel")
        lbl_formato.pack(side='left', padx=(0, 10))
        formatos = ["mp4", "avi", "mov", "mkv", "webm"]
        menu_formato = ttk.Combobox(frame_formato, textvariable=self.formato_saida, values=formatos, state="readonly", style="Dark.TCombobox")
        menu_formato.pack(side='left', padx=(0, 10))
        
        # Label e combobox para qualidade
        lbl_qualidade = ttk.Label(frame_formato, text="Qualidade:", style="Dark.TLabel")
        lbl_qualidade.pack(side='left', padx=(0, 10))
        qualidades = ["Rápido", "Média", "Alta"]
        menu_qualidade = ttk.Combobox(frame_formato, textvariable=self.qualidade, values=qualidades, state="readonly", style="Dark.TCombobox")
        menu_qualidade.pack(side='left')
        
        # Botão para selecionar pasta de saída
        btn_saida = RoundedButton(frame_controles, "Selecionar Pasta de Saída",
                                command=self.selecionar_pasta_saida,
                                width=200, height=40)
        btn_saida.pack(side='left', padx=10)
        
        # Frame para a lista de vídeos
        frame_lista = ttk.Frame(self.frame, style="Dark.TFrame")
        frame_lista.pack(fill='both', expand=True, pady=10)
        
        # Frame para treeview e scrollbar
        frame_tree = ttk.Frame(frame_lista, style="Dark.TFrame")
        frame_tree.pack(fill='both', expand=True)
        
        # Treeview para mostrar a fila de vídeos
        colunas = ("arquivo", "status", "legenda")
        self.tree = ttk.Treeview(frame_tree, columns=colunas, show="headings", style="Dark.Treeview")
        self.tree.heading("arquivo", text="Arquivo")
        self.tree.heading("status", text="Status")
        self.tree.heading("legenda", text="Legenda")
        self.tree.column("arquivo", width=300)
        self.tree.column("status", width=150)
        self.tree.column("legenda", width=150)
        self.tree.pack(side='left', fill='both', expand=True)
        
        # Adicionar evento de duplo clique para selecionar legenda
        self.tree.bind("<Double-1>", self.selecionar_legenda)
        
        # Scrollbar para a treeview
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Label para mostrar o vídeo atual
        self.lbl_video_atual = ttk.Label(self.frame, text="", style="Dark.TLabel")
        self.lbl_video_atual.pack(pady=(0, 5))
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=100, mode="determinate", style="Dark.Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        self.lbl_progresso = ttk.Label(self.frame, text="", style="Dark.TLabel")
        self.lbl_progresso.pack(pady=(0, 5))
        
        # Frame para botões de controle
        frame_botoes = ttk.Frame(self.frame, style="Dark.TFrame")
        frame_botoes.pack(fill='x', pady=10)
        
        # Botão para remover vídeo selecionado
        btn_remover = RoundedButton(frame_botoes, "Remover Selecionado",
                                  command=self.remover_selecionado,
                                  width=200, height=40)
        btn_remover.pack(side='left', padx=10)
        
        # Botão para limpar fila
        btn_limpar = RoundedButton(frame_botoes, "Limpar Fila",
                                 command=self.limpar_fila,
                                 width=200, height=40)
        btn_limpar.pack(side='left', padx=10)
        
        # Botão de conversão
        self.btn_converter = RoundedButton(frame_botoes, "Iniciar Conversão",
                                    command=self.iniciar_conversao,
                                    width=200, height=40)
        self.btn_converter.pack(side='right', padx=10)
        
        # Botão para parar conversão
        self.btn_parar = RoundedButton(frame_botoes, "Parar Conversão",
                                    command=self.parar_conversao_processo,
                                    width=200, height=40)
        self.btn_parar.pack(side='right', padx=10)
        self.btn_parar.configure(state='disabled')  # Inicialmente desabilitado
        
    def atualizar_progresso(self, progresso):
        self.progresso = progresso
        self.progress_bar["value"] = progresso
        self.root.update_idletasks()
        
    def adicionar_videos(self):
        arquivos = filedialog.askopenfilenames(
            title="Selecione os vídeos",
            filetypes=[
                ("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if arquivos:
            for arquivo in arquivos:
                self.fila_videos.append({
                    "caminho": arquivo,
                    "status": "Na fila"
                })
                # Adicionar à treeview
                self.tree.insert("", "end", values=(os.path.basename(arquivo), "Na fila", "Sem legenda"))
                # Inicializar sem legenda selecionada
                self.subtitle_selection[arquivo] = None
                
    def selecionar_pasta_saida(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta de saída")
        if pasta:
            self.caminho_saida.set(pasta)
            
    def remover_selecionado(self):
        selecionado = self.tree.selection()
        if selecionado:
            index = self.tree.index(selecionado[0])
            self.tree.delete(selecionado[0])
            self.fila_videos.pop(index)
            
    def limpar_fila(self):
        self.tree.delete(*self.tree.get_children())
        self.fila_videos.clear()
        
    def atualizar_status(self, index, status):
        self.fila_videos[index]["status"] = status
        self.tree.set(self.tree.get_children()[index], "status", status)
        
    def detectar_hardware_acceleration(self):
        """Detecta se há suporte a hardware acceleration disponível."""
        try:
            result = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if 'h264_nvenc' in result.stdout:
                return 'nvenc'
            # VAAPI só em sistemas Linux
            if sys.platform != 'win32' and 'h264_vaapi' in result.stdout:
                return 'vaapi'
            return None
        except Exception:
            return None

    def get_bitrates(self):
        """Retorna os bitrates de vídeo e áudio baseados na qualidade selecionada."""
        qualidade = self.qualidade.get()
        if qualidade == "Alta":
            return '5000k', '256k'
        elif qualidade == "Média":
            return '2500k', '192k'
        else:  # Rápido
            return '1500k', '128k'
        
    def parar_conversao_processo(self):
        if self.conversao_ativa and self.process:
            self.parar_conversao = True
            self.process.terminate()
            self.atualizar_status(self.fila_videos.index(self.video_atual), "Interrompido")
            self.conversao_ativa = False
            self.btn_converter.configure(state='normal')
            self.btn_parar.configure(state='disabled')
            self.lbl_video_atual.config(text="Conversão interrompida")
            self.progress_bar["value"] = 0
            self.lbl_progresso.config(text="")

    def selecionar_legenda(self, event):
        item = self.tree.selection()[0]
        index = self.tree.index(item)
        video_path = self.fila_videos[index]["caminho"]
        
        # Obter legendas disponíveis
        subtitles = get_video_subtitles(video_path)
        
        if not subtitles:
            messagebox.showinfo("Legendas", "Nenhuma legenda encontrada neste vídeo.")
            return
        
        # Criar janela de seleção de legenda
        subtitle_window = tk.Toplevel(self.root)
        subtitle_window.title("Selecionar Legenda")
        subtitle_window.geometry("400x300")
        subtitle_window.configure(bg="#1e1e1e")
        
        # Lista de legendas
        subtitle_list = tk.Listbox(subtitle_window, bg="#2b2b2b", fg="white", font=("Ubuntu", 10))
        subtitle_list.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Adicionar opção "Sem legenda"
        subtitle_list.insert(0, "Sem legenda")
        
        # Adicionar legendas disponíveis
        for i, sub in enumerate(subtitles):
            display_text = f"{sub['language']}"
            if sub['title']:
                display_text += f" - {sub['title']}"
            subtitle_list.insert(tk.END, display_text)
        
        def on_select():
            selection = subtitle_list.curselection()
            if selection:
                selected_index = selection[0]
                if selected_index == 0:  # "Sem legenda"
                    self.subtitle_selection[video_path] = None
                    self.tree.set(item, "legenda", "Sem legenda")
                else:
                    # Salvar o índice da lista, não o stream['index']
                    self.subtitle_selection[video_path] = selected_index - 1
                    self.tree.set(item, "legenda", f"Legenda {selected_index - 1}")
            subtitle_window.destroy()
        
        # Botão de seleção
        btn_select = RoundedButton(subtitle_window, "Selecionar", command=on_select, width=150, height=40)
        btn_select.pack(pady=10)

    def converter_video(self, index):
        if not self.caminho_saida.get():
            messagebox.showerror("Erro", "Por favor, selecione a pasta de saída")
            return
            
        video_info = self.fila_videos[index]
        try:
            self.atualizar_status(index, "Convertendo...")
            self.video_atual = video_info
            self.lbl_video_atual.config(text=f"Convertendo: {os.path.basename(video_info['caminho'])}")
            self.root.update_idletasks()
            nome_arquivo = os.path.splitext(os.path.basename(video_info["caminho"]))[0]
            pasta_saida = self.caminho_saida.get().replace('\\', '/').replace('\\', '/')
            caminho_completo = os.path.join(pasta_saida, f"{nome_arquivo}.{self.formato_saida.get()}").replace('\\', '/').replace('\\', '/')
            v_bitrate, a_bitrate = self.get_bitrates()
            duracao = get_video_duration(video_info["caminho"])

            def run_ffmpeg(cmd):
                print('Comando FFmpeg:', ' '.join(cmd))
                if sys.platform == "win32":
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                tempo_atual = 0
                ffmpeg_output = []
                for line in self.process.stdout:
                    ffmpeg_output.append(line)
                    if self.parar_conversao:
                        self.process.terminate()
                        break
                    if 'out_time_ms=' in line:
                        try:
                            out_time_ms = int(line.split('=')[1].strip())
                            tempo_atual = out_time_ms / 1000000
                            if duracao > 0:
                                progresso = (tempo_atual / duracao) * 100
                                self.progress_bar["value"] = progresso
                                self.lbl_progresso.config(text=f"Progresso: {int(progresso)}%  ({int(tempo_atual)}/{int(duracao)}s)")
                                self.root.update_idletasks()
                        except (ValueError, IndexError):
                            continue
                self.process.wait()
                return ffmpeg_output

            # Primeira tentativa: usar NVENC se disponível
            cmd = ['ffmpeg', '-y', '-i', video_info["caminho"]]
            nvenc_usado = False
            
            # Adicionar filtro de subtítulos se uma legenda foi selecionada
            if video_info["caminho"] in self.subtitle_selection and self.subtitle_selection[video_info["caminho"]] is not None:
                subtitle_index = self.subtitle_selection[video_info["caminho"]]
                # Escapar caminho para o filtro subtitles (Windows)
                video_path_escaped = video_info["caminho"].replace('\\', '/').replace(':', '\\:')
                # Colocar entre aspas simples se houver espaço
                if ' ' in video_path_escaped:
                    video_path_escaped = f"'{video_path_escaped}'"
                # Verificar se há mais de uma legenda
                subtitles = get_video_subtitles(video_info["caminho"])
                if len(subtitles) > 1:
                    cmd.extend(['-vf', f"subtitles={video_path_escaped}:si={subtitle_index}"])
                else:
                    cmd.extend(['-vf', f"subtitles={video_path_escaped}"])
            
            if self.hw_accel == 'nvenc':
                cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p1'])
                nvenc_usado = True
            elif self.hw_accel == 'vaapi' and sys.platform != 'win32':
                cmd.extend(['-vaapi_device', '/dev/dri/renderD128', '-c:v', 'h264_vaapi'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast'])
            
            # Parâmetros de compatibilidade
            cmd.extend([
                '-profile:v', 'high',
                '-level', '4.1',
                '-pix_fmt', 'yuv420p',
                '-g', '48',
                '-b:v', v_bitrate,
                '-c:a', 'aac',
                '-b:a', a_bitrate,
                '-movflags', '+faststart',
                '-progress', 'pipe:1',
                caminho_completo
            ])
            ffmpeg_output = run_ffmpeg(cmd)

            # Se NVENC foi usado e falhou, tenta fallback para libx264
            if nvenc_usado and (not os.path.exists(caminho_completo) or os.path.getsize(caminho_completo) == 0 or any('h264_nvenc' in l and ('error' in l.lower() or 'not supported' in l.lower() or 'no capable devices' in l.lower()) for l in ffmpeg_output)):
                # Remove arquivo vazio/corrompido
                if os.path.exists(caminho_completo):
                    try:
                        os.remove(caminho_completo)
                    except:
                        pass
                # Tenta novamente com libx264 (sem popup)
                cmd2 = ['ffmpeg', '-y', '-i', video_info["caminho"]]
                
                # Adicionar filtro de subtítulos novamente
                if video_info["caminho"] in self.subtitle_selection and self.subtitle_selection[video_info["caminho"]] is not None:
                    subtitle_index = self.subtitle_selection[video_info["caminho"]]
                    video_path_escaped = video_info["caminho"].replace('\\', '/').replace(':', '\\:')
                    if ' ' in video_path_escaped:
                        video_path_escaped = f"'{video_path_escaped}'"
                    subtitles = get_video_subtitles(video_info["caminho"])
                    if len(subtitles) > 1:
                        cmd2.extend(['-vf', f"subtitles={video_path_escaped}:si={subtitle_index}"])
                    else:
                        cmd2.extend(['-vf', f"subtitles={video_path_escaped}"])
                
                cmd2.extend(['-c:v', 'libx264', '-preset', 'ultrafast',
                        '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p', '-g', '48',
                        '-b:v', v_bitrate, '-c:a', 'aac', '-b:a', a_bitrate, '-movflags', '+faststart', '-progress', 'pipe:1', caminho_completo])
                ffmpeg_output = run_ffmpeg(cmd2)

            if not self.parar_conversao:
                if os.path.exists(caminho_completo) and os.path.getsize(caminho_completo) > 0:
                    self.progress_bar["value"] = 100
                    self.lbl_progresso.config(text="Progresso: 100%")
                    self.atualizar_status(index, "Concluído")
                    self.lbl_video_atual.config(text="")
                else:
                    messagebox.showerror("Erro FFmpeg", "Arquivo de saída não foi criado ou está vazio.\n\nSaída do FFmpeg:\n" + ''.join(ffmpeg_output)[-2000:])
                    raise Exception("Arquivo de saída não foi criado ou está vazio. Veja detalhes no popup.")
        except Exception as e:
            self.atualizar_status(index, f"Erro: {str(e)}")
            self.lbl_video_atual.config(text="")
            self.progress_bar["value"] = 0
            self.lbl_progresso.config(text="")
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except:
                    pass

    def processar_fila(self):
        self.parar_conversao = False
        for i in range(len(self.fila_videos)):
            if self.parar_conversao:
                break
            if self.fila_videos[i]["status"] == "Na fila":
                self.converter_video(i)
        self.conversao_ativa = False
        self.btn_converter.configure(state='normal')
        self.btn_parar.configure(state='disabled')
        self.progress_bar["value"] = 0
        self.lbl_progresso.config(text="")
        
    def iniciar_conversao(self):
        if not self.fila_videos:
            messagebox.showwarning("Aviso", "A fila está vazia")
            return
        if not self.caminho_saida.get():
            messagebox.showerror("Erro", "Por favor, selecione a pasta de saída")
            return
        if not self.formato_saida.get() or self.formato_saida.get() not in ["mp4", "avi", "mov", "mkv", "webm"]:
            messagebox.showerror("Erro", "Por favor, selecione o formato de saída antes de converter.")
            return
        if not self.conversao_ativa:
            self.conversao_ativa = True
            self.btn_converter.configure(state='disabled')
            self.btn_parar.configure(state='normal')
            threading.Thread(target=self.processar_fila, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConversorVideo(root)
    root.mainloop() 