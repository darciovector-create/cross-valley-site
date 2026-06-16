# -*- coding: utf-8 -*-
"""
CROSS VALLEY STUDIO GPT - GUI v1.0
BUILD 015.1 | CAPCUT AUTO EDIT ENGINE
Interface grafica profissional - customtkinter
"""

import sys
import os
import threading
import io
import contextlib
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# ── Instala dependencias se ausentes ──────────────────────────────────────────
def _require(pkg, import_as=None):
    import importlib
    try:
        return importlib.import_module(import_as or pkg)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        return importlib.import_module(import_as or pkg)

ctk = _require("customtkinter")
_require("pillow", "PIL")

# ── Importa o motor ─────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
import Cross_Valley_Studio_OS as engine

# ── Paleta Cross Valley ──────────────────────────────────────────────────────
GOLD       = "#FFD166"
GOLD_DARK  = "#B8860B"
GOLD_HOV   = "#FFE080"
BG_DARK    = "#0D0D0D"
BG_PANEL   = "#161616"
BG_CARD    = "#1C1C1C"
BG_INPUT   = "#232323"
TXT_WHITE  = "#F0F0F0"
TXT_MUTED  = "#777777"
TXT_LOG    = "#A8E6A3"
RED        = "#FF6060"
GREEN      = "#5FD980"
BORDER     = "#282828"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ══════════════════════════════════════════════════════════════════════════════
#  BOTAO LATERAL
# ══════════════════════════════════════════════════════════════════════════════
class SideButton(ctk.CTkButton):
    def __init__(self, master, number, label, command, highlight=False):
        clr = GOLD_DARK if highlight else "transparent"
        txt = BG_DARK   if highlight else TXT_WHITE
        hov = GOLD      if highlight else BG_CARD
        fnt = ctk.CTkFont("Segoe UI", 13, "bold") if highlight else ctk.CTkFont("Segoe UI", 13)
        prefix = f"  {number:02d}   " if number else "  "
        super().__init__(
            master,
            text=f"{prefix}{label}",
            command=command,
            anchor="w",
            height=42 if highlight else 38,
            corner_radius=8,
            fg_color=clr,
            text_color=txt,
            hover_color=hov,
            font=fnt,
            border_width=0,
        )
        self._highlight = highlight

    def activate(self):
        if self._highlight:
            self.configure(fg_color=GOLD, text_color=BG_DARK,
                           font=ctk.CTkFont("Segoe UI", 13, "bold"))
        else:
            self.configure(fg_color=BG_CARD, text_color=GOLD,
                           font=ctk.CTkFont("Segoe UI", 13, "bold"))

    def deactivate(self):
        if self._highlight:
            self.configure(fg_color=GOLD_DARK, text_color=BG_DARK,
                           font=ctk.CTkFont("Segoe UI", 13, "bold"))
        else:
            self.configure(fg_color="transparent", text_color=TXT_WHITE,
                           font=ctk.CTkFont("Segoe UI", 13))

