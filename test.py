from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import getCppPointer
from shiboken2 import wrapInstance
from functools import partial

import re
import sys
import maya.OpenMayaUI as omui
import maya.cmds as mc
import os
import json

AGTools = 'AGTools_0.53'

available_color_spaces = re.compile(r'sRGB|ACEScg|raw', re.IGNORECASE)
COLOR_SPACES = cmds.colorManagementPrefs(q=True, inputSpaceNames=True)
FILTERED_COLOR_SPACES = [space for space in COLOR_SPACES if available_color_spaces.search(space)]

maya_script_dir = '{}/scripts'.format(os.environ['MAYA_APP_DIR'].split(';')[0])
agtools_dir = '{}/agtools'.format(maya_script_dir)
image_dir = '{}/images'.format(agtools_dir)


settings_dir = '{}/settings'.format(agtools_dir)


image_dir = os.path.abspath(r'T:\gz\AGTools_RP_Editions\images')

AGT_UI_SETTINGS = QtCore.QSettings('MyCompany', 'MyApp')
BANNER_IMG = os.path.join(image_dir, 'header_img_{}.png')

agt_suffix = '{}/agt_suffix.json'.format(settings_dir)


class CustomColorButton(QtWidgets.QWidget):
    
    color_changed = QtCore.Signal(QtGui.QColor)
    
    def __init__(self, color=QtCore.Qt.white, parent=None):
        super(CustomColorButton, self).__init__(parent)
        
        self.setObjectName('CustomColorButton')
        self.create_control()
        
        self.set_size(24, 24)
        self.set_color(color)
        
    def create_control(self):
        
        # 1 create thet colorSliderGrp
        window = mc.window()
        self._name = mc.colorSliderGrp()
        
        # 2 find the colorSLiderGrp widget
        color_slider_obj = omui.MQtUtil.findControl(self._name)
        if color_slider_obj:
            self._color_slider_widget = wrapInstance(int(color_slider_obj), QtWidgets.QWidget)
            
            # 3 Reparent the colorSliderGrp widget to this widget
            main_layout = QtWidgets.QVBoxLayout(self)
            main_layout.setObjectName('main_layout')
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self._color_slider_widget)
            
            # 4 Update the colorSliderGrp control name (used by Maya)
            
            self._name = omui.MQtUtil.fullName(int(color_slider_obj))
            
            
            # 5 identify/store the colorSliderGrp's child widgets (and hide if necessary)

            
            self._slider_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, 'slider')
            if self._slider_widget:
                self._slider_widget.hide()
                
            self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, 'port')
            
            mc.colorSliderGrp(self._name, e=True, changeCommand=partial(self.on_color_changed))
            
        mc.deleteUI(window, window=True)
        
    def set_size(self, height, width):
        
        self._color_slider_widget.setFixedWidth(width)
        self._color_widget.setFixedHeight(height)
    
    def set_color(self, color):
        
        color = QtGui.QColor(color)
        mc.colorSliderGrp(self._name, e=True, rgbValue=(color.redF(), color.greenF(), color.blueF()))
        self.on_color_changed()
        
    def get_color(self):
        
        color = mc.colorSliderGrp(self._color_slider_widget.objectName(), q=True, rgbValue=True)
        color = QtGui.QColor(color[0] * 255, color[1] * 255, color[2] * 255)
        return color
    
    def on_color_changed(self, *args):
        
        self.color_changed.emit(self.get_color())
        

class textBox(QtWidgets.QLineEdit):
    enter_pressed = QtCore.Signal(str)
    def keyPressEvent(self, e):
        
        super(textBox, self).keyPressEvent(e)
        if e.key() == QtCore.Qt.Key_Enter:
            self.enter_pressed.emit("Enter Key Pressed")
        elif e.key() == QtCore.Qt.Key_Return:
            self.enter_pressed.emit("Return Key Pressed")

class CustomImageWidget(QtWidgets.QWidget):
    
    def __init__(self, width, height, image_path, parent=None):
        super(CustomImageWidget, self).__init__(parent)
        self.set_size(width, height)
        self.set_image(image_path)
        self.set_backgorund_color(QtCore.Qt.black)
    
    def set_size(self, width, height):
        
        self.setFixedSize(width, height)
        
    def set_image(self, image_path):
        
        image = QtGui.QImage(image_path)
        image = image.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.pixmap = QtGui.QPixmap()
        self.pixmap.convertFromImage(image)
        
    def set_backgorund_color(self, color):
        
        self.background_color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), self.background_color)
        painter.drawPixmap(self.rect(), self.pixmap)
        

