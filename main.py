import os
import customtkinter as ctk
from cleaner import get_temp_files_sorted, delete_files
from utils import format_bytes
from tkinter import messagebox
import datetime
import tkinter as tk
import subprocess
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class TempCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows Temp Cleaner")
        self.geometry("850x600")
        self.files = []
        self.check_vars = []

        self.select_all_var = ctk.BooleanVar()
        self.select_all_checkbox = ctk.CTkCheckBox(self, text="Tümünü Seç", variable=self.select_all_var, command=self.toggle_select_all)
        self.select_all_checkbox.pack(anchor="w", padx=20, pady=(10, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=400)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.total_label = ctk.CTkLabel(self, text="Toplam Alan: 0 B", font=ctk.CTkFont(size=14))
        self.total_label.pack(pady=(0, 10))

        # Butonlar
        button_frame = ctk.CTkFrame(self)
        button_frame.pack()
        ctk.CTkButton(button_frame, text="Taramayı Başlat", command=self.refresh).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Seçilenleri Sil", command=self.delete_selected).pack(side="left", padx=10)

        # Sağ tıklama menüsü
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Detayları Göster", command=self.show_file_details)

        self.right_click_path = None  # Sağ tıklanan dosya

        # Yükleniyor göstergesi
        self.loading_label = ctk.CTkLabel(self, text="Taranıyor...", font=ctk.CTkFont(size=16))
        self.loading_spinner = ctk.CTkProgressBar(self, mode="indeterminate")

    def refresh(self):
        self.loading_label.pack(pady=10)
        self.loading_spinner.pack(pady=(0, 20))
        self.loading_spinner.start()

        threading.Thread(target=self._scan_temp_files, daemon=True).start()

    def _scan_temp_files(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.files = get_temp_files_sorted()
        self.check_vars = []

        total = 0
        for f in self.files:
            var = ctk.BooleanVar()
            path = f['path']
            size = f['size']
            text = f"{path} ({format_bytes(size)})"
            cb = ctk.CTkCheckBox(self.scroll_frame, text=text, variable=var)
            cb.pack(anchor="w", pady=2)

            # Sağ tıklama bağla
            cb.bind("<Button-3>", lambda e, p=path: self.open_context_menu(e, p))

            self.check_vars.append((var, path, size))
            total += size

        # Ana thread'de UI güncelle
        self.after(0, lambda: self._on_scan_complete(total))

    def _on_scan_complete(self, total):
        self.loading_spinner.stop()
        self.loading_spinner.pack_forget()
        self.loading_label.pack_forget()
        self.total_label.configure(text=f"Toplam Alan: {format_bytes(total)}")

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

            # Yeni pencere oluştur
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


if __name__ == "__main__":
    app = TempCleanerApp()
    app.mainloop()
