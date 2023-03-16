import requests
import re
import time
import anilist
import json

title_regex = r".*?(([A-Z][a-z]+ ?)+).*?[{\[](.+)[}\]]"

def get_posts(end=None):
    url = "https://reddit.com/r/kuudere/new.json"
    if end:
        url += "?after={}".format(end)
    r = requests.get(url, headers={"User-Agent": "KuudereBot 1.0"})
    return r.json()["data"]["children"]

def handle_post(post_id, character_name, source):
    character_id = anilist.search_characters(character, source)
    print("{}: {}, {}, {}".format(post_id, character_name, source, character_id))
    post_db[post_id] = character_id

#load post database
post_db = {}

try:
    file = open("data/reddit.json")
    post_db = json.loads(file.read())
    file.close()
except:
    print("Couldn't open Reddit database, assuming first run")

posts = get_posts("")
end = None
while len(posts):
    for post in posts:
        post_id = post["data"]["name"]
        if post_id in post_db:
            #already handled this post and everything after it so the program's job is done
            print("Handled all posts, saving database")

            file = open("data/reddit.json", "w")
            file.write(json.dumps(post_db))
            file.close()

            print("Saved, exiting")
            exit()

        title = post["data"]["title"]
        result = re.search(title_regex, title)
        if result:
            character = result.group(1).strip()
            source = result.group(3).strip()
            handle_post(post_id, character, source)

        time.sleep(1)
        end = post_id
    
    posts = get_posts(end)
    print(end)
