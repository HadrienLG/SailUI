#include "esphome.h"

#include "bmm150.h"
#include "bmm150_defs.h"

class CustomBMM150 : public PollingComponent {
 public:

  BMM150 bmm = BMM150();
  bmm150_mag_data value_offset;

  Sensor *headingXY_sensor = new Sensor();
  Sensor *headingYZ_sensor = new Sensor();
  Sensor *headingZX_sensor = new Sensor();

  // constructor, update interval in ms
  CustomBMM150() : PollingComponent(500) {}
  
  float get_setup_priority() const override { 
    return esphome::setup_priority::HARDWARE; 
  }

  void setup() override {
    // This will be called by App.setup()
    bmm.initialize();

    // Calibration
    uint32_t timeout = 3000;

    int16_t value_x_min = 0;
    int16_t value_x_max = 0;
    int16_t value_y_min = 0;
    int16_t value_y_max = 0;
    int16_t value_z_min = 0;
    int16_t value_z_max = 0;
    uint32_t timeStart = 0;

    bmm.read_mag_data();  
    value_x_min = bmm.raw_mag_data.raw_datax;
    value_x_max = bmm.raw_mag_data.raw_datax;
    value_y_min = bmm.raw_mag_data.raw_datay;
    value_y_max = bmm.raw_mag_data.raw_datay;
    value_z_min = bmm.raw_mag_data.raw_dataz;
    value_z_max = bmm.raw_mag_data.raw_dataz;
    delay(100);

    timeStart = millis();
    
    while((millis() - timeStart) < timeout)
    {
      bmm.read_mag_data();
      
      /* Update x-Axis max/min value */
      if(value_x_min > bmm.raw_mag_data.raw_datax)
      {
        value_x_min = bmm.raw_mag_data.raw_datax;
        // Serial.print("Update value_x_min: ");
        // Serial.println(value_x_min);

      } 
      else if(value_x_max < bmm.raw_mag_data.raw_datax)
      {
        value_x_max = bmm.raw_mag_data.raw_datax;
        // Serial.print("update value_x_max: ");
        // Serial.println(value_x_max);
      }

      /* Update y-Axis max/min value */
      if(value_y_min > bmm.raw_mag_data.raw_datay)
      {
        value_y_min = bmm.raw_mag_data.raw_datay;
        // Serial.print("Update value_y_min: ");
        // Serial.println(value_y_min);

      } 
      else if(value_y_max < bmm.raw_mag_data.raw_datay)
      {
        value_y_max = bmm.raw_mag_data.raw_datay;
        // Serial.print("update value_y_max: ");
        // Serial.println(value_y_max);
      }

      /* Update z-Axis max/min value */
      if(value_z_min > bmm.raw_mag_data.raw_dataz)
      {
        value_z_min = bmm.raw_mag_data.raw_dataz;
        // Serial.print("Update value_z_min: ");
        // Serial.println(value_z_min);

      } 
      else if(value_z_max < bmm.raw_mag_data.raw_dataz)
      {
        value_z_max = bmm.raw_mag_data.raw_dataz;
        // Serial.print("update value_z_max: ");
        // Serial.println(value_z_max);
      }
      
      Serial.print(".");
      delay(100);

    }

    value_offset.x = value_x_min + (value_x_max - value_x_min)/2;
    value_offset.y = value_y_min + (value_y_max - value_y_min)/2;
    value_offset.z = value_z_min + (value_z_max - value_z_min)/2;


  }

  void update() override {
    // This will be called every "update_interval" milliseconds.
    bmm150_mag_data value;
    bmm.read_mag_data();

    value.x = bmm.raw_mag_data.raw_datax - value_offset.x;
    value.y = bmm.raw_mag_data.raw_datay - value_offset.y;
    value.z = bmm.raw_mag_data.raw_dataz - value_offset.z;

    // Headings
    float xyHeading = atan2(value.x, value.y);
    float yzHeading = atan2(value.y, value.z);
    float zxHeading = atan2(value.z, value.x);

    float xyHeadingDegrees = xyHeading * 180 / M_PI;
    float yzHeadingDegrees = yzHeading * 180 / M_PI;
    float zxHeadingDegrees = zxHeading * 180 / M_PI;

    float heading = xyHeading;
    if(heading < 0)
      heading += 2*PI;
    if(heading > 2*PI)
      heading -= 2*PI;
    float headingDegrees = heading * 180/M_PI; 

    headingXY_sensor->publish_state(xyHeadingDegrees);
    headingYZ_sensor->publish_state(yzHeadingDegrees);
    headingZX_sensor->publish_state(zxHeadingDegrees);
  }
};

