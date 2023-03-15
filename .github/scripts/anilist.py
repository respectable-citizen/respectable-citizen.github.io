import requests
import jellyfish
import time

first_request_timestamp = None

def do_paginated_search(json, path):
    global first_request_timestamp

    results = []
    while True:
        if not first_request_timestamp:
            first_request_timestamp = time.time()

        r = requests.post("https://graphql.anilist.co", json=json)
        result_list = r.json()["data"]
        
        print(r.headers)
        print(r.json())
        print(r.headers["X-RateLimit-Remaining"], "requests remaining")
        if r.headers["X-RateLimit-Remaining"] == "5":
            time.sleep(60)

        page = None
        for key in path:
            if "pageInfo" in result_list:
                page = result_list["pageInfo"]

            result_list = result_list[key]

        results += result_list

        if not page["hasNextPage"]:
            break

        json["variables"]["page"] += 1

    return results

def get_media(character_id):
    r = do_paginated_search({
        "query": "query character($id:Int,$page:Int,$sort:[MediaSort],$onList:Boolean,$withRoles:Boolean = false){Character(id:$id){id name{first middle last full native userPreferred alternative alternativeSpoiler}image{large}favourites isFavourite isFavouriteBlocked description age gender bloodType dateOfBirth{year month day}media(page:$page,sort:$sort,onList:$onList)@include(if:$withRoles){pageInfo{total perPage currentPage lastPage hasNextPage}edges{id characterRole voiceActorRoles(sort:[RELEVANCE,ID]){roleNotes voiceActor{id name{userPreferred}image{large}language:languageV2}}node{id type isAdult bannerImage title{userPreferred}coverImage{large}startDate{year}mediaListEntry{id status}}}}}}",
        "variables": {
            "id": character_id,
            "page": 1,
            "sort": "POPULARITY_DESC",
            "onList": None,
            "withRoles": True
        }
    }, ["Character", "media", "edges"])

    media = map(lambda media: media["node"]["title"]["userPreferred"], r)

    return list(media)

#search for characters by name, find correct one using source
def search_characters(character, source):
    characters = do_paginated_search({
        "query": "query($page:Int = 1 $id:Int $search:String $isBirthday:Boolean $sort:[CharacterSort]=[FAVOURITES_DESC]){Page(page:$page,perPage:20){pageInfo{total perPage currentPage lastPage hasNextPage}characters(id:$id search:$search isBirthday:$isBirthday sort:$sort){id name{userPreferred}image{large}}}}",
        "variables": {
            "page": 1,
            "type": "CHARACTERS",
            "search": character,
            "sort": "SEARCH_MATCH"
        }
    }, ["Page", "characters"])

    if len(characters) == 0:
        return None

    evaluated_characters = {}
    for character in characters:
        media = get_media(character["id"])
   
        highest = 0
        for media_source in media:
            similarity = jellyfish.jaro_winkler_similarity(media_source.lower(), source.lower())
            if similarity > highest:
                highest = similarity

        evaluated_characters[character["id"]] = highest

    character_id = max(evaluated_characters, key=evaluated_characters.get)
    if evaluated_characters[character_id] >= 0.80:
        return character_id
    else:
        return None

