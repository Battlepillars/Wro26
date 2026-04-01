import pygame
import threading

from parser import Parser
from ui import Ui
from driveController import DriveController

# sem = threading.Semaphore()


def main():
    pygame.init()
    parser = Parser()
    ui = Ui()

    # global sem

    running = True

    
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1000, 500))

    parserThread = threading.Thread(target=parser.pars, args=(), daemon=True) #arges=(sem,)
    parserThread.start()
    clThread = threading.Thread(target=controllLoop, args=(parser,), daemon=True) #arges=(sem,)
    clThread.start()


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        
        ui.draw(screen,parser)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

def controllLoop(parser):
    dC = DriveController(parser)
    dC.driveSpeed(1)


if __name__ == "__main__":
    main()