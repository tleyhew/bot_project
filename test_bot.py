import discord
import logging
import sys
import json
import datetime
from discord.ext import commands

try: #Do we have a client token? If we don't, shut down
  token_file = open("./resources/bot_token.txt", "r")
except:
  print ("No client token found. Can't log in to discord without one, boss.")
  quit()

bot_token = token_file.read()

#logging.basicConfig(level=logging.INFO)

#Set up some logging. I don't really know what I'm doing, but this 
#is what professionals do, so here we are.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='UTF-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot_std_out = open('bot_std_out.txt', 'a')
sys.stdout = bot_std_out

special_names = ['everyone', 'the house', 'here','me'] #These 'users' are always present
server_roles_m = ["Bartender", "Barboy", "Barkeep"]    #Male server roles
server_roles_f = ["Alewife", "Coffee Mom", "Meido"]    #Female server roles
server_roles_n = ["Server","Barstaff"]                 #Neuter server roles
minor_roles = ["Minor", "Underage"]

try: #If we don't have the drink list, why bother?
  drink_file = open("./resources/drinklist.json", "r",encoding="utf-8") 
except:
  print ("Drink list not found")
  quit()

drink_string = drink_file.read() # load and parse the JSON
drink_file.close()
drink_list = json.loads(drink_string)

#print (json.dumps(drink_list)) #turn this on if you need to test it.
#print (drink_list.keys())
#print(type(drink_list))

   

#build the bot framework
intentions = discord.Intents(guilds=True, members=True, emojis=True, messages=True)
bot = commands.Bot(command_prefix='!bb - ', case_insensitive = True, intents=intentions)

@bot.event
async def on_ready():
   print('We have logged in as {0.user}'.format(bot))
   print(bot.user.id)
   
   for guild in bot.guilds:
      print(guild.name)
      
@bot.command()
async def serve(ctx):
     allowed_to_serve = False #Is the invoking user allowed to serve the drink?
     valid_user = False       #Is the user being served present in the server?
     valid_drink = False      #Is this a real drink?
     self_flag = False        #Is this user serving a drink to themselves?
     all_flag = False         
     serve_pronoun = ''
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
     
     for i in ctx.guild.members: 
         if valid_user == True:
             break            
         
         if i.name.lower() == modified_content[0].strip() or i.display_name.lower() == modified_content[0].strip():
             valid_user = True
             recipient = i
     
     if valid_user == False:
         await ctx.send( "Sorry, but " + modified_content[0].strip() + " is not a valid user.")
                  
         
     for drinks in drink_list.keys():
         if drink_list[drinks].get("name").lower().startswith(modified_content[1].strip()) or drink_list[drinks].get("name").lower().endswith(modified_content[1].strip()) or modified_content[1].strip() in drink_list[drinks].get("name").lower():
            valid_drink = True
            curr_drink = drink_list[drinks]
            #await ctx.send("this is placeholder for a valid drink message")
            break
         else: 
             pass
             
     #print(curr_drink)
     #print(type(curr_drink))
     #print (type(curr_drink['roles']))     
     if valid_drink == False:   
         await ctx.send ("Sorry, but I don't know what a " + modified_content[1].strip() + " is. Try ordering something else.")
         return
     
     if ctx.author.id in curr_drink["users"]:
        allowed_to_serve = True
     else:
         role_list = ctx.author.roles
         #print(role_list)
         allowed_roles = ["Bartender","Barkeep","Alewife","Server","Barstaff"]
         allowed_roles + curr_drink["roles"]
         #print(allowed_roles)
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
         elif role.name in server_roles_f:
            serve_pronoun = 'herself'
         elif role.name in server_roles_n:
            serve_pronoun = 'themselves'
     
     if curr_drink["alcoholic"] and not self_flag:
         for r in recipient.roles:
            if r.name in minor_roles:
                await ctx.send("Sorry, " + ctx.author.display_name + ", but " + recipient.display_name + " is not old enough to consume alcoholic beverages.")
                return
                     
     
     
     embed = build_embed(ctx, recipient, curr_drink, serve_pronoun, self_flag, all_flag)
     #await ctx.send(ctx.author.display_name + ' pours ' + recipient.display_name + ' a/an ' + curr_drink["name"])
     await ctx.send(embed=embed)
     return
    

        
@bot.command()
async def menu(ctx):
    await ctx.send('This is a placeholder for the menu interface')
    
      
@bot.command()
async def test(ctx):    
    await ctx.send(ctx.message.content)
    print (ctx.send(ctx.message.content))
    
@bot.command()
async def zork(ctx):
    await ctx.send('It is pitch black. You are likely to be eaten by a grue.')
    
@bot.command()
async def nethack(ctx):
     await ctx.send('Who do you think you are, War?')
    
    
def build_embed(ctx, recipient, curr_drink, serve_pronoun, self_flag, all_flag):

     article = ' a '
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
     print(embed.fields)
     return embed


def starts_with_vowel(in_string):
    vowel = 'a','e','i','o','u'
    if in_string.startswith(vowel):
        return True
    else:
        return False


bot.run(bot_token)