def search_anilist_id(media_type, media_name, character_name):
    media_name = media_name.split(" (")[0]

    media = do_paginated_search({
       "query": "query($page:Int = 1 $id:Int $type:MediaType $isAdult:Boolean = false $search:String $format:[MediaFormat]$status:MediaStatus $countryOfOrigin:CountryCode $source:MediaSource $season:MediaSeason $seasonYear:Int $year:String $onList:Boolean $yearLesser:FuzzyDateInt $yearGreater:FuzzyDateInt $episodeLesser:Int $episodeGreater:Int $durationLesser:Int $durationGreater:Int $chapterLesser:Int $chapterGreater:Int $volumeLesser:Int $volumeGreater:Int $licensedBy:[Int]$isLicensed:Boolean $genres:[String]$excludedGenres:[String]$tags:[String]$excludedTags:[String]$minimumTagRank:Int $sort:[MediaSort]=[POPULARITY_DESC,SCORE_DESC]){Page(page:$page,perPage:20){pageInfo{total perPage currentPage lastPage hasNextPage}media(id:$id type:$type season:$season format_in:$format status:$status countryOfOrigin:$countryOfOrigin source:$source search:$search onList:$onList seasonYear:$seasonYear startDate_like:$year startDate_lesser:$yearLesser startDate_greater:$yearGreater episodes_lesser:$episodeLesser episodes_greater:$episodeGreater duration_lesser:$durationLesser duration_greater:$durationGreater chapters_lesser:$chapterLesser chapters_greater:$chapterGreater volumes_lesser:$volumeLesser volumes_greater:$volumeGreater licensedById_in:$licensedBy isLicensed:$isLicensed genre_in:$genres genre_not_in:$excludedGenres tag_in:$tags tag_not_in:$excludedTags minimumTagRank:$minimumTagRank sort:$sort isAdult:$isAdult){id synonyms title{userPreferred english}coverImage{extraLarge large color}startDate{year month day}endDate{year month day}bannerImage season seasonYear description type format status(version:2)episodes duration chapters volumes genres isAdult averageScore popularity nextAiringEpisode{airingAt timeUntilAiring episode}mediaListEntry{id status}studios(isMain:true){edges{isMain node{id name}}}}}}",
       "variables": {
           "page": 1,
           "type": media_type.upper(),
           "sort": "SEARCH_MATCH",
           "search": media_name
        }
    }, ["Page", "media"])

    evaluated_media = {}
    for media_source in media:
        media_names = [media_source["title"]["userPreferred"]] + [media_source["title"]["english"]] + media_source["synonyms"]
        media_names = list(filter(None, media_names))

        for candidate_name in media_names:
            similarity = jellyfish.jaro_winkler_similarity(media_name.lower(), candidate_name.lower())
            if media_source["id"] not in evaluated_media or similarity > evaluated_media[media_source["id"]]:
                evaluated_media[media_source["id"]] = similarity

    found_media = {k:v for (k,v) in evaluated_media.items() if v > 0.80}

    characters = {}
    for media_id in found_media:
        character = search_source_characters(media_id, media_type, character_name)
        if character:
            (character_id, similarity) = character
            characters[character_id] = similarity

    if len(characters) == 0:
        return None

    character_id = max(characters, key=characters.get)
    similarity = characters[character_id]
    if similarity > 0.80:
        return character_id
    else:
        return None

def search_source_characters(media_id, media_type, character_name):
    characters = do_paginated_search({
        "query": "query media($id:Int,$page:Int){Media(id:$id){id characters(page:$page,sort:[ROLE,RELEVANCE,ID]){pageInfo{total perPage currentPage lastPage hasNextPage}edges{id role name voiceActorRoles(sort:[RELEVANCE,ID]){roleNotes dubGroup voiceActor{id name{userPreferred}language:languageV2 image{large}}}node{id name{userPreferred alternative alternativeSpoiler}image{large}}}}}}",
        "variables": {
            "id": media_id,
            "type": media_type.upper(),
            "page": 1
        }
    }, ["Media", "characters", "edges"])

    character_id = None
    highest_similarity = 0

    for character in characters:
        character_names = [character["node"]["name"]["userPreferred"]] + character["node"]["name"]["alternative"] + character["node"]["name"]["alternativeSpoiler"]
        character_names = list(filter(None, character_names))

        for candidate_name in character_names:
            similarity = jellyfish.jaro_winkler_similarity(candidate_name.lower(), character_name.lower())
            if similarity > highest_similarity:
                character_id = character["node"]["id"]
                highest_similarity = similarity
    
    if highest_similarity >= 0.80:
        return (character_id, highest_similarity)
    else:
        return None
