import httplib
import httplib2
import random
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

def get_authenticated_service(args):
    flow = flow_from_clientsecrets("client_secrets.json", 
            scope="https://www.googleapis/com/auth/youtube.upload"
            message="client_secrets.json not found. please follow the guide linked in the readme"
    )
    
    storage = Storage("album-uploader-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build("youtube", "v3", credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, options):
    body = {
        "snippet": {
            "title": options.title,
            "categoryId": "10"
        },
        "status": {
            "privacyStatus": "private"
        }
    }

    insert_request = youtube.videos().insert(
        part=",".join(body.keys())
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    return insert_request

retriable_exceptions = (httplib2.HttpLib2Error, IOError, httplib.NotConnected, httplib.IncompleteRead, httplib.ImproperConnectionState, httplib.CannotSendHeader, httplib.ResponseNotReady, httplib.BadStatusLine)
max_retries = 10
def upload(insert_request):
    response, error, retry = None, None, 0
    while response is None:
        try:
            print("uploading video")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("video with id {} was successfully uploaded".format(response['id']))
                    with open("video_ids.txt", "a") as f:
                        f.write("{}\n".format(response['id']))
                else:
                    exit("upload failed with unexpected response {}".format(response))
        except HttpError, e:
            if e.resp.status in [500, 502, 503, 504]:
                error = "http error {} occured\n{}\nretrying".format(e.resp.status, e.content)
            else:
                raise
        
        except retriable_exceptions, e:
            error = "retriable error occured {}".format(e)

        if error is not None:
            print(error)
            retry += 1
            if retry > max_retries:
                exit("max retries reached, quitting")

            sleep_seconds = random.random() * (2**retry)
            print("sleeping {} seconds and then retrying".format(sleep_seconds))
            time.sleep(sleep_seconds)

argparser.add_argument("-f", "--file", required=True, help="video file to upload")
argparser.add_argument("-t", "--title", help="video title")
argparser.add_argument("-d", "--description", help="video description")
args = argparser.parse_args()

if not os.path.exists(args.file)
    if args.file:
        exit("file {} not found".format(args.file))
    else:
        exit("specify a file with the --file parameter")

flow = flow_from_clientsecrets("client_secrets.json", 
    scope="https://www.googleapis/com/auth/youtube.upload"
    message="client_secrets.json not found. please follow the guide linked in the readme"
)
    
storage = Storage("album-uploader-oauth2.json")
credentials = storage.get()

if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

youtube = build("youtube", "v3", credentials.authorize(httplib2.Http()))

try:
    insert_request = initialize_upload(youtube, args)
    upload(insert_request)

except HttpError, e:
    print("http error {} occured\n{}".format(e.resp.status, e.content))
