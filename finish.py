import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import mutagen
import pathlib
import random
import time

artists = []
album_artists = []
album_titles = []
album_artist = ""
album_title = ""
songs = []
with open("songs.txt", "r") as f:
    songs = f.read().split("\n")

for song in songs:
    mutagen_file = mutagen.File(song)
    artists.append(get_tag(mutagen_file, "TPE1"))
    album_artists.append(get_tag(mutagen_file, "TPE2"))
    album_titles.append(get_tag(mutagen_file, "TALB"))

# logic that determines album title / artist
if is_homogenous(album_artists + artists):
    album_artist = album_artists[0]
elif is_homogenous(album_artists) and album_artists[0] != "[unknown artist]":
    album_artist = album_artists[0]
elif is_homogenous(artists) and artists[0] != "[unknown artist]":
    album_artist = artists[0]

album_artists = [i for i in album_artists if i != "[unknown artist]"]
artists = [i for i in artists if i != "[unknown artist]"]

most_common_artists = most_common(album_artists + artists)
if len(most_common_artists) == 1:
    album_artist = most_common_artists[0]
elif len(most_common_artists) == 2:
    album_artist = "{} / {}".format(*most_common_artists)
else:
    most_common_artists = most_common(album_artists)
    if len(most_common_artists) == 1:
        album_artist = most_common_artists[0]
    elif len(most_common_artists) == 2:
        album_artist = "{} / {}".format(*most_common_artists)
    else:
        album_artist = "Various Artists"

if is_homogenous(album_titles):
    album_title = album_titles[0]
else:
    album_title = "[untitled]"

check = input("the artist that the program has detected for the album is {}. type the artist's actual name if this is correct. otherwise, leave the input field empty and hit enter".format(album_artist))
if check != "":
    _check = input("are you sure? [y/N] ")
    if _check == "y":
        album_artist = check

check = input("the title that the program has detected for the album is {}. type the album's actual title if this is correct. otherwise, leave the input field empty and hit enter".format(album_artist))
if check != "":
    _check = input("are you sure? [y/N] ")
    if _check == "y":
        album_title = check

playlist_title = "{} - {}".format(album_artist, album_title)

# set up api
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, 
    [
        "https://www.googleapis.com/auth/youtube.force-ssl", 
        "https://www.googleapis.com/auth/youtube.upload"
    ]
)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
    "youtube", "v3", credentials=credentials
)

# upload videos
video_ids = []
converted_videos_path = pathlib.Path("./.out")
uploads = 0

for path in converted_videos_path.iterdir():
    title = input("file '{}' queued for upload. enter a title [if the field is empty when submitted, it will be '{}']\n".format(path.name, path.stem))
    if title == "":
        title = path.stem

    request = youtube.videos().insert(
        part="snippet,status",
        notifySubscribers=uploads==0,
        body={
            "snippet": {
                "categoryId": "10",
                "title": title
            },
            "status": {
                "privacyStatus": "public"
            }
        }
    )
    response = request.execute()
    print(response)
    uploads += 1
    video_ids.append(response["id"])
    time.sleep(random.random() * 3)

# create playlist
request = youtube.playlists().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": playlist_title,
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "public"
        }
    },
)
response = request.execute()
playlist_id = response["id"]
print(response)
time.sleep(random.random())

# add videos to playlist
for index, video_id in enumerate(video_ids):
    request = youtube.playlistItems().insert(
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": index,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    response = request.execute()
    print(response)
    time.sleep(random.random() * 3)
