import discord
import logging
import sys
import json
import datetime
import math
import unicodedata
import datetime
from discord.ext import commands
import configLoader
import drinkLoader


try:  # If we don't have the drink list, why bother?
    config_file = open("./resources/config.json", "r", encoding="utf-8")
except:
    print("Configuration File Not Found")
    quit()

config = json.load(config_file)  # load and parse the JSON
config_file.close()

configLoader.validateConfig(config)

try: #Do we have a client token? If we don't, shut down
  token_file = open("./resources/bot_token.txt", "r")
except:
  print ("No client token found. Can't log in to discord without one, boss.")
  quit()


try: #If we don't have the drink list, why bother?
  drink_file = open("./resources/drinklist.json", "r",encoding="utf-8") 
except:
  print ("Drink list not found")
  quit()


bot_token = token_file.read()

drink_string = drink_file.read() # load and parse the JSON
drink_file.close()
drink_list = json.loads(drink_string)

drinkLoader.validateDrinkList(drink_list)
drink_categories = drinkLoader.generateCategories(drink_list)
drink_keys = drink_list.keys()
sorted_drink_keys = sorted(drink_keys)

#Set up some logging. I don't really know what I'm doing, but this 
#is what professionals do, so here we are.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='UTF-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot_std_out = open('bot_std_out.txt', 'a',encoding='UTF-8')
sys.stdout = bot_std_out

special_names = ['everyone', 'the house', 'here','me'] #These 'users' are always present
server_roles_m = ["Bartender", "Barboy", "Barkeep"]    #Male server roles
server_roles_f = ["Alewife", "Coffee Mom", "Meido"]    #Female server roles
server_roles_n = ["Server","Barstaff"]                 #Neuter server roles
minor_roles = ["Minor", "Underage"]
#drink_categories = ["all","beers","cocktails","hot coffee","iced coffee","spirits","tea","miscellaneous"]
menu_page_size = config["menu_page_size"]
menu_num_pages = 0
menu_list = []



drink_keys = drink_list.keys()
sorted_drink_keys = sorted(drink_keys)
#print (json.dumps(drink_list)) #turn this on if you need to test it.

#menu_list_keys = dict.fromkeys(drink_categories, list())

categorized_key_list = { key : list() for key in drink_categories}

for x in sorted_drink_keys:
     #print(drink_list[x].get("category"))
     categorized_key_list[drink_list[x].get("category")].append(x)
     
#print (categorized_key_list)

categorized_menus = { key : list() for key in drink_categories}


def build_menu_list():  #this has to go here, because python won't let me forward declare it,
     menu_num_pages  = math.ceil(len(drink_keys)/menu_page_size)#but I also can't call it before it's declared. Python, man. 
     #print(len(drink_keys))
     #print(menu_num_pages)
     sorted_drink_keys = sorted(drink_keys)
     drink_counter = 0
     return_list = []
     #this builds the primary list, that contains all drinks
     for x in range(menu_num_pages):
         title_string = "Menu Page " + str((x + 1))
         curr_embed = discord.Embed(title=title_string,color=0xffffff)
         for i in range(menu_page_size):
             drink_name = drink_list[sorted_drink_keys[drink_counter]].get("name")
             drink_desc = drink_list[sorted_drink_keys[drink_counter]].get("menudesc")
             curr_embed.add_field(name=drink_name, value=drink_desc, inline=False)
             curr_embed.set_footer(text=str(x + 1))
             drink_counter+=1
             if drink_counter == len(drink_keys):
                 break
         return_list.append(curr_embed)
         
         
     for cat in categorized_key_list.keys():
         menu_num_pages  = math.ceil(len(categorized_key_list.get(cat))/menu_page_size)
         #print (cat + ' ' + str(menu_num_pages))
         drink_counter = 0
         for x in range (menu_num_pages):
             title_string = cat.capitalize().replace("_"," ") + " Menu Page " + str((x + 1))
             #print(title_string)
             curr_embed = discord.Embed(title=title_string,color=0xffffff)
             for i in range(menu_page_size):
                 drink_name = drink_list[(categorized_key_list.get(cat))[drink_counter]].get("name")
                 drink_desc = drink_list[(categorized_key_list.get(cat))[drink_counter]].get("menudesc")
                 curr_embed.add_field(name=drink_name, value=drink_desc, inline=False)
                 curr_embed.set_footer(text=str(x + 1))
                 drink_counter+=1
                 if drink_counter == len(categorized_key_list.get(cat)):
                     break
                 
             categorized_menus[cat].append(curr_embed)
     return return_list   

