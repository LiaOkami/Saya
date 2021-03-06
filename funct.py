import time
import math
import random
import discord
import aiosqlite
from itertools import repeat
from Arcapi import AsyncApi
from operator import itemgetter
from datetime import datetime, timedelta

# Initialize an API with user code
api_ = AsyncApi(user_code="610602710")

diff = ["PST", "PRS", "FTR", "BYD"]
diff_fn = ["Past", "Present", "Future", "Beyond"]
clr = ["F", "NC", "FR", "PM", "EC", "HC"]
partners_names = ["Hikari", "Tairitsu", "Kou", "Sapphire", "Lethe", "unknown_icon", "[Axium] Tairitsu",
		          "[Grievous] Tairitsu", "unknown_icon", "Hikari & Fisica", "Ilith", "Eto", "Luna", "Shirabe",
                  "[Zero] Hikari", "[Fracture] Hikari", "[Summer] Hikari", "[Summer] Tairitsu", "Tairitsu & Trin",
                  "Ayu", "[Winter] Eto & Luna", "Yume", "Hikari & Seine", "Saya", "[Grievous] Tairistu & Chuni Penguin",
                  "Chuni Pinguin", "Haruna", "Nono", "[MTA-XXX] Pandora Nemesis", "[MDA-21] Regulus", "Kanae",
                  "[Fantasia] Hikari", "[Sonata] Tairitsu", "Sia", "DORO*C", "[Tempest] Tairitsu",
                  "[E/S Primera] Brillante", "[Summer] Ilith", "[Etude] Saya",  "Alice & Tenniel", "Luna & Mia",
                  "Areus", "Seele", "Isabelle"]

# Asset links
partners = "http://119.23.30.103:8080/ArcAssets/icon/"
cover = "http://119.23.30.103:8080/ArcAssets/cover/"


async def register(message):
    code = None
    if len(message.content.split(" ")) == 2:
        if len(message.content.split(" ")[1]) == 9 and message.content.split(" ")[1].isdigit():
            code = message.content.split(" ")[1]

    elif len(message.content.split(" ")) < 2:
        if len("".join(message.content.split(" ")[1:])) == 9 and "".join(message.content.split(" ")[1:].isdigit()):
            code = "".join(message.content.split(" ")[1:])

    if code:
        async with aiosqlite.connect(f"players.db") as db:
            async with db.execute(f"SELECT * FROM players WHERE discord_id = {message.author.id}") as c:
                if len(await c.fetchall()) == 0:
                    async with db.execute(f"INSERT INTO players (discord_id, arc_id) VALUES "
                                          f"('{message.author.id}', '{code}')"):
                        await db.commit()
                    await message.channel.send("> INFO: Code ajouté a la base de données")
                    return
                else:
                    async with db.execute(f"UPDATE players SET arc_id = '{code}' "
                                          f"WHERE discord_id = '{message.author.id}'"):
                        await db.commit()
                    await message.channel.send("> INFO: Code mis à jour la base de données")
                    return

    else:
        await message.channel.send("> ERREUR: Le format du code est incorrect")
        return


