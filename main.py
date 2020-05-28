import discord
import logging
import asyncio
import json
from datetime import datetime, time

logging.basicConfig(level=logging.INFO)

with open("botsettings.txt", "r") as file:
    botparameters = json.loads(file.read())

bottoken = botparameters['token']
guilds = {}
myid = botparameters['myid']
myserverid = botparameters['myserverid']

class BotSettings:
    def __init__(self, args):
        x = args[:]
        args = []
        default = [2, True, "]", 0, 0]

        for i in range(0, len(default)):
            if i < len(x):
                args.append(x[i])
            else:
                args.append(default[i])

        self.minforcount, self.iscounting, self.prefix, self.starttime, self.endtime = args


class BotGuild:
    def __init__(self, iid, isettings, ileaderboard, ilbdisplay, ileaderboardmsg, isettingsmsg, iobject):
        self.ac = None
        self.id = iid
        self.settings = isettings
        self.auto = None
        self.leaderboard = ileaderboard
        self.lbdisplay = ilbdisplay
        self.lbsave = ileaderboardmsg
        self.settingsmessage = isettingsmsg
        self.object = iobject


class Security:
    CREATOR = 0
    OWNER = 1
    ADMIN = 2
    EVERYBODY = 3
    invalid = "You do not have high enough permissions to use this command."


def timebetween(begin_time: time, end_time: time, check_time: time):
    if begin_time < end_time:
        return begin_time <= check_time < end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time < end_time


def validate(message: discord.Message, security):
    author = message.author
    perms = author.guild_permissions
    authorlevel = 3
    if perms.administrator:
        authorlevel = 2
    if message.guild.owner == author:
        authorlevel = 1
    if author.id == myid:
        authorlevel = 0
    if authorlevel <= security:
        return True
    return False


async def ping(message: discord.Message):  # Simple test command
    await message.channel.send(content="Pong!")
    return True


async def watchserver(guild: discord.Guild):  # Automatically adds coolpoints to people in voice chat in different
    cguild = guilds[guild.id]                 # servers.
    csettings = cguild.settings

    while csettings.iscounting:
        await asyncio.sleep(5)
        # Checks if the time is between the start and end.
        if timebetween(time(csettings.starttime), time(csettings.endtime), datetime.now().time()):
            for vc in guild.voice_channels:
                if len(vc.members) >= csettings.minforcount:
                    for member in vc.members:
                        vs = member.voice
                        if vs.deaf or vs.self_deaf:
                            print("{} is deaf in {}.".format(member.name, guild.name))
                            continue
                        print("Doing {} in {}.".format(member.name, guild.name))
                        if member.id not in cguild.leaderboard:
                            cguild.leaderboard[member.id] = 1
                        else:
                            cguild.leaderboard[member.id] += 1


# async def recordchannel(channel, message: discord.Message):
#     # Manually scans a channel.
#     cguildid = message.guild.id
#     cguild = guilds[cguildid]
#     while len(channel.members) >= cguild.settings.minforcount:  # Checks if enough people
#         for member in channel.members:
#             memid = member.id
#             if memid not in cguild.leaderboard:
#                 cguildid.leaderboard[memid] = 1
#             else:
#                 cguild.leaderboard[memid] += 1
#         await asyncio.sleep(1)
#
#     else:
#         await message.channel.send(content='Not enough people in call. Stopping counting.')
#         guilds[cguildid].ac = None


# async def manualchannel(message: discord.Message):
#     if not validate(message, Security.ADMIN):
#         await message.channel.send(content=Security.invalid)
#         return True
#     member = message.author
#     voicestate = member.voice
#     if voicestate is None:
#         await message.channel.send(content="You are not currently in a voice channel.\nPlease join the voice channel "
#                                            "you would like me to watch.")
#         return True
#
#     vc = voicestate.channel
#     curguild = guilds[message.guild.id]
#     if curguild.ac is None:
#         watch = asyncio.create_task(recordchannel(vc, message))
#         await message.channel.send(content="Started watching channel **{}**."
#                                    .format(message.channel.name))
#     else:
#         await message.channel.send(content="Already watching **{}**. Switching to **{}**."
#                                    .format(curguild.ac[0].name, vc.name))
#         curguild.ac[1].cancel()
#         watch = asyncio.create_task(recordchannel(vc, message))
#     curguild.ac = [vc, watch]
#     return True


