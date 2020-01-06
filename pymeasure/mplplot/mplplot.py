from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import random,time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class MPLWidget(QWidget):
    def __init__(self,*args,**kwargs):
        super(MPLWidget,self).__init__(*args,**kwargs)
        self.canvas=MPLCanvas(self)
        self.toolbar=NavigationToolbar(self.canvas,self)
        self.mtoolbar=MPLToolbar(self.canvas,self)
        layout=QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.mtoolbar)
        self.setLayout(layout)
        self.toolbartext='Hide Toolbar'
        self.autoScaleXAct = QAction('Auto Scale X', self, checkable=True)
        self.autoScaleXAct.triggered.connect(self.canvas.autoScaleXF)
        self.autoScaleYAct = QAction('Auto Scale Y', self, checkable=True)
        self.autoScaleYAct.triggered.connect(self.canvas.autoScaleYF)

    def contextMenuEvent(self,event):
        cmenu=QMenu(self)
        self.toolbarAct=cmenu.addAction(self.toolbartext)
        self.autoScaleXAct.setChecked(self.canvas.autoScaleX)
        cmenu.addAction(self.autoScaleXAct)
        self.autoScaleYAct.setChecked(self.canvas.autoScaleY)
        cmenu.addAction(self.autoScaleYAct)
        action=cmenu.exec_(self.mapToGlobal(event.pos()))
        if action==self.toolbarAct:
            self.SHToolbar()
            
    def setFigure(self,title='Figure',xlabel='x Label', ylabel='y Label'):
        self.canvas.setFigure(title,xlabel,ylabel)        
    def plot(self):
        self.canvas.plot()
        
    def SHToolbar(self):
        self.toolbar.setHidden(not self.toolbar.isHidden())
        if self.toolbar.isHidden():
            self.toolbartext='Show Toolbar'
        else:
            self.toolbartext='Hide Toolbar'
    


class MPLCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('dark_background')
        fig = Figure(dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.threadpool = QThreadPool()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.mparent=parent
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.MinimumExpanding,
                QSizePolicy.MinimumExpanding)
        FigureCanvas.updateGeometry(self)
        self.line=None
        self.autoScaleX=True
        self.autoScaleY=True
        self.updatefig=False
        self.cursorOn=False
        self.zoomBox=MPLZoomBox(self,(0.1,0.1),width=0.5,height=0.5,fill=False,
                                color='r',linestyle='dotted',visible=False)
        self.cursor=MPLCursor(self)
        #Below are two possible cursor implementations.
        #self.mpl_connect('motion_notify_event',self.cursorPos)
        #self.cursor = Cursor(self.axes, useblit=True, color='red', linewidth=1)
        self.draw()
        self.timer = self.new_timer(100, [(self.update_canvas, (), {})])
        self.timer.start()
    
    def update_canvas(self):
        if self.updatefig:
            self.autoScale()
            self.draw()
            self.updatefig=False
        
    def setFigure(self,title='Figure',xlabel='x Label', ylabel='y Label'):
        self.axes.clear()
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.grid(True,which='both',color='y',linestyle='--',linewidth=0.5)
        self.zoomBox=MPLZoomBox(self,(0.1,0.1),width=0.5,height=0.5,fill=False,
                                color='r',linestyle='dotted',visible=False)
        self.cursor=MPLCursor(self)
        self.cursor.connectEvents()
        self.axes.add_patch(self.zoomBox)
        self.zoomEvent=False
        
        #For second cursor implementation
        #self.cursorX=self.getLineHandle()
        #self.cursorX.set_color('r')
        #self.cursorY=self.getLineHandle()
        #self.cursorY.set_color('r')
    
    def getLineHandle(self):
        self.line, =self.axes.plot([],[])
        return self.line
    
    def plot(self):
        worker=MPLWorker(self.plot0)
        self.threadpool.start(worker)
        
    def getaxlims(self,data,tickpos,lefttight=True,righttight=False):
        npdata=np.array(data)
        ll=np.min(npdata)
        ul=np.max(npdata)
        deltatick=tickpos[1]-tickpos[0]
        #print(tickpos,deltatick)
        if lefttight:
            tickpos[0]=ll
        else:
            while tickpos[0]>ll: #Expand lowerlimit if necessary
                tickpos[0]=tickpos[0]-deltatick
            while tickpos[0]+deltatick<ll: #Contract lowerlimit if necessary
                tickpos[0]=tickpos[0]+deltatick
                #print("Lower level",ll,"Proposed",tickpos[0])
        if righttight:
            tickpos[-1]=ul
        else:
            while tickpos[-1]<ul: #Expand upperlimit if necessary
                tickpos[-1]=tickpos[-1]+deltatick
            while tickpos[-1]-deltatick>ul: #Contract upperlimit if necessary
                tickpos[-1]=tickpos[-1]-deltatick
                #print("Upper level",ul,"Proposed",tickpos[-1])
        return [tickpos[0],tickpos[-1]]
    
    def autoScale(self):
        #self.axes.relim()
        xbi=self.axes.get_xbound()
        ybi=self.axes.get_ybound()
        try:
            xticks=self.axes.get_xticks()
            yticks=self.axes.get_yticks()
            xd,yd =self.line.get_data()
            #print("Ticks:",xticks[0],xticks[-1],yticks[0],yticks[-1])
            if len(xd)>1:
                if self.autoScaleX:
                    #print("AutoScale X")
                    self.axes.set_xlim(self.getaxlims(xd,xticks))
                if self.autoScaleY:
                    #print("AutotScale Y")
                    self.axes.set_ylim(self.getaxlims(yd,yticks,lefttight=False))
                    #print(type(xd))
            xbf=self.axes.get_xbound()
            ybf=self.axes.get_ybound()
            self.cursor.repos(xbi,ybi,xbf,ybf)
        #self.axes.autoscale_view(tight=False,scalex=self.autoScaleX,scaley=self.autoScaleY)
        except:
            pass
    def autoScaleXF(self):
        self.autoScaleX=(not self.autoScaleX)
        if self.mparent.mtoolbar.magnifyAction.isChecked():
            self.mparent.mtoolbar.magnifyAction.trigger()
        #elif self.mparent.mtoolbar.panAction.isChecked():
        #    self.mparent.mtoolbar.pan(None)
        try:
            self.autoScale()
        except:
            pass
        self.updatefig=True
        
    def autoScaleYF(self):
        self.autoScaleY=(not self.autoScaleY)
        if self.toolbar.magnifyAction.isChecked():
            self.toolbar.magnifyAction.trigger()
        #elif self.mparent.mtoolbar.panAction.isChecked():
        #    self.mparent.mtoolbar.pan(None)
        try:
            self.autoScale()
        except:
            pass
        self.updatefig=True
        
    def cursorPos(self,event):
        if (event.xdata!=None):
            self.cursorX.set_data([event.xdata,event.xdata],self.axes.get_ylim())
            self.cursorY.set_data(self.axes.get_xlim(),[event.ydata,event.ydata])
            self.updatefig=True
            
    def drawZoomBox(self,event):
        if event.name=='button_press_event' and event.button==1:
            self.zoomBox.set_xy((event.xdata,event.ydata))
            self.zoomEvent=True
        elif self.zoomEvent and event.name=='motion_notify_event':
            xpos,ypos=self.zoomBox.get_xy()
            self.zoomBox.set_width(event.xdata-xpos)
            self.zoomBox.set_height(event.ydata-ypos)
            self.zoomBox.set_visible(True)
            self.updatefig=True          
        elif event.name=='button_release_event' and event.button==1 and self.zoomEvent:
            self.zoomBox.set_visible(False)
            xbi=self.axes.get_xbound()
            ybi=self.axes.get_ybound()
            xbf=self.zoomBox.getxlim()
            ybf=self.zoomBox.getylim()
            self.axes.set(xlim=xbf,ylim=ybf)
            self.cursor.repos(xbi,ybi,xbf,ybf)
            self.zoomEvent=False
            self.updatefig=True
            
    def drawCursor(self,event):
        if self.cursorOn and event.name=='motion_notify_event':
            self.cursor.set_pos(event.xdata,event.ydata)
            self.updatefig=True   
    def leaveAxes(self,event):
        if self.zoomEvent:
            self.zoomEvent=False
            self.zoomBox.set_visible(False)
        if self.cursorOn:
            self.cursor.set_visible(False)
        self.updatefig=True
    def enterAxes(self,event):
        if self.cursorOn:
            self.cursor.set_visible(True)
            self.updatefig=True
    def setToolbar(self,toolbar):
        self.toolbar=toolbar
      

        
