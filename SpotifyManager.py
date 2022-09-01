import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pprint


class spotifyManager:
    def __init__(self, SPOTIFY_CLIENT_ID: str, SPOTIFY_CLIENT_TOKEN: str, SPOTIFY_REDIRECT_URI: str):
        self.SPOTIFY_CLIENT_ID = SPOTIFY_CLIENT_ID
        self.SPOTIFY_CLIENT_TOKEN = SPOTIFY_CLIENT_TOKEN
        self.SPOTIFY_REDIRECT_URI = SPOTIFY_REDIRECT_URI
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-modify-public",
                                                            client_id=self.SPOTIFY_CLIENT_ID, \
                                                            client_secret=self.SPOTIFY_CLIENT_TOKEN,
                                                            redirect_uri=self.SPOTIFY_REDIRECT_URI))

    def search(self, track: str, artist: str) -> str:
        """search a track based with artist name and track name. return track ID"""
        try:
            search_result = self.sp.search(type="track", q=f"artist:{artist} track:{track}")
            track_name = search_result["tracks"]["items"][0]["name"]
            artist_name = search_result["tracks"]["items"][0]["album"]["artists"][0]["name"]
            track_id = search_result["tracks"]["items"][0]["id"]

            return track_id
        except IndexError:
            pass


    def create_playlist(self, user_id: str, playlist_name: str) -> str:
        """create a playlist and returns its playlist ID"""
        playlist_create_result = self.sp.user_playlist_create(user=user_id,
                                                              name=playlist_name,
                                                              public=True,
                                                              collaborative=False,
                                                              description='')
        created_playlist_id = playlist_create_result["id"]
        return created_playlist_id

    def add_items_to_playlist(self, playlist_id: str, track_id: list[str]) -> str:
        """Add a song to a playlist. Returns the api response"""
        playlist_result = self.sp.playlist_add_items(playlist_id, track_id, position=None)
        return playlist_result
    
    def search_playlist(self, user_id:str)-> str: 
        user_playlist_result = self.sp.current_user_playlists(limit=50)["items"]
        print(user_playlist_result)


        result_playlist = []
        for playlist in user_playlist_result:
            playlist_element = {}
            playlist_element["id"] = (playlist["id"])
            playlist_element["name"] = playlist["name"]
            result_playlist.append(playlist_element)

        return result_playlist


    def get_playlist_items(self, playlist_id: str, limit:int, offset:int) -> list[str]:
        retrieved_playlist = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)

        return retrieved_playlist



