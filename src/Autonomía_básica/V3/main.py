#!/usr/bin/env python3
# main.py

import multiprocessing as mp
import signal
import sys

def signal_handler(sig, frame):
    print("\n[Main] Cerrando...")
    if proc_qr.is_alive():
        proc_qr.terminate()
        proc_qr.join()
    sys.exit(0)

if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)

    mp.set_start_method('spawn', force=True)

    qr_queue = mp.Queue()
    action_queue = mp.Queue()
    line_status_queue = mp.Queue()
    status_queue = mp.Queue()

    from Vision_Artificial.motor_control import run_motor_control
    from Vision_Artificial.qr_logic import run_qr_logic

    proc_qr = mp.Process(
        target=run_qr_logic,
        args=(qr_queue, action_queue, line_status_queue, status_queue),
        daemon=True
    )

    proc_qr.start()

    print("[Main] Stream en: http://<IP>:5000")

    run_motor_control(qr_queue, action_queue, line_status_queue, status_queue)