# async def stopwatching(message: discord.Message):
#     if not validate(message, Security.ADMIN):
#         await message.channel.send(content=Security.invalid)
#         return True
#     curguild = guilds[message.guild.id]
#     if curguild.ac is None:
#         await message.channel.send(content="I'm not manually watching a channel. Automatic mode is **{}**."
#                                    .format(curguild.settings.iscounting))
#     else:
#         await message.channel.send(content="Stopped watching channel **{}**."
#                                    .format(curguild.ac[0].name))
#         curguild.ac[1].cancel()
#         curguild.ac = None
#     return True


async def settings(message: discord.Message):
    # Updates the current guild's settings
    if not validate(message, Security.ADMIN):
        await message.channel.send(content=Security.invalid)
        return True
    cguild = guilds[message.guild.id]
    csettings = cguild.settings
    params = message.content.split(" ")
    errmsg = ("Invalid. Say '{}help' for more info."
              .format(cguild.settings.prefix))
    if len(params) < 2:
        await message.channel.send(content=errmsg)

    if params[1] == "prefix":

        if len(params[2]) != 1:
            await message.channel.send(content="Prefix must be 1 character.")
        else:
            csettings.prefix = params[2]
            await message.channel.send(content="Successfully changed prefix to '{}'.".format(params[2]))

    elif params[1] == "autocount":
        cautocount = csettings.iscounting

        if params[2].lower() in ['on', 'yes', 'true', 'enabled', 'enable']:
            csettings.iscounting = True
            if cguild.auto is None:
                cguild.auto = asyncio.create_task(watchserver(message.guild))
            await message.channel.send(content="Autocounting enabled. Used to be {}.".format(cautocount))

        elif params[2].lower() in ['off', 'no', 'false', 'disabled', 'disable']:
            csettings.iscounting = False
            if cguild.auto is not None:
                cguild.auto.cancel()
                cguild.auto = None
            await message.channel.send(content="Autocounting disabled. Used to be {}.".format(cautocount))

        else:
            await message.channel.send(content="Invalid value. Try off or on.")

    elif params[1] == "minreqforcount":
        if not params[2].isdecimal():
            await message.channel.send(content="Please provide a number.")
        else:
            csettings.minforcount = int(params[2])
            await message.channel.send(content="Set minimum required people in a call to gather points to **{}**."
                                       .format(params[2]))
    elif params[1] == "settime":
        if len(params) != 4:
            await message.channel.send(content="Please check help to see how to do this command.")
        else:
            csettings.starttime = int(params[2])
            csettings.endtime = int(params[3])
            await message.channel.send(content="Successfully set start time to {} and end time to {}.,"
                                       .format(params[2], params[3]))

    else:
        await message.channel.send(content=errmsg)
    await updatesettings(guilds[message.guild.id])


async def updatesettings(guild: BotGuild):
    # Saves the current guild's settings
    gsettings = guild.settings
    jsonsettings = json.dumps(gsettings.__dict__)
    await guild.settingsmessage.edit(content=jsonsettings)