async def recent(message):
    code = await check_id(message.author.id)
    if not code:
        await message.channel.send("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

    api_ = AsyncApi(user_code=code)
    data = await api_.songs()
    songlist = data[0]
    prfl = data[1]
    recent = prfl["recent_score"][0]

    if recent["difficulty"] == 3:
        cover_url = cover + "3_" + recent["song_id"] + ".jpg"
    else:
        cover_url = cover + recent["song_id"] + ".jpg"
    msg_emb = discord.Embed(title="Last play", type="rich", color=discord.Color.dark_teal())
    msg_emb.set_thumbnail(url=cover_url)
    msg_emb.set_author(name=f'{prfl["name"]}', icon_url=get_partner_icon(prfl))
    msg_emb.add_field(name=f'**{songlist[recent["song_id"]]["en"]}\n<{diff[recent["difficulty"]]} '
                           f'{get_diff(recent["constant"])}\>**',
                      value=f'> **{format_score(recent["score"])}** [{clr[recent["best_clear_type"]]}] '
                            f'(Rating: {round(recent["rating"], 3)})\n'
                            f'> Pure: {recent["perfect_count"]} ({recent["shiny_perfect_count"]}) \n'
                            f'> Far: {recent["near_count"]} |  Lost: {recent["miss_count"]}\n'
                            f'> Date: {format_time(recent["time_played"]).split(" - ")[0]}')
    await message.channel.send(embed=msg_emb)


async def best(message):
    code = await check_id(message.author.id)
    nb_scores = 30
    if not code:
        await message.channel.send("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

    if len(message.content.split(" ")) > 1:
        if message.content.split(" ")[1].isdigit():
            if 1 <= int(message.content.split(" ")[1]) <= 30:
                nb_scores = int(message.content.split(" ")[1])

    api_ = AsyncApi(user_code=code)
    data = await api_.scores()
    songlist = data[0]
    prfl = data[1]
    ls_top = []

    for elm in data[2:]:
        ls_top.append(elm)

    ls_top = sorted(ls_top, key=itemgetter("rating"), reverse=True)[0:30]

    msg_emb = discord.Embed(title=f'Top {nb_scores}', type="rich", color=discord.Color.dark_teal())
    msg_emb.set_author(name=f'{prfl["name"]}', icon_url=get_partner_icon(prfl))
    
    if nb_scores == 1:
        if ls_top[0]["difficulty"] == 3:
            cover_url = cover + "3_" + ls_top[0]["song_id"] + ".jpg"
        else:
            cover_url = cover + ls_top[0]["song_id"] + ".jpg"
        msg_emb.set_thumbnail(url=cover_url)

    if (nb_scores > len(ls_top)):
        nb_scores = len(ls_top)
		
    for i in range(nb_scores):
        if i == round(nb_scores/2) and nb_scores > 20:
            await message.channel.send(embed=msg_emb)
            msg_emb = discord.Embed(title="Top 30", type="rich", color=discord.Color.dark_teal())
            msg_emb.set_author(name=f'{prfl["name"]}', icon_url=get_partner_icon(prfl))
        msg_emb.add_field(name=f'**{songlist[ls_top[i]["song_id"]]["en"]}\n<{diff[ls_top[i]["difficulty"]]} '
                               f'{get_diff(ls_top[i]["constant"])}\>**',
                          value=f'> **{format_score(ls_top[i]["score"])}** [{clr[ls_top[i]["best_clear_type"]]}] '
                                f'(Rating: {round(ls_top[i]["rating"], 3)})\n'
                                f'> Pure: {ls_top[i]["perfect_count"]} ({ls_top[i]["shiny_perfect_count"]}) \n'
                                f'> Far: {ls_top[i]["near_count"]} | Lost: {ls_top[i]["miss_count"]}\n'
                                f'> Date: {format_time(ls_top[i]["time_played"]).split(" - ")[0]}')
    await message.channel.send(embed=msg_emb)


async def profile(message):
    code = await check_id(message.author.id)
    if not code:
        await message.channel.send("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

    api_ = AsyncApi(user_code=code)
    data = await api_.scores()
    prfl = data[1]

    rating = "{0:04d}".format(prfl["rating"])[:2] + "." + "{0:04d}".format(prfl["rating"])[2:] + " PTT"

    if rating == "-0.01 PTT":
        rating = "*Hidden*"

    msg_emb = discord.Embed(title="Profile", type="rich", color=discord.Color.dark_teal())
    msg_emb.set_thumbnail(url=get_partner_icon(prfl))
    msg_emb.add_field(name=f'**{prfl["name"]}\'s profile**',
                      value=f'> Rating: **{rating}**\n'
                            f'> Favchar: **{partners_names[prfl["character"]]}**\n'
                            f'> Last play: **{format_time(prfl["recent_score"][0]["time_played"])}**\n'
                            f'> Join date: **{format_time(prfl["join_date"])}**\n'
                            f'> Code: **{format_code(code)}**')
    await message.channel.send(embed=msg_emb)


# Return nb_scores recommendations based on given scores/profile, doesn't display anything
def get_ptt_recommendation_scores(scores, prfl, nb_scores):
    ptt_rec = []
    PTT = float(prfl["rating"]) / 100

    scores = sorted(scores, key=itemgetter("rating"), reverse=True)
    # Divides scores between top 30 and scores below
    scores_top_30 = scores[0:30]
    last_top_30 = scores_top_30[-1]
    scores_others = scores[30:]
    scores_others_2 = scores_others
    # Removes PMs
    scores_top_30 = filter(lambda scores: scores["score"] < 10000000, scores_top_30)
    scores_others = list(filter(lambda scores: scores["score"] < 10000000, scores_others))

    half_nb_scores = math.floor(nb_scores / 2)
    # Max 1/4 recommendations : Oldest scores not in top 30 with Chart Constant > PTT - 1
    filtered_scores = filter(lambda scores: scores["constant"] > PTT - 1 and scores["rating"] > last_top_30["rating"] - 1, scores_others)
    ptt_rec += sorted(filtered_scores, key=itemgetter("time_played"), reverse=False)[0:int(math.ceil(half_nb_scores/2))]
    # Max 1/4 recommendations : Oldest scores not in top 30 with PTT - 1 >= Chart Constant > PTT - 2
    filtered_scores = filter(lambda scores: PTT - 1 >= scores["constant"] > last_top_30["rating"] - 2 and scores["rating"] > last_top_30["rating"] - 1, scores_others)
    ptt_rec += sorted(filtered_scores, key=itemgetter("time_played"), reverse=False)[0:int(math.floor(half_nb_scores/2))]
    # Rest of recommendations : Oldest scores from top 30
    ptt_rec += sorted(scores_top_30, key=itemgetter("time_played"), reverse=False)[0:nb_scores - len(ptt_rec)]
    # Sort by time_played
    ptt_rec = sorted(ptt_rec, key=itemgetter("time_played"), reverse=False)
    return ptt_rec


# Gives [1-20] PTT recommendations
async def ptt_recommendation(message):
    code = await check_id(message.author.id)
    if not code:
        await message.channel.send("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

    nb_scores = 5
    if len(message.content.split(" ")) > 1:
        if message.content.split(" ")[1].isdigit():
            if 1 <= int(message.content.split(" ")[1]) <= 20:
                nb_scores = int(message.content.split(" ")[1])

    api_ = AsyncApi(user_code=code)
    data = await api_.scores()
    songlist = data[0]
    prfl = data[1]
    scores = []
    for elm in data[2:]:
        scores.append(elm)

    ptt_rec = get_ptt_recommendation_scores(scores, prfl, nb_scores)

    msg_emb = discord.Embed(title="Recommendation", type="rich", color=discord.Color.dark_teal())
    msg_emb.set_author(name=f'{prfl["name"]}', icon_url=get_partner_icon(prfl))
    msg_emb.set_footer(text="*(Credit: Okami)*")
    for elm in ptt_rec:
        msg_emb.add_field(name=f'**{songlist[elm["song_id"]]["en"]}\n<{diff[elm["difficulty"]]} '
                               f'{get_diff(elm["constant"])}\>**',
                          value=f'> **{format_score(elm["score"])}** [{clr[elm["best_clear_type"]]}] '
                                f'(Rating: {round(elm["rating"], 3)})\n'
                                f'> Pure: {elm["perfect_count"]} ({elm["shiny_perfect_count"]}) \n'
                                f'> Far: {elm["near_count"]} | Lost: {elm["miss_count"]}\n'
                                f'> Date: {format_time(elm["time_played"]).split(" - ")[0]}')
    await message.channel.send(embed=msg_emb)


# Generate an Arcaea session depending of parameters entered by user
async def session_generator(message):
    code = await check_id(message.author.id)
    if not code:
        await message.channel.send("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

	# Parse parameters
    params = message.content.split(" ")
    if len(params) <= 1 or len(params) % 2 == 0:
        await message.channel.send("> Erreur: Paramètres incorrects, aucune session ne peut être générée (*Exemple : !session 8 4 9 2 9+ 1*)")
        return
    i = 1
    diffs = []
    nb_songs = []
    while i < len(params):
        if not params[i + 1].isdigit():
            await message.channel.send("> Erreur: Le nombre de songs d'une difficulté ne doit contenir que des chiffres (*Exemple : !session 8 4 9 2 9+ 1*)")
            return
        diffs.append(params[i])
        nb_songs.append(int(params[i + 1]))
        i += 2
    
    api_ = AsyncApi(user_code=code)
    data = await api_.scores()
    songlist = data[0]
    prfl = data[1]
    scores = []
    for elm in data[2:]:
        scores.append(elm)

	# Get PTT Recommendations so they can be used in the algorithm
    ptt_rec = get_ptt_recommendation_scores(scores, prfl, 20)
    
    session_songs = []
    for i in range(len(diffs)):
        songs_list = sorted(filter(lambda score: get_diff(score["constant"]) == diffs[i], scores), key=itemgetter("time_played"), reverse=True)
        if len(songs_list) < nb_songs[i]:
            await message.channel.send(f'> Erreur: Impossible de générer {nb_songs[i]} songs de difficulté {diffs[i]} ({len(songs_list)} disponibles)')
            return
        songs_pool = []
        for j in range(len(songs_list)):
            song = songs_list[j]
            is_rec = len(list(filter(lambda rec_score: rec_score["song_id"] == song["song_id"] and rec_score["difficulty"] == song["difficulty"], ptt_rec))) # Check if a song is in PTT Recommendations
            songs_pool.extend(repeat(song, j + 1 + is_rec * 2))
        for j in range(nb_songs[i]):
            song = random.choice(songs_pool)
            while len(list(filter(lambda score: score["song_id"] == song["song_id"] and score["difficulty"] == song["difficulty"], session_songs))) > 0: # Avoid duplicate songs
                song = random.choice(songs_pool)
            session_songs.append(song)
    session_songs = sorted(session_songs, key=itemgetter("constant"), reverse=False)

    msg_emb = discord.Embed(title="Session Generator", type="rich", color=discord.Color.dark_teal())
    msg_emb.set_author(name=f'{prfl["name"]}', icon_url=get_partner_icon(prfl))
    msg_emb.set_footer(text="*(Credit: Okami)*")
    for elm in session_songs:
        msg_emb.add_field(name=f'**{songlist[elm["song_id"]]["en"]}\n<{diff[elm["difficulty"]]} '
                               f'{get_diff(elm["constant"])}\>**',
                          value=f'> **{format_score(elm["score"])}** [{clr[elm["best_clear_type"]]}] '
                                f'(Rating: {round(elm["rating"], 3)})\n'
                                f'> Pure: {elm["perfect_count"]} ({elm["shiny_perfect_count"]}) \n'
                                f'> Far: {elm["near_count"]} | Lost: {elm["miss_count"]}\n'
                                f'> Date: {format_time(elm["time_played"]).split(" - ")[0]}')
    await message.channel.send(embed=msg_emb)


# Display help
async def get_help(message):
    await message.channel.send("**Help:**\n"
                               "> !art: Displays a random art tweet\n"
                               "> !best [1-30]: Sends the Top [1-30] plays (Default: 30)\n"
                               "> !help: Sends this message\n"
                               "> !profile: Displays the user profile\n"
                               "> !rec [1-20]: Sends [1-20] recommended plays to increase PTT (Default: 5)\n"
                               "> !session [args]: Generate a personalized Arcaea session (Example : !session 8 4 9 2 9+ 1)\n"
                               "> !recent: Sends the latest play\n"
                               "> !register: Links a user code to a Discord account")


async def check_id(id):
    async with aiosqlite.connect(f"players.db") as db:
        async with db.execute(f"SELECT * FROM players WHERE discord_id = {id}") as c:
            res = await c.fetchall()
            if len(res) != 0:
                return str("{0:09d}").format(res[0][1])
            else:
                return None


# Format score as 00'000'000
def format_score(score):
    return "{0:08d}".format(score)[:2] + "'" + "{0:08d}".format(score)[2:5] + "'" + "{0:08d}".format(score)[5:]


# Format player code as 000 000 000
def format_code(code):
    return code[:3] + " " + code[3:6] + " " + code[6:]


# Get song difficulty based on PTT (Is incorrect for Moonheart BYD)
def get_diff(cst):
    if 9.6 < cst < 11:
        if cst < 10:
            return "9+"
        elif cst < 10.6:
            return "10"
        else:
            return "10+"
    else:
        return str(cst).split(".")[0]


# Get URL asset for Partner icon
def get_partner_icon(prfl):
    if prfl["is_char_uncapped"]:
        return partners + str(prfl["character"]) + "u_icon.png"
    else:
        return partners + str(prfl["character"]) + "_icon.png"


# Format time; Arcapi returns a delta from current time instead of EPOCH
def format_time(ts):
    sec = int(time.time() - ts/1000)
    days = int(sec / 86400)
    hours = int(sec % 86400 / 3600)
    minutes = int(sec % 86400 % 3600 / 60)
    seconds = int(sec % 86400 % 3600 % 60)

    res = datetime.today() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    return res.strftime("%d/%m/%Y - %H:%M")
