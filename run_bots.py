"""
run_bots.py -- DS-160 Bot Manager
Kullanim:
  python run_bots.py            -> 3 bot baslatir (varsayilan)
  python run_bots.py --bots 5   -> 5 bot baslatir
  python run_bots.py --bots 1   -> tek bot (test)
  burası kontrol
"""

import argparse
import subprocess
import sys
import time
import os

parser = argparse.ArgumentParser()
parser.add_argument("--bots", type=int, default=3, help="Kac bot baslatilacak")
args = parser.parse_args()

BOT_COUNT   = args.bots
MAIN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
LOG_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

os.makedirs(LOG_DIR, exist_ok=True)

print(f"{BOT_COUNT} bot baslatiliyor...")
print(f"Log klasoru: {LOG_DIR}")

log_files = {}
procs     = {}

# Windows UTF-8 encoding icin environment
bot_env = os.environ.copy()
bot_env["PYTHONUTF8"] = "1"
bot_env["PYTHONIOENCODING"] = "utf-8"

def start_bot(bot_id: int):
    log_path = os.path.join(LOG_DIR, f"bot-{bot_id}.log")
    log_file = open(log_path, "a", encoding="utf-8")
    log_files[bot_id] = log_file

    p = subprocess.Popen(
        [sys.executable, "-u", MAIN_SCRIPT, "--bot-id", str(bot_id)],
        stdout=log_file,
        stderr=log_file,
        text=True,
        env=bot_env,
    )
    print(f"BOT-{bot_id} baslatildi (PID: {p.pid}) -> {log_path}")
    return p

for i in range(1, BOT_COUNT + 1):
    procs[i] = start_bot(i)
    time.sleep(2)

print(f"\nTum {BOT_COUNT} bot calisiyor.")
print(f"Loglar: logs/bot-1.log, bot-2.log ...")
print(f"Durdurmak icin: Ctrl+C\n")

try:
    while True:
        for bot_id in list(procs.keys()):
            ret = procs[bot_id].poll()
            if ret is not None:
                print(f"BOT-{bot_id} durdu (exit={ret}), 5 saniye sonra yeniden baslatiliyor...")
                if bot_id in log_files:
                    try:
                        log_files[bot_id].close()
                    except Exception:
                        pass
                time.sleep(5)
                procs[bot_id] = start_bot(bot_id)
        time.sleep(5)

except KeyboardInterrupt:
    print("\nTum botlar durduruluyor...")
    for bot_id, proc in procs.items():
        try:
            proc.terminate()
            print(f"  BOT-{bot_id} durduruldu (PID: {proc.pid})")
        except Exception:
            pass
    for lf in log_files.values():
        try:
            lf.close()
        except Exception:
            pass
    print("Tamamlandi")