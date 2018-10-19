#!/usr/bin/env python3

import discord
import asyncio
import sys
import requests
import json
import gspread
import time
import re
import datetime
import cv2
from pyvirtualdisplay import Display
from selenium import webdriver
from oauth2client.service_account import ServiceAccountCredentials
from gspread import CellNotFound

client = discord.Client()

admin_channel = "<unique discord admin channel number>"

api_key = "<riot game api key>"

current_users = []
global gc
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('Brunel Esport Sheet.json',scope)
gc = gspread.authorize(credentials)

#Sends message to admin channel
async def admin_notif(server,string):

    channel = server.get_channel(admin_channel)
    await client.send_message(channel,string)

#Used as part of google sheets authentcation

def google_auth(current_key):    

    if current_key.auth.access_token_expired is True:
        print("Google Token Expired")
        global gc       
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('Brunel Esport Sheet.json',scope)
        gc = gspread.authorize(credentials)
        time.sleep(2)
        print("Refreshed Key")
    else:
        print("Key is still valid")    

#api calls to get and return league rank
def check_league_rank(ign):
    reponse_id = requests.get("https://euw1.api.riotgames.com/lol/summoner/v3/summoners/by-name/" + ign + "?api_key=" + api_key)
    json_data_id = json.loads(reponse_id.text)
    playerid = json_data_id["id"]

    response_rank = requests.get("https://euw1.api.riotgames.com/lol/league/v3/positions/by-summoner/" + str(playerid) + "?api_key=" + api_key)
    json_data_rank = json.loads(response_rank.text)
    for i in json_data_rank:
        if str(i["queueType"]) == "RANKED_SOLO_5x5":
            tier = i["tier"].lower().title()            
            rank = i["rank"]
    return tier, rank


#api call to get overwatch rank
def check_overwatch_rank(battletag):
    searchObj = re.match(r'([a-zA-Z0-9]+)#([0-9]+)', battletag, re.M|re.I)

    battletag = searchObj.group(1) + "-" + searchObj.group(2)

    reponse_id = requests.get("https://ow-api.com/v1/stats/pc/eu/" + str(battletag) + "/profile")
    json_data_id = json.loads(reponse_id.text)
    rank = json_data_id["ratingName"]

    if rank is "":
        rank = "Unranked"

    return rank


#api call to get dota2 rank
def check_dota_rank(steam_id):
    dota_ranks = ["Herald", "Guardian", "Crusader", "Archon", "Legend", "Ancient", "Divine", "Immortal"]
    
    try:
        api_response = requests.get("https://api.opendota.com/api/players/" + steam_id)
    except ValueError:
        print("error")
    json_data = json.loads(api_response.text)
    rank_tier = json_data["rank_tier"]
    
    str_rank = str(rank_tier)    
    rank = dota_ranks[int(str_rank[0])-1]
    sub_rank = str_rank[1]    

    return rank, sub_rank


# Adds users information into a public google doc
def add_to_google_doc(brunel_id, name, discord_name, league_ign, league_rank, battletag, overwatch_rank, cs_rank, dota_rank,steam_id, steam_link):
    #Google sheets authentication
    global gc
    google_auth(gc)
    wks = gc.open('Brunel Society Members').sheet1
    wks.append_row([brunel_id, name, discord_name, league_ign, league_rank, battletag, overwatch_rank,cs_rank,dota_rank,steam_id, steam_link])

#Overwrites users information in the public google doc
def overwrite_google_doc(row, brunel_id, name, discord_name, league_ign, league_rank, battletag, overwatch_rank, cs_rank, dota_rank,steam_id, steam_link):
    global gc
    google_auth(gc)
    wks = gc.open('Brunel Society Members').sheet1
    range_build = 'A' + str(row) + ':K'+ str(row)
    cell_list = wks.range(range_build)
    cell_list[0].value = brunel_id
    cell_list[1].value = name
    cell_list[2].value = discord_name
    cell_list[3].value = league_ign
    cell_list[4].value = league_rank
    cell_list[5].value = battletag
    cell_list[6].value = overwatch_rank
    cell_list[7].value = cs_rank
    cell_list[8].value = dota_rank
    cell_list[9].value = steam_id
    cell_list[10].value = steam_link
    

    wks.update_cells(cell_list)

