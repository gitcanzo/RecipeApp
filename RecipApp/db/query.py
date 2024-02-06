import sqlite3

from kivy.app import App
from kivy.utils import platform
from pathlib import Path
import os.path

# Check platform to choose correct path for user files
if platform == 'android':
    from android.storage import app_storage_path

    user_data_dir = app_storage_path()
    dbFile = user_data_dir+'/recipes.db'
    print('THE DB FILE IS: ',user_data_dir)
else:
    dbFile = 'user/recipes.db'

def dbInit(): # called on startup to create DB if it does not exist already

    if os.path.isfile(dbFile):
        print("[RECIPAPP] Database already exists. Skip")
        return dbFile
    else:
        print(dbFile)
        print("[RECIPAPP] No database found. Creating now")
        conn = sqlite3.connect(dbFile)
        c = conn.cursor()
        c.execute('''CREATE TABLE ingredients (
                            IngredientId   INTEGER PRIMARY KEY,
                            IngredientName STRING  NOT NULL ON CONFLICT IGNORE
                                                UNIQUE ON CONFLICT IGNORE
                                                COLLATE NOCASE
                            )''')

        c.execute('''CREATE TABLE measures (
                            MeasureId   INTEGER PRIMARY KEY,
                            MeasureName STRING  UNIQUE ON CONFLICT IGNORE
                                        COLLATE NOCASE
                            )''')
        default_measures = ['g', 'Kg', 'ml', 'L']
        for unit in default_measures:
            c.execute("INSERT INTO measures (MeasureName) VALUES (?)", (unit,))

        c.execute('''CREATE TABLE pairs (
                            RecipeId     INTEGER REFERENCES recipes (RecipeId) ON DELETE CASCADE
                                                        ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
                            IngredientId INTEGER REFERENCES ingredients (IngredientId),
                            Quantity     NUMERIC,
                            Portions     INTEGER,
                            MeasureId    INTEGER REFERENCES measures (MeasureId)
                            )''')

        c.execute('''CREATE TABLE recipes (
                            RecipeId   INTEGER PRIMARY KEY
                                            NOT NULL,
                            RecipeName STRING  NOT NULL
                                            UNIQUE
                                            COLLATE NOCASE,
                            Steps      TEXT,
                            PrepTime   TEXT
                            )''')

        c.execute('''CREATE TABLE tags (
                            tagId   INTEGER PRIMARY KEY,
                            tagName STRING  NOT NULL
                                    UNIQUE ON CONFLICT IGNORE
                            )''')
        default_tags = ['breakfast', 'lunch', 'dinner', 'dessert']
        for tag in default_tags:
            c.execute("INSERT INTO tags (TagName) VALUES (?)", (tag,))

        c.execute('''CREATE TABLE tagPairs (
                            RecipeId INTEGER REFERENCES recipes (RecipeId) ON DELETE CASCADE
                                                        ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED,
                            TagId    INTEGER REFERENCES tags (tagId) ON DELETE CASCADE
                                                        ON UPDATE CASCADE DEFERRABLE INITIALLY DEFERRED
                            )''')

        conn.commit()
        conn.close()
        print("[RECIPAPP] Database created successfully!")
        return dbFile


def deleteRecipe(instance, recipeName):
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    recipeId_temp = c.execute("SELECT recipeId FROM recipes WHERE recipeName = (?)", (recipeName,)).fetchone()
    recipeId = recipeId_temp[0]
    tagIds_temp = c.execute("SELECT TagId FROM tagPairs WHERE recipeId = (?)", (recipeId,)).fetchall()
    tagIds = []
    for tag in tagIds_temp:
        id = tag[0]
        tagIds.append(id)
    ingredientIds_temp = c.execute("SELECT ingredientId FROM pairs WHERE recipeId = (?)", (recipeId,)).fetchall()
    ingredientIds = []
    measureIds = []
    for i in ingredientIds_temp:
        ingId = i[0]
        ingredientIds.append(ingId)
        measureId_temp = c.execute("SELECT MeasureId FROM pairs WHERE recipeId = (?) AND ingredientId = (?)", (recipeId, ingId)).fetchone()
        measureId = measureId_temp[0]
        measureIds.append(measureId)
    c.execute("DELETE FROM recipes WHERE recipeName = (?)", (recipeName,))
    # Fetch all remaining ingredients in pairs table. If there are no other
    # entries of the same ingredient, delete it also from ingredients table
    allIngs_temp = c.execute("SELECT ingredientId FROM pairs").fetchall()
    allIngs = []
    for i in allIngs_temp:
        ing = i[0]
        allIngs.append(ing)
    for i in ingredientIds:
        if i in allIngs:
            pass
        else:
            c.execute("DELETE FROM ingredients WHERE ingredientId = (?)", (i,))
    # Do the same for tags
    # Check all remaining tags.
    remainingTagIds_temp = c.execute("SELECT TagId FROM tagPairs").fetchall() #fetch all remaining TagIds once the recipe has been deleted
    remainingTagIds = []
    for tag in remainingTagIds_temp:
        id = tag[0]
        remainingTagIds.append(id)
    print('remaining: ',remainingTagIds)
    print('tagIds from deleted recipe: ', tagIds)
    for id in tagIds:
        if id in remainingTagIds or id in [1, 2, 3, 4]:
            pass
        else:
            c.execute("DELETE FROM tags WHERE TagId = (?)", (id,))
    # Do the same for measures
    allMeasures_temp = c.execute("SELECT MeasureId FROM pairs").fetchall()
    allMeasures = []
    for i in allMeasures_temp:
        measureN = i[0]
        allMeasures.append(measureN)
    for i in measureIds:
        if i in allMeasures or i in [1,2,3,4]: # do not delete default measures (g, Kg, ml, L)
            pass
        else:
            c.execute("DELETE FROM measures WHERE MeasureId = (?)", (i,))
    conn.commit()
    conn.close()
    if App.get_running_app().root.current == 'result':
        instance.popup.dismiss()
        App.get_running_app().root.transition.direction = 'right'
        App.get_running_app().root.current = 'main'


