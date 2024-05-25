import threading


def scheduler_start(worker):
    thread = threading.Thread(target=worker)
    thread.start()
