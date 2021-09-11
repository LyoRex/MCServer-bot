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
restart_check = False
max_restart_tries = 3
cur_restart_tries = 0

player_update_list = []
player_all_updates_list = []

def get_players():
    query = server.query()
    list_players = query.players.names
    return list_players

async def restart_check_players(chnl):
    global will_check_players
    global restart_check
    global cur_restart_tries
    global max_restart_tries
    if cur_restart_tries >= max_restart_tries:
        await chnl.send("Could not restart player join/leave checking. Attempts have exceeded the max...")
        print("Could not restart player join/leave checking. Attempts have exceeded the max...")
        cur_restart_tries = 0
        will_check_players = False
        restart_check = False
        return
    await asyncio.sleep(10)
    await chnl.send(f"Attempting to restart player join/leave checking. **Attempt {cur_restart_tries}:**")
    print(f"Attempting to restart player join/leave checking. **Attempt {cur_restart_tries}:**")
    try:
        client.loop.create_task(check_players_online(chnl))
        await chnl.send("Restarted player join/leave checking...")
        print("Restarted player join/leave checking...")
        cur_restart_tries = cur_restart_tries + 1
    except:
        if restart_check == True:
            client.loop.create_task(restart_check_players(chnl))
            print("Retrying restart check players function...")
        else:
            return

async def check_players_online(chnl):
    global cur_num_players
    while will_check_players:
        try:
            new_num_players = server.status().players.online
            embedMsg = discord.Embed()
            if new_num_players > cur_num_players:
                embedMsg.title = "A player has joined the server."
                embedMsg.description = f"There are now **{new_num_players}** players online"
                await chnl.send(embed = embedMsg)
                for user in player_all_updates_list:
                    await user.send(embed = embedMsg)
                if cur_num_players == 0:
                    playerEmbed = discord.Embed()
                    playerEmbed.title = "There are players online!"
                    playerEmbed.description = f"There are now **{new_num_players}** players online"
                    for user in player_update_list:
                        await user.send(embed = playerEmbed)
            elif new_num_players < cur_num_players:
                embedMsg.title = "A player has left the server."
                embedMsg.description = f"There are now **{new_num_players}** players online"
                await chnl.send(embed = embedMsg)
                for user in player_all_updates_list:
                    await user.send(embed = embedMsg)
                if new_num_players == 0:
                    playerEmbed = discord.Embed()
                    playerEmbed.title = "There are now no players online!"
                    for user in player_update_list:
                        await user.send(embed = playerEmbed)
            cur_num_players = new_num_players
            await asyncio.sleep(10)
        except ConnectionRefusedError:
            await chnl.send("**Could not reach the server!**")
            if restart_check == True:
                client.loop.create_task(restart_check_players(chnl))
            return
        except OSError:
            await chnl.send("**Could not reach the server!**")
            if restart_check == True:
                client.loop.create_task(restart_check_players(chnl))
            return

@client.event
async def on_ready():
    print("MCServer-chan is up and running uwu...")
    global cur_num_players
    cur_num_players = server.status().players.online

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global will_check_players
    global restart_check
    if not message.content.startswith('$'):
        return
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
        if will_check_players:
            await message.channel.send("Player join/leave tracking is already enabled...")
            return
        will_check_players = True
        client.loop.create_task(check_players_online(message.channel))
        await message.channel.send("Now checking when players join or leave...")

    elif message.content == '$mp off':
        if not will_check_players:
            await message.channel.send("Player join/leave tracking is already disabled...")
            return
        will_check_players = False
        await message.channel.send("Turning off...")
    elif message.content == "$rc on":
        if restart_check:
            await message.channel.send("Restart Check is already enabled...")
            return
        restart_check = True
        await message.channel.send("Restart Check is now enabled...")
    elif message.content == "$rc off":
        if not restart_check:
            await message.channel.send("Restart Check is already disabled...")
            return
        restart_check = False
        await message.channel.send("Restart Check is now disabled...")
    elif message.content == "$updates on":
        user = message.author
        if user in player_update_list:
            await message.channel.send("**You are already in the 'updates' list!**")
            return
        await user.send("You will now receive updates when there is a player online!")
        if user in player_all_updates_list:
            player_all_updates_list.remove(user)
        player_update_list.append(user)
    elif message.content == "$updates all on":
        user = message.author
        if user in player_all_updates_list:
            await message.channel.send("**You are already in the 'all updates' list!**")
            return
        await user.send("You will now receive all updates of players joining and leaving!")
        if user in player_update_list:
            player_update_list.remove(user)
        player_all_updates_list.append(user)
    elif message.content == "$updates off":
        user = message.author
        if not user in player_update_list and not user in player_all_updates_list:
            await message.channel.send("**You are not in the 'updates' lists!**")
            return
        await user.send("You will now stop receiving updates on the player activity of the server!")
        if user in player_update_list:
            player_update_list.remove(user)
        if user in player_all_updates_list:
            player_all_updates_list.remove(user)
    elif message.content == "$updatelist":
        update_list_embed = discord.Embed()
        update_list_embed.title = "Users in Updates List"
        update_list_embed.description = f""
        for user in player_update_list:
            update_list_embed.description += (user.name + "\n")
        await message.channel.send(embed=update_list_embed)
        all_update_list_embed = discord.Embed()
        all_update_list_embed.title = "Users in Full Updates List"
        all_update_list_embed.description = f""
        for user in player_all_updates_list:
            all_update_list_embed.description += (user.name + "\n")
        await message.channel.send(embed=all_update_list_embed)
    else:
        print("COMMAND IS NOT REGISTERED")

if __name__ == '__main__':
    client.run(TOKEN)