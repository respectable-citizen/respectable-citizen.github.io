import json
import anilist

def lookup_character(character_id):
    result = anilist.do_request({
        "query": """query ($id: Int) { # Define which variables will be used in the query (id)
          Character (id: $id) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
            id
            name {
              userPreferred
            }
            image {
              large
            }
          }
        }""",
        "variables": {
            "id": character_id
        }
    })
    
    return result["Character"]

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
    character = lookup_character(kuudere_id)
    file.write("<a href='https://anilist.co/character/{}'><img src='{}'/></a><br>".format(kuudere_id, character["image"]["large"]))
file.close()
