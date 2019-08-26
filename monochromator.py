#%%
import tkinter as tk
import os
from time import sleep
from tkinter import messagebox
from tkinter import filedialog
import seabreeze.spectrometers as sb
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.optimize import minimize
def gauss(x,p):
    return np.abs(p[0])+np.abs(p[1])*np.exp(-((x-p[2])/p[3])**2)

from time import localtime
def today():
    t = localtime()
    return "{0}{1:0>2}{2:0>2}-{3:0>2}{4:0>2}{5:0>2}".format(str(t.tm_year)[-2:],t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)
from ctypes import c_long, c_float, windll, pointer

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
            
class Calibrate(tk.Frame):
    def __init__(self,monochromator):
        tk.Frame.__init__(self,None)
        self.master.title("Calibration Window")
        self.master.protocol("WM_DELETE_WINDOW", lambda : self.master.destroy())
        self.spec = Spectrometer()
        self.specRunning = True
        self.mono = monochromator
        self.mono.reset_calibration()
        self.create_widgets()
        self.start_aquisition()
        self.mainloop()
        self.spec.close()
        
    def create_widgets(self):
        # Create MPL Figure
        self.mpl = MPL(self.master,
                       self.spec.wavelengths(),self.spec.intensities(),
                       #np.arange(0,100,0.1),gauss(np.arange(0,100,0.1),[200,2700,40,5]),
                       #self.spec.wavelengths,self.spec.intensities,
                       column=0,row=2,columnspan=2)
        
        # Create Spectrometer control window
        self.specFrame = tk.LabelFrame(self.master,text="Spectrometer Controls")
        self.specFrame.grid(column=0,row=0)
        self.ITLabel = tk.Label(self.specFrame,text="IT (ms)")
        self.ITLabel.grid(column=0,row=0,sticky=tk.E)
        self.ITvariable = tk.StringVar()
        self.set_IT(20)
        self.ITEntry = tk.Entry(self.specFrame,
                                textvariable=self.ITvariable,
                                width=6)
        self.ITEntry.grid(column=1,row=0)
        self.ITUpdateButton = tk.Button(self.specFrame,text="Update",
                                        command=lambda: self.set_IT(self.ITvariable.get()))
        self.ITUpdateButton.grid(column=2,row=0,sticky=tk.W)
        self.PPLabel = tk.Label(self.specFrame,text="Aquire:")
        self.PPLabel.grid(column=0,row=1,sticky=tk.E)
        self.playButton = tk.Button(self.specFrame,text="Play",
                                    command=lambda: self.start_aquisition())
        self.playButton.grid(column=1,row=1)
        self.pauseButton = tk.Button(self.specFrame,text="Pause",
                                    command=lambda: self.stop_aquisition())
        self.pauseButton.grid(column=2,row=1)
        
        # Create calibration setup
        self.calFrame = tk.LabelFrame(self.master,text="Spectrometer Controls")
        self.calFrame.grid(column=1,row=0)
        self.PosLabel = tk.Label(self.calFrame,text="Starting Position:")
        self.PosLabel.grid(column=0,row=0,sticky=tk.E)
        self.Posvariable = tk.StringVar()
        self.set_Pos(self.mono.lower_bound)
        self.PosEntry = tk.Entry(self.calFrame,
                                textvariable=self.Posvariable,
                                width=6)
        self.PosEntry.grid(column=1,row=0)
        self.PosUpdateButton = tk.Button(self.calFrame,text="Move",
                                        command=lambda: self.set_Pos(self.Posvariable.get()))
        self.PosUpdateButton.grid(column=2,row=0,sticky=tk.W)
        self.stepLabel = tk.Label(self.calFrame,text="Number of Steps:")
        self.stepLabel.grid(column=0,row=1,sticky=tk.E)
        self.Stepvariable = tk.StringVar()
        self.Stepvariable.set("3")
        self.StepEntry = tk.Entry(self.calFrame,
                                textvariable=self.Stepvariable,
                                width=6)
        self.StepEntry.grid(column=1,row=1)
        self.startCalButton = tk.Button(self.calFrame,
                                         text="Start Calibration",
                                         command = lambda: self.start_calibration())
        self.startCalButton.grid(column=0,row=2)
        self.nextButton = tk.Button(self.calFrame,
                                    text="Next Position",
                                    command = lambda: self.next_position())
        self.nextButton.grid(column=1,row=2)
        self.nextButton.config(state='disabled')
        
        
    def set_IT(self,IT):
        try:
            it = int(IT)*1000
        except:
            it = 100*1000
        if it<10*1000:
            it = 10*1000
        elif it>10*1000*1000:
            it = 10*1000*1000
        self.spec.integration_time_micros(it)
        self.ITvariable.set(str(it//1000))
        self.mpl.update_spectrum(self.spec.intensities())
    
    def set_Pos(self,POS):
        try:
            pos = int(POS)
        except:
            pos = 100
        if pos<0:
            pos = 0
        elif pos>150:
            pos = 150
        self.mono.set_lower_bound(pos)
        self.Posvariable.set(str(pos))
        self.mono.move(self.mono.lower_bound)
        
    def start_aquisition(self):
        self.specRunning = True
        self.aquire()
    
    def aquire(self):
#        y = self.mpl.spectrum.get_ydata()
        self.mpl.update_spectrum(self.spec.intensities())#(0.99*y)
        if self.specRunning:
            self.master.after(0,self.aquire)
            
    def stop_aquisition(self):
        self.specRunning = False
        
    def start_calibration(self):
        self.stop_aquisition()
        self.playButton.config(state="disabled")
        self.pauseButton.config(state="disabled")
        self.PosUpdateButton.config(state="disabled")
        self.startCalButton.config(state="disabled")
        self.nextButton.config(state='normal')
        try:
            n = int(self.Stepvariable.get())
        except:
            n = 5
        if n<2:
            n = 2
        elif n>10:
            n = 10
        self.mmSpace = list(self.mono.lower_bound-np.linspace(5,31-4,n))
        self.mono.move(self.mmSpace.pop(0))
        sleep(0.1)
        self.mpl.update_spectrum(self.spec.intensities())
        self.mpl.gen_fit()
        
    def next_position(self):
        self.mono.add_point(self.mono.mot.getPos(),*self.mpl.p[-2:])
        try:
            mm = self.mmSpace.pop(0)
        except IndexError:
            self.save_calibration_file()
            self.master.destroy()
        else:
            self.mono.move(mm)
            sleep(0.1)
            self.mpl.update_spectrum(self.spec.intensities())
            self.mpl.gen_fit()
        
    
    def save_calibration_file(self):
        path = filedialog.askdirectory(initialdir = os.getcwd(),
                                      title= "Calibration File Directory")
        self.mono.save_calibration_points(path)
    
    
class MPL:
    def __init__(self,master,x,y,p=[0,0,500,5],**kwargs):
        self.x = x
        self.p = np.array(p)
        
        # Create tk Frame to hold MPL plot
        self.frame = tk.Frame(master)
        self.frame.grid(**kwargs)
        
        # Create MPL figure
        self.fig = plt.figure(figsize=(10,5))
        self.ax = self.fig.add_subplot(111)
        self.spectrum, = self.ax.plot(x,y,color="blue")
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Counts")
        self.ax.set_ylim(0,4000)
        
        # Attached MPL figure and toolbar to tk Frame
        self.canvas = FigureCanvasTkAgg(self.fig,self.frame)
        self.canvas.get_tk_widget().pack()
        self.toolbar = NavigationToolbar2Tk(self.canvas,self.frame)
        self.toolbar.update()
        
        # initialize fit
        self.fit, = self.ax.plot(x,gauss(x,self.p),color="black")
        
        # Setup MPL click collbacks
        self.canvas.mpl_connect('button_press_event',self.click)
        
    def click(self,event):
        if event.inaxes == self.ax:
            if event.button == 1:
                print("Left click @ x=",event.xdata," y=",event.ydata)
                self.p[1],self.p[2] = event.ydata,event.xdata
                self.update_fit()
            if event.button == 2:
                print("Scroll click @ x=",event.xdata," y=",event.ydata)
            if event.button == 3:
                print("Right click @ x=",event.xdata," y=",event.ydata)
                self.gen_fit()
    
    def update_fit(self):
        self.fit.set_ydata(gauss(self.x,self.p))
        self.fig.canvas.draw()
        
    def update_spectrum(self,y):
        self.spectrum.set_ydata(y)
        self.fig.canvas.draw()
        
    def gen_fit(self):
        y = self.spectrum.get_ydata()
        x0 = self.x[np.argmax(y)]
        y0 = np.max(y)
        mask = np.array(np.abs(self.x-x0)<50)
        def diff(p):
            return np.sum((y[mask]-gauss(self.x,p)[mask])**2)
        fit = minimize(diff,[y[0],y0,x0,1])
#        print(fit)
        self.p = np.copy(fit.x)
        self.update_fit()
        
#%
class selectionBox(tk.LabelFrame):
    def __init__(self,master,variable,valueList,label="",textList=None):
        tk.LabelFrame.__init__(self,master,text=label)
        self.variable = variable
        self.RBList = []
        self.gen_list(valueList,textList)
        
        
    def gen_list(self,valueList,textList=None):
        for rb in self.RBList:
            rb.destroy()
        if textList is None:
            tL = [str(v) for v in valueList]
        else:
            tL = textList
        self.RBList = [tk.Radiobutton(self,text=t,variable=self.variable,value=v,indicatoron=0)\
                       for t,v in zip(tL,valueList)]
        for i,rb in enumerate(self.RBList):
            rb.grid(column=0,row=i)

class Spectrometer(sb.Spectrometer):
    def __init__(self):
        def scan():
            return sb.list_devices()
        deviceList = scan()
        if len(deviceList) == 1:
            sb.Spectrometer.__init__(self,deviceList[0])
        else:
            root = tk.Tk()
            root.title("Spectrometer Selection")
            root.geometry("200x200")
            d = tk.StringVar()
            buttonList = selectionBox(root,d,deviceList,label="Select Spectrometer")
            buttonList.grid(column=0,row=1,columnspan=2)
            def rescan(buttonList):
                deviceList = scan()
                buttonList.gen_list(deviceList)
            tk.Button(root,text="Rescan",command= lambda : rescan(buttonList)).grid(column=0,row=0)
            def load():
                try:
                    sb.Spectrometer.__init__(self,d.get())
                except:
                    print("Problem loading device \'%s\', try again" % d.get())
                else:
                    root.destroy()
            tk.Button(root,text="Load",command=load).grid(column=1,row=0)
            root.protocol("WM_DELETE_WINDOW", lambda : root.destroy())
            root.mainloop()