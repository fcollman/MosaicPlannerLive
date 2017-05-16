from PyQt4 import Qt,QtGui,uic

import os
import sys
import SQLModels
from SQLModels import Volume,Ribbon,Block
from alchemical_model import AlchemicalTableModel


class SelectModelFromQueryForm(QtGui.QDialog):
    def __init__(self,session,query_model,Model,ModelDialog,layoutfile):
        super(SelectModelFromQueryForm,self).__init__()
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,layoutfile)
        uic.loadUi(filename,self)
        self.theTableView.setModel(query_model)
        self.theTableView.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
        self.query_model = query_model
        self.session = session
        self.select_button.clicked.connect(self.selectModel)
        self.new_button.clicked.connect(self.newModel)
        self.model = None
        self.Model = Model
        self.ModelDialog = ModelDialog

    def selectModel(self,evt):
        index=self.theTableView.selectedIndexes()
        if len(index)>0:
            print index[0].row()
            self.model=self.query_model.results[index[0].row()]
            self.close()

    def initialModel(self):
        return self.Model()

    def newModel(self):
        mod = self.initialModel()
        moddlg = self.ModelDialog(mod)
        moddlg.exec_()
        if not moddlg.cancelled:
            self.model = moddlg.getModel()
            self.close()
        moddlg.destroy()

    def closeEvent(self, event):
        super(SelectModelFromQueryForm,self).closeEvent(event)
        #self.session.close()

    def getModel(self):
        return self.model

class RibbonForm(SelectModelFromQueryForm):

    def __init__(self,session,experiment,layoutfile='RibbonQueryForm.ui'):

        self.session = session
        self.experiment = experiment
        rib_query = self.session.query(Ribbon).filter(Ribbon.experiment_id==experiment.id)
        self.query_model = AlchemicalTableModel(self.session,rib_query,
                                           [('id',Ribbon.id,'id',{'editable':False}),
                                            ('order',Ribbon.order,'order',{'editable':False}),
                                            ('modified',Ribbon.modified,'modified',{'editable':False,'dateformat':'%c'}),
                                            ('created',Ribbon.created,'created',{'editable':False,'dateformat':'%c'}),
                                            ('sections',Ribbon.sections,'sections',{'editable':False,'show_count':True}),
                                            ('imagingsessions',Ribbon.imagingsessions,'imagingsessions',{'editable':False,'show_count':True})]
                                           )
        super(RibbonForm,self).__init__(self.session,self.query_model,Ribbon,EditRibbonDialog,layoutfile)

    def initialModel(self):

        return Ribbon()


class ExperimentForm(SelectModelFromQueryForm):

    def __init__(self,session,layoutfile = 'ExperimentForm.ui'):
        #QtGui.QWidget.__init__(self)

        self.session = session
        exp_query = self.session.query(Volume)
        self.query_model = AlchemicalTableModel(self.session,exp_query,
                                           [('id',Volume.id,'id',{'editable':False}),
                                            ('name',Volume.name,'name',{'editable':False}),
                                            ('modified',Volume.modified,'modified',{'editable':False,'dateformat':'%c'}),
                                            ('created',Volume.created,'created',{'editable':False,'dateformat':'%c'}),
                                            ('ribbons',Volume.ribbons,'ribbons',{'editable':False,'show_count':True})]
                                           )
        super(ExperimentForm,self).__init__(session,self.query_model,Volume,EditExperimentDialog,layoutfile)

class BlockForm(SelectModelFromQueryForm):

    def __init__(self,session,layoutfile = 'ExperimentForm.ui'):
        #QtGui.QWidget.__init__(self)

        self.session = session
        block_query = self.session.query(Block)
        self.block_model = AlchemicalTableModel(self.session,block_query,
                                           [('id',Block.id,'id',{'editable':False}),
                                            ('label',Block.label,'label',{'editable':False}),
                                            ('modified',Block.modified,'modified',{'editable':False,'dateformat':'%c'}),
                                            ('created',Block.created,'created',{'editable':False,'dateformat':'%c'}),
                                            ('ribbons',Block.ribbons,'ribbons',{'editable':False,'show_count':True})]
                                           )
        super(ExperimentForm,self).__init__(session,self.block_model,Block,EditExperimentDialog,layoutfile)



