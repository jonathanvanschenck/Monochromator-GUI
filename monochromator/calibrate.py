#%%
import tkinter as tk
import os
from time import sleep
from tkinter import messagebox
from tkinter import filedialog
from spectrometer import Spectrometer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.optimize import minimize
def gauss(x,p):
    return np.abs(p[0])+np.abs(p[1])*np.exp(-((x-p[2])/p[3])**2)

class Calibrate(tk.Frame):
    def __init__(self,monochromator):
        tk.Frame.__init__(self,None)
        self.master.title("Calibration Window")
        self.master.protocol("WM_DELETE_WINDOW", lambda : self.master.destroy())
        if not messagebox.askyesno("Title","Create a new calibration file?"):
            fname = filedialog.askopenfilename(title="Load Calibration File",
                                               initialdir = os.getcwd(),
                                               filetypes = (("calibration files","*.cal"),("all files","*.*")))
            monochromator.load_calibration_points(fname)
            self.master.destroy()
        else:
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