async def bothelp(message: discord.Message):
    # Prints out the help menu
    cguild = guilds[message.guild.id]
    csettings = cguild.settings

    helpembed = discord.Embed(title="Help", type="rich", description="Coolbot help",
                              colour=discord.Color.blue())
    helpembed.set_author(name="Coolbot", icon_url=client.user.avatar_url)

    helpembed.add_field(name="***prefix*** - {} - Admin".format(csettings.prefix), value=
    "**{}settings** prefix [single character prefix]\nChanges the prefix. "
                        .format(csettings.prefix))

    helpembed.add_field(name="***autocount*** - {} - Admin".format(csettings.iscounting), value=
    "**{}settings** autocount [on or off]\nSets whether the bot will automatically start counting "
    "unless set to a specific channel. "
                        .format(csettings.prefix))

    helpembed.add_field(name="***minreqforcount*** - {} - Admin".format(csettings.minforcount), value=
    "**{}settings** minreqforcount [number]\nSets the amount of people required to be in the call for "
    "the bot to start counting. "
                        .format(csettings.prefix))

    helpembed.add_field(name="***settime*** - {} -> {} - Admin".format(csettings.starttime, csettings.endtime), value=
    "**{}settings** settime [start time - 24hr clock] [end time - 24hr clock]\nSets the two times between which you "
    "will be able to gather points. Set to 0 -> 0 to be always active.".format(csettings.prefix))

    helpembed.add_field(name="***leaderboard*** - Anybody", value=
    "{}leaderboard\nDisplays the leaderboard. It can also be found here: <#{}>"
                        .format(csettings.prefix, cguild.lbdisplay.channel.id))

    helpembed.add_field(name="***set*** - Owner", value=
    "{}set [discord id] [point value]\nSets the points of the target to the given value. Note that it is discord id, "
    "not their username and tag. Look up how to get this value. (Looks like this: 127892225546280672) "
                        .format(csettings.prefix))

    helpembed.add_field(name="***reset*** - Owner", value=
    "{}reset\nCompletely resets the leaderboard."
                        .format(csettings.prefix))

    helpembed.add_field(name="***ping***", value=
    "{}ping\nPong!"
                        .format(csettings.prefix))

    await message.channel.send(embed=helpembed)


def generateleaderboard(guild: discord.Guild):
    # Generates a text leaderboard output for that guild
    if isinstance(guild, discord.Message):
        guild = guild.guild
    cguild = guilds[guild.id]
    cleaderboard = cguild.leaderboard
    sortedleaderboard = reversed(sorted([item for item in cleaderboard.items()], key=lambda n: n[1]))
    leaderboardnames = []
    for x in sortedleaderboard:
        member = guild.get_member(x[0])
        if member is None:
            break
        leaderboardnames.append([member.nick or member.name, x[1]])

    outputstr = "```makefile\nLEADERBOARD\n"
    if not leaderboardnames:
        return "Empty leaderboard."
    maxname = len(max(leaderboardnames, key=lambda z: len(z[0])))

    for i in range(len(leaderboardnames)):
        item = leaderboardnames[i]
        outputstr += "{}: {:>{width}} | {} points\n".format(i + 1, item[0], item[1], width=maxname)
    return outputstr + '```'


async def leaderboard(message: discord.Message):
    boardoutput = generateleaderboard(message)
    await message.channel.send(content=boardoutput)
    return True


async def autoupdateleaderboard(guild: BotGuild):
    while True:
        print("updating {}".format(guild.object.name))
        await guild.lbdisplay.edit(content=generateleaderboard(guild.object))
        await guild.lbsave.edit(content=json.dumps(guild.leaderboard))
        await asyncio.sleep(15)


async def setdata(message: discord.Message):
    if not validate(message, Security.OWNER):
        await message.channel.send(content=Security.invalid)
        return True
    params = message.content[1:].split(" ")
    if len(params) != 3:
        await message.channel.send(content="Invalid arguments.")
        return True
    if params[1].isdecimal() and params[2].isdecimal():
        cguild = guilds[message.guild.id]
        cguild.leaderboard[int(params[1])] = int(params[2])
        await message.channel.send("Successfully set {}'s points to {}."
                                   .format(cguild.object.get_member(int(params[1])).name, params[2]))
    else:
        message.channel.send(content="Numbers only.")
        return True


