import time
import cv2 as cv # type: ignore
import numpy as np # type: ignore
import libcamera # type: ignore
import argparse
import imutils # type: ignore


from libcamera import Transform # type: ignore
from picamera2 import Picamera2 # type: ignore
from parser import Parser

# rpicam-hello -t0   #zum testen der Kamera

def main():
    cam = Camera()
    cam.captureImage()

class Camera():
    """@brief Camera interface for color-based obstacle detection.

    Captures a blurred horizontal scan band, thresholds HSV for RED/GREEN,
    extracts contour centers, and maps them to angular offsets from optical
    midline. Results stored in blocksAngle / blocksColor lists.
    """
    
    imgCam = np.zeros((1536,846,3), np.uint8)

    blocksColor = []
    blocksCx = []
    blocksCy = []
    pictureNum = 0
    
    def __init__(self, parser: Parser):
        """@brief Initialize Picamera2 and configure capture settings.

        Sets HDR mode, resolution, and starts the camera stream.
        @return None
        """
        
        self.parser = parser

        self.picam2 = Picamera2()
        self.picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.SingleExposure})
        resolution = (1536, 1152)
        self.ySize = resolution[1]
        self.config = self.picam2.create_still_configuration(transform=Transform(vflip=False,hflip=False),main={"size": resolution})   #hflip=True
        self.picam2.configure(self.config)
        #self.picam2.switch_mode_and_capture_array(self.config, delay=10)
        self.picam2.start()
        

    
    def captureImage(self):
        self.pictureNum = self.pictureNum+1
        self.baseImage = self.picam2.capture_array()
        realColor = cv.cvtColor(self.baseImage, cv.COLOR_BGR2RGB)
        cv.imwrite(f'capture/{self.pictureNum}-0baseImage.jpg', realColor)
    def loadImage(self, path):
        realColor = cv.imread(path)
        
        self.baseImage = cv.cvtColor(realColor, cv.COLOR_BGR2RGB)
    def getObstacles2(self):
        """@brief Capture frame, extract scan band, detect RED/GREEN blobs.

        Performs blur, HSV conversion, masking for color ranges (including
        wrap-around red hues), then records each contour's horizontal angle.
        @param checkHeightNear bool If True, lowers scan band for near obstacle perspective.
        @param leftDist float Distance to left wall, used to shift scan band right.
        @param rightDist float Distance to right wall, used to shift scan band left.
        @param upDist float Distance to ceiling, used to lower scan band.
        @param downDistList list of float Distances to floor, used to raise scan band.
        @return None (populates blocksAngle/blocksColor + imgCam for drawing)
        """

        timeStart = time.time()
        self.blocksCx = []
        self.blocksCy = []
        self.blocksColor = []


        imgclear = self.baseImage.copy()


        
        # print(time.time()-timeStart)
        imgIn = cv.blur(imgclear,(10,10))
        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        cv.imwrite(f'capture/{self.pictureNum}-0hsv.jpg', hsv)
        img=imgIn
        
            

        assert hsv is not None, "HSV color conversion failed"

            # in photo shop: rgb -> vsh
            
        # lower boundary RED color range values; Hue (0 - 10)
        lower1 = np.array([0, 190, 190])
        upper1 = np.array([10, 255, 255])
        
        # upper boundary RED color range values; Hue (160 - 180)
        lower2 = np.array([160,100,20])
        upper2 = np.array([179,255,255])
            
        lower_mask = cv.inRange(hsv, lower1, upper1)
        upper_mask = cv.inRange(hsv, lower2, upper2)

        maskred = lower_mask + upper_mask

        lowerGreen = np.array([35, 100, 20])
        upperGreen = np.array([95, 255, 255])

        maskgreen = cv.inRange(hsv, lowerGreen, upperGreen)

        lowerBlack = np.array([0, 0, 0])        # H S V
        upperBlack = np.array([255, 255, 90])     # Letzter wert hier ist die maximale Helligkeit für schwarze Wände
        maskblack = cv.inRange(hsv, lowerBlack, upperBlack)
        
        cv.imwrite(f'capture/{self.pictureNum}-0walls.jpg', maskblack)

        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        regionMask[230:390, 300:1000] = 255
        #               y          x
 

        # Bitwise-AND mask and original image
        
        cv.imwrite(f'capture/{self.pictureNum}-1regionMask.jpg', regionMask)

        
        maskred   = cv.bitwise_and(maskred,   regionMask)
        maskgreen = cv.bitwise_and(maskgreen, regionMask)

        region = cv.bitwise_and(img, img, mask=regionMask)
        cv.imwrite(f'capture/{self.pictureNum}-5imageRegion.jpg', region)
        
       
            
        imgRed = cv.bitwise_and(img, img, mask=maskred)
        imgGreen = cv.bitwise_and(img, img, mask=maskgreen)



        cv.imwrite(f'capture/{self.pictureNum}-7imgRed.jpg', imgRed)
        cv.imwrite(f'capture/{self.pictureNum}-8imgGreen.jpg', imgGreen    )




        cntsgreen = cv.findContours(maskgreen.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        cntsred = cv.findContours(maskred.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)

        cntsred = imutils.grab_contours(cntsred)
        cntsgreen = imutils.grab_contours(cntsgreen)

 
        for c in cntsgreen:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                # cv.line(imgclear,(cX,0),(cX,846),(0,255,0),3)
                cv.circle(imgclear, (cX, cY), 7, (0, 255, 0), -1)
                
                #print("Green at: ", (mid - cX) / split)
                self.blocksCx.append(cX)
                self.blocksCy.append(cY)
                self.blocksColor.append(self.parser.GREEN)

                # result = self.parser.GREEN
                # break

        for c in cntsred:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                # cv.line(imgclear,(cX,0),(cX,846),(0,0,255),3)
                cv.circle(imgclear, (cX, cY), 7, (0, 0, 255), -1)
                
                #print("Red at: ", (mid - cX) / split)
                self.blocksCx.append(cX)
                self.blocksCy.append(cY)
                self.blocksColor.append(self.parser.RED)
                # result = self.parser.RED
                # break
                
        if (len(self.blocksCy) == 0):
            return None
        
        lowestIndex = max(range(len(self.blocksCy)), key=self.blocksCy.__getitem__)
        cX = self.blocksCx[lowestIndex]
        cY = self.blocksCy[lowestIndex]
        color=self.blocksColor[lowestIndex]
        cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)
        
        cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)
        
        return color
        
    def getObstacles1(self):
        
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[200:500, 300:1000] = 255
        #           y          x    
        return self.getObstacles(regionMask,650,490,1)
        #                             x   y
    def getObstacles3(self):
        
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[200:500, 320:1000] = 255
        #           y          x
        
        return self.getObstacles(regionMask,660,490,3)
        #                             x   y
    def getObstacles4(self):
        self.pictureNum=4
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[300:1100, 150:600] = 255
        #           y          x
        return self.getObstacles(regionMask,450,1090,4)
        #                             x   y        
    def getObstacles(self,regionMask,fillx,filly,regionNum):    
        """@brief Capture frame, extract scan band, detect RED/GREEN blobs.

        Performs blur, HSV conversion, masking for color ranges (including
        wrap-around red hues), then records each contour's horizontal angle.
        @param checkHeightNear bool If True, lowers scan band for near obstacle perspective.
        @param leftDist float Distance to left wall, used to shift scan band right.
        @param rightDist float Distance to right wall, used to shift scan band left.
        @param upDist float Distance to ceiling, used to lower scan band.
        @param downDistList list of float Distances to floor, used to raise scan band.
        @return None (populates blocksAngle/blocksColor + imgCam for drawing)
        """
        self.blocksCx = []
        self.blocksCy = []
        self.blocksColor = []

        
        timeStart = time.time()
        # imgclear = cv.imread(f'c:\\t\\capture0.jpg')
        imgclear = self.baseImage.copy()
        # imgclear = cv.cvtColor(imgclear, cv.COLOR_BGR2RGB)

        
        # print(time.time()-timeStart)
        imgIn = cv.blur(imgclear,(10,10))
        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        cv.imwrite(f'capture/{self.pictureNum}-0hsv.jpg', hsv)
        img=imgIn
        
            

        assert hsv is not None, "HSV color conversion failed"

            # in photo shop: rgb -> vsh
            
        # lower boundary RED color range values; Hue (0 - 10)
        lower1 = np.array([0, 190, 190])
        upper1 = np.array([10, 255, 255])
        
        # upper boundary RED color range values; Hue (160 - 180)
        lower2 = np.array([160,100,20])
        upper2 = np.array([179,255,255])
            
        lower_mask = cv.inRange(hsv, lower1, upper1)
        upper_mask = cv.inRange(hsv, lower2, upper2)

        maskred = lower_mask + upper_mask

        lowerGreen = np.array([35, 100, 20])
        upperGreen = np.array([95, 255, 255])

        maskgreen = cv.inRange(hsv, lowerGreen, upperGreen)

        lowerBlack = np.array([0, 0, 0])        # H S V
        upperBlack = np.array([255, 255, 90])     # Letzter wert hier ist die maximale Helligkeit für schwarze Wände
        maskblack = cv.inRange(hsv, lowerBlack, upperBlack)
        
        cv.imwrite(f'capture/{self.pictureNum}-0walls.jpg', maskblack)



        regionMaskInv = cv.bitwise_not(regionMask)
        #               y          x
        
        

        maskblack = cv.bitwise_and(maskblack, regionMask)
        maskblack2 = cv.bitwise_or(maskblack, regionMaskInv)
        

        # Floodfill maskblack starting at x=650, y=400
        floodMask = np.zeros((maskblack2.shape[0] + 2, maskblack2.shape[1] + 2), dtype=np.uint8)
        maskblackFilled = maskblack2.copy()
        cv.floodFill(maskblackFilled, floodMask, (fillx, filly), 128)

        # Maske aller Punkte mit Wert 128 aus maskblackFilled
        maskRegionFinal = np.where(maskblackFilled == 128, np.uint8(255), np.uint8(0))

        # Bitwise-AND mask and original image
        
        cv.imwrite(f'capture/{self.pictureNum}-1maskBlack.jpg', maskblack)
        cv.imwrite(f'capture/{self.pictureNum}-2maskBlack2.jpg', maskblack2)
        cv.imwrite(f'capture/{self.pictureNum}-3maskBlackFilled.jpg', maskblackFilled)
        cv.imwrite(f'capture/{self.pictureNum}-4imageMaskedFlooded.jpg', maskRegionFinal)
        
        
        maskred   = cv.bitwise_and(maskred,   maskRegionFinal)
        maskgreen = cv.bitwise_and(maskgreen, maskRegionFinal)

        imageMasked = cv.bitwise_and(img, img, mask=maskblackFilled)
        
        
        region = cv.bitwise_and(img, img, mask=regionMask)
        cv.imwrite(f'capture/{self.pictureNum}-5imageRegion.jpg', region)
        
        regionFlooded = cv.bitwise_and(img, img, mask=maskRegionFinal)
        cv.imwrite(f'capture/{self.pictureNum}-6regionFlooded.jpg', regionFlooded)    
        
        
            
        imgRed = cv.bitwise_and(img, img, mask=maskred)
        imgGreen = cv.bitwise_and(img, img, mask=maskgreen)



        cv.imwrite(f'capture/{self.pictureNum}-7imgRed.jpg', imgRed)
        cv.imwrite(f'capture/{self.pictureNum}-8imgGreen.jpg', imgGreen    )




        cntsgreen = cv.findContours(maskgreen.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        cntsred = cv.findContours(maskred.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)

        cntsred = imutils.grab_contours(cntsred)
        cntsgreen = imutils.grab_contours(cntsgreen)

        # cv.line(imgclear,(checkWidthStart,checkEnd),(checkWidth+1,checkEnd),(255,0,0),2)
        # cv.line(imgclear,(checkWidthStart,checkHeightStart),(checkWidth+1,checkHeightStart),(255,0,0),2)
            
        mid = 788       # This value sets the midpoint of the image, which is used as a reference to calculate the angle of detected blocks.
        split  = 19.12  # This value is used to scale the difference between the midpoint of the image and the x-coordinate of the detected block's center to calculate the angle.
        
        for c in cntsgreen:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                cv.circle(imgclear, (cX, cY), 7, (0, 255, 0), -1)
                
                self.blocksCx.append(cX)
                self.blocksCy.append(cY)
                self.blocksColor.append(self.parser.GREEN)
                print("Green at: ", cX, cY)

        for c in cntsred:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                # cv.line(imgclear,(cX,0),(cX,846),(0,0,255),3)
                cv.circle(imgclear, (cX, cY), 7, (0, 0, 255), -1)
                
                self.blocksCx.append(cX)
                self.blocksCy.append(cY)
                self.blocksColor.append(self.parser.RED)
                print("Red at: ", cX, cY)
        if (len(self.blocksCx) == 0):
            return None
        if (regionNum == 1 or regionNum == 3):
            index = max(range(len(self.blocksCx)), key=self.blocksCx.__getitem__)
        else:
            index = min(range(len(self.blocksCx)), key=self.blocksCx.__getitem__)
        cX = self.blocksCx[index]
        cY = self.blocksCy[index]
        color=self.blocksColor[index]
        cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)

        cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)

        return color
               



if __name__ == "__main__":
    main()