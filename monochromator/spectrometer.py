"""Allows pyseabreeze spectrometers to be loaded via a popup window
---Classes---
selectionBox:
    A tk widget to hold a list of tk.Radiobuttons which all refer to the same variable
    
Spectrometer:
    A wrapper for the seabreeze.spectrometer.Spectrometer class, which automatically
    searches for available OceanOptics spectrometers. If multiple devices (or no
    devices) are available, the software launches a tk window to list the options.
   
Created by: Jonathan D. B. Van Schenck
"""

#%%
import tkinter as tk
import seabreeze.spectrometers as sb
#%%
class selectionBox(tk.LabelFrame):
    '''Container for associated tk.Radiobuttons
    ---Initialization Parameters---
        master: tk.Frame instance into which the widget will be created
        variable: The underlying tk variable which all the Radiobuttons 
                    will be attached to
        valueList: List of possible values for which tk.Radiobuttons will
                    be created
        label: Optional Label for the tk.LabelFrame which wraps the radiobuttons
        textList: Optional list of labels to represent each valueList (must be either
                   the same length as valueList, or None).
    ---Variables---
    variable:
        The underlying tk variable which all the Radiobuttons will be attached to
       
    RBList:
        List to hold each tk.Radiobutton instance
       
    ---Methods---
    gen_list:
        Generates and packs the tk.Radiobuttons into a tk.LabelFrame
    
    '''
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
    """Wrapper for seabreeze.spectrometer.Spectrometer class with smart inialization and popup window
    ---Initialization Variables---
    
    ---Variables---
    
    ---Methods---
    """
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
