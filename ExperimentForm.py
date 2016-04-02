from PyQt4 import Qt,QtGui,uic

import os
import sys
import SQLModels
from SQLModels import Experiment,Ribbon
from alchemical_model import AlchemicalTableModel


class SelectModelFromQueryForm(QtGui.QDialog):
    def __init__(self,session,query_model,Model,EditModelDialog,layoutfile):
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

    def selectModel(self,evt):
        index=self.theTableView.selectedIndexes()
        if len(index)>0:
            print index[0].row()
            self.model=self.query_model.results[index[0].row()]
            self.close()

    def initialModel(self):
        mod = self.Model()

    def newModel(self):
        mod = self.initialModel()
        moddlg = EditModelDialog(mod)
        moddlg.exec_()
        if not moddlg.cancelled:
            self.model = moddlg.getModel()
            self.close()
        moddlg.destroy()

    def closeEvent(self, event):
        super(SelectModelFromQueryForm,self).closeEvent(event)
        self.session.close()

    def getModel(self):
        return self.model

class RibbonForm(QtGui.QDialog):

    def __init__(self,Session,experiment,layoutfile='RibbonQueryForm.ui'):

        self.session = Session()
        self.experiment = experiment
        rib_query = self.session.query(Ribbon).filter(Ribbon.experiment_id==experiment.id)
        self.query_model = AlchemicalTableModel(self.session,rib_query,
                                           [('id',Experiment.id,'id',{'editable':False}),
                                            ('order',Experiment.name,'order',{'editable':False}),
                                            ('modified',Experiment.modified,'modified',{'editable':False,'dateformat':'%c'}),
                                            ('created',Experiment.created,'created',{'editable':False,'dateformat':'%c'}),
                                            ('sections',Experiment.sections,'sections',{'editable':False,'show_count':True}),
                                            ('imagingsessions',Experiment.imagingsessions,'imagingsessions',{'editable':False,'show_count':True})]
                                           )
        super(RibbonForm,self).__init__(self.session,self.query_model,Ribbon,EditRibbonDialog,layoutfile)

    def initialModel(self):
        return Ribbon(experiment=self.experiment)


class ExperimentForm(QtGui.QDialog):

    def __init__(self,Session,layoutfile = 'ExperimentForm.ui'):
        #QtGui.QWidget.__init__(self)



        self.session = Session()
        exp_query = self.session.query(Experiment)
        self.query_model = AlchemicalTableModel(self.session,exp_query,
                                           [('id',Experiment.id,'id',{'editable':False}),
                                            ('name',Experiment.name,'name',{'editable':False}),
                                            ('modified',Experiment.modified,'modified',{'editable':False,'dateformat':'%c'}),
                                            ('created',Experiment.created,'created',{'editable':False,'dateformat':'%c'}),
                                            ('ribbons',Experiment.ribbons,'ribbons',{'editable':False,'show_count':True})]
                                           )
        super(ExperimentForm,self).__init__(self.session,self.query_model,Experiment,EditExperimentDialog,layoutfile)


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
        super(EditRibbonDialog,self).__init__(ribbon,layoutfile)

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
        super(EditExperimentDialog,self).__init__(experiment,layoutfile)
        if experiment.name is not None:
            self.name_textEdit.setPlainText(experiment.name)
        if experiment.notes is not None:
            self.notes_textEdit.setPlainText(experiment.notes)

    def editModel(self,evt):
        name = self.name_textEdit.toPlainText()
        notes = self.notes_textEdit.toPlainText()
        self.model.name = name
        self.model.notes = notes


if __name__ == "__main__":


    from MosaicPlanner import SETTINGS_FILE
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

    exp1 = Experiment(name="testme",status=0)
    mysess.add(exp1)
    exp1 = Experiment(name="testme2",status=0)
    mysess.add(exp1)

    ribb1 = Ribbon(order=0,experiment=exp1)
    mysess.add(ribb1)
    mysess.commit()
    mysess = Session()
    exp1 = Experiment(name="testme",status=0)
    mysess.add(exp1)
    exp1 = Experiment(name="testme2",status=0)
    mysess.add(exp1)

    ribb1 = Ribbon(order=0,experiment=exp1)
    mysess.add(ribb1)

    for i in range(20):
        exp = Experiment(name="exp%d"%i,status=1)
        mysess.add(exp)

    mysess.commit()

    print type(ribb1.created)
    dlg = ExperimentForm(Session)
    dlg.exec_()
    experiment = dlg.getValues()
    dlg.destroy()

    print experiment
    app.exec_()
    sys.exit()


