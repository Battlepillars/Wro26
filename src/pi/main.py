import pygame
import threading
import signal
import time
import openChallenge
import obstacleChallenge

from parser import Parser
from ui import Ui
from driveController import DriveController
from camera import Camera

stop_event = threading.Event()
start_event = threading.Event()
running = True

def main():
    pygame.init()
    parser = Parser()
    ui = Ui()

    global running
    
    manual = False
    speed = 0
    steer = 90
    
    
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1000, 500))

    signal.signal(signal.SIGINT, handle_kb_interrupt)
    parserThread = threading.Thread(target=parser.pars, args=(), daemon=True)
    parserThread.start()
    clThread = threading.Thread(target=controllLoop, args=(parser,), daemon=True)
    clThread.start()


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:   # stop driving
                    manual = not manual
                    stop_event.set()
                    start_event.set()
                if event.key == pygame.K_c:       # exit
                    stop_event.set()
                    running = False
                if event.key == pygame.K_m:       # toggle manual mode
                    manual = not manual
                    stop_event.set()
                    start_event.set()
                if event.key == pygame.K_v:
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

        
        ui.draw(screen,parser)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

def handle_kb_interrupt(sig, frame):
    global running
    running = False
    stop_event.set()

def controllLoop(parser):
    dC = DriveController(parser,stop_event)
    cam = Camera()
    
    start_event.wait()
    if stop_event.is_set():
        return
    parser.setLowVoltageCheck(True)
    #dC.driveDist(0.2,90,1000)
    #openChallenge.clockwise(parser, dC)
    obstacleChallenge.clockwise(parser, dC, cam)



if __name__ == "__main__":
    main()