#Verifies that the student id number is in the members list
def verify_brunel_id(brunel_id):
    global gc
    google_auth(gc)
    sh = gc.open('Brunel Society Members')
    wks = sh.get_worksheet(1)

    try:
        wks.find(brunel_id)
    except CellNotFound:
        return False

    return True

#Gets the users brunel id number
def get_brunel_id(discord_name):
    global gc
    google_auth(gc)
    wks = gc.open('Brunel Society Members').sheet1

    try:
        cell = wks.find(discord_name)
        i = cell.row
        return wks.cell(i,1).value
    except:
        return False
    
    
#Gets the row the user is in the google sheet
def find_row(discord_name):
    global gc
    google_auth(gc)
    wks = gc.open('Brunel Society Members').sheet1
    try:
        cell = wks.find(discord_name)
        i = cell.row
        return i
    except:
        return False      

#Updates there competative rank on the google sheet
async def updateranks(discord_name,message):
    global gc
    google_auth(gc)
    wks = gc.open('Brunel Society Members').sheet1

    try:
        cell = wks.find(discord_name)
        i = cell.row        
    except:
        await client.send_message(message.channel, "Your account is not currently set up. Please use `!signup` in *#welcome*.")
        return    
        
    league_ign = wks.cell(i,4).value            
    old_league_rank = wks.cell(i,5).value
    battletag = wks.cell(i,6).value
    old_ow_rank = wks.cell(i,7).value
    dota_num = wks.cell(i,10).value
    old_dota_rank = wks.cell(i,9).value

    if league_ign != "N/A":
        league_tier, league_div = check_league_rank(league_ign)
        league_rank = league_tier + " " + league_div
        wks.update_cell(i,5,league_rank)
        await client.send_message(message.channel, "In League you have gone from " + old_league_rank + " to " + league_rank + ".")
    if battletag != "N/A":
        ow_rank = check_overwatch_rank(battletag)
        wks.update_cell(i,7,ow_rank)
        await client.send_message(message.channel, "In Overwatch you have gone from " + old_ow_rank + " to " + ow_rank + ".")
    if dota_num != "N/A":
        dota_tier, dota_sub_tier = check_dota_rank(dota_num)
        dota_rank = dota_tier + " " + dota_sub_tier
        wks.update_cell(i,9,dota_rank)
        await client.send_message(message.channel, "In Dota 2 you have gone from " + old_dota_rank + " to " + dota_rank + ".")            

    return

#Checks that the bot command has not been typed to the bot directly and has only been used in the server channel
def message_checker(message):
    try:
        server_tester = message.author.server
    except AttributeError:        
        return False
    return True

#function returns user input
def check_dm(msg):
    if msg.content.startswith('!exit'):      
        raise AttributeError 
    elif msg.server is None:
        return msg.content.startswith('')       

#function returns user input
def check(msg):    
    return msg.content.startswith('')

