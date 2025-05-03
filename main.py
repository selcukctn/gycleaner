import os
import customtkinter as ctk
from cleaner import get_temp_files_sorted, delete_files
from utils import format_bytes, load_whitelist, save_whitelist, load_settings, save_settings, should_auto_clean
from tkinter import messagebox
import datetime
import tkinter as tk
import subprocess
import threading
from tkinter import simpledialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class TempCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows Temp Cleaner")
        self.geometry("900x700")
        self.files = []
        self.check_vars = []
        self.filtered_files = []
        self.filter_text = ctk.StringVar()
        self.ext_filter = ctk.StringVar(value="Tümü")
        self.date_filter = ctk.StringVar(value="Tümü")
        self.settings = load_settings()

        # 🔍 Arama ve filtre çubuğu
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(padx=20, pady=(10, 0), fill="x")

        ctk.CTkLabel(filter_frame, text="🔍 Ara:").pack(side="left", padx=(5, 10))
        filter_entry = ctk.CTkEntry(filter_frame, textvariable=self.filter_text)
        filter_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(filter_frame, text="📁 Tür:").pack(side="left", padx=(10, 5))
        ext_menu = ctk.CTkOptionMenu(filter_frame, variable=self.ext_filter, values=["Tümü", ".tmp", ".log", ".bak"], command=lambda _: self.apply_filter())
        ext_menu.pack(side="left")

        ctk.CTkLabel(filter_frame, text="🕒 Tarih:").pack(side="left", padx=(10, 5))
        date_menu = ctk.CTkOptionMenu(filter_frame, variable=self.date_filter, values=["Tümü", "Son 24 saat", "Son 7 gün", "Son 30 gün"], command=lambda _: self.apply_filter())
        date_menu.pack(side="left")

        self.filter_text.trace_add("write", lambda *_: self.apply_filter())

        self.select_all_var = ctk.BooleanVar()
        self.select_all_checkbox = ctk.CTkCheckBox(self, text="Tümünü Seç", variable=self.select_all_var, command=self.toggle_select_all)
        self.select_all_checkbox.pack(anchor="w", padx=20, pady=(10, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=850, height=400)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.total_label = ctk.CTkLabel(self, text="Toplam Alan: 0 B", font=ctk.CTkFont(size=14))
        self.total_label.pack(pady=(0, 10))

        button_frame = ctk.CTkFrame(self)
        button_frame.pack()
        ctk.CTkButton(button_frame, text="Taramayı Başlat", command=self.refresh).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Seçilenleri Sil", command=self.delete_selected).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Whitelist'i Düzenle", command=self.edit_whitelist).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Gelişmiş Ayarlar", command=self.open_settings).pack(side="left", padx=10)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Detayları Göster", command=self.show_file_details)

        self.right_click_path = None
        self.loading_label = ctk.CTkLabel(self, text="Taranıyor...", font=ctk.CTkFont(size=16))
        self.loading_spinner = ctk.CTkProgressBar(self, mode="indeterminate")

        self.after(1000, self.check_auto_clean)

    def refresh(self):
        self.loading_label.pack(pady=10)
        self.loading_spinner.pack(pady=(0, 20))
        self.loading_spinner.start()
        threading.Thread(target=self._scan_temp_files, daemon=True).start()

    def _scan_temp_files(self):
        self.files = get_temp_files_sorted()
        self.after(0, self.apply_filter)

    def apply_filter(self):
        search = self.filter_text.get().lower()
        ext = self.ext_filter.get()
        date_filter = self.date_filter.get()

        now = datetime.datetime.now()

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.check_vars = []
        total = 0

        for f in self.files:
            path = f['path']
            size = f['size']
            if search and search not in path.lower():
                continue
            if ext != "Tümü" and not path.lower().endswith(ext.lower()):
                continue
            if date_filter != "Tümü":
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                delta = now - mtime
                if date_filter == "Son 24 saat" and delta > datetime.timedelta(days=1):
                    continue
                if date_filter == "Son 7 gün" and delta > datetime.timedelta(days=7):
                    continue
                if date_filter == "Son 30 gün" and delta > datetime.timedelta(days=30):
                    continue

            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self.scroll_frame, text=f"{path} ({format_bytes(size)})", variable=var)
            cb.pack(anchor="w", pady=2)
            cb.bind("<Button-3>", lambda e, p=path: self.open_context_menu(e, p))
            self.check_vars.append((var, path, size))
            total += size

        self.total_label.configure(text=f"Toplam Alan: {format_bytes(total)}")
        self.loading_spinner.stop()
        self.loading_spinner.pack_forget()
        self.loading_label.pack_forget()

    def toggle_select_all(self):
        select = self.select_all_var.get()
        for var, _, _ in self.check_vars:
            var.set(select)

    def delete_selected(self):
        to_delete = [path for var, path, _ in self.check_vars if var.get()]
        if not to_delete:
            messagebox.showinfo("Uyarı", "Hiçbir dosya seçilmedi.")
            return

        if messagebox.askyesno("Emin misin?", f"{len(to_delete)} dosya silinecek. Emin misiniz?"):
            total_freed = delete_files(to_delete)
            messagebox.showinfo("Silindi", f"{format_bytes(total_freed)} boş alan açıldı.")
            self.refresh()

    def open_context_menu(self, event, file_path):
        self.right_click_path = file_path
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def show_file_details(self):
        path = self.right_click_path
        if not path or not os.path.exists(path):
            messagebox.showerror("Hata", "Dosya bulunamadı.")
            return
        try:
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            detail_window = ctk.CTkToplevel(self)
            detail_window.title("Dosya Detayı")
            detail_window.geometry("600x250")
            detail_window.grab_set()

            ctk.CTkLabel(detail_window, text="📄 Dosya Yolu:", anchor="w").pack(fill="x", padx=10, pady=(10, 0))
            text_box = ctk.CTkTextbox(detail_window, height=40)
            text_box.pack(fill="x", padx=10)
            text_box.insert("1.0", path)
            text_box.configure(state="disabled")

            ctk.CTkLabel(detail_window, text=f"📏 Boyut: {format_bytes(size)}", anchor="w").pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(detail_window, text=f"📅 Değiştirilme: {modified}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))

            def open_in_explorer():
                subprocess.run(['explorer', '/select,', path])

            ctk.CTkButton(detail_window, text="📂 Dosyayı Aç", command=open_in_explorer).pack(pady=(10, 10))
        except Exception as e:
            messagebox.showerror("Hata", f"Detay alınamadı:\n{e}")

    def edit_whitelist(self):
        whitelist = load_whitelist()

        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Whitelist Düzenle")
        edit_win.geometry("600x400")
        edit_win.grab_set()

        listbox = tk.Listbox(edit_win)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for item in whitelist:
            listbox.insert("end", item)

        def add_item():
            new_path = simpledialog.askstring("Yeni Yol", "Yeni whitelist yolunu gir:")
            if new_path:
                listbox.insert("end", new_path)

        def remove_item():
            selection = listbox.curselection()
            for index in reversed(selection):
                listbox.delete(index)

        def save_and_close():
            updated = list(listbox.get(0, "end"))
            save_whitelist(updated)
            messagebox.showinfo("Kaydedildi", "Whitelist güncellendi.")
            edit_win.destroy()

        button_frame = ctk.CTkFrame(edit_win)
        button_frame.pack(pady=10)
        ctk.CTkButton(button_frame, text="Ekle", command=add_item).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Sil", command=remove_item).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Kaydet", command=save_and_close).pack(side="left", padx=5)

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("Gelişmiş Ayarlar")
        win.geometry("400x250")
        win.grab_set()

        auto_var = ctk.BooleanVar(value=self.settings.get("auto_clean_enabled", False))
        hour_var = tk.IntVar(value=self.settings.get("auto_clean_interval_hours", 24))

        ctk.CTkCheckBox(win, text="Otomatik temizlik aktif", variable=auto_var).pack(pady=10, anchor="w", padx=20)
        ctk.CTkLabel(win, text="Temizlik aralığı (saat):").pack(anchor="w", padx=20, pady=(10, 0))
        spin = tk.Spinbox(win, from_=1, to=168, textvariable=hour_var)
        spin.pack(anchor="w", padx=20)

        def save():
            self.settings["auto_clean_enabled"] = auto_var.get()
            self.settings["auto_clean_interval_hours"] = hour_var.get()
            save_settings(self.settings)
            messagebox.showinfo("Kaydedildi", "Ayarlar güncellendi.")
            win.destroy()

        ctk.CTkButton(win, text="Kaydet", command=save).pack(pady=20)

    def check_auto_clean(self):
        if should_auto_clean(self.settings):
            if self.settings.get("auto_clean_enabled", False):
                files = get_temp_files_sorted()
                to_delete = [f['path'] for f in files]
                delete_files(to_delete)
                self.settings["last_clean_time"] = datetime.datetime.now().isoformat()
                save_settings(self.settings)
                print("✅ Otomatik temizlik yapıldı.")


if __name__ == "__main__":
    app = TempCleanerApp()
    app.mainloop()
