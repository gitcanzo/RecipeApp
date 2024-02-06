import sqlite3

from kivy.app import App
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from ui.widgets import (
    AddToBasketButton,
    BaseLabel,
    BasePopup,
    BaseTextInput,
    BoxLayout,
    BrowseListRow,
    Button,
    ConfirmPopup,
    DelIngButton,
    DropListButton,
    DropListTextInput,
    IngredientRow,
    InputPopup,
    Label,
    LeftLabel,
    ListButton,
    MainButton,
    SmallLabel,
    SmallLeftLabel,
    Spacing,
    TagButton,
    TagLabel,
    WrappedLabel)

from db.query import (
    fetchIngredients,
    fetchRecipesAll,
    deleteRecipe,
    fetchRecipe,
    recipeExists,
    saveRecipe)


'''
DEFINING WINDOWS / SCREENS
'''
class MainWindow(Screen):
    '''
    Main screen of the application
    '''
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        print('[RECIPAPP] Main Window started')

    def comingSoon(self):
        self.comingSoonPopup = BasePopup()
        self.comingSoonPopup.title = "Coming soon"
        self.comingSoonPopup.message.text = "Coming soon!"
        self.comingSoonPopup.open()

class AddWindow(Screen):
    '''
    Screen for creating a new recipe
    '''
    def __init__(self, **kwargs):
        super(AddWindow, self).__init__(**kwargs)

        self.row_height = '35sp'
        self.newRecipe = True
        self.nameInput = ''
        self.oldName = ''

        self.exitFlag = False

    def recipeEdit(self, nameInput):
        '''
        Fill all the text inputs automatically when editing a recipe
        '''
        if self.newRecipe == False:
            recipeName, portions, prepTime, tagsList, ingsList, quants, measures, steps = fetchRecipe(nameInput, True)
            self.oldName = recipeName
            self.recipeName.text = self.oldName
            self.portions.text = str(portions)
            self.prepTime.text = str(prepTime)
            self.steps.text = steps
            # tags
            tagsGrid = self.tagsStack.children[0]
            tagsBox = tagsGrid.children[:]
            self.tagButtonsBox = tagsBox[0]
            if len(tagsList) >= 1:
                for tag in tagsList:
                    self.tagButtonsBox.add_widget(TagButton(text=tag))
            # ingredients
            if len(ingsList) >= 2:
                for n in range(1, len(ingsList)):
                    self.ingsGrid.add_widget(Factory.IngredientRow(), index=0)
            rows = self.ingsGrid.children[:] # all the IngredientRow widgets
            for row in rows[1:]:
                row.remove_widget(row.children[0])
                row.add_widget(Factory.DelIngButton(), index=0)
            str_quants = {}
            i = 0
            for index in range(len(rows)-1,-1,-1):
                row = rows[index]
                if len(ingsList) >=1:
                    row.children[3].text = ingsList[i]
                    row.children[2].text = str(quants[i]) if quants[i] != 0 else ''
                    row.children[1].text = measures[i] if not type(measures[i]) is int else str(measures[i])
                i += 1
        else:
            pass

    def addIngredient(self, instance):
        '''
        Adds a new IngredientRow to the ingredients grid
        '''
        row = instance.parent
        row.remove_widget(row.children[0]) # replace '+' button with '-' button in actual row
        row.add_widget(Factory.DelIngButton(), index=0)
        self.ingsGrid.add_widget(Factory.IngredientRow(), index=0) # add new row

    def preSave(self):
        '''
        Prepare inputs for saving recipe into DB
        '''
        print("[RECIPAPP] Preparing to save recipe")
        self.noIngredientsFlag = True # Changes to False if there is at least one non-empty ingredient row
        self.noIngNameFlag = False # Changes to True if one row has empty ingredient name and non-empty quantity and/or measure
        self.exitFlag = False # True when saving is complete

        recipeName = self.recipeName.text.lower()
        portions = int(self.portions.text) if self.portions.text != '' else 1
        prepTime = self.prepTime.text if self.portions.text != '' else 'n.d.'
        steps = self.steps.text
        tagsList = []
        ingsList = {}
        quants = {}
        measures = {}
        
        # TAGS
        tagsGrid = self.tagsStack.children[0]
        tagsBox = tagsGrid.children[:]
        tagButtonsBox = tagsBox[0]
        tags_temp = tagButtonsBox.children[:]
        for tag in tags_temp:
            tagText = tag.text
            if not tagText in tagsList:
                tagsList.append(tagText)

        # INGREDIENTS
        rows = self.ingsGrid.children[:] # all the IngredientRows
        i = 0
        for index in range(len(rows)-1,-1,-1):
            row = rows[index]
            ing = row.children[3]
            quant = row.children[2]
            measure = row.children[1]
            if ing.text == quant.text == measure.text == '': # skip empty rows
                pass
            else:
                ingsList[i] = str(ing.text.lower())
                quant.text = quant.text.translate(quant.text.maketrans(',','.'))
                quants[i] = float(quant.text) if quant.text.isdigit() else quant.text
                measures[i] = str(measure.text)
                i+=1
                ''' Old script for extracting quantity and measure automatically
                for s in quant.text.split():
                    if s.isdigit():
                        quants[i] = float(s)
                measures[i] = ''
                for s in quant.text.split():
                    if s.isalpha():
                        measures[i] = str(s).lower()
                i += 1
                '''
        for i in range(0, len(ingsList)): # Flag if an ingredient has no name
            if (quants[i] != '' or measures[i] != '') and ingsList[i] == '':
                self.noIngNameFlag = True
        for ing in ingsList:
            if ing != '':
                self.noIngredientsFlag = False
        if recipeName == '': # Check that recipeName is not empty
            self.noNamePopup = BasePopup()
            self.noNamePopup.title = "No name"
            self.noNamePopup.message.text = "Please enter a name for your recipe."
            self.noNamePopup.open()
        elif recipeName.isdigit():
            self.wrongNamePopup = BasePopup()
            self.wrongNamePopup.title = "Wrong name"
            self.wrongNamePopup.message.text = "Your recipe name must include at least one letter."
            self.wrongNamePopup.open()
        elif self.noIngredientsFlag == True: # if there are no ingredients
            self.noIngredientsPopup = BasePopup()
            self.noIngredientsPopup.title = "No ingredients"
            self.noIngredientsPopup.message.text = "Your recipe must include at least one ingredient."
            self.noIngredientsPopup.open()
        elif self.noIngNameFlag == True: # If ingredient has no name
            self.noIngNamePopup = BasePopup()
            self.noIngNamePopup.title = "No ingredient name"
            self.noIngNamePopup.message.text = "You must give a name to all your ingredients!"
            self.noIngNamePopup.open()
        else:
            if recipeExists(recipeName) and self.newRecipe==True: # if recipe already exists, when saving a new recipe
                self.existsPopup = BasePopup()
                self.existsPopup.title = "Already exists"
                self.existsPopup.message.text = "This recipe already exists. Please use a different name."
                self.existsPopup.open()
            elif recipeExists(self.oldName) and self.newRecipe==False: # when editing a recipe and keeping the same name
                self.editPopup = ConfirmPopup()
                self.editPopup.title = "Are you sure?"
                self.editPopup.message.text = "Do you want to overwrite this recipe?"
                self.editPopup.noButton.text = "No"
                self.editPopup.noButton.bind(on_release=self.editPopup.dismiss)
                self.editPopup.yesButton.text = "Yes"
                self.editPopup.yesButton.bind(on_release=lambda x: saveRecipe(self, self.oldName, recipeName, portions, prepTime, tagsList, ingsList, quants, measures, steps, self.newRecipe))
                self.editPopup.open()
            else: # if simply saving a new recipe
                saveRecipe(self, self.oldName, recipeName, portions, prepTime, tagsList, ingsList, quants, measures, steps, self.newRecipe)
            self.savePopup = BasePopup()
            self.savePopup.title = "Done"
            self.savePopup.message.text = "Your recipe was saved!"
            self.savePopup.bind(on_dismiss=self.goBack)
            if self.exitFlag == True:
                self.savePopup.open()

    def dismissAndLeave(self, instance):
        '''
        Called by pressing yes button on leave popup (popup that appears if going back and recipe title non empty)
        '''
        self.popup.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'

    def goBack(self, instance):
        '''
        Go back to main screen. If recipe title is not empty, show confirmation popup
        '''
        if self.recipeName.text != '' and self.exitFlag == False:
            self.popup = ConfirmPopup()
            self.popup.title = "Are you sure?"
            self.popup.message.text = "Do you want to leave and discard your changes?"
            self.popup.noButton.text = "Stay"
            self.popup.noButton.bind(on_release=self.popup.dismiss)
            self.popup.yesButton.text = "Leave"
            self.popup.yesButton.bind(on_release=self.dismissAndLeave)
            self.popup.open()   
        else:
            self.exitFlag = False
            self.manager.transition.direction = 'right'
            self.manager.current = 'main'
            
    def clearWidgets(self, instance):
        '''
        Called when leaving the screen. Removes all added tags and ingredient rows to give back a fresh screen
        '''
        #self.tagButtonsBox = self.tagsGrid.children[0]
        #self.tagsInputBox = self.tagsGrid.children[1]
        #self.tagInput = self.tagsInputBox.children[1]
        #self.tagInput.text = ''
        #self.tagButtonsBox.clear_widgets()
        #tagsGrid = self.mainGrid.children[8]
        #self.mainGrid.remove_widget(tagsGrid)
        #self.mainGrid.add_widget(Factory.TagsGrid(), index=8)
        self.tagsStack.clear_widgets()
        self.tagsStack.add_widget(Factory.TagsGrid())
        self.ingsGrid.clear_widgets()
        self.ingsGrid.add_widget(Factory.IngredientRow())


