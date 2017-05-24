
from pyqtgraph.Qt import QtCore, QtGui
from PositionList import posList as PositionList
import functools
from imageSourceMM import imageSource
import threading
import numpy as np

class FocusCorrectionPlaneWindow(QtGui.QWidget):

    def __init__(self , posList,imgSrc, debug=True):

        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()

        table_layout = QtGui.QVBoxLayout()

        self.positionListTable = QtGui.QTableWidget(self)

        self.imgSrc = imgSrc
        self.posList = posList

        table_layout.addWidget(self.positionListTable)
        self.fill_table()
        self.positionListTable.itemSelectionChanged.connect(self.select_row)

        self.currentPositionTable = QtGui.QTableWidget(self)
        self.setup_current_position_table()
        table_layout.addWidget(self.currentPositionTable)
        self.currentPositionTable.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        table_layout.addStretch(1)
        buttonlayout = QtGui.QVBoxLayout()

        mark_button=QtGui.QPushButton("mark new",self)
        reshift_button = QtGui.QPushButton("reshift Z",self)
        delete_button = QtGui.QPushButton("delete selected",self)
        delete_all_button = QtGui.QPushButton("delete all",self)
        goto_button = QtGui.QPushButton("go to selected",self)
        load_button = QtGui.QPushButton("Load Position list",self)
        save_button = QtGui.QPushButton("Save Position list",self)

        delete_button.clicked.connect(self.delete_selected)
        mark_button.clicked.connect(self.mark_new)
        delete_all_button.clicked.connect(self.delete_all)
        goto_button.clicked.connect(self.goto_selected)
        load_button.clicked.connect(self.load_position_list)
        save_button.clicked.connect(self.save_position_list)

        buttonlayout.addWidget(mark_button)
        buttonlayout.addWidget(reshift_button)
        buttonlayout.addWidget(goto_button)
        buttonlayout.addWidget(delete_button)
        buttonlayout.addWidget(delete_all_button)
        buttonlayout.addWidget(load_button)
        buttonlayout.addWidget(save_button)
        buttonlayout.addStretch(1)
        
        self.layout.addLayout(table_layout)
        self.layout.addLayout(buttonlayout)
        self.setLayout(self.layout)
        self.resize(430, 500)
        self._dialog = None
       

        self.update_current_pos()
    
    def load_position_list(self,evt):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'Position List File', selectedFilter='*.csv')
        print fileName
        self.posList.LoadFromFile(fileName,'AxioVision')
        self.fill_table()
        self.update_plane()


    def save_position_list(self,evt):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 'Position List File', selectedFilter='*.csv')
        print fileName
        self.posList.save_position_list(fileName)
        


    def setup_current_position_table(self):
        self.currentPositionTable.clear()
        self.currentPositionTable.setRowCount(1)
        self.currentPositionTable.setColumnCount(3)
        self.currentPositionTable.setHorizontalHeaderLabels(["Xcurr", "Ycurr","Zcurr"])

    def goto_selected(self):
        i_sel=self.positionListTable.currentRow()
        (xx,yy,zz)=self.posList.getXYZ()
        x=xx[i_sel]
        y=yy[i_sel]
        z=zz[i_sel]
        self.imgSrc.set_xy(x,y)
        self.imgSrc.set_z(z)

    def update_plane(self):
        x,y,z = self.posList.getXYZ()
        if len(x)>3:
            XYZ = np.column_stack((x,y,z))
            self.imgSrc.define_focal_plane(np.transpose(XYZ))

    def delete_all(self):
        "delete all the positions"
        self.posList.select_all()
        self.posList.delete_selected()
        self.fill_table()

    def delete_selected(self):
        i_sel = self.positionListTable.currentRow()
        self.posList.delete_position(i_sel)
        self.update_plane()
        self.fill_table()

    def get_xyz(self):
        x,y = self.imgSrc.get_xy()
        z = self.imgSrc.get_z()

        return x,y,z

    def mark_new(self):
        x,y,z = self.get_xyz()

        self.posList.add_position(x=x,y=y,z=z,edgecolor='m')
        self.update_plane()
        self.fill_table()

    def select_row(self):
        #print "hello"
        i_sel=self.positionListTable.currentRow()
        N=self.positionListTable.rowCount()

        for i in range(N):
            if i == i_sel:
                color = QtCore.Qt.lightGray
            else:
                color = QtCore.Qt.white
            for j in range(3):
                self.positionListTable.item(i,j).setBackground(color)

    def closeEvent(self,evt=None):
        print "closing"
        self.cursor_timer.cancel()
        

    def update_current_pos(self):
        x,y,z = self.get_xyz()
        self.fill_row(x,y,z,0,table=self.currentPositionTable)
        self.cursor_timer = threading.Timer(.5, self.update_current_pos)
        self.cursor_timer.start()

    def fill_table(self):
        (xx,yy,zz)=self.posList.getXYZ()
        N=len(xx)
        self.positionListTable.clear()
        self.positionListTable.setRowCount(N)
        self.positionListTable.setColumnCount(3)
        self.positionListTable.setHorizontalHeaderLabels(["X", "Y","Z"])

        for i in range(N):
            self.fill_row(xx[i],yy[i],zz[i],i,self.positionListTable)

        self.positionListTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.positionListTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.positionListTable.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)

    def fill_row(self,x,y,z,row,table):
        self.add_name_item(str(x),row=row,table=table,col=0)
        self.add_name_item(str(y),row=row,table=table,col=1)
        self.add_name_item(str(z),row=row,table=table,col=2)

    def add_name_item(self,text,row,table,isReadOnly=True,col=0,greyBack = False):
        NameItem = QtGui.QTableWidgetItem(text)
        if isReadOnly:
            NameItem.setFlags(QtCore.Qt.ItemIsEnabled)
        if greyBack:
            NameItem.setBackground(QtCore.Qt.lightGray)
        table.setItem(row, col, NameItem) 
        return NameItem

    def handle_open_dialog(self):
        if self._dialog is None:
            self._dialog = QtGui.QDialog(self)
            self._dialog.resize(200, 100)
        self._dialog.show()

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)

    defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    configFile = QtGui.QFileDialog.getOpenFileName(
        None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    configFile = str(configFile.replace("/", "\\"))
    print configFile

    imgSrc = imageSource(configFile)
    plist = PositionList(None)
    
    win = FocusCorrectionPlaneWindow(plist,imgSrc)
    win.show()
    app.exec_()
    imgSrc.shutdown()
    sys.exit()