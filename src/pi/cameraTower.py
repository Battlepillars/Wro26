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
    """@brief Standalone entry point: capture a single image for testing.

    @return None
    """
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
        self.redlower1 = np.array([0,  100, 60])  #s:150 v:120
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
        
        self.addQuader("CW", 0, 496, 356, 612, 458)
        self.addQuader("CW", 1, 744, 374, 988, 614)
        self.addQuader("CW", 2, 316, 520, 706, 827)
        self.addQuader("CW", 3, 808, 370, 1066, 469)
        self.addQuader("CW", 4, 674, 323, 864, 381)
        self.addQuader("CW", 5, 598, 256, 763, 332)
        self.addQuader("CW", 6, 823, 249, 920, 301)
        self.addQuader("CW", 7, 586, 250, 756, 293)
        self.addQuader("CW", 8, 405, 252, 559, 292)
        self.addQuader("CW", 9, 929, 253, 1098, 314)
        self.addQuader("CW", 10, 789, 260, 913, 330)
        self.addQuader("CW", 11, 590, 275, 705, 334)
        
        self.addQuader("CCW", 0, 515, 340, 672, 503)
        self.addQuader("CCW", 1, 159, 410, 559, 771)
        self.addQuader("CCW", 2, 276, 448, 730, 816)
        self.addQuader("CCW", 3, 647, 365, 862, 430)
        self.addQuader("CCW", 4, 486, 328, 649, 373)
        self.addQuader("CCW", 5, 334, 265, 540, 337)
        self.addQuader("CCW", 6, 899, 248, 1076, 284)
        self.addQuader("CCW", 7, 689, 245, 858, 281)
        self.addQuader("CCW", 8, 522, 246, 653, 282)
        self.addQuader("CCW", 9, 990, 241, 1144, 299)
        self.addQuader("CCW", 10, 830, 252, 982, 298)
        self.addQuader("CCW", 11, 625, 268, 777, 333)


    def addQuader(self, direction, number, leftX, topY, rightX, bottomY):
        """@brief Register a rectangular region (quader) used to crop one obstacle.

        Each direction/number pair stores the pixel box that a single obstacle
        is expected to appear in for a given tower scan angle.
        @param direction str scan direction key ("CW" or "CCW").
        @param number    int obstacle/region index.
        @param leftX     int left pixel coordinate.
        @param topY      int top pixel coordinate.
        @param rightX    int right pixel coordinate.
        @param bottomY   int bottom pixel coordinate.
        @return None
        """
        if direction not in self.quaders:
            return
        self.quaders[direction][str(number)] = {
            "leftX": leftX,
            "topY": topY,
            "rightX": rightX,
            "bottomY": bottomY,
        }

    def createQuadar(self, capture):
        """@brief Interactively pick a region box and print its addQuader() call.

        Calibration helper: lets the user drag a rectangle over an image and
        prints the coordinates to paste back as an `addQuader` definition.
        @param capture bool True to grab a fresh image, False to load a stored one.
        @return None
        """
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
        """@brief Grab a still frame from the camera and save it to disk.

        Stores the RGB frame in `self.baseImage` and writes a numbered JPEG
        into the capture folder for later review.
        @return None
        """
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
        """@brief Load an image from disk into `self.baseImage` for analysis.

        @param path str file path of the image to load.
        @return None
        """
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
        minSize = 20
        
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
        imgIn = cv.blur(imgclear,(10,10))              # soften noise and color edges
        imgInCroped = imgIn[topY:bottomY, leftX:rightX]  # crop to this obstacle's region
        hsv = cv.cvtColor(imgInCroped, cv.COLOR_RGB2HSV)  # HSV is robust to brightness changes
        cv.imwrite(f'capture/{self.pictureNum}-0hsv.jpg', hsv)
        
        img = imgInCroped
        
        assert hsv is not None, "HSV color conversion failed"

        # Red wraps around the hue circle, so combine a low- and high-hue mask.
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
        
        # quader["leftX"]
        if len(self.blocksColor) == 0:
            color = self.defaultColor        # nothing found -> fall back to default
        else:
            cX = self.blocksCx[0]
            cY = self.blocksCy[0]
            cv.line(imgclear,(cX,0),(cX,1150),(0,0,255),3)
            color = self.blocksColor[0]      # first blob in the region wins
            
        cv.line(imgclear,(quader["leftX"],quader["topY"]),(quader["rightX"],quader["topY"]),(0,255,0),3)
        cv.line(imgclear,(quader["leftX"],quader["bottomY"]),(quader["rightX"],quader["bottomY"]),(0,255,0),3)
        cv.line(imgclear,(quader["leftX"],quader["topY"]),(quader["leftX"],quader["bottomY"]),(0,255,0),3)
        cv.line(imgclear,(quader["rightX"],quader["topY"]),(quader["rightX"],quader["bottomY"]),(0,255,0),3)

        cv.imwrite(f'capture/{self.pictureNum}-4detection_result.jpg', imgclear)
        self.pictureNum += 1

        return color


if __name__ == "__main__":
    main()