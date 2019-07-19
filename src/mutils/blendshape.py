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
"""
#
# pose.py
import mutils

# Example 1:
# Save and load a pose from the selected objects
objects = maya.cmds.ls(selection=True)
mutils.saveBlendshape("/tmp/pose.json", objects)

mutils.loadBlendshape("/tmp/pose.json")

# Example 2:
# Create a pose object from a list of object names
pose = mutils.Blendshape.fromObjects(objects)

# Example 3:
# Create a pose object from the selected objects
objects = maya.cmds.ls(selection=True)
pose = mutils.Blendshape.fromObjects(objects)

# Example 4:
# Save the pose object to disc
path = "/tmp/pose.json"
pose.save(path)

# Example 5:
# Create a pose object from disc
path = "/tmp/pose.json"
pose = mutils.Blendshape.fromPath(path)

# Load the pose on to the objects from file
pose.load()

# Load the pose to the selected objects
objects = maya.cmds.ls(selection=True)
pose.load(objects=objects)

# Load the pose to the specified namespaces
pose.load(namespaces=["character1", "character2"])

# Load the pose to the specified objects
pose.load(objects=["Character1:Hand_L", "Character1:Finger_L"])

"""
import os
import shutil
import logging

from studiovendor.Qt import QtWidgets

import mutils
import mutils.gui

try:
    import maya.cmds
except ImportError:
    import traceback
    traceback.print_exc()


__all__ = ["Blendshape", "saveBlendshape", "loadBlendshape"]

logger = logging.getLogger(__name__)

MIN_TIME_LIMIT = -10000
MAX_TIME_LIMIT = 100000
DEFAULT_FILE_TYPE = "mayaBinary"  # "mayaAscii"
BLEND_SHAPE_TYPE = "blendShape"

# A feature flag that will be removed in the future.
FIX_SAVE_ANIM_REFERENCE_LOCKED_ERROR = True

class PasteOption:

    Insert = "insert"
    Replace = "replace"
    ReplaceAll = "replace all"
    ReplaceCompletely = "replaceCompletely"


class AnimationTransferError(Exception):
    """Base class for exceptions in this module."""
    pass


class OutOfBoundsError(AnimationTransferError):
    """Exceptions for clips or ranges that are outside the expected range"""
    pass


def validateAnimLayers():
    """
    Check if the selected animation layer can be exported.
    
    :raise: AnimationTransferError
    """
    animLayers = maya.mel.eval('$gSelectedAnimLayers=$gSelectedAnimLayers')

    # Check if more than one animation layer has been selected.
    if len(animLayers) > 1:
        msg = "More than one animation layer is selected! " \
              "Please select only one animation layer for export!"

        raise AnimationTransferError(msg)

    # Check if the selected animation layer is locked
    if len(animLayers) == 1:
        if maya.cmds.animLayer(animLayers[0], query=True, lock=True):
            msg = "Cannot export an animation layer that is locked! " \
                  "Please unlock the anim layer before exporting animation!"

            raise AnimationTransferError(msg)

def saveBlendshape(
        objects,
        path,
        time=None,
        sampleBy=1,
        fileType="",
        metadata=None,
        iconPath="",
        sequencePath="",
        bakeConnected=True
):
    """
    Convenience function for saving a pose to disc for the given objects.

    Example:
        path = "C:/example.pose"
        pose = saveBlendshape(path, metadata={'description': 'Example pose'})
        print pose.metadata()
        # {
        'user': 'Hovel', 
        'mayaVersion': '2016', 
        'description': 'Example pose'
        }

    :type path: str
    :type objects: list[str]
    :type metadata: dict or None
    :rtype: Blendshape
    """
    # Copy the icon path to the temp location
    if iconPath:
        shutil.copyfile(iconPath, path + "/thumbnail.jpg")

    # Copy the sequence path to the temp location
    if sequencePath:
        shutil.move(sequencePath, path + "/sequence")

    blendshape = mutils.Blendshape.fromObjects(objects)

    if metadata:
        blendshape.updateMetadata(metadata)

    blendshape.save(
        path,
        time=time,
        sampleBy=sampleBy,
        fileType=fileType,
        bakeConnected=bakeConnected
    )

    return blendshape


