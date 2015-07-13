#!/usr/bin/python

import json
import requests
import websocket
import time
import string

tok = 'xoxp-7361418342-7569957862-7569672320-32d137'
send_url = 'https://hooks.slack.com/services/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'
payload = {'token': tok}

def on_message(ws, message):
    global tok
    action = json.loads(message)
    # Action is relevant
    if action.get('type') == 'message' and (action.get('subtype') != "bot_message"):
        # Print chat in terminal, pretty much for debug only
        payload = {'token': tok, "user": action.get('user')}
        response = requests.get('https://slack.com/api/users.info', params=payload)
        if(response.json().get('ok')):
            name = response.json().get('user').get('name')
        else:
            name = "EDIT"
        print(str(name) + ": " + str(action.get('text')))
        print(action)
        # Image code found
        if action.get('text').count("!") > 0:
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
            # Find the right image's url
            payload = {
                'token': tok,
                'query': search_text,
                'count': 1
            }
            image_search = requests.get('https://slack.com/api/search.files', params=payload)
            print(image_search.json())
            image_url = image_search.json().get('files').get('matches')[0].get('url_private')
            # Send the message
            payload = {
                'token': tok,
                'channel': action.get('channel'),
                'text': image_url,
                'username': name,
                'as_user': True,
                'unfurl_media': True,
                'icon_emoji': ":shurelia:"
            }
            print(requests.get('https://slack.com/api/chat.postMessage', params=payload).json())

def on_error(ws, error):
    print(error)

def on_close(ws):
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

response = requests.get('https://slack.com/api/rtm.start', params=payload)
ws = websocket.WebSocketApp(response.json().get('url'),
                            on_message = on_message,
                            on_error = on_error,
                            on_close = on_close)
ws.on_open = on_open
ws.run_forever()
