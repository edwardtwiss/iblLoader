import os
import sys

from hutil.Qt import QtCore
from hutil.Qt import QtGui
from hutil.Qt import QtWidgets
from hutil.Qt import QtUiTools
from hutil.Qt.QtGui import QPixmap

import ConfigParser
from os.path import basename

global ui_location
global ui_file_path
# Change this location to match the location of the iblLoader.ui file
userDir = hou.expandString("$HOUDINI_USER_PREF_DIR")
ui_location = (userDir + "/python_panels/") 
ui_file_path = (ui_location + "iblLoader.ui")

# To support both PySide/Qt4 and PySide2/Qt5.
try:
    from PySide2 import QtWebEngineWidgets
    web_view_cls = QtWebEngineWidgets.QWebEngineView
    pyside_version = 2
except:
    from PySide import QtWebKit
    web_view_cls = QtWebKit.QWebView
    pyside_version = 1 

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)        
        

theMainWidget = None
theDisplayLabel = None
    
def browse_folder():
        listSiblFiles = theMainWidget.findChild(QtWidgets.QListWidget, "listSiblFiles")
        listSiblFiles.clear()         
        directory = QtWidgets.QFileDialog.getExistingDirectory()  #(self,"Pick a folder") 
        with open(ui_location + "directory.cfg", "w") as text_file:
            text_file.write(directory) 
        comboBox = theMainWidget.findChild(QtWidgets.QComboBox, "comboBox")
        comboBox.clear()
        comboBox.addItem(directory)
        directory = str(comboBox.currentText())
        populate_list()   
       
def read_cfg():
        with open(ui_location + "directory.cfg", "r") as text_file:
            directory = text_file.read()         
        comboBox = theMainWidget.findChild(QtWidgets.QComboBox, "comboBox")
        comboBox.clear()
        comboBox.addItem(directory)       
        directory = str(comboBox.currentText())
        populate_list()
        
            
def populate_list():
        comboBox = theMainWidget.findChild(QtWidgets.QComboBox, "comboBox")
        directory = str(comboBox.currentText())
        #displayDialog = hou.ui.selectFile(file_type=hou.fileType.Directory)
        #directory = displayDialog()
        #print directory
        listSiblFiles = theMainWidget.findChild(QtWidgets.QListWidget, "listSiblFiles")
        if directory:                                      
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.ibl'):
                        currentFile = os.path.join(root, file).replace("\\", "/")
                        item = QtWidgets.QListWidgetItem(file)
                        item.setData(QtCore.Qt.UserRole, str(currentFile))
                        listSiblFiles.addItem(item)
                        listSiblFiles.sortItems()                        
                                             
def item_click(item):
        path = item.data(QtCore.Qt.UserRole)
        global itemPath
        itemPath = path
        #print path
        head, tail = os.path.split(path)        
        label = theMainWidget.findChild(QtWidgets.QLabel,"label")
        #print label
        pixmap = QtGui.QPixmap()        
        config = ConfigParser.ConfigParser()
        config.read(path)        
        if config.has_option('Header', 'PREVIEWfile'):   
            PREVIEWfile = config.get('Header', 'PREVIEWfile')
            previewPath = head + "/" + PREVIEWfile[1:-1]
            pixmap.load(_fromUtf8(previewPath))
            label.setPixmap(pixmap)            
        else:
            PREVIEWfile = config.get('Background', 'BGfile')
            previewPath = head + "/" + PREVIEWfile[1:-1]
            pixmap.load(_fromUtf8(previewPath))
            myScaledPixmap = pixmap.scaledToHeight(300)
            #scaled(label.size(),Qt.KeepAspectRatio)            
            label.setPixmap(myScaledPixmap)                  
              
        name = config.get('Header', 'Name')
        print name
        nameLabel = theMainWidget.findChild(QtWidgets.QLabel, "nameLabel")
        nameLabel.setText("Name: " + name[1:-1])
        locationLabel = theMainWidget.findChild(QtWidgets.QLabel, "locationLabel")
        location = config.get('Header', 'Location')
        print location
        locationLabel.setText("Location: " + location[1:-1])
        commentLabel = theMainWidget.findChild(QtWidgets.QLabel, "commentLabel")
        comment = config.get('Header', 'Comment')
        print comment
        commentLabel.setText("Comment: " + comment[1:-1])                        

    
