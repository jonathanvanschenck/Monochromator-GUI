#%%
from time import localtime
def today():
    t = localtime()
    return "{0}{1:0>2}{2:0>2}-{3:0>2}{4:0>2}{5:0>2}".format(str(t.tm_year)[-2:],t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)
from ctypes import c_long, c_buffer, c_float, windll, pointer
import os
import numpy as np
#%%

class APTMotor():
    def __init__(self,SerialNum=None, HWTYPE=31, loc='', verbose=False, dllname='APT.dll'):
        '''
        HWTYPE_BSC001		11	// 1 Ch benchtop stepper driver
        HWTYPE_BSC101		12	// 1 Ch benchtop stepper driver
        HWTYPE_BSC002		13	// 2 Ch benchtop stepper driver
        HWTYPE_BDC101		14	// 1 Ch benchtop DC servo driver
        HWTYPE_SCC001		21	// 1 Ch stepper driver card (used within BSC102,103 units)
        HWTYPE_DCC001		22	// 1 Ch DC servo driver card (used within BDC102,103 units)
        HWTYPE_ODC001		24	// 1 Ch DC servo driver cube
        HWTYPE_OST001		25	// 1 Ch stepper driver cube
        HWTYPE_MST601		26	// 2 Ch modular stepper driver module
        HWTYPE_TST001		29	// 1 Ch Stepper driver T-Cube
        HWTYPE_TDC001		31	// 1 Ch DC servo driver T-Cube
        HWTYPE_LTSXXX		42	// LTS300/LTS150 Long Travel Integrated Driver/Stages
        HWTYPE_L490MZ		43	// L490MZ Integrated Driver/Labjack
        HWTYPE_BBD10X		44	// 1/2/3 Ch benchtop brushless DC servo driver
        '''

        self.verbose = verbose
#        print(1)
        self.Connected = False
#        print(2)
        if not os.path.exists(loc+dllname):
#            print(3)
            print("ERROR: DLL not found")
#        print(4)
        self.aptdll = windll.LoadLibrary(loc+dllname)
#        print(5)
        self.aptdll.EnableEventDlg(True)
#        print(6)
        self.aptdll.APTInit()
#        print(7)
        #print('APT initialized'
        self.HWType = c_long(HWTYPE)
#        print(8)
        self.blCorr = 0.10 #100um backlash correction
#        print(9)
        if SerialNum is not None:
#            print(10)
            if self.verbose: print("Serial is", SerialNum)
#            print(11)
            self.SerialNum = c_long(SerialNum)
#            print(12)
            self.initializeHardwareDevice()
        # TODO : Error reporting to know if initialisation went sucessfully or not.
        else:
#            print(13)
            if self.verbose: print("No serial, please setSerialNumber")

    def getNumberOfHardwareUnits(self):
        '''
        Returns the number of HW units connected that are available to be interfaced
        '''
        numUnits = c_long()
        self.aptdll.GetNumHWUnitsEx(self.HWType, pointer(numUnits))
        return numUnits.value

    def initializeHardwareDevice(self):
        '''
        Initialises the motor.
        You can only get the position of the motor and move the motor after it has been initialised.
        Once initiallised, it will not respond to other objects trying to control it, until released.
        '''
        if self.verbose: print('initializeHardwareDevice serial', self.SerialNum)
        result = self.aptdll.InitHWDevice(self.SerialNum)
        if result == 0:
            self.Connected = True
            if self.verbose: print('initializeHardwareDevice connection SUCESS')
        # need some kind of error reporting here
        else:
            raise Exception('Connection Failed. Check Serial Number!')
        return True

        '''
        Controlling the motors
        m = move
        c = controlled velocity
        b = backlash correction

        Rel = relative distance from current position.
        Abs = absolute position
        '''
    def getPos(self):
        '''
        Obtain the current absolute position of the stage
        '''
        if self.verbose: print('getPos probing...')
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')

        position = c_float()
        self.aptdll.MOT_GetPosition(self.SerialNum, pointer(position))
        if self.verbose: print('getPos ', position.value)
        return position.value

    def mRel(self, relDistance):
        '''
        Moves the motor a relative distance specified
        relDistance    float     Relative position desired
        '''
        if self.verbose: print('mRel ', relDistance, c_float(relDistance))
        if not self.Connected:
            print('Please connect first! Use initializeHardwareDevice')
            #raise Exception('Please connect first! Use initializeHardwareDevice')
        relativeDistance = c_float(relDistance)
        self.aptdll.MOT_MoveRelativeEx(self.SerialNum, relativeDistance, True)
        if self.verbose: print('mRel SUCESS')
        return True

    def mAbs(self, absPosition):
        '''
        Moves the motor to the Absolute position specified
        absPosition    float     Position desired
        '''
        if self.verbose: print('mAbs ', absPosition, c_float(absPosition))
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')
        absolutePosition = c_float(absPosition)
        self.aptdll.MOT_MoveAbsoluteEx(self.SerialNum, absolutePosition, True)
        if self.verbose: print('mAbs SUCESS')
        return True

    def mcRel(self, relDistance, moveVel=0.5):
        '''
        Moves the motor a relative distance specified at a controlled velocity
        relDistance    float     Relative position desired
        moveVel        float     Motor velocity, mm/sec
        '''
        if self.verbose: print('mcRel ', relDistance, c_float(relDistance), 'mVel', moveVel)
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')
        # Save velocities to reset after move
        maxVel = self.getVelocityParameterLimits()[1]
        # Set new desired max velocity
        self.setVel(moveVel)
        self.mRel(relDistance)
        self.setVel(maxVel)
        if self.verbose: print('mcRel SUCESS')
        return True

    def mcAbs(self, absPosition, moveVel=0.5):
        '''
        Moves the motor to the Absolute position specified at a controlled velocity
        absPosition    float     Position desired
        moveVel        float     Motor velocity, mm/sec
        '''
        if self.verbose: print('mcAbs ', absPosition, c_float(absPosition), 'mVel', moveVel)
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')
        # Save velocities to reset after move
        minVel, acc, maxVel = self.getVelocityParameters()
        # Set new desired max velocity
        self.setVel(moveVel)
        self.mAbs(absPosition)
        self.setVel(maxVel)
        if self.verbose: print('mcAbs SUCESS')
        return True

    def mbRel(self, relDistance):
        '''
        Moves the motor a relative distance specified
        relDistance    float     Relative position desired
        '''
        if self.verbose: print('mbRel ', relDistance, c_float(relDistance))
        if not self.Connected:
            print('Please connect first! Use initializeHardwareDevice')
            #raise Exception('Please connect first! Use initializeHardwareDevice')
        self.mRel(relDistance-self.blCorr)
        self.mRel(self.blCorr)
        if self.verbose: print('mbRel SUCESS')
        return True

    def mbAbs(self, absPosition):
        '''
        Moves the motor to the Absolute position specified
        absPosition    float     Position desired
        '''
        if self.verbose: print('mbAbs ', absPosition, c_float(absPosition))
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')
        if (absPosition < self.getPos()):
            if self.verbose: print('backlash mAbs', absPosition - self.blCorr)
            self.mAbs(absPosition-self.blCorr)
        self.mAbs(absPosition)
        if self.verbose: print('mbAbs SUCESS')
        return True


    def go_home(self):
        '''
        Move the stage to home position and reset position entry
        '''
        if self.verbose: print('Going home')
        if not self.Connected:
            raise Exception('Please connect first! Use initializeHardwareDevice')
        if self.verbose: print('go_home SUCESS')
        self.aptdll.MOT_MoveHome(self.SerialNum)
        return True


    def cleanUpAPT(self):
        '''
        Releases the APT object
        Use when exiting the program
        '''
        self.aptdll.APTCleanUp()
        if self.verbose: print('APT cleaned up')
        self.Connected = False


