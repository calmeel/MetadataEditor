import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import re

# =========================
# Design settings
# =========================
WINDOW_W, WINDOW_H = 500, 550

BG_COLOR = "#480e04"
LABEL_BG = "#3a0a04"
LABEL_FG = "white"

INPUT_BG = "#e9dad8"
INPUT_FG = "black"
DIFF_BG = "#fff4cc"

BTN_BG = "#6a1a0f"
BTN_ACTIVE_BG = "#8b2618"
BTN_FG = "white"

NORMAL_BORDER = "#6b5b59"
ERROR_BORDER = "red"

FONT_BTN = ("メイリオ", 12, "bold")
FONT_LABEL = ("メイリオ", 11, "bold")
FONT_INPUT = ("メイリオ", 11, "bold")

FIELDS = ["Title", "TitleUnicode", "Artist", "ArtistUnicode", "Source", "Tags"]
ALLOW_EMPTY_FIELDS = {"Source", "Tags"}
ASCII_ONLY_FIELDS = {"Title", "Artist"}

# =========================
# Language dictionaries
# =========================
LANG_JP = {
    "app_title": "osu! メタデータ一括編集ツール",
    "btn_load": "ファイルからメタデータを読み込む",
    "btn_process": "フォルダを選択して処理",
    "load_file_title": "メタデータを読み込む .osu ファイルを選択",
    "meta_not_found": "[Metadata] が見つかりません",
    "done": "完了",
    "loaded": "メタデータを読み込みました。",
    "select_input_title": "入力フォルダを選択",
    "select_input_msg": "入力フォルダを選択してください\n\n.osu ファイルが入っているフォルダ",
    "select_output_title": "出力フォルダを選択",
    "select_output_msg": "出力フォルダを選択してください\n\n変更後のファイルを保存するフォルダ",
    "input_error_title": "入力エラー",
    "input_error_msg": "次の項目に問題があります：\n\n{}",
    "confirm_title": "確認",
    "confirm_changed": "以下の項目が変更されます：\n\n{}\n\n実行しますか？",
    "confirm_nochange": "変更された項目はありません。\n（そのままコピーします）\n\n実行しますか？",
    "processed": "{} 件のファイルを処理しました。",
    "empty_tag": "（空欄）",
    "non_ascii_tag": "（英数字以外）",
}
LANG_EN = {
    "app_title": "osu! Bulk Metadata Editor",
    "btn_load": "Load metadata from file",
    "btn_process": "Select folder and process",
    "load_file_title": "Select a .osu file to load metadata",
    "meta_not_found": "[Metadata] not found.",
    "done": "Done",
    "loaded": "Metadata loaded successfully.",
    "select_input_title": "Select input folder",
    "select_input_msg": "Select INPUT folder\n\nFolder containing .osu files",
    "select_output_title": "Select output folder",
    "select_output_msg": "Select OUTPUT folder\n\nFolder to save modified files",
    "input_error_title": "Input error",
    "input_error_msg": "The following fields are invalid:\n\n{}",
    "confirm_title": "Confirm",
    "confirm_changed": "The following fields will be modified:\n\n{}\n\nProceed?",
    "confirm_nochange": "No fields were modified.\n(Files will be copied as-is.)\n\nProceed?",
    "processed": "Processed {} file(s).",
    "empty_tag": " (empty)",
    "non_ascii_tag": " (non-ASCII)",
}

# =========================
# Config (save language)
# =========================
def get_config_path() -> str:
    appdata = os.getenv("APPDATA")
    base = appdata if appdata else os.path.expanduser("~")
    cfg_dir = os.path.join(base, "BulkMetadataEditor")
    os.makedirs(cfg_dir, exist_ok=True)
    return os.path.join(cfg_dir, "config.json")

CONFIG_PATH = get_config_path()

def load_lang_setting() -> str:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        lang = data.get("lang", "JP")
        return "EN" if lang == "EN" else "JP"
    except Exception:
        return "JP"

def save_lang_setting(lang: str) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"lang": lang}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# =========================
# Globals
# =========================
original_values = {}
entries = {}

# =========================
# Utility
# =========================
def normalize_text(s: str) -> str:
    return " ".join(s.split())