def loadBlendshape(
    path,
    spacing=1,
    objects=None,
    option=None,
    connect=False,
    namespaces=None,
    startFrame=None,
    mirrorTable=None,
    currentTime=None,
    showDialog=False,
):
    """
    Load the animations in the given order of paths with the spacing specified.

    :type paths: list[str]
    :type spacing: int
    :type connect: bool
    :type objects: list[str]
    :type namespaces: list[str]
    :type startFrame: int
    :type option: PasteOption
    :type currentTime: bool
    :type mirrorTable: bool
    :type showDialog: bool
    """
    isFirstAnim = True

    if spacing < 1:
        spacing = 1

    if option is None or option == "replace all":
        option = PasteOption.ReplaceCompletely

    if currentTime and startFrame is None:
        startFrame = int(maya.cmds.currentTime(query=True))

    if showDialog:

        msg = "Load the following animation in sequence;\n"

        for i, path in enumerate(paths):
            msg += "\n {0}. {1}".format(i, os.path.basename(path))

        msg += "\n\nPlease choose the spacing between each animation."

        spacing, accepted = QtWidgets.QInputDialog.getInt(
            None,
            "Load animation sequence",
            msg,
            spacing,
            QtWidgets.QInputDialog.NoButtons,
        )

        if not accepted:
            raise Exception("Dialog canceled!")

    for path in paths:

        anim = mutils.Blendshape.fromPath(path)

        if startFrame is None and isFirstAnim:
            startFrame = anim.startFrame()

        if option == "replaceCompletely" and not isFirstAnim:
            option = "insert"

        anim.load(
            option=option,
            objects=objects,
            connect=connect,
            startFrame=startFrame,
            namespaces=namespaces,
            currentTime=currentTime,
            mirrorTable=mirrorTable,
        )

        duration = anim.endFrame() - anim.startFrame()
        startFrame += duration + spacing
        isFirstAnim = False


