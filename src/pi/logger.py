import os


class Logger:
    """@brief Rotating text logger for recording test and drive events.

    Each run opens a fresh log_1.txt and shifts older logs up, keeping at most
    MAX_LOGS files.
    """
    LOG_DIR = "logs"

    def __init__(self):
        """@brief Create the log directory and open a new log file for this run.

        @return None
        """
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self._file = open(self._next_log_path(), "w+", encoding="utf-8")
        self.lineCount = 0
        print(f"Logging to {self._file.name}")

    MAX_LOGS = 10

    def _next_log_path(self) -> str:
        """@brief Rotate existing logs and return the path for the new log file.

        Renames log_1 -> log_2, … dropping any beyond MAX_LOGS, so the newest
        run is always log_1.txt.
        @return str path of the log file to open for this run.
        """
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
        """@brief Write a numbered message as a new line and flush to disk.

        @param message str text to record.
        @return None
        """
        self._file.write(f"{self.lineCount} {message}\n")
        self._file.flush()
        self.lineCount += 1

    def logAppend(self, message: str):
        """Append message to the current last line instead of starting a new line."""
        end = self._file.seek(0, 2)   # jump to end of file
        if end > 0:
            self._file.seek(end - 1)
            # Strip the trailing newline so the message extends the last line.
            if self._file.read(1) == "\n":
                self._file.seek(end - 1)
                self._file.truncate()
        self._file.write(" " + message + "\n")
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
        """@brief Close the underlying log file.

        @return None
        """
        self._file.close()