#build the bot framework
intentions = discord.Intents(guilds=True, members=True, emojis=True, messages=True, reactions=True)
bot = commands.Bot(command_prefix='!bb - ', case_insensitive = True, intents=intentions)

menu_list = build_menu_list()


@bot.event
async def on_ready():
   print('We have logged in as {0.user}'.format(bot))
   print(bot.user.id)
   
   for guild in bot.guilds:
      print(guild.name)
      
@bot.command(help="""Serves a drink. 
The correct invocation is '!bb - serve [person] - [drink].
Replace [person] with the name of the individual getting the drink, and [drink] with the name of the beverage in question""",
             brief="Serves a drink to a thirsty soul")
async def serve(ctx):
     allowed_to_serve = False #Is the invoking user allowed to serve the drink?
     valid_user = False       #Is the user being served present in the server?
     valid_drink = False      #Is this a real drink?
     self_flag = False        #Is this user serving a drink to themselves?
     all_flag = False         #Are they serving the house?
     serve_pronoun = ''       #himself, herself, or themselves?
     role_list = []
     recipient = ''
     content = ctx.message.content #get the text
     modified_content = content.lower().replace('!bb - serve','',1).split('-') #strip out the formatting

     for i in special_names: #Is the target one of the always-present users?
         if i in modified_content[0].strip():
             valid_user = True 
             if i == "me":
                 self_flag = True
             else:
                 all_flag = True
             break
     
     if not valid_user:
         mention_list = ctx.message.mentions
         if len(mention_list) == 1:
             recipient = mention_list[0]
             valid_user = True
         elif len(mention_list) >= 2:
             await ctx.send("Sorry, but you mentioned more than one user in this request. Please make two separate requests.")
     
     for i in ctx.guild.members: #This tries to match on account name and on
         if valid_user == True:  #display name. Haven't decided what to do if multiple users
             break               #share a name
         
         if modified_content[0].strip() in i.name.lower() or modified_content[0].strip() in i.display_name.lower():
             valid_user = True
             recipient = i
     
     if valid_user == False:
         await ctx.send( "Sorry, but " + modified_content[0].strip() + " is not a valid user.")
         return
     
     if recipient != '' and not self_flag:
         if ctx.author.id == recipient.id:
                 self_flag = True
         
     sorted_drink_keys = sorted(drink_keys)
     try:
     #need to catch an index error here.    
         for drinks in sorted_drink_keys: #drink_list.keys(): #moderately fuzzy string matching
             if (drink_list[drinks].get("name").lower().startswith(modified_content[1].strip()) 
             or drink_list[drinks].get("name").lower().endswith(modified_content[1].strip()) 
             or modified_content[1].strip() in drink_list[drinks].get("name").lower()):
                 valid_drink = True
                 curr_drink = drink_list[drinks]
                 #await ctx.send("this is placeholder for a valid drink message")
                # print (curr_drink)
                 break
             else: 
                 pass
     except IndexError:
         await ctx.send("That command was incorrectly formatted. Please include the '-'.")
         return
                 
     if valid_drink == False:   
         await ctx.send ("Sorry, but we don't have " + modified_content[1].strip() + " in this establishment.")
         return
      
     allowed_roles = []      
     if "Coffee Mom" in curr_drink["roles"]:
         allowed_roles = curr_drink["roles"]
     elif "Meido" in curr_drink["roles"]:
         allowed_roles = curr_drink["roles"]   
     else:    
         allowed_roles = ["Bartender","Barkeep","Alewife","Server","Barstaff"] 
     role_list = ctx.author.roles   
     #print(ctx.author.id)
     if ctx.author.id == int('316005415211106305'): #316005415211106305
         allowed_to_serve = True
         #print(allowed_to_serve)
     elif ctx.author.id in [int(x) for x in curr_drink["users"]]: #Someone who suggests a drink can always serve it,
         allowed_to_serve = True               #regardless of role   
        # print(allowed_to_serve)           
     else:
         role_list = ctx.author.roles #Does the invoker have a role that can serve this drink
         print (role_list)
         #allowed_roles = ["Bartender","Barkeep","Alewife","Server","Barstaff"]
         #allowed_roles = allowed_roles + curr_drink["roles"]
         #print (allowed_roles)
         for r in role_list:
             if r.name in allowed_roles:
                allowed_to_serve = True
                break

     if allowed_to_serve == False:
         await ctx.send("Sorry, " + ctx.author.display_name + ", but you aren't allowed to serve that.")
         return
    
     for role in role_list:
         if role.name in server_roles_m:
            serve_pronoun = 'himself'
            break
         elif role.name in server_roles_f:
            serve_pronoun = 'herself'
            break
         elif role.name in server_roles_n:
            serve_pronoun = 'themselves'
            break
         else:
             serve_pronoun = 'themselves'
     
     if curr_drink["alcoholic"] and not self_flag and not all_flag: #Is the recipient tagged as a minor?
         for r in recipient.roles:
             if r.name in config["minor_roles"]:
                 await ctx.send("Sorry, " + ctx.author.display_name + ", but " + recipient.display_name + " is not old enough to consume alcoholic beverages.")
                 return
                     
     
     #TO DO: put error handling here for when the image is missing.
     embed = build_embed(ctx, recipient, curr_drink, serve_pronoun, self_flag, all_flag)
     
     try:
         msg = await ctx.channel.send(embed=embed)  
     except discord.HTTPException as error:
         print (curr_drink["name"])
         print(error.text + ' ' + str(error.status) + ' ' + str(error.code))
         err_string = error.text.split(".")
         print(embed.fields[int(err_string[2])])
         await ctx.channel.send("I'm sorry, but we seem to be out of the ingredients for " + curr_drink["name"] + ". Our staff is working on it. Would you like something else?")
         
     return
    

        
