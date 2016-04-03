#!/usr/bin/env python2
# -*- coding=utf-8 -*-
# © 2013 Mark Harviston, BSD License
from __future__ import absolute_import, unicode_literals, print_function

"""
Qt data models that bind to SQLAlchemy queries
"""
from PyQt4 import QtGui
from PyQt4.QtCore import QAbstractTableModel, QVariant, Qt
import logging  # noqa

# class AlchemicalModifyModelTable(QAbstractTableModel):
#     # """
#     # A Qt Table Model that binds to a SQL Alchemy query
#     #
#     # Example:
#     # >>> model = AlchemicalTableModel(Session, [('Name', Entity.name)])
#     # >>> table = QTableView(parent)
#     # >>> table.setModel(model)
#     # """
#
#     def __init__(self, model,fields):
#         super(AlchemicalModifyModelTable, self).__init__()
#         # TODO self.sort_data = None
#         self.model = model
#         self.fields = fields
#         self.count = None
#         self.refresh()
#
#     def headerData(self, col, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             if col == 0:
#                 return QVariant("name")
#             if col == 1:
#                 return QVariant("value")
#             if col == 2:
#                 return QVariant("type")
#
#             #return QVariant(self.fields[col][0])
#         return QVariant()
#
#     def refresh(self):
#         """Recalculates, self.results and self.count"""
#
#         self.layoutAboutToBeChanged.emit()
#
#         # q = self.query
#         # if self.sort is not None:
#         #     order, col = self.sort
#         #     col = self.fields[col][1]
#         #     if order == Qt.DescendingOrder:
#         #         col = col.desc()
#         # else:
#         #     col = None
#         #
#         # if self.filter is not None:
#         #     q = q.filter(self.filter)
#         #
#         # q = q.order_by(col)
#         # if self.slice is not None:
#         #     q = q.slice(self.slice[0],self.slice[1])
#         # self.results = q.all()
#         # self.count = q.count()
#         self.layoutChanged.emit()
#
#     def flags(self, index):
#         _flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
#
#         # if self.sort is not None:
#         #     order, col = self.sort
#         #
#         #     if self.fields[col][3].get('dnd', False) and index.column() == col:
#         #         _flags |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
#
#         if index.column()==0:
#             _flags |= Qt.ItemIsEditable
#
#         # if self.fields[index.column()][3].get('editable', False):
#         #     _flags |= Qt.ItemIsEditable
#
#         return _flags
#
#     def supportedDropActions(self):
#         return Qt.MoveAction
#
#     def dropMimeData(self, data, action, row, col, parent):
#         if action != Qt.MoveAction:
#             return
#
#         return False
#
#     def rowCount(self, parent):
#         return len(self.fields)
#
#     def columnCount(self, parent):
#         return 3
#
#     def data(self, index, role):
#         if not index.isValid():
#             return QVariant()
#
#         elif role not in (Qt.DisplayRole, Qt.EditRole):
#             return QVariant()
#         name = self.fields[index.row()][2]
#         display_name = self.fields[index.row()][0]
#         if index.column()==2:
#             return unicode(type(getattr(self.model,name)))
#         if index.column()==1:
#             return unicode(getattr(self.model,name))
#         if index.column()==0:
#             return display_name
#         # row = self.results[index.row()]
#         # name = self.fields[index.column()][2]
#         # if self.fields[index.column()][3].get('show_count', False):
#         #     return unicode(len(getattr(row,name)))
#         # else:
#         #     return unicode(getattr(row, name))
#
#     def setData(self, index, value, role=None):
#         name = self.fields[index.row()][2]
#         setattr(self.model,name,value.toString())
#
#         try:
#             setattr(self.model, name, value.toString())
#         except Exception as ex:
#             QtGui.QMessageBox.critical(None, 'SQL Error', unicode(ex))
#             return False
#         else:
#             self.dataChanged.emit(index, index)
#             return True
#
#     def sort(self, col, order):
#         """Sort table by given column number."""
#         self.sort = order, col
#         self.refresh()


class AlchemicalTableModel(QAbstractTableModel):
    # """
    # A Qt Table Model that binds to a SQL Alchemy query
    #
    # Example:
    # >>> model = AlchemicalTableModel(Session, [('Name', Entity.name)])
    # >>> table = QTableView(parent)
    # >>> table.setModel(model)
    # """

    def __init__(self, session, query, columns):
        super(AlchemicalTableModel, self).__init__()
        # TODO self.sort_data = None
        self.session = session
        self.fields = columns
        self.query = query

        self.results = None
        self.count = None
        self.sort = None
        self.filter = None
        self.slice = None
        self.refresh()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.fields[col][0])
        return QVariant()

    def setFilter(self, filter):
        """Sets or clears the filter, clear the filter by setting to None"""
        self.filter = filter
        self.refresh()

    def setSlice(self,startstop):
        if startstop is None:
            self.slice = None
        else:
            self.slice = startstop
        self.refresh()

    def refresh(self):
        """Recalculates, self.results and self.count"""

        self.layoutAboutToBeChanged.emit()

        q = self.query
        if self.sort is not None:
            order, col = self.sort
            col = self.fields[col][1]
            if order == Qt.DescendingOrder:
                col = col.desc()
        else:
            col = None

        if self.filter is not None:
            q = q.filter(self.filter)

        q = q.order_by(col)
        if self.slice is not None:
            q = q.slice(self.slice[0],self.slice[1])
        self.results = q.all()
        self.count = q.count()
        self.layoutChanged.emit()

    def flags(self, index):
        _flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if self.sort is not None:
            order, col = self.sort

            if self.fields[col][3].get('dnd', False) and index.column() == col:
                _flags |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

        if self.fields[index.column()][3].get('editable', False):
            _flags |= Qt.ItemIsEditable

        return _flags

    def supportedDropActions(self):
        return Qt.MoveAction

    def dropMimeData(self, data, action, row, col, parent):
        if action != Qt.MoveAction:
            return

        return False

    def rowCount(self, parent):
        return self.count or 0

    def columnCount(self, parent):
        return len(self.fields)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        elif role not in (Qt.DisplayRole, Qt.EditRole):
            return QVariant()

        row = self.results[index.row()]
        name = self.fields[index.column()][2]
        options = self.fields[index.column()][3]
        thefield = getattr(row,name)

        if options.get('show_count', False):
            return unicode(len(thefield))
        elif options.get('dateformat',None) is not None:
            return unicode(thefield.strftime(options.get('dateformat')))
        else:
            return unicode(thefield)

    def setData(self, index, value, role=None):
        row = self.results[index.row()]
        name = self.fields[index.column()][2]

        try:
            setattr(row, name, value.toString())
            self.session.commit()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, 'SQL Error', unicode(ex))
            return False
        else:
            self.dataChanged.emit(index, index)
            return True

    def sort(self, col, order):
        """Sort table by given column number."""
        self.sort = order, col
        self.refresh()
