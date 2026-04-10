import math
import subprocess
import time

import pygame   #type: ignore

clock = pygame.time.Clock()
running = True

class Ui:
    def __init__(self):
        self.uiScale = 1
        self.font = pygame.font.Font('freesansbold.ttf',20)
        self.cpu_usage = "--"
        self.cpu_temp = "--"
        self.cpu_throttled = "unknown"
        self._last_cpu_sample = None
        self._last_telemetry_refresh = 0.0

    def _read_cpu_usage(self):
        try:
            with open("/proc/stat", "r", encoding="utf-8") as proc_stat:
                cpu_fields = proc_stat.readline().split()[1:]

            values = [int(value) for value in cpu_fields]
            idle_time = values[3] + values[4]
            total_time = sum(values)

            if self._last_cpu_sample is None:
                self._last_cpu_sample = (idle_time, total_time)
                return None

            prev_idle, prev_total = self._last_cpu_sample
            self._last_cpu_sample = (idle_time, total_time)

            total_delta = total_time - prev_total
            idle_delta = idle_time - prev_idle
            if total_delta <= 0:
                return None

            return 100.0 * (total_delta - idle_delta) / total_delta
        except (FileNotFoundError, IndexError, ValueError):
            return None

    def _read_cpu_temperature(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as temp_file:
                return float(temp_file.read().strip()) / 1000.0
        except (FileNotFoundError, ValueError):
            return None


    def updatePiTelemetry(self):
        now = time.monotonic()
        if now - self._last_telemetry_refresh < 1.0:
            return

        cpu_usage = self._read_cpu_usage()
        cpu_temp = self._read_cpu_temperature()

        if cpu_usage is not None:
            self.cpu_usage = f"{cpu_usage:.1f}%"
        if cpu_temp is not None:
            self.cpu_temp = f"{cpu_temp:.1f}C"

        self._last_telemetry_refresh = now

    def draw(self, screen, parser):
        self.updatePiTelemetry()
        screen.fill("black")

        green = (0, 255, 0)
        blue = (0, 0, 128)
        
        size=8
        
        for i in range(4):
            for j in range(size):
                for k in range(size):
                    pos = j*size+k
                    
                    val = parser.camValues[i][pos]
                    if val <= 0:
                        text = "      -"
                    elif val < 10:
                        text = "      "+str(val)
                    elif val < 100:
                        text = "    "+str(val)
                    elif val < 1000:
                        text = "  "+str(val)
                    else:
                        text = str(val)
                    
                    text = self.font.render(text, True, green, blue)

                    if i < 2:
                        screen.blit(text, (50*k+i*410, j * 20))
                    else:
                        screen.blit(text, (50*k+(i-2)*410, j*20+180))
        
        prints = 4
        for i in range(prints):
            if i == 0:
                text = self.font.render(str(parser.voltage) + "v CPU: " + self.cpu_usage + " Temp: " + self.cpu_temp , True, green, blue)
            if i == 1:
                text = self.font.render("Speed: " + str(parser.speed)+" Head: "+str(parser.gyro.euler[0]), True, green, blue)             #26,5
            if i == 2:
                text = self.font.render("Distance: " + str(parser.distance), True, green, blue)             #26,5
            if i == 3:
                text = self.font.render("Captures: "+ str(parser.sensorCaptures[0])+" / "+str(parser.sensorCaptures[1])+" / "+str(parser.sensorCaptures[2])+" / "+str(parser.sensorCaptures[3]), True, green, blue)
            screen.blit(text, (0,i*20+360))