#signup function asks the user a variety of questions of what games they play and assign correct roles and permission accordingly as well as adding there info to the google sheet
async def signup(client,member):
    
    global gc
    google_auth(gc)

    discord_username = member.name + "#" + member.discriminator

    current_users.append(str(member))    
    
    ign = "N/A"
    league_rank = "N/A"
    battletag = "N/A"
    overwatch_rank = "N/A"
    cs_rank = "N/A"
    steam_id = "N/A"
    dota_rank = "N/A" 
    steam_link = "N/A"

    
    attempt = 0
    old_roles = []

    overwrite = find_row(discord_username)    
    
    if overwrite is not False:        
        for role in member.roles:
            old_roles.append(str(role))        
        old_roles.remove("@everyone")
        if "Admin" in old_roles: old_roles.remove("Admin")
        if "Reps" in old_roles: old_roles.remove("Reps")           

    # Greeting message
    await client.send_message(member, "Hello, this is Brunel Esports bot. \nI am going to ask a few questions to get you set up for our server. \nYou can use `!exit` in this chat to quit at any time.")
    
    while attempt < 2:
        await client.send_message(member,"Please tell me your Brunel Student ID followed by your full name. \n*Example:* `1234 John Smith`")
        
        try:
            name_questions_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)            
        #load user input from function and assign to a variable               
            message_content = name_questions_response.content            
        except AttributeError:
            await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
            current_users.remove(str(member))
            return        

        try:
            searchObj = re.match(r'([0-9]+) (.*)', message_content, re.M|re.I)
            brunel_id = searchObj.group(1)
            full_name = searchObj.group(2)
        except AttributeError:
            await client.send_message(member, "Invalid input.")
            attempt += 1
            continue

        verified_brunel_id = verify_brunel_id(brunel_id)

        if verified_brunel_id == True:
            await client.send_message(member, "Thanks, you have been verified as a member of the Brunel Esports Society! \nFull permissions have been granted to you.")
            role = discord.utils.get(member.server.roles, name="Verified Member")
            await client.add_roles(member, role)
            if "Verified Member" in old_roles: old_roles.remove("Verified Member")            
            break

        else:
            await client.send_message(member, "Thanks, unfortunately you are not a member. Please join using this link: \nhttps://brunelstudents.com/societies/esports/ \nIt can take up to 24 hours to fully process your membership (contact an admin to speed up the process). \nOnce you have joined, type `!verify` in the *#welcome* chat. \nYou have 2 weeks to join the society, after which you will be removed from the server.")
            role = discord.utils.get(member.server.roles, name="Unverified Member")
            await client.add_roles(member, role)           
            if "Unverified Member" in old_roles: old_roles.remove("Unverified Member")
            break

    if attempt == 2:
        await client.send_message(member, "You have entered incorrectly too many times. \n*To edit your information, please contact an admin or redo the process by typing* `!signup`. \nExiting.")
        current_users.remove(str(member))
        return   

    attempt = 0

    await client.send_message(member, "Do you play League of Legends?  *Input options:* `yes/no`")        

    #load user input from function and assign to a variable
    
    try:
        league_questions_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)
        answer_league_question = league_questions_response.content.lower()
    except AttributeError:
        await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
        current_users.remove(str(member))
        return   

    if answer_league_question == "yes":

        if "League of Legends" in old_roles: old_roles.remove("League of Legends")

        league_role = discord.utils.get(member.server.roles, name="League of Legends")
        await client.add_roles(member, league_role)

        while attempt < 2:
            #Asks for in game name for Riot api lookup
            await client.send_message(member, "What is your Summoner Name? \n*Region is assumed to be EUW. If your account is otherwise, please continue as normal and contact an admin to adjust incorrect rank.*")
            
            #load user input from function and assign to a variable
            
            try:
                message = await client.wait_for_message(author=member, check=check_dm,timeout=300)
                ign = message.content
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return   

            try:
            #uses function that returns league rank and assigns to variable
                league_tier, league_div = check_league_rank(ign)
            except KeyError:
                await client.send_message(member, "Unable to find Summoner Name.")
                attempt += 1
                continue
            except UnboundLocalError:
                await client.send_message(member, "Looks like you do not have a rank.")                
                league_tier = "Unranked"
                league_div = ""

            #Returns response to verify rank
            await client.send_message(member, "Your rank is " + league_tier + " " + league_div + ". Is this correct?")

            #load user input from function and assign to a variable            
            try:
                validation_league_rank = await client.wait_for_message(author=member, check=check_dm, timeout=300)
                answer_league_rank = validation_league_rank.content.lower()
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return 

            if answer_league_rank == "yes":                
                #Assign tag based on ranked
                await client.send_message(member, "Good. I will assign this to you as a tag.")
                role = discord.utils.get(member.server.roles, name="League " + league_tier)
                league_rank = league_tier + " " + league_div
                await client.add_roles(member, role)
                if "League " + league_tier in old_roles: old_roles.remove("League " + league_tier)                
                break

            else:
                #Error response - FUTURE DEVELOPMENT: sends a message to me of there name and error message
                await client.send_message(member, "Something has gone wrong. Either your rank hasn't been updated or your Summoner Name was incorrect. \nI'm notifying admins of the issue...")
                await admin_notif(member.server,str(member) + " is having issues sorting out league rank" )
                attempt = 0
                break

        if attempt == 2:
            await client.send_message(member, "You have entered incorrectly too many times. \n*To edit your information, please contact an admin or redo the process by typing* `!signup`. \nI will now ask you a different question.")
            attempt = 0
            league_rank = "N/A"

    attempt = 0

    await client.send_message(member, "Do you play Overwatch? *Input options:* `yes/no`")

    #load user input from function and assign to a variable
    
    try:
        overwatch_questions_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)
        answer_overwatch_question = overwatch_questions_response.content.lower()
    except AttributeError:
        await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
        current_users.remove(str(member))
        return 

    if answer_overwatch_question == "yes":

        if "Overwatch" in old_roles: old_roles.remove("Overwatch")
        ow_role = discord.utils.get(member.server.roles, name="Overwatch")
        await client.add_roles(member, ow_role)

        while attempt < 2:
            #Asks for in game name for Blizzard api lookup
            await client.send_message(member, "What is your BattleTag? This includes the hashtag (case sensitive). \n*Region is assumed EUW. If your account is otherwise please continue as normal and contact an admin to adjust incorrect rank.*")

            #load user input from function and assign to a variable
            
            try:
                message = await client.wait_for_message(author=member, check=check_dm, timeout=300)
                battletag = message.content
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return 
    

            try:
            #uses function that returns league rank and assigns to variable
                overwatch_rank = check_overwatch_rank(battletag)
            except KeyError:
                await client.send_message(member, "I was unable to find your BattleTag.")
                attempt += 1
                battletag = None
                continue
            except AttributeError:
                await client.send_message(member, "Incorrect BattleTag format.")
                attempt += 1
                continue


            #Returns response to verify rank
            await client.send_message(member, "You are " + format(overwatch_rank) + ". Is this correct?")

            
            try:
                validation_overwatch_rank = await client.wait_for_message(author=member, check=check_dm, timeout=300)
                answer_overwatch_rank = validation_overwatch_rank.content.lower()
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return

            if answer_overwatch_rank == "yes":
                if "OW " + overwatch_rank in old_roles: old_roles.remove("OW " + overwatch_rank)
                #Assign tag based on ranked
                await client.send_message(member, "Good. I will assign this to you as a tag.")
                role = discord.utils.get(member.server.roles, name="OW " + overwatch_rank)
                await client.add_roles(member, role)
                break

            else:
                #Error response - FUTURE DEVELOPMENT: sends a message to me of there name and error message
                await client.send_message(member, "Something has gone wrong. Either your rank hasn't been updated or your Summoner Name was incorrect. \nI'm notifying admins of the issue...")
                break

        if attempt == 2:
            await client.send_message(member, "You have entered incorrectly too many times. \n*To edit your information, please contact an admin or redo the process by typing* `!signup`. \nI will now ask you a different question.")
            await admin_notif(member.server,str(member) + " is having issues sorting out ow rank" )            
            overwatch_rank = "N/A"

    attempt = 0


    await client.send_message(member, "Do you play CS:GO? *Input options:* `yes/no`")

    #load user input from function and assign to a variable
    
    try:
        cs_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)
        cs_question = cs_response.content.lower()
    except AttributeError:
        await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
        current_users.remove(str(member))
        return 

    if cs_question == "yes":
        if "Counter Strike" in old_roles: old_roles.remove("Counter Strike")
        cs_role = discord.utils.get(member.server.roles, name="Counter Strike")
        await client.add_roles(member, cs_role)

        await client.send_message(member, "What is your steam profile link? This will be used to manually verify your rank and make it easier for us to approve you to our steam group. \nTo find your steam profile link go on your steam client, click on profile and copy and paste the URL above.")

        try:
            steam_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)
            steam_link = steam_response.content
        except AttributeError:
            await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
            current_users.remove(str(member))
            return 

        cs_ranks = ["1: Silver", "2: Gold Nova","3: MG", "4: LE(M)", "5: Supreme", "6: Global"]

        while attempt < 2:            
            await client.send_message(member, "Please select the number that corresponds with your rank from the list: \n`1` Silver \n`2` Gold Nova \n`3` (Distinguished) Master Guardian \n`4` Legendary Eagle (Master) \n`5` Supreme Master First Class \n`6` The Global Elite")

            #load user input from function and assign to a variable
            
            try:
                message = await client.wait_for_message(author=member, check=check_dm, timeout=300)
                cs_rank = cs_ranks[int(message.content)-1]
                searchObj = re.match(r'\d:\s(.*)', cs_rank , re.M|re.I)
                cs_rank = searchObj.group(1)                
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return
            except ValueError:
                await client.send_message(member, "Incorrect format.")
                attempt += 1
                continue
            
            await client.send_message(member, "Assigning " + cs_rank + " to you.")
            role = discord.utils.get(member.server.roles, name="CS:GO " + cs_rank)
            await client.add_roles(member, role)
            if "CS:GO " + cs_rank in old_roles: old_roles.remove("CS:GO " + cs_rank)
            
            break       
            

        if attempt == 2:
            await client.send_message(member, "You have entered incorrectly too many times. \n*To edit your information, please contact an admin or redo the process by typing* `!signup`. \nI will now ask you a different question.")            
            cs_rank = "N/A"

    attempt = 0

    await client.send_message(member, "Do you play Dota 2? *Input options:* `yes/no`")

    #load user input from function and assign to a variable
    
    try:
        dota_questions_response = await client.wait_for_message(author=member, check=check_dm, timeout=300)
        dota_question = dota_questions_response.content.lower()
    except AttributeError:
        await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
        current_users.remove(str(member))
        return
    if dota_question == "yes":

        dota_role = discord.utils.get(member.server.roles, name="Dota 2")
        await client.add_roles(member, dota_role)
        if "Dota 2" in old_roles: old_roles.remove("Dota 2")
                
        while attempt < 2:
            await client.send_message(member, "Please enter your account ID. \nTo get your account id, sign up on https://www.opendota.com/ \nOnce signed up, go to your profile; your account ID is the last set of numbers in the url. \n*Example:* `36271238` *from* `https://www.opendota.com/players/36271238`")
            
            try:
                message = await client.wait_for_message(author=member, check=check_dm,timeout=300)
                steam_id = message.content
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return   

            try:
            #uses function that returns league rank and assigns to variable
                dota_tier,dota_sub_tier = check_dota_rank(steam_id)
            except KeyError:
                await client.send_message(member, "I was unable to find your account ID.")
                attempt += 1
                continue                
            except ValueError:
                await client.send_message(member, "I was unable to find your account ID.")
                attempt += 1
                continue
            except UnboundLocalError:
                await client.send_message(member, "Looks like you don't have a rank.")                
                break


            #Returns response to verify rank
            await client.send_message(member, "You are " + dota_tier + " " + dota_sub_tier + ". Is this correct?")

            #load user input from function and assign to a variable
            
            try:
                validation_dota_rank = await client.wait_for_message(author=member, check=check_dm, timeout=300)
                answer_dota_rank = validation_dota_rank.content.lower()
            except AttributeError:
                await client.send_message(member, "Sign up has timed out. Please use `!signup` in the *#welcome* chat.")
                current_users.remove(str(member))
                return 

            if answer_dota_rank == "yes":
                #Assign tag based on ranked
                await client.send_message(member, "Good. I will assign this to you as a tag.")                
                role = discord.utils.get(member.server.roles, name="Dota " + dota_tier)
                await client.add_roles(member, role)
                if "Dota " + dota_tier in old_roles: old_roles.remove("Dota " + dota_tier)
                dota_rank = dota_tier + " " + dota_sub_tier
                break                

            else:
                #Error response - FUTURE DEVELOPMENT: sends a message to me of there name and error message
                await client.send_message(member, "Something has gone wrong. Either your rank hasn't been updated or your Summoner Name was incorrect. \nI'm notifying admins of the issue...")
                await admin_notif(member.server,str(member) + " is having issues sorting out dota 2 rank" )
                attempt = 0
                break

        if attempt == 2:
            await client.send_message(member, "You have entered incorrectly too many times. \n*To edit your information, please contact an admin or redo the process by typing* `!signup`.")
            attempt = 0
            dota_rank = "N/A"

    await client.send_message(member, "Thank you for your time. Your information will be added to the google docs members list (<Google doc link>). If there is any incorrect information or something went wrong please contact an admin.")


    if overwrite is False:
        add_to_google_doc(brunel_id,full_name, discord_username, ign, league_rank, battletag, overwatch_rank, cs_rank, dota_rank, steam_id, steam_link)
    else:
        for i in range (0,len(old_roles)):
            removed_role = discord.utils.get(member.server.roles, name=old_roles[i])
            await client.remove_roles(member, removed_role)

        overwrite_google_doc(overwrite, brunel_id,full_name, discord_username, ign, league_rank, battletag, overwatch_rank, cs_rank, dota_rank, steam_id, steam_link)
    current_users.remove(str(member))