class WorkspaceControl(object):
    
    def __init__(self, name):
        self.name = name
        self.widget = None
        
    def create(self, label, widget, ui_script=None):
        
        mc.workspaceControl(self.name, label=label)
        
        if ui_script:
            mc.workspaceControl(self.name, e=True, uiScript=ui_script)
            
        self.add_widget_to_layout(widget)
        self.set_visible(True)
        
    def restore(self, widget):
        self.add_widget_to_layout(widget)
        
    def add_widget_to_layout(self, widget):
        if widget:
            self.widget = widget
            self.widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)
            
            workspace_control_ptr = int(omui.MQtUtil.findControl(self.name))
            widget_ptr = int(getCppPointer(self.widget)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(widget_ptr, workspace_control_ptr)
        
    def exists(self):
        return mc.workspaceControl(self.name, q=True, exists=True)
        
    def is_visible(self):
        return mc.workspaceControl(self.name, q=True, vis=True)
        
    def set_visible(self, visible):
        if visible:
            mc.workspaceControl(self.name, e=True, restore=True)
        else:
            mc.workspaceControl(self.name, e=True, visible=False)
            
    def set_label(self, label):
        mc.workspaceControl(self.name, e=True, label=label)
        
    def is_floating(self):
        return mc.workspaceControl(self.name, q=True, floating=True)
        
    def is_collapsed(self):
        return mc.workspaceControl(self.name, q=True, collapse=True)
        

#MayaQWidgetDockableMixin

class MyLineEdit(QtWidgets.QLineEdit):
    
    enter_pressed = QtCore.Signal()
    
    def keyPressEvent(self, e):
        super(MyLineEdit, self).keyPressEvent(e)
        
        if e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return:
            self.enter_pressed.emit()

class CustomRoundCornerButton(QtWidgets.QPushButton):
    def __init__(self, text):
        super(CustomRoundCornerButton, self).__init__(text)
        self.setStyleSheet('''
            QPushButton {background-color: #5d5d5d; border-radius: 2px; padding: 5px;}
            QPushButton:hover {background-color: #707070;color: white;}
            QPushButton:pressed {background-color: #1d1d1d;color: white;}
            '''
            )

class AGTools(QtWidgets.QWidget):
        
    WINDOW_TITLE = 'AGTools RP Editions'
    UI_NAME = 'AGToolsUI'
    
    ui_instance = None
    AGtoolsWindows = None

    @classmethod
    def display(cls):
        print(cls.ui_instance)
        
        if cls.ui_instance:
            print('yo')
            cls.ui_instance.show_workspace_control()
        else:
            print('agt')
            
            cls.ui_instance = AGTools() #
    
    @classmethod
    def get_workspace_control_name(cls):
        return '{0}WorkspaceControl'.format(cls.UI_NAME) 

    
    def __init__(self):
        super(AGTools, self).__init__()
        
        self.setObjectName(self.__class__.UI_NAME)
              
        self.setWindowTitle('AGTools RP Editions')
        self.setMinimumSize(400, 520)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.installEventFilter(self)
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_workspace_control()
        
        self.renderer_node_switch()
        self.job_update_selection = mc.scriptJob(event=['SelectionChanged', 'agt_ui.rename_refresh_items()'], parent=self.__class__.UI_NAME)
        self.rename_refresh_items()
        self.set_user_data()
        print('job_num')
        print(self.job_update_selection)
        
    def create_widgets(self):
        
        self.menubar = QtWidgets.QMenuBar()
        
        self.menu_banner = QtWidgets.QMenu('Banner')
        self.hide_banner = self.menu_banner.addAction('Hide Banner')
        self.hide_banner.setCheckable(True)
        
        self.hide_banner.setChecked(AGT_UI_SETTINGS.value('hide_banner', False, type=bool))
        # print(AGT_UI_SETTINGS.value('banner_img', 'agao'))
        banner_items = ['RP', 'AGao', 'Doge', 'Kirby', 'Lycoris']
        self.banner_items = [self.menu_banner.addAction(banner) for banner in banner_items]

        
        self.menu_open = QtWidgets.QMenu('Settings')
        self.open_autosuffix = self.menu_open.addAction('Auto Suffix')
        
        self.menu_help = QtWidgets.QMenu('Help')
        self.help_tutorial = self.menu_help.addAction('Video Tutorial')
        self.help_manual = self.menu_help.addAction('Manual')
        self.help_about = self.menu_help.addAction('About...')
        
        self.menubar.addMenu(self.menu_banner)
        self.menubar.addMenu(self.menu_open)
        self.menubar.addMenu(self.menu_help)
        #self.model_line_01edit
        self.create_title_label()
        
        self.title_label.setHidden(AGT_UI_SETTINGS.value('hide_banner', True, type=bool))
        
        self.header_img = QtGui.QPixmap('{}\\header_img_agao.png'.format(image_dir))
        self.header_label = QtWidgets.QLabel()
        self.header_label.setPixmap(self.header_img)
        self.header_label.setScaledContents(True)
        
        self.model_line_01 = QtWidgets.QLabel()
        self.model_line_01.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.model_line_01.setLineWidth(1)
        
        self.model_line_02 = QtWidgets.QLabel()
        self.model_line_02.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.model_line_02.setLineWidth(1)
        
        self.model_vline_01 = QtWidgets.QLabel()
        self.model_vline_01.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Plain)
        self.model_vline_01.setLineWidth(1)
        
        self.model_vline_02 = QtWidgets.QLabel()
        self.model_vline_02.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Plain)
        self.model_vline_02.setLineWidth(1)
        
        # T A B S
        self.tab_model = QtWidgets.QWidget()
        self.tab_shader = QtWidgets.QWidget()
        self.tab_export = QtWidgets.QWidget()
        self.tab_rename = QtWidgets.QWidget()
        
        model_btn_size_01 = QtCore.QSize(64, 64)
        
        
        
        self.axis_inst_rb = QtWidgets.QRadioButton()
        self.axis_dupl_rb = QtWidgets.QRadioButton()
        self.axis_mirror_rb = QtWidgets.QRadioButton()
        self.axis_flip_rb = QtWidgets.QRadioButton()
        
        self.axis_x_btn = CustomRoundCornerButton('x')
        self.axis_y_btn = CustomRoundCornerButton('y')
        self.axis_z_btn = CustomRoundCornerButton('z')
        self.axis_none_btn = CustomRoundCornerButton('none')
        self.axis_auto_btn = CustomRoundCornerButton('auto')
        self.axis_radial_btn = CustomRoundCornerButton('radial')
        
        self.inst_btn = CustomRoundCornerButton('Instance')
        self.duplicate_btn = CustomRoundCornerButton('Duplicate')
        self.mirror_btn = CustomRoundCornerButton('Mirror') 
        self.flip_btn = CustomRoundCornerButton('Flip')
        
        inst_dupl_menu_dict = {
            'Y' : 'N',
            'Auto' : 'S',
            'Radial' : 'SW',
            'Z' : 'E',
            'X' : 'W',
        }
        flip_mirror_menu_dict = inst_dupl_menu_dict.copy()
        del flip_mirror_menu_dict['Radial']
        
        quick_model_btn_dict = {
            'inst' : {'btn':self.inst_btn, 'icon':'polyShareInstancesSelect', 'func':'print("{}")', 'menu':inst_dupl_menu_dict}, 
            'dupl' : {'btn':self.duplicate_btn, 'icon':'polyShareInstancesLarge', 'func':'print("{}")', 'menu':inst_dupl_menu_dict}, 
            'mirr' : {'btn':self.mirror_btn, 'icon':'polyMirrorGeometry', 'func':'print("{}")', 'menu':flip_mirror_menu_dict}, 
            'flip' : {'btn':self.flip_btn, 'icon':'polyFlip', 'func':'print("{}")', 'menu':flip_mirror_menu_dict}
            }            
            
        for btn in quick_model_btn_dict:
            btn_info = quick_model_btn_dict[btn]
            btn_info['btn'].setFixedSize(model_btn_size_01)
            btn_info['btn'].setObjectName('{}_btn'.format(btn))
            mc.popupMenu(mm=True, p=btn_info['btn'].objectName())
            for axis in btn_info['menu']:
                mc.menuItem(l=axis, rp=btn_info['menu'][axis], c=btn_info['func'].format(btn+axis), i=btn_info['icon'])
            
        #self.inst_btn.setStyleSheet()
        
        self.my_tab = QtWidgets.QTabWidget(self)
        
        # M O D E L   W I D G E T S
        self.object_rb = QtWidgets.QRadioButton('Object')
        self.world_rb = QtWidgets.QRadioButton('World')
        self.object_rb.setChecked(True)
        
        self.inst_colorize_ckb = QtWidgets.QCheckBox('Colorize Instances')
        self.inst_colorize_ckb.setChecked(True)
        self.change_checkbox_color(self.inst_colorize_ckb, 'fdca3b')
        
        self.inst_bake_btn = CustomRoundCornerButton('Instance to Ojbect')
        self.inst_bake_btn.setIcon(QtGui.QIcon(':instanceToObject.png'))
        #self.inst_bake_btn.setFixedWidth(100)
        self.inst_merge_ckb = QtWidgets.QCheckBox('Merge Verts')
        #self.inst_merge_ckb.setIcon(QtGui.QIcon(':polyMergeToCenter.png'))
        
        self.badmesh_btn = CustomRoundCornerButton('Select Bad Mesh')
        self.badmesh_btn.setIcon(QtGui.QIcon(':polyTriangulate.png'))
        
        self.hardedges_label_main = QtWidgets.QLabel('Hard Edges')
        
        self.hardeges_ckb_min = QtWidgets.QCheckBox()
        self.hardeges_ckb_min.setChecked(True)
        #self.hardeges_ckb_min.setChecked()
        self.hardedges_slider_min = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.hardedges_slider_min.setMinimum(0)
        self.hardedges_slider_min.setMaximum(360)
        self.hardedges_slider_min.setValue(30)
        
        self.hardedges_label_min = QtWidgets.QLabel('30')
        
        self.hardeges_ckb_max = QtWidgets.QCheckBox()
        self.hardedges_slider_max = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.hardedges_slider_max.setMinimum(0)
        self.hardedges_slider_max.setMaximum(360)
        self.hardedges_slider_max.setValue(360)
        self.hardedges_slider_max.setDisabled(True)
        self.hardedges_label_max = QtWidgets.QLabel('360')
        
        self.hardedges_select_btn = CustomRoundCornerButton('Select Edges')
        self.hardedges_select_btn.setIcon(QtGui.QIcon(':componentTag_edge.png'))
        self.hardedges_select_btn.setObjectName('hardedges_select_btn')
        mc.popupMenu(mm=True, p=self.hardedges_select_btn.objectName())
        mc.menuItem(l='Set Crease', rp="N", c="print('Set Crease')", i='polyCrease')
        mc.menuItem(l='Remove Crease', rp="S", c="print('Remove Crease')", i='QR_delete')
        mc.menuItem(l='Cut UV Seam', rp="SW", c="print('Cut UV Seam')", i='cutUV')
        mc.menuItem(l='Set Hard Edges', rp="W", c="print('Set Hard Edges')", i='polyHardEdge')
        mc.menuItem(l='Triple Edge', rp="E", c="print('Triple Edge')", i='polyBevel')
        #mc.menuItem(l='X', rp="W", c="print('W')")
        
        self.hardedges_select_btn.setMinimumHeight(36)
        self.hardedges_select_btn.setStyleSheet('''
            QPushButton {background-color: #5d5d5d; border-radius: 5px; padding: 5px;}
            QPushButton:hover {background-color: #707070;color: white;}
            QPushButton:pressed {background-color: #1d1d1d;color: white;}
            '''
            )
        
        #self.hardedges_select_btn.setStyleSheet('{ border : none}')
        
        self.hardedges_btn = CustomRoundCornerButton('Hard Edges')
        self.hardedges_btn.setStyleSheet('''
            QPushButton {background-color: #5d5d5d; border-radius: 5px; padding: 5px;}
            QPushButton:hover {background-color: #707070;color: white;}
            QPushButton:pressed {background-color: #1d1d1d;color: white;}
            '''
            )
        
        self.floor_btn = CustomRoundCornerButton('Move to Center')

        self.floor_btn.setIcon(QtGui.QIcon(':alignTool.png'))
        self.checker_btn = CustomRoundCornerButton('Checker Select')
        self.checker_btn.setIcon(QtGui.QIcon(':polyDuplicateedge_loop.png'))
        #self.checker_btn.setIcon(QtGui.QIcon(':polyDelEdgeVertex.png'))
        
        self.badmesh_menu = QtWidgets.QMenu()
        
        self.badmesh_menu.addAction('Non-Quad', lambda: select_bad_mesh('Non-Quad'))
        self.badmesh_menu.addAction('Non-Manifold', lambda: nonmanifold())
        self.badmesh_menu.addAction('Concave', lambda: select_bad_mesh('Concave'))
        self.badmesh_menu.addSeparator()
        self.badmesh_menu.addAction('N-Gons', lambda: select_bad_mesh('N-Gons'))
        self.badmesh_menu.addAction('Triangles', lambda: select_bad_mesh('Triangles'))
        
        self.badmesh_btn.setMenu(self.badmesh_menu)
        
        
        # S H A D E R   W I D G E T S
        self.shader_line_01 = QtWidgets.QLabel()
        self.shader_line_01.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.shader_line_01.setLineWidth(1)
        self.shader_line_02 = QtWidgets.QLabel()
        self.shader_line_02.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.shader_line_02.setLineWidth(1)
        self.shader_line_03 = QtWidgets.QLabel()
        self.shader_line_03.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.shader_line_03.setLineWidth(1)
        
        self.create_shader_folder_le = QtWidgets.QLineEdit()
        self.create_shader_folder_le.setMinimumHeight(24)
        self.select_file_path_btn = CustomRoundCornerButton('')
        self.select_file_path_btn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.select_file_path_btn.setToolTip('Select Folder')
        
        self.shader_name_ckb = QtWidgets.QCheckBox('Auto Named')
        self.shader_name_ckb.setChecked(True)
        
        self.create_shader_name_le = QtWidgets.QLineEdit()
        self.create_shader_name_le.setMinimumHeight(24)
        self.create_shader_subfolder_ckb = QtWidgets.QCheckBox('Sub Folder')
        self.create_shader_subfolder_ckb.setToolTip('Include sub folder')
        self.create_shader_assign_ckb = QtWidgets.QCheckBox('Assign')
        self.autoname_ckb = QtWidgets.QCheckBox('auto')
        self.create_shader_colorcorrect_ckb = QtWidgets.QCheckBox('Color Correct')
        self.create_shader_colorcorrect_ckb.setToolTip('Insert color correction nodes between shader and files')
        self.create_shader_renderer_cb = QtWidgets.QComboBox()
        self.create_shader_renderer_cb.setMinimumHeight(27)
        #self.create_shader_renderer_cb.setFixedWidth(72)
        self.create_shader_renderer_cb.addItems(['Maya Defualt', 'Arnold', 'V-Ray', 'Redshift'])
        self.create_shader_renderer_cb.setCurrentIndex(1)
        
        self.create_shader_colorspace_cb = QtWidgets.QComboBox()
        self.create_shader_colorspace_cb.setMinimumHeight(27)
        self.create_shader_colorspace_cb.addItems(FILTERED_COLOR_SPACES)
        
        self.create_shader_btn = CustomRoundCornerButton('Create Shader')
        self.create_shader_btn.setIcon(QtGui.QIcon(':hypershadeIcon.png'))
        
        self.color_slider = CustomColorButton()
        self.surfaceshader_btn = CustomRoundCornerButton('Surface Shader')
        self.surfaceshader_btn.setIcon(QtGui.QIcon(':render_surfaceShader.png'))
        self.surfaceshader_btn.setStyleSheet("font-size: 9px;")
        self.lambert_btn = CustomRoundCornerButton('Lambert')
        self.lambert_btn.setIcon(QtGui.QIcon(':render_lambert.png'))
        self.blinn_btn = CustomRoundCornerButton('Blinn')
        self.blinn_btn.setIcon(QtGui.QIcon(':render_blinn.png'))
        self.standardsurface_btn = CustomRoundCornerButton('Standard Surface')
        self.standardsurface_btn.setStyleSheet("font-size: 9px;")
        self.standardsurface_btn.setIcon(QtGui.QIcon(':out_standardSurface.png'))
        self.aiflat_btn = CustomRoundCornerButton('Ai Flat')
        self.aiMixShader = CustomRoundCornerButton('Ai Mix Shader')
        self.aistandardsurface_btn = CustomRoundCornerButton('Ai Standard Surface')
        
        self.create_file_btn = CustomRoundCornerButton('Create File')
        
        self.hardedges_slider_max = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.hardedges_slider_max.setMinimum(0)
        self.hardedges_slider_max.setMaximum(360)
        self.hardedges_slider_max.setValue(360)
        self.hardedges_slider_max.setEnabled(False)
        
        self.create_file_num_label = QtWidgets.QLabel('File Counts : ')
        
        
        self.create_file_num_spinbox = QtWidgets.QSpinBox()
        self.create_file_num_spinbox.setMinimum(1)
        self.create_file_num_spinbox.setMinimumWidth(48)
        self.create_file_num_spinbox.setMinimumHeight(24)
        
        self.create_file_btn.setIcon(QtGui.QIcon(':out_file.png'))
        self.create_file_udim_ckb = QtWidgets.QCheckBox('UDIM')
        self.create_file_aces_ckb = QtWidgets.QCheckBox('ACES')
        self.create_file_linkuv_ckb = QtWidgets.QCheckBox('Link Repeat UV')
        self.create_file_linkuv_ckb.setChecked(True)
        self.change_checkbox_color(self.create_file_linkuv_ckb, '31d2b1')
        self.create_file_acescg_rb = QtWidgets.QRadioButton('ACEScg')
        self.create_file_acescg_rb.setVisible(False)
        self.create_file_srgb_rb = QtWidgets.QRadioButton('sRGB')
        self.create_file_raw_rb = QtWidgets.QRadioButton('Raw')
        
        self.create_file_srgb_rb.setChecked(True)
        
        self.create_node_renderer_cb = QtWidgets.QComboBox()
        self.create_node_renderer_cb.setMinimumHeight(27)
        self.create_node_renderer_cb.addItems(['Arnold', 'Maya Default'])
        
        
        self.create_range_btn = CustomRoundCornerButton('Range')
        self.create_range_btn.setIcon(QtGui.QIcon(':out_remapValue.png'))
        self.create_cc_btn = CustomRoundCornerButton('Color Correct')
        self.create_cc_btn.setIcon(QtGui.QIcon(':out_remapColor.png'))
        
        self.color_space_menu = QtWidgets.QMenu()
        self.color_space_list = [cs for cs in FILTERED_COLOR_SPACES]
        self.color_space_btn = CustomRoundCornerButton('Color Space')
        self.color_space_btn.setIcon(QtGui.QIcon(':render_colorProfile.png'))
        
        self.color_space_action_list = [self.color_space_menu.addAction(obj) for obj in self.color_space_list]
        self.color_space_btn.setMenu(self.color_space_menu)
        
        
        self.link_repeat_btn = CustomRoundCornerButton('Link Repeat UV')
        #out_place2dTexture
        self.link_repeat_btn.setIcon(QtGui.QIcon(':out_place2dTexture.png'))
        
        self.link_break_btn = CustomRoundCornerButton('Break Linked')
        self.link_break_btn.setIcon(QtGui.QIcon(':out_place2dTexture.png'))
        
        # R E N A M E   W I D G E T S
        colorize_btn_size = 24
        
        self.rename_colorize_01_btn = CustomRoundCornerButton('')
        self.rename_colorize_label = QtWidgets.QLabel('Colorize Objects :')
        
        self.rename_colorize_01_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_01_btn.setStyleSheet("background-color: #{};".format('fd3b70'))
        self.rename_colorize_02_btn = CustomRoundCornerButton('')
        self.rename_colorize_02_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_02_btn.setStyleSheet("background-color: #{};".format('ff7e3d'))
        self.rename_colorize_03_btn = CustomRoundCornerButton('')
        self.rename_colorize_03_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_03_btn.setStyleSheet("background-color: #{};".format('fdca3b'))
        self.rename_colorize_04_btn = CustomRoundCornerButton('')
        self.rename_colorize_04_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_04_btn.setStyleSheet("background-color: #{};".format('31d2b1'))
        self.rename_colorize_05_btn = CustomRoundCornerButton('')
        self.rename_colorize_05_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_05_btn.setStyleSheet("background-color: #{};".format('3b8dfd'))
        self.rename_colorize_06_btn = CustomRoundCornerButton('')
        self.rename_colorize_06_btn.setFixedSize(colorize_btn_size,colorize_btn_size)
        self.rename_colorize_06_btn.setStyleSheet("background-color: #{};".format('e450ff'))
        
        self.rename_colorize_reset_btn = CustomRoundCornerButton('Reset')
        
        self.rename_line_01 = QtWidgets.QLabel()
        self.rename_line_01.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.rename_line_01.setLineWidth(1)
        
        self.rename_le = MyLineEdit()
        self.rename_le.setMinimumHeight(24)
        #self.rename_le.setText('fefe')
        #self.rename_le.setDisabled(True)
        self.rename_separator_cb = QtWidgets.QComboBox()
        self.rename_separator_cb.addItems(['None', '_', 'Custom'])
        self.rename_separator_cb.setCurrentIndex(1)
        self.rename_separator_cb.setMinimumHeight(27)
        self.rename_separator_cb.setFixedWidth(68)
        
        self.rename_separator_label = QtWidgets.QLabel('Separator :')
        self.rename_separator_le = QtWidgets.QLineEdit()
        self.rename_separator_le.setText('_')
        self.rename_separator_le.setMinimumHeight(24)
        self.rename_separator_le.setFixedWidth(32)
        
        self.rename_index_cb = QtWidgets.QComboBox()
        self.rename_index_cb.setMinimumHeight(27)
        self.rename_index_cb.addItems(['None', '1', '01', '001', '0001', '00001', '000001'])
        self.rename_index_cb.setCurrentIndex(3)
        
        self.rename_prefix_le = MyLineEdit()
        self.rename_prefix_le.setMinimumHeight(24)
        self.rename_suffix_le = MyLineEdit()
        self.rename_suffix_le.setMinimumHeight(24)
        self.rename_prefix_rb = QtWidgets.QRadioButton()
        self.rename_suffix_rb = QtWidgets.QRadioButton()
        
        self.rename_caps_ckb = QtWidgets.QCheckBox('CAPS')
        self.rename_autosuffix_ckb = QtWidgets.QCheckBox('Auto Suffix')
        
        self.rename_clear_ckb = QtWidgets.QCheckBox('Clear TextBox')
        self.rename_clear_ckb.setChecked(True)
        self.rename_clear_ckb.setStyleSheet("color: #{};".format('3b8dfd'))
        self.rename_selection_cb = QtWidgets.QComboBox()
        self.rename_selection_cb.setMinimumHeight(24)
        self.rename_selection_cb.addItems(['Hierarchy', 'Selected', 'Group', 'All'])
        self.rename_selection_cb.setCurrentIndex(1)
        self.is_cap_when_create = self.is_caps()
        
        self.rename_hierarchy_rb = QtWidgets.QRadioButton('Hierarchy')
        self.rename_selected_rb = QtWidgets.QRadioButton('Selected')
        self.rename_all_rb = QtWidgets.QRadioButton('All')
        self.rename_hierarchy_rb.setChecked(True)
        
        self.rename_btn = CustomRoundCornerButton('Rename')
        self.rename_btn.setIcon(QtGui.QIcon(':quickRename.png'))
        

        
        self.rename_item_object_label = QtWidgets.QLabel('Objects :')
        self.rename_item_count_label = QtWidgets.QLabel()
        self.rename_clear_btn = CustomRoundCornerButton('Clear')
        self.rename_item_preview_ckb = QtWidgets.QCheckBox('Preview')
        self.rename_item_preview_ckb.setChecked(True)
        self.change_checkbox_color(self.rename_item_preview_ckb, '3b8dfd')
        
        self.rename_item_list_tree = QtWidgets.QTreeWidget()
        self.rename_item_list_tree.setHeaderHidden(True)
        
        self.rename_item_renamedlist_tree = QtWidgets.QTreeWidget()
        self.rename_item_renamedlist_tree.setHeaderHidden(True)
        
        self.prefix_btn_label = 'Prefix List'
        if self.is_cap_when_create:
            self.prefix_btn_label = 'PREFIX List'
        self.prefix_btn = CustomRoundCornerButton(self.prefix_btn_label)
        self.prefix_menu = QtWidgets.QMenu()
        self.prefix_btn.setMenu(self.prefix_menu)
        self.suffix_label = QtWidgets.QLabel('Suffix : ')
        
        
        self.prefix_list = ['l', 'c', 'r', '', 'ft', 'bk', 'lf', 'rt']
        self.prefix_actions = []
        
        for prefix in self.prefix_list:
            self.label = prefix
            if self.is_cap_when_create:
                self.label = self.label.upper()
            if prefix:
                action = self.prefix_menu.addAction(self.label)
            else:
                action = self.prefix_menu.addSeparator()
            self.prefix_actions.append(action)
            
        self.suffix_btn_label = 'Suffix List'
        if self.is_cap_when_create:
            self.suffix_btn_label = 'Quick SUFFIX'
        self.suffix_btn = CustomRoundCornerButton(self.suffix_btn_label)
        self.suffix_menu = QtWidgets.QMenu()
        self.suffix_btn.setMenu(self.suffix_menu)
        self.suffix_list = ['auto detect', '', 'geo', 'grp', 'jnt', 'nul', 'ctr', 'mtl', 'mat', 'sg', 'loc', 'con', '', 'high', 'low', 'ignorebf', 'hp', 'lp', '', 'm', 'p', 'w', 'g', 'r', 'i', 'c']
        self.suffix_actions = []
        for suffix in self.suffix_list:
            self.label = suffix
            if self.is_cap_when_create:
                self.label = self.label.upper()
            if suffix:
                if 'auto detect' in suffix:
                    action = self.suffix_menu.addAction(self.label)
                else:
                    action = self.suffix_menu.addAction(self.label)
            else:
                action = self.suffix_menu.addSeparator()
            self.suffix_actions.append(action)

        # E X P O R T   W I D G E T S
        
        self.export_create_shader_folder_le = QtWidgets.QLineEdit()
        self.export_create_shader_folder_le.setMinimumHeight(24)
        self.export_select_file_path_btn = CustomRoundCornerButton('')
        self.export_select_file_path_btn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.export_select_file_path_btn.setToolTip('Select Folder')
        
        self.export_tex_btn = CustomRoundCornerButton('Export Selection')
        self.export_tex_btn.setIcon(QtGui.QIcon(':out_substanceOutput.png'))
        self.export_tex_btn.setMinimumHeight(54)
        self.export_mari_ckb = QtWidgets.QCheckBox('Mari')
        self.export_sp_ckb = QtWidgets.QCheckBox('Substance (Texturing)')
        self.export_spbake_ckb = QtWidgets.QCheckBox('Substance (Baking)')
        
        self.export_abc_btn = CustomRoundCornerButton('Alembic')
        
    def create_title_label(self):
        image_path = BANNER_IMG.format(AGT_UI_SETTINGS.value('banner_img', 'agao'))
        self.title_label = CustomImageWidget(400, 80, image_path)
        self.title_label.set_backgorund_color(QtGui.QColor('#fdca3b'))

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.menubar)
        
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.my_tab)
        
        # M O D E L   L A Y O U T
        model_btn_layout_01 = QtWidgets.QHBoxLayout(self)
        model_btn_layout_01.addWidget(self.inst_btn)
        model_btn_layout_01.addWidget(self.duplicate_btn)
        model_btn_layout_01.addWidget(self.mirror_btn)
        model_btn_layout_01.addWidget(self.flip_btn)
        model_btn_layout_01.setAlignment(QtCore.Qt.AlignCenter)
        model_axis_rd_btn = QtWidgets.QVBoxLayout(self)
        model_axis_rd_btn.addWidget(self.object_rb)
        model_axis_rd_btn.addWidget(self.world_rb)
        

        
        model_btn_layout_02 = QtWidgets.QHBoxLayout(self)
        model_btn_layout_02.setAlignment(QtCore.Qt.AlignCenter)
        model_btn_layout_02.addWidget(self.inst_colorize_ckb)
        model_btn_layout_02.addWidget(self.inst_merge_ckb)
        model_btn_layout_02.addWidget(self.inst_bake_btn)
        
        model_hardedges_layout_min = QtWidgets.QHBoxLayout(self)
        model_hardedges_layout_min.addWidget(self.hardeges_ckb_min)
        model_hardedges_layout_min.addWidget(self.hardedges_slider_min)
        model_hardedges_layout_min.addWidget(self.hardedges_label_min)
        
        model_hardedges_layout_max = QtWidgets.QHBoxLayout(self)
        model_hardedges_layout_max.addWidget(self.hardeges_ckb_max)
        model_hardedges_layout_max.addWidget(self.hardedges_slider_max)
        model_hardedges_layout_max.addWidget(self.hardedges_label_max)
        
        model_hardedges_HBoxlayout_01 = QtWidgets.QHBoxLayout()
        
        model_hardedges_form_layout_main = QtWidgets.QFormLayout()
        model_hardedges_form_layout_main.addRow('Min Angle', model_hardedges_layout_min)
        model_hardedges_form_layout_main.addRow('Max Angle', model_hardedges_layout_max)
        
        model_hardedges_HBoxlayout_01.addLayout(model_hardedges_form_layout_main)
        model_hardedges_HBoxlayout_01.addWidget(self.hardedges_select_btn)
        
        
        model_select_layout_01 = QtWidgets.QHBoxLayout(self)
        model_select_layout_01.addWidget(self.floor_btn)
        model_select_layout_01.addWidget(self.checker_btn)
        model_select_layout_01.addWidget(self.badmesh_btn)
        
        model_btn_layout_01.addLayout(model_axis_rd_btn)
        model_layout = QtWidgets.QVBoxLayout(self)
        model_layout.setAlignment(QtCore.Qt.AlignTop)
        model_layout.addLayout(model_btn_layout_01)
        model_layout.addLayout(model_btn_layout_02)
        model_layout.addWidget(self.model_line_01)
        model_layout.addLayout(model_hardedges_layout_min)
        model_layout.addLayout(model_hardedges_HBoxlayout_01)
        model_layout.addWidget(self.model_line_02)
        model_layout.addLayout(model_select_layout_01)
        
        # S H A D E R   L A Y O U T
        shader_layout = QtWidgets.QVBoxLayout(self)
        shader_layout.setAlignment(QtCore.Qt.AlignTop)
        
        file_path_layout = QtWidgets.QHBoxLayout()
        file_path_layout.addWidget(self.create_shader_folder_le)
        file_path_layout.addWidget(self.select_file_path_btn)
        file_path_layout.addWidget(self.create_shader_subfolder_ckb)
        
        shader_name_layout = QtWidgets.QHBoxLayout()
        shader_name_layout.addWidget(self.create_shader_name_le)
    
        
        shader_name_layout.addWidget(self.create_shader_colorcorrect_ckb)
        shader_name_layout.addWidget(self.create_shader_assign_ckb)
        
        
        shader_form_layout = QtWidgets.QFormLayout()
        shader_form_layout.addRow('Folder :', file_path_layout)
        shader_form_layout.addRow('Name :', shader_name_layout)
        
        
        shader_settings_layout = QtWidgets.QHBoxLayout()
        shader_settings_layout.addWidget(self.create_shader_renderer_cb)
        shader_settings_layout.addWidget(self.create_shader_colorspace_cb)
        shader_settings_layout.addWidget(self.create_shader_btn)
        
        shader_quick_action_layout = QtWidgets.QVBoxLayout()
        shader_quick_action_layout.setSpacing(0)
        
        shader_quick_action_layout.addWidget(self.link_repeat_btn)
        shader_quick_action_layout.addWidget(self.link_break_btn)
        shader_quick_action_layout.addWidget(self.color_space_btn)
        
        shader_create_file_layout = QtWidgets.QHBoxLayout()
        
        shader_create_file_settings_Hlayout = QtWidgets.QHBoxLayout()
        
        shader_create_file_ckb_Vlayout = QtWidgets.QVBoxLayout()
        shader_create_file_ckb_Vlayout.addWidget(self.create_file_linkuv_ckb)
        shader_create_file_ckb_Vlayout.addWidget(self.create_file_udim_ckb)
        shader_create_file_ckb_Vlayout.addWidget(self.create_file_aces_ckb)
        shader_create_file_rb_Vlayout = QtWidgets.QVBoxLayout()
        
        shader_create_file_rb_Vlayout.addWidget(self.create_file_srgb_rb)
        shader_create_file_rb_Vlayout.addWidget(self.create_file_raw_rb)
        shader_create_file_rb_Vlayout.addWidget(self.create_file_acescg_rb)
        shader_create_file_rb_Vlayout.setAlignment(QtCore.Qt.AlignTop)
        shader_create_file_count_Hlayout = QtWidgets.QHBoxLayout()
        shader_create_file_count_Hlayout.addWidget(self.create_file_num_label)
        shader_create_file_count_Hlayout.addWidget(self.create_file_num_spinbox)
        shader_create_file_count_Hlayout.addWidget(self.create_file_btn)
        shader_create_file_form_layout = QtWidgets.QFormLayout()
        
        shader_create_file_settings_Hlayout.addLayout(shader_create_file_ckb_Vlayout)
        shader_create_file_settings_Hlayout.addLayout(shader_create_file_rb_Vlayout)
        shader_create_file_form_layout.addRow('', shader_create_file_settings_Hlayout)
        
        shader_create_file_layout.addLayout(shader_create_file_form_layout)
        shader_create_file_form_layout.addRow('', shader_create_file_count_Hlayout)

        
        shader_create_node_layout = QtWidgets.QHBoxLayout()
        shader_create_node_layout.addWidget(self.create_node_renderer_cb)
        shader_create_node_layout.addWidget(self.create_range_btn)
        shader_create_node_layout.addWidget(self.create_cc_btn)
        
        color_slider_layout = QtWidgets.QHBoxLayout()
        shader_mayashader_layout = QtWidgets.QHBoxLayout()
        
        self.maya_shader_btn_grp = [self.lambert_btn, self.blinn_btn, self.surfaceshader_btn, self.standardsurface_btn]
        self.arnold_shader_btn_grp = [self.aiflat_btn, self.aiMixShader, self.aistandardsurface_btn]
        self.shader_btn_grp_list = [self.maya_shader_btn_grp, self.arnold_shader_btn_grp]
        
        for grp in self.shader_btn_grp_list:
            
            for btn in grp:
                color_slider_layout.addWidget(btn)
        
        
        
        self.shader_util_Vline_01 = QtWidgets.QLabel()
        self.shader_util_Vline_01.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Plain)
        self.shader_util_Vline_01.setLineWidth(1)

        shader_file_util_Hlayout = QtWidgets.QHBoxLayout()
        shader_file_util_Hlayout.addLayout(shader_create_file_layout)
        shader_file_util_Hlayout.addWidget(self.shader_util_Vline_01)
        shader_file_util_Hlayout.addLayout(shader_quick_action_layout)
        
        shader_layout.addLayout(shader_form_layout)
        shader_layout.addLayout(shader_settings_layout)
        shader_layout.addWidget(self.shader_line_01)
        shader_layout.addLayout(shader_file_util_Hlayout)
        shader_layout.addWidget(self.shader_line_02)
        shader_layout.addLayout(shader_create_node_layout)
        
        shader_layout.addLayout(color_slider_layout)
        shader_layout.addWidget(self.shader_line_03)
        # R E N A M E   L A Y O U T
        rename_layout = QtWidgets.QVBoxLayout()
        rename_layout.setAlignment(QtCore.Qt.AlignTop)
        
        self.rename_colorize_Hline_01 = QtWidgets.QLabel()
        self.rename_colorize_Hline_01.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        self.rename_colorize_Hline_01.setLineWidth(1)
        
        rename_colorize_layout = QtWidgets.QHBoxLayout()
        rename_colorize_layout.setSpacing(2)
        rename_colorize_layout.addWidget(self.rename_colorize_label)
        rename_colorize_layout.addWidget(self.rename_colorize_01_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_02_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_03_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_04_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_05_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_06_btn)
        rename_colorize_layout.addWidget(self.rename_colorize_reset_btn)
        
        rename_le_layout = QtWidgets.QHBoxLayout()
        rename_le_layout.addWidget(self.rename_le)
        rename_le_layout.addWidget(self.rename_index_cb)
        
        
        rename_le_form_layout = QtWidgets.QFormLayout()

        presuf_layout = QtWidgets.QHBoxLayout()
        
        prefix_layout = QtWidgets.QHBoxLayout()
        prefix_layout.addWidget(self.rename_prefix_le)
        prefix_layout.addWidget(self.prefix_btn)
        prefix_layout.addWidget(self.suffix_label)
        prefix_layout.addWidget(self.rename_suffix_le)
        prefix_layout.addWidget(self.suffix_btn)

        quickmenu_layout = QtWidgets.QVBoxLayout()
        quickmenu_layout.addWidget(self.prefix_btn)
        quickmenu_layout.addWidget(self.suffix_btn)
        presuf_layout.addLayout(quickmenu_layout)
        
        rename_options_layout = QtWidgets.QHBoxLayout()
        rename_options_layout.addWidget(self.rename_caps_ckb)
        rename_options_layout.addWidget(self.rename_clear_ckb)
        rename_options_layout.addWidget(self.rename_btn)
        rename_options_layout.setAlignment(QtCore.Qt.AlignRight)
        
        rename_btn_layout = QtWidgets.QHBoxLayout()
        rename_item_preview_cbk_layout = QtWidgets.QHBoxLayout()
        rename_item_preview_cbk_layout.addStretch()
        
        rename_item_preview_cbk_layout.addWidget(self.rename_item_preview_ckb)
        rename_item_preview_cbk_layout.addWidget(self.rename_clear_btn)
        
        
        rename_item_object_count_layout = QtWidgets.QHBoxLayout() 
        rename_item_object_count_layout.setAlignment(QtCore.Qt.AlignLeft)
        rename_item_object_count_layout.addWidget(self.rename_selection_cb)
        rename_item_object_count_layout.addWidget(self.rename_item_object_label)
        rename_item_object_count_layout.addWidget(self.rename_item_count_label)
        
        rename_item_preview_layout = QtWidgets.QHBoxLayout()

        rename_item_preview_layout.addLayout(rename_item_object_count_layout)
        rename_item_preview_layout.addLayout(rename_item_preview_cbk_layout)
        #rename_item_preview_layout.addWidget(self.rename_item_preview_ckb)
        
        
        rename_item_list_layout = QtWidgets.QHBoxLayout()
        rename_item_list_layout.addWidget(self.rename_item_list_tree)
        rename_item_list_layout.addWidget(self.rename_item_renamedlist_tree)
        #rename_btn_layout.addWidget(self.rename_btn)
        
        self.rename_separator_layout = QtWidgets.QHBoxLayout()
        
        rename_separator_le_layout = QtWidgets.QHBoxLayout()
        rename_separator_le_layout.addWidget(self.rename_separator_le)
        rename_separator_le_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        rename_separator_options_layout = QtWidgets.QHBoxLayout()
        #rename_separator_options_layout.addWidget(self.rename_caps_ckb)
        rename_separator_options_layout.addWidget(self.rename_autosuffix_ckb)
        #rename_separator_options_layout.addStretch()
        rename_separator_options_layout.setAlignment(QtCore.Qt.AlignRight)
        #self.rename_separator_layout.addStretch()
        
        self.rename_separator_layout.addWidget(self.rename_separator_label)
        self.rename_separator_layout.addLayout(rename_separator_le_layout)
        self.rename_separator_layout.addLayout(rename_separator_options_layout)
        

        rename_le_form_layout.addRow('Prefix :', prefix_layout)
        #rename_le_form_layout.addRow('Suffix :', suffix_layout)
        rename_le_form_layout.addRow('Name :', rename_le_layout)
        
        #rename_le_form_layout.addRow('Suffix :', suffix_layout)
        rename_layout.addLayout(self.rename_separator_layout)
        rename_layout.addLayout(rename_le_form_layout)
        
        rename_layout.addLayout(rename_item_preview_layout)
        rename_layout.addLayout(rename_item_list_layout)
        rename_layout.addLayout(rename_options_layout)
       
        
        rename_layout.addWidget(self.rename_colorize_Hline_01)
        rename_layout.addLayout(rename_colorize_layout)
        #rename_layout.addLayout(rename_btn_layout)
        
        
        # E X P O R T    L A Y O U T
        
        
        self.export_tab_grp = QtWidgets.QTabWidget(self)
        
        self.export_mari_tab = QtWidgets.QTabBar()
        self.export_sp_tab = QtWidgets.QTabBar()
        self.export_spbake_tab = QtWidgets.QTabBar()
        
        export_mari_main_layout = QtWidgets.QHBoxLayout()
        export_sp_main_layout = QtWidgets.QHBoxLayout()
        export_spbake_main_layout = QtWidgets.QHBoxLayout()
        
        expor_file_path_layout = QtWidgets.QHBoxLayout()
        expor_file_path_layout.addWidget(self.export_create_shader_folder_le)
        expor_file_path_layout.addWidget(self.export_select_file_path_btn)
        
     
        
        
        
        
        self.export_mari_tab.setLayout(export_mari_main_layout)
        self.export_sp_tab.setLayout(export_sp_main_layout)
        self.export_spbake_tab.setLayout(export_spbake_main_layout)
        
        self.export_tab_grp.addTab(self.export_mari_tab, 'Mari')
        self.export_tab_grp.addTab(self.export_sp_tab, 'Substance (Texturing)')
        self.export_tab_grp.addTab(self.export_spbake_tab, 'Substance (Baking)')
        
        
        
        
        
        export_layout = QtWidgets.QVBoxLayout(self)
        
        export_tex_layout = QtWidgets.QHBoxLayout(self)
        
        export_tex_Vlayout = QtWidgets.QVBoxLayout(self)
        export_tex_Vlayout.addWidget(self.export_mari_ckb)
        export_tex_Vlayout.addWidget(self.export_sp_ckb)
        export_tex_Vlayout.addWidget(self.export_spbake_ckb)
        
        export_tex_layout.addWidget(self.export_tex_btn)
        export_tex_layout.addLayout(export_tex_Vlayout)
        export_tex_layout.setAlignment(QtCore.Qt.AlignLeft)
        #export_tex_layout.addWidget(self.export_tex_btn)
        #export_layout.addLayout(expor_file_path_layout)
        export_layout.addLayout(export_tex_layout)
        export_layout.addWidget(self.export_tab_grp)
        export_layout.setAlignment(QtCore.Qt.AlignTop)
        
        
        
        self.my_tab.addTab(self.tab_model, 'Model')
        self.tab_model.setLayout(model_layout)
        #self.tab_model.setStyleSheet("background-color: #3a3a3a")
        self.my_tab.addTab(self.tab_shader, 'Shader')
        self.tab_shader.setLayout(shader_layout)
        self.my_tab.addTab(self.tab_rename, 'Rename')
        self.tab_rename.setLayout(rename_layout)
        self.my_tab.addTab(self.tab_export, 'Export')
        self.tab_export.setLayout(export_layout)
        
        #main_layout.addTab(self.test)
        
        
        
    def create_connections(self):
        

        for item in self.banner_items:
            item.triggered.connect(lambda checked=None, text=item.text().lower(): self.update_banner(text))
        
        self.hide_banner.triggered.connect(lambda: self.banner_display_toggle())
        #self.inst_btn.
        #print(self.changedValue(self.hardedges_slider_min, self.hardedges_label_min))
        self.my_tab.currentChanged.connect(lambda: self.rename_refresh_items())
        
        self.rename_colorize_01_btn.clicked.connect(lambda: colorize(0.992, 0.231, 0.439))
        self.rename_colorize_02_btn.clicked.connect(lambda: colorize(1.0, 0.494, 0.239))
        self.rename_colorize_03_btn.clicked.connect(lambda: colorize(1.531999945640564, 0.8253204822540283, 0.4320240020751953))
        self.rename_colorize_04_btn.clicked.connect(lambda: colorize(0.192, 0.824, 0.694))
        self.rename_colorize_05_btn.clicked.connect(lambda: colorize(0.231, 0.553, 0.992))
        self.rename_colorize_06_btn.clicked.connect(lambda: colorize(0.894, 0.314, 1.0))
        self.rename_colorize_reset_btn.clicked.connect(lambda: reset_color())
        self.rename_caps_ckb.clicked.connect(lambda: self.is_caps())
        
        self.rename_caps_ckb.clicked.connect(lambda: self.rename_refresh_items())
        self.rename_separator_cb.currentTextChanged.connect(lambda: self.rename_separator_cb_changed())
        self.rename_separator_le.textChanged.connect(lambda: self.rename_refresh_items())
        self.rename_selection_cb.currentTextChanged.connect(lambda: self.rename_refresh_items())
        self.rename_item_preview_ckb.toggled.connect(lambda: self.change_checkbox_color(self.rename_item_preview_ckb, '3b8dfd'))
        self.rename_item_preview_ckb.toggled.connect(lambda: self.rename_refresh_items())
        self.rename_le.enter_pressed.connect(lambda: self.rename(True))
        self.rename_le.enter_pressed.connect(lambda: self.rename_refresh_items())
        self.rename_le.textChanged.connect(lambda: self.rename_refresh_items())
        self.rename_prefix_le.enter_pressed.connect(lambda: self.rename(True))
        self.rename_prefix_le.enter_pressed.connect(lambda: self.rename_refresh_items())
        self.rename_prefix_le.textChanged.connect(lambda: self.rename_refresh_items())
        self.rename_suffix_le.enter_pressed.connect(lambda: self.rename(True))
        self.rename_suffix_le.enter_pressed.connect(lambda: self.rename_refresh_items())
        self.rename_suffix_le.textChanged.connect(lambda: self.rename_refresh_items())
        self.rename_index_cb.currentTextChanged.connect(lambda: self.rename_refresh_items())
        
        self.create_file_btn.clicked.connect(lambda: self.create_file())
        self.create_shader_btn.clicked.connect(lambda: self.create_shader())
        self.link_repeat_btn.clicked.connect(lambda: link_uv())
        self.link_break_btn.clicked.connect(lambda: break_linked_uv())
        self.rename_btn.clicked.connect(lambda: self.rename(True))
        self.inst_merge_ckb.toggled.connect(lambda: self.change_checkbox_color(self.inst_merge_ckb, 'fdca3b'))
        self.inst_colorize_ckb.toggled.connect(lambda: self.change_checkbox_color(self.inst_colorize_ckb, 'fdca3b'))
        self.inst_btn.clicked.connect(lambda: instance(colorize=self.inst_colorize_ckb.isChecked()))
        # self.inst_btn.clicked.connect(lambda: print(self.inst_colorize_ckb.isChecked()))
        self.inst_bake_btn.clicked.connect(lambda: bake_instance())

        #print
        
        #self.hardeges_ckb_max.toggled.connect(lambda: self.change_checkbox_color(self.hardeges_ckb_max, 'fdca3b'))
        #self.hardeges_ckb_min.toggled.connect(lambda: self.change_checkbox_color(self.hardeges_ckb_min, 'fdca3b'))
        
        self.hardeges_ckb_min.toggled.connect(lambda: self.enableCheck(self.hardeges_ckb_min, self.hardedges_slider_min))
        self.hardeges_ckb_max.toggled.connect(lambda: self.enableCheck(self.hardeges_ckb_max, self.hardedges_slider_max))
        self.hardedges_slider_min.valueChanged.connect(lambda: self.value_to_label(self.hardedges_slider_min, self.hardedges_label_min))
        self.hardedges_slider_max.valueChanged.connect(lambda: self.value_to_label(self.hardedges_slider_max, self.hardedges_label_max))
        
        print(int(self.hardedges_label_min.text()),  int(self.hardedges_label_max.text()))
        
        self.hardedges_select_btn.clicked.connect(lambda: select_hard_edges(
            int(self.hardedges_label_min.text()),  int(self.hardedges_label_max.text())
            ))
        
        
        for i in self.color_space_list:
            print(self.color_space_list.index(i))
        
        for action in self.color_space_action_list:
            action.triggered.connect(lambda checked=None, cs=action.text(): set_color_space(cs))
                
        self.checker_btn.clicked.connect(lambda: checker_select())
        self.floor_btn.clicked.connect(lambda: move_to_center())
        self.create_node_renderer_cb.currentTextChanged.connect(self.renderer_node_switch)
        self.create_file_aces_ckb.toggled.connect(self.aces_checked)
        
        self.create_shader_subfolder_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_shader_subfolder_ckb, '31d2b1'))
        self.create_shader_assign_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_shader_assign_ckb, '31d2b1'))
        self.create_shader_colorcorrect_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_shader_colorcorrect_ckb, '31d2b1'))
        self.create_file_linkuv_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_file_linkuv_ckb, '31d2b1'))
        self.create_file_udim_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_file_udim_ckb, '31d2b1'))
        self.create_file_aces_ckb.toggled.connect(lambda: self.change_checkbox_color(self.create_file_aces_ckb, '31d2b1'))
        self.rename_caps_ckb.toggled.connect(lambda: self.change_checkbox_color(self.rename_caps_ckb, '3b8dfd'))
        self.rename_autosuffix_ckb.toggled.connect(lambda: self.change_checkbox_color(self.rename_autosuffix_ckb, '3b8dfd'))
        self.rename_autosuffix_ckb.toggled.connect(lambda: self.rename_suffix_le.setDisabled(self.rename_autosuffix_ckb.isChecked()))
        self.rename_autosuffix_ckb.toggled.connect(lambda: self.rename_refresh_items())
        
        self.rename_clear_ckb.toggled.connect(lambda: self.change_checkbox_color(self.rename_clear_ckb, '3b8dfd'))
        
        self.export_mari_ckb.toggled.connect(lambda: self.change_checkbox_color(self.export_mari_ckb, 'fd3b70'))
        self.export_sp_ckb.toggled.connect(lambda: self.change_checkbox_color(self.export_sp_ckb, 'fd3b70'))
        self.export_spbake_ckb.toggled.connect(lambda: self.change_checkbox_color(self.export_spbake_ckb, 'fd3b70'))
        
        #self.hardedges_slider_min
        
        #self.hardedges_label_min.set
        #self.my_tab.tabBarClicked()
        self.select_file_path_btn.clicked.connect(self.show_file_select_dialog)
        #self.shader_name_ckb.toggled.connect(lambda: self.enableCheck(self.shader_name_ckb, self.create_shader_name_le))
        
        self.color_slider.color_changed.connect(self.on_color_changed)
        #self.inst_btn.clicked.connect(self.test)
        self.my_tab.currentChanged.connect(self.indexEvent)
        #self.resizeEvent('re')
        
        #self.inst_btn.
        
    def value_to_label(self, slider, label):
        value = slider.value()
        print(value)
        label.setText(str(value))
        
        
    # def eventFilter(self, sourece, evenet):
    #     if QtWidgets.QApplication.activePopupWidget() is None:
    #         if event.type() == QtCore.QEvent.MouseMove:
    #             rect = self.geometry()
    #             rect.setHeight(60)
                
    #             if rect.contains():
    #                 pass

    def indexEvent(self):
        color_dict = {
            0: '#fdca3b',
            1: '#31d2b1',
            2: '#3b8dfd',
            3: '#fd3b70',
        }

        index = self.my_tab.currentIndex()
        color = color_dict.get(index)

        if color:
            self.title_label.set_backgorund_color(QtGui.QColor(color))
            AGT_UI_SETTINGS.setValue('my_tab', index)
        
    def on_color_changed(self, new_color):
        print('new color: ({0}, {1}, {2})'.format(new_color.red(), new_color.green(), new_color.blue()))
        
    def resizeEvent(self, event):
        width, height = event.size().width(), event.size().height()
        self.title_label.set_size(width-20, width*0.2)
        
        
    def keyPressEvent(self, key_event):
        
        
        max_tab_idx = 3
        
        key = key_event.key()
        
        if key_event.modifiers() == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_1:
                self.my_tab.setCurrentIndex(0)
            if key == QtCore.Qt.Key_2:
                self.my_tab.setCurrentIndex(1)
            if key == QtCore.Qt.Key_3:
                self.my_tab.setCurrentIndex(2)
            if key == QtCore.Qt.Key_4:
                self.my_tab.setCurrentIndex(3)

        
        if key_event.modifiers() == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_Tab:
                if not self.my_tab.currentIndex() == max_tab_idx:
                    self.my_tab.setCurrentIndex(self.my_tab.currentIndex()+1)
                else:
                    self.my_tab.setCurrentIndex(0)
                    
        if key_event.modifiers() == QtCore.Qt.ShiftModifier:
            if key == QtCore.Qt.Key_Tab:
                if not self.my_tab.currentIndex() == 0:
                    self.my_tab.setCurrentIndex(self.my_tab.currentIndex()-1)
                else:
                    self.my_tab.setCurrentIndex(max_tab_idx)
    
    def show_file_select_dialog(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory')
        if folder_path:
            self.create_shader_folder_le.setText(folder_path)
            
    def textBoxName(self):
        name = self.textBox.text()
        return name
        
    def is_caps(self):
        
        caps = self.rename_caps_ckb.isChecked()
        print(caps)
        if caps:
            try:
                self.prefix_btn.setText('PREFIX List')
                self.suffix_btn.setText('SUFFIX List')
                for idx, prefix in enumerate(self.prefix_list):
                    self.prefix_list[idx] = prefix.upper()
                for idx, suffix in enumerate(self.suffix_list):
                    self.suffix_list[idx] = suffix.upper()
            except:
                pass
            self.caps = True
        else:
            try:
                self.prefix_btn.setText('Prefix List')
                self.suffix_btn.setText('Suffix List')
                for idx, prefix in enumerate(self.prefix_list):
                    self.prefix_list[idx] = prefix.lower()
                for idx, suffix in enumerate(self.suffix_list):
                    self.suffix_list[idx] = suffix.lower()
            except:
                pass
            self.caps = False
        try:
            for idx, prefix in enumerate(self.prefix_list):
                if prefix:
                    self.prefix_actions[idx].setText(prefix)
                else:
                    continue
            for idx, suffix in enumerate(self.suffix_list):
                if suffix:
                    self.suffix_actions[idx].setText(suffix)
                else:
                    continue
        except:
            pass
        return self.caps
        
    def create_workspace_control(self):
        print(self.get_workspace_control_name())
        self.workspace_control_instance = WorkspaceControl(self.get_workspace_control_name())
        if self.workspace_control_instance.exists():
            print('ex')
            self.workspace_control_instance.restore(self)
        else:
            ui_script = 'from {0} import AGTools\nAGTools.display()'.format('AGTools RP Editions')
            self.workspace_control_instance.create(self.WINDOW_TITLE, self, ui_script=ui_script)
    
    def show_workspace_control(self):
        self.workspace_control_instance.set_visible(True)
        
    def showEvent(self, e):
        if self.workspace_control_instance.is_floating():
            self.workspace_control_instance.set_label('AGTools RP Editions')
        else:
            self.workspace_control_instance.set_label('AGTools RP Editions')
            
    def enableCheck(self, ckb, widgets):
        widgets.setEnabled(ckb.isChecked())
            
    def changedValue(self, slider, label):
        slider.valueChanged()
        value = slider.value()
        label.setText(str(value))
        
    def change_checkbox_color(self, ckb, hexcode):
        
        if ckb.isChecked():
            #fdca3b, 31d2b1
            ckb.setStyleSheet("color: #{};".format(hexcode))
        if not ckb.isChecked():
            ckb.setStyleSheet("")
        
    def renderer_node_switch(self):
        renderer = self.create_node_renderer_cb.currentText()
        if renderer == 'Maya Default':
            self.create_range_btn.setText('Remap Value')
            self.create_cc_btn.setText('Remap HSV')
            for btn in self.arnold_shader_btn_grp:
                btn.setVisible(False)
            for btn in self.maya_shader_btn_grp:
                btn.setVisible(True)
        elif renderer == 'Arnold':
            self.create_range_btn.setText('Range')
            self.create_cc_btn.setText('Color Correct')
            for btn in self.arnold_shader_btn_grp:
                btn.setVisible(True)
            for btn in self.maya_shader_btn_grp:
                btn.setVisible(False)
        else:
            self.create_range_btn.setText('Remap Value')
            self.create_cc_btn.setText('Remap Hsv')
    
    def banner_display_toggle(self):
        if self.title_label.isHidden():
            self.title_label.setHidden(False)
            AGT_UI_SETTINGS.setValue('hide_banner', False)
        else:
            self.title_label.setHidden(True)
            AGT_UI_SETTINGS.setValue('hide_banner', True)
            
    def update_banner(self, banner_str):
        AGT_UI_SETTINGS.setValue('banner_img', banner_str)
        self.title_label.set_image(BANNER_IMG.format(banner_str))
        
        for _ in range(2):
            self.banner_display_toggle()
            
    def aces_checked(self):
        if self.create_file_aces_ckb.isChecked():
            self.create_file_acescg_rb.setVisible(True)
            self.create_file_srgb_rb.setText('sRGB - Texture')
            self.create_file_raw_rb.setText('Utility - Raw')
        else:
            self.create_file_acescg_rb.setVisible(False)
            self.create_file_srgb_rb.setText('sRGB')
            self.create_file_raw_rb.setText('Raw')
            
    def rename(self, rename):
        
        clear_le_list = [self.rename_le, self.rename_suffix_le, self.rename_prefix_le]
        for obj in self.selection_dict:
            mc.rename(mc.ls(obj['uid'], l=True), obj['new_name'])
            
        if self.rename_clear_ckb.isChecked():
            for le in clear_le_list:
                le.setText('')
 
        self.rename_refresh_items()
        return
        
    def create_shader(self):
        
        folder = self.create_shader_folder_le.text()
        name = self.create_shader_name_le.text()
        
        print(folder)
        print(name)
        
        print(self.create_shader_subfolder_ckb.isChecked())
        print(self.create_shader_assign_ckb.isChecked())
        print(self.create_shader_colorcorrect_ckb.isChecked())
        
        print(self.create_shader_renderer_cb.currentText())
        print(self.create_shader_colorspace_cb.currentText())
        print('create shader')
        print('')
        
    def create_file(self):
        file_colorspace = 'sRGB'
        link = self.create_file_linkuv_ckb.isChecked()
        udim = self.create_file_udim_ckb.isChecked()
        file_counts = self.create_file_num_spinbox.value()
        if self.create_file_aces_ckb.isChecked():
            print('ACES:')
            if self.create_file_acescg_rb.isChecked():
                file_colorspace = 'ACES - ACEScg'
            elif self.create_file_raw_rb.isChecked():
                file_colorspace = 'Utility - Raw'
            else:
                file_colorspace = 'Utility - sRGB - Texture'
        else:
            print('MAYA:')
            if self.create_file_srgb_rb.isChecked():
                file_colorspace = 'sRGB'
            else:
                file_colorspace = 'Raw'
        for file in range(file_counts):
            current_file = file_generator()
            mc.setAttr('{}.colorSpace'.format(current_file), file_colorspace, type='string')
            if link:
                link_uv()
            if udim:
                print(current_file)
                mc.setAttr('{}.uvTilingMode'.format(current_file), 3)
                
                
                
        print(file_colorspace)
        
        print('create file')
        print('')
        
    def test(self):
        print('test')
        
    def get_new_name(self, selection_dict, rename_setting_dict):
        invalid_characters = ' !@#$%^&*()-=+[];:\'\"<>?{}\\/,|~.*'
        zeros_padding = ''
        old_name = selection_dict['name']
        idx = selection_dict['index']
        padding_length = rename_setting_dict['padding_length']
        separator = rename_setting_dict['separator']
        prefix = rename_setting_dict['prefix']
        new_name = rename_setting_dict['new_name'] or old_name
        suffix = rename_setting_dict['suffix']
        
        if padding_length and new_name != old_name:
            zeros_padding = str(idx).zfill(padding_length)
            
        new_name_full = [prefix, new_name, zeros_padding, suffix]
        new_name_full = separator.join(filter(None, new_name_full))
        
        for char in invalid_characters:
            new_name_full = new_name_full.replace(char, '_')
        
        return new_name_full

                
    def rename_refresh_items(self):
        '''
        referesh items depends on current state
        '''
        is_preview_enabled = self.rename_item_preview_ckb.isChecked()
        current_tab_index = self.my_tab.currentIndex()
        if not is_preview_enabled or current_tab_index != 2:
            self.rename_item_list_tree.clear()
            self.rename_item_renamedlist_tree.clear()
            return
        self.selection_dict = self.rename_list_selection()
        
                
                
    def rename_list_selection(self):
        clear = self.rename_clear_ckb.isChecked()
        selection_dict = self.selection(self.rename_selection_cb.currentText().lower())
        
        rename_setting_dict = {
            'new_name' : self.rename_le.text(),
            'padding_length' : 0,
            'prefix' : self.rename_prefix_le.text(),
            'suffix' : self.rename_suffix_le.text(),
            'separator' : self.rename_separator_le.text(),
            'apply_new_name' : False,
            'auto_suffix' : self.rename_autosuffix_ckb.isChecked()
        }
        
        self.rename_item_count_label.setText(str(len(selection_dict)))
        self.rename_item_list_tree.clear()
        self.rename_item_renamedlist_tree.clear()


        padding_length_str  = self.rename_index_cb.currentText()
        if padding_length_str != 'None':
            rename_setting_dict['padding_length'] = len(padding_length_str)
        
        if selection_dict:
            for obj in selection_dict:
                item = self.rename_list_item(obj['name'])
                self.rename_item_list_tree.addTopLevelItem(item)
                obj['new_name'] = self.get_new_name(obj, rename_setting_dict)
                renamed_item = self.rename_list_item(obj['new_name'])
                self.rename_item_renamedlist_tree.addTopLevelItem(renamed_item)
        
        return selection_dict
        
    def rename_list_item(self, name):
        item = QtWidgets.QTreeWidgetItem([name])
        return item
        
    def selection(self, selection_type='selected'):
        READ_ONLY = mc.ls(['|top', '|front', '|persp', '|side'], uid=True)
        selection = []
        if selection_type == 'hierarchy':
            selection = mc.ls(mc.ls(dagObjects=True, shapes=False, sl=True, tr=True), uid=True)
        elif selection_type == 'selected':
            selection = mc.ls(sl=True, tr=True, uid=True)
        elif selection_type == 'all':
            selection = mc.ls('*', tr=True, uid=True)
        elif selection_type == 'group':
            selection = mc.ls(
                [i for obj in mc.ls(sl=True, tr=True, uid=True) 
                for i in mc.listRelatives(mc.ls(obj, l=True), c=True, f=True) 
                if mc.listRelatives(i, c=True, f=True)], 
                uid=True
                )
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Invalid selection type')
        selection_uid = [node for node in selection if node not in READ_ONLY]
        selection_dict = [
                {
                    'uid':node, 
                    'name':mc.ls(node)[0].split('|')[-1],
                    'index':idx+1,
                    'new_name':''
                }
                for idx, node in enumerate(selection_uid)
            ]
        return selection_dict
        
    def hideEvent(self, e):
        try:
            if self and self.parent():
                ui_exist = True
                workspace_control_name = self.parent().objectName()
                self.save_user_data()
                if mc.workspaceControl(workspace_control_name, q=True, exists=True):
                    
                    for child_widget in self.findChildren(QtWidgets.QWidget):
                        child_widget.deleteLater()
                    for layout in self.findChildren(QtWidgets.QLayout):
                        layout.deleteLater()
                    
                    self.deleteLater()
                    
                    mc.deleteUI(workspace_control_name)
                    mc.workspaceControl(workspace_control_name, e=True, close=True)
                del self
            else:
                ui_exist = False
        except:
            pass
        
            
    def save_user_data(self):
        mc.scriptJob(kill=self.job_update_selection, f=True)
        print('clear jobs')
        AGT_UI_SETTINGS.setValue('my_tab', self.my_tab.currentIndex())
        AGT_UI_SETTINGS.setValue('rename_selection_cb', self.rename_selection_cb.currentIndex())
        AGT_UI_SETTINGS.setValue('rename_index_cb', self.rename_index_cb.currentIndex())
     
    def set_user_data(self):
        self.my_tab.setCurrentIndex(AGT_UI_SETTINGS.value('my_tab', 0))
        self.rename_selection_cb.setCurrentIndex(AGT_UI_SETTINGS.value('rename_selection_cb', 1))
        self.rename_index_cb.setCurrentIndex(AGT_UI_SETTINGS.value('rename_index_cb', 3))
        
     
# if __name__ == "__main__":
#     ui_exist = False
#     try:
#         if agt_ui and agt_ui.parent():
#             ui_exist = True
#             workspace_control_name = agt_ui.parent().objectName()
#             if mc.workspaceControl(workspace_control_name, q=True, exists=True):
#                 mc.deleteUI(workspace_control_name)
#                 mc.workspaceControl(workspace_control_name, e=True, close=True)
#             del agt_ui
#         else:
#             ui_exist = False
#     except:
#         pass
#     if not ui_exist:
#         agt_ui = AGTools()

def display():
    global agt_ui
    ui_exist = False
    
    try:
        if agt_ui and agt_ui.parent():
            ui_exist = True
            workspace_control_name = agt_ui.parent().objectName()
            agt_ui.save_user_data()
            if mc.workspaceControl(workspace_control_name, q=True, exists=True):
                
                for child_widget in agt_ui.findChildren(QtWidgets.QWidget):
                    child_widget.deleteLater()
                for layout in agt_ui.findChildren(QtWidgets.QLayout):
                    layout.deleteLater()
                
                agt_ui.deleteLater()
                
                mc.deleteUI(workspace_control_name)
                mc.workspaceControl(workspace_control_name, e=True, close=True)
            del agt_ui
            
        else:
            ui_exist = False
    except:
        pass
    if not ui_exist:
        agt_ui = AGTools()
        
display()

def getFaceCenter(face):
    vtxList = mc.xform(face, q = True, ws = True, t = True)
    facePos = []
    pos = None
    side = int(len(vtxList)/3)
    for obj in range(3):
        round = range(3).index(obj)
        for vtx in range(side):
            vtxIndex = range(side).index(vtx)*3 + round
            if not pos:
                pos = vtxList[vtxIndex]
            else:
                pos = pos + vtxList[vtxIndex]
            if vtx == side-1:
                pos = pos / side
                facePos.append(pos)
                pos = 0
    return facePos

def getDistance(vectorA, vectorB):
    distance = sqrt(pow(vectorA[0]-vectorB[0],2)+pow(vectorA[1]-vectorB[1],2)+pow(vectorA[2]-vectorB[2],2))
    distance = float(distance)
    return distance

def autoAxis(operation = 'flip'):
    sel_obj = mc.ls(sl = True)
    if sel_obj:
        mc.undoInfo(openChunk=True)
        for obj in sel_obj:
            bBox = mc.geomToBBox(obj, ko = True, ns = '_bBox')[0]
            objPos = mc.xform(obj, q = True, ws = True ,rp = True)
            x_face_a_pos = getFaceCenter(bBox+'.f[3]')
            x_face_b_pos = getFaceCenter(bBox+'.f[5]')
            y_face_a_pos = getFaceCenter(bBox+'.f[1]')
            y_face_b_pos = getFaceCenter(bBox+'.f[0]')
            z_face_a_pos = getFaceCenter(bBox+'.f[2]')
            z_face_b_pos = getFaceCenter(bBox+'.f[4]')
            mc.delete(bBox)
            allFacePos = [x_face_a_pos, x_face_b_pos, y_face_a_pos, y_face_b_pos, z_face_a_pos, z_face_b_pos]
            all_distance = []
            for pos in allFacePos:
                all_distance.append(getDistance(objPos, pos))
            min_distance = min(all_distance)
            if min_distance == all_distance[0] or min_distance == all_distance[1]:
                axis = 'x'
            if min_distance == all_distance[2] or min_distance == all_distance[3]:
                axis = 'y'
            if min_distance == all_distance[4] or min_distance == all_distance[5]:
                axis = 'z'
            mc.select(obj)
            if operation == 'inst':
                instance_axis(axis)
            elif operation == 'dup':
                duplicate_axis(axis)
            elif operation == 'mirror':
                mirror_axis(axis)
            elif operation == 'flip':
                flip(axis)
            else:
                pass    
        mc.select(sel_obj)
        mc.undoInfo(closeChunk=True)
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
        
def normal_instance():
    sel_obj = mc.ls(sl=True)
    if sel_obj:
        for obj in sel_obj:
            inst = mc.instance(obj)
            mc.select(inst[0], add=True)
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
        

def instance_axis(axis='x'):
    mc.undoInfo(openChunk=True)
    if mc.ls(sl=True):
        sel_obj = mc.ls(sl=True)
        for obj in sel_obj:
            obj_scale_x = mc.getAttr(obj+'.scaleX')
            obj_scale_y = mc.getAttr(obj+'.scaleY')
            obj_scale_z = mc.getAttr(obj+'.scaleZ')
            instance_mesh = mc.instance(obj)
            mc.ls(sl = True)
            mc.scale(obj_scale_x, obj_scale_y, obj_scale_z, obj)
            if axis == 'x':
                mc.scale(obj_scale_x*-1, obj_scale_y, obj_scale_z, obj)
            elif axis == 'y':
                mc.scale(obj_scale_x, obj_scale_y*-1, obj_scale_z, obj)
            elif axis == 'z':
                mc.scale(obj_scale_x, obj_scale_y, obj_scale_z*-1, obj)
            else:
                continue
            mc.select(obj, add = True)
            mc.select(instance_mesh[0], add = True)
    else:
        mc.warning("nothing selected")
        
    mc.undoInfo(closeChunk=True)
    
def duplicate_axis(axis='x'):
    mc.undoInfo(openChunk=True)
    sel_obj = mc.ls(sl=True)
    if sel_obj:
        for obj in sel_obj:
            obj_scale_x = mc.getAttr(obj+'.scaleX')
            obj_scale_y = mc.getAttr(obj+'.scaleY')
            obj_scale_z = mc.getAttr(obj+'.scaleZ')
            dup = mc.duplicate(obj)
            mc.scale(obj_scale_x, obj_scale_y, obj_scale_z, obj)
            if axis == 'x':
                mc.scale(obj_scale_x*-1, obj_scale_y, obj_scale_z, obj)
            elif axis == 'y':
                mc.scale(obj_scale_x, obj_scale_y*-1, obj_scale_z, obj)
            elif axis == 'z':
                mc.scale(obj_scale_x, obj_scale_y, obj_scale_z*-1, obj)
            else:
                print('axis should be less than 3')
            mc.select(obj, add=True)
            mc.select(dup[0], add=True)
    mc.undoInfo(closeChunk=True)
        
def instance_to_object():
    mc.undoInfo(openChunk=True)
    sel_obj = mc.ls(sl=True)
    mc.pickWalk(d='down')
    def isInstanced(shape):
        return len (mc.listRelatives(shape, ap=True) or []) > 1
    for obj in sel_obj:
        mc.select(obj)
        mc.pickWalk(d='down')
        childObj = mc.ls(sl=True)
        inst = isInstanced(childObj)
        if inst == True:
            mc.select(obj)
            mc.ConvertInstanceToObject()
            print(str(obj)+' is successful converted')
        else:
            print(str(obj)+' is not an instance')
    mc.select(sel_obj)
    om.MGlobal.displayInfo("successfully converted")
    mc.undoInfo(closeChunk=True)
    
def bakeMerge():
    mc.undoInfo(openChunk=True)
    sel_obj = mc.ls(sl=True)
    if sel_obj:
        instanceToObject()
        mc.undoInfo(openChunk=True)
        new_obj = btCombine()
        mc.polyMergeVertex(d=0.0001)
        mc.select(new_obj)
        mc.undoInfo(closeChunk=True)
    
    mc.undoInfo(closeChunk=True)
    return new_obj

def btCombine():
    mc.undoInfo(openChunk=True)
    def getParent():
        sel_obj = mc.ls(sl = True, l = True)
        if sel_obj:
            fullPath = str(sel_obj[-1])
            parentPath = fullPath.split('|')
            parentPath.remove(parentPath[0])
            parentPath.remove(parentPath[-1])
            tempList = []
            for obj in parentPath:
                tempName = '|'+obj
                tempList.append(tempName)
            parent_name = "".join(tempList)
            return parent_name
        else:
            return None
        #mc.undoInfo(closeChunk=True)
    

def mirror_axis(x=0):
    mc.undoInfo(openChunk=True)
    sel_obj = mc.ls(sl=True)
    if sel_obj:
        for obj in sel_obj:
            mc.select(obj)
            mc.DeleteHistory()
            mc.polyMirrorFace(cutMesh = 0, axis=x, mirror_axis=1, mergeMode=0, mirrorPosition=0)
            mc.polyMergeVertex(d=0.0001)
            mc.polySoftEdge()   
            mc.DeleteHistory()
        om.MGlobal.displayInfo("successfully mirrored")
        mc.select(sel_obj)
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
    mc.undoInfo(closeChunk=True)
    
def flip(x=0):
    mc.undoInfo(openChunk=True)
    obj = mc.ls(sl=True)
    if mc.ls(selection=True) :
        obj_scale_x = mc.getAttr(obj[0]+'.scaleX')
        obj_scale_y = mc.getAttr(obj[0]+'.scaleY')
        obj_scale_z = mc.getAttr(obj[0]+'.scaleZ')
    if x == 0 and mc.ls(selection=True) :
        print('flip X')
        mc.scale(obj_scale_x*-1, obj_scale_y, obj_scale_z)
    elif x == 1 and mc.ls(selection=True) :
        print('flip Y')
        mc.scale(obj_scale_x, obj_scale_y*-1, obj_scale_z)     
    elif x == 2 and mc.ls(selection=True) :
        print('flip Z')
        mc.scale(obj_scale_x, obj_scale_y, obj_scale_z*-1)
    else :
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
    mc.undoInfo(closeChunk=True)


def toEdge(ep):
    sel_obj = mc.ls(sl=True, flatten = True)
    faces = mc.filterExpand(selectionMask = 34) or []
    edge_perimeter = []
    if faces and ep:
        sel_obj = list(set(sel_obj).difference(set(faces)))
        mc.select(faces)
        mel.eval('{string $c[]; string $f[]; convertToSelectionBorder(-1, true, $c, $f);}')
        edge_perimeter = mc.ls(sl = True, flatten = True) or []
    convCpnt = mc.polyListComponentConversion(sel_obj, te=True)
    mc.select(convCpnt)
    edges = mc.ls(sl = True, flatten = True)
    edges.extend(edge_perimeter)
    edges = list(set(edges))
    mc.filterExpand(edges, sm = 32)
    mc.select(edges)
    return edges

def to_obj_set_subd_level(in_mesh, subd_level, adjust_subd):
    transform = []
    shape = []
    for obj in in_mesh:
        try:
            mesh = obj.split('.')[0]
        except:
            mesh = obj
        transform.append(mesh)  
    transform = list(set(transform))
    if adjust_subd:
        for obj in transform:
            mc.setAttr(str(obj)+'.smoothLevel', subd_level)
    return transform

def creasing(creasingValue):
    sel_obj = mc.ls(sl=True)
        
    def crease(v):
        sel_edge = toEdge(True)
        mc.select(sel_edge)
        if not mc.objExists('creaseSet'):
            mc.sets(n = 'creaseSet')
            
        for edge in sel_edge:
            mc.polyCrease(edge, value=v)
        if v != 0:
            mc.sets(sel_edge, add = 'creaseSet', e = True)
            transform = to_obj_set_subd_level(sel_edge, 4, True)
        else:
            mc.sets(sel_edge, rm = 'creaseSet', e = True)
            transform = to_obj_set_subd_level(sel_edge, 2, True)
            creaseSetList = mc.sets('creaseSet', q = True) or []
            creaseSetListTransform = []
            for obj in creaseSetList:
                try:
                    mesh = obj.split('.')[0]
                except:
                    mesh = obj
                creaseSetListTransform.append(mesh)
            transform = list(set(transform).intersection(set(creaseSetListTransform)))
            if transform:
                to_obj_set_subd_level(sel_edge, 4, True)
        mc.select(transform)
        mc.DeleteHistory()
        mel.eval('setSelectMode components Components; selectType -smp 0 -sme 1 -smf 0 -smu 0 -pv 0 -pe 1 -pf 0 -puv 0; HideManipulators; ')
        mc.select(sel_edge)

    mc.undoInfo(openChunk=True)   
        
    if sel_obj:
        selType = mc.objectType(sel_obj[0])
        if selType == 'mesh' :
            crease(creasingValue)
        elif selType == 'transform' :
            mc.pickWalk(d='down')
            sel_obj = mc.ls(sl=True)
            selType = mc.objectType(sel_obj[0])
            if selType == 'mesh' :
                    crease(creasingValue)
            else :
                mc.warning("please select mesh")
        else :
            mc.warning("please select mesh")
    else :
            mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)

    mc.undoInfo(closeChunk=True)
    