async def resetlb(message: discord.Message):
    if not validate(message, Security.OWNER):
        await message.channel.send(content=Security.invalid)
        return True
    guilds[message.guild.id].leaderboard = {}
    await message.channel.send(content="Successfully reset leaderboard.")


async def executecode(message: discord.Message):
    if not validate(message, Security.CREATOR):
        await message.channel.send(content=Security.invalid)
        return True
    code = message.content[9:]
    exec(code)
    await message.channel.send(content="Code executed.")


commands = {
    'ping': ping,
    'settings': settings,
    'help': bothelp,
    'leaderboard': leaderboard,
    'set': setdata,
    'reset': resetlb,
    'execute': executecode,
}


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        myguild = self.get_guild(myserverid)
        for guild in client.guilds:
            settingschannel = None
            lbchannel = None
            lbsavechannel = None
            lbinput = {}
            for channel in myguild.text_channels:
                if channel.name == str(guild.id) + "s":
                    settingschannel = channel
                if channel.name == str(guild.id) + "l":
                    lbsavechannel = channel
            for channel in guild.text_channels:
                if channel.name == "coolbot-leaderboard":
                    lbchannel = channel
            if settingschannel is None:
                settingschannel = await myguild.create_text_channel(str(guild.id) + "s")
                settingsmessage = await settingschannel.send(content="Initialising server.")
                await settingsmessage.edit(content=json.dumps(BotSettings([]).__dict__))
                settingsdict = json.loads(settingsmessage.content)
            else:
                settingsmessage = await settingschannel.fetch_message(settingschannel.last_message_id)
                settingsdict = json.loads(settingsmessage.content)

            if lbsavechannel is None:
                lbsavechannel = await myguild.create_text_channel(str(guild.id) + "l")
                lbsavemsg = await lbsavechannel.send(content="Initialising leaderboard.")
            else:
                lbsavemsg = await lbsavechannel.fetch_message(lbsavechannel.last_message_id)
                lbbadinput = json.loads(lbsavemsg.content)
                lbinput = {}
                for item in lbbadinput.items():
                    lbinput[int(item[0])] = item[1]

                print(lbinput)
            if lbchannel is None:
                permissions = discord.PermissionOverwrite(
                    create_instant_invite=False,
                    manage_channels=False,
                    read_messages=True,
                    send_messages=False,
                    send_tts_messages=False,
                    manage_messages=False,
                    embed_links=False,
                    read_message_history=True,
                    mention_everyone=False,
                    attach_files=False,
                    manage_roles=False,
                    manage_webhooks=False
                )
                meperms = discord.PermissionOverwrite(
                    create_instant_invite=True,
                    manage_channels=True,
                    read_messages=True,
                    send_messages=True,
                    send_tts_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    read_message_history=True,
                    mention_everyone=True,
                    attach_files=True,
                    manage_roles=True,
                    manage_webhooks=True,
                )
                lbdisplay = await guild.create_text_channel('coolbot-leaderboard', overwrites={
                    guild.default_role: permissions,
                    self.user: meperms
                })
                lbdisplaymsg = await lbdisplay.send(content="Initalising leaderboard. Please wait.")
            else:
                lbdisplaymsg = await lbchannel.fetch_message(lbchannel.last_message_id)

            settingvalues = list(settingsdict.values())
            print(settingvalues)
            newguild = BotGuild(guild.id, BotSettings(settingvalues), lbinput, lbdisplaymsg, lbsavemsg, settingsmessage,
                                guild)

            asyncio.create_task(autoupdateleaderboard(newguild))
            watcher = asyncio.create_task(watchserver(guild))
            newguild.auto = watcher

            guilds[guild.id] = newguild

        print("Prepared.")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith(guilds[message.guild.id].settings.prefix):
            params = message.content[1:].split(" ")
            asyncio.create_task(commands[params[0]](message))


client = MyClient()
client.run(bottoken)

client.event()