#removes members if they are not a verified member or have not used signup to set up there account in a given time period
async def remove_inactive_members(client,s):

    kicked_members = []
    
    current_time = time.time()   
    
    for member in s.members:

        if len(member.roles) == 1:
            duration = current_time - time_joined
            if duration > 172800:
                kicked_members.append(member)
                await client.send_message(member, "You have been kicked from the Esports society discord due to not being signed up in over 48hrs. Please contact an admin if you are a member.")
                await admin_notif(member.server, str(member) + " has been kicked") 

        for role in member.roles:
            if str(role) == "Unverified Member":
                
                time_joined = int(member.joined_at.strftime('%s'))

                duration = current_time - time_joined                                                   
                    
                #after 2 weeks kick
                if duration > 1209600:                                      
                    kicked_members.append(member)
                    
                    await admin_notif(member.server, str(member) + " has been kicked")
                    
                #24hrs before they get kicked send a warning message
                elif duration > 1123200:
                    await client.send_message(member, "Reminder: You have less than 24hrs to join the society and verify your account before being kicked.")                    
                    await admin_notif(member.server, str(member) +  " will be kicked in 24hrs")
                elif duration > 604800:
                    await client.send_message(member, "Reminder: You have 1 week remaining to join the society and verify your account before being kicked.")                    
                    await admin_notif(member.server, str(member) +  " will be kicked in 1 week")

    for m in kicked_members:
        await client.kick(m)
        
