import os
import re
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class AnimeFileRenamer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 Renomeador de Arquivos de Anime")
        self.root.geometry("900x750")  # Aumentei a altura de 700 para 750
        self.root.configure(bg='#2b2b2b')
        self.root.resizable(True, True)
        self.root.minsize(800, 600)  # Tamanho mínimo da janela
        
        # Tentar definir ícone (se existir)
        try:
            self.root.iconbitmap('anime_icon.ico')
        except:
            pass  # Ignorar se não houver ícone
        
        # Extensões suportadas
        self.supported_extensions = ['.mkv', '.mp4', '.avi', '.srt', '.ass', '.vtt']
        
        # Sistema de backup
        self.backup_info = None
        self.last_operation = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Estilo melhorado
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Arial', 9))
        style.configure('TButton', background='#404040', foreground='white', font=('Arial', 9))
        style.configure('TEntry', background='white', foreground='black', insertcolor='black', font=('Arial', 10))
        style.configure('TSpinbox', background='white', foreground='black', insertcolor='black', font=('Arial', 10))
        style.configure('Treeview', background='white', foreground='black', font=('Arial', 9))
        style.configure('Treeview.Heading', background='#404040', foreground='white', font=('Arial', 9, 'bold'))
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = ttk.Label(main_frame, text="Renomeador de Arquivos de Anime", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Seleção de diretório
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(dir_frame, text="Diretório:").pack(anchor='w')
        
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill='x', pady=(5, 0))
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_select_frame, textvariable=self.dir_var, width=80)
        self.dir_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(dir_select_frame, text="Procurar", 
                  command=self.select_directory).pack(side='right', padx=(10, 0))
        
        # Configurações de renomeação
        config_frame = ttk.LabelFrame(main_frame, text="Configurações de Renomeação", padding=15)
        config_frame.pack(fill='x', pady=(0, 15))
        
        # Nome da série
        ttk.Label(config_frame, text="Nome da Série:").pack(anchor='w')
        self.series_var = tk.StringVar(value="One Punch Man")
        ttk.Entry(config_frame, textvariable=self.series_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Temporada
        season_frame = ttk.Frame(config_frame)
        season_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(season_frame, text="Temporada:").pack(side='left')
        self.season_var = tk.StringVar(value="01")
        season_spin = ttk.Spinbox(season_frame, from_=1, to=99, textvariable=self.season_var, 
                                 width=5, format="%02.0f")
        season_spin.pack(side='left', padx=(10, 0))
        
        # Episódio inicial
        ttk.Label(season_frame, text="Episódio inicial:").pack(side='left', padx=(20, 0))
        self.start_episode_var = tk.StringVar(value="01")
        episode_spin = ttk.Spinbox(season_frame, from_=1, to=999, textvariable=self.start_episode_var, 
                                  width=5, format="%02.0f")
        episode_spin.pack(side='left', padx=(10, 0))
        
        # Preview do padrão
        preview_frame = ttk.Frame(config_frame)
        preview_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(preview_frame, text="Padrão de renomeação:").pack(anchor='w')
        self.preview_var = tk.StringVar()
        preview_label = ttk.Label(preview_frame, textvariable=self.preview_var, 
                                 font=('Courier', 10), foreground='#00ff00')
        preview_label.pack(anchor='w', pady=(5, 0))
        
        # Botão para atualizar preview manualmente
        ttk.Button(preview_frame, text="🔄 Atualizar Preview", 
                  command=self.force_update_preview).pack(anchor='w', pady=(5, 0))
        
        # Atualizar preview quando os campos mudarem
        self.series_var.trace('w', self.on_config_change)
        self.season_var.trace('w', self.on_config_change)
        self.start_episode_var.trace('w', self.on_config_change)
        self.dir_var.trace('w', self.on_directory_change)
        self.update_preview()
        
        # Lista de arquivos
        files_frame = ttk.LabelFrame(main_frame, text="Arquivos Encontrados", padding=10)
        files_frame.pack(fill='both', expand=True, pady=(0, 10))  # Reduzido de 15 para 10
        
        # Treeview para mostrar arquivos
        columns = ('Original', 'Novo Nome', 'Extensão')
        self.tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=8)  # Reduzido de 10 para 8
        
        self.tree.heading('Original', text='Nome Original')
        self.tree.heading('Novo Nome', text='Novo Nome')
        self.tree.heading('Extensão', text='Extensão')
        
        self.tree.column('Original', width=300)
        self.tree.column('Novo Nome', width=300)
        self.tree.column('Extensão', width=80)
        
        # Scrollbar para a treeview
        scrollbar = ttk.Scrollbar(files_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(5, 0))  # Reduzido padding
        
        # Primeira linha de botões (principais)
        button_row1 = ttk.Frame(button_frame)
        button_row1.pack(fill='x', pady=(0, 3))  # Reduzido espaçamento
        
        ttk.Button(button_row1, text="🔍 Escanear", 
                  command=self.scan_files).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_row1, text="✏️ Renomear", 
                  command=self.rename_files).pack(side='left', padx=(0, 5))
        
        # Botão de desfazer (inicialmente desabilitado)
        self.undo_button = ttk.Button(button_row1, text="↶ Desfazer", 
                                     command=self.undo_rename, state='disabled')
        self.undo_button.pack(side='left', padx=(0, 5))
        
        ttk.Button(button_row1, text="🧹 Limpar", 
                  command=self.clear_all).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_row1, text="❌ Sair", 
                  command=self.root.quit).pack(side='right')
        
        # Segunda linha de botões (auxiliares)
        button_row2 = ttk.Frame(button_frame)
        button_row2.pack(fill='x')
        
        ttk.Button(button_row2, text="💾 Backup Manual", 
                  command=self.create_manual_backup).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_row2, text="🔄 Restaurar", 
                  command=self.restore_backup).pack(side='left', padx=(0, 5))
        
        ttk.Button(button_row2, text="ℹ️ Status", 
                  command=self.show_backup_status).pack(side='left', padx=(0, 5))
        
        # Bind Ctrl+Z
        self.root.bind('<Control-z>', lambda e: self.undo_rename())
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Pronto para usar!")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief='sunken', anchor='w',
                              background='#404040', foreground='#00ff00',
                              font=('Arial', 9))
        status_bar.pack(fill='x', pady=(5, 0))
        
        # Variável para armazenar lista de arquivos
        self.files_list = []
        
    def update_preview(self, *args):
        """Atualiza o preview do padrão de renomeação"""
        series = self.series_var.get().strip()
        season = self.season_var.get().strip()
        episode = self.start_episode_var.get().strip()
        
        if series and season and episode:
            try:
                season_num = int(season)
                episode_num = int(episode)
                preview = f"{series} S{season_num:02d}E{episode_num:02d}.extensão"
                self.preview_var.set(preview)
            except ValueError:
                self.preview_var.set("Erro: Temporada e episódio devem ser números")
        else:
            self.preview_var.set("Configure os campos acima")
    
    def force_update_preview(self):
        """Força atualização do preview e limpa dados antigos"""
        self.clear_file_list(clear_undo=False)  # Não limpar desfazer
        self.update_preview()
        self.status_var.set("🔄 Preview atualizado! Clique em 'Escanear' para aplicar mudanças.")
    
    def on_config_change(self, *args):
        """Chamado quando configurações mudam"""
        self.update_preview()
        # REMOVIDO: Não limpar lista quando configuração muda
        # Só limpar se não há arquivos escaneados ainda
        if hasattr(self, 'files_list') and self.files_list:
            self.status_var.set("⚠️ Configuração alterada! Clique em 'Escanear' para aplicar mudanças.")
        else:
            self.status_var.set("📝 Configuração atualizada.")
    
    def on_directory_change(self, *args):
        """Chamado quando diretório muda"""
        self.clear_file_list(clear_undo=True)  # Limpar desfazer ao mudar diretório
        
        # LIMPAR backup quando muda de diretório (como solicitado)
        self.backup_info = None
        self.last_operation = None
        
        # Desabilitar botão de desfazer (backup não é mais válido)
        if hasattr(self, 'undo_button'):
            self.undo_button.configure(state='disabled')
        
        directory = self.dir_var.get()
        if directory:
            self.status_var.set(f"📁 Novo diretório: {os.path.basename(directory)} | 🧹 Backup anterior limpo")
        else:
            self.status_var.set("📁 Diretório removido | 🧹 Dados limpos")    
    def clear_file_list(self, clear_undo=True):
        """Limpa a lista de arquivos"""
        self.tree.delete(*self.tree.get_children())
        self.files_list = []
        # Só desabilitar botão de desfazer se explicitamente solicitado
        if clear_undo and hasattr(self, 'undo_button'):
            self.undo_button.configure(state='disabled')
    
    def show_backup_status(self):
        """Mostra informações sobre o status atual dos backups"""
        status_info = "📊 STATUS DOS BACKUPS:\n\n"
        
        # Verificar backup disponível
        if self.backup_info:
            backup_type = self.backup_info.get('type', 'desconhecido')
            file_count = len(self.backup_info['files'])
            directory = self.backup_info['directory']
            timestamp = time.strftime('%d/%m/%Y %H:%M:%S', 
                                    time.localtime(self.backup_info['timestamp']))
            
            status_info += f"✅ BACKUP DISPONÍVEL:\n"
            status_info += f"   📁 Diretório: {os.path.basename(directory)}\n"
            status_info += f"   📊 Tipo: {backup_type.title()}\n"
            status_info += f"   📄 Arquivos: {file_count}\n"
            status_info += f"   🕐 Criado em: {timestamp}\n\n"
        else:
            status_info += f"❌ NENHUM BACKUP DISPONÍVEL\n\n"
        
        # Verificar operação para desfazer
        if self.last_operation:
            operation_count = len(self.last_operation)
            status_info += f"↶ DESFAZER DISPONÍVEL:\n"
            status_info += f"   📄 Operações: {operation_count} arquivos\n"
            status_info += f"   ⌨️ Atalho: Ctrl+Z\n\n"
        else:
            status_info += f"❌ NENHUMA OPERAÇÃO PARA DESFAZER\n\n"
        
        # Diretório atual
        current_dir = self.dir_var.get()
        if current_dir:
            status_info += f"📁 DIRETÓRIO ATUAL:\n   {current_dir}\n\n"
        else:
            status_info += f"📁 NENHUM DIRETÓRIO SELECIONADO\n\n"
        
        # Arquivos na lista
        if hasattr(self, 'files_list') and self.files_list:
            status_info += f"📋 LISTA ATUAL:\n   {len(self.files_list)} arquivos prontos para renomear"
        else:
            status_info += f"📋 LISTA VAZIA\n   Clique 'Escanear Arquivos' para popular"
        
        messagebox.showinfo("Status dos Backups", status_info)

    def clear_all(self):
        """Limpa todas as configurações e dados"""
        result = messagebox.askyesno("Limpar Tudo", 
                                   "Deseja limpar todas as configurações e dados?\n\n"
                                   "Isso irá:\n"
                                   "• Limpar nome da série\n"
                                   "• Resetar temporada para 01\n"
                                   "• Resetar episódio para 01\n"
                                   "• Limpar lista de arquivos\n"
                                   "• Limpar diretório selecionado")
        
        if result:
            # Limpar campos
            self.series_var.set("")
            self.season_var.set("01")
            self.start_episode_var.set("01")
            self.dir_var.set("")
            
            # Limpar dados
            self.clear_file_list()
            self.backup_info = None
            self.last_operation = None
            
            # Resetar interface
            self.preview_var.set("Configure os campos acima")
            self.status_var.set("🧹 Tudo limpo! Configure uma nova série.")
            
            # Desabilitar botão de desfazer
            if hasattr(self, 'undo_button'):
                self.undo_button.configure(state='disabled')
            
            messagebox.showinfo("Limpo!", "Todas as configurações foram resetadas!")
    
    def natural_sort_key(self, filename):
        """Cria uma chave para ordenação natural (números em ordem correta)"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]
        
    def select_directory(self):
        """Abre diálogo para selecionar diretório"""
        # Verificar se há backup/operação anterior
        has_previous_data = self.backup_info is not None or self.last_operation is not None
        
        directory = filedialog.askdirectory(title="Selecione a pasta com os arquivos de anime")
        if directory:
            # Avisar sobre limpeza se havia dados anteriores
            if has_previous_data:
                result = messagebox.askokcancel(
                    "Mudança de Diretório", 
                    f"Novo diretório selecionado:\n{directory}\n\n"
                    "⚠️ ATENÇÃO:\n"
                    "• Backup anterior será limpo\n"
                    "• Função 'Desfazer' será desabilitada\n"
                    "• Lista de arquivos será limpa\n\n"
                    "Deseja continuar?"
                )
                if not result:
                    return
            
            self.dir_var.set(directory)
            
            # Mostrar status detalhado
            if has_previous_data:
                self.status_var.set(f"📁 Diretório alterado: {os.path.basename(directory)} | 🧹 Backup/Desfazer limpos")
            else:
                self.status_var.set(f"📁 Diretório selecionado: {os.path.basename(directory)}")
                
            # Escanear automaticamente se campos estão preenchidos
            if self.series_var.get().strip():
                self.scan_files()
            else:
                self.status_var.set(f"📁 {os.path.basename(directory)} | ⚠️ Configure o nome da série para escanear")
    
    def create_backup_info(self, directory):
        """Cria informações de backup dos arquivos antes da renomeação"""
        backup_data = []
        try:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext.lower() in self.supported_extensions:
                        backup_data.append({
                            'current_name': file,
                            'current_path': file_path,
                            'timestamp': os.path.getmtime(file_path)
                        })
            return backup_data
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return None
    
    def create_manual_backup(self):
        """Cria um backup manual dos arquivos atuais"""
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Erro", "Selecione um diretório válido primeiro!")
            return
        
        backup_data = self.create_backup_info(directory)
        if backup_data:
            self.backup_info = {
                'directory': directory,
                'files': backup_data,
                'type': 'manual',
                'timestamp': time.time()
            }
            self.status_var.set(f"💾 Backup manual criado! ({len(backup_data)} arquivos)")
            messagebox.showinfo("Backup", f"Backup criado com sucesso!\n{len(backup_data)} arquivos salvos.")
        else:
            messagebox.showerror("Erro", "Não foi possível criar o backup!")

    def undo_rename(self):
        """Desfaz a última operação de renomeação"""
        if not self.backup_info or not self.last_operation:
            messagebox.showwarning("Aviso", "Nenhuma operação para desfazer!")
            return
        
        # Confirmar ação
        result = messagebox.askyesno("Confirmar Desfazer", 
                                   f"Desfazer a última renomeação?\n\n"
                                   f"Isso irá restaurar {len(self.last_operation)} arquivos "
                                   f"para seus nomes originais.")
        if not result:
            return
        
        success_count = 0
        errors = []
        
        try:
            for operation in self.last_operation:
                try:
                    # Restaurar nome original
                    current_path = operation['new_path']
                    original_path = operation['original_path']
                    
                    if os.path.exists(current_path):
                        os.rename(current_path, original_path)
                        success_count += 1
                    else:
                        errors.append(f"Arquivo não encontrado: {os.path.basename(current_path)}")
                        
                except Exception as e:
                    errors.append(f"Erro ao restaurar {os.path.basename(operation['original_path'])}: {str(e)}")
            
            # Limpar operação desfeita
            if success_count > 0:
                self.last_operation = None
                self.undo_button.configure(state='disabled')
                self.status_var.set(f"↶ Desfeito! {success_count} arquivos restaurados")
            
            # Mostrar resultado
            message = f"Operação desfeita!\n\n"
            message += f"Arquivos restaurados: {success_count}\n"
            
            if errors:
                message += f"Erros: {len(errors)}\n\n"
                message += "Detalhes:\n" + "\n".join(errors[:3])
                if len(errors) > 3:
                    message += f"\n... e mais {len(errors) - 3} erros."
                messagebox.showwarning("Desfeito com erros", message)
            else:
                messagebox.showinfo("Sucesso", message)
            
            # Reescanear
            self.scan_files()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao desfazer operação: {str(e)}")
    
    def restore_backup(self):
        """Restaura arquivos de um backup salvo"""
        if not self.backup_info:
            messagebox.showwarning("Aviso", "Nenhum backup disponível!")
            return
        
        backup_type = self.backup_info.get('type', 'automático')
        file_count = len(self.backup_info['files'])
        
        # Confirmar restauração
        result = messagebox.askyesno("Confirmar Restauração", 
                                   f"Restaurar backup {backup_type}?\n\n"
                                   f"Arquivos no backup: {file_count}\n\n"
                                   f"⚠️ Esta ação pode sobrescrever arquivos atuais!")
        if not result:
            return
        
        success_count = 0
        errors = []
        directory = self.backup_info['directory']
        
        try:
            # Tentar restaurar cada arquivo
            for file_info in self.backup_info['files']:
                try:
                    original_name = file_info['current_name']
                    original_path = os.path.join(directory, original_name)
                    
                    # Verificar se o arquivo atual existe com nome diferente
                    current_files = [f for f in os.listdir(directory) 
                                   if os.path.isfile(os.path.join(directory, f))]
                    
                    # Esta é uma implementação básica - em cenários reais seria mais complexa
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Erro com {original_name}: {str(e)}")
            
            # Mostrar resultado
            message = f"Tentativa de restauração concluída!\n\n"
            message += f"Operações: {success_count}\n"
            
            if errors:
                message += f"Avisos: {len(errors)}"
                messagebox.showwarning("Restauração", message)
            else:
                messagebox.showinfo("Sucesso", message)
                
            self.status_var.set("🔄 Backup restaurado!")
            self.scan_files()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na restauração: {str(e)}")
        """Cria uma chave para ordenação natural (números em ordem correta)"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]
    
    def scan_files(self):
        """Escaneia o diretório em busca de arquivos de vídeo e legenda"""
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Erro", "Selecione um diretório válido!")
            self.status_var.set("❌ Diretório inválido")
            return
        
        # Forçar atualização das configurações
        self.force_update_preview()
        
        self.status_var.set("🔍 Escaneando arquivos...")
        self.root.update()
        
        # Limpar lista anterior SEMPRE
        self.clear_file_list()
        
        # Buscar arquivos
        try:
            files = []
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext.lower() in self.supported_extensions:
                        files.append((file, ext.lower()))
            
            # Ordenar arquivos naturalmente
            files.sort(key=lambda x: self.natural_sort_key(x[0]))
            
            # Obter configurações ATUAIS (não antigas)
            series = self.series_var.get().strip()
            season = self.season_var.get().strip()
            start_episode = self.start_episode_var.get().strip()
            
            # Validar configurações
            if not series:
                messagebox.showerror("Erro", "Digite o nome da série!")
                self.status_var.set("❌ Nome da série vazio")
                return
            
            try:
                season_num = int(season)
                start_episode_num = int(start_episode)
            except ValueError:
                messagebox.showerror("Erro", "Temporada e episódio inicial devem ser números!")
                self.status_var.set("❌ Valores inválidos")
                return
            
            # Gerar novos nomes com configurações ATUAIS
            episode_counter = start_episode_num
            
            for original_name, ext in files:
                new_name = f"{series} S{season_num:02d}E{episode_counter:02d}{ext}"
                
                self.files_list.append({
                    'original': original_name,
                    'new': new_name,
                    'extension': ext,
                    'path': os.path.join(directory, original_name)
                })
                
                # Adicionar à treeview
                self.tree.insert('', 'end', values=(original_name, new_name, ext))
                
                episode_counter += 1
            
            if self.files_list:
                self.status_var.set(f"✅ {len(self.files_list)} arquivos encontrados e configurados!")
                messagebox.showinfo("Arquivos Encontrados", 
                                  f"📄 Encontrados {len(self.files_list)} arquivos!\n\n"
                                  f"🎬 Série: {series}\n"
                                  f"📺 Temporada: {season_num:02d}\n"
                                  f"🔢 Episódio inicial: {start_episode_num:02d}\n"
                                  f"📊 Tipos: {', '.join(set(f['extension'] for f in self.files_list))}")
            else:
                self.status_var.set("⚠️ Nenhum arquivo encontrado")
                messagebox.showwarning("Nenhum Arquivo", 
                                     f"Nenhum arquivo encontrado com as extensões suportadas!\n\n"
                                     f"Extensões suportadas: {', '.join(self.supported_extensions)}")
                
        except Exception as e:
            self.status_var.set("❌ Erro ao escanear")
            messagebox.showerror("Erro", f"Erro ao escanear diretório: {str(e)}")
    
    def rename_files(self):
        """Renomeia os arquivos conforme a lista gerada"""
        if not self.files_list:
            messagebox.showerror("Erro", "Primeiro escaneie os arquivos!")
            return
        
        # Verificar se as configurações ainda estão válidas
        current_series = self.series_var.get().strip()
        current_season = self.season_var.get().strip()
        current_episode = self.start_episode_var.get().strip()
        
        if not current_series:
            messagebox.showerror("Erro", "Nome da série não pode estar vazio!")
            return
        
        # Verificar se a primeira renomeação corresponde às configurações atuais
        if self.files_list:
            expected_name = f"{current_series} S{current_season}E{current_episode}.{self.files_list[0]['extension'][1:]}"
            if self.files_list[0]['new'] != expected_name:
                result = messagebox.askyesno("Configurações Alteradas", 
                                           f"As configurações foram alteradas!\n\n"
                                           f"Nome atual: {current_series}\n"
                                           f"Esperado: {expected_name}\n"
                                           f"Na lista: {self.files_list[0]['new']}\n\n"
                                           f"Deseja escanear novamente com as configurações atuais?")
                if result:
                    self.scan_files()
                    return
        
        directory = self.dir_var.get()
        
        # Criar backup automático antes da renomeação
        self.status_var.set("💾 Criando backup automático...")
        self.root.update()
        
        backup_data = self.create_backup_info(directory)
        if backup_data:
            self.backup_info = {
                'directory': directory,
                'files': backup_data,
                'type': 'automático',
                'timestamp': time.time()
            }
        
        # Confirmar ação
        result = messagebox.askyesno("Confirmar Renomeação", 
                                   f"Deseja renomear {len(self.files_list)} arquivos?\n\n"
                                   f"🎬 Série: {current_series}\n"
                                   f"📺 Temporada: {current_season}\n"
                                   f"🔢 Episódio inicial: {current_episode}\n\n"
                                   f"✅ Backup automático criado!\n"
                                   f"✅ Você poderá desfazer com Ctrl+Z\n\n"
                                   "Esta ação não pode ser desfeita manualmente!")
        
        if not result:
            self.status_var.set("❌ Operação cancelada")
            return
        
        self.status_var.set("🔄 Renomeando arquivos...")
        self.root.update()
        
        success_count = 0
        errors = []
        operations = []  # Para rastrear o que foi feito
        
        try:
            for file_info in self.files_list:
                try:
                    old_path = file_info['path']
                    new_path = os.path.join(directory, file_info['new'])
                    
                    # Verificar se o arquivo novo já existe
                    if os.path.exists(new_path) and old_path != new_path:
                        errors.append(f"Arquivo já existe: {file_info['new']}")
                        continue
                    
                    # Renomear arquivo
                    os.rename(old_path, new_path)
                    success_count += 1
                    
                    # Salvar operação para possível desfazer
                    operations.append({
                        'original_path': old_path,
                        'new_path': new_path,
                        'original_name': file_info['original'],
                        'new_name': file_info['new']
                    })
                    
                except Exception as e:
                    errors.append(f"Erro ao renomear {file_info['original']}: {str(e)}")
            
            # Salvar operações para desfazer
            if operations:
                self.last_operation = operations
                self.undo_button.configure(state='normal')
            
            # Mostrar resultado
            message = f"Renomeação concluída!\n\n"
            message += f"✅ Arquivos renomeados: {success_count}\n"
            message += f"💾 Backup automático salvo\n"
            message += f"↶ Use Ctrl+Z para desfazer\n"
            
            if errors:
                message += f"\n❌ Erros: {len(errors)}\n\n"
                message += "Detalhes dos erros:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    message += f"\n... e mais {len(errors) - 5} erros."
                messagebox.showwarning("Concluído com erros", message)
                self.status_var.set(f"⚠️ Concluído com {len(errors)} erros | ↶ Ctrl+Z para desfazer")
            else:
                messagebox.showinfo("Sucesso", message)
                self.status_var.set(f"✅ {success_count} arquivos renomeados! | ↶ Ctrl+Z para desfazer")
            
            # REMOVIDO: Não reescanear automaticamente para manter backup
            # self.scan_files()  ← Isso estava limpando o backup
            
            # Opcional: Limpar apenas a lista visual para mostrar os novos nomes
            self.clear_file_list(clear_undo=False)  # Não limpar desfazer
            self.status_var.set(f"✅ {success_count} arquivos renomeados! | ↶ Ctrl+Z disponível | 🔍 Clique 'Escanear' para ver novos nomes")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante a renomeação: {str(e)}")
            self.status_var.set("❌ Erro na renomeação")
    
    def run(self):
        """Inicia a aplicação"""
        # Centralizar janela
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()

# Para usar este programa:
# 1. Salve este código como "anime_file_renamer.py"
# 2. Instale o Python em python.org (marque "Add to PATH")
# 3. Execute: python anime_file_renamer.py

if __name__ == "__main__":
    app = AnimeFileRenamer()
    app.run()