# iblLoader
Houdini python panel to load .ibl lighting files from: http://hdrlabs.com/sibl

Currently supporting Mantra only

iblLoader.ui goes in $HOUDINI_USER_PREF_DIR/python_panels (Textport: echo $HOUDINI_USER_PREF_DIR)

iblLoader.py code gets copied into a new python panel interface in Houdini (http://www.sidefx.com/docs/houdini/ref/panes/pythonpanel)

Download ibl sets from http://hdrlabs.com/sibl/archive.html and browse through the iblLoader python panel interface to the folder containing the unzipped archive folders

To do:

1) Add .rat conversion on the fly

2) Enable the .ibl creation section from HDR files (experimental)

3) Enable other renderers (Arnold, PRMan, Redshift, Vray etc) 
