# Copyright 2019 by Kurt Rathjen. All Rights Reserved.
#
# This library is free software: you can redistribute it and/or modify it 
# under the terms of the GNU Lesser General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. This library is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from studiovendor.Qt import QtGui
from studiovendor.Qt import QtCore
from studiovendor.Qt import QtWidgets

import studioqt
import studiolibrary
import studiolibrary.widgets

try:
    import mutils
    import mutils.gui
    import maya.cmds
except ImportError as error:
    print(error)

__all__ = [
    "BaseLoadWidget",
]

logger = logging.getLogger(__name__)


class BaseLoadWidget(QtWidgets.QWidget):

    """Base widget for loading items."""

    def __init__(self, item, parent=None):
        """
        :type item: studiolibrarymaya.BaseItem
        :type parent: QtWidgets.QWidget or None
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.setObjectName("studioLibraryBaseLoadWidget")
        self.setWindowTitle("Load Item")

        self.loadUi()

        self._item = item
        self._iconPath = ""
        self._scriptJob = None
        self._formWidget = None
        self._infoFormWidget = None

        self.ui.titleLabel.setText(item.MenuName)
        self.ui.titleIcon.setPixmap(QtGui.QPixmap(item.TypeIconPath))

        # Create the icon group box
        groupBox = studiolibrary.widgets.GroupBoxWidget("Icon", self.ui.iconFrame)
        groupBox.setObjectName("iconGroupBoxWidget")
        groupBox.setPersistent(True)
        self.ui.iconTitleFrame.layout().addWidget(groupBox)

        # Create the thumbnail widget and set the image
        self.ui.thumbnailButton = studiolibrary.widgets.ImageSequenceWidget(self)
        self.ui.thumbnailButton.setObjectName("thumbnailButton")
        self.ui.thumbnailFrame.layout().insertWidget(0, self.ui.thumbnailButton)

        if os.path.exists(item.imageSequencePath()):
            self.ui.thumbnailButton.setPath(item.imageSequencePath())

        elif os.path.exists(item.thumbnailPath()):
            self.ui.thumbnailButton.setPath(item.thumbnailPath())

        # Create the info widget and set the info schema
        self._infoFormWidget = studiolibrary.widgets.FormWidget(self)
        self._infoFormWidget.setSchema(item.info())
        self.ui.infoFrame.layout().addWidget(self._infoFormWidget)

        # Create the load widget and set the load schema
        self._formWidget = studiolibrary.widgets.FormWidget(self)
        self._formWidget.setObjectName(item.__class__.__name__ + "Form")
        self._formWidget.setSchema(item.loadSchema())
        self._formWidget.setValidator(item.loadValidator)
        self._formWidget.validate()
        self.ui.formFrame.layout().addWidget(self._formWidget)

        try:
            self.selectionChanged()
            self.setScriptJobEnabled(True)
        except NameError as error:
            logger.exception(error)

        self.updateThumbnailSize()

        self._item.loadValueChanged.connect(self._itemValueChanged)
        self.ui.acceptButton.clicked.connect(self.accept)
        self.ui.selectionSetButton.clicked.connect(self.showSelectionSetsMenu)

    def _itemValueChanged(self, field, value):
        """
        Triggered when the a field value has changed.

        :type field: str
        :type value: object
        """
        self._formWidget.setValue(field, value)

    def loadUi(self):
        """Convenience method for loading the .ui file."""
        studioqt.loadUi(self, cls=BaseLoadWidget)

    def setCustomWidget(self, widget):
        """Convenience method for adding a custom widget when loading."""
        self.ui.customWidgetFrame.layout().addWidget(widget)

    def item(self):
        """
        Get the library item to be created.

        :rtype: studiolibrarymaya.BaseItem
        """
        return self._item

    def showSelectionSetsMenu(self):
        """Show the selection sets menu."""
        item = self.item()
        item.showSelectionSetsMenu()

    def resizeEvent(self, event):
        """
        Overriding to adjust the image size when the widget changes size.

        :type event: QtCore.QSizeEvent
        """
        self.updateThumbnailSize()

    def updateThumbnailSize(self):
        """Update the thumbnail button to the size of the widget."""
        width = self.width() - 10
        if width > 250:
            width = 250

        size = QtCore.QSize(width, width)
        self.ui.thumbnailButton.setIconSize(size)
        self.ui.thumbnailButton.setMaximumSize(size)
        self.ui.thumbnailFrame.setMaximumSize(size)

    def close(self):
        """Overriding this method to disable the script job when closed."""
        self.setScriptJobEnabled(False)

        if self._formWidget:
            self._formWidget.savePersistentValues()

        if self._infoFormWidget:
            self._infoFormWidget.savePersistentValues()

        QtWidgets.QWidget.close(self)

    def scriptJob(self):
        """
        Get the script job object used when the users selection changes.

        :rtype: mutils.ScriptJob
        """
        return self._scriptJob

    def setScriptJobEnabled(self, enabled):
        """
        Enable the script job used when the users selection changes.

        :type enabled: bool
        """
        if enabled:
            if not self._scriptJob:
                event = ['SelectionChanged', self.selectionChanged]
                self._scriptJob = mutils.ScriptJob(event=event)
        else:
            sj = self.scriptJob()
            if sj:
                sj.kill()
            self._scriptJob = None

    def selectionChanged(self):
        """Triggered when the users Maya selection has changed."""
        self._formWidget.validate()

    def accept(self):
        """Called when the user clicks the apply button."""
        self.item().loadFromCurrentOptions()
