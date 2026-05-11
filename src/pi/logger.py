import os


class Logger:
    LOG_DIR = "logs"

    def __init__(self):
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self._file = open(self._next_log_path(), "w", encoding="utf-8")
        print(f"Logging to {self._file.name}")

    def _next_log_path(self) -> str:
        existing = [
            f for f in os.listdir(self.LOG_DIR)
            if f.startswith("log_") and f.endswith(".txt")
        ]
        numbers = []
        for name in existing:
            try:
                numbers.append(int(name[4:-4]))
            except ValueError:
                pass
        next_num = max(numbers, default=0) + 1
        return os.path.join(self.LOG_DIR, f"log_{next_num}.txt")

    def log(self, message: str):
        self._file.write(message + "\n")
        self._file.flush()

    def close(self):
        self._file.close()