def unload_sibl():
        for n in hou.node('/obj').children():
            if n.name().startswith('IBL_'):                
                #deleteMe = n.path(self)
                hou.Node.destroy(n) 
            #else:
                #print 'Nothing to unload'               
                
                
def load_sibl():
        filePath = itemPath
        # Parse file name to use later
        fileName = basename(filePath.replace (" ", "_"))
        assetName = os.path.splitext(fileName)[0]
        head, tail = os.path.split(filePath)
        # Create subnet to hold nodes
        objectRoot = hou.node('/obj')
        masterNet = objectRoot.createNode('subnet') 
        masterNet.setName("IBL_" + assetName)
        
        hou_parm_template_group = hou.ParmTemplateGroup()
        hou_parm_template = hou.FolderParmTemplate("folder0", "IBL Setup", folder_type=hou.folderType.Simple, default_value=0, ends_tab_group=False)
        hou_parm_template_group.append(hou_parm_template)
        masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
        
        # Functions to create nodes from .ibl file
        
        # Background setup        
        def ConfigBackground():
                BGfile = config.get('Background', 'BGfile')
                bgFile = head + "/" + BGfile[1:-1]
                backgroundSop = masterNet.createNode('envlight')
                backgroundSop.setPosition([-3, -3])
                backgroundSop.parm('env_map').set(bgFile)
                backgroundSop.parm('ogl_enablelight').set(True)
                backgroundSop.parm('light_contrib').set("3")
                backgroundSop.parm('light_contribname1').set("reflect")
                backgroundSop.parm('light_contribenable1').set(False)
                backgroundSop.parm('light_contribname2').set("direct")
                backgroundSop.parm('light_contribenable2').set(False)
                backgroundSop.parm('light_contribname3').set("indirect")
                backgroundSop.parm('light_contribenable3').set(False)
                backgroundSop.parm('light_contribprimary').set(True)
                backgroundSop.parm('env_mode').set("direct")
                backgroundSop.setName("IBL_background")
                hou_parm_template = hou.ToggleParmTemplate("BG_enable", "Background Enable", default_value=False, default_expression='on', default_expression_language=hou.scriptLanguage.Hscript)
                hou_parm_template_group.append(hou_parm_template)
                masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
                BGenable = hou.parm(str(masterNet.path()) + "/BG_enable")
                hou.parm(str(backgroundSop.path()) + "/light_enable").set(BGenable)
        
        # Environment light setup
        def ConfigEnvironment():
                EVfile = config.get('Enviroment', 'EVfile')
                EVmulti = config.get('Enviroment', 'EVmulti')
                EVgamma = config.get('Enviroment', 'EVmulti')
                envFile = head + "/" + EVfile[1:-1]
                envLightSop = masterNet.createNode('envlight')
                envLightSop.setPosition([-3, -1])
                envLightSop.parm('env_map').set(envFile)
                envLightSop.parm('light_exposure').set(float(EVgamma))
                envLightSop.parm('ogl_enablelight').set(False)
                envLightSop.parm('light_contrib').set("1")
                envLightSop.parm('light_contribname1').set("reflect")
                envLightSop.parm('light_contribenable1').set(False)
                envLightSop.parm('env_mode').set("direct")
                envLightSop.setName("IBL_environmentLght")
                hou_parm_template = hou.ToggleParmTemplate("envLight_enable", "Environment Light Enable", default_value=False, default_expression='on', default_expression_language=hou.scriptLanguage.Hscript)
                hou_parm_template_group.append(hou_parm_template)
                masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
                ENVenable = hou.parm(str(masterNet.path()) + "/envLight_enable")
                hou.parm(str(envLightSop.path()) + "/light_enable").set(ENVenable)
        
        # Reflection setup        
        def ConfigReflection():
                REFfile = config.get('Reflection', 'REFfile')
                refFile = head + "/" + REFfile[1:-1]
                reflectionSop = masterNet.createNode('envlight')
                reflectionSop.setName("IBL_reflection")
                reflectionSop.setPosition([-3, -2])
                reflectionSop.parm('env_map').set(refFile)
                reflectionSop.parm('ogl_enablelight').set(False)
                reflectionSop.parm('light_contrib').set("3")
                reflectionSop.parm('light_contribname1').set("reflect")
                reflectionSop.parm('light_contribenable1').set(True)
                reflectionSop.parm('light_contribname2').set("direct")
                reflectionSop.parm('light_contribenable2').set(False)
                reflectionSop.parm('light_contribname3').set("indirect")
                reflectionSop.parm('light_contribenable3').set(False)
                reflectionSop.parm('env_mode').set("background")
                hou_parm_template = hou.ToggleParmTemplate("refl_enable", "Reflection Enable", default_value=False, default_expression='on', default_expression_language=hou.scriptLanguage.Hscript)
                hou_parm_template_group.append(hou_parm_template)
                masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
                REFLenable = hou.parm(str(masterNet.path()) + "/refl_enable")
                hou.parm(str(reflectionSop.path()) + "/light_enable").set(REFLenable)        
                
        # Sunlight setup
        def ConfigSunlight():
                SUNcolor = config.get('Sun', 'SUNcolor')
                SUNmulti = config.get('Sun', 'SUNmulti')
                SUNu = config.get('Sun', 'SUNu')
                SUNv = config.get('Sun', 'SUNv')
                sunColors = SUNcolor.split(",")
                sunXrot = (-90) + (float(SUNv) * 180)
                sunYrot = (-(float(SUNu) * 360))
                controlSop = masterNet.createNode('null')
                controlSop.setPosition([0, -1])
                controlSop.parm('rx').set(sunXrot)
                controlSop.parm('ry').set(sunYrot)
                sunLightSop = masterNet.createNode('hlight')
                sunLightSop.setPosition([0, -2])
                sunLightSop.parm('light_type').set("distant")
                sunLightSop.parm('light_colorr').set((float(sunColors[0])/255))
                sunLightSop.parm('light_colorg').set((float(sunColors[1])/255))
                sunLightSop.parm('light_colorb').set((float(sunColors[2])/255))
                sunLightSop.parm('light_intensity').set(SUNmulti)
                sunLightSop.parm('tz').set("100")
                sunLightSop.parm('orthowidth').set("10")
                sunLightSop.setFirstInput(controlSop) 
                sunLightSop.setName("IBL_sun")
                hou_parm_template = hou.ToggleParmTemplate("sunLight_enable", "Sunlight Enable", default_value=False, default_expression='on', default_expression_language=hou.scriptLanguage.Hscript)
                hou_parm_template_group.append(hou_parm_template)
                masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
                SUNenable = hou.parm(str(masterNet.path()) + "/sunLight_enable")
                hou.parm(str(sunLightSop.path()) + "/light_enable").set(SUNenable)
        
        #Lights setup        
        def ConfigLights(section_name):
                LIGHTname  = config.get(section_name, 'LIGHTname')
                LIGHTcolor = config.get(section_name, 'LIGHTcolor')
                LIGHTmulti = config.get(section_name, 'LIGHTmulti')
                LIGHTu = config.get(section_name, 'LIGHTu')
                LIGHTv = config.get(section_name, 'LIGHTv')
                lightColors = LIGHTcolor.split(",")
                lightXrot = (-90) + (float(LIGHTv) * 180)
                lightYrot = (-(float(LIGHTu) * 360))
                controlSop = masterNet.createNode('null')
                controlSop.setPosition([0, -5])
                controlSop.parm('rx').set(lightXrot)
                controlSop.parm('ry').set(lightYrot)
                extraLightSop = masterNet.createNode('hlight')
                extraLightSop.setPosition([0, -6])
                extraLightSop.parm('light_type').set("distant")
                extraLightSop.parm('light_colorr').set((float(lightColors[0])/255))
                extraLightSop.parm('light_colorg').set((float(lightColors[1])/255))
                extraLightSop.parm('light_colorb').set((float(lightColors[2])/255))
                extraLightSop.parm('light_intensity').set((float(LIGHTmulti)/4))
                extraLightSop.parm('tz').set("10")
                # extraLightSop.parm('orthowidth').set("10")
                extraLightSop.setFirstInput(controlSop) 
                extraLightSop.setName(LIGHTname[1:-1])
                hou_parm_template = hou.ToggleParmTemplate(section_name + "_enable", section_name + " Enable", default_value=False, default_expression='on', default_expression_language=hou.scriptLanguage.Hscript)
                hou_parm_template_group.append(hou_parm_template)
                masterNet.addSpareParmTuple( hou_parm_template, in_folder=(["IBL"]), create_missing_folders=True)
                LIGHTenable = hou.parm(str(masterNet.path()) + "/" + section_name + "_enable")
                hou.parm(str(extraLightSop.path()) + "/light_enable").set(LIGHTenable)
        
        # Shader balls for lighting verifcation        
        def configShaderBalls():
                print "Shader balls disabled for now"
                """
                shopnetSop = masterNet.createNode('shopnet')
                shopnetSop.setPosition([3, -1])
                shaderSop = shopnetSop.createNode('principledshader')
                shaderSop.parm('reflect').set("1")
                shaderSop.parm('metallic').set("1")
                shaderSop.parm('rough').set("0")
                shaderSop.parm('sheen').set("1")
                shaderSop.setName("mirrorBallShader")
                chromeShader = shaderSop.path()
                chromeSphere = masterNet.createNode('geo')
                chromeSphere.node('file1').destroy()
                chromeSphere.createNode('sphere')
                chromeSphere.setPosition([0, -3])
                chromeSphere.parm('tx').set("4")
                chromeSphere.parm('ty').set("1")
                chromeSphere.parm('shop_materialpath').set(chromeShader)
                chromeSphere.setName("mirrorBall")
                shaderSop = shopnetSop.createNode('principledshader')
                shaderSop.parm('reflect').set("0")
                shaderSop.parm('metallic').set("0")
                shaderSop.parm('rough').set("1")
                shaderSop.parm('sheen').set("0")
                shaderSop.setName("greyShader")
                greyShader = shaderSop.path()
                greySphere = masterNet.createNode('geo')
                greySphere.node('file1').destroy()
                greySphere.createNode('sphere')
                greySphere.setPosition([0, -4])
                greySphere.parm('tx').set("-4")
                greySphere.parm('ty').set("1")
                greySphere.parm('shop_materialpath').set(greyShader)
                greySphere.setName("greyBall")
                """
        
        # Open and import .ibl config file variables
        config = ConfigParser.ConfigParser()
        config.read(filePath)   
        
        # Parse the .ibl file to create nodes
        for section_name in config.sections():
                if section_name == 'Enviroment':
                        ConfigEnvironment()
                if section_name == 'Reflection':
                        ConfigReflection()
                if section_name =='Background':
                        ConfigBackground()
                if section_name == 'Sun':
                        ConfigSunlight()
                if section_name == 'Light1':
                        ConfigLights(section_name)
                if section_name == 'Light2':
                        ConfigLights(section_name)        
                        
        #Height = config.get('Header', 'Height')
        #masterNet.parm('ty').set(Height)        
        configShaderBalls()        
        

