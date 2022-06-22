//================================== LIBS
#include <Stepper_28BYJ.h>
#include <TFLidar.h>
#include <TcpClient.h>

//================================== CONST

#define MAX_STEPS 4096
//4076

//================================== PINS

#define IN1_X 2
#define IN2_X 4
#define IN3_X 22
#define IN4_X 23

#define IN1_Y 5
#define IN2_Y 18
#define IN3_Y 19
#define IN4_Y 21

#define BZ 12

//================================== WIFI
const char* ssid = "MGTS-455";
const char* password = "4953306832";
//================================== SERVER
const char * host = "192.168.100.5";
const uint16_t port = 8081;
//================================== MESSAGE

Stepper_28BYJ motorX(MAX_STEPS, IN1_X, IN2_X, IN3_X, IN4_X);
Stepper_28BYJ motorY(MAX_STEPS, IN1_Y, IN2_Y, IN3_Y, IN4_Y);

const int start_msg_size = 5;

TFLidar lidar;
int16_t dist;

TcpClient tcp_client(5);
String msg = "";

void beep(uint8_t pin, int delay_time_1, int delay_time_2, int some)
{
  for(int i = 0; i < some; i++)
  {
    digitalWrite(pin, 1);
    delay(delay_time_1);
    digitalWrite(pin, 0);
    delay(delay_time_2);
  }
}

void setup()
{
  //=================== MODE PINS
  pinMode(BZ, OUTPUT);
  //===================
  delay(2000);

  Serial.begin(115200);
  Serial2.begin(115200);

  beep(BZ, 200, 0, 1);//power on
  
  lidar.begin(&Serial2);
  
  motorX.setSpeed(12);
  motorY.setSpeed(12);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  beep(BZ, 100, 50, 2);//connected

  Serial.print("WiFi connected with IP: ");
  Serial.println(WiFi.localIP());
}

void scanning(int x_max, int y_max)
{
  //x_in кратно MAX_STEPS (4096) т.е. 2,8,16,32,64..

  int step_x = MAX_STEPS / x_max;
  int step_y = (MAX_STEPS/2)/y_max;

  for(int y = 0; y < y_max; y++)
  {
    for(int x = 0; x < x_max; x++)
    {
      lidar.getData(dist);//first no clear
      lidar.getData(dist);
      msg = String(dist);
      tcp_client.write_socket(msg);
      tcp_client.read_socket(msg);//ping
      motorX.step(step_x);
    }
    motorX.step(-MAX_STEPS);
    motorY.step((-1)*step_y);
  }
  
  motorY.step((-1)*(-MAX_STEPS/2));
}

String action(String msg)
{
  String command = msg.substring(0,2);// sc01280064 -> get sc
  int cord_x;
  int cord_y;

  Serial.print("command:");
  Serial.println(command);

  if(command.equals("rd")){ return "ok"; }

  if(command.equals("sс"))
  {
    cord_x = msg.substring(2, 6).toInt();// sc01280064 -> get 0128
    cord_y = msg.substring(6).toInt();// sc01280064 -> get 0064

    Serial.print("x:");
    Serial.println(cord_x);
    Serial.print("y:");
    Serial.println(cord_y);
    
    scanning(cord_x, cord_y);
    return "dn";
  }
}

void loop()
{
  if (!tcp_client.connect_to(host, port)) {
      Serial.println("Connection to host failed");
      delay(1000);
      return;
  }
  beep(BZ, 50, 30, 5);//
  while(tcp_client.is_connected())
  {
    tcp_client.read_socket(msg);
    Serial.print("server: ");
    Serial.println(msg);
    msg = action(msg);
    tcp_client.write_socket(msg);
    //delay(1000);
  }
}
