import requests
import telebot
import subprocess
import os, shutil
from PIL import Image
from io import BytesIO

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
    try: shutil.rmtree("frames")
    except: pass

    try: os.remove(output_path)
    except: pass

    os.mkdir("frames")

    command = ['magick', input_path, '-gravity', 'center', '-background', 'transparent', '-extent', f'512x{format(height)}', "frames/img.png"]
    subprocess.run(command)
    
    command = [
        'ffmpeg', '-y', '-framerate', '25', '-f', 'image2', '-i', 'frames/img-%0d.png', '-vf', f'scale=512:{height}',
        '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-t', '2.8', output_path
    ]
    subprocess.run(command)

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

def getEmotes(userID):
    if userID:
        emoteurls = []
        url = f"https://7tv.io/v3/emote-sets/{userID}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for emote in data["emotes"]:
                emoteurls.append(f'https://cdn.7tv.app/emote/{emote["id"]}/2x.webp')
        print(response)
        return emoteurls

def makePack(channelID: int|str, tg_Token: str, tg_user_id: int, 
             pack_title:str, pack_name:str, pack_type:str, 
             target_height:int|float) -> str|bool:
    """
     :param channelID: channels username, the channel to get emotes of
     :type name: :obj:`str` or :obj:`int`
     
     :param tg_Token: your telegram bot's token
     :type name: :obj:`str`
     
     :param tg_user_id: pack owner user's telegram account id, an integer, eg: 1026202266
     :type name: :obj:`int`

     :param pack_title: your telegram bot's token
     :type name: :obj:`str`

     :param pack_name: your sticker pack name
     :type name: :obj:`str`

     :param pack_type: your sticker pack type, animated or static, each type can hold varying quantity of stickers 
        with static being the most
     :type name: :obj:`str`

     :param target_height: your sticker pack height for all stickers
     :type name: :obj:`float` or :obj:`int`
    """
    
    bot = telebot.TeleBot(tg_Token)
    emoteurls = getEmotes(channelID)
    result = False

    pack_name += "_by_" + bot.user.username
    print(pack_name)

    if pack_type == "animated":
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

    if pack_type == "static":
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

    if result: return pack_name
    else: result


#example
#replace all of the values under to fit your needs
token = """Bearer <your_bearer_token>"""
channelName = "Psp1g"
channelID = getUser(channelName, token)

tg_Token = "<your_bot_token>"
tg_user_id = 1026202266
pack_title = "Psp's 7tv Emotes"
pack_name = "Psp7TV"
pack_type = "static"
stickers_height = 100

makePack(
    channelID=channelID, 
    tg_Token=tg_Token, 
    tg_user_id=tg_user_id, 
    pack_title=pack_title, 
    pack_name=pack_name, 
    pack_type=pack_type,
    target_height=stickers_height
)
