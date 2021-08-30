import os
import shutil
import argparse
import subprocess
import os.path as path
import traceback
from tqdm import tqdm


parser = argparse.ArgumentParser()
parser.add_argument('--description_file', type=str, required=True)
parser.add_argument('--cookie', type=str, required=False)
parser.add_argument('--save_dir', type=str, default='output', required=False)
parser.add_argument('--log', type=str, default='error-log.txt', required=False)

down_cmd_pattern = 'youtube-dl -q -f best --cookies {} {} -o {}'
down_cmd_pattern_v1 = 'youtube-dl -f best {} -o {}'
trim_cmd_pattern = 'ffmpeg -y -hide_banner -loglevel error -ss 00:{} -t {} -i {} -async 1 {}'


class ErrorLogWriter:
    def __init__(self, ars):
        self.args = ars
        self.f = open(self.args.log, 'w')

    def __del__(self):
        if self.f:
            self.f.close()

    def write(self, uri, tick):
        self.f.write('Uncompleted task: {} at {} - {}\n'.format(uri, *tick))


class DownYoutubeVideo:
    def __init__(self, ars):
        self.args = ars
        self.tasks = self._parse_uri_from_txt()
        self.error_writer = ErrorLogWriter(self.args)

    def start_process(self):
        proc_bar = tqdm(total=self._count_task())
        proc_bar.set_description('Completed_task: 0 - Error_task: 0')
        completed_task_count = error_task_count = 0

        for task in self.tasks:
            # step 1. download video from youtube
            temp_path = self._down_video(task['youtube_uri'], cookie=True)
            # step 2. trim video based on ffmpeg
            for tick in task['time_ticks']:
                try:
                    self._trim_video(temp_path, tick[0], tick[1], task['sub_dir'])
                    completed_task_count += 1
                except Exception as e:
                    traceback.print_exc()
                    error_task_count += 1
                    self.error_writer.write(task['youtube_uri'], tick)

                proc_bar.set_description('Completed_task: {} - Error_task: {}'.format(completed_task_count, error_task_count))
                proc_bar.update()

    def _count_task(self):
        task_count = 0
        for t in self.tasks:
            task_count += len(t['time_ticks'])
        return task_count

    def _parse_uri_from_txt(self):
        tasks_to_down = []
        with open(self.args.description_file, 'r') as f:
            all_line = f.readlines()
            sub_dir = None
            for line in all_line:
                if len(line.strip()) == 0:
                    continue
                if 'youtube' not in line:
                    _, sub_dir = line.strip().split()[:2]
                    continue

                line = line.strip().split()
                youtube_uri = line[0]
                down_info = {'youtube_uri': youtube_uri, 'time_ticks': [], 'sub_dir': sub_dir}
                time_ticks = ' '.join(line[1:])
                time_ticks = time_ticks.split(',')
                for tick in time_ticks:
                    if tick.strip() == '':
                        continue
                    start_time, end_time = tick.split('-')
                    start_time, end_time = start_time.strip(), end_time.strip()
                    down_info['time_ticks'].append((start_time, end_time))

                tasks_to_down.append(down_info)

        return tasks_to_down

    def _down_video(self, youtube_uri, cookie=True):
        youtube_id = youtube_uri.split('?v=')[1]
        save_path = path.join('temp', f'{youtube_id}.mp4')
        if cookie:
            cmd = down_cmd_pattern.format(self.args.cookie, youtube_uri, save_path)
        else:
            cmd = down_cmd_pattern_v1.format(youtube_uri, save_path)

        subprocess.call(cmd, shell=True)
        return save_path

    def _trim_video(self, video_path, start_time, end_time, sub_dir):
        save_path = f'{self.args.save_dir}/{sub_dir}/{start_time}-{end_time}.mp4'
        os.makedirs(path.dirname(save_path), exist_ok=True)

        if not path.isfile(video_path):
            raise ValueError("Video path is not a valid path {}".format(video_path))
        duration = self._extract_cutting_duration(start_time, end_time)
        trim_cmd = trim_cmd_pattern.format(start_time, duration, video_path, save_path)

        subprocess.call(trim_cmd, shell=True)
        return True

    @staticmethod
    def _extract_cutting_duration(start_t, end_t):
        start_min, start_sec = list(map(int, start_t.split(':')))
        end_min, end_sec = list(map(int, end_t.split(':')))
        if end_min - start_min < 0:
            return None
        if end_min - start_min == 0:
            return end_sec - start_sec
        else:
            return (60 - start_sec) + (end_min - start_min - 1) * 60 + end_sec


if __name__ == '__main__':
    args = parser.parse_args()
    os.makedirs(args.save_dir, exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    down_video = DownYoutubeVideo(args)
    # start download & trim to clips
    down_video.start_process()
    shutil.rmtree('temp', ignore_errors=True)