def select_crease():
    if mc.objExists('creaseSet'):
        select_edges = toEdge(False)
        creased_edges = mc.sets('creaseSet', q = True)
        creased_edges = mc.ls(creased_edges, flatten = True)
        select_creased_edge = list(set(creased_edges).intersection(select_edges))
        de_select = list(set(creased_edges).difference(select_edges))
        transform = to_obj_set_subd_level(select_edges, 2, False)
        mc.select(transform)
        mel.eval('setSelectMode components Components; selectType -smp 0 -sme 1 -smf 0 -smu 0 -pv 0 -pe 1 -pf 0 -puv 0; HideManipulators; ')

        if len(transform) == 1:
            mc.select(select_creased_edge)
        else:
            mc.select(creased_edges)
            mc.select(de_select, d = True)
        return select_creased_edge

def nonmanifold():
    sel_obj = mc.ls(sl = True)
    if sel_obj:
        monmani = mc.polyInfo( nme=True, nmv=True )
        mc.selectMode(component=True)
        mc.select(monmani)
        sel_edge = mc.ls(sl=True)
        if not sel_edge :
            mc.inViewMessage(amg='<font color="#31d2b1">Your mesh is good</font><br>.', pos='topCenter', fade=True)
            mc.select(sel_obj)
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
        #mc.warning("Nothing selected") 
        
