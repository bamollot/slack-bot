#!/usr/bin/python

import subprocess
import json
import requests
import websocket
import soundcloud
import time
import string
import urllib.request

tok = 'xoxp-7361418342-7569957862-7569672320-32d137'
payload = {'token': tok}
debug_enabled = True

soundcloud_ids = json.loads(open('ids.json').read())

def on_message(ws, message):
    global tok
    global sc
    global debug_enabled
    action = json.loads(message)
    if debug_enabled:
        print(action)
    # Action is relevant
    if action.get('type') == 'message' and (action.get('subtype') != "bot_message") and (action.get('subtype') != "message_deleted") and (action.get('subtype') != "file_comment") and (action.get('subtype') != "pinned_item") and (action.get('subtype') != "unpinned_item"):
        # Edit event
        if action.get('subtype') == "message_changed":
            text = action.get('message').get('text')
            payload = {'token': tok, "user": action.get('message').get('user')}
        # No spectial subtype treatment
        else:
            text = action.get('text')
            payload = {'token': tok, "user": action.get('user')}
        response = requests.get('https://slack.com/api/users.info', params=payload)
        name = response.json().get('user').get('name')
        # /me message
        if action.get('subtype') == "me_message":
            print(str(name) + " " + text)
        # Normal message
        else:
            print(str(name) + ": " + text)
        # File code found
        if text.count("!") > 0:
            # Find out what to search for
            target_substring = False
            search_text = ""
            for char in action.get('text'):
                if char == '!':
                    target_substring = True
                elif char == ' ':
                    target_substring = False
                elif target_substring:
                    search_text = search_text + char
            # Only proceed if there is a query
            if search_text != "":
                # Find the right image's url
                payload = {
                    'token': tok,
                    'query': search_text,
                    'count': 1
                    }
                search_results = requests.get('https://slack.com/api/search.files', params=payload)
                if debug_enabled:
                    print(search_results.json())
                # If the query is ok, send the first result
                if search_results.json().get('ok') and len(search_results.json().get('files').get('matches')) > 0:
                    result_url = search_results.json().get('files').get('matches')[0].get('url')
                    # If a sound file
                    if search_results.json().get('files').get('matches')[0].get('mimetype').count("audio") > 0:
                        soundcloud_id = ""
                        # Check to see if this file has already been uploaded
                        for key in soundcloud_ids.keys():
                            if key == search_results.json().get('files').get('matches')[0].get('name'):
                                soundcloud_id = soundcloud_ids[key]
                        # Not found
                        if soundcloud_id == "":
                            # First, tell the chat that an upload is about to occur
                            payload = {
                                'token': tok,
                                'channel': action.get('channel'),
                                'text': "Uploading " + search_results.json().get('files').get('matches')[0].get('name') + " to SoundCloud. Please wait.",
                                'as_user': True
                            }
                            print(requests.get('https://slack.com/api/chat.postMessage', params=payload).json())
                            # Upload the file
                            upload = urllib.request.urlopen(search_results.json().get('files').get('matches')[0].get('url_download'))
                            track = sc.post('/tracks', track={
                                'title': search_results.json().get('files').get('matches')[0].get('name'),
                                'asset_data': upload
                            })
                            text = track.permalink_url.replace("http", "https")
                            # Wait for upload to complete or fail. This is awful practice, I really need to process requests in separate threads.
                            while(track.state == "processing"):
                                track = sc.get('/tracks/' + str(track.id))
                                print("waiting for soundcloud...")
                                time.sleep(1)
                            # After the upload is complete, add the song's id to the database
                            soundcloud_ids[search_results.json().get('files').get('matches')[0].get('name')] = track.id
                        # Found
                        else:
                            text = sc.get('/tracks/' + str(soundcloud_id)).permalink_url.replace("http", "https")

                    # Nonspecific type
                    else:
                        text = result_url
                    # Send the message
                    payload = {
                        'token': tok,
                        'channel': action.get('channel'),
                        'text': text,
                        'unfurl-media': True,
                        'as_user': True
                    }
                    print(requests.get('https://slack.com/api/chat.postMessage', params=payload).json())

def on_error(ws, error):
    print(error)

def on_close(ws):
    json.dump(soundcloud_ids, open('ids.json', 'w'))
    print("### closed ###")

def on_open(ws):
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()

# Main
websocket.enableTrace(True)

# Log into soundcloud
sc = soundcloud.Client(client_id='b742b9fa99b45ace585cb7be1cb30b2b', client_secret='223e2d5710b54e4a7b63bc8fa6789680', username='3mollot@gmail.com', password='haveam27')

response = requests.get('https://slack.com/api/rtm.start', params=payload)
ws = websocket.WebSocketApp(response.json().get('url'),
                            on_message = on_message,
                            on_error = on_error,
                            on_close = on_close)
ws.on_open = on_open
ws.run_forever()
