import pygame   #type: ignore
import math

clock = pygame.time.Clock()
running = True

class Ui:
    def __init__(self):
        self.uiScale = 1
        self.font = pygame.font.Font('freesansbold.ttf',20)

    def draw(self, screen, parser):
        screen.fill("black")

        green = (0, 255, 0)
        blue = (0, 0, 128)
        

        
        for i in range(4):
            for j in range(8):
                for k in range(8):
                    pos = j*8+k
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
        
        prints = 3
        for i in range(prints):
            if i == 0:
                text = self.font.render("Voltage: " + str(parser.voltage), True, green, blue)       #10,5min
            if i == 1:
                text = self.font.render("Speed: " + str(parser.speed), True, green, blue)             #26,5
            if i == 2:
                text = self.font.render("Distance: " + str(parser.distance), True, green, blue)             #26,5
            screen.blit(text, (0,i*20+360))