class BrowseWindow(Screen):
    '''
    Screen for browsing list of saved recipes.
    '''
    #def __init__(self, **kwargs):
    #    super(BrowseWindow, self).__init__(**kwargs)

    def goToAddScreen():
        App.get_running_app().root.transition.direction = 'left'
        App.get_running_app().root.current = 'add'


    def makeList(self):
        '''
        Fetches all recipes in database to make list of recipes.
        It also updates the list of recipes based on similar recipe names, tags or ingredients (performed inside fetchRecipesAll())
        If there are no recipes in the database, prints a message inviting to create a recipe.
        '''
        self.curr_screen = App.get_running_app().root.current
        if self.searchInput.focus or self.curr_screen == 'browse':
            self.browseList.clear_widgets()
            textinput = self.searchInput.text
            recipesList = fetchRecipesAll(textinput)
            if len(recipesList) == 0 and self.searchInput.text == '':
                self.browseList.add_widget(BaseLabel( #just empty space
                    size_hint = (1, None),
                    height = '40sp'))
                self.browseList.add_widget(Factory.WrappedLabel(
                    text="You have not added any recipes yet.",
                    size_hint = (1, None)))
                self.browseList.add_widget(BaseLabel( #just empty space
                    size_hint = (1, None),
                    height = '40sp'))
                self.addButton = MainButton(
                    text="Add one now!",
                    size_hint = (1, None),
                    height = '40sp')
                self.addButton.bind(on_release= lambda self: BrowseWindow.goToAddScreen())
                self.browseList.add_widget(self.addButton)
            elif  len(recipesList) == 0 and self.searchInput.text != '':
                self.browseList.add_widget(BaseLabel( #just empty space
                    size_hint = (1, None),
                    height = '40sp'))
                self.browseList.add_widget(Factory.WrappedLabel(
                    text="No recipes matching your search.",
                    size_hint = (1, None)))
            else:
                for recipe in recipesList:
                    self.OneRow = BrowseListRow()
                    self.ListButton = self.OneRow.children[1]
                    self.browseList.add_widget(self.OneRow)
                    self.ListButton.text = recipe.title()
        else:
            pass

