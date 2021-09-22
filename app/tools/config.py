import os

APP_NAME = 'easyfm'

home_path = os.path.expanduser("~")
app_path = os.path.join(home_path, APP_NAME)
module_path = os.path.dirname(os.path.abspath(__file__)) #path to module

config = {
    'app': app_path,
    'img':os.path.normpath(os.path.join(module_path, "../img")),
    'libs':os.path.normpath(os.path.join(module_path, "../libs")),
}

preference = {
    # 'project_folder':'', 
}