def set_border(widget, color: str, thick: int):
    widget.configure(
        highlightthickness=thick,
        highlightbackground=color,
        highlightcolor=color
    )

def get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end").strip()

def set_text(widget: tk.Text, value: str):
    widget.delete("1.0", "end")
    widget.insert("1.0", value)

def is_ascii_only(s: str) -> bool:
    return s.isascii()

# current_lang will be created after root
def T(key: str) -> str:
    return (LANG_JP if current_lang.get() == "JP" else LANG_EN)[key]

def update_visual_state(field: str):
    w = entries[field]
    cur = normalize_text(get_text(w))
    org = normalize_text(original_values.get(field, ""))

    if cur != org:
        w.configure(bg=DIFF_BG)
    else:
        w.configure(bg=INPUT_BG)

    if field in ASCII_ONLY_FIELDS:
        if cur and not is_ascii_only(cur):
            set_border(w, ERROR_BORDER, 2)
        else:
            set_border(w, NORMAL_BORDER, 1)
    else:
        set_border(w, NORMAL_BORDER, 1)

def refresh_all_visuals():
    for f in FIELDS:
        update_visual_state(f)

# =========================
# Actions
# =========================
def load_metadata():
    path = filedialog.askopenfilename(
        title=T("load_file_title"),
        filetypes=[("osu files", "*.osu")]
    )
    if not path:
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    try:
        start = lines.index("[Metadata]")
    except ValueError:
        messagebox.showerror("Error", T("meta_not_found"))
        return

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("[") and lines[i].endswith("]"):
            end = i
            break

    original_values.clear()
    for fkey in FIELDS:
        original_values[fkey] = ""

    for line in lines[start + 1:end]:
        if ":" in line:
            k, v = line.split(":", 1)
            if k in original_values:
                original_values[k] = v

    for fkey in FIELDS:
        set_text(entries[fkey], original_values.get(fkey, ""))

    refresh_all_visuals()
    messagebox.showinfo(T("done"), T("loaded"))

