#!/usr/bin/python

# This code sample creates a private playlist in the authorizing user's
# YouTube channel.
# Usage:
#   python playlist_updates.py --title=<TITLE> --description=<DESCRIPTION>

import argparse
import os

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    
CLIENT_SECRETS_FILE = '/Users/dougkim/dev/oneshot/client_secret.json'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
    
# Authorize the request and store authorization credentials.
def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  flow.run_local_server(port=9090,prompt='consent')
  credentials = flow.credentials
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)
    
def add_video(youtube, playlistid, videoid):
  
  body = dict(
    snippet=dict(
      playlistId=playlistid,
      resourceId={
        "kind":"youtube#video",
        "videoId": videoid
      }
    )
  ) 
    
  playlists_insert_response = youtube.playlistItems().insert(
    part='snippet',
    body=body
  ).execute()

  print(f"Successfully Added:{playlists_insert_response}")
  
if __name__ == '__main__':
           
  parser = argparse.ArgumentParser()
  parser.add_argument('--title',
      default='Test Playlist',
      help='The title of the new playlist.')
  parser.add_argument('--description',
      default='A private playlist created with the YouTube Data API.',
      help='The description of the new playlist.')
    
  args = parser.parse_args()
    
  youtube = get_authenticated_service()
  try:
    add_video(youtube, args)
  except Exception as e:
    print(f"An HTTP error %d occurred:\n{(e.resp.status, e.content)}") 