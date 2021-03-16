#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import smbus
import math



pu8data = [0,0,0,0,0,0,0,0]
U8tempX = [0,0,0,0,0,0,0,0,0]
U8tempY = [0,0,0,0,0,0,0,0,0]
U8tempZ = [0,0,0,0,0,0,0,0,0]
GyroOffset = [0,0,0]
Ki = 1.0
Kp = 4.50
q0 = 1.0
q1 = q2 = q3 = 0.0
angles = [0.0, 0.0, 0.0]
true = 0x01
false = 0x00

# define ICM-20948 Device I2C address
I2C_ADD_ICM20948                     = 0x68
I2C_ADD_ICM20948_AK09916             = 0x0C
I2C_ADD_ICM20948_AK09916_READ        = 0x80
I2C_ADD_ICM20948_AK09916_WRITE       = 0x00

# define ICM-20948 Register
# user bank 0 register
REG_ADD_WIA                          = 0x00
REG_VAL_WIA                          = 0xEA
REG_ADD_USER_CTRL                    = 0x03
REG_VAL_BIT_DMP_EN                   = 0x80
REG_VAL_BIT_FIFO_EN                  = 0x40
REG_VAL_BIT_I2C_MST_EN               = 0x20
REG_VAL_BIT_I2C_IF_DIS               = 0x10
REG_VAL_BIT_DMP_RST                  = 0x08
REG_VAL_BIT_DIAMOND_DMP_RST          = 0x04
REG_ADD_PWR_MIGMT_1                  = 0x06
REG_VAL_ALL_RGE_RESET                = 0x80
REG_VAL_RUN_MODE                     = 0x01 # Non low-power mode
REG_ADD_LP_CONFIG                    = 0x05
REG_ADD_PWR_MGMT_1                   = 0x06
REG_ADD_PWR_MGMT_2                   = 0x07
REG_ADD_ACCEL_XOUT_H                 = 0x2D
REG_ADD_ACCEL_XOUT_L                 = 0x2E
REG_ADD_ACCEL_YOUT_H                 = 0x2F
REG_ADD_ACCEL_YOUT_L                 = 0x30
REG_ADD_ACCEL_ZOUT_H                 = 0x31
REG_ADD_ACCEL_ZOUT_L                 = 0x32
REG_ADD_GYRO_XOUT_H                  = 0x33
REG_ADD_GYRO_XOUT_L                  = 0x34
REG_ADD_GYRO_YOUT_H                  = 0x35
REG_ADD_GYRO_YOUT_L                  = 0x36
REG_ADD_GYRO_ZOUT_H                  = 0x37
REG_ADD_GYRO_ZOUT_L                  = 0x38
REG_ADD_EXT_SENS_DATA_00             = 0x3B
REG_ADD_REG_BANK_SEL                 = 0x7F
REG_VAL_REG_BANK_0                   = 0x00
REG_VAL_REG_BANK_1                   = 0x10
REG_VAL_REG_BANK_2                   = 0x20
REG_VAL_REG_BANK_3                   = 0x30

# user bank 1 register
# user bank 2 register
REG_ADD_GYRO_SMPLRT_DIV              = 0x00
REG_ADD_GYRO_CONFIG_1                = 0x01
REG_VAL_BIT_GYRO_DLPCFG_2            = 0x10  # bit[5:3]
REG_VAL_BIT_GYRO_DLPCFG_4            = 0x20  # bit[5:3]
REG_VAL_BIT_GYRO_DLPCFG_6            = 0x30  # bit[5:3]
REG_VAL_BIT_GYRO_FS_250DPS           = 0x00  # bit[2:1]
REG_VAL_BIT_GYRO_FS_500DPS           = 0x02  # bit[2:1]
REG_VAL_BIT_GYRO_FS_1000DPS          = 0x04  # bit[2:1]
REG_VAL_BIT_GYRO_FS_2000DPS          = 0x06  # bit[2:1]
REG_VAL_BIT_GYRO_DLPF                = 0x01  # bit[0]
REG_ADD_ACCEL_SMPLRT_DIV_2           = 0x11
REG_ADD_ACCEL_CONFIG                 = 0x14
REG_VAL_BIT_ACCEL_DLPCFG_2           = 0x10  # bit[5:3]
REG_VAL_BIT_ACCEL_DLPCFG_4           = 0x20  # bit[5:3]
REG_VAL_BIT_ACCEL_DLPCFG_6           = 0x30  # bit[5:3]
REG_VAL_BIT_ACCEL_FS_2g              = 0x00  # bit[2:1]
REG_VAL_BIT_ACCEL_FS_4g              = 0x02  # bit[2:1]
REG_VAL_BIT_ACCEL_FS_8g              = 0x04  # bit[2:1]
REG_VAL_BIT_ACCEL_FS_16g             = 0x06  # bit[2:1]
REG_VAL_BIT_ACCEL_DLPF               = 0x01  # bit[0]

