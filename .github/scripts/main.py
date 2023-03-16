import requests
import re
import time
import anilist

title_regex = r".*?(([A-Z][a-z]+ ?)+).*?[{\[](.+)[}\]]"

def get_posts(end=None):
    url = "https://reddit.com/r/kuudere.json"
    if end:
        url += "?after={}".format(end)
    r = requests.get(url, headers={"User-Agent": "KuudereBot 1.0"})
    return r.json()["data"]["children"]

posts = get_posts("t3_yrfjhg")
end = None
while len(posts):
    for post in posts:
        end = post["data"]["name"]
        
        title = post["data"]["title"]
        result = re.search(title_regex, title)
        if result:
            character = result.group(1).strip()
            source = result.group(3).strip()
            character_id = search_characters(character, source)
            print("{} [{}]: {}".format(character, source, character_id))

        time.sleep(10)
    posts = get_posts(end)
    print(end)
