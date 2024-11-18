"""
What You Need:
    #API Token: Get your Bearer token from inspecting https://7tv.app/emotes, going to networks and check the headers of a gql request 
    #Telegram Bot Token: Create a bot on Telegram and copy the token.
    #User ID: Get your telegram User ID from (for owning the pack).
    #Channel ID/ EmoteSet ID: Either the Twitch channel you want to copy or the Emote set ID from 7tv.app
"""

import telebot
import requests
import os, shutil
import subprocess
from io import BytesIO
from PIL import Image, ImageSequence

def download_webp_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print("Image downloaded successfully.")
    else:
        print("Failed to download image.")

def download_webp_image_as_png(url, output_path, height):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    width = int(height * image.width / image.height)
    resized_image = image.resize((width, height))
    new_image = Image.new("RGBA", (512, height), (0, 0, 0, 0))
    x = (new_image.width - resized_image.width) // 2
    y = (new_image.height - resized_image.height) // 2
    new_image.paste(resized_image, (x, y))
    new_image.save(output_path, "PNG")

def convert_webp_to_webm(input_path, output_path, height):
    """Convert WebP to WebM (animated stickers) using Pillow"""
    try:
        # Ensure the frames directory is cleared
        shutil.rmtree("frames", ignore_errors=True)
        os.makedirs("frames", exist_ok=True)

        # Extract frames from the WebP animation
        with Image.open(input_path) as webp_image:
            frame_idx = 0
            for frame in ImageSequence.Iterator(webp_image):
                frame_resized = frame.resize((512, height), Image.Resampling.LANCZOS)
                frame_path = f"frames/img_{frame_idx:03d}.png"
                frame_resized.save(frame_path, "PNG")
                frame_idx += 1

        # Convert extracted frames to WebM using webptools
        command = [
            'ffmpeg', '-y', '-framerate', '25', '-f', 'image2', '-i', 'frames/img_%03d.png',
            '-vf', f'scale=512:{height}', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
            '-t', '2.8', output_path
        ]
        subprocess.run(command)
        print(f"Converted {input_path} to {output_path}.")
    except Exception as e:
        print("Error converting WebP to WebM:", e)

def getUser(username, token):
    """
    :param username: username of the channel to search and get the id of
    :param token: bearer authorization token from 7tv.app, inspect the page and get it
    """

    url = "https://7tv.io/v3/gql"
    payload = {
        "operationName": "SearchUsers",
        "variables": {"query": username},
        "query": "query SearchUsers($query: String!) {\n users(query: $query) {\n id\n username\n display_name\n roles\n style {\n color\n __typename\n }\n avatar_url\n __typename\n }\n}"
    }
    headers = {"Authorization": token}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(response)
    if response.status_code == 200:
        data = response.json()
        print(data['data']['users'][0]['id'])
        return data['data']['users'][0]['id']
    else:
        print("Request failed with status code:", response.status_code)
    return None

def getEmotes(userID: int|str = None, setID: int|str = None):
    """
     :param userID: 7tv channel id
     :type name: :obj:`str` or :obj:`int`

     :param setID: 7tv emote set id
     :type name: :obj:`str` or :obj:`int`
    """
    emoteurls = []
    url =  f"https://7tv.io/v3/emote-sets/{userID}" if userID else f"https://7tv.io/v3/emote-sets/{setID}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for emote in data["emotes"]:
            emoteurls.append(f'https://cdn.7tv.app/emote/{emote["id"]}/2x.webp')
    print(response)
    return emoteurls

def makePack(tg_Token: str, tg_user_id: int, 
             pack_title:str, pack_name:str, animated:bool, 
             target_height:int|float, channelID: int|str = None,
             emotesetID: int|str = None) -> str|bool:
    """
     :param channelID: channels username, the channel to get emotes of
     :type name: :obj:`str` or :obj:`int`
     
     :param tg_Token: your telegram bot's token
     :type name: :obj:`str`
     
     :param tg_user_id: pack owner user's telegram account id, an integer, eg: 1026202266
     :type name: :obj:`int`

     :param pack_title: your telegram bot's token
     :type name: :obj:`str`

     :param pack_name: your sticker pack name, no spaces and no special characters other than underscore
     :type name: :obj:`str`

     :param animated: animated true or static false, each type can hold varying quantity of stickers 
        with static being the most
     :type name: :obj:`str`

     :param target_height: your sticker pack height for all stickers
     :type name: :obj:`float` or :obj:`int`
    """
    
    bot = telebot.TeleBot(tg_Token)
    emoteurls = []
    if channelID: emoteurls = getEmotes(channelID)
    else: emoteurls = emoteurls = getEmotes(emotesetID)
    pack_name += "_by_" + bot.user.username
    result = False

    if animated:
        emote_name = emoteurls[0]
        webp_input_path = 'input.webp'
        webm_output_path = 'output.webm'
        download_webp_image(emote_name, webp_input_path)
        convert_webp_to_webm(webp_input_path, webm_output_path, target_height)
        file = open(webm_output_path, 'rb')
        bot.create_new_sticker_set(tg_user_id, pack_name, pack_title, emojis=["👍"], webm_sticker=file)
        for url in emoteurls[1:]:
            download_webp_image(url, webp_input_path)
            convert_webp_to_webm(webp_input_path, webm_output_path, target_height)
            file = open(webm_output_path, 'rb')
            bot.add_sticker_to_set(tg_user_id, pack_name, emojis=["👍"], webm_sticker=file)
        result = True

    else:
        emote_name = emoteurls[0]
        png_output_path = "output.png"
        download_webp_image_as_png(emote_name, png_output_path, target_height)
        file = open(png_output_path, 'rb')
        bot.create_new_sticker_set(tg_user_id, pack_name, pack_title, emojis=["👍"], png_sticker=file)
        for url in emoteurls[1:]:
            print(url)
            download_webp_image_as_png(url, png_output_path, target_height)
            file = open(png_output_path, 'rb')
            bot.add_sticker_to_set(tg_user_id, pack_name, emojis=["👍"], png_sticker=file)
        result = True

    if result: return "https://t.me/addstickers/" + pack_name
    else: result


token = """Bearer <token>"""

"""
Copying a Twitch Channel:

channelName = "Psp1g"
channelID = getUser(channelName, token)
emotesetID = None
"""

channelID = None
emotesetId = "<emote set id>"
tg_Token = "<bot token>"
tg_user_id = 123456789
pack_title = "Pack title"
pack_name = "Pack_link_name"
stickers_height = 200

pack_link = makePack(
    channelID=channelID,
    emotesetID=emotesetId, 
    tg_Token=tg_Token, 
    tg_user_id=tg_user_id, 
    pack_title=pack_title, 
    pack_name=pack_name, 
    animated=True,
    target_height=stickers_height
)

if pack_link: print(pack_link)
