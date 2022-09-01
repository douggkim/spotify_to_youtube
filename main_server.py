import os
from flask import Flask, session, request, redirect, url_for, render_template
from flask_bootstrap import Bootstrap
from flask_session import Session
import spotipy
import pandas as pd
import os, glob
import pprint
import search_video
import create_playlist
import add_to_playlist
import time 

with open("spotify_to_youtube/CONFIG.txt") as file:
    SPOTIPY_CLIENT_ID = file.readline().strip()
    SPOTIPY_CLIENT_SECRET = file.readline().strip()
    SPOTIPY_REDIRECT_URI = "http://localhost:8080"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Bootstrap(app)
Session(app)


@app.route('/')
def index():

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                                               scope='user-read-currently-playing playlist-modify-private',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 3. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/playlists">my playlists</a> | ' \
           f'<a href="/currently_playing">currently playing</a> | ' \
           f'<a href="/migrate_to_youtube">migrate a playlist to youtube</a> | ' \
        f'<a href="/current_user">me</a>' \



@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()

@app.route('/migrate_to_youtube', methods=['GET', 'POST'])
def migrate_to_youtube():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    if request.method =='GET': 
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        user_playlist_result = spotify.current_user_playlists(limit=50)["items"]
        
        result_playlist = []

        for playlist in user_playlist_result:
            playlist_element = {}
            playlist_element["id"] = (playlist["id"])
            playlist_element["name"] = playlist["name"]
            playlist_element['images'] = playlist["images"][0]["url"]
            result_playlist.append(playlist_element)

        return render_template("sp_to_youtube_playlists.html", result_playlist = result_playlist)
    
        
@app.route('/start_migration/<playlist_id>', methods=['GET', 'POST'])
def start_migration(playlist_id:str):
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')


    # TODO : Open the csv file
    path="/Users/dougkim/dev/spotify_to_youtube"
    target_files = glob.glob(path+"/*.csv")
    for filename in target_files :
        print(filename)
        songs_to_add_df = pd.read_csv(filename, index_col=None, encoding='utf-8')
        songs_to_add_df.to_csv(path+'/songs_to_add.csv')

    # TODO : if there's no file, create a new dataframe 
    try:
        songs_to_add_df
    except:  
        songs_to_add_df = pd.DataFrame(columns=['spotify_playlist','spotifyid','youtube_playlist_id','youtube_video_id','keyword'])

    # TODO : get the items of the playlist 
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    playlist_items = spotify.playlist_items(playlist_id=playlist_id,limit=100, offset=0)
    playlist_name = spotify.playlist(playlist_id=playlist_id)['name']
    
    for _ in range(int(playlist_items["total"]/100)+1):
        playlist_items = spotify.playlist_items(playlist_id=playlist_id,limit=100, offset=_*100)
        
        for item_num in range(len(playlist_items["items"])): 
            search_keyword = playlist_items["items"][item_num]["track"]["artists"][0]["name"] + " " + playlist_items["items"][item_num]["track"]["name"]
            search_id = playlist_items["items"][item_num]["track"]["id"]

            # TODO :  if search_id not in spotifyid col, add the new row (song) to the data frame 
            if not songs_to_add_df['spotifyid'].str.contains(search_id).any() :
                search_dict = {'spotify_playlist': playlist_name, 'spotifyid':[search_id], 'keyword':[search_keyword]}
                songs_to_add_df = pd.concat([songs_to_add_df.reset_index(drop=True),pd.DataFrame(search_dict).reset_index(drop=True)])


    # print(songs_to_add_df[songs_to_add_df['spotifyid']==search_id])
    retrieve_songs_mask = (songs_to_add_df.spotify_playlist == playlist_name) & (songs_to_add_df.youtube_video_id.isna())
    print(retrieve_songs_mask)
    print(f"\nNumber of Songs retrieved from Spotify : {len(songs_to_add_df.loc[retrieve_songs_mask,:])}")
    print(songs_to_add_df.head(1)['spotify_playlist'][0])
    
    return render_template("show_songs.html", songs_to_add = songs_to_add_df.loc[retrieve_songs_mask,:])

