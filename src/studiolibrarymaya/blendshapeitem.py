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

from studiovendor.Qt import QtCore

from studiolibrarymaya import baseitem
from studiolibrarymaya import baseloadwidget

try:
    import mutils
    import maya.cmds
except ImportError as error:
    print(error)


__all__ = [
    "BlendshapeItem"
]


logger = logging.getLogger(__name__)


DIRNAME = os.path.dirname(__file__)
ICON_PATH = os.path.join(DIRNAME, "resource", "icons", "pose.png")


# class PoseLoadWidget(baseloadwidget.BaseLoadWidget):

#     def __init__(self, *args, **kwargs):
#         """
#         Using a custom load widget to support nicer blending.
#         """
#         super(PoseLoadWidget, self).__init__(*args, **kwargs)

#         self.ui.blendSlider.sliderMoved.connect(self.sliderMoved)
#         self.ui.blendSlider.sliderReleased.connect(self.sliderReleased)

#         self.item().blendChanged.connect(self.setSliderValue)

#     def setSliderValue(self, value):
#         """
#         Trigger when the item changes blend value.

#         :type value: int
#         """
#         self.ui.blendSlider.setValue(value)

#     def sliderReleased(self):
#         """Triggered when the user releases the slider handle."""
#         self.item().loadFromCurrentOptions(
#             blend=self.ui.blendSlider.value(),
#             refresh=False,
#             showBlendMessage=True
#         )

#     def sliderMoved(self, value):
#         """
#         Triggered when the user moves the slider handle.

#         :type value: float
#         """
#         self.item().loadFromCurrentOptions(
#             blend=value,
#             batchMode=True,
#             showBlendMessage=True
#         )

#     def accept(self):
#         """Triggered when the user clicks the apply button."""
#         self.item().loadFromCurrentOptions(clearSelection=False)