def fetchIngredients(ingInput):
    '''
    lookup all ingredients with similar name (same root)
    '''
    dbInit() 
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    ingsList_temp = c.execute("SELECT IngredientName FROM ingredients WHERE IngredientName LIKE (?)", (ingInput+'%',)).fetchall()
    conn.close()
    ingsList = []
    for i in ingsList_temp:
        ingsList.append(i[0])
    return sorted(ingsList)

def fetchMeasures():
    dbInit()
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    measures_temp = c.execute("SELECT MeasureName FROM measures").fetchall()
    conn.close()
    measures = []
    for i in measures_temp:
        measures.append(i[0])
    return measures

def fetchRecipe(nameInput, full=False):
    '''
    Fetch recipe details by name (Exact match)
        Option 'full':
            = False: returns the joint ingsQuantsList (e.g. 'ing1, 50 ml'). This is the default.
            = True: returns ingsList, quant_numbers and measures (e.g. 'ing1', '50', 'ml').
    ''' 
    recipeName = nameInput.lower()
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    # Select recipeId and use it to retrieve all other details
    recipeId_temp = c.execute("SELECT recipeId FROM recipes WHERE recipeName = (?)", (recipeName,)).fetchone()
    recipeId = recipeId_temp[0]
    
    # retrieve tags
    tagIds_temp = c.execute("SELECT TagId FROM tagPairs WHERE recipeId = (?)", (recipeId,)).fetchall()
    tagsList = []
    for temp in tagIds_temp:
        tagId = temp[0]
        tag_temp = c.execute("SELECT TagName FROM tags WHERE TagId = (?)", (tagId,)).fetchone()
        tag = tag_temp[0]
        tagsList.append(tag)
    # steps
    steps_temp = c.execute("SELECT Steps FROM recipes WHERE recipeName = (?)", (recipeName,)).fetchone()
    steps = steps_temp[0]
    # preparation time
    prepTime_temp = c.execute("SELECT PrepTime FROM recipes WHERE recipeName = (?)", (recipeName,)).fetchone()
    prepTime = prepTime_temp[0] if prepTime_temp != None else None
    # ingredients, quantities and measures
    ingsIds_temp = c.execute("SELECT ingredientId FROM pairs WHERE recipeId = (?)", (recipeId,)).fetchall()
    measureIds_temp = c.execute("SELECT MeasureId FROM pairs WHERE recipeId = (?)", (recipeId,)).fetchall()
    ingsList = {}
    quants = {}
    measures = {}
    ingsQuantsList = {} # single string containing ingredient, quantity and measure (for display purposes)
    i = 0
    for i in range(0, len(ingsIds_temp)):
        ingId_temp = ingsIds_temp[i]
        ingId = int(ingId_temp[0])
        ingName_temp = c.execute("SELECT ingredientName FROM ingredients WHERE ingredientId = (?)", (ingId,)).fetchone()
        ingName = str(ingName_temp[0])
        ingsList[i] = ingName
        quant_temp = c.execute("SELECT Quantity FROM pairs WHERE  ingredientId = (?) AND recipeId = (?)", (ingId, recipeId)).fetchone()
        quants[i] = quant_temp[0] or 0
        measureId_temp = measureIds_temp[i]
        measureId = measureId_temp[0]
        measure_temp = c.execute("SELECT MeasureName FROM measures WHERE measureId = (?)", (measureId,)).fetchone()
        measures[i] = measure_temp[0] or ''
        str_quant = str(quants[i]) if quants[i] != 0 else ''
        if type(measures[i]) is int:
            measures[i] = str(measures[i])
        ingsQuantsList[i] = (ingsList[i] + ",     " + str_quant + " " + measures[i])
    portions_temp = c.execute("SELECT portions FROM pairs WHERE recipeId = (?)", (recipeId,)).fetchone()
    portions = portions_temp[0] if portions_temp[0] != None else 1
    conn.close()
    if full == True:
        return recipeName, portions, prepTime, tagsList, ingsList, quants, measures, steps
    else:
        return recipeName, portions, prepTime, tagsList, ingsQuantsList, steps