@bot.command(help="""Shows a menu. Use the arrow reacts to page through. React with an X emote to close the menu.
You can bring up a more specific menu by invoking the command with a category name, a page number, or both.""",
             brief="Displays a list of the beverages available in this establishment")
async def menu(ctx, *args):
     if len(args) == 0:
         category = "all"
         page_no = 1
     elif len(args) == 1:
         if args[0].isdigit():
             page_no = abs(int(args[0]))
             category = "all"
         elif isinstance(args[0], str):
             if args[0].lower() in drink_categories:
                 category = args[0].lower()
                 page_no = 1
             else:
                 await ctx.send("I'm sorry, but that is not a category of drink that we serve here")
                 return
         else:
             await ctx.send("I'm sorry, but that command was garbled and I am not sure what to make of it. Please try again.")
             return
     elif len(args) == 2:
         if args[0].isdigit() and isinstance(args[1], str):
             if args[1].lower() in drink_categories:
                 page_no = int(args[0])
                 category = args[1].lower()
             else:
                 await ctx.send("I'm sorry, but that is not a category of drink that we serve here")
                 return
         elif isinstance(args[0], str) and args[1].isdigit():
             if args[0].lower() in drink_categories:
                 page_no = int(args[1])
                 category = args[0].lower()
             else:    
                 await ctx.send("I'm sorry, but that is not a category of drink that we serve here")
                 return
         else:
             await ctx.send("I'm sorry, but that command was garbled and I am not sure what to make of it. Please try again.")
             return
     else:    
         await ctx.send("I'm sorry, but that command was garbled and I am not sure what to make of it. Please try again.")
         return
     
     #await ctx.send(category + '  ' + str(page_no))
     if category == "all":
         if page_no > len(menu_list):
             page_num = len(menu_list)
         menu_page = await ctx.send(embed=menu_list[page_no - 1])
     else:
         if page_no > len (categorized_menus.get(category.lower())):
             page_no = len (categorized_menus.get(category.lower()))
         menu_page = await ctx.send(embed = categorized_menus.get(category.lower())[page_no - 1])     
     #print(menu_page.id)
     await menu_page.add_reaction("\N{BLACK LEFT-POINTING TRIANGLE}")  #"\N{BLACK LEFT-POINTING TRIANGLE}"
     await menu_page.add_reaction("\N{BLACK RIGHT-POINTING TRIANGLE}")  #"\N{BLACK RIGHT-POINTING TRIANGLE}"

    
