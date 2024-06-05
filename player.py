from flask import Flask, jsonify, request
from flask_cors import CORS
from multiprocessing import Process, Manager, Value
import time
import requests
import json

app = Flask(__name__)
CORS(app)

@app.route("/current_time")
def get_current_time():
  if not current_player_time.value == 0:
    current_time = current_player_time.value
  else:
    current_time = 0
  return str(current_time)

@app.route("/get_timestamped_url")
def get_timestampted_url():
  url = 'https://youtube.com/watch?v=' + get_current_song()[0] + '?t=' + get_current_time()
  print(url)
  return jsonify({'url': url})

# TODO: improve timing to use static end time and delta
def player(player_time_queue, current_player_time):
  while True:
    song, song_duration_seconds = get_current_song()
    time.sleep(1)
    print(song)
    print(song_duration_seconds)
    target_time = int(song_duration_seconds)
    current_time = 0
    while current_time < target_time:
      time.sleep(1)
      current_time += 1
      current_player_time.value = current_time
    current_time = 0
    mark_song_played(song)

# returns tuple of the id and duration in seconds
def get_current_song():
  print("getting current song")
  request_url = "http://127.0.0.1:5002/current_song"
  response = requests.get(request_url)
  song = response.text
  if (song == "None"):
    # playlist has played through, reset
    request_url = "http://127.0.0.1:5002/reset_playlist"
    response = requests.get(request_url)

    # get first song
    request_url = "http://127.0.0.1:5002/current_song"
    response = requests.get(request_url)
    song = response.text
    
  request_url = "http://127.0.0.1:5003/song_info/" + song
  response = requests.get(request_url)
  song_dict = json.loads(response.text)
  song_duration_seconds = int(song_dict['duration_seconds'])
  return song, song_duration_seconds

def mark_song_played(song):
  print('Marking song {} played'.format(song))
  request_url = "http://127.0.0.1:5002/mark_song_played/" + song
  response = requests.get(request_url)
  song = response.text
  return song

if __name__ == '__main__':
  manager = Manager()
  player_time_queue = manager.Queue()
  current_player_time = manager.Value('i', 0)
  p = Process(target=player, name="playlist_player", args=(player_time_queue, current_player_time))
  p.start()
  app.run(debug=False, port=5001)