#Checks if the user has admin permissions
def check_admin_permissions(message):
    permission = False
    for i in message.author.roles:                
        if str(i) == "Admin":
            permission = True                    
    return permission

#Checks if the user has member permissions
def check_member_permissions(message):
    permission = False
    for i in message.author.roles:                
        if str(i) == "Verified Member":
            permission = True                    
    return permission

#Uses google chrome drives to take a print screen of the users stats page for league of legends and upload that image to the discords text channel
def opgg(server,ign):


    display = Display(visible=0, size=(1920,1080))
    display.start()

    DRIVER = 'chromedriver'
    driver = webdriver.Chrome(DRIVER)
    driver.get('http://' + server + '.op.gg/summoner/userName=' + ign)
    driver.set_window_size(1350,2000)
    screenshot = driver.save_screenshot('my_screenshot.png')
    driver.quit()

    img = cv2.imread("my_screenshot.png")
    crop_img = img[153:1600, 150:1180]  
    cv2.imwrite("cropped.png", crop_img)
    display.stop()

#Every two days it will remove inactive members
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    while True:
        global gc
        google_auth(gc)
        print(time.time())
        print("Looking to remove people")
        for s in client.servers:
                await remove_inactive_members(client,s)
        print("Done for today")
        await asyncio.sleep(172800)        

