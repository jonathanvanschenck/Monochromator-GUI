#%%
import tkinter as tk
import os
#from datetime.datetime import today
from tkinter import filedialog
from spectrometer import Spectrometer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.optimize import minimize
def gauss(x,p):
    return p[0]+np.abs(p[1])*np.exp(-((x-p[2])/p[3])**2)

class Calibrate(tk.Frame):
    def __init__(self,monochromator):
        #self.spec = Spectrometer()
        self.specRunning = True
        #self.mono = monochromator
        tk.Frame.__init__(self,None)
        self.master.title("Calibration Window")
        self.master.protocol("WM_DELETE_WINDOW", lambda : self.master.destroy())
        self.create_widgets()
        self.mainloop()
        
    def create_widgets(self):
        # Create Spectrometer control window
        self.specFrame = tk.LabelFrame(self.master,text="Spectrometer Controls")
        self.specFrame.grid(column=0,row=0)
        self.ITLabel = tk.Label(self.specFrame,text="IT (ms)")
        self.ITLabel.grid(column=0,row=0,sticky=tk.E)
        self.ITvariable = tk.StringVar()
        self.set_IT(100)
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
        
        # Create MPL Figure
        self.mpl = MPL(self.master,
                       np.arange(0,100,0.1),gauss(np.arange(0,100,0.1),[200,2700,40,5]),
                       #self.spec.wavelengths,self.spec.intensities,
                       column=0,row=2)
        
    def set_IT(self,IT):
        try:
            it = int(IT)*1000
        except:
            it = 100*1000
        if it<10*1000:
            it = 10*1000
        elif it>10*1000*1000:
            it = 10*1000*1000
        #self.spec.integration_time_micros(it)
        self.ITvariable.set(str(it//1000))
        
    def start_aquisition(self):
        self.specRunning = True
        self.aquire()
    
    def aquire(self):
        y = self.mpl.spectrum.get_ydata()
        self.mpl.update_spectrum(0.99*y)
        if self.specRunning:
            self.master.after(0,self.aquire)
            
    def stop_aquisition(self):
        self.specRunning = False
        
    def save_calibration_file(self):
        path = filedialog.asksaveasfile(intialdir = os.get_cwd(),
                                      title= "Calibration File Directory")#,
                                      #filetypes = (("calibration files","*.cal"),("all files","*.*")),
                                      #confirmoverwrite=True)#,
                                      #initialfile=str(today()))
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
        def diff(p):
            return np.sum((y-gauss(self.x,p))**2)
        fit = minimize(diff,[y[0],y0,x0,5])
#        print(fit)
        self.p = np.copy(fit.x)
        self.update_fit()