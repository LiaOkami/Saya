import discord
import requests

from constants import diff, clr, api_url, headers
from utils import check_id, get_diff, get_partner_icon, get_ptt_recommendation_scores, format_time, format_score, \
    send_back_error, query_songname, query_constant, send_back_http_error


# Gives [1-20] PTT recommendations
async def ptt_recommendation(message):
    code = await check_id(message.author.id)
    if not code:
        await message.reply("> Erreur: Aucun code Arcaea n'est lié a ce compte Discord (*!register*)")
        return

    nb_scores = 5
    if len(message.content.split(" ")) > 1:
        if message.content.split(" ")[1].isdigit():
            if 1 <= int(message.content.split(" ")[1]) <= 20:
                nb_scores = int(message.content.split(" ")[1])

    response_best_30 = requests.post(f"{api_url}/user/best30", headers=headers,
                                     params={"usercode": code, "overflow": 400}, timeout=180)
    if not response_best_30.ok:
        await send_back_http_error(message, response_best_30.status_code)
        return
    best_30_json = response_best_30.json()
    if best_30_json['status'] != 0:
        await send_back_error(message, best_30_json)
        return

    response_info = requests.post(f"{api_url}/user/info", headers=headers, params={"usercode": code}, timeout=180)
    if not response_info.ok:
        await send_back_http_error(message, response_info.status_code)
        return
    info_json = response_info.json()
    if info_json['status'] != 0:
        await send_back_error(message, info_json)
        return

    profile = info_json['content']
    scores = []
    for elm in best_30_json['content']['best30_list']:
        scores.append(elm)

    for elm in best_30_json['content']['best30_overflow']:
        scores.append(elm)

    ptt_rec = get_ptt_recommendation_scores(scores, profile, nb_scores)

    msg_emb = discord.Embed(title="Recommendation", type="rich", color=discord.Color.dark_teal())
    msg_emb.set_author(name=f'{profile["name"]}', icon_url=get_partner_icon(profile))
    msg_emb.set_footer(text="*(Credit: Okami)*")
    for elm in ptt_rec:
        msg_emb.add_field(name=f'**{query_songname(elm["song_id"])}\n<{diff[elm["difficulty"]]} '
                               f'{get_diff(query_constant(elm))}\>**',
                          value=f'> **{format_score(elm["score"])}** [{clr[elm["best_clear_type"]]}] '
                                f'(Rating: {round(elm["rating"], 3)})\n'
                                f'> Pure: {elm["perfect_count"]} ({elm["shiny_perfect_count"]}) \n'
                                f'> Far: {elm["near_count"]} | Lost: {elm["miss_count"]}\n'
                                f'> Date: {format_time(elm["time_played"]).split(" - ")[0]}')
    await message.reply(embed=msg_emb)