def fetchRecipesAll(textinput):
    '''
    Fetch all recipes containing recipe name, tag or ingredient name from textinput
    '''
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()

    # Fetch all recipes with similar name
    recipesList_temp = c.execute("SELECT recipeName FROM recipes WHERE recipeName LIKE (?)", ('%'+textinput+'%',)).fetchall()
    recipesList = []
    for i in recipesList_temp:
        recipesList.append(i[0])

    # Fetch all recipes containing ingredients with similar name
    ingredientIds = c.execute("SELECT ingredientId FROM ingredients WHERE ingredientName LIKE (?)", ('%'+textinput+'%',)).fetchall()
    for i in ingredientIds:
        recipeIds = c.execute("SELECT recipeId FROM pairs WHERE ingredientId = (?)", (i[0],)).fetchall()
        for n in recipeIds:
            recipeNames = c.execute("SELECT recipeName FROM recipes WHERE recipeId = (?)", (n[0],)).fetchall()
            for recipe in recipeNames:
                if recipe[0] not in recipesList:
                    recipesList.append(recipe[0])

    # Fetch all recipes containing tags with similar name
    tagIds = c.execute("SELECT TagId FROM tags WHERE TagName LIKE (?)", (textinput+'%',)).fetchall()
    for id in tagIds:
        recipeIds = c.execute("SELECT recipeId FROM tagPairs WHERE TagId = (?)", (id[0],)).fetchall()
        for rId in recipeIds:
            recipeNames = c.execute("SELECT recipeName FROM recipes WHERE recipeId = (?)", (rId[0],)).fetchall()
            for recipe in recipeNames:
                if recipe[0] not in recipesList:
                    recipesList.append(recipe[0])
    conn.close()
    return sorted(recipesList)

def fetchTags():
    '''
    Fetch all tag names in db
    '''
    dbInit()
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    tags_temp = c.execute("SELECT TagName FROM tags").fetchall()
    conn.close()
    tags = []
    for tag in tags_temp:
        tags.append(tag[0])
    return sorted(tags)


def recipeExists(searchInput):
    '''
    Return true if recipe exists in db
    '''   
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    matchFound = bool(c.execute("SELECT RecipeName FROM recipes WHERE RecipeName = (?)", (searchInput,)).fetchone())
    conn.close()
    return matchFound


def saveRecipe(instance, oldName, newName, portions, prepTime, tagsList, ingsList, quants, measures, steps, newRecipe=True):
    '''
    Save recipe into db
    '''  
    recipeName = newName
    if newRecipe == False:# if editing a recipe, delete existing record and save again (with new name)
        deleteRecipe(instance, oldName)
        instance.editPopup.dismiss()

    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    c.execute("INSERT INTO recipes (RecipeName, Steps, PrepTime) VALUES (?, ?, ?)", (recipeName, steps, prepTime))
    recipeId_temp = c.execute("SELECT RecipeId FROM recipes WHERE RecipeName = (?)", (recipeName,)).fetchone()
    recipeId = recipeId_temp[0]
    tag_pairs = []
    for tagName in tagsList:
        c.execute("INSERT INTO tags (tagName) VALUES (?)", (tagName,))
        tagId_temp = c.execute("SELECT tagId FROM tags WHERE tagName = (?)", (tagName,)).fetchone()
        tagId = tagId_temp[0]
        tag_pairs.append([recipeId, tagId])
    print('saving tag_pairs: ',tag_pairs)
    c.executemany("INSERT INTO tagPairs (RecipeId, TagId) VALUES (?, ?)", tag_pairs)
    pairs = [] # Combinations of RecipeId, IngredientId, Quantity, MeasureId
    for i in range(0, len(ingsList), 1):
        c.execute("INSERT INTO ingredients (IngredientName) VALUES (?)", (ingsList[i],))
        ingId_temp = c.execute("SELECT IngredientId FROM ingredients WHERE IngredientName = (?)", (ingsList[i],)).fetchone()
        ingId = ingId_temp[0]
        c.execute("INSERT INTO measures (MeasureName) VALUES (?)", (measures[i],))
        measureId_temp = c.execute("SELECT MeasureId FROM measures WHERE MeasureName = (?)", (measures[i],)).fetchone()
        measureId = measureId_temp[0]
        pairs.append([recipeId, ingId, quants[i], measureId, portions]) #list of lists
    c.executemany("INSERT INTO pairs (RecipeId, IngredientId, Quantity, MeasureId, Portions) VALUES (?, ?, ?, ?, ?)", pairs)
    conn.commit()
    conn.close()
    instance.exitFlag = True
    if App.get_running_app().root.current == 'add' and newRecipe==False and instance.exitFlag==True:
        instance.savePopup.open()
    print("[RECIPAPP] The recipe was saved successfully")
    return False