# user bank 3 register
REG_ADD_I2C_SLV0_ADDR                = 0x03
REG_ADD_I2C_SLV0_REG                 = 0x04
REG_ADD_I2C_SLV0_CTRL                = 0x05
REG_VAL_BIT_SLV0_EN                  = 0x80
REG_VAL_BIT_MASK_LEN                 = 0x07
REG_ADD_I2C_SLV0_DO                  = 0x06
REG_ADD_I2C_SLV1_ADDR                = 0x07
REG_ADD_I2C_SLV1_REG                 = 0x08
REG_ADD_I2C_SLV1_CTRL                = 0x09
REG_ADD_I2C_SLV1_DO                  = 0x0A

# define ICM-20948 Register  end

# define ICM-20948 MAG Register
REG_ADD_MAG_WIA1                     = 0x00
REG_VAL_MAG_WIA1                     = 0x48
REG_ADD_MAG_WIA2                     = 0x01
REG_VAL_MAG_WIA2                     = 0x09
REG_ADD_MAG_ST2                      = 0x10
REG_ADD_MAG_DATA                     = 0x11
REG_ADD_MAG_CNTL2                    = 0x31
REG_VAL_MAG_MODE_PD                  = 0x00
REG_VAL_MAG_MODE_SM                  = 0x01
REG_VAL_MAG_MODE_10HZ                = 0x02
REG_VAL_MAG_MODE_20HZ                = 0x04
REG_VAL_MAG_MODE_50HZ                = 0x05
REG_VAL_MAG_MODE_100HZ               = 0x08
REG_VAL_MAG_MODE_ST                  = 0x10
# define ICM-20948 MAG Register  end

MAG_DATA_LEN = 6

