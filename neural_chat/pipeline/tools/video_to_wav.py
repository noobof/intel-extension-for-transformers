#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import argparse

from pydub import AudioSegment

def convert_video_to_wav(path, output_sample_rate, is_mono=True):
    is_dir = os.path.isdir(path)
    if is_dir: 
        path_list=os.listdir(path)
    else: # input is a file
        path, basename = os.path.split(path)
        path_list = [basename]
    print(path)

    output_dir = os.path.join(path, "../raw")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    for filename in path_list:
        if os.path.isdir(os.path.join(path, filename)):
            continue
        filename_suffix = os.path.splitext(filename)[1]
        print(filename)
        input_file_path = os.path.join(path, filename)
        output_file_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".wav")
        if filename_suffix == '.flv':
            sound = AudioSegment.from_flv(input_file_path)
            sound = sound.set_frame_rate(output_sample_rate)
            if is_mono:
                sound = sound.set_channels(1)
            sound.export(os.path.join(output_file_path), format="wav")
        elif filename_suffix == '.mp4' or filename_suffix == '.mp3':
            # file name should not contain space.
            if is_mono:
                cmd = "ffmpeg -i {} -ac 1 -ar {} -f wav {}".format(input_file_path, output_sample_rate, output_file_path)
            else:
                cmd = "ffmpeg -i {} -ac 2 -ar {} -f wav {}".format(input_file_path, output_sample_rate, output_file_path)
            os.system(cmd)
        else:
            print("file ", filename, " format not supported!")
            continue
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--is_mono", type=str, default=True)
    parser.add_argument("--sr", type=int, default=16000)
    args = parser.parse_args()
    output_sample_rate = args.sr
    is_exist = os.path.exists(args.path)
    if not is_exist:
        print("path not existed!")
    else:
        path = args.path
        is_mono = args.is_mono
        convert_video_to_wav(path, output_sample_rate, is_mono)