@app.route('/runmigration/<spotify_playlist>', methods=['GET', 'POST'])
def runmigration(spotify_playlist):
    return "<h1> look at the console</h1>"
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,cache_handler=cache_handler)
    
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')


    # TODO : Open the csv file
    path="/Users/dougkim/dev/spotify_to_youtube"
    target_files = glob.glob(path+"/*.csv")
    for filename in target_files :
        print(filename)
        songs_to_add_df = pd.read_csv(filename, index_col=None, encoding='utf-8')

    # TODO : if there's no file, create a new dataframe 
    try:
        songs_to_add_df
    except:  
        songs_to_add_df = pd.DataFrame(columns=['spotify_playlist','spotifyid','youtube_playlist_id','youtube_video_id','keyword'])

    # TODO : filter the songs 
    retrieve_songs_mask = (songs_to_add_df.spotify_playlist == spotify_playlist) & (songs_to_add_df.youtube_video_id.isna()) 
    songs_to_retrieve = songs_to_add_df.loc[retrieve_songs_mask,:]
    songs_to_retrieve_total = songs_to_retrieve.shape[0]


    # TODO : get the items of the playlist 
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    youtube = add_to_playlist.get_authenticated_service()
    if songs_to_retrieve.iloc[0].isna()['youtube_playlist_id']:
        target_playlist_id = create_playlist.add_playlist(youtube,title=f"{spotify_playlist}",description="playlist migrated from spotify")    
        songs_to_retrieve.loc[songs_to_retrieve['spotify_playlist']==spotify_playlist,'youtube_playlist_id'] = target_playlist_id
    else:
        # TODO : If the playlist is already created, get the id of the playlist 
        target_playlist_id = songs_to_retrieve[songs_to_retrieve['spotify_playlist']==spotify_playlist].iloc[0]['youtube_playlist_id']

    # TODO  : Add the videos to the playlist 
    added_songs=[]
    
    for row in songs_to_add_df[songs_to_add_df['spotify_playlist']==spotify_playlist].iterrows():
        # TODO : iterate over songs which has not been added to the playlist 
        if pd.isna(row[1]['youtube_video_id']): 
            for attempt in range(6):
                if attempt==5: 
                    # TODO Quit the program if it fails more than 5 times (probably exceeded quota)
                    songs_to_add_df.to_csv(path+'/songs_to_add.csv', mode='w+', index=False)
                    exit()

                time.sleep(0.5)
                try: 
                    video_results = search_video.youtube_search(row[1]['keyword'], 10)
                    target_video_id = video_results[0][-14:].translate(str.maketrans({"(":"",")":""," ":""}))
                    # TODO Add a new video to the playlist 
                    added_results =  add_to_playlist.add_video(youtube=youtube,playlistid=target_playlist_id,videoid=target_video_id)    
                    # TODO Add the id the of the new video to the data frame 
                    songs_to_add_df.loc[songs_to_add_df['spotifyid']==row[1]['spotifyid'],'youtube_video_id'] = target_video_id
                    added_songs.append(row[1]['keyword'])
                    return render_template("migration_results.html", added_songs = added_songs, total = songs_to_retrieve)
                    break
                except Exception as e: 
                    print(f"An error occurred : {e}")
                    time.sleep(3)
                    
    # TODO ADD The added songs to csv file                         
    songs_to_add_df.to_csv(path+'/songs_to_add.csv', mode='w+', index=False)

if __name__ == '__main__':
    app.run(threaded=True, debug=True, port=int(os.environ.get("PORT",
                                                   str(os.environ.get("SPOTIPY_REDIRECT_URI", 8080)).split(":")[-1])))