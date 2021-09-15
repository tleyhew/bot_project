import re

def generateCategories(drink_list):
    #Holder for final list
    #Dictionary holds number of times this category was seen, for future stats
    categorylist_dedupe = []

    #Create a list of categories without the rest of the data, non-deduplicated
    category_list = list(map(lambda x: x[1]["category"], drink_list.items()))

    #Deduplicate the list
    for category in category_list:
        if not category in categorylist_dedupe:
            categorylist_dedupe += [category]
        
    #Return just the keys for now
    return categorylist_dedupe

def validateDrink(drinkname, drink):
    #Check that the index has no spaces     
    assert re.match("\w+",drinkname)
    
    #Check that we have a name and it's a string
    assert "name" in drink
    assert type(drink["name"]) is str

    #Check that we have an alcoholic key and it's a bool
    assert "alcoholic" in drink
    assert type(drink["alcoholic"]) is bool

    #Check that we have a pic and that it's a str
    assert "pic" in drink
    assert type(drink["pic"]) is str

    #Check that we have an author
    assert "by" in drink
    assert type(drink["by"]) is str

    #Check that we have a menu desc
    assert "menudesc" in drink
    assert type(drink["menudesc"]) is str

    #Check that we have a description
    assert "desc" in drink
    assert type(drink["desc"]) is str

    #Check that we have a roles key
    assert "roles" in drink
    assert type(drink["roles"]) is list

    #Check that we have a users key
    assert "users" in drink
    assert type(drink["users"]) is list


def validateDrinkList(drink_list):
    for drinkname in drink_list: 
        validateDrink(drinkname,drink_list[drinkname])