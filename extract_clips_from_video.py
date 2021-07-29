import os
import subprocess
import sys
from tqdm import tqdm


def process_tick_pair(start, end, clip_duration=5):
    min_start, sec_start = int(start.split(".")[0]), int(start.split(".")[1])
    min_end, sec_end = int(end.split(".")[0]), int(end.split(".")[1])
    min_delta = min_end - min_start
    second_count = 0
    if min_delta >= 1:
        second_count = (min_delta - 1) * 60 + (60-sec_start) + sec_end
    elif min_delta == 0:
        second_count = sec_end - sec_start

    ranges = []
    mark_nums = int(second_count // clip_duration)
    mark_start_sec = sec_start
    mark_start_min = min_start
    for i in range(mark_nums):
        if i == mark_nums-1:
            temp_secs = clip_duration + int(second_count % clip_duration)
        else:
            temp_secs = clip_duration
        min_offset = int(temp_secs // 60) + int((temp_secs % 60 + mark_start_sec) // 60)
        mark_end_sec = int((temp_secs % 60 + mark_start_sec) % 60)
        ranges.append(("00:{}:{}".format(mark_start_min, mark_start_sec), temp_secs))
        # update time tick for next iteration
        mark_start_sec = mark_end_sec
        mark_start_min = mark_start_min + min_offset
    return ranges


if __name__ == "__main__":
    input_dir = "/home/manvd1/Research/LipSync/data/quality/1080/easy"
    output_dir = "/home/manvd1/Research/LipSync/data/quality/1080/clips"
    statistic_file = "/home/manvd1/Research/LipSync/data/video-statictis.txt"
    command_pattern = "ffmpeg -i \"{input}\" -ss {start_time} -t 00:00:{duration} -filter:v fps=fps=25 -ar 16000 -async 1 \"{video_path}\""

    video_marks = None
    with open(statistic_file, "r") as f:
        video_marks = f.readlines()

    for item in tqdm(video_marks):
        video_name = item.split(",")[0]
        time_ticks = item.split(",")[1:]
        video_path = os.path.join(input_dir, video_name)
        if not os.path.isfile(video_path):
            print("File at {} is not exist.".format(video_path))
            continue
        # extract clips from video
        time_ranges = []
        for i in range(int(len(time_ticks)//2)):
            start_tick, end_tick = time_ticks[i*2], time_ticks[i*2+1]
            time_ranges.extend(process_tick_pair(start_tick, end_tick))

        sub_dir = os.path.join(output_dir, video_name.replace(".mp4", ""), "0001")
        os.makedirs(sub_dir, exist_ok=True)
        for i, (start_time, duration) in enumerate(time_ranges):
            output_video_path = os.path.join(sub_dir, start_time + ".mp4")
            command = command_pattern.format(
                input=video_path,
                start_time=start_time,
                duration=duration,
                video_path=output_video_path)
            print(command)
            subprocess.call(command, shell=True)
        break
