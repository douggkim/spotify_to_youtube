from googleapiclient.discovery import build
import search_video
import create_playlist
import add_to_playlist
from SpotifyManager import spotifyManager
import pprint
import time
import pandas as pd
import csv
import datetime
import os, glob

# TODO : get all the credentials
with open("spotify_to_youtube/CONFIG.txt") as file:
    SPOTIFY_CLIENT_ID = file.readline().strip()
    SPOTIFY_CLIENT_TOKEN = file.readline().strip()
    USER_ID = file.readline().strip()
    SPOTIFY_REDIRECT_URI = "http://example.com"

# TODO  : load spotify manager
spotifymanager = spotifyManager(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_TOKEN, SPOTIFY_REDIRECT_URI)

# TODO  : get the id of the playlist
playlist= spotifymanager.search_playlist(user_id=USER_ID)
for _ in range(len(playlist)): 
    print(f"<<{_}>> Playlist : {playlist[_]['name']}")
chosen_playlist_num = int(input("\nType the number of the playlist you want to migrate (ex. 1 ): "))

# TODO : Open the csv file
path="/Users/dougkim/dev/spotify_to_youtube"
target_files = glob.glob(path+"/*.csv")
for filename in target_files :
    print(filename)
    songs_to_add_df = pd.read_csv(filename, index_col=None)
    songs_to_add_df.to_csv(path+'/songs_to_add.csv', index=False)

# TODO : if there's no file, create a new dataframe 
try:
    songs_to_add_df
except:  
    songs_to_add_df = pd.DataFrame(columns=['spotify_playlist','spotifyid','youtube_playlist_id','youtube_video_id','keyword'])

# TODO : get the items of the playlist 
playlist_items = spotifymanager.get_playlist_items(playlist_id=playlist[chosen_playlist_num]["id"],limit=100, offset=0)
chosen_playlist_name = playlist[chosen_playlist_num]['name']


for _ in range(int(playlist_items["total"]/100)+1):
    playlist_items = spotifymanager.get_playlist_items(playlist_id=playlist[chosen_playlist_num]["id"],limit=100, offset=_*100)

    for item_num in range(len(playlist_items["items"])): 
        search_keyword = playlist_items["items"][item_num]["track"]["artists"][0]["name"] + " " + playlist_items["items"][item_num]["track"]["name"]
        search_id = playlist_items["items"][item_num]["track"]["id"]

        # TODO :  if search_id not in spotifyid col, add the new row (song) to the data frame 
        if not songs_to_add_df['spotifyid'].str.contains(search_id).any() :
            search_dict = {'spotify_playlist': [chosen_playlist_name], 'spotifyid':[search_id], 'keyword':[search_keyword]}
            songs_to_add_df = pd.concat([songs_to_add_df.reset_index(drop=True),pd.DataFrame(search_dict).reset_index(drop=True)])

print(f"\nNumber of Songs retrieved from Spotify : {len(songs_to_add_df)}")

# TODO : check if there are songs to add 
if len(songs_to_add_df)==0:
    print("No New Song to Add")
else: 
    # TODO : Create Youtube Playlist
    youtube = add_to_playlist.get_authenticated_service()
    if songs_to_add_df[songs_to_add_df['spotify_playlist']==chosen_playlist_name].iloc[0].isna()['youtube_playlist_id']:
        target_playlist_id = create_playlist.add_playlist(youtube,title=f"{playlist[chosen_playlist_num]['name']}",description="test_playlist")    
        songs_to_add_df.loc[songs_to_add_df['spotify_playlist']==chosen_playlist_name,'youtube_playlist_id'] = target_playlist_id
    else:
        # TODO : If the playlist is already created, get the id of the playlist 
        target_playlist_id = songs_to_add_df[songs_to_add_df['spotify_playlist']==chosen_playlist_name].iloc[0]['youtube_playlist_id']

    # TODO  : Add the videos to the playlist 
    failed_keywords = []
    
    for row in songs_to_add_df[songs_to_add_df['spotify_playlist']==chosen_playlist_name].iterrows():
        # TODO : iterate over songs which has not been added to the playlist 
        if pd.isna(row[1]['youtube_video_id']): 
            for attempt in range(6):
                if attempt==5: 
                    # TODO Quit the program if it fails more than 5 times (probably exceeded quota)
                    songs_to_add_df.to_csv(path+'/songs_to_add.csv', mode='w+')
                    exit()

                time.sleep(0.5)
                try: 
                    video_results = search_video.youtube_search(row[1]['keyword'], 10)
                    target_video_id = video_results[0][-14:].translate(str.maketrans({"(":"",")":""," ":""}))
                    # TODO Add a new video to the playlist 
                    added_results =  add_to_playlist.add_video(youtube=youtube,playlistid=target_playlist_id,videoid=target_video_id)    
                    # TODO Add the id the of the new video to the data frame 
                    songs_to_add_df.loc[songs_to_add_df['spotifyid']==row[1]['spotifyid'],'youtube_video_id'] = target_video_id
                    break
                except Exception as e: 
                    print(f"An error occurred : {e}")
                    time.sleep(3)
                    
    # TODO ADD The added songs to csv file                         
    songs_to_add_df.to_csv(path+'/songs_to_add.csv', mode='w+', index=False)


