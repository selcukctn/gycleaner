import os
import tempfile

# Tarama yapılacak klasörler
TARGET_DIRS = [
    tempfile.gettempdir(),          # %TEMP%
    r"C:\Windows\Temp",             # Windows geçici dosyalar
    os.path.expanduser(r"~\AppData\Local\Temp"),  # Kullanıcı temp
]

# Silinmeyecek dosyalar (beyaz liste)
WHITELIST = [
    "dont_delete.txt",
    "important.log"
]
