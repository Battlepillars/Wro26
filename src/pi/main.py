import pygame
import threading
import signal
import time
import openChallenge
import obstacleChallenge
import camTest
import obstacleChallengeSingle
import os
import shutil

from autoChallenge import autoChallenge
from parser import Parser
from ui import Ui
from driveController import DriveController
from cameraAIO import Camera

stop_event = threading.Event()
start_event = threading.Event()
running = True

def main():
    pygame.init()
    parser = Parser()
    cam = Camera(parser)
    ui = Ui()

    global running
    
    manual = False
    speed = 0
    steer = 90
    
    
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1220, 500), pygame.RESIZABLE)
    
    signal.signal(signal.SIGINT, handle_kb_interrupt)
    parserThread = threading.Thread(target=parser.pars, args=(), daemon=True)
    parserThread.start()
    clThread = threading.Thread(target=controllLoop, args=(parser, cam), daemon=True)
    clThread.start()

    parser.sendReadySignal()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                #screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # pygame.transform.scale(screen, (event.w, event.h))
                pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:   # stop driving
                    manual = True
                    stop_event.set()
                    start_event.set()
                if event.key == pygame.K_c:       # exit
                    stop_event.set()
                    running = False
                if event.key == pygame.K_m:       # toggle manual mode
                    print("Toggling manual mode")
                    manual = not manual
                    stop_event.set()
                    start_event.set()
                if event.key == pygame.K_v:
                    start_event.set()
                if event.key == pygame.K_t:
                    if parser.uiType != parser.Capture_Dynamic:
                        parser.loadImages
                        parser.uiType = parser.Capture_Dynamic
                    else:
                        parser.uiType = parser.Default
                if event.key == pygame.K_u:
                    cam.getNearestObstacle()
            if event.type == pygame.MOUSEBUTTONDOWN:
                length = len(parser.images) if parser.imageType == parser.All else len(parser.hsvImages)
                if event.button == 1 and parser.currentImage > 0:
                    parser.currentImage -= 1
                if event.button == 3 and parser.currentImage < length - 1:
                    parser.currentImage += 1
                
                if event.button == 2:
                    if parser.imageType == parser.All:
                        parser.imageType = parser.HSV
                        # path = f"{parser.images[parser.currentImage]}"
                        # parser.currentImage = findCloesetHsvImage(parser.images, path)
                        parser.currentImage = 0
                    else:
                        parser.imageType = parser.All
                        path = f"{parser.hsvImages[parser.currentImage]}"
                        parser.currentImage = parser.images.index(path)
        
        if parser.button and not parser.started:
            parser.started = True
            start_event.set()

        if manual:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                speed = 1
            elif keys[pygame.K_s]:
                speed = -1
            else:
                speed = 0
            if keys[pygame.K_a]:
                steer = 180
            elif keys[pygame.K_d]:
                steer = 0
            else:
                steer = 90
            
            # print("Speed: "+str(speed)+" Steer: "+str(steer))
            parser.setSpeed(speed)
            parser.setSteer(steer)

        
        ui.draw(screen,parser,cam)

        pygame.display.flip()
        if manual:
            clock.tick(30)
        else:
            clock.tick(30)
    pygame.quit()

def findCloesetHsvImage(images, path):
    indexes = [i for i, value in enumerate(images) if value == path]
    return indexes[0] if indexes else 0

def handle_kb_interrupt(sig, frame):
    global running
    running = False
    stop_event.set()

def controllLoop(parser,cam):
    dC = DriveController(parser,stop_event)
    
    start_event.wait()
    parser.startTime = time.time()
    if stop_event.is_set():
        return
    
    parser.resetGyro()
    shiftCaptures()

    print("Started")
    
    # obstacleChallengeSingle.scanSimulation(parser, cam)
    # obstacleChallengeSingle.scanClockwiseSimulation(parser, cam)
    # obstacleChallengeSingle.scanCounterClockwiseSimulation(parser, cam )
    autoChallenge(parser, dC, cam)
    
    
    # camTest.test(parser, dC, cam)
    # cam.getNearestObstacle()


def shiftCaptures():
    # Shift capture folders: capture → capture1, capture1 → capture2, …
    MAX_CAPTURE_DIRS = 10
    for n in range(MAX_CAPTURE_DIRS, 0, -1):
        src = "capture" + (str(n) if n > 1 else "")
        dst = f"capture{n + 1}"
        if os.path.isdir(src):
            if n >= MAX_CAPTURE_DIRS:
                shutil.rmtree(src)
            else:
                os.rename(src, dst)
    os.makedirs("capture", exist_ok=True)



if __name__ == "__main__":
    main()