def process_folder():
    messagebox.showinfo(T("select_input_title"), T("select_input_msg"))
    in_dir = filedialog.askdirectory(title=T("select_input_title"))
    if not in_dir:
        return

    messagebox.showinfo(T("select_output_title"), T("select_output_msg"))
    out_dir = filedialog.askdirectory(title=T("select_output_title"))
    if not out_dir:
        return

    changes = {}
    invalid_fields = []

    for fkey in FIELDS:
        cur = normalize_text(get_text(entries[fkey]))
        org = normalize_text(original_values.get(fkey, ""))

        if cur != org:
            if cur == "" and fkey not in ALLOW_EMPTY_FIELDS:
                invalid_fields.append(f"{fkey}{T('empty_tag')}")
            if fkey in ASCII_ONLY_FIELDS and cur and not is_ascii_only(cur):
                invalid_fields.append(f"{fkey}{T('non_ascii_tag')}")
            changes[fkey] = cur

    if invalid_fields:
        for fkey in ASCII_ONLY_FIELDS:
            update_visual_state(fkey)
        messagebox.showerror(
            T("input_error_title"),
            T("input_error_msg").format("\n".join(invalid_fields))
        )
        return

    if changes:
        msg = T("confirm_changed").format("\n".join(changes.keys()))
    else:
        msg = T("confirm_nochange")

    if not messagebox.askyesno(T("confirm_title"), msg):
        return

    processed = 0

    for fn in os.listdir(in_dir):
        if not fn.lower().endswith(".osu"):
            continue

        src_path = os.path.join(in_dir, fn)
        dst_path = os.path.join(out_dir, fn)

        with open(src_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        try:
            start = lines.index("[Metadata]")
        except ValueError:
            with open(dst_path, "w", encoding="utf-8") as wf:
                wf.write("\n".join(lines))
            processed += 1
            continue

        end = len(lines)
        for i in range(start + 1, len(lines)):
            if lines[i].startswith("[") and lines[i].endswith("]"):
                end = i
                break

        if changes:
            for i in range(start + 1, end):
                for k, v in changes.items():
                    if lines[i].startswith(k + ":"):
                        lines[i] = f"{k}:{v}"

        with open(dst_path, "w", encoding="utf-8") as wf:
            wf.write("\n".join(lines))

        processed += 1

    messagebox.showinfo(T("done"), T("processed").format(processed))

# =========================
# GUI
# =========================
root = tk.Tk()
root.geometry(f"{WINDOW_W}x{WINDOW_H}")
root.resizable(False, False)
root.configure(bg=BG_COLOR)

current_lang = tk.StringVar(value=load_lang_setting())

def refresh_text():
    root.title(T("app_title"))
    btn_load.config(text=T("btn_load"))
    btn_run.config(text=T("btn_process"))

def on_lang_change():
    save_lang_setting(current_lang.get())
    refresh_text()

# Top bar (language switch)
topbar = tk.Frame(root, bg=BG_COLOR)
topbar.pack(fill="x", padx=10, pady=(8, 0))

lang_frame = tk.Frame(topbar, bg=BG_COLOR)
lang_frame.pack(side="right")

tk.Radiobutton(
    lang_frame, text="JP", value="JP",
    variable=current_lang, command=on_lang_change,
    font=FONT_LABEL, fg=LABEL_FG, bg=BG_COLOR,
    activebackground=BG_COLOR, activeforeground=LABEL_FG,
    selectcolor=LABEL_BG
).pack(side="left", padx=(0, 6))

tk.Radiobutton(
    lang_frame, text="EN", value="EN",
    variable=current_lang, command=on_lang_change,
    font=FONT_LABEL, fg=LABEL_FG, bg=BG_COLOR,
    activebackground=BG_COLOR, activeforeground=LABEL_FG,
    selectcolor=LABEL_BG
).pack(side="left")

container = tk.Frame(root, bg=BG_COLOR)
container.pack(fill="both", expand=True, padx=10, pady=10)

# Buttons
btn_frame = tk.Frame(container, bg=BG_COLOR)
btn_frame.pack(fill="x")

btn_load = tk.Button(
    btn_frame,
    text="",
    font=FONT_BTN,
    fg=BTN_FG,
    bg=BTN_BG,
    activebackground=BTN_ACTIVE_BG,
    activeforeground=BTN_FG,
    relief="flat",
    height=2,
    command=load_metadata
)
btn_load.pack(fill="x", pady=(0, 8))

btn_run = tk.Button(
    btn_frame,
    text="",
    font=FONT_BTN,
    fg=BTN_FG,
    bg=BTN_BG,
    activebackground=BTN_ACTIVE_BG,
    activeforeground=BTN_FG,
    relief="flat",
    height=2,
    command=process_folder
)
btn_run.pack(fill="x")

# Form
form = tk.Frame(container, bg=BG_COLOR)
form.pack(fill="both", expand=True, pady=(10, 0))

form.grid_columnconfigure(0, weight=0)
form.grid_columnconfigure(1, weight=1)

for r, fkey in enumerate(FIELDS):
    if fkey == "Tags":
        label_height = 4
        text_height = 4
    else:
        label_height = 1
        text_height = 1

    tk.Label(
        form,
        text=fkey,
        font=FONT_LABEL,
        fg=LABEL_FG,
        bg=LABEL_BG,
        width=14,
        anchor="w",
        padx=8,
        pady=4,
        height=label_height
    ).grid(row=r, column=0, sticky="nsew", padx=(0, 8), pady=5)

    input_frame = tk.Frame(form, bg=BG_COLOR)
    input_frame.grid(row=r, column=1, sticky="nsew", pady=5)
    input_frame.grid_columnconfigure(0, weight=1)

    txt = tk.Text(
        input_frame,
        height=text_height,
        font=FONT_INPUT,
        fg=INPUT_FG,
        bg=INPUT_BG,
        wrap="word",
        relief="flat",
        insertbackground=INPUT_FG
    )
    txt.grid(row=0, column=0, sticky="nsew")

    set_border(txt, NORMAL_BORDER, 1)
    txt.bind("<KeyRelease>", lambda e, k=fkey: update_visual_state(k))

    entries[fkey] = txt
    original_values[fkey] = ""

# Initial text + visuals
refresh_text()
refresh_all_visuals()

root.mainloop()