class Monochromator:
    def __init__(self,reset=True,SerialNum=20808447, HWTYPE=13, loc='C:/Users/vanschej/Documents/Python Scripts/PyAPT/',verbose=False, dllname='APT.dll'):
        self.mot = APTMotor(SerialNum=SerialNum, HWTYPE=HWTYPE, loc=loc,verbose=verbose, dllname=dllname)
        self.reset_calibration()
        self.set_lower_bound(10)
        if reset:
            self.go_home()
        
    def go_home(self):
        self.mot.go_home()
        self.move(self.lower_bound+5)
    
    def move(self,mm):
#        print(mm)
        self.mot.mbAbs(mm)
        
    def set_lower_bound(self,mm):
        self.lower_bound = mm
    
    def reset_calibration(self):
        self.__calibration = [[],[],[]]
        
    def add_point(self,pos,wave,fwhm):
        self.__calibration[0].append(pos)
        self.__calibration[1].append(wave)
        self.__calibration[2].append(fwhm)
        
    def create_calibration(self):
        self.__b=np.sum((np.array(self.__calibration[1])-np.mean(self.__calibration[1]))*(np.array(self.__calibration[0])-np.mean(self.__calibration[0])))/np.sum((np.array(self.__calibration[1])-np.mean(self.__calibration[1]))**2)
        self.__a=np.mean(self.__calibration[0])-self.__b*np.mean(self.__calibration[1])
        self.__monoBound = [np.ceil((self.lower_bound-self.__a)/self.__b),np.floor((self.lower_bound-31-self.__a)/self.__b)]
    
    def save_calibration_points(self,path_to_folder):
        self.create_calibration()
        oldD = os.getcwd()
        os.chdir(path_to_folder)
        f = open(today()+".cal","w")
        for c in self.__calibration:
            f.write(",".join([str(cc) for cc in c])+"\n")
        f.write("{0},{1},{2},{3}\n".format(self.__b,self.__a,*self.__monoBound))
        f.close()
        os.chdir(oldD)

    def load_calibration_points(self,file):
        f = open(file)
        calibrationPoints = [[float(ll) for ll in l.strip("\n").split(",")] for l in f]
        check_old = np.array(calibrationPoints.pop())
        self.reset_calibration()
        for p,w,f in zip(*calibrationPoints):
            self.add_point(p,w,f)
        self.create_calibration()
        check_new = np.append([self.__b,self.__a],self.__monoBound)
        return np.all(np.abs(check_old-check_new)/check_old < 0.1)
    
    def get_pos(self,lam):
        res = self.__a+self.__b*lam
        #assert res>=iniPos and res<=iniPos+31
        return(res)

    def go_to_wave(self,lam):
        self.move(self.get_pos(lam))
        
    def shutdown(self):
        self.mot.cleanUpAPT()
