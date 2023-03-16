import json

#load data
kuudere_ids = []

try:
    file = open("data/anilist.json", "r")
    kuudere_ids = json.loads(file.read())
    file.close()
except:
    print("Could not open AniList kuudere database")

try:
    file = open("database/anilist.json", "r")
    post_db = json.loads(file.read())
    file.close()

    for character_id in post_db.items():
        if character_id is not None:
            kuudere_ids.append(character_id)
except:
    print("Could not open Reddit kuudere database")

#generate website
file = open("index.html", "w")
for kuudere_id in kuudere_ids:
    file.write("<a href='https://anilist.co/character/{}'>{}</a><br>".format(kuudere_id, kuudere_id))
file.close()
