import time
import cv2 as cv # type: ignore
import numpy as np # type: ignore
import libcamera # type: ignore
import imutils # type: ignore
from subprocess import call


from libcamera import Transform # type: ignore
from picamera2 import Picamera2 # type: ignore
from parser import Parser

# rpicam-hello -t0   #zum testen der Kamera

def main():
    cam = Camera()
    cam.captureImage()

class Camera():
    """@brief Camera interface for color-based obstacle detection.

    Captures a blurred scan quader, thresholds HSV for RED/GREEN,
    extracts contour centers.
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
        
        self.defaultColor = None
        
        # lower boundary RED color range values; Hue (0 - 10)
        #                          H    S    V
        self.redlower1 = np.array([0,  150, 120])
        self.redupper1 = np.array([10, 255, 255])
        
        # upper boundary RED color range values; Hue (160 - 180)
        #                           H    S   V
        self.redlower2 = np.array([160, 100, 20])
        self.redupper2 = np.array([179, 255,255])

        #                           H     S    V 
        self.lowerGreen = np.array([35,  80,  20])
        self.upperGreen = np.array([95,  255,  255])

        # in Photoshop :
        #   R = Value       - Helligkeit
        #   G = Saturation  - Farbintensität
        #   B = Hue         - Farbton 
        
        
        self.quaders = {"CW": {},"CCW": {}}
        self.addQuader("CW", 0, 20, 20, 400, 400)
        self.addQuader("CW", 1, 20, 20, 400, 400)
        self.addQuader("CW", 2, 20, 20, 400, 400)
        self.addQuader("CW", 3, 20, 20, 400, 400)
        self.addQuader("CW", 4, 20, 20, 400, 400)
        self.addQuader("CW", 5, 20, 20, 400, 400)
        self.addQuader("CW", 6, 20, 20, 400, 400)
        self.addQuader("CW", 7, 20, 20, 400, 400)
        self.addQuader("CW", 8, 20, 20, 400, 400)
        self.addQuader("CW", 9, 20, 20, 400, 400)
        self.addQuader("CW", 10, 20, 20, 400, 400)
        self.addQuader("CW", 11, 20, 20, 400, 400)
        
        # self.addQuader("CCW", 0, 20, 20, 400, 400)
        self.addQuader("CCW", 1, 20, 20, 400, 400)
        self.addQuader("CCW", 2, 20, 20, 400, 400)
        self.addQuader("CCW", 3, 20, 20, 400, 400)
        self.addQuader("CCW", 4, 20, 20, 400, 400)
        self.addQuader("CCW", 5, 20, 20, 400, 400)
        self.addQuader("CCW", 6, 20, 20, 400, 400)
        self.addQuader("CCW", 7, 20, 20, 400, 400)
        self.addQuader("CCW", 8, 20, 20, 400, 400)
        self.addQuader("CCW", 9, 20, 20, 400, 400)
        self.addQuader("CCW", 10, 20, 20, 400, 400)
        self.addQuader("CCW", 11, 20, 20, 400, 400)
        
        self.addQuader("CCW", 0, 429, 331, 518, 460)

    def addQuader(self, direction, number, leftX, topY, rightX, bottomY):
        if direction not in self.quaders:
            return
        self.quaders[direction][str(number)] = {
            "leftX": leftX,
            "topY": topY,
            "rightX": rightX,
            "bottomY": bottomY,
        }

    def createQuadar(self, capture):
        # Load the image
        if capture:
            self.captureImage()
        else:
            self.loadImage("captureStore/1-0baseImage.jpg")
        
        img = self.baseImage.copy()
        
        # Let user select ROI (drag a box)
        roi = cv.selectROI("Select ROI", img, False)
        
        print(f"Quader:\n self.addQuader(\"CW\", 0, {roi[0]}, {roi[1]}, {roi[0]+roi[2]}, {roi[1]+roi[3]})")
        
        # Extract cropped region
        cropped_img = img[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
        
        # Save and display cropped image
        cv.imshow("Cropped Image", cropped_img)
        cv.waitKey(0)
        cv.destroyAllWindows()
    
    def captureImage(self):
        # self.captureHdr()
        # return
        
        # 
        # 
        #  to enable custom hdr, enable the 2 lines above and switch from SingleExposure to HdrModeEnum.Off in __init_
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
        realColor = cv.imread(path)
        self.baseImage = cv.cvtColor(realColor, cv.COLOR_BGR2RGB)
        
    def getObstacles(self, direction, regionNumber):    
        """@brief Capture frame, extract scan quader, detect RED/GREEN blobs.

        Performs blur, HSV conversion, masking for color ranges (including
        wrap-around red hues)
        @param direction str Direction of the Robot ("CW" or "CCW").
        @param regionNumber int Number of the region/quader for obstacle detection.
        @return Color
        """
        minSize = 200
        
        self.blocksCx = []
        self.blocksCy = []
        self.blocksColor = []
        self.blocksDist = []
        
        timeStart = time.time()
        # print(time.time()-timeStart)
        imgclear = self.baseImage.copy()
        # imgclear = cv.cvtColor(imgclear, cv.COLOR_BGR2RGB)

        quader = self.quaders[direction][str(regionNumber)]
        leftX = quader["leftX"]
        topY = quader["topY"]
        rightX = quader["rightX"]
        bottomY = quader["bottomY"]
        imgIn = cv.blur(imgclear,(10,10))
        imgInCroped = imgIn[topY:bottomY, leftX:rightX]
        hsv = cv.cvtColor(imgInCroped, cv.COLOR_RGB2HSV)
        cv.imwrite(f'capture/{self.pictureNum}-0hsv.jpg', hsv)
        
        img = imgInCroped
        
        assert hsv is not None, "HSV color conversion failed"

        lower_mask = cv.inRange(hsv, self.redlower1, self.redupper1)
        upper_mask = cv.inRange(hsv, self.redlower2, self.redupper2)
        
        maskred = lower_mask + upper_mask
        maskgreen = cv.inRange(hsv, self.lowerGreen, self.upperGreen)
        
        cv.imwrite(f'capture/{self.pictureNum}-1imageRegion.jpg', img)
            
        imgRed = cv.bitwise_and(img, img, mask=maskred)
        imgGreen = cv.bitwise_and(img, img, mask=maskgreen)

        cv.imwrite(f'capture/{self.pictureNum}-2imgRed.jpg', imgRed)
        cv.imwrite(f'capture/{self.pictureNum}-3imgGreen.jpg', imgGreen)

        cntsgreen = cv.findContours(maskgreen.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        cntsred = cv.findContours(maskred.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)

        cntsred = imutils.grab_contours(cntsred)
        cntsgreen = imutils.grab_contours(cntsgreen)

        # cv.line(imgclear,(checkWidthStart,checkEnd),(checkWidth+1,checkEnd),(255,0,0),2)
        # cv.line(imgclear,(checkWidthStart,checkHeightStart),(checkWidth+1,checkHeightStart),(255,0,0),2)
        
        for c in cntsgreen:
            c = c + np.array([leftX, topY])
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

        for c in cntsred:
            c = c + np.array([leftX, topY])
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
                
                if area > minSize:
                    self.blocksCx.append(cX)
                    self.blocksCy.append(cY)
                    self.blocksColor.append(self.parser.RED)
                    _h, _w = imgclear.shape[:2]
                    self.blocksDist.append(((cX - _w // 2) ** 2 + (cY - _h) ** 2) ** 0.5)
            
        if len(self.blocksColor) == 0:
            color = self.defaultColor
        else:
            cX = self.blocksCx[0]
            cY = self.blocksCy[0]
            cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)
            color = self.blocksColor[0]

        cv.imwrite(f'capture/{self.pictureNum}-4detection_result.jpg', imgclear)

        return color


if __name__ == "__main__":
    main()