class ResultWindow(Screen):
    def __init__(self, **kwargs):
        super(ResultWindow, self).__init__(**kwargs)

        self.exitFlag = False

    def printRecipe(self, nameInput):
        recipeName, portions, prepTime, tagsList, ingsQuantsList, steps = fetchRecipe(nameInput)
        self.recipeName.text = recipeName.title()
        self.portions.text = "Portions:   "+str(portions)
        self.prepTime.text = "Preparation time:   "+str(prepTime)
        # Tags
        for tag in tagsList:
            self.tagsBox.add_widget(TagLabel(text=tag))
        # List of ingredients
        for i in range(0, len(ingsQuantsList)):
            self.ingredientsBox.add_widget(SmallLeftLabel(text=ingsQuantsList[i]))
        # Recipe steps
        if steps != None:
            self.steps.text = steps
        else: pass


    def deletePopup(self):
        self.popup = ConfirmPopup()
        self.popup.title = "Are you sure?"
        self.popup.message.text ="Do you really want to delete this recipe?"
        self.popup.noButton.text = "No"
        self.popup.noButton.bind(on_release=self.popup.dismiss)
        self.popup.yesButton.text = "Yes"
        self.popup.yesButton.bind(on_release=lambda x: deleteRecipe(self, self.recipeName.text))
        self.popup.open()


class ShoppingWindow(Screen):
    pass


class WMan(ScreenManager):
    def __init__(self, **kwargs):
        super(WMan, self).__init__(**kwargs)
        print('[RECIPAPP] Screen Manager Started')

    def openPortionsPopup(self, instance):
        print('[RECIPAPP] Portions Popup opened')
        self.portionsPopup = InputPopup()
        self.portionsPopup.title = "Portions"
        self.portionsPopup.message.text = "How many portions do you need?"
        self.portionsPopup.userInput.input_filter = 'int'
        self.portionsPopup.userInput.bind(on_text_validate=lambda x: self.addToBasket(recipe))
        self.portionsPopup.noButton.text = "Back"
        self.portionsPopup.noButton.bind(on_release=self.portionsPopup.dismiss)
        self.portionsPopup.yesButton.text = "Ok"
        self.recipe = instance.parent.children[1].text.lower()
        self.portionsPopup.yesButton.bind(on_release=lambda x: self.addToBasket(self.recipe))
        self.portionsPopup.open()

    def addToBasket(self, recipe):
        print('[RECIPAPP] Adding to basket')
        self.portionsWanted = int(self.portionsPopup.userInput.text)
        self.portionsPopup.dismiss()
        recipeName, portions, _, _, ingsList, quants, measures, _ = fetchRecipe(recipe, full=True)
        self.portionsWanted = int(self.portionsWanted)
        ratio = self.portionsWanted/portions
        quantsWanted = {}
        i=0
        for i in range(0,len(quants)):
            quantsWanted[i] = quants[i]*ratio if quants[i] is float else quants[i]
            i+=1
        print(ingsList, quants, quantsWanted, measures)
        MainWindow.comingSoon(self)
