import traceback

import discord
import os
from dotenv import load_dotenv

import time
import subprocess
from requests import get #For getting the external IP of the machine from ipify.org

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')
MC_VER = os.getenv('MC_SER_VER')

client = discord.Client()

curr_vote = 0
vote_needed = 4
voters = []
time_limit = 10*60
disabled = False
hello_world = False
vote_deadline_time = 0

def sec_to_min_and_sec(sec):
	min = int(sec/60)
	string = ""
	if sec >= 60:
		string = string + str(min) + " minute"
		if min != 1:
			string = string + "s"
	remain_sec = sec % 60
	if sec >= 60 and remain_sec != 0:
		string = string + " and "
	if min == 0 and remain_sec == 0: #0 seconds left is rare but possible
		remain_sec = 1 #Round up to 1 second instead
	if remain_sec != 0:
		string = string + str(remain_sec) + " second"
		if remain_sec != 1:
			string = string + "s"
	return string;

@client.event
async def on_ready():
	global hello_world
	
	curr_guild = discord.utils.get(client.guilds, name=GUILD)
	if curr_guild is None:
		print("Guild \"" + GUILD + "\" not found")
		return
		
	mc_channel = discord.utils.get(curr_guild.text_channels, name=CHANNEL)
	if mc_channel is None:
		print("In guild: \"" + GUILD +  "\", text channel \"" + CHANNEL + "\" not found")
		return
		
	msg = "The Minecraft Server BOT is now online\nIf you want to start the server, type ***/mcs vote***\nVotes needed: " + str(vote_needed) + ", Time limit: " + sec_to_min_and_sec(time_limit)
	if hello_world == False:
		await mc_channel.send(msg)
		hello_world = True
		print("Bot is ready")

@client.event
async def on_message(message):

	global curr_vote, vote_needed, voters, time_limit, disabled, vote_deadline_time

	curr_chan = message.channel
	received_message = message.content.lower()
	
	help_line = "Minecraft Server BOT v0.2.3.1 made by shun\nCommands available:\n***/mcs show*** -------------- Show the current vote status\n***/mcs vote*** --------------- Vote to start the server\n***/mcs devote*** ------------ Cancel your vote (if you have voted)\n***/mcs help*** --------------- Show these texts"
	
	#Stop executing if it is the BOT himself
	if message.author == client.user: 
		return
	
	if received_message.startswith("/mcs"):
		try:
			command, first_part = received_message.split(" ", 1)
		except ValueError:
			await curr_chan.send(help_line)
			return
		
		if first_part.startswith("help"):
			response = help_line
		
		elif first_part.startswith("vote"):
		
			if disabled:
				await curr_chan.send("Server has already started")
				return
		
			voted = False
			if len(voters) == 0:
				vote_deadline_time = time.time() + time_limit
				
			for voter in voters:
				if voter == message.author:
					voted = True
					break
					
			if not voted:
				if time.time() > vote_deadline_time:
					response = sec_to_min_and_sec(time_limit) + " has passed, reseting all previous expired votes..."
					curr_vote = 0
					voters = []
					vote_deadline_time = time.time() + time_limit
					await curr_chan.send(response)
				curr_vote = curr_vote + 1
				voters.append(message.author)
				if curr_vote == vote_needed:
					ip = get('https://api.ipify.org').text #Obtain external IP via API from ipify.org
					response = "Enough votes has been received, starting server...\nThe server IP is: " + ip + ", Minecraft version: " + MC_VER
					subprocess.Popen('start.bat')
					disabled = True
					voters = []
					curr_vote = 0
				else:
					response = message.author.display_name + " has voted to start the server. Need " + str(vote_needed - curr_vote) + " more vote(s) to start the server within " + sec_to_min_and_sec(int(vote_deadline_time - time.time()))
					response = response + "\nIf you want to start the server, type ***/mcs vote***"
			else:
				response = "You have already voted!"
				
		elif first_part.startswith("show"):
			if time.time() > vote_deadline_time and len(voters) > 0:
					response = sec_to_min_and_sec(time_limit) + " has passed, reseting all previous expired votes..."
					voters = []
					curr_vote = 0
					await curr_chan.send(response)
			if disabled:
				await curr_chan.send("Server has already started")
				return
			response = "There are currently " + str(curr_vote) + " vote(s) out of " + str(vote_needed) + " votes needed to start the server"
			if curr_vote > 0:
				response = response + " with " + sec_to_min_and_sec(int(vote_deadline_time - time.time())) + " remaining"
		
		elif first_part.startswith("devote"):
			check_devote_voted = False
			for voter in voters:
				if voter == message.author:
					check_devote_voted = True
					voters.remove(voter)
					curr_vote = curr_vote - 1
					response = "Your vote has been cancelled successfully.\n"
					response = response + "There are currently " + str(curr_vote) + " vote(s) out of " + str(vote_needed) + " votes needed to start the server"
					if curr_vote > 0:
						response = response + " with " + sec_to_min_and_sec(int(vote_deadline_time - time.time())) + " remaining"
					break
						
			if not check_devote_voted:
				response = "You did not vote to start the server"
		
		else:
			response = help_line
		
		try:
			await curr_chan.send(response)
		except UnboundLocalError as emsg:
			print("Log: UnboundLocalError catched!!!!")
			traceback.print_exc()
			curr_vote = 0
			await curr_chan.send("An error occured during execution, reseting all the data...")

client.run(TOKEN)