def select_bad_mesh(selType):
    # 1 nonquad, 2 concave, 3 ngons, 4 tris
    sel_obj = mc.ls(sl = True)
    if sel_obj:
        mc.selectMode(component=True)
        mc.selectType(facet=True)
        if selType == 'Non-Quad':
            mc.polySelectConstraint(mode=3, type=0x0008, size=2)
            mc.InvertSelection()
        elif selType == 'Concave':
            mc.polySelectConstraint(mode=3, type=0x0008, c=1)
        elif selType == 'N-Gons':
            mc.polySelectConstraint(mode=3, type=0x0008, size=3)
        elif selType == 'Triangles':
            mc.polySelectConstraint(mode=3, type=0x0008, size=1)
        mc.polySelectConstraint(disable=True)
        sel_poly = mc.ls(sl=True)
        if sel_poly:
            return sel_poly
        else:
            mc.inViewMessage(amg='<font color="#31d2b1">Your mesh is good</font><br>.', pos='topCenter', fade=True, fst=5)
            mc.select(sel_obj)
    else :
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True, fst=5)
        #mc.warning("nothing selected")

def growAlongRing():
    sel_obj = mc.ls(sl = True, flatten = True)
    mc.select(sel_obj[0])
    mc.polySelectSp(ring = True)
    ring = mc.ls(sl = True, flatten = True)
    mc.select(sel_obj)
    mc.select(mc.polyListComponentConversion(tf = True))
    mc.select(mc.polyListComponentConversion(te = True))
    growEdges = mc.ls(sl = True, flatten = True)
    growRings = list(set(growEdges).intersection(set(ring)))
    mc.select(growRings)
    return growRings

