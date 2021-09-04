import os
import asyncio
import discord
from dotenv import load_dotenv
from mcstatus import MinecraftServer

load_dotenv()

server = MinecraftServer.lookup("209.192.238.12:25576")
client = discord.Client()
TOKEN = os.getenv('TOKEN')
cur_num_players = 0
will_check_players = False

def get_players():
    query = server.query()
    list_players = query.players.names
    return list_players

async def check_players_online(chnl):
    while will_check_players:
        global cur_num_players
        new_num_players = server.status().players.online
        embedMsg = discord.Embed()
        if new_num_players > cur_num_players:
            embedMsg.title = "A player has joined the server."
            embedMsg.description = f"There are now **{new_num_players}** players online"
            await chnl.send(embed = embedMsg)
        elif new_num_players < cur_num_players:
            embedMsg.title = "A player has left the server."
            embedMsg.description = f"There are now **{new_num_players}** players online"
            await chnl.send(embed = embedMsg)
        cur_num_players = new_num_players
        await asyncio.sleep(10)

@client.event
async def on_ready():
    print("MCServer-chan is up and running...")
    global cur_num_players
    cur_num_players = server.status().players.online

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global will_check_players
    if message.content == '$players':
        try:
            status = server.status()
            await message.channel.send(f"There are {status.players.online} players online")
            # list_players = get_players()
            # bold_names = ['**' + name + '**' for name in list_players]
            # print(bold_names)
            # if(len(list_players) < 1):
            #     await message.channel.send("There are no players online...")
            # else:
            #     await message.channel.send(f"The following players are online: {', '.join(bold_names)}")
        except:
            await message.channel.send("Server could not be reached...")
    elif message.content == '$mp on':
        will_check_players = True
        client.loop.create_task(check_players_online(message.channel))
        await message.channel.send("Now checking when players join or leave...")
    elif message.content == '$mp off':
        will_check_players = False
        await message.channel.send("Turning off...")
    else:
        print("DONE")

if __name__ == '__main__':
    client.run(TOKEN)