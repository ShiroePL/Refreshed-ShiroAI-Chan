from shared_code.anilist import anilist_api_requests
from modules.db_module import connect_to_phpmyadmin
import hashlib
import re
from src.config import api_keys
from api_functions.anilist_ai_service import AnimeAIService

host = api_keys.host_name
database = api_keys.db_name
user = api_keys.user_name
password = api_keys.db_password

# Initialize the AI service
anime_ai_service = AnimeAIService()

def hash_username(username):
    # Remove any characters that are not alphanumeric (letters and numbers)
    username = username.lower()
    sanitized_username = re.sub(r'[^a-zA-Z0-9]', '', username)
    # Compute the SHA-1 hash of the original username
    hashed_username = hashlib.sha1(username.encode()).hexdigest()
    # Combine the sanitized username and the hash
    combined_username = f"{sanitized_username}{hashed_username}"
    return combined_username

def get_progress_emoji(progress, total, content_type):
    if progress == 0:
        return "🚫"
    elif progress >= total / 2: 
        return "🏆"
    else:
        if content_type == "ANIME":
            return "📺"
        else:
            return "📖"

async def show_media_list(content_type):
    """Get the 10 newest anime/manga formatted for prompt
    media_type: 'anime' or 'manga'"""
    try:
        discord_username = "madrus"  # Hardcoded username since it's for personal use
        formatted_string, media_list = anilist_api_requests.get_10_newest_entries(content_type)
        

        title_name = "anime" if content_type == "ANIME" else "manga"
        response_text = f"Your {title_name} list:\n"

        for media in media_list:  # Use the media_list instead of the formatted string
            try:
                name = media['english'] or media['romaji']
                total = media['chapters'] if content_type == 'MANGA' else media['episodes']
                progress = media['progress']
                media_id = media['mediaId']
                status = media['on_list_status']
                
                emoji = get_progress_emoji(progress, total, content_type)
                
                progress_text = f"Episodes: {progress}/{total}" if content_type == "ANIME" else f"Chapters: {progress}/{total}"
                status_text = f"[{status}]" if status else ""
                response_text += f"{emoji} {name} {status_text} - ID: {media_id} - {progress_text}\n"
                
            except Exception as e:
                print(f"Error processing media entry: {e}")
                continue

        print("----- media list successfully sent -------------")
        return response_text
        
    except Exception as e: 
        print(f"Error in show_media_list: {e}")
        print("-----END media list with crash-------------")
        return "Oh, something went wrong while fetching your media list."

# BIG TO DO , NEED TO HASH AND STORE TOKEN, PROBABLY USING VALUT, TO MUCH FOR NOW
async def update_media_list(user_question, content_type):
    """Get the 10 newest anime/manga formatted for prompt
    media_type: 'anime' or 'manga'"""
    try:
        discord_username = "madrus"  # Hardcoded username since it's for personal use
        connect_to_phpmyadmin.check_user_in_database(discord_username)
        database_messages = connect_to_phpmyadmin.retrieve_chat_history_from_database(discord_username)

        print("content type: " + content_type)
        media_list,_ = anilist_api_requests.get_10_newest_entries(content_type)

        question = f"Madrus: I will give you list of my 10 most recent watched/read {content_type} from site AniList. Here is this list:{media_list}. I want you to remember this because in next question I will ask you to update episodes/chapters of one of them."
        database_messages.append({"role": "user", "content": question})
        
        # send to open ai for answer
        answer = "Okay, I will remember it, Madrus. I'm waiting for your next question. Give it to me nyaa."
        database_messages.append({"role": "assistant", "content": answer})

        #################################################################################################
        end_question = "I would like you to answer me giving me ONLY THIS: ' title:<title>,id:<id>,"
        extra = " episodes:<episodes>'. Nothing more." if content_type == "ANIME" else " chapters:<chapters>'. Nothing more."
        question = f"Madrus: {user_question}. {end_question}{extra}"

        database_messages.append({"role": "user", "content": question})

        print("database_messages: " + str(database_messages))

        # Process through AI service
        answer = await anime_ai_service.process_anime_update(user_question, database_messages)
        if not answer:
            return "Oh, something went wrong while updating your media list."
            
        print("answer from AI: " + answer)
        
        # START find ID and episodes number of updated anime
        # The regex pattern             
        pattern = r"id:\s*(\d+),\s*episodes:\s*(\d+)" if content_type == "ANIME" else r"id:\s*(\d+),\s*chapters:\s*(\d+)"

        # Use re.search to find the pattern in the text
        match = re.search(pattern, answer)
        
        if match:
            # match.group(1) contains the id, match.group(2) contains the episodes number
            updated_id = match.group(1)
            updated_info = match.group(2)
            print(f"reformatted request: id:{updated_id}, type:{content_type}: ep/chap{updated_info}")
            
            anilist_api_requests.change_progress(updated_id, updated_info, content_type)
            return answer

        return "Could not parse the AI response correctly."

    except Exception as e: 
        print(e)
        print("---------------------------------")
        return "Oh, something went wrong while updating your media list."