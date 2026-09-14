import customtkinter as ctk
from tkinter import filedialog
import os
import glob
import ezdxf
import re
import json
import time

# Configuração base de cores
COR_FUNDO = "#0F0F0F"       
COR_PAINEL = "#171717"      
COR_CAMPO = "#1F1F1F"       
COR_AZUL = "#29439F"        
COR_AZUL_HOVER = "#3B58C4"  
RAIO_BORDA = 15             

DIRETORIO_USUARIO = os.path.expanduser("~")
CONFIG_FILE = os.path.join(DIRETORIO_USUARIO, ".config_automador_dxf.json")

ctk.set_appearance_mode("dark")

# =========================================================
#                 UTILITÁRIOS DE INTERFACE
# =========================================================
def centralizar_janela(janela, largura, altura):
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (largura // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

def mostrar_popup(titulo, mensagem):
    popup = ctk.CTkToplevel(root)
    popup.title("Aviso")
    centralizar_janela(popup, 300, 180)
    popup.resizable(False, False)
    popup.configure(fg_color=COR_PAINEL)
    popup.transient(root)
    popup.grab_set()

    ctk.CTkLabel(popup, text=titulo, font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=COR_AZUL).pack(pady=(20, 5))
    ctk.CTkLabel(popup, text=mensagem, font=ctk.CTkFont(family="Segoe UI", size=13), justify="center").pack(pady=5)
    ctk.CTkButton(popup, text="OK", width=100, height=35, corner_radius=17, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, command=popup.destroy).pack(pady=(15, 10))

def perguntar_substituicao(nome_arquivo):
    resposta = ctk.BooleanVar(value=False)
    popup = ctk.CTkToplevel(root)
    popup.title("Arquivo Existente")
    centralizar_janela(popup, 350, 160)
    popup.resizable(False, False)
    popup.configure(fg_color=COR_PAINEL)
    popup.transient(root)
    popup.grab_set()

    ctk.CTkLabel(popup, text="Atenção: Sobrescrita", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#EAB308").pack(pady=(15, 5))
    
    nome_exibicao = nome_arquivo if len(nome_arquivo) < 30 else nome_arquivo[:27] + "..."
    ctk.CTkLabel(popup, text=f"Deseja substituir '{nome_exibicao}' e os próximos?", font=ctk.CTkFont(family="Segoe UI", size=13)).pack(pady=5)
    
    frame_btn = ctk.CTkFrame(popup, fg_color="transparent")
    frame_btn.pack(pady=10)
    
    def btn_sim():
        resposta.set(True)
        popup.destroy()
    def btn_nao():
        resposta.set(False)
        popup.destroy()
        
    ctk.CTkButton(frame_btn, text="Sim (Todos)", width=100, height=30, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, command=btn_sim).pack(side="left", padx=10)
    ctk.CTkButton(frame_btn, text="Não (Pular)", width=100, height=30, fg_color="#4A4A4A", hover_color="#606060", command=btn_nao).pack(side="left", padx=10)
    
    popup.wait_window()
    return resposta.get()

def log_msg(mensagem):
    caixa_log.insert("end", mensagem + "\n")
    caixa_log.see("end")
    root.update()

# =========================================================
#                 FUNÇÕES DE LÓGICA E MEMÓRIA
# =========================================================
def carregar_configuracoes():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                entry_origem_p.insert(0, config.get("origem_p", ""))
                entry_destino_p.insert(0, config.get("destino_p", ""))
                var_nome.set(config.get("chk_nome", True))
                var_lote.set(config.get("chk_lote", True))
                var_livre.set(config.get("chk_livre", False))
                entry_lote.insert(0, config.get("txt_lote", "-LOTE-01"))
                entry_livre.insert(0, config.get("txt_livre", ""))
                entry_fonte.insert(0, config.get("fonte", "5.0"))
                entry_origem_g.insert(0, config.get("origem_g", ""))
                entry_destino_g.insert(0, config.get("destino_g", ""))
                entry_chave.insert(0, config.get("chave", "LOTE"))
                entry_qtd.insert(0, config.get("qtd", ""))
        except Exception:
            restaurar_padroes()
    else:
        restaurar_padroes()

def salvar_configuracoes():
    config = {
        "origem_p": entry_origem_p.get().strip(),
        "destino_p": entry_destino_p.get().strip(),
        "chk_nome": var_nome.get(),
        "chk_lote": var_lote.get(),
        "txt_lote": entry_lote.get(),
        "chk_livre": var_livre.get(),
        "txt_livre": entry_livre.get(),
        "fonte": entry_fonte.get().strip(),
        "origem_g": entry_origem_g.get().strip(),
        "destino_g": entry_destino_g.get().strip(),
        "chave": entry_chave.get().strip(),
        "qtd": entry_qtd.get().strip()
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception:
        pass

def restaurar_padroes():
    var_nome.set(True)
    var_lote.set(True)
    var_livre.set(False)
    entry_lote.delete(0, 'end')
    entry_lote.insert(0, "-LOTE-01")
    entry_livre.delete(0, 'end')
    entry_fonte.delete(0, 'end')
    entry_fonte.insert(0, "5.0")
    salvar_configuracoes()

def regra_toggle_lote():
    if var_lote.get():
        var_livre.set(False)
    salvar_configuracoes()

def regra_toggle_livre():
    if var_livre.get():
        var_lote.set(False)
    salvar_configuracoes()

def buscar_origem_p():
    caminho = filedialog.askdirectory(title="Origem (Preparador)")
    if caminho:
        entry_origem_p.delete(0, 'end')
        entry_origem_p.insert(0, caminho)
        salvar_configuracoes()

def buscar_destino_p():
    caminho = filedialog.askdirectory(title="Destino (Preparador)")
    if caminho:
        entry_destino_p.delete(0, 'end')
        entry_destino_p.insert(0, caminho)
        salvar_configuracoes()

def buscar_origem_g():
    caminho = filedialog.askdirectory(title="Origem (Gerador)")
    if caminho:
        entry_origem_g.delete(0, 'end')
        entry_origem_g.insert(0, caminho)
        salvar_configuracoes()

def buscar_destino_g():
    caminho = filedialog.askdirectory(title="Destino (Gerador)")
    if caminho:
        entry_destino_g.delete(0, 'end')
        entry_destino_g.insert(0, caminho)
        salvar_configuracoes()

# =========================================================
#                 AÇÕES PRINCIPAIS (DXF)
# =========================================================
def executar_preparador():
    salvar_configuracoes()
    pasta_origem = entry_origem_p.get().strip()
    pasta_destino = entry_destino_p.get().strip()
    
    try:
        tamanho_fonte = float(entry_fonte.get().strip().replace(',', '.'))
    except ValueError:
        mostrar_popup("Erro", "O tamanho da fonte é inválido.")
        return

    if not pasta_origem or not pasta_destino:
        mostrar_popup("Atenção", "Selecione as pastas de origem e destino.")
        return

    arquivos = glob.glob(os.path.join(pasta_origem, "*.dxf"))
    if not arquivos:
        mostrar_popup("Aviso", "Nenhum arquivo .dxf encontrado.")
        return

    log_msg("-" * 40)
    log_msg(f"PREPARADOR: Processando {len(arquivos)} arquivos...")
    inicio = time.time()
    sucesso, erro = 0, 0

    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        nome_sem_extensao = os.path.splitext(nome_arquivo)[0]

        texto_final = ""
        if var_nome.get():
            texto_final += nome_sem_extensao
        if var_lote.get():
            texto_final += entry_lote.get()
        elif var_livre.get():
            texto_final += entry_livre.get()

        if not texto_final.strip():
            log_msg(f"⚠️ IGNORADO: '{nome_arquivo}' (Texto vazio)")
            erro += 1
            continue
            
        caminho_salvar = os.path.join(pasta_destino, nome_arquivo)
        
        # Preparador agora salva diretamente (passa por cima sem perguntar)
        try:
            doc = ezdxf.readfile(arquivo)
            msp = doc.modelspace()
            msp.add_text(texto_final, dxfattribs={'insert': (0, 0), 'height': tamanho_fonte})
            doc.saveas(caminho_salvar)
            log_msg(f"✅ PREPARADO: {nome_arquivo}")
            sucesso += 1
        except Exception as e:
            log_msg(f"❌ ERRO em '{nome_arquivo}': {e}")
            erro += 1

    tempo_gasto = time.time() - inicio
    log_msg(f"⏱️ Tempo total: {tempo_gasto:.2f} segundos")
    log_msg(f"Concluído: {sucesso} prontos | {erro} erros.\n")
    mostrar_popup("Processamento Concluído", f"✅ Preparados: {sucesso}\n❌ Erros: {erro}")

def executar_gerador():
    salvar_configuracoes()
    pasta_origem = entry_origem_g.get().strip()
    pasta_destino = entry_destino_g.get().strip()
    palavra_chave = entry_chave.get().strip().upper()
    qtd_str = entry_qtd.get().strip()

    if not all([pasta_origem, pasta_destino, palavra_chave, qtd_str]):
        mostrar_popup("Atenção", "Preencha todos os campos do Gerador.")
        return

    if not qtd_str.isdigit() or int(qtd_str) < 1:
        mostrar_popup("Erro", "A quantidade deve ser um número inteiro > 0.")
        return

    arquivos = glob.glob(os.path.join(pasta_origem, "*.dxf"))
    if not arquivos:
        mostrar_popup("Aviso", "Nenhum arquivo .dxf encontrado.")
        return

    log_msg("-" * 40)
    log_msg(f"GERADOR: Processando {len(arquivos)} arquivos...")
    inicio = time.time()
    
    qtd_lotes = int(qtd_str)
    sucesso, ignorado, erro, pulado = 0, 0, 0, 0
    regex_padrao = re.compile(rf'({palavra_chave}[\s\-_]*\d+)', re.IGNORECASE)
    
    # Flag para controlar a substituição em massa
    substituir_todos = False

    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        nome_sem_ext = os.path.splitext(nome_arquivo)[0]

        try:
            doc = ezdxf.readfile(arquivo)
            msp = doc.modelspace()
            texto_encontrado = False

            for entity in msp.query('TEXT MTEXT'):
                if hasattr(entity.dxf, 'text'):
                    match = regex_padrao.search(entity.dxf.text)
                    if match:
                        texto_encontrado = True
                        texto_original = entity.dxf.text
                        trecho_antigo = match.group(1) 
                        numeros_antigos = re.search(r'\d+', trecho_antigo).group()
                        tamanho_zeros = len(numeros_antigos)
                        arquivos_gerados = 0

                        for lote_atual in range(1, qtd_lotes + 1):
                            novo_numero = str(lote_atual).zfill(tamanho_zeros)
                            novo_trecho = trecho_antigo.replace(numeros_antigos, novo_numero)
                            entity.dxf.text = texto_original.replace(trecho_antigo, novo_trecho)
                            
                            novo_nome = f"{nome_sem_ext}_LOTE_{novo_numero}.dxf"
                            caminho_salvar = os.path.join(pasta_destino, novo_nome)
                            
                            # Lógica de substituição com "Sim para Todos"
                            if os.path.exists(caminho_salvar):
                                if not substituir_todos:
                                    if not perguntar_substituicao(novo_nome):
                                        log_msg(f"⚠️ PULADO: '{novo_nome}' (Não substituído)")
                                        pulado += 1
                                        continue
                                    else:
                                        substituir_todos = True
                                        log_msg("⚠️ Substituição em massa ativada.")
                                
                            doc.saveas(caminho_salvar)
                            arquivos_gerados += 1

                        entity.dxf.text = texto_original
                        if arquivos_gerados > 0:
                            log_msg(f"✅ GERADO: {nome_arquivo} -> {arquivos_gerados} novos lotes.")
                            sucesso += arquivos_gerados
                        break

            if not texto_encontrado:
                log_msg(f"⚠️ IGNORADO: '{nome_arquivo}' (Sem tag base).")
                ignorado += 1

        except Exception as e:
            log_msg(f"❌ ERRO em '{nome_arquivo}': {e}")
            erro += 1

    tempo_gasto = time.time() - inicio
    log_msg(f"⏱️ Tempo total: {tempo_gasto:.2f} segundos")
    log_msg(f"Concluído: {sucesso} gerados | {ignorado} ignorados | {pulado} pulados | {erro} erros.\n")
    mostrar_popup("Lotes Gerados", f"✅ Gerados: {sucesso}\n⚠️ Ignorados/Pulados: {ignorado + pulado}\n❌ Erros: {erro}")


# =========================================================
#                 INTERFACE GRÁFICA
# =========================================================
root = ctk.CTk(fg_color=COR_FUNDO)
root.title("LoteGen")
root.geometry("650x640")
root.resizable(False, False)

fonte_padrao = ctk.CTkFont(family="Segoe UI", size=13)
fonte_titulo = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")

tabview = ctk.CTkTabview(
    root, 
    fg_color=COR_PAINEL, 
    segmented_button_fg_color=COR_FUNDO,
    segmented_button_selected_color=COR_AZUL,
    segmented_button_selected_hover_color=COR_AZUL_HOVER,
    segmented_button_unselected_color=COR_FUNDO,
    segmented_button_unselected_hover_color=COR_CAMPO,
    corner_radius=RAIO_BORDA
)
tabview.pack(padx=15, pady=15, fill="both", expand=True)

aba_preparador = tabview.add("Preparador")
aba_gerador = tabview.add("Gerador")

var_nome = ctk.BooleanVar()
var_lote = ctk.BooleanVar()
var_livre = ctk.BooleanVar()

# ----------------- ABA 1: PREPARADOR -----------------
ctk.CTkLabel(aba_preparador, text="Caminhos de Arquivo", font=fonte_titulo).pack(pady=(10, 5), padx=15, anchor="w")

linha_origem_p = ctk.CTkFrame(aba_preparador, fg_color="transparent")
linha_origem_p.pack(fill="x", padx=15, pady=5)
ctk.CTkLabel(linha_origem_p, text="Origem:", width=60, anchor="w", font=fonte_padrao).pack(side="left")
entry_origem_p = ctk.CTkEntry(linha_origem_p, placeholder_text="Pasta dos DXFs brutos...", height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_origem_p.pack(side="left", fill="x", expand=True, padx=10)
ctk.CTkButton(linha_origem_p, text="Buscar", width=70, fg_color=COR_CAMPO, hover_color="#2A2A2A", corner_radius=RAIO_BORDA, command=buscar_origem_p).pack(side="left")

linha_destino_p = ctk.CTkFrame(aba_preparador, fg_color="transparent")
linha_destino_p.pack(fill="x", padx=15, pady=(5, 10))
ctk.CTkLabel(linha_destino_p, text="Destino:", width=60, anchor="w", font=fonte_padrao).pack(side="left")
entry_destino_p = ctk.CTkEntry(linha_destino_p, placeholder_text="Pasta para salvar...", height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_destino_p.pack(side="left", fill="x", expand=True, padx=10)
ctk.CTkButton(linha_destino_p, text="Buscar", width=70, fg_color=COR_CAMPO, hover_color="#2A2A2A", corner_radius=RAIO_BORDA, command=buscar_destino_p).pack(side="left")

ctk.CTkLabel(aba_preparador, text="Parâmetros do Texto", font=fonte_titulo).pack(pady=(10, 5), padx=15, anchor="w")

chk_nome = ctk.CTkCheckBox(aba_preparador, text="Manter Nome Original", variable=var_nome, font=fonte_padrao, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, corner_radius=5, command=salvar_configuracoes)
chk_nome.pack(pady=5, padx=15, anchor="w")

linha_lote = ctk.CTkFrame(aba_preparador, fg_color="transparent")
linha_lote.pack(fill="x", padx=15, pady=5)
chk_lote = ctk.CTkCheckBox(linha_lote, text="Adicionar Lote:", variable=var_lote, font=fonte_padrao, width=150, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, corner_radius=5, command=regra_toggle_lote)
chk_lote.pack(side="left")
entry_lote = ctk.CTkEntry(linha_lote, height=35, width=150, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_lote.pack(side="left", padx=10)

linha_livre = ctk.CTkFrame(aba_preparador, fg_color="transparent")
linha_livre.pack(fill="x", padx=15, pady=5)
chk_livre = ctk.CTkCheckBox(linha_livre, text="Texto Livre:", variable=var_livre, font=fonte_padrao, width=150, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, corner_radius=5, command=regra_toggle_livre)
chk_livre.pack(side="left")
entry_livre = ctk.CTkEntry(linha_livre, height=35, width=150, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_livre.pack(side="left", padx=10)

linha_fonte = ctk.CTkFrame(aba_preparador, fg_color="transparent")
linha_fonte.pack(fill="x", padx=15, pady=5)
ctk.CTkLabel(linha_fonte, text="Tamanho Fonte:", font=fonte_padrao, width=145, anchor="w").pack(side="left")
entry_fonte = ctk.CTkEntry(linha_fonte, height=35, width=80, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_fonte.pack(side="left", padx=15)

frame_acoes_p = ctk.CTkFrame(aba_preparador, fg_color="transparent")
frame_acoes_p.pack(pady=15, padx=15, fill="x")

btn_reset = ctk.CTkButton(frame_acoes_p, text="Resetar Padrões", width=120, height=45, fg_color="transparent", border_width=1.5, border_color=COR_AZUL, text_color=COR_AZUL, hover_color=COR_CAMPO, corner_radius=22, command=restaurar_padroes)
btn_reset.pack(side="left", padx=(0, 10))

btn_gerar_p = ctk.CTkButton(frame_acoes_p, text="Preparar Arquivos", font=fonte_titulo, height=45, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, corner_radius=22, command=executar_preparador)
btn_gerar_p.pack(side="right", fill="x", expand=True)

# ----------------- ABA 2: GERADOR -----------------
ctk.CTkLabel(aba_gerador, text="Caminhos de Arquivo", font=fonte_titulo).pack(pady=(10, 5), padx=15, anchor="w")

linha_origem_g = ctk.CTkFrame(aba_gerador, fg_color="transparent")
linha_origem_g.pack(fill="x", padx=15, pady=5)
ctk.CTkLabel(linha_origem_g, text="Origem:", width=60, anchor="w", font=fonte_padrao).pack(side="left")
entry_origem_g = ctk.CTkEntry(linha_origem_g, placeholder_text="DXFs base...", height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_origem_g.pack(side="left", fill="x", expand=True, padx=10)
ctk.CTkButton(linha_origem_g, text="Buscar", width=70, fg_color=COR_CAMPO, hover_color="#2A2A2A", corner_radius=RAIO_BORDA, command=buscar_origem_g).pack(side="left")

linha_destino_g = ctk.CTkFrame(aba_gerador, fg_color="transparent")
linha_destino_g.pack(fill="x", padx=15, pady=(5, 15))
ctk.CTkLabel(linha_destino_g, text="Destino:", width=60, anchor="w", font=fonte_padrao).pack(side="left")
entry_destino_g = ctk.CTkEntry(linha_destino_g, placeholder_text="Onde salvar os lotes...", height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_destino_g.pack(side="left", fill="x", expand=True, padx=10)
ctk.CTkButton(linha_destino_g, text="Buscar", width=70, fg_color=COR_CAMPO, hover_color="#2A2A2A", corner_radius=RAIO_BORDA, command=buscar_destino_g).pack(side="left")

ctk.CTkLabel(aba_gerador, text="Regras de Multiplicação", font=fonte_titulo).pack(pady=(10, 5), padx=15, anchor="w")

linha_regras = ctk.CTkFrame(aba_gerador, fg_color="transparent")
linha_regras.pack(fill="x", padx=15, pady=(5, 20))

ctk.CTkLabel(linha_regras, text="Palavra-chave:", font=fonte_padrao).pack(side="left")
entry_chave = ctk.CTkEntry(linha_regras, width=100, height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_chave.pack(side="left", padx=(10, 25))

ctk.CTkLabel(linha_regras, text="Quantidade:", font=fonte_padrao).pack(side="left")
entry_qtd = ctk.CTkEntry(linha_regras, width=80, height=35, fg_color=COR_CAMPO, border_width=0, corner_radius=RAIO_BORDA)
entry_qtd.pack(side="left", padx=10)

btn_gerar_g = ctk.CTkButton(aba_gerador, text="Gerar Lotes", font=fonte_titulo, height=45, fg_color=COR_AZUL, hover_color=COR_AZUL_HOVER, corner_radius=22, command=executar_gerador)
btn_gerar_g.pack(pady=10, padx=15, fill="x")

# ----------------- LOG COMPARTILHADO -----------------
caixa_log = ctk.CTkTextbox(root, height=120, fg_color=COR_PAINEL, corner_radius=RAIO_BORDA, font=("Consolas", 12))
caixa_log.pack(pady=(0, 15), padx=15, fill="x")
caixa_log.insert("end", "Pronto para iniciar...\n")

carregar_configuracoes()
root.mainloop()