class ICM20948(object):
    Roll = 0.0
    Pitch = 0.0
    Yaw = 0.0
    Acceleration = [0, 0, 0]
    Gyroscope = [0, 0, 0]
    Magnetic = [0, 0, 0]
    
    def __init__(self, address=I2C_ADD_ICM20948):
        self._address = address
        self._bus = smbus.SMBus(1)
        bRet = self.icm20948Check() # Initialization of the device multiple times after power on will result in a return error
        time.sleep(0.5) # We can skip this detection by delaying it by 500 milliseconds
        
        # user bank 0 register 
        self._write_byte( REG_ADD_REG_BANK_SEL , REG_VAL_REG_BANK_0)
        self._write_byte( REG_ADD_PWR_MIGMT_1 , REG_VAL_ALL_RGE_RESET)
        time.sleep(0.1)
        
        self._write_byte( REG_ADD_PWR_MIGMT_1 , REG_VAL_RUN_MODE)  
        #user bank 2 register
        self._write_byte( REG_ADD_REG_BANK_SEL , REG_VAL_REG_BANK_2)
        self._write_byte( REG_ADD_GYRO_SMPLRT_DIV , 0x07)
        self._write_byte( REG_ADD_GYRO_CONFIG_1 , REG_VAL_BIT_GYRO_DLPCFG_6 | REG_VAL_BIT_GYRO_FS_1000DPS | REG_VAL_BIT_GYRO_DLPF)
        self._write_byte( REG_ADD_ACCEL_SMPLRT_DIV_2 ,  0x07)
        self._write_byte( REG_ADD_ACCEL_CONFIG , REG_VAL_BIT_ACCEL_DLPCFG_6 | REG_VAL_BIT_ACCEL_FS_2g | REG_VAL_BIT_ACCEL_DLPF)
        #user bank 0 register
        self._write_byte( REG_ADD_REG_BANK_SEL , REG_VAL_REG_BANK_0) 
        time.sleep(0.1)
        
        self.icm20948GyroOffset()
        self.icm20948MagCheck()
        self.icm20948WriteSecondary( I2C_ADD_ICM20948_AK09916|I2C_ADD_ICM20948_AK09916_WRITE,REG_ADD_MAG_CNTL2, REG_VAL_MAG_MODE_20HZ)
        
    def _read_byte(self,cmd):
        return self._bus.read_byte_data(self._address,cmd)

    def _read_block(self, reg, length=1):
        return self._bus.read_i2c_block_data(self._address, reg, length)

    def _read_u16(self,cmd):
        LSB = self._bus.read_byte_data(self._address,cmd)
        MSB = self._bus.read_byte_data(self._address,cmd+1)
        return (MSB << 8) + LSB

    def _write_byte(self,cmd,val):
        self._bus.write_byte_data(self._address,cmd,val)
        time.sleep(0.0001)
    
    def icm20948Check(self):
        bRet = false
        if REG_VAL_WIA == self._read_byte(REG_ADD_WIA):
          bRet = true
        return bRet
    
    def icm20948GyroOffset(self):
        s32TempGx = 0
        s32TempGy = 0
        s32TempGz = 0
        for i in range(0,32):
            self.icm20948_Gyro_Accel_Read()
            s32TempGx += self.Gyroscope[0]
            s32TempGy += self.Gyroscope[1]
            s32TempGz += self.Gyroscope[2]
            time.sleep(0.01)
        GyroOffset[0] = s32TempGx >> 5
        GyroOffset[1] = s32TempGy >> 5
        GyroOffset[2] = s32TempGz >> 5
    
    
    def icm20948_Gyro_Accel_Read(self):
        self._write_byte( REG_ADD_REG_BANK_SEL , REG_VAL_REG_BANK_0)
        data =self._read_block(REG_ADD_ACCEL_XOUT_H, 12)
        self._write_byte( REG_ADD_REG_BANK_SEL , REG_VAL_REG_BANK_2)
        self.Acceleration[0] = (data[0]<<8)|data[1]
        self.Acceleration[1] = (data[2]<<8)|data[3]
        self.Acceleration[2] = (data[4]<<8)|data[5]
        self.Gyroscope[0]  = ((data[6]<<8)|data[7]) - GyroOffset[0]
        self.Gyroscope[1]  = ((data[8]<<8)|data[9]) - GyroOffset[1]
        self.Gyroscope[2]  = ((data[10]<<8)|data[11]) - GyroOffset[2]
        
        for k in range(0,3):
            # Solve the problem that Python shift will not overflow
            if self.Acceleration[k] >= 32767:             
                self.Acceleration[k] = self.Acceleration[k] - 65535
            elif self.Acceleration[k] <= -32767:
                self.Acceleration[k] = self.Acceleration[k] + 65535
            
            if self.Gyroscope[k] >= 32767:
                self.Gyroscope[k] = self.Gyroscope[k] - 65535
            elif self.Gyroscope[k] <= -32767:
                self.Gyroscope[k] = self.Gyroscope[k] + 65535
  
    def icm20948MagRead(self):
        counter=20
        while counter > 0:
            time.sleep(0.01)
            self.icm20948ReadSecondary( I2C_ADD_ICM20948_AK09916|I2C_ADD_ICM20948_AK09916_READ , REG_ADD_MAG_ST2, 1)
            if (pu8data[0] & 0x01)!= 0:
                break
            counter-=1
        if counter!=0:
            for i in range(0,8):
                self.icm20948ReadSecondary( I2C_ADD_ICM20948_AK09916|I2C_ADD_ICM20948_AK09916_READ , REG_ADD_MAG_DATA , MAG_DATA_LEN)
                U8tempX[i] = (pu8data[1]<<8)|pu8data[0]
                U8tempY[i] = (pu8data[3]<<8)|pu8data[2]
                U8tempZ[i] = (pu8data[5]<<8)|pu8data[4]
            self.Magnetic[0] = sum(U8tempX[0:8])/8
            self.Magnetic[1] = -sum(U8tempY[0:8])/8
            self.Magnetic[2] = -sum(U8tempZ[0:8])/8
            
            for k in range(0,3):
                #Solve the problem that Python shift will not overflow
                if self.Magnetic[k]>=32767:
                    self.Magnetic[k] = self.Magnetic[k] - 65535
                elif self.Magnetic[k]<=-32767:
                    self.Magnetic[k] = self.Magnetic[k] + 65535
    
    def icm20948ReadSecondary(self,u8I2CAddr,u8RegAddr,u8Len):
        u8Temp = 0
        self._write_byte( REG_ADD_REG_BANK_SEL,  REG_VAL_REG_BANK_3) #swtich bank3
        self._write_byte( REG_ADD_I2C_SLV0_ADDR, u8I2CAddr)
        self._write_byte( REG_ADD_I2C_SLV0_REG,  u8RegAddr)
        self._write_byte( REG_ADD_I2C_SLV0_CTRL, REG_VAL_BIT_SLV0_EN|u8Len)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_0) #swtich bank0
        
        u8Temp = self._read_byte(REG_ADD_USER_CTRL)
        u8Temp |= REG_VAL_BIT_I2C_MST_EN
        self._write_byte( REG_ADD_USER_CTRL, u8Temp)
        time.sleep(0.01)
        
        u8Temp &= ~REG_VAL_BIT_I2C_MST_EN
        self._write_byte( REG_ADD_USER_CTRL, u8Temp)
        for i in range(0,u8Len):
            pu8data[i]= self._read_byte( REG_ADD_EXT_SENS_DATA_00+i)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_3) #swtich bank3
        u8Temp = self._read_byte(REG_ADD_I2C_SLV0_CTRL)
        u8Temp &= ~((REG_VAL_BIT_I2C_MST_EN)&(REG_VAL_BIT_MASK_LEN))
        self._write_byte( REG_ADD_I2C_SLV0_CTRL,  u8Temp)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_0) #swtich bank0
    
    def icm20948WriteSecondary(self,u8I2CAddr,u8RegAddr,u8data):
        u8Temp = 0
        self._write_byte( REG_ADD_REG_BANK_SEL,  REG_VAL_REG_BANK_3) #swtich bank3
        self._write_byte( REG_ADD_I2C_SLV1_ADDR, u8I2CAddr)
        self._write_byte( REG_ADD_I2C_SLV1_REG,  u8RegAddr)
        self._write_byte( REG_ADD_I2C_SLV1_DO,   u8data)
        self._write_byte( REG_ADD_I2C_SLV1_CTRL, REG_VAL_BIT_SLV0_EN|1)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_0) #swtich bank0
        u8Temp = self._read_byte(REG_ADD_USER_CTRL)
        u8Temp |= REG_VAL_BIT_I2C_MST_EN
        self._write_byte( REG_ADD_USER_CTRL, u8Temp)
        time.sleep(0.01)
        u8Temp &= ~REG_VAL_BIT_I2C_MST_EN
        self._write_byte( REG_ADD_USER_CTRL, u8Temp)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_3) #swtich bank3
        u8Temp = self._read_byte(REG_ADD_I2C_SLV0_CTRL)
        u8Temp &= ~((REG_VAL_BIT_I2C_MST_EN)&(REG_VAL_BIT_MASK_LEN))
        self._write_byte( REG_ADD_I2C_SLV0_CTRL,  u8Temp)
        self._write_byte( REG_ADD_REG_BANK_SEL, REG_VAL_REG_BANK_0) #swtich bank0

    def imuAHRSupdate(self, gx, gy, gz, ax, ay, az, mx, my, mz):    
        norm = 0.0
        hx = hy = hz = bx = bz = 0.0
        vx = vy = vz = wx = wy = wz = 0.0
        exInt = eyInt = ezInt = 0.0
        ex = ey = ez = 0.0 
        halfT = 0.024
        
        global q0
        global q1
        global q2
        global q3
        q0q0 = q0 * q0
        q0q1 = q0 * q1
        q0q2 = q0 * q2
        q0q3 = q0 * q3
        q1q1 = q1 * q1
        q1q2 = q1 * q2
        q1q3 = q1 * q3
        q2q2 = q2 * q2   
        q2q3 = q2 * q3
        q3q3 = q3 * q3          

        denom = math.sqrt(ax * ax + ay * ay + az * az)
        if denom != 0:
            norm = float(1/denom)     
            ax = ax * norm
            ay = ay * norm
            az = az * norm

        denom = math.sqrt(mx * mx + my * my + mz * mz)
        if denom != 0:
            norm = float(1/denom)      
            mx = mx * norm
            my = my * norm
            mz = mz * norm

        # compute reference direction of flux
        hx = 2 * mx * (0.5 - q2q2 - q3q3) + 2 * my * (q1q2 - q0q3) + 2 * mz * (q1q3 + q0q2)
        hy = 2 * mx * (q1q2 + q0q3) + 2 * my * (0.5 - q1q1 - q3q3) + 2 * mz * (q2q3 - q0q1)
        hz = 2 * mx * (q1q3 - q0q2) + 2 * my * (q2q3 + q0q1) + 2 * mz * (0.5 - q1q1 - q2q2)         
        bx = math.sqrt((hx * hx) + (hy * hy))
        bz = hz     

        # estimated direction of gravity and flux (v and w)
        vx = 2 * (q1q3 - q0q2)
        vy = 2 * (q0q1 + q2q3)
        vz = q0q0 - q1q1 - q2q2 + q3q3
        wx = 2 * bx * (0.5 - q2q2 - q3q3) + 2 * bz * (q1q3 - q0q2)
        wy = 2 * bx * (q1q2 - q0q3) + 2 * bz * (q0q1 + q2q3)
        wz = 2 * bx * (q0q2 + q1q3) + 2 * bz * (0.5 - q1q1 - q2q2)  

        # error is sum of cross product between reference direction of fields and direction measured by sensors
        ex = (ay * vz - az * vy) + (my * wz - mz * wy)
        ey = (az * vx - ax * vz) + (mz * wx - mx * wz)
        ez = (ax * vy - ay * vx) + (mx * wy - my * wx)

        if ex != 0.0 and ey != 0.0 and ez != 0.0:
            exInt = exInt + ex * Ki * halfT
            eyInt = eyInt + ey * Ki * halfT  
            ezInt = ezInt + ez * Ki * halfT

            gx = gx + Kp * ex + exInt
            gy = gy + Kp * ey + eyInt
            gz = gz + Kp * ez + ezInt
        
        q0 = q0 + (-q1 * gx - q2 * gy - q3 * gz) * halfT
        q1 = q1 + (q0 * gx + q2 * gz - q3 * gy) * halfT
        q2 = q2 + (q0 * gy - q1 * gz + q3 * gx) * halfT
        q3 = q3 + (q0 * gz + q1 * gy - q2 * gx) * halfT  
        
        denom = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if denom != 0:
            norm = float(1/denom)
            q0 = q0 * norm
            q1 = q1 * norm
            q2 = q2 * norm
            q3 = q3 * norm

    def icm20948MagCheck(self):
        self.icm20948ReadSecondary( I2C_ADD_ICM20948_AK09916|I2C_ADD_ICM20948_AK09916_READ,REG_ADD_MAG_WIA1, 2)
        if (pu8data[0] == REG_VAL_MAG_WIA1) and ( pu8data[1] == REG_VAL_MAG_WIA2) :
            bRet = true
        return bRet
  
    def icm20948update(self, latence=0.1):
        self.icm20948_Gyro_Accel_Read()
        self.icm20948MagRead()
        time.sleep(latence)
        self.imuAHRSupdate(
            self.Gyroscope[0] / 32.8 * 0.0175, self.Gyroscope[1] / 32.8 * 0.0175, self.Gyroscope[2] / 32.8 * 0.0175,
            self.Acceleration[0], self.Acceleration[1], self.Acceleration[2],
            self.Magnetic[0], self.Magnetic[1], self.Magnetic[2])
        self.Pitch = math.asin(-2 * q1 * q3 + 2 * q0* q2) * 57.3
        self.Roll  = math.atan2(2 * q2 * q3 + 2 * q0 * q1, -2 * q1 * q1 - 2 * q2* q2 + 1) * 57.3
        self.Yaw   = math.atan2(-2 * q1 * q2 - 2 * q0 * q3, 2 * q2 * q2 + 2 * q3 * q3 - 1) * 57.3
        
    
if __name__ == '__main__':
    import time
    icm20948 = ICM20948()
    while True:
        icm20948.icm20948update()
        print("-------------------------------------------------------------")
        print('Roll = {:.2f}, Pitch = {:.2f}, Yaw = {:.2f}'.format(icm20948.Roll, icm20948.Pitch, icm20948.Yaw))
        print('Acceleration:  X = {}, Y = {}, Z = {}'.format(icm20948.Acceleration[0], icm20948.Acceleration[1], icm20948.Acceleration[2]))  
        print('Gyroscope:     X = {}, Y = {}, Z = {}'.format(icm20948.Gyroscope[0], icm20948.Gyroscope[1], icm20948.Gyroscope[2]))
        print('Magnetic:      X = {}, Y = {}, Z = {}'.format(icm20948.Magnetic[0], icm20948.Magnetic[1], icm20948.Magnetic[2]))