class MPLToolbar(QToolBar):
    def __init__(self,canvas,parent,*args,**kwargs):
        #super(MPLToolbar,self).__init__(*args,**kwargs)
        QToolBar.__init__(self, parent)
        self.resdir="C:\\Users\\byilm\\OneDrive\\Documents\\Python Scripts\\pymeasure\\pymeasure\\mplplot\\res\\"
        self.canvas=canvas
        canvas.setToolbar(self)
        self.zoomBox=self.canvas.zoomBox
        self.parent=parent
        
        #Define zoom button
        self.magnifyAction=QAction('',self)
        self.magnifyAction.setToolTip('Zoom to Rectangle')
        self.magnifyAction.setIcon(QIcon(self.resdir+'magnifier-left.png'))
        self.magnifyAction.setCheckable(True)
        self.magnifyAction.triggered.connect(self.magnify)
        self.addAction(self.magnifyAction)
        
        #Define pan button
        self.panAction=QAction('',self)
        self.panAction.setToolTip('Pan Axes')
        self.panAction.setIcon(QIcon(self.resdir+'arrow-move.png'))
        self.panAction.setCheckable(True)
        self.panAction.triggered.connect(self.pan)
        self.addAction(self.panAction)
        
        #Define cursor button
        self.cursorAction=QAction('',self)
        self.cursorAction.setToolTip('Switch Cursor On/Off')
        self.cursorAction.setIcon(QIcon(self.resdir+'target.png'))
        self.cursorAction.setCheckable(True)
        self.cursorAction.triggered.connect(self.cursorSwitch)
        self.addAction(self.cursorAction)
        
        
    def magnify(self,event):
        self.panAction.setChecked(False)
        events=['button_press_event','button_release_event','motion_notify_event']
        if self.magnifyAction.isChecked():
            self.parent.autoScaleXAct.setChecked(False)
            self.parent.autoScaleYAct.setChecked(False)
            self.canvas.autoScaleX=False
            self.canvas.autoScaleY=False
            self.zoomBox.connectEvents()
        else:
            self.zoomBox.disconnectEvents()
        
    def pan(self,event):
        self.magnifyAction.setChecked(False)
        
    def cursorSwitch(self,event):
        if self.cursorAction.isChecked():
            self.canvas.cursorOn=True
        else:
            self.canvas.cursorOn=False
            self.canvas.cursor.set_visible(False)
            self.canvas.updatefig=True

class MPLZoomBox(Rectangle):
    def __init__(self,canvas,*args,**kwargs):
        Rectangle.__init__(self,*args,**kwargs)
        self.canvas=canvas
        self.zoomEvents=[None,None,None]
        self.events=['button_press_event','button_release_event','motion_notify_event']
        
    def connectEvents(self):
        self.axEvent=self.canvas.mpl_connect('axes_leave_event',self.canvas.leaveAxes)
        for i in range(len(self.events)):
            self.zoomEvents[i]=self.canvas.mpl_connect(self.events[i],self.canvas.drawZoomBox)
            
    def disconnectEvents(self):
        try:
            self.canvas.mpl_disconnect(self.axEvent)
            for i in range(len(self.events)):
                self.canvas.mpl_disconnect(self.zoomEvents[i])
        except:
            pass
        
    def getxlim(self):
        x=self.get_x()
        w=self.get_width()
        return self._orderedlims(x,w)
        
    def getylim(self):
        y=self.get_y()
        h=self.get_height()
        return self._orderedlims(y,h)
    
    def _orderedlims(self,a,b):
        c=a+b
        if a<c:
            return(a,c)
        else:
            return (c,a)

class MPLCursor():
    def __init__(self,canvas,*args,**kwargs):
        self.canvas=canvas
        self.lineh = self.canvas.axes.axhline(self.canvas.axes.get_ybound()[0], visible=False, color='r')
        self.linev = self.canvas.axes.axvline(self.canvas.axes.get_xbound()[0], visible=False, color='r')
        self._x=0
        self._y=0
        self.cursorEvents=[None,None,None]
        self.events=['button_press_event','button_release_event','motion_notify_event']
        self.connectEvents()
        
    def set_visible(self,isVisible):
        self.lineh.set_visible(isVisible)
        self.linev.set_visible(isVisible)
    def set_pos(self,xpos,ypos):
        self._x=xpos
        self._y=ypos
        self.linev.set_xdata((xpos,xpos))
        self.lineh.set_ydata((ypos,ypos))
    def repos(self,xi,yi,xf,yf):
        xpos=xf[0]+(xf[1]-xf[0])*(self._x-xi[0])/(xi[1]-xi[0])
        ypos=yf[0]+(yf[1]-yf[0])*(self._y-yi[0])/(yi[1]-yi[0])
        self.set_pos(xpos,ypos)
    def connectEvents(self):
        self.axleaveEvent=self.canvas.mpl_connect('axes_leave_event',self.canvas.leaveAxes)
        self.axenterEvent=self.canvas.mpl_connect('axes_enter_event',self.canvas.enterAxes)
        for i in range(len(self.events)):
            self.cursorEvents[i]=self.canvas.mpl_connect(self.events[i],self.canvas.drawCursor)
            
    def disconnectEvents(self):
        try:
            self.canvas.mpl_disconnect(self.axleaveEvent)
            self.canvas.mpl_disconnect(self.axenterEvent)
            for i in range(len(self.events)):
                self.canvas.mpl_disconnect(self.cursorEvents[i])
        except:
            pass
        
class MPLWorker(QRunnable):
    
    def __init__(self, fn, *args, **kwargs):
        super(MPLWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)        