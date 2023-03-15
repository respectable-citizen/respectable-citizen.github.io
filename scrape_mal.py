import requests
import re
import anilist
import html

character_regex = r"borderClass.+?character\/(\d+)\">(.+?)<"
media_regex = r"valign=\"top\" class=\"borderClass\"><a href=\".+?\/(anime|manga)\/(\d+).+?>(.+?)<\/a"

def get_characters():
    r = requests.get("https://myanimelist.net/clubs.php?cid=9188")
   
    characters = {}

    for match in re.finditer(character_regex, r.text):
        character_name = match.group(2).split(", ")
        character_name.reverse()
        character_name = " ".join(character_name)
        characters[match.group(1)] = html.unescape(character_name.strip())

    return characters

def get_shortest_key(dictionary):
    shortest_length = 9999
    shortest_key = None

    for key in dictionary:
        if len(key) < shortest_length:
            shortest_key = key
            shortest_length = len(key)

    return shortest_key

def get_character_media(character_id):
    r = requests.get("https://myanimelist.net/character/{}".format(character_id))
    
    media = []
    for match in re.finditer(media_regex, r.text):
        media_type = match.group(1)
        media_id = match.group(2)
        media_name = html.unescape(match.group(3))

        media.append((media_type, media_name))

    return media

characters = get_characters()

for character_id in characters:
    character_name = characters[character_id]
    media = get_character_media(character_id)
    anilist_id = None
    for media_source in media:
        (media_type, media_name) = media_source
        anilist_id_candidate = anilist.search_anilist_id(media_type, media_name, character_name)

        if anilist_id_candidate:
            anilist_id = anilist_id_candidate
            break

    print(media_type, media_name)
    print("{}:{}".format(character_name, anilist_id))