def getloop_or_ring(typ, sel_obj):
    mc.select(sel_obj)
    if typ == 'l':
        mc.polySelectSp(loop = True)
    else:
        mc.polySelectSp(ring = True)
    return mc.ls(sl = True, flatten = True)

def growloop_or_ring(typ):
    if typ == 'r':
        growAlongRing()
    else:
        mel.eval('PolySelectTraverse 5')

def checker_select(op = 'l', spacing = 1):
    sel_obj = mc.ls(sl=True, flatten = True)
    check_spacing = False
    non_edge = False
    loop_or_ring = []
    de_sel = []
    #caculating spacing based on selection
    if sel_obj:
        if '.e[' in sel_obj[0]:
            edge_loop = getloop_or_ring('l', sel_obj[0])
            edge_ring = getloop_or_ring('r', sel_obj[0])
            if len(sel_obj) == 2:
                if sel_obj[-1] in edge_loop:
                    op = 'l'
                    check_spacing = True
                elif sel_obj[-1] in edge_ring:
                    op = 'r'
                    check_spacing = True
            if len(sel_obj) > 2:
                deledge_loop = list(set(edge_loop) - set(sel_obj))
                deledge_ring = list(set(edge_ring) - set(sel_obj))
                if len(deledge_loop) == 2:
                    op = 'l'
                    check_spacing = True
                    de_sel = deledge_loop
                    sel_obj = de_sel
                    loop_or_ring = edge_loop
                elif len(deledge_loop) == 0:
                    op = 'l'
                elif len(deledge_ring) == 2:
                    op = 'r'
                    de_sel = deledge_ring
                    sel_obj = de_sel
                    check_spacing = True
                    loop_or_ring = edge_ring
                elif len(deledge_ring) == 0:
                    op = 'r'
                else:
                    return
                    
        elif '.f[' in sel_obj[0] or '.vtx[' in sel_obj[0] or '.map[' in sel_obj[0]:
            non_edge = True
            op = 'l'
            for obj in range(2):
                mc.polySelectSp(loop = True)
            non_edge_loop = mc.ls(sl = True, flatten = True)   
            if len(sel_obj) == 2:
                check_spacing = True
            if len(sel_obj) > 2:
                de_sel = list(set(non_edge_loop) - set(sel_obj))
                if len(de_sel) == 2:
                    check_spacing = True
                    sel_obj = de_sel         
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True, fst=5)
        return
    
    if check_spacing:
        mc.select(sel_obj[0])
        for obj in range(50):
            growloop_or_ring(op)
            if sel_obj[-1] in mc.ls(sl = True, flatten = True):
                spacing = obj
                break
    spacing = spacing + 1
    is_edge = True
    current_obj = sel_obj
    ordered_obj = []
    added_obj = []
    filtered_obj = []
        
    if len(sel_obj) == 1:
        ordered_obj = sel_obj
        
    mc.select(sel_obj[0])
    for i in range(5000):

        index = i+1
        growloop_or_ring(op)
        added_obj = mc.ls(sl = True, flatten = True)
        if non_edge:
            added_obj = list(set(non_edge_loop).intersection(set(added_obj)))
        filtered_obj = list(set(added_obj) - set(current_obj))
        current_obj = added_obj
        if not filtered_obj:
            break
        if index % spacing == 0:
            ordered_obj.append(filtered_obj[0])
            if len(filtered_obj) == 2:
                ordered_obj.append(filtered_obj[1])
        else:
            continue
        ordered_obj.append(sel_obj[0])        
    if de_sel and non_edge:
        ordered_obj = list(set(non_edge_loop) - set(ordered_obj))
    if de_sel and loop_or_ring:
        ordered_obj = list(set(loop_or_ring) - set(ordered_obj))
        
    mc.select(ordered_obj)

