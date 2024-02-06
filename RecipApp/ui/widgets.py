from kivy.app import App
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.bubble import Bubble
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from db.query import(
    dbFile,
    fetchIngredients,
    fetchMeasures,
    fetchTags)

import os.path

'''
BUTTONS
'''
class MainButton(Button):
    pass

class DropListButton(Button):  # Custom button for DropDown widget
    def __init__(self, **kwargs):
        super(DropListButton, self).__init__(**kwargs)
        self.bind(on_release=lambda x: self.parent.parent.select(self.text))

class TagButton(Button):
    pass

'''
LABELS
'''
class BaseLabel(Label):
    pass

class SmallLabel(BaseLabel):
    pass

class LeftLabel(BaseLabel): # left aligned label
    pass

class SmallLeftLabel(LeftLabel):
    pass

class TagLabel(Button):
    pass

class WrappedLabel(BaseLabel):
    pass

'''
TEXT INPUTS
'''
class BaseTextInput(TextInput):
    pass

class CutCopyPaste(Bubble):
    pass

class DropListTextInput(BaseTextInput):
    '''
    TextInput inside DropDown: this class is to keep the dropdown open while focusing the DropDown's textinput.
    '''
    def on_focus(self, *args):
        if self.focus:
            self.parent.parent.selection_is_DLTI = True
        else:
            self.parent.parent.selection_is_DLTI = False

    def on_text_validate(self, *args):
        self.parent.parent.selection_is_DLTI = False
        # put the text from this widget into the TextInput that the DropDown is attached to
        self.parent.parent.attach_to.text = self.text
        # dismiss the DropDown
        self.parent.parent.dismiss()


class TagsGrid(GridLayout):
    '''
    Box containing text input for choosing recipe tags
    '''
    def __init__(self, **kwargs):
        super(TagsGrid, self).__init__(**kwargs)
        self.dropdown = BaseDropDown()

        self.tags = fetchTags()
        for tag in self.tags:
            self.tagRow = DropListButton()
            self.tagRow.text = tag
            self.tagRow.size_hint = 1, None
            self.tagRow.height = '35sp'
            self.dropdown.add_widget(self.tagRow)


    def addTag(self):
        tags = self.tagButtonsBox.children[:]
        tagsList = []
        for tag in tags:
            tagsList.append(tag.text)
        if not self.tagInput.text in tagsList and not self.tagInput.text.isdigit() and not self.tagInput.text =='':
            self.tagButtonsBox.add_widget(TagButton(text=self.tagInput.text))
        elif self.tagInput.text.isdigit():
            self.popup = BasePopup()
            self.popup.title = 'Wrong tag'
            self.popup.message.text = 'You cannot add a tag containing only numbers.'
            self.popup.open()
        else:
            pass

    def handle_focus(self, ti):
        if ti.focus:
            # open DropDown if the TextInput gets focus
            self.dropdown.open(ti)
        else:
            # ti has lost focus
            if self.dropdown.selection_is_DLTI:
                # do not dismiss if a DropListTextInput is the selection
                return

            # dismiss DropDown
            self.dropdown.dismiss(ti)
            self.dropdown.unbind_all()
            self.dropdown.fbind('on_select', lambda self, x: setattr(ti, 'text', x))



#########################
#   AddWindow-specific  #
#########################

class DelIngButton(Button): # button for deleting IngredientRow in AddRecipe window
    pass


class IngredientRow(BoxLayout): # Row containing textinputs for ingredient, quantity and measure
    def __init__(self, **kwargs):
        super(IngredientRow, self).__init__(**kwargs)
        self.ings_dropdown = BaseDropDown()        
        self.m_dropdown = BaseDropDown()

        self.ingsList = []

        # Add measures to measure Drop Down
        if not os.path.isfile(dbFile):
            pass
        else:
            measures = fetchMeasures()
            for measure in measures:
                if measure == '':
                    pass
                else:
                    self.mRow = DropListButton(halign='center')
                    self.mRow.text = measure
                    self.mRow.size_hint = 1, None
                    self.mRow.height = '35sp'
                    self.m_dropdown.add_widget(self.mRow)
            #self.m_dropdown.add_widget(DropListTextInput())

    def update_ingredients(self, ti):
        dropdown = self.ings_dropdown
        dropdown.clear_widgets()
        if len(ti.text)>=1:
            self.ingsList = fetchIngredients(ti.text)
            for ingredient in self.ingsList:
                self.IRow = DropListButton()
                self.IRow.text = ingredient
                self.IRow.size_hint = 1, None
                self.IRow.height = '35sp'
                dropdown.add_widget(self.IRow)
        else:
            self.ingsList = []

    def handle_focus(self, ti, ing=False):
        '''
        Handle on_focus event for the measure TextInput.
            ing=True indicates the focus is requested by an ingredient text input (which triggers ingredient suggestions)
        '''
        if ing==False: # if textinput is not an ingredient input
            dropdown = self.m_dropdown
        else: 
            dropdown = self.ings_dropdown # Add ingredient suggestions to ingredient Drop Down

        if ti.focus:
            # open DropDown if the TextInput gets focus
            dropdown.open(ti)
        else:
            # ti has lost focus
            if dropdown.selection_is_DLTI:
                # do not dismiss if a DropListTextInput is the selection
                return

            # dismiss DropDown
            dropdown.dismiss(ti)
            dropdown.unbind_all()
            dropdown.fbind('on_select', lambda self, x: setattr(ti, 'text', x))


class BaseDropDown(DropDown):
    selection_is_DLTI = BooleanProperty(False)

    def unbind_all(self):
        # unbind all the current call backs for `on_slect`
        for callBack in self.get_property_observers('on_select'):
            self.funbind('on_select', callBack)


#############################
#   BrowseWindow specific   #
#############################
class BrowseListRow(BoxLayout):
    pass

class ListButton(Button):
    '''
    Button for browseWindow list of recipes. On click, it opens the recipe window
    '''
    def __init__(self, **kwargs):
        super(ListButton, self).__init__(**kwargs)

        self.bind(on_release = lambda x: self.listBindings(self))

    def listBindings(self, i):
        App.get_running_app().root.current = 'result'
        App.get_running_app().root.ids.result.printRecipe(i.text)

class AddToBasketButton(Button):
    pass

##########################
#   ShoppingWindow-specific
##########################

class RecipeRow(BoxLayout):
    pass


##########################
#   GENERAL
##########################
class BasePopup(Popup):
    pass

class ConfirmPopup(Popup):
    pass

class InputPopup(Popup):
    pass

class Spacing(Widget):
    pass

class TopBar(BoxLayout):
    pass
