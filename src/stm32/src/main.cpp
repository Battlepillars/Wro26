#include <Arduino.h>
#include "Servo.h"  
#include <PID_v1.h>
#include <SPI.h>

#include <vl53l8cx.h>

// Encoder pins
#define interruptPinA PA0
#define interruptPinB PA1



Servo servo;
volatile long EncoderCount = 0;
int32_t EncoderCountFull = 0;

// Timer object for encoder
HardwareTimer *encoder;

// Timer object for PWM
HardwareTimer *pwm;

// Timer object for 100 Hz interrupt
HardwareTimer *tick100HzTimer;

int32_t impulse_diff = 0;

int32_t lastEncoderCount = 0;
int32_t rotations_per_sec = 0;

bool newdata = false, checkVoltage = false;

String strinList[100] = {};
int amountDividers = 0;


// PWM-capable pin for BlackPill F411.
// Avoid pins used by UART (often Serial1 = PA9/PA10 or PB6/PB7 depending on variant).
// Good alternatives include PA6/PA7 (TIM3), PB0/PB1 (TIM3), PB8/PB9 (TIM4).
#define PWM_PIN1 PA6
#define PWM_PIN2 PA7

#define SPI_CLK_PIN PB13
#define SPI_MISO_PIN PB14
#define SPI_MOSI_PIN PB15
#define CS_PIN1 PB10
#define CS_PIN2 PB1
#define CS_PIN3 PB7
#define CS_PIN4 PB6
#define LED1 PA2
#define LED2 PA3
uint8_t status;
#define BUSSPEED 5000000

SPIClass DEV_SPI(SPI_MOSI_PIN, SPI_MISO_PIN, SPI_CLK_PIN);

VL53L8CX sensor_vl53l8cx_top1(&DEV_SPI, CS_PIN1, -1,  -1,  BUSSPEED);
VL53L8CX sensor_vl53l8cx_top2(&DEV_SPI, CS_PIN2, -1,  -1,  BUSSPEED);
VL53L8CX sensor_vl53l8cx_top3(&DEV_SPI, CS_PIN3, -1,  -1,  BUSSPEED);
VL53L8CX sensor_vl53l8cx_top4(&DEV_SPI, CS_PIN4, -1,  -1,  BUSSPEED);
int sensorCaptures[8] = {0,0,0,0,0,0,0,0};


double Setpoint=0, Input, Output;
PID myPID(&Input, &Output, &Setpoint,0.5,20,0/*0.0005*/, DIRECT);

void setSpeed(double speed);
void motorController100Hz();
void waitForNewMessage();
void parse();

#define RESOLUTION VL53L8CX_RESOLUTION_4X4

void initVL53(VL53L8CX * sensor, int speed)
{ 
  
  Serial1.println("Sensor Begin");
  // Configure VL53L8CX component.
  status = sensor->begin();
  Serial1.println("Sensor Init");
  status = sensor->init();
  Serial1.println("Sensor resolution");
  status = sensor->set_resolution(RESOLUTION);
  Serial1.println("Sensor Frquency");
  sensor->set_ranging_frequency_hz(speed);
  Serial1.println("Sensor ranging mode");
  sensor->set_ranging_mode(VL53L8CX_RANGING_MODE_CONTINUOUS);
  Serial1.println("Sensor start ranging");
  status = sensor->start_ranging();
  Serial1.println("Sensor init Done");
}

int update(VL53L8CX * sensor, VL53L8CX_ResultsData * result) 
{
  // Serial1.println("\nSensor updating");

  uint8_t NewDataReady = 0;
  // Serial1.println("looking for data");

  status = sensor->check_data_ready(&NewDataReady);
  if (status)
  {
    // Serial1.printf("-");
    return 0;
  }
  if (!NewDataReady)
  {
    // Serial1.printf(".");
    return 0;
  }

  // Serial1.printf("x");

  status = sensor->get_ranging_data(result);
  return 1;

}

