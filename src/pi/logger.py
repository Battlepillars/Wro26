import os


class Logger:
    LOG_DIR = "logs"

    def __init__(self):
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self._file = open(self._next_log_path(), "w", encoding="utf-8")
        print(f"Logging to {self._file.name}")

    MAX_LOGS = 10

    def _next_log_path(self) -> str:
        # Shift existing logs up by one (log_1 → log_2, …), drop any beyond MAX_LOGS
        existing = [
            f for f in os.listdir(self.LOG_DIR)
            if f.startswith("log_") and f.endswith(".txt")
        ]
        numbers = sorted(
            (int(name[4:-4]) for name in existing if name[4:-4].isdigit()),
            reverse=True,
        )
        for n in numbers:
            src = os.path.join(self.LOG_DIR, f"log_{n}.txt")
            if n + 1 > self.MAX_LOGS:
                os.remove(src)
            else:
                os.rename(src, os.path.join(self.LOG_DIR, f"log_{n + 1}.txt"))
        return os.path.join(self.LOG_DIR, "log_1.txt")

    def log(self, message: str):
        self._file.write(message + "\n")
        self._file.flush()

    def logTof(self, parser, camera: int):
        """Log the 8x8 ToF grid for one sensor index, mirroring the ui.py layout."""
        size = 8
        lines = [f"ToF sensor {camera}:"]
        for j in range(size):
            row = ""
            for k in range(size):
                val = parser.camValues[camera][j * size + k]
                if val <= 0:
                    row += "     - "
                elif val < 10:
                    row += f"     {val} "
                elif val < 100:
                    row += f"    {val} "
                elif val < 1000:
                    row += f"   {val} "
                else:
                    row += f"  {val} "
            lines.append(row)
        self.log("\n".join(lines))

    def close(self):
        self._file.close()
