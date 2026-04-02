import pygame
import threading
import signal
import time

from parser import Parser
from ui import Ui
from driveController import DriveController

# sem = threading.Semaphore()
stop_event = threading.Event()
running = True

def main():
    pygame.init()
    parser = Parser()
    ui = Ui()

    # global sem
    global running

    

    
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1000, 500))

    signal.signal(signal.SIGINT, handle_kb_interrupt)
    parserThread = threading.Thread(target=parser.pars, args=(), daemon=True) #arges=(sem,)
    parserThread.start()
    clThread = threading.Thread(target=controllLoop, args=(parser,True)) #arges=(sem,)
    clThread.start()


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    stop_event.set()
                if event.key == pygame.K_c:
                    stop_event.set()
                    running = False

        
        ui.draw(screen,parser)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

def handle_kb_interrupt(sig, frame):
    global running
    running = False
    stop_event.set()

def controllLoop(parser,checkVoltage):
    dC = DriveController(parser,stop_event,checkVoltage)
    time.sleep(1)
    dC.driveSpeed(1,0)


if __name__ == "__main__":
    main()