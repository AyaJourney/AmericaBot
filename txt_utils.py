from tkinter import Tk, filedialog
import sys

def select_txt_file():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="TXT dosyasını seç",
        filetypes=[("Text Files", "*.txt")]
    )
    if not file_path:
        print("❌ TXT seçilmedi")
        sys.exit()
    return file_path


def read_txt_data(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            data[key.strip().upper()] = value.strip()

    return data



def append_to_txt(path, key, value):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{key.strip().upper()}={value.strip()}")