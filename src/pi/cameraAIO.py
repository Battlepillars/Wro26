import time
import cv2 as cv # type: ignore
import numpy as np # type: ignore
import libcamera # type: ignore
import argparse
import imutils # type: ignore
from subprocess import call


from libcamera import Transform # type: ignore
from picamera2 import Picamera2 # type: ignore
from parser import Parser

# rpicam-hello -t0   #zum testen der Kamera

def main():
    """@brief Standalone entry point: capture a single image for testing.

    @return None
    """
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
    
    # Exposure times (microseconds) used for custom HDR fusion.
    # Tune these for your lighting conditions: dark scene → lower values,
    # bright scene → higher values. Three stops apart is a good starting point.
    HDR_EXPOSURES_US = [500, 4000, 32000]
    
    def __init__(self, parser: Parser):
        """@brief Initialize Picamera2 and configure capture settings.

        Sets HDR mode, resolution, and starts the camera stream.
        @return None
        """
        
        self.parser = parser

        self.picam2 = Picamera2()
        self.picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.SingleExposure})
        # self.picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.Off})     
        # 
        # 
        #  to enable custom hdr , enable the line above (disable single exposure)and the captureHdr() method below
        #
        #
        resolution = (1536, 1152)
        self.ySize = resolution[1]
        self.config = self.picam2.create_still_configuration(transform=Transform(vflip=False,hflip=False),main={"size": resolution})   #hflip=True
        self.picam2.configure(self.config)
        self.picam2.start()
        
        self.defaultColor = self.parser.GREEN
        
        # lower boundary RED color range values; Hue (0 - 10)
        #                          H    S    V
        self.redlower1 = np.array([0,  150, 120]) #v 120->100
        self.redupper1 = np.array([10, 255, 255])
        
        # upper boundary RED color range values; Hue (160 - 180)
        #                           H    S   V
        self.redlower2 = np.array([160, 100, 20])
        self.redupper2 = np.array([179, 255,255])

        #                           H     S    V 
        self.lowerGreen = np.array([35,  80,  20])
        self.upperGreen = np.array([95,  255,  255])


        #                             H    S   V
        self.lowerBlack = np.array([  0,   0,  0])  # H S V Min Wert für Schwarz
        self.upperBlack = np.array([255, 255, 50])  # Max Wert für Schwarz,   v = 90            # v = 40   --change
                                                    # Letzter wert hier ist die maximale Helligkeit für schwarze Wände
                                                    # in Photoshop :
                                                    #   R = Value       - Helligkeit
                                                    #   G = Saturation  - Farbintensität
                                                    #   B = Hue         - Farbton 


    def captureImage(self):
        """@brief Grab a still frame from the camera and save it to disk.

        Stores the RGB frame in `self.baseImage` and writes a numbered JPEG
        into the capture folder.
        @return None
        """
        # self.captureHdr()
        # return
        
        # 
        # 
        #  to enable custom hdr , enable the 2 line above and  switch from SingleExposure to HdrModeEnum.Off in __init_
        #
        #       
        
        self.pictureNum = self.pictureNum+1
        self.baseImage = self.picam2.capture_array()
        realColor = cv.cvtColor(self.baseImage, cv.COLOR_BGR2RGB)
        cv.imwrite(f'capture/{self.pictureNum}-0baseImage.jpg', realColor)

    def captureHdr(self):
        """Capture multiple frames at different exposures and merge with Mertens
        fusion. Result is stored in self.baseImage like captureImage().
        Slower than captureImage (~3x frames) but handles high-contrast scenes.
        """
        self.pictureNum += 1
        frames = []
        for exposure_us in self.HDR_EXPOSURES_US:
            self.picam2.set_controls({
                'AeEnable': False,
                'ExposureTime': exposure_us,
            })
            # Wait two frames so the new exposure takes effect
            self.picam2.capture_array()
            self.picam2.capture_array()
            frame = self.picam2.capture_array()
            frames.append(cv.cvtColor(frame, cv.COLOR_RGB2BGR))

        # Re-enable auto exposure for subsequent normal captures
        self.picam2.set_controls({'AeEnable': True})

        merged = cv.createMergeMertens().process(frames)
        merged_8u = np.clip(merged * 255, 0, 255).astype(np.uint8)
        self.baseImage = cv.cvtColor(merged_8u, cv.COLOR_BGR2RGB)
        cv.imwrite(f'capture/{self.pictureNum}-0baseImage.jpg', merged_8u)
    def loadImage(self, path):
        """@brief Load an image from disk into `self.baseImage` for analysis.

        @param path str file path of the image to load.
        @return None
        """
        realColor = cv.imread(path)
        
        self.baseImage = cv.cvtColor(realColor, cv.COLOR_BGR2RGB)
    def getObstacles2(self, mask = [230,390, 300,1000], defaultColor=20):
        """@brief Detect the dominant obstacle color inside a rectangular region.

        Blurs the frame, converts to HSV, builds RED/GREEN masks (including the
        wrap-around red hue range), restricts them to `mask`, and returns the
        color of the lowest (nearest) detected blob.
        @param mask         list [y0, y1, x0, x1] pixel bounds of the region.
        @param defaultColor color returned when no obstacle is found (20 = use
                            the camera's configured default).
        @return the detected obstacle color, or the default color.
        """

        timeStart = time.time()
        self.blocksCx = []
        self.blocksCy = []
        self.blocksColor = []

        if defaultColor == 20:
            defaultColor = self.defaultColor

        imgclear = self.baseImage.copy()


        
        # print(time.time()-timeStart)
        imgIn = cv.blur(imgclear,(10,10))
        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        cv.imwrite(f'capture/{self.pictureNum}-0hsv.jpg', hsv)
        img=imgIn
        
            

        assert hsv is not None, "HSV color conversion failed"


        lower_mask = cv.inRange(hsv, self.redlower1, self.redupper1)
        upper_mask = cv.inRange(hsv, self.redlower2, self.redupper2)
        
        maskred = lower_mask + upper_mask
        maskgreen = cv.inRange(hsv, self.lowerGreen, self.upperGreen)
        maskblack = cv.inRange(hsv, self.lowerBlack, self.upperBlack)
        
        cv.imwrite(f'capture/{self.pictureNum}-0walls.jpg', maskblack)

        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        regionMask[mask[0]:mask[1], mask[2]:mask[3]] = 255
        #                 y                  x


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
                
                cv.circle(imgclear, (cX, cY), 7, (0, 255, 0), -1)
                area = cv.contourArea(c)
                
                cv.putText(imgclear, str(int(area)), (cX + 20, cY), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                if area> 100:
                    self.blocksCx.append(cX)
                    self.blocksCy.append(cY)
                    self.blocksColor.append(self.parser.GREEN)
                print("Green at: ", cX, cY, "Area: ", area) 
                

        for c in cntsred:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                
                cv.circle(imgclear, (cX, cY), 7, (0, 0, 255), -1)
                area = cv.contourArea(c)
                
                cv.putText(imgclear, str(int(area)), (cX + 20, cY), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if area> 100:
                    self.blocksCx.append(cX)
                    self.blocksCy.append(cY)
                    self.blocksColor.append(self.parser.RED)
                print("Red at: ", cX, cY, "Area: ", area)
                
        if (len(self.blocksCy) == 0):
            cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)
            return defaultColor
        
        lowestIndex = max(range(len(self.blocksCy)), key=self.blocksCy.__getitem__)
        cX = self.blocksCx[lowestIndex]
        cY = self.blocksCy[lowestIndex]
        color=self.blocksColor[lowestIndex]
        cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)
        
        cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)
        
        return color
        
    def getObstacles1(self):
        """@brief Detect the obstacle in section-1's field of view (flood-fill ROI).

        @return the detected obstacle color, or the default color.
        """
        
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[260:510, 400:1150] = 255   # y: [300:550] 
        #           y          x    
        return self.getObstacles(regionMask,800,500,1)  # y: 540
        #                                    x   y
    def getObstacles1b(self):
        """@brief Detect the extra section-0 obstacle from the section-1 image.

        @return the detected obstacle color, or the default color.
        """
        self.pictureNum += 1
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8) 
        return self.getObstacles2([600,1000, 400,1150],None)
        #      
    def getObstacles3(self):
        """@brief Detect the obstacle in section-3's field of view (flood-fill ROI).

        @return the detected obstacle color, or the default color.
        """
        
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[225:400, 500:1350] = 255   #[275:450, 500:1350]
        #           y          x
        
        return self.getObstacles(regionMask,800,390,3)
        #                                    x   y
    def getObstacles4(self):
        """@brief Detect the obstacle in section-0's field of view (flood-fill ROI).

        @return the detected obstacle color, or the default color.
        """
        self.pictureNum=4
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[340:900, 300:1150] = 255
        #           y          x
        return self.getObstacles(regionMask,759,890,4)
        #                                    x   y    
    def getObstacles3b(self):
        """@brief Alternate section-3 detection with a wider ROI (clockwise scan).

        @return the detected obstacle color, or the default color.
        """
        
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[200:450, 500:1400] = 255  # y: 200:450   x: 500:1400
        #           y          x
        
        return self.getObstacles(regionMask,800,440,3)  # 800,440
        #                             x   y
    def getObstacles4b(self):
        """@brief Alternate section-0 (left) detection ROI (clockwise scan).

        @return the detected obstacle color, or the default color.
        """
        self.pictureNum=5
        # Maske x: 500-1000, y: 300-800
        regionMask = np.zeros(self.baseImage.shape[:2], dtype=np.uint8)
        regionMask[360:700, 280:800] = 255
        #           y          x
        return self.getObstacles(regionMask,400,690,4)
        #                                     x   y 
    def getObstacles(self,regionMask,fillx,filly,regionNum,minSize=200):    
        """@brief Detect an obstacle inside a flood-filled drivable region.

        Uses the black course walls as a flood-fill barrier so only the
        drivable area is analyzed, masks RED/GREEN inside it, and returns the
        most relevant blob's color (rightmost for sections 1/3, nearest otherwise).
        @param regionMask ndarray initial region-of-interest mask.
        @param fillx      int flood-fill seed x coordinate (inside the track).
        @param filly      int flood-fill seed y coordinate (inside the track).
        @param regionNum  int section index, selecting the blob-picking rule.
        @param minSize    int minimum contour area (px^2) to accept a blob.
        @return the detected obstacle color, or the default color.
        """
        self.blocksCx = []
        self.blocksCy = []
        self.blocksColor = []
        self.blocksDist = []

        
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

        lower_mask = cv.inRange(hsv, self.redlower1, self.redupper1)
        upper_mask = cv.inRange(hsv, self.redlower2, self.redupper2)
        
        maskred = lower_mask + upper_mask
        maskgreen = cv.inRange(hsv, self.lowerGreen, self.upperGreen)
        maskblack = cv.inRange(hsv, self.lowerBlack, self.upperBlack)
        
        cv.imwrite(f'capture/{self.pictureNum}-0walls.jpg', maskblack)



        regionMaskInv = cv.bitwise_not(regionMask)
        #               y          x
        
        

        # Treat everything outside the ROI as "wall" so the flood fill can only
        # spread across the drivable area inside the region.
        maskblack = cv.bitwise_and(maskblack, regionMask)
        maskblack2 = cv.bitwise_or(maskblack, regionMaskInv)
        

        # Flood fill from a seed known to be on the track; the black walls act
        # as barriers, so only the reachable floor gets marked (value 128).
        floodMask = np.zeros((maskblack2.shape[0] + 2, maskblack2.shape[1] + 2), dtype=np.uint8)
        maskblackFilled = maskblack2.copy()
        cv.floodFill(maskblackFilled, floodMask, (fillx, filly), 128)

        # Keep only the flooded (drivable) pixels as the final analysis mask.
        maskRegionFinal = np.where(maskblackFilled == 128, np.uint8(255), np.uint8(0))

        # Bitwise-AND mask and original image
        
        cv.imwrite(f'capture/{self.pictureNum}-1maskBlack.jpg', maskblack)
        cv.imwrite(f'capture/{self.pictureNum}-2maskBlack2.jpg', maskblack2)
        cv.imwrite(f'capture/{self.pictureNum}-3maskBlackFilled.jpg', maskblackFilled)
        cv.imwrite(f'capture/{self.pictureNum}-4imageMaskedFlooded.jpg', maskRegionFinal)
        
        
        # Restrict the color masks to the drivable area: obstacles behind walls
        # or off the course are discarded.
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
        cv.imwrite(f'capture/{self.pictureNum}-8imgGreen.jpg', imgGreen)




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
                
                area = cv.contourArea(c)
                cv.putText(imgclear, str(int(area)), (cX + 20, cY), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if area> minSize:
                    self.blocksCx.append(cX)
                    self.blocksCy.append(cY)
                    self.blocksColor.append(self.parser.GREEN)
                    _h, _w = imgclear.shape[:2]
                    self.blocksDist.append(((cX - _w // 2) ** 2 + (cY - _h) ** 2) ** 0.5)
                print("Green at: ", cX, cY, "Area: ", area)

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
                area = cv.contourArea(c)
                cv.putText(imgclear, str(int(area)), (cX + 20, cY), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if area> minSize:
                    self.blocksCx.append(cX)
                    self.blocksCy.append(cY)
                    self.blocksColor.append(self.parser.RED)
                    _h, _w = imgclear.shape[:2]
                    self.blocksDist.append(((cX - _w // 2) ** 2 + (cY - _h) ** 2) ** 0.5)
                print("Red at: ", cX, cY, "Area: ", area)
        if (len(self.blocksCx) == 0):
            cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)
            return self.defaultColor
        # Sections 1/3 pick the rightmost blob; others pick the nearest one
        # (closest to the bottom-center of the frame).
        if (regionNum == 1 or regionNum == 3):
            index = max(range(len(self.blocksCx)), key=self.blocksCx.__getitem__)
        else:
            index = min(range(len(self.blocksDist)), key=self.blocksDist.__getitem__)
        cX = self.blocksCx[index]
        cY = self.blocksCy[index]
        color=self.blocksColor[index]
        cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)

        cv.imwrite(f'capture/{self.pictureNum}-9detection_result.jpg', imgclear)

        return color



if __name__ == "__main__":
    main()
