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
debug_enabled = False
four_oh_four = {
    "id": "F07L6C0FJ",
    "created": 1436928606,
    "timestamp": 1436928606,
    "name": "not-found.jpg",
    "title": "not-found.jpg",
    "mimetype": "image\/jpeg",
    "filetype": "jpg",
    "pretty_type": "JPEG",
    "user": "U07AN38CT",
    "editable": False,
    "size": 54246,
    "mode": "hosted",
    "is_external": False,
    "external_type": "",
    "is_public": True,
    "public_url_shared": False,
    "display_as_bot": False,
    "username": "",
    "url": "https:\/\/slack-files.com\/files-pub\/T07AMCAA2-F07L6C0FJ-d333dc2ee0\/not-found.jpg",
    "url_download": "https:\/\/slack-files.com\/files-pub\/T07AMCAA2-F07L6C0FJ-d333dc2ee0\/download\/not-found.jpg",
    "url_private": "https:\/\/files.slack.com\/files-pri\/T07AMCAA2-F07L6C0FJ\/not-found.jpg",
    "url_private_download": "https:\/\/files.slack.com\/files-pri\/T07AMCAA2-F07L6C0FJ\/download\/not-found.jpg",
    "thumb_64": "https:\/\/slack-files.com\/files-tmb\/T07AMCAA2-F07L6C0FJ-b4935ef172\/not-found_64.jpg",
    "thumb_80": "https:\/\/slack-files.com\/files-tmb\/T07AMCAA2-F07L6C0FJ-b4935ef172\/not-found_80.jpg",
    "thumb_360": "https:\/\/slack-files.com\/files-tmb\/T07AMCAA2-F07L6C0FJ-b4935ef172\/not-found_360.jpg",
    "thumb_360_w": 360,
    "thumb_360_h": 237,
    "thumb_480": "https:\/\/slack-files.com\/files-tmb\/T07AMCAA2-F07L6C0FJ-b4935ef172\/not-found_480.jpg",
    "thumb_480_w": 480,
    "thumb_480_h": 315,
    "thumb_160": "https:\/\/slack-files.com\/files-tmb\/T07AMCAA2-F07L6C0FJ-b4935ef172\/not-found_160.jpg",
    "image_exif_rotation": 1,
    "permalink": "https:\/\/yog-sothoth.slack.com\/files\/uncanny_smile\/F07L6C0FJ\/not-found.jpg",
    "permalink_public": "https:\/\/slack-files.com\/T07AMCAA2-F07L6C0FJ-d333dc2ee0",
    "channels": [
        "C07AMAWBT"
    ],
    "groups": [],
    "ims": [],
    "comments_count": 0,
    "preview": None
}

soundcloud_ids = json.loads(open('ids.json').read())

def translate(str):
    ret = str.replace(':', '%3A').replace('/', '%2F')
    return ret

def dict_to_url_param(d):
    ret = '%5B%7B'
    for key in d.keys():
        ret = ret + '\"' + translate(key) + '\"' #item
        ret = ret + '%3A%20' #colon
        ret = ret + '\"' + translate(d[key]) + '\"' #value
        ret = ret + '%2C%20' #comma
    ret = ret.rstrip('%2C%20') + '%7D%5D'
    return ret

def getFile(query):
    # Turn the query into a list of substrings to be found
    targets = query.split('+')
    # Grab the list of all files
    payload = {
        'token': tok,
        'count': 999
    }
    response = requests.get('https://slack.com/api/files.list', params=payload)
    if debug_enabled:
        print(response.json())
        print(str(response.json().get('paging').get('count')) + " of " + str(response.json().get('paging').get('total')) + " returned")
    files = response.json().get('files')
    # Award points
    high_p = 0
    for file in files:
        p = 0
        for target in targets:
            # Case for awarding a point
            if target in file.get('name'):
                p = p + 1
        # New best match
        print(file.get("name") + " gets " + str(p))
        if p >= high_p:
            high_p = p
            ret = file
        # No matches
        if high_p == 0:
            ret = four_oh_four
    return ret

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
        # No special subtype treatment
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
        if ("!" in text) and ((text.find("!") == 0 or text[text.find("!")-1] == ' ')):
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
                # If the query is ok, send the first result
                if True:
                    file = getFile(search_text)
                    result_url = file.get('url')
                    add_attachments = False
                    # If a audio file
                    if "audio" in file.get('mimetype'):
                        soundcloud_id = ""
                        # Check to see if this file has already been uploaded
                        for key in soundcloud_ids.keys():
                            if key == file.get('name'):
                                soundcloud_id = soundcloud_ids[key]
                        # Not found
                        if soundcloud_id == "":
                            # First, tell the chat that an upload is about to occur
                            payload = {
                                'token': tok,
                                'channel': action.get('channel'),
                                'text': "Uploading " + file.get('name') + " to SoundCloud. Please wait.",
                                'as_user': True
                            }
                            if debug_enabled:
                                print(requests.get('https://slack.com/api/chat.postMessage', params=payload).json())
                            # Upload the file
                            upload = urllib.request.urlopen(file.get('url'))
                            track = sc.post('/tracks', track={
                                'title': file.get('name'),
                                'asset_data': upload
                            })
                            text = track.permalink_url.replace("http", "https")
                            # Wait for upload to complete or fail. This is awful practice, I really need to process requests in separate threads.
                            while(track.state == "processing"):
                                track = sc.get('/tracks/' + str(track.id))
                                print("waiting for soundcloud...")
                                time.sleep(1)
                            # After the upload is complete, add the song's id to the database
                            soundcloud_ids[file.get('name')] = track.id
                        # Found
                        else:
                            text = sc.get('/tracks/' + str(soundcloud_id)).permalink_url.replace("http", "https")
                        # Prep audio payload
                        payload = {
                            'token': tok,
                            'channel': action.get('channel'),
                            'text': text,
                            'unfurl-media': True,
                            'as_user': True
                        }
                    # If image file
                    elif "image" in file.get('mimetype'):
                        add_attachments = True
                        # Prep image payload
                        payload = {
                            'token': tok,
                            'channel': action.get('channel'),
                            'username': name,
                            'icon_emoji': ":shurelia:",
                            'text': ""
                        }
                        if debug_enabled:
                            print(payload)
                    # Nonspecific type
                    else:
                        text = result_url
                        # Prep unspecified payload
                        payload = {
                            'token': tok,
                            'channel': action.get('channel'),
                            'text': text,
                            'unfurl-media': True,
                            'as_user': True
                        }
                    # Send the message
                    url = 'https://slack.com/api/chat.postMessage?'
                    for key in payload.keys():
                        url = url + translate(key) + "=" + translate(str(payload[key])) + "&"
                    if add_attachments:
                        attachment = {
                            'fallback': file.get('name'),
                            'text': file.get('name'),
                            'image_url': file.get('url')
                        }
                        url = url + 'attachments=' + dict_to_url_param(attachment) + "&pretty=1"
                    else:
                        url = url.rstrip('&')
                    if debug_enabled:
                        print(url)
                        print(requests.get(url))
                    else:
                        requests.get(url)

def on_error(ws, error):
    print(error)

def on_close(ws):
    json.dump(soundcloud_ids, open('ids.json', 'w'))
    print("### closed ###")

def on_open(ws):
    def run(*args):
        i = 0
        while(True):
            time.sleep(1)
            ws.send("Hello %d" % i)
            i = i + 1
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
