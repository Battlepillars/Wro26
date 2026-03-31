import pygame   #type: ignore

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
            if len(parser.camValues[i]) == 64:
                for j in range(8):
                    for k in range(8):
                        pos = j*8+k
                        val = parser.camValues[i][pos]
                        if val <= 0:
                            text = "   -" 
                        elif val < 10:
                            text = "   "+str(val)
                        elif val < 100:
                            text = "  "+str(val)
                        elif val < 1000:
                            text = " "+str(val)
                        else:
                            text = str(val)
                        
                        text = self.font.render(text, True, green, blue)

                        screen.blit(text, (40*k * self.uiScale, j * 20))