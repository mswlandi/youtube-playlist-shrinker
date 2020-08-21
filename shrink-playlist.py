from pytube import Playlist, YouTube
import re
import os
import sys, getopt

try:
    opts, args = getopt.getopt(sys.argv[2:],"hv:s:m:",["sounded_speed=", "silent_speed=", "margin="])
    s = '10'
    v = '1.25'
    m = '2'
except getopt.GetoptError:
    print('shrink-playlist.py <inputfile> -o <outputfile> -v <sounded speed> -s <silent speed> -m <margin>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('shrink-playlist.py <inputfile> -o <outputfile> -v <sounded speed> -s <silent speed> -m <margin>')
        sys.exit()
    elif opt in ("-v", "--sounded_speed"):
        v = arg
    elif opt in ("-s", "--silent_speed"):
        s = arg
    elif opt in ("-m", "--margin"):
        m = arg

playlist = Playlist(sys.argv[1])
titles = []

arguments = f'-v {v} -s {s} -m {m}'

# YouTube updated their HTML so the regex that Playlist uses to find the videos is currently outdated
playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")

print(f'downloading {len(playlist.video_urls)} videos from {playlist.title()}:\n')
for url in playlist.video_urls:
    print(url)
    video = YouTube(url)
    titles.append(video.title)
    video.streams.get_highest_resolution().download(playlist.title())

for title in titles:
    print(f"\nshrinking {title}")
    os.system(f'auto-editor "{playlist.title()}/{title}.mp4" {arguments} --no_open -o "{playlist.title()}/{title}_t.mp4"')
    os.remove(f'{playlist.title()}/{title}.mp4')
    os.rename(f'{playlist.title()}/{title}_t.mp4', f'{playlist.title()}/{title}.mp4')