class Blendshape(mutils.Animation):

    def __init__(self):
        mutils.TransferObject.__init__(self)

        self._cache = None
        self._mtime = None
        self._cacheKey = None
        self._isLoading = False
        self._selection = None
        self._mirrorTable = None
        self._autoKeyFrame = None

    def getBlendshapeParamList(self, name):
        attrs = []
        blend_shape_param_size = maya.cmds.getAttr(name + ".weight", size = True)                
        for i in range(0, blend_shape_param_size):
            # $attr_name = ($blend_shape + ".weight[" + $i + "]");
            attr_w_name = (name + ".weight[{0}]").format(i)
            alias_attr_name = maya.cmds.aliasAttr(attr_w_name, query = True);
            attrs.append(alias_attr_name)
        return attrs

    def createObjectData(self, name):
        """
        Create the object data for the given object name.
        
        :type name: str
        :rtype: dict
        """
        attrs = []
        # logger.debug(("maya.cmds.ls(name, showType = True) = {0}").format(maya.cmds.ls(name, showType = True)))
        # [u'Face', u'blendShape']
        name_type_list = maya.cmds.ls(name, showType = True)
        if name_type_list[1] == BLEND_SHAPE_TYPE:
            attrs = self.getBlendshapeParamList(name)
        else:
            attrs = maya.cmds.listAttr(name, keyable = True) or []        
            attrs = list(set(attrs))
        attrs = [mutils.Attribute(name, attr) for attr in attrs]

        data = {"attrs": self.attrs(name)}

        for attr in attrs:
            if attr.isValid():
                if attr.value() is None:
                    msg = "Cannot save the attribute %s with value None."
                    logger.warning(msg, attr.fullname())
                else:
                    data["attrs"][attr.attr()] = {
                        "type": attr.type(),
                        "value": attr.value()
                    }

        return data

    @mutils.timing
    @mutils.unifyUndo
    @mutils.showWaitCursor
    @mutils.restoreSelection
    def save(
        self,
        path,
        time=None,
        sampleBy=1,
        fileType="",
        bakeConnected=True
    ):
        """
        Save all animation data from the objects set on the Anim object.

        :type path: str
        :type time: (int, int) or None
        :type sampleBy: int
        :type fileType: str
        :type bakeConnected: bool
        
        :rtype: None
        """
        objects = self.objects().keys()
        logger.debug(("objects = {0}").format(objects))

        fileType = fileType or DEFAULT_FILE_TYPE

        if not time:
            time = mutils.selectedObjectsFrameRange(objects)
        start, end = time

        # Check selected animation layers
        validateAnimLayers()

        # Check frame range
        if start is None or end is None:
            msg = "Please specify a start and end frame!"
            raise AnimationTransferError(msg)

        if start >= end:
            msg = "The start frame cannot be greater than or equal to the end frame!"
            raise AnimationTransferError(msg)

        # Check if animation exists
        if mutils.getDurationFromNodes(objects or []) <= 0:
            msg = "No animation was found on the specified object/s! " \
                  "Please create a pose instead!"
            raise AnimationTransferError(msg)

        self.setMetadata("endFrame", end)
        self.setMetadata("startFrame", start)

        end += 1
        validCurves = []
        deleteObjects = []

        msg = u"Animation.save(path={0}, time={1}, bakeConnections={2}, sampleBy={3})"
        msg = msg.format(path, str(time), str(bakeConnected), str(sampleBy))
        logger.debug(msg)

        try:
            if bakeConnected:
                maya.cmds.undoInfo(openChunk=True)
                mutils.bakeConnected(objects, time=(start, end), sampleBy=sampleBy)

            for name in objects:
                if maya.cmds.copyKey(name, time=(start, end), includeUpperBound=False, option="keys"):

                    logger.debug(name)
                    # Might return more than one object when duplicating shapes or blendshapes
                    transform = maya.cmds.duplicate(name, name="CURVE", parentOnly=True)

                    if not FIX_SAVE_ANIM_REFERENCE_LOCKED_ERROR:
                        mutils.disconnectAll(transform[0])

                    deleteObjects.append(transform[0])
                    maya.cmds.pasteKey(transform[0])

                    attrs = []
                    name_type_list = maya.cmds.ls(transform[0], showType = True)
                    if name_type_list[1] == BLEND_SHAPE_TYPE:
                        attrs = self.getBlendshapeParamList(transform[0])
                    else:
                        attrs = maya.cmds.listAttr(transform[0], unlocked=True, keyable=True) or []
                    attrs = list(set(attrs) - set(['translate', 'rotate', 'scale']))

                    logger.debug(("attrs = {0}").format(attrs))
                    for attr in attrs:
                        logger.debug(("transform name = {0}, attr name = {1}").format(transform[0], attr))
                        dstAttr = mutils.Attribute(transform[0], attr)
                        dstCurve = dstAttr.animCurve()

                        if dstCurve:

                            dstCurve = maya.cmds.rename(dstCurve, "CURVE")
                            deleteObjects.append(dstCurve)

                            srcAttr = mutils.Attribute(name, attr)
                            srcCurve = srcAttr.animCurve()

                            if srcCurve:
                                preInfinity = maya.cmds.getAttr(srcCurve + ".preInfinity")
                                postInfinity = maya.cmds.getAttr(srcCurve + ".postInfinity")
                                curveColor = maya.cmds.getAttr(srcCurve + ".curveColor")
                                useCurveColor = maya.cmds.getAttr(srcCurve + ".useCurveColor")

                                maya.cmds.setAttr(dstCurve + ".preInfinity", preInfinity)
                                maya.cmds.setAttr(dstCurve + ".postInfinity", postInfinity)
                                maya.cmds.setAttr(dstCurve + ".curveColor", *curveColor[0])
                                maya.cmds.setAttr(dstCurve + ".useCurveColor", useCurveColor)

                            if maya.cmds.keyframe(dstCurve, query=True, time=(start, end), keyframeCount=True):
                                self.setAnimCurve(name, attr, dstCurve)
                                maya.cmds.cutKey(dstCurve, time=(MIN_TIME_LIMIT, start - 1))
                                maya.cmds.cutKey(dstCurve, time=(end + 1, MAX_TIME_LIMIT))
                                validCurves.append(dstCurve)

            fileName = "animation.ma"
            if fileType == "mayaBinary":
                fileName = "animation.mb"

            mayaPath = os.path.join(path, fileName)
            posePath = os.path.join(path, "pose.json")
            mutils.Pose.save(self, posePath)

            if validCurves:
                maya.cmds.select(validCurves)
                logger.info("Saving animation: %s" % mayaPath)
                maya.cmds.file(mayaPath, force=True, options='v=0', type=fileType, uiConfiguration=False, exportSelected=True)
                self.cleanMayaFile(mayaPath)

        finally:
            if bakeConnected:
                # HACK! Undo all baked connections. :)
                maya.cmds.undoInfo(closeChunk=True)
                maya.cmds.undo()
            elif deleteObjects:
                maya.cmds.delete(deleteObjects)

        self.setPath(path)

    def TestBlendshape(self):
        selections = maya.cmds.ls(selection=True) or []
        
        for obj in selections:
            # print maya.cmds.listHistory(obj)
            # print maya.cmds.findKeyframe(obj)
            print maya.cmds.keyframe(obj, query = True, keyframeCount = True)

            # attrs = maya.cmds.listAttr(obj, keyable = True) or []        
            # attrs = list(set(attrs))
            # print attrs
            # attrs = [mutils.Attribute(obj, attr) for attr in attrs]
            # for attr in attrs:
            #     print attr.name()

            if obj == "Face":
                blend_shape_param_size = maya.cmds.getAttr(obj + ".weight", size = True)                
                for i in range(0, blend_shape_param_size):
                    # $attr_name = ($blend_shape + ".weight[" + $i + "]");
                    attr_w_name = (obj + ".weight[{0}]").format(i)
                    alias_attr_name = maya.cmds.aliasAttr(attr_w_name, query = True);
                    print alias_attr_name