# ══════════════════════════════════════════════════════════════════════════════
#  APLICATIVO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class CrossValleyApp(ctk.CTk):

    VERSION = "BUILD 017 - MAQUINA DE VIDEOS"

    # None = separador de secao (nao e botao)
    # (num, label, fn, highlight?)
    MENU = [
        # ── PROJETO ──────────────────────────────────────────────
        (None, "PROJETO",                    None,   False),
        (1,  "Criar Novo Projeto",           "create_project",       False),
        (2,  "Organizar Projeto",            "organize_project",     False),

        # ── CONTEUDO ─────────────────────────────────────────────
        (None, "CONTEUDO",                   None,   False),
        (3,  "Gerar Legendas SRT",           "generate_srt",         False),
        (4,  "Gerar SEO Premium 2.0",        "generate_seo",         False),
        (5,  "Gerar Thumbnails IA",          "generate_story_thumbs",False),
        (6,  "Pacote YouTube Completo",      "youtube_package",      False),
        (7,  "Gerar Prompts Story DNA",      "build_story_prompts",  False),

        # ── ANALISE ──────────────────────────────────────────────
        (None, "ANALISE",                    None,   False),
        (8,  "Story Analyzer",               "story_analyzer",       False),
        (9,  "Storyboard Viral",             "write_storyboard",     False),
        (10, "CTR Intelligence",             "ctr_report",           False),

        # ── EDICAO ───────────────────────────────────────────────
        (None, "EDICAO",                     None,   False),
        (11, "Montar Sequencia CapCut",      "montar_sequencia_capcut", False),

        # ── PUBLICACAO ───────────────────────────────────────────
        (None, "PUBLICACAO",                 None,   False),
        (12, "REEL MACHINE  (cria 45s)",     "reel_machine",             False),
        (13, "YouTube Shorts",               "upload_youtube_shorts",    False),
        (14, "Instagram Reels",              "upload_instagram_reels",   False),
        (15, "TikTok",                       "upload_tiktok",            False),
        (16, "PUBLICAR TUDO",                "publicar_tudo",            True),

        # ── SISTEMA ──────────────────────────────────────────────
        (None, "SISTEMA",                    None,   False),
        (17, "Configurar Chave OpenAI",      "configure_key",        False),
        (18, "Aprovar Thumbnail",            "approve_thumb",        False),
        (19, "Rejeitar Thumbnail",           "reject_thumb",         False),
        (20, "Atualizar Persona Master",     "update_persona_master",False),
        (21, "Diagnostico DNA",              "dna_diagnostic",       False),
    ]

    def __init__(self):
        super().__init__()
        self.title("APP CROSSVALLEY STUDIO_CLAUDE CODE")
        self.geometry("1280x780")
        self.minsize(900, 600)
        self.configure(fg_color=BG_DARK)
        self._proj     = tk.StringVar(value="")
        self._running  = False
        self._active   = None          # numero do botao ativo
        self._btns     : dict[int, SideButton] = {}
        self._fn_name  = None
        # mapa num -> (label, fn) apenas para itens reais
        self._menu_map = {num: (label, fn) for num, label, fn, *_ in self.MENU if num is not None}
        self._build_ui()
        self.after(80, self._show_welcome)

    # ── CONSTRUCAO DA UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar()
        self._main_area()

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    def _sidebar(self):
        sb = ctk.CTkFrame(self, width=272, corner_radius=0,
                          fg_color=BG_PANEL, border_width=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(1, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        # Cabecalho fixo
        hdr = ctk.CTkFrame(sb, fg_color=BG_DARK, corner_radius=0, height=88)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="+  CROSSVALLEY STUDIO",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=GOLD).place(relx=0.5, rely=0.38, anchor="center")
        ctk.CTkLabel(hdr, text="CLAUDE CODE",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TXT_MUTED).place(relx=0.5, rely=0.70, anchor="center")

        # Area scrollavel com os botoes
        scroll = ctk.CTkScrollableFrame(
            sb, fg_color=BG_PANEL, corner_radius=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=GOLD_DARK,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        row_i = 0
        for entry in self.MENU:
            num, label, fn = entry[0], entry[1], entry[2]
            highlight = entry[3] if len(entry) > 3 else False

            if num is None:
                # Separador de secao
                if row_i > 0:
                    ctk.CTkFrame(scroll, height=1, fg_color=BORDER, corner_radius=0
                                 ).grid(row=row_i, column=0, sticky="ew", padx=10, pady=(6, 2))
                    row_i += 1
                ctk.CTkLabel(scroll, text=f"  {label}",
                             font=ctk.CTkFont("Segoe UI", 10, "bold"),
                             text_color=GOLD_DARK, anchor="w"
                             ).grid(row=row_i, column=0, sticky="ew", padx=12, pady=(4, 0))
                row_i += 1
            else:
                btn = SideButton(scroll, num, label,
                                 command=lambda n=num: self._select(n),
                                 highlight=highlight)
                btn.grid(row=row_i, column=0, sticky="ew", padx=8, pady=1)
                self._btns[num] = btn
                row_i += 1

        # Versao no rodape fixo
        foot = ctk.CTkFrame(sb, fg_color=BG_DARK, corner_radius=0, height=28)
        foot.grid(row=2, column=0, sticky="ew")
        foot.grid_propagate(False)
        ctk.CTkLabel(foot, text=self.VERSION,
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=TXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")

    # ── AREA PRINCIPAL ────────────────────────────────────────────────────────
    def _main_area(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_DARK)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # Barra do projeto
        pbar = ctk.CTkFrame(main, fg_color=BG_PANEL, corner_radius=12, height=62)
        pbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 6))
        pbar.grid_propagate(False)
        pbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pbar, text="PROJETO",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=GOLD).grid(row=0, column=0, padx=(16, 8), pady=16)

        self._proj_entry = ctk.CTkEntry(
            pbar, textvariable=self._proj,
            placeholder_text="Caminho da pasta do projeto...",
            fg_color=BG_INPUT, border_color=BORDER,
            text_color=TXT_WHITE,
            font=ctk.CTkFont("Segoe UI", 12),
            height=34,
        )
        self._proj_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=14)

        ctk.CTkButton(
            pbar, text="Selecionar", width=100, height=34,
            fg_color=GOLD_DARK, hover_color=GOLD, text_color=BG_DARK,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=8, command=self._browse,
        ).grid(row=0, column=2, padx=(0, 14), pady=14)

        # Titulo funcao ativa
        self._title = ctk.CTkLabel(
            main, text="  Selecione uma funcao no menu lateral",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=GOLD, anchor="w"
        )
        self._title.grid(row=1, column=0, sticky="ew", padx=22, pady=(2, 4))

        # Console
        log_wrap = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=12)
        log_wrap.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 10))
        log_wrap.grid_columnconfigure(0, weight=1)
        log_wrap.grid_rowconfigure(0, weight=1)

        self._log = ctk.CTkTextbox(
            log_wrap,
            fg_color=BG_CARD,
            text_color=TXT_LOG,
            font=ctk.CTkFont("Consolas", 12),
            corner_radius=12,
            wrap="word",
            border_width=0,
            state="disabled",
        )
        self._log.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Barra inferior
        bot = ctk.CTkFrame(main, fg_color=BG_PANEL, corner_radius=12, height=54)
        bot.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        bot.grid_propagate(False)
        bot.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            bot, text="Pronto",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=GREEN, anchor="w"
        )
        self._status.grid(row=0, column=0, padx=18, sticky="w")

        self._run_btn = ctk.CTkButton(
            bot, text="EXECUTAR", width=150, height=34,
            fg_color=GOLD_DARK, hover_color=GOLD,
            text_color="#000000", text_color_disabled="#000000",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            corner_radius=8, state="disabled",
            command=self._run,
        )
        self._run_btn.grid(row=0, column=1, padx=(0, 10))

        ctk.CTkButton(
            bot, text="Limpar", width=76, height=34,
            fg_color="transparent", hover_color=BG_CARD,
            text_color=TXT_MUTED,
            font=ctk.CTkFont("Segoe UI", 12),
            border_width=1, border_color=BORDER,
            corner_radius=8, command=self._clear,
        ).grid(row=0, column=2, padx=(0, 14))

    # ── SELECAO DE FUNCAO ────────────────────────────────────────────────────
    def _select(self, num: int):
        if self._running:
            return
        if self._active is not None:
            self._btns[self._active].deactivate()
        self._btns[num].activate()
        self._active = num
        label, fn = self._menu_map[num]
        self._fn_name = fn
        self._title.configure(text=f"  {num:02d} — {label}")
        self._run_btn.configure(state="normal")
        self._set_status(f"Funcao selecionada: {label}", GOLD)

    # ── EXECUTAR ─────────────────────────────────────────────────────────────
    def _run(self):
        if self._running or not self._fn_name:
            return
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        self._running = True
        self.after(0, lambda: self._run_btn.configure(state="disabled", text="Executando..."))
        self.after(0, lambda: self._set_status("Executando...", GOLD))

        fn_name = self._fn_name
        proj    = self._proj.get().strip().strip('"').strip("'")

        buf = io.StringIO()
        try:
            NEEDS_PROJ = {
                "build_story_prompts", "generate_srt", "generate_seo",
                "generate_story_thumbs", "organize_project",
                "write_storyboard", "ctr_report", "story_analyzer",
                "montar_sequencia_capcut", "reel_machine", "upload_youtube_shorts", "upload_instagram_reels",
                "upload_tiktok", "publicar_tudo",
            }
            INTERACTIVE = {
                "create_project", "configure_key",
                "approve_thumb", "reject_thumb",
                "update_persona_master", "youtube_package",
            }

            if fn_name in NEEDS_PROJ:
                if not proj:
                    self._append("\nNenhum projeto selecionado.\nUse o botao Selecionar.\n", RED)
                    return
                p = Path(proj)
                if not p.exists():
                    self._append(f"\nPasta nao encontrada:\n{proj}\n", RED)
                    return
                self._patch_input(proj)
                with contextlib.redirect_stdout(buf):
                    if fn_name == "story_analyzer":
                        moments = engine.analyze_story_moments(p)
                        for i, m in enumerate(moments, 1):
                            print(f"#{i}  CTR {m['score']}/100 | {m['thumb']} | {m['lyric']}")
                    elif fn_name == "generate_srt":
                        dur_str = self._ask(
                            "DURACAO TOTAL da musica (MM:SS ou segundos)\n"
                            "Exemplo:  6:41  ou  401\n\n"
                            "Deixe em branco para padrao (400s)."
                        )
                        off_str = self._ask(
                            "QUANDO COMECA A VOZ? (segundos)\n"
                            "Exemplo:  3   ou   2.5\n\n"
                            "Deixe em branco se comeca no inicio (0)."
                        )
                        total_sec  = engine.parse_duration(dur_str)
                        offset_sec = engine.parse_duration(off_str) or 0.0
                        engine.generate_srt(p, total_seconds=total_sec, start_offset=offset_sec)
                    elif fn_name in ("write_storyboard", "ctr_report"):
                        getattr(engine, fn_name)(p)
                    else:
                        getattr(engine, fn_name)(p)

            elif fn_name in INTERACTIVE:
                self._patch_input(proj)
                with contextlib.redirect_stdout(buf):
                    getattr(engine, fn_name)()

            elif fn_name == "dna_diagnostic":
                with contextlib.redirect_stdout(buf):
                    engine.dna_diagnostic()

            output = buf.getvalue()
            if output:
                self.after(0, lambda o=output: self._append(o))
            self.after(0, lambda: self._append("\nConcluido.\n", GREEN))
            self.after(0, lambda: self._set_status("Concluido com sucesso", GREEN))

        except Exception as exc:
            output = buf.getvalue()
            if output:
                self.after(0, lambda o=output: self._append(o))
            msg = f"\nErro: {exc}\n"
            self.after(0, lambda m=msg: self._append(m, RED))
            self.after(0, lambda m=msg: self._set_status(m.strip(), RED))

        finally:
            self._unpatch_input()
            self._running = False
            self.after(0, lambda: self._run_btn.configure(state="normal", text="EXECUTAR"))

    # ── PATCH input() ────────────────────────────────────────────────────────
    def _patch_input(self, proj_path: str):
        import builtins
        self._orig_input = builtins.input
        _proj = proj_path

        def _fake(prompt=""):
            self.after(0, lambda p=str(prompt): self._append(f"\n> {p}", GOLD))
            low = str(prompt).lower()
            if any(k in low for k in ["caminho do projeto", "caminho onde criar"]):
                self.after(0, lambda: self._append(_proj + "\n"))
                return _proj
            result = self._ask(str(prompt))
            self.after(0, lambda r=result: self._append((r or "") + "\n"))
            return result or ""

        builtins.input = _fake

    def _unpatch_input(self):
        import builtins
        if hasattr(self, "_orig_input") and self._orig_input:
            builtins.input = self._orig_input

    def _ask(self, prompt: str) -> str:
        result = {"v": ""}
        ev = threading.Event()
        def _show():
            dlg = ctk.CTkInputDialog(text=prompt, title="Cross Valley Studio")
            result["v"] = dlg.get_input() or ""
            ev.set()
        self.after(0, _show)
        ev.wait(timeout=120)
        return result["v"]

    # ── BROWSE ───────────────────────────────────────────────────────────────
    def _browse(self):
        initial = self._proj.get().strip() or engine.DEFAULT_PATH
        folder = filedialog.askdirectory(title="Selecione a pasta do projeto",
                                         initialdir=initial)
        if folder:
            self._proj.set(folder)
            self._set_status(f"Projeto: {Path(folder).name}", GOLD)

    # ── LOG ──────────────────────────────────────────────────────────────────
    def _append(self, text: str, color: str = TXT_LOG):
        self._log.configure(state="normal")
        self._log.insert("end", text)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _set_status(self, text: str, color: str = TXT_WHITE):
        self._status.configure(text=text, text_color=color)

    def _show_welcome(self):
        lines = [
            "=" * 56,
            "",
            "   APP CROSSVALLEY STUDIO  |  " + self.VERSION,
            "   Maquina de Videos Gospel - YouTube / Instagram / TikTok",
            "",
            "=" * 56,
            "",
            "  FLUXO RAPIDO - Nova Musica:",
            "  1. Clique em 'Selecionar' e escolha a pasta do projeto",
            "  2. PUBLICACAO > PUBLICAR TUDO  ->  EXECUTAR",
            "     (cria o Reel 45s + publica em todas as plataformas)",
            "",
            "  FLUXO DETALHADO:",
            "  CONTEUDO  > Gerar Legendas SRT",
            "  CONTEUDO  > Gerar SEO Premium 2.0",
            "  CONTEUDO  > Gerar Thumbnails IA",
            "  PUBLICACAO > REEL MACHINE  (gera o video 45s)",
            "  PUBLICACAO > YouTube / Instagram / TikTok  (individualmente)",
            "",
            "  Dica: role o menu lateral com o scroll do mouse!",
            "",
        ]
        self._append("\n".join(lines) + "\n")

# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    engine.setup_dna()
    app = CrossValleyApp()
    app.mainloop()