#Provides the welcome message when a new user joins the server
@client.event
async def on_member_join(member):
     await client.send_message(member,"Hi and welcome to Brunel Esports Discord. To get correct permissions and roles assigned to you please use `!signup` command in the `#welcome` chat. Thanks :D")

#This is where all the commands for the bot gets executed
@client.event
async def on_message(message):
    global gc
    if message.content.startswith('!'):        
        checker = message_checker(message)        
        if checker is True:
            #Triggers the signup function     
            if message.content.startswith('!signup'):                                
                google_auth(gc)
                if str(message.author) in current_users:
                    await client.send_message(message.channel, "Looks like you have a session already running. Direct message the bot `!exit` to terminate it and try again.")
                else:
                    await signup(client,message.author) 
            #Manual trigger of the remove inactive members function                   
            if message.content.startswith('!cleanup'):                
                permission = check_admin_permissions(message)
                if permission == True:
                    s = message.server
                    await remove_inactive_members(client,s)
                    await client.send_message(message.channel,"Cleanup complete.")
                else:
                    await client.send_message(message.channel, "Permission denied! You are not an admin.")
            #Lists all unverifeid members
            if message.content.startswith("!unverified"):
                permission = check_admin_permissions(message)
                if permission == True:
                    count = 0
                    server = message.server
                    for member in server.members:
                        for role in member.roles:
                            if str(role) == "Unverified Member":
                                count = count + 1
                                await client.send_message(message.channel,member.name + "#" + member.discriminator)
                    if count is 0:
                        await client.send_message(message.channel,"There are no unverified members in the server :D")
                else:
                    await client.send_message(message.channel, "Permission denied! You are not an admin.")
            #creates a temporary invite link that members can use to add non university friends to the group, there friends will auto be kicked once there session has ended
            if message.content.startswith("!invlink"):
                permission = check_member_permissions(message)
                if permission == True:        
                    invite = await client.create_invite(message.channel,temporary = True, max_age = 3600, max_uses = 1)
                    await client.send_message(message.channel,invite)
                else:
                    await client.send_message(message.channel, "Permission denied! You are not an admin.")
            #The bot will direct message groups of users depending on there tags, this is a more affect way of providing members with society information
            if message.content.startswith("!broadcast"):
                permission = check_admin_permissions(message)
                server = message.server
                array = []
                if permission == True:
                    await client.send_message(message.author,"This command will direct message users based on their role within the server." 
                    "Please input the role and message split with a pipe. \n*Example:* `League of legends | this is my message`")
                    
                    user_message = await client.wait_for_message(author=message.author, check=check_dm)
                    response = user_message.content
                    try:
                        searchObj = re.match(r'(.*) (?<!\\)\| (.*)', response, re.M|re.I)                
                        role = searchObj.group(1)
                        broadcast_message = searchObj.group(2)
                    except AttributeError:
                        await client.send_message(message.author, "Invalid input.")  
                    
                    for server_member in server.members:                
                        for member_role in server_member.roles:                                      
                            if str(member_role) == role:
                                try:                        
                                    await client.send_message(server_member, broadcast_message)
                                except:
                                    print(str(server_member) + " can not send broadcast message")
                                    continue
                                array.append(str(server_member))
                    
                    await client.send_message(message.author,"Message has been sent to: " + str(array))
                else:
                    await client.send_message(message.channel, "Permission denied! You are not an admin.")
            #Prints help text in channel
            if message.content.startswith("!help"):
                await client.send_message(message.channel, "This bot supports the following commands: \n```!signup: will ask the user a series "
                "of questions to set up correct server roles \n!cleanup: manual removal of unverified users \n!unverified: lists all users in the " 
                "server that are unverfied \n!invlink: creates a temporary invite link that can only be used once \n!broadcast: direct messages everyone "
                "with a specific role with a message \n!verify: checks to see if you are a member and updates your tag \n!lolstats: takes a snapshot of your recent statistics. *Example:* `!lolstats EUW best_ign`"
                "\n!updateranks: updates your competitive ranks in the esports google doc```")
            #If a member is unverfied and then buys membership instead of using a signup again they can use this command, this will do a look up on the database, if they are there will remove unverfied role and give verfied role
            if message.content.startswith("!verify"):                
                google_auth(gc)
                member = message.author        
                brunel_id = get_brunel_id(str(member))       
                if brunel_id == False:
                    await client.send_message(message.channel, "I cannot find you in the google doc. Please make sure you have signed up through Brunel Esports Bot.")
                    return
                
                status = verify_brunel_id(brunel_id)       

                if status == True:
                    role1 = discord.utils.get(member.server.roles, name="Unverified Member")
                    await client.remove_roles(member, role1)
                    role2 = discord.utils.get(member.server.roles, name="Verified Member")
                    await client.add_roles(member, role2)
                    await client.send_message(message.channel, "You are now a member.")
                else:
                    await client.send_message(message.channel, "You are not a member or our database is not up to date. If you are a member, please check with an admin.")
            #This command prints a users league of league stats using the opgg function and uploads the image to the text channel
            if message.content.startswith("!lolstats"):        
                msg = message.content
                msg = msg.replace("!lolstats ","")        
                searchObj = re.match(r'([a-z]+)\s((.*)+)', msg, re.M|re.I)
                try:        
                    region = searchObj.group(1)
                    ign = searchObj.group(2)
                except AttributeError:
                    await client.send_message(message.channel, "Invalid format. Please follow the *Example:* `!lolstats EUW best_ign`")
                    return
                opgg(region,ign)
                await client.send_file(message.channel,"cropped.png")
            #This calls update rank fucntion
            if message.content.startswith("!updateranks"):               
                google_auth(gc)       
                await updateranks(str(message.author),message)
        #This is used to quit the signup session half way through            
        elif message.content.startswith('!exit'):
            await client.send_message(message.author,"Quitting process.")                        
        else:
            try:                        
                await client.send_message(message.author,"Missing role - this could be because you are trying to use a command directly to me. Please try again in the *#welcome* chat of the server.")
            except discord.errors.HTTPException:
                print("Something wrong for some reason. Command tried to be sent directly to bot.")


client.run("<Discord Key>")
