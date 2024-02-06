from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.utils import platform
from pathlib import Path

from ui.views import (
    AddWindow,
    WMan)

from db.query import (
    dbInit)

Window.clearcolor = (.95, .95, .95, 1)
Window.softinput_mode = 'below_target'

kv = Builder.load_file("ui/layout.kv")

'''
# For sharing the clipboard between app and system:

from jnius import autoclass

if platform == 'android':
    from android import mActivity
    JS     = autoclass('java.lang.String')
    Intent = autoclass('android.content.Intent')

    def share_text(self, data):
        send = Intent()
        send.setAction(Intent.ACTION_SEND)  
        send.setType("text/plain")
        send.putExtra(Intent.EXTRA_TEXT, JS(data))
        mActivity.startActivity(Intent.createChooser(send,None))  

    self.share_text('Greetings Earthlings')

'''

class RecipApp(App):
    manager = ObjectProperty()
  
    def build(self):
        self.sm = WMan()
        self.manager = self.sm
        self.bind(on_start=self.post_build_init)
        
        # Get writeable folder user files (OS-dependent)
        dbFool = dbInit()
        print('[RECIPAPP] The database is located at: ',dbFool)
        
        return kv

    '''
    Following two methods are for 'Esc' button (Windows) or 'Back' button (Android) not to exit the app (unless in MainWindow)
    '''
    def post_build_init(self, *args):
        self.win = Window
        self.win.bind(on_keyboard=self.my_key_handler)

    def my_key_handler(self, window, keycode1, keycode2, text, modifiers):
        if keycode1 in [27, 1001] and App.get_running_app().root.current != 'add' and App.get_running_app().root.current != 'main':
            App.get_running_app().root.transition.direction = 'right'
            App.get_running_app().root.current = 'main'
            return True
        elif keycode1 in [27, 1001] and App.get_running_app().root.current == 'add':
            App.get_running_app().root.ids.add.goBack(AddWindow)
            return True
        elif keycode1 in [27, 1001] and App.get_running_app().root.current == 'main':
            App.get_running_app().stop()
            return True
        return False