def createInterface():
    global theMainWidget
    
    # Load the interface layout from the .ui file.
    #ui_file_path = "%s/houdini15.5/config/Applications/siblLoader.ui" % os.environ["HOME"]
    loader = QtUiTools.QUiLoader()
    ui_file = QtCore.QFile(ui_file_path)
    ui_file.open(QtCore.QFile.ReadOnly)
    theMainWidget = loader.load(ui_file)

   
    layout = theMainWidget.layout()
    #layout.insertWidget(0, theHelpWidget, 1, QtCore.Qt.AlignTop)

    # Connect ui items to event handlers.
    submit_btn = theMainWidget.findChild(QtWidgets.QPushButton, "btnBrowse")
    submit_btn.clicked.connect(browse_folder)
    comboBox = theMainWidget.findChild(QtWidgets.QComboBox, "comboBox")
    comboBox.activated.connect(read_cfg)    
    btnLoad = theMainWidget.findChild(QtWidgets.QPushButton, "btnLoad")
    btnLoad.clicked.connect(load_sibl)
    btnUnload = theMainWidget.findChild(QtWidgets.QPushButton, "btnUnload")
    btnUnload.clicked.connect(unload_sibl)    
    #self.add_items()
    listSiblFiles = theMainWidget.findChild(QtWidgets.QListWidget, "listSiblFiles")
    listSiblFiles.itemClicked.connect(item_click)
    if os.path.isfile(ui_location + "directory.cfg"):
        read_cfg()

    
    return theMainWidget
    