def set_color_space(color_space):
    
    sel_file = mc.ls(sl=True, type='file')
    if sel_file:
        for file in sel_file:
            mc.setAttr(file+'.colorSpace', color_space, type='string')
        print('set color space to '+color_space)
    else:
        mc.inViewMessage(amg='Selecte file nodes<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True, fst=5)
        mc.warning('Selecte file nodes')

def file_generator():
    
    sel_tile = mc.ls(sl=True, type='place2dTexture')
    if sel_tile:
        tile = sel_tile[0]
    else:
        tile = mc.shadingNode('place2dTexture', asUtility=True)
    file = mc.createNode('file')
    
    #connecting repeator and file node
    connect_tweaker_to_file(tile, file)
    file_nodetree = [tile, file]
    mc.select(file_nodetree)
    mel.eval('NodeEditorGraphAddSelected;')
    mc.select(tile)
    return file

def insert_color_adjustment(color_adjustment):
    
    ai_nodes = ['aiRange', 'aiColorCorrect']
    try:
        node = mc.ls(sl = True)[0]
    except:
        node = ''
    insert_node = core.createArnoldNode(color_adjustment)
    
    single_output_suffix = ['.outColorR', '.outColorG', '.outColorB']
    node_connections = mc.listConnections(node+'.outColor', plugs=True)
    node_connections_rbg = []
    for single_plug in single_output_suffix:
        single_connection = mc.listConnections(node+single_plug, plugs=True)
        if single_connection:
            node_connections_rbg.append(single_connection)
    if node:
        mc.connectAttr(node+'.outColor', insert_node+'.input') 
        if '_' in node:
            node = node.split('_')[0]
            print(node)
        insert_node = mc.rename(insert_node, node+'_'+color_adjustment)
    
    if node_connections:
        for plug in node_connections:
            mc.connectAttr(insert_node+'.outColor', plug, f=True)
    if node_connections_rbg:
        for connections in node_connections_rbg:
            index = node_connections_rbg.index(connections)
            node_output = insert_node+single_output_suffix[index]
            for single_color_input_plug in connections:
                mc.connectAttr(node_output, single_color_input_plug, f=True)
    print(str(insert_node))
    mel.eval('NodeEditorGraphAddSelected;')
    return insert_node

def link_uv():
    
    sel_obj = mc.ls(sl=True)
    for obj in sel_obj:
        
        if mc.objectType(obj) == 'place2dTexture':
            mc.connectAttr('{}.repeatU'.format(obj), '{}.repeatV'.format(obj), f=True)
            
        elif mc.objectType(obj) == 'file':
            
            for node in set(mc.listConnections(obj)):
                
                if mc.objectType(node) == 'place2dTexture':
                    mc.connectAttr('{}.repeatU'.format(node), '{}.repeatV'.format(node), f=True)
            
        elif mc.objectType(obj) == 'aiNoise':
            
            mc.connectAttr('{}.scale.scaleX'.format(obj), '{}.scale.scaleY'.format(obj), f=True)
            mc.connectAttr('{}.scale.scaleX'.format(obj), '{}.scale.scaleZ'.format(obj), f=True)
            
        else:
            pass

def break_linked_uv():
    
    sel_obj = mc.ls(sl=True)
    for obj in sel_obj:
        if mc.objectType(obj) == 'place2dTexture':
            mc.disconnectAttr('{}.repeatU'.format(obj), '{}.repeatV'.format(obj))
            
        elif mc.objectType(obj) == 'file':
            
            for node in set(mc.listConnections(obj)):
                
                if mc.objectType(node) == 'place2dTexture':
                    mc.disconnectAttr('{}.repeatU'.format(node), '{}.repeatV'.format(node))
            
        elif mc.objectType(obj) == 'aiNoise':
            
            mc.disconnectAttr('{}.scale.scaleX'.format(obj), '{}.scale.scaleY'.format(obj))
            mc.disconnectAttr('{}.scale.scaleX'.format(obj), '{}.scale.scaleZ'.format(obj))
            
        else:
            pass

def instance(axis='', colorize=True):
    
    sel_obj = mc.ls(sl=True, typ='transform')
    for obj in sel_obj:
        if colorize:
            mc.setAttr('{}.useOutlinerColor'.format(obj), True)
            mc.setAttr('{}.outlinerColor'.format(obj), 1.531999945640564, 0.8253204822540283, 0.4320240020751953, typ='double3')
        #print(mc.getAttr('{}.outlinerColor'.format(obj)))        
        
def bake_instance():
    
    sel_obj = mc.ls(sl=True, typ='transform')
    for obj in sel_obj:
        mc.setAttr('{}.useOutlinerColor'.format(obj), False)
        
def colorize(r, g, b):
    
    sel_obj = mc.ls(sl=True)
    for obj in sel_obj:
        mc.setAttr('{}.useOutlinerColor'.format(obj), True)
        mc.setAttr('{}.outlinerColor'.format(obj), r, g, b, typ='double3')

def reset_color():
    
    sel_obj = mc.ls(sl=True)
    for obj in sel_obj:
        mc.setAttr('{}.useOutlinerColor'.format(obj), False)
        
def select_hard_edges(low_angle, high_angle):
    
    mc.undoInfo(openChunk=True)
    sel_obj = mc.ls(sl=True)
    filtered_edge = []
    if sel_obj:
        selEdge = mc.polyListComponentConversion(toEdge=True)
        mc.select(selEdge)
        preserved_edge = mc.ls(sl=True, flatten=True)
        mc.polySelectConstraint(m=3 , t=0x8000, a=True, ab=(low_angle, high_angle))
        mc.polySelectConstraint(m=0)
        allHE = mc.ls(sl = True, flatten=True)
        filtered_edge = list(set(allHE).intersection(set(preserved_edge)))
        mc.select(sel_obj)
        mel.eval('setSelectMode components Components; selectType -smp 0 -sme 1 -smf 0 -smu 0 -pv 0 -pe 1 -pf 0 -puv 0; HideManipulators; ')
        mc.select(filtered_edge, r=True)
    else:
        mc.inViewMessage(amg='Nothing selected<font color="#fdca3b"></font><br>.', pos='topCenter', fade=True)
    mc.undoInfo(closeChunk=True)
    
    
def get_true_object_type(sel_obj):
    true_type = ''
    if sel_obj:
        child = mc.listRelatives(sel_obj, c=True, f=True)
        if child:
            transform_list = mc.listRelatives(sel_obj, c=True, f=True, typ='transform')
            if not transform_list:
                if len(child) == 1:
                    true_type = mc.objectType(child)
                elif len(child) == 0:
                    pass
                else:
                    true_type = mc.objectType(child[0])
            else:
                shape = list(set(child)-set(transform_list))
                if shape:
                    true_type = mc.objectType(shape[0])
                else:
                    true_type = mc.objectType(sel_obj)
        else:
             true_type = mc.objectType(sel_obj)
            
    else:
        true_type = ''
    
    return true_type
