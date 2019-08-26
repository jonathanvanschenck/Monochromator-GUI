#%%
import tkinter as tk
import seabreeze.spectrometers as sb
#%%
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