class EditModelDialog(QtGui.QDialog):
    def __init__(self,model,layoutfile):

        super(EditModelDialog,self).__init__()
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,layoutfile)
        uic.loadUi(filename,self)

        self.OK_pushButton.clicked.connect(self.editModel)
        self.OK_pushButton.clicked.connect(lambda: self.myClose(False))
        self.cancel_pushButton.clicked.connect(lambda: self.myClose(True))
        self.cancelled = True
        self.model = model

    def myClose(self,cancelled=True):
        self.cancelled = cancelled
        self.close()

    #def cancelModel(self,evt):
    #    self.cancelled = True
    #    self.close()
    def getModel(self):
        return self.model

    def editModel(self,evt):
        pass


class EditRibbonDialog(EditModelDialog):
    def __init__(self,ribbon,layoutfile='RibbonModelForm.ui'):
        EditModelDialog.__init__(self,ribbon,layoutfile)

        if ribbon.experiment is not None:
            self.experiment_Label.setText(ribbon.experiment.name)
        if ribbon.order is not None:
            self.order_spinBox.setValue(ribbon.order)
        if ribbon.notes is not None:
            self.notes_textEdit.setText(ribbon.notes)

    def editModel(self,evt):
        order = self.order_spinBox.value()
        notes = self.notes_textEdit.toPlainText()
        self.model.order = order
        self.model.notes = notes


class EditExperimentDialog(EditModelDialog):
    def __init__(self,experiment,layoutfile = 'ExperimentModelForm.ui'):
        EditModelDialog.__init__(self,experiment,layoutfile)
        if experiment.name is not None:
            self.name_textEdit.setPlainText(experiment.name)
        if experiment.notes is not None:
            self.notes_textEdit.setPlainText(experiment.notes)

    def editModel(self,evt):
        name = self.name_textEdit.toPlainText()
        notes = self.notes_textEdit.toPlainText()
        self.model.name = name
        self.model.notes = notes

class EditBlockDialog(EditModelDialog):
    def __init__(self, block, layoutfile='BlockModelForm.ui'):
        EditModelDialog.__init__(self, experiment, layoutfile)
        if block.name is not None:
            self.name_textEdit.setPlainText(experiment.name)
        if block.notes is not None:
            self.notes_textEdit.setPlainText(experiment.notes)

    def editModel(self, evt):
        label = self.label_textEdit.toPlainText()
        #notes = self.notes_textEdit.toPlainText()
        self.model.label = label
        #self.model.notes = notes

if __name__ == "__main__":

    SETTINGS_FILE = 'MosaicPlannerSettings.cfg'
    from configobj import ConfigObj
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    app = QtGui.QApplication(sys.argv) #opens window
    cfg = ConfigObj(SETTINGS_FILE,unrepr=True)
    #sql_engine = create_engine(cfg['SqlAlchemy']['database_path'])
    sql_engine = create_engine(cfg['SqlAlchemy']['database_path'])

    SQLModels.Base.metadata.create_all(sql_engine)

    Session = sessionmaker(bind=sql_engine)

    mysess = Session()

    block = Block(label ="test",status=0)
    vol1 = Volume(name="testme",status=0)
    mysess.add(vol1)
    vol1 = Volume(name="testme2",status=0)
    mysess.add(vol1)

    ribb1 = Ribbon(order=0)
    vol1.ribbons.append(ribb1)
    mysess.add(ribb1)
    mysess.commit()
    mysess = Session()
    vol1 = Volume(name="testme",status=0)
    mysess.add(vol1)
    vol1 = Volume(name="testme2",status=0)
    mysess.add(vol1)

    ribb1 = Ribbon(order=0)
    vol1.ribbons.append(ribb1)

    mysess.add(ribb1)

    for i in range(20):
        exp = Volume(name="exp%d"%i,status=1)
        mysess.add(exp)



    print type(ribb1.created)
    dlg = ExperimentForm(mysess)
    dlg.exec_()
    experiment = dlg.getModel()
    dlg.destroy()

    dlg = RibbonForm(mysess,experiment)
    dlg.exec_()
    ribbon = dlg.getModel()
    dlg.destroy()
    #
    # print experiment
    # print ribbon

    mysess.close()
    app.exec_()
    sys.exit()


