import requests
import pytube
import sys
import os
import time
import concurrent.futures
from multiprocessing.pool import ThreadPool
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Value, Lock
from moviepy.editor import VideoFileClip
from moviepy.editor import *

api_key = "AIzaSyAINNLc7K5uMUaawDnmnt_UUHHlbJpfhjY"
base_url = "https://www.googleapis.com/youtube/v3/search"


def main():
    # Exception Handling
    if len(sys.argv) != 5:
        print("The Number of Arguments ar not equal to 4")
        exit(1)
    if sys.argv[1] == "":
        print("Singer Name Not Found!")
        exit(1)
    if int(sys.argv[2]) < 10:
        print("No. of Videos should be greater than or Equal to 10")
        exit(1)
    if int(sys.argv[3]) < 20:
        print(
            "Audio Duration or Cut Time of Audio should be greater than or Equal to 20 sec")
        exit(1)
    if sys.argv[4] == "":
        print("Output File Name Not Found!")
        exit(1)

    # Taking the input from terminal
    singer_name = sys.argv[1]
    no_songs = int(sys.argv[2])
    dur = int(sys.argv[3])
    output_file = sys.argv[4]

    extract_videos(no_songs, singer_name, dur, output_file)

# This function extracts the top n corresponding to given Singer


def extract_videos(n, singer_name, dur, output_file):
    params = {
        "part": "snippet",
        "q": singer_name,
        "type": "video",
        "maxResults": 50,    # maximum number of results per API request
        "key": api_key
    }

    # make the API request
    response = requests.get(base_url, params=params)

    # parse the JSON response
    data = response.json()
    # print(data)
    # extract the video URLs from the response

    if data["items"]:
        # extract the video URLs from the response
        video_urls = [
            f"https://www.youtube.com/watch?v={item['id']['videoId']}" for item in data["items"]]
    else:
        # if there are no videos found, print an error message
        print("No videos found for the specified query.")

    # set the download path
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    download_path = os.path.join(desktop, "SingerVideos")

    # create the directory if it does not exist
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # download the first 'n' videos

    def download_videos(video_url, count, n, download_path):
        try:
            yt = pytube.YouTube(video_url)
            video_stream = yt.streams.filter(file_extension='mp4').first()
            video_title = yt.title
            video_title = video_title.replace(
                "|", "").replace("/", "").replace("\"", "_")

        except pytube.exceptions.LiveStreamError as e:
            yt = pytube.YouTube(video_url)
            video_title = yt.title
            print(
                f"Skipping video: {video_title} ,as it is a Live streaming!")
            print(f"Video URL: {video_url}\n")
            return

        video_duration = yt.length
        if video_duration < int(dur) or video_duration > 600 or video_duration < 60:
            print(
                f"Skipping Video: {video_title} ,as it is having Duration Less than Audio Duration input by User or taking high Time to Download!")
            print(f"Video URL: {video_url}\n")
            return

        with Lock():
            if count.value >= n:
                print(
                    "All Required Videos are downloaded, so Stops Downloading Process!")
                return
            count.value = count.value+1

        if (video_stream):
            video_stream.download(download_path, video_title+".mp4")
            print(f"Downloaded Video {count.value} of {n}: {video_title}")
            print(f"Video Duration: {video_duration} sec\n")

        else:
            print(
                f"Skipping Video: {video_title} ,as it does not Support .mp4 format!")
            print(f"Video URL: {video_url}")
            print(f"Video Duration: {video_duration} sec\n")

        return

    count = Value('i', 0)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for video_url in video_urls:
            futures = executor.submit(download_videos(
                video_url, count, n, download_path))
            if count.value == n:
                break

    # Converting 'n' videos to audio
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    audio_path = os.path.join(desktop, "VideoToAudio")

    # create the directory if it does not exist
    if not os.path.exists(audio_path):
        os.makedirs(audio_path)

    # specify the path to the folder containing the video files
    # download_path is a Path where Videos are downloaded in .mp4 format

    # loop through each file in the folder
    for filename in os.listdir(download_path):
        # check if the file is a video file
        if filename.endswith(".mp4"):
            # construct the full path to the video file
            video_file = os.path.join(download_path, filename)

            # load the video file
            video = VideoFileClip(video_file)

            # convert the video to audio
            audio = video.audio

            # construct the full path to the audio file
            audio_file = os.path.join(
                audio_path, os.path.splitext(filename)[0] + ".mp3")

            # save the audio file with the MP3 codec
            audio.write_audiofile(audio_file, codec="mp3")

    # Now cut the Audio Files in no. of seconds as input by user and merge in output file

    # Forming output file as input by user on Desktop
    output_file = os.path.join(os.path.expanduser('~/Desktop'), output_file)

    # Get a list of all audio files in the input folder
    files = [f for f in os.listdir(audio_path) if f.endswith('.mp3')]

    # Cut the first 'cut_time' seconds from each file and store the clips in a list
    clips = []
    for file in files:
        clip = AudioFileClip(os.path.join(audio_path, file))
        clip = clip.subclip(0, dur)
        clips.append(clip)

    # Concatenate the clips into a single audio file
    concatenated_clip = concatenate_audioclips(clips)

    # Write the output file
    concatenated_clip.write_audiofile(output_file, codec='mp3')


if __name__ == "__main__":
    startTime = time.time()
    main()
    print(f"Total Time Taken: {time.time() -startTime}")