/* Setup ---------------------------------------------------------------------*/
void setup()
{

  // Initialize serial for output.
  Serial1.begin(921600);

  Serial1.println("Startup");
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PA15, OUTPUT);
  pinMode(PA4, INPUT_ANALOG);
  // pinMode(LED1, OUTPUT);
  // pinMode(LED2, OUTPUT);
  // digitalWrite(LED1, HIGH);
  // digitalWrite(LED2, HIGH);

  // *** Hardware Encoder Setup (TIM2) ***
  encoder = new HardwareTimer(TIM2);
  
  // Encoder mode: count on rising edges only
  encoder->setMode(1, TIMER_INPUT_CAPTURE_RISING, interruptPinA);
  encoder->setMode(2, TIMER_INPUT_CAPTURE_RISING, interruptPinB);
  
  // Configure encoder mode via HAL
  TIM_Encoder_InitTypeDef encoderConfig;
  encoderConfig.EncoderMode = TIM_ENCODERMODE_TI12;
  encoderConfig.IC1Polarity = TIM_INPUTCHANNELPOLARITY_RISING;
  encoderConfig.IC1Selection = TIM_ICSELECTION_DIRECTTI;
  encoderConfig.IC1Prescaler = TIM_ICPSC_DIV1;
  encoderConfig.IC1Filter = 0;
  encoderConfig.IC2Polarity = TIM_INPUTCHANNELPOLARITY_RISING;
  encoderConfig.IC2Selection = TIM_ICSELECTION_DIRECTTI;
  encoderConfig.IC2Prescaler = TIM_ICPSC_DIV1;
  encoderConfig.IC2Filter = 0;
  
  HAL_TIM_Encoder_Init(encoder->getHandle(), &encoderConfig);
  
  // Set counter to max value for bidirectional counting
  encoder->setOverflow(0xFFFF);
  encoder->setCount(0); 
  
  HAL_TIM_Encoder_Start(encoder->getHandle(), TIM_CHANNEL_ALL);
  
  Serial1.println("Hardware encoder initialized");

  // 100 Hz interrupt (TIM5)
  tick100HzTimer = new HardwareTimer(TIM5);
  tick100HzTimer->setOverflow(100, HERTZ_FORMAT);
  tick100HzTimer->attachInterrupt(motorController100Hz);
  tick100HzTimer->resume();

  // Initialize PWM output: 70kHz with 20% duty cycle
  pinMode(PWM_PIN1, OUTPUT);
  pinMode(PWM_PIN2, OUTPUT);
  analogWriteResolution(10);                 // 0..255
  analogWriteFrequency(70000);              // 70 kHz (core-wide setting)

  setSpeed(0);

  Serial1.println("done");

  Input = 100;
  myPID.SetOutputLimits(-100, 100);
  myPID.SetSampleTime(1);
  myPID.SetMode(AUTOMATIC);

  // Initialize SPI bus.
  Serial1.println("Sensor init start");
  DEV_SPI.begin();

  Serial1.println("*** CS1 ***");
  initVL53(&sensor_vl53l8cx_top1,60);
  Serial1.println("*** CS2 ***");
  initVL53(&sensor_vl53l8cx_top2,60);
  Serial1.println("*** CS3 ***");
  initVL53(&sensor_vl53l8cx_top3,60);
  Serial1.println("*** CS4 ***");
  initVL53(&sensor_vl53l8cx_top4,60);
  Serial1.println("Sensor init end");
  servo.attach(PA5);
}


void setSpeed(double speed)
{
  if (speed > 0) 
  {
    speed = constrain(speed, 0, 100);
    analogWrite(PWM_PIN2, 0);
    analogWrite(PWM_PIN1, (1023*(speed/100.0)));
  } else if (speed < 0) 
  {
    speed = constrain(speed, -100, 0);
    analogWrite(PWM_PIN1, 0);
    analogWrite(PWM_PIN2, (1023*(abs(speed)/100.0)));
  } else 
  {
    analogWrite(PWM_PIN1, 0);
    analogWrite(PWM_PIN2, 0);
  }

  // analogWrite(PWM_PIN1, 200);
  // analogWrite(PWM_PIN2, 800);
}
void printSensorData(int cam,VL53L8CX_ResultsData * result) 
{
  int res=8;
  if (RESOLUTION == VL53L8CX_RESOLUTION_4X4)
    res=4;
  Serial1.printf("cam,%i",cam);
  for (int i = 0; i < res*res; i++) 
  {
    if (result->target_status[i]!=5 && result->target_status[i]!=9)
      Serial1.printf(",-1");
    else
      Serial1.printf(",%i", result->distance_mm[i]);
  }
  Serial1.println(",");
}

void printMultiSensorData(int cam,VL53L8CX_ResultsData * result,int offset) 
{
  int res=8;
  if (RESOLUTION == VL53L8CX_RESOLUTION_4X4)
    res=4;
  Serial1.printf("cam,%i",offset+1);
  for (int i = 0; i < res*res*4; i+=4) 
  {
    if (result->target_status[i+offset]!=5 && result->target_status[i+offset]!=9)
      Serial1.printf(",-1");
    else
      Serial1.printf(",%i", result->distance_mm[i+offset]);
  }
  Serial1.println(",");
}

void waitForNewMessage()
{
  char str[2] = "";
  int r = Serial1.read();
  while (r>=0) 
  {
    if (r==',')
    {
      if (amountDividers<99)
        amountDividers++;
    }
    else if (r=='\n')
    {
      parse();
    }
    else
    {
      str[0]=(char)r;
      strinList[amountDividers] += String(str);
    }
    r = Serial1.read();
   
  }
// Serial1.printf(" %i:<%c> ",r,r);
}

void parse()
{
  if (strinList[0] == "speed" && amountDividers==1) 
  {
    Setpoint = strinList[1].toDouble();
  } 
  else if (strinList[0] == "servo" && amountDividers==1) 
  {
    servo.write(strinList[1].toDouble());
  }
  else if (strinList[0] == "checkVoltage" && amountDividers==1) 
  {
    checkVoltage = strinList[1].toInt()>0;
  }

  for (int i=0;i<=amountDividers;i++)
  {
    // Serial1.printf(" %i:<",i);
    // Serial1.print(strinList[i]);
    // Serial1.print("> ");
    strinList[i]="";
  }
  amountDividers=0;
  // Serial1.println("");
}