@bot.command()
async def suggest(ctx):
    await ctx.send('This will eventually be how drinks are added.')
    
    
@bot.command(help="Displays all valid drink categories.",
             brief="Displays all valid drink categories.")
async def categories(ctx):
     msg = "The valid categories are:\n"
     for x in drink_categories:
         msg+= (x + "\n")
     
     msg += "Use quotes around the multi word category names"
     await ctx.send(msg)     
    
      
@bot.command(hidden=True)
async def test(ctx):    
    await ctx.send(ctx.message.content)
    print (ctx.message.content)
    
@bot.command(hidden=True) #Some easter eggs
async def zork(ctx):
    await ctx.send('It is pitch black. You are likely to be eaten by a grue.')
    
@bot.command(hidden=True)
async def nethack(ctx):
     await ctx.send('Who do you think you are, War?')
     
     
@bot.event  
async def on_reaction_add(reaction, user):
     cur_page_no = 0
     next_page_no = 0
     if user.id == bot.user.id:
        return
     elif len(reaction.message.embeds) == 0:
        return
     elif reaction.message.embeds[0].footer == discord.Embed.Empty:
        return
     else:
         if isinstance(reaction.emoji, str):
             emote = unicodedata.name(reaction.emoji[0])
             #print (emote)
         else:
             return
             
         if reaction.message.embeds[0].title.startswith("Menu Page"):
             curr_menu = menu_list
         else:
             for x in drink_categories:
                 if reaction.message.embeds[0].title.lower().startswith(x.lower()):
                     curr_menu = categorized_menus[x]
         
         if emote == "BLACK LEFT-POINTING TRIANGLE":
             cur_page_no = reaction.message.embeds[0].footer
             next_page_no = int(cur_page_no.text) - 1
             if next_page_no == 0:
                next_page_no = len(curr_menu)
             await reaction.message.clear_reactions()
             await reaction.message.edit(embed=curr_menu[next_page_no - 1])
             await reaction.message.add_reaction("\N{BLACK LEFT-POINTING TRIANGLE}")  #"\N{BLACK LEFT-POINTING TRIANGLE}"
             await reaction.message.add_reaction("\N{BLACK RIGHT-POINTING TRIANGLE}")  #"\N{BLACK RIGHT-POINTING TRIANGLE}"
             
         elif emote == "BLACK RIGHT-POINTING TRIANGLE":
             cur_page_no = reaction.message.embeds[0].footer
             next_page_no = int(cur_page_no.text) + 1
             if next_page_no > len(curr_menu):
                next_page_no = 1
             await reaction.message.clear_reactions()
             await reaction.message.edit(embed=curr_menu[next_page_no - 1])
             await reaction.message.add_reaction("\N{BLACK LEFT-POINTING TRIANGLE}")  #"\N{BLACK LEFT-POINTING TRIANGLE}"
             await reaction.message.add_reaction("\N{BLACK RIGHT-POINTING TRIANGLE}")  #"\N{BLACK RIGHT-POINTING TRIANGLE}"
         
         elif emote == "CROSS MARK":
             await reaction.message.delete()
    
def build_embed(ctx, recipient, curr_drink, serve_pronoun, self_flag, all_flag):

     article = ' a ' #This is a hack job, but it should be fine
     if starts_with_vowel(curr_drink["name"]):
        article = ' an '

     if self_flag == True:
        title_string = ctx.author.display_name + ' pours ' + serve_pronoun + article + curr_drink["name"]
     elif all_flag == True:
        title_string = ctx.author.display_name + ' pours the House a round of ' + curr_drink["name"]
     else:
        title_string = ctx.author.display_name + ' pours ' + recipient.display_name + article + curr_drink["name"]
        
     picture_url = curr_drink["pic"]
     
     embed = discord.Embed(title=title_string, color=0xffffff, description=curr_drink["desc"])
     embed.set_image(url=picture_url)
     embed.add_field(name="So, what's in the glass?", value=curr_drink["menudesc"],inline=False)
     embed.add_field(name="suggested by", value=curr_drink["by"],inline=False)
     #print(embed.fields)
     return embed


def starts_with_vowel(in_string):
    vowel = 'a','e','i','o','u'
    if in_string.lower().startswith(vowel):
        return True
    else:
        return False



bot.run(bot_token)