class BlendshapeItem(baseitem.BaseItem):

    Extension = ".blendshape"
    Extensions = [".blendshape"]
    MenuName = "BlendShape"
    MenuOrder = 11
    MenuIconPath = ICON_PATH
    TypeIconPath = ICON_PATH
    # PreviewWidgetClass = PoseLoadWidget

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of the pose item from the given path.

        :type path: str
        :type args: list
        :type kwargs: dict
        """
        super(BlendshapeItem, self).__init__(*args, **kwargs)

        self._options = None

        self.setBlendingEnabled(True)
        self.setTransferClass(mutils.Blendshape)
        self.setTransferBasename("blendshape.json")

    def loadValidator(self, **values):
        """
        Using the validator to change the state of the mirror option.

        :type values: dict
        :rtype: list[dict]
        """
        # Mirror check box
        # mirrorTip = "Cannot find a mirror table!"
        # mirrorTable = self.mirrorTable()
        # if mirrorTable:
        #     mirrorTip = "Using mirror table: %s" % mirrorTable.path()

        # fields = [
        #     {
        #         "name": "mirror",
        #         "toolTip": mirrorTip,
        #         "enabled": mirrorTable is not None,
        #     },
        #     {
        #         "name": "searchAndReplace",
        #         "visible": values.get("searchAndReplaceEnabled")
        #     },
        # ]

        # fields.extend(super(BlendshapeItem, self).loadValidator(**values))

        # return fields
        pass

    def switchSearchAndReplace(self):
        """
        Switch the values of the search and replace field.

        :rtype: (str, str)
        """
        values = self.currentLoadValue("searchAndReplace")
        return values[1], values[0]

    def clearSearchAndReplace(self):
        """
        Clear the search and replace field.

        :rtype: (str, str)
        """
        return '', ''

    def loadSchema(self):
        """
        Get the schema used for creating the load options.

        :rtype: list[dict]
        """
        schema = [
            {
                "name": "optionsGroup",
                "title": "Options",
                "type": "group",
            },
            {
                "name": "key",
                "type": "bool",
                "inline": True,
                "default": False,
                "persistent": True,
            },
            {
                "name": "mirror",
                "type": "bool",
                "inline": True,
                "default": False,
                "persistent": True,
            },
            {
                "name": "searchAndReplaceEnabled",
                "title": "Search and Replace",
                "type": "bool",
                "inline": True,
                "default": False,
                "persistent": True,
            },
            {
                "name": "searchAndReplace",
                "title": "",
                "type": "stringDouble",
                "default": ("", ""),
                "placeholder": ("search", "replace"),
                "persistent": True,
                "actions": [
                    {
                        "name": "Switch",
                        "callback": self.switchSearchAndReplace
                    },
                    {
                        "name": "Clear",
                        "callback": self.clearSearchAndReplace
                    },
                ]
            },
        ]

        schema.extend(super(BlendshapeItem, self).loadSchema())

        return schema

    def keyPressEvent(self, event):
        """
        Called when a key press event for the item is triggered.
        
        :type event: QtGui.QEvent
        """
        super(BlendshapeItem, self).keyPressEvent(event)

        if not event.isAutoRepeat():
            if event.key() == QtCore.Qt.Key_M:

                # Toggle the value of the mirror option
                mirror = self.currentLoadValue("mirror")
                self.emitLoadValueChanged("mirror", not mirror)

                blend = self.blendValue()

                if self.isBlending():
                    self.loadFromCurrentOptions(
                        blend=blend,
                        batchMode=True,
                        showBlendMessage=True
                    )
                else:
                    self.loadFromCurrentOptions(
                        blend=blend,
                        refresh=True,
                        batchMode=False,
                    )

    def mouseReleaseEvent(self, event):
        """
        Triggered when the mouse button is released on this item.

        :type event: QtCore.QMouseEvent
        """
        if self.isBlending():
            self.loadFromCurrentOptions(blend=self.blendValue(), refresh=False)

    def doubleClicked(self):
        """Triggered when the user double clicks the item."""
        self.loadFromCurrentOptions(clearSelection=False)

    def selectionChanged(self):
        """Triggered when the item is selected or deselected."""
        self._transferObject = None
        baseitem.BaseItem.selectionChanged(self)

    def stopBlending(self):
        """This method is called from the base class to stop blending."""
        self._options = None
        baseitem.BaseItem.stopBlending(self)

    def setBlendValue(self, value, load=True):
        """
        This method is called from the base class to set the blend amount.

        :type value: float
        :type load: bool
        """
        super(BlendshapeItem, self).setBlendValue(value)

        if load:
            self.loadFromCurrentOptions(
                blend=value,
                batchMode=True,
                showBlendMessage=True
            )

    def loadFromCurrentOptions(
        self,
        blend=100.0,
        refresh=True,
        batchMode=False,
        clearSelection=True,
        showBlendMessage=False,
    ):
        """
        Load the pose item with the current user settings from disc.

        :type blend: float
        :type refresh: bool
        :type batchMode: bool
        :type clearSelection: bool
        :type showBlendMessage: bool
        """
        if self._options is None:
            self._options = dict()
            self._options["key"] = self.currentLoadValue("key")
            # self._options['namespaces'] = self.currentLoadValue("namespaces")
            self._options['mirrorTable'] = self.mirrorTable()
            self._options['objects'] = maya.cmds.ls(selection=True) or []

        searchAndReplace = None
        if self.currentLoadValue("searchAndReplaceEnabled"):
            searchAndReplace = self.currentLoadValue("searchAndReplace")

        try:
            self.load(
                blend=blend,
                refresh=refresh,
                batchMode=batchMode,
                clearSelection=clearSelection,
                showBlendMessage=showBlendMessage,
                searchAndReplace=searchAndReplace,
                **self._options
            )
        except Exception as error:
            self.showErrorDialog("Item Error", str(error))
            raise

    def load(
        self,
        objects=None,
        namespaces=None,
        blend=100.0,
        key=False,
        attrs=None,
        mirror=None,
        refresh=True,
        batchMode=False,
        mirrorTable=None,
        clearSelection=False,
        showBlendMessage=False,
        searchAndReplace=None,
    ):
        """
        Load the pose item to the given objects or namespaces.
        
        :type objects: list[str]
        :type blend: float
        :type key: bool
        :type namespaces: list[str] or None
        :type refresh: bool
        :type attrs: list[str] or None
        :type mirror: bool or None
        :type batchMode: bool
        :type showBlendMessage: bool
        :type clearSelection: bool
        :type mirrorTable: mutils.MirrorTable
        :type searchAndReplace: (str, str) or None
        """
        logger.debug(u'Loading: {0}'.format(self.path()))

        # The mirror option can change during blending, so we always get
        # the value instead of caching it. This might make blending slower.
        if mirror is None:
            mirror = self.currentLoadValue("mirror")

        if namespaces is None:
            namespaces = self.currentLoadValue("namespaces")

        self.setBlendValue(blend, load=False)

        if showBlendMessage:
            self.showToastMessage("Blend: {0}%".format(blend))

        logger.info(u'Options: {0}'.format(namespaces))

        try:
            self.transferObject().load(
                objects=objects,
                namespaces=namespaces,
                key=key,
                blend=blend,
                attrs=attrs,
                mirror=mirror,
                refresh=refresh,
                batchMode=batchMode,
                mirrorTable=mirrorTable,
                clearSelection=clearSelection,
                searchAndReplace=searchAndReplace
            )

        except Exception:
            self.stopBlending()
            raise

        finally:
            if not batchMode:
                self.stopBlending()

        logger.debug(u'Loaded: {0}'.format(self.path()))

    def write(self, path, objects, iconPath="", **options):
        """
        Write all the given object data to the given path on disc.

        :type path: str
        :type objects: list[str]
        :type iconPath: str
        :type options: dict
        """
        super(BlendshapeItem, self).write(path, objects, iconPath, **options)

        # Save the pose to the temp location
        mutils.saveBlendshape(
            path + "/blendshape.json",
            objects,
            metadata={"description": options.get("comment", "")}
        )
        logger.debug("BlendShape Save!!")