void loop()
{
  waitForNewMessage();
  uint32_t ad = analogRead(PA4);
  double vBat=(double)ad * 3.3*5.7 / 1023.0;

  //Serial1.printf("Ad: %i V:<%i> \n",ad,(int)(vBat*10.));
  static unsigned long lastTime = 0;
  static bool ledState = false;

  
  static VL53L8CX_ResultsData results1;
  static VL53L8CX_ResultsData results2;
  static VL53L8CX_ResultsData results3;
  static VL53L8CX_ResultsData results4;

  int s1=0;
  int s2=0;
  int s3=0;
  int s4=0;

  static int d=0;
  d++;
  s1=update(&sensor_vl53l8cx_top1, &results1);
  // if (d%3==0)
    s2=update(&sensor_vl53l8cx_top2, &results2);
  // if ((d+1)%3==0)
    s3=update(&sensor_vl53l8cx_top3, &results3);
  // if ((d+2)%3==0)
    s4=update(&sensor_vl53l8cx_top4, &results4);
  // if (s1>0)
  //   printSensorData(1,&results1);
  // if (s2>0)
  //   printSensorData(2,&results2);
  // if (s3>0)
  //   printSensorData(3,&results3);
  // if (s4>0)
  //   printSensorData(4,&results4);

  if (s3>0)
  {
    printMultiSensorData(3,&results3,0);    
    printMultiSensorData(3,&results3,1);    
    printMultiSensorData(3,&results3,2);    
    printMultiSensorData(3,&results3,3);    
  }
        
  sensorCaptures[0]+=s1;
  sensorCaptures[1]+=s2;
  sensorCaptures[2]+=s3;
  sensorCaptures[3]+=s4;

  static int c=0;
  static unsigned long lastPrint=micros();

  if (vBat<10.8 && checkVoltage)
  {
    while (true)
    {
      if (micros()-lastPrint>500000) {
        lastPrint=micros();
        Setpoint = 0;
        Serial1.print("lowVoltage,");
        Serial1.print(vBat);  //Voltage
        Serial1.print(",\n");
        static int pos=0;
        servo.write(90);
        if (pos==0)
          servo.write(0);
        if (pos==1)
          servo.write(90);
        if (pos==2)
          servo.write(180);
        if (pos==3)
          servo.write(90);      
        pos++;
        if (pos>3)
          pos=3;
      }
    }
  }


  if (micros()-lastPrint>500000)
  {
    // static int pos=0;
    // servo.write(90);
    // if (pos==0)
    //   servo.write(0);
    // if (pos==1)
    //   servo.write(90);
    // if (pos==2)
    //   servo.write(180);
    // if (pos==3)
    //   servo.write(90);      
    // pos++;
    // if (pos>3)
    //   pos=0;
  
    lastPrint = micros();
    // Serial1.printf("%i    %i  %i     ",impulse_diff,rotations_per_sec,(int)(Output*10)); 
    Serial1.print("stat,");
    Serial1.print(vBat);    //Voltage
    for (int i=0;i<4;i++) 
    {
      Serial1.print(",");
      Serial1.print(sensorCaptures[i]*2);
      sensorCaptures[i]=0;
    }
    // uint8_t status;
    // sensor_vl53l8cx_top1.get_ranging_frequency_hz(&status);
    // Serial1.printf("Freq: %i ",status);

    Serial1.print(",\n");
  }

  if (newdata) 
  {
    // static double dir=1;
    // if (Setpoint>=200)
    //   dir=-1;
    // if (Setpoint<=40)
    //   dir=1;

    // Setpoint+=dir*2;    

    Serial1.print("speed,");
    Serial1.print(rotations_per_sec);   //Speed
    Serial1.print(",");
    Serial1.print(EncoderCountFull);    //Counter
    Serial1.print(",");
    Serial1.print(Output);    //Counter
    Serial1.print(",");    
    Serial1.print(Setpoint);    //Counter
    Serial1.print(",\n");
    newdata = false;
  }
}

// Cams 1/2/3/4:
// Cam,1/2/3/4,value1,value2,...,value16/64;

// Speed,Counter,Voltage:
// speed,value,value,value;


void motorController100Hz()
{
  digitalWrite(PA15,1); 
  // Read encoder count from hardware timer
  EncoderCount = (long)encoder->getCount();
  
  
  // Calculate impulses per second
  impulse_diff = EncoderCount - lastEncoderCount;
  if (impulse_diff > 30000)
    impulse_diff-=0xffff;
  if (impulse_diff <- 30000)
    impulse_diff+=0xffff;

  int32_t impulses_per_sec = impulse_diff * 100;

  EncoderCountFull += impulse_diff;
  

  //  30 counts per rotation
  rotations_per_sec = impulses_per_sec / 30.0;
  int32_t rpm = impulses_per_sec * 60.0 /30;

  Input = (double)rotations_per_sec;
  myPID.Compute();

  setSpeed(Output);
  lastEncoderCount = EncoderCount;  
  digitalWrite(PA15,0); 

  newdata = true;
}

