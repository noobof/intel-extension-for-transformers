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

import sys, os
import argparse
from typing import List
from ..utils.command import NeuralChatCommandDict
from .base_executor import BaseCommandExecutor
from neural_chat.config import PipelineConfig, FinetuningConfig, GenerationConfig
from neural_chat.chatbot import build_chatbot, finetune_model
from neural_chat.pipeline.plugins.audio.asr import AudioSpeechRecognition
from neural_chat.pipeline.plugins.audio.asr_chinese import ChineseAudioSpeechRecognition
from neural_chat.pipeline.plugins.audio.tts import TextToSpeech
from neural_chat.pipeline.plugins.audio.tts_chinese_tts import ChineseTextToSpeech

__all__ = ['BaseCommand', 'HelpCommand', 'TextChatExecutor', 'VoiceChatExecutor', 'FinetuingExecutor']

neuralchat_commands = NeuralChatCommandDict()

def get_command(name: str):
    items = name.split('.')
    com = neuralchat_commands
    for item in items:
        com = com[item]

    return com['_command']

def cli_register(name: str, description: str=''):
    def _warpper(command):
        items = name.split('.')

        com = neuralchat_commands
        for item in items:
            com = com[item]
        com['_command'] = command
        if description:
            com['description'] = description
        return command

    return _warpper

def command_register(name: str, description: str='', cls: str=''):
    items = name.split('.')
    com = neuralchat_commands
    for item in items:
        com = com[item]
    com['_command'] = cls
    if description:
        com['description'] = description

def neuralchat_execute():
    com = neuralchat_commands

    idx = 0
    for _argv in (['neuralchat'] + sys.argv[1:]):
        if _argv not in com:
            break
        idx += 1
        com = com[_argv]

    if not callable(com['_command']):
        i = com['_command'].rindex('.')
        module, cls = com['_command'][:i], com['_command'][i + 1:]
        exec("from {} import {}".format(module, cls))
        com['_command'] = locals()[cls]
    status = 0 if com['_command']().execute(sys.argv[idx:]) else 1
    return status

@cli_register(name='neuralchat')
class BaseCommand:
    """
    BaseCommand class serving as a foundation for other neuralchat commands.

    This class provides a common structure for neuralchat commands. It includes a
    default implementation of the execute method, which acts as a fallback and
    invokes the 'neuralchat.help' command to provide assistance to users when
    no specific command is provided.

    Attributes:
        None

    Methods:
        execute(argv): Executes the fallback 'neuralchat.help' command and
                       returns its execution result.

    Usage example:
        base_command = BaseCommand()
        base_command.execute([])
    """
    def execute(self, argv: List[str]) -> bool:
        help = get_command('neuralchat.help')
        return help().execute(argv)


@cli_register(name='neuralchat.help', description='Show help for neuralchat commands.')
class HelpCommand:
    """
    HelpCommand class for displaying help about available neuralchat commands.

    This class provides the functionality to display a list of available neuralchat
    commands and their descriptions. It helps users understand how to use different
    commands provided by the neuralchat package.

    Attributes:
        None

    Methods:
        execute(argv): Executes the help display and returns a success status.
    """
    def execute(self, argv: List[str]) -> bool:
        msg = 'Usage:\n'
        msg += '    neuralchat <command> <options>\n\n'
        msg += 'Commands:\n'
        for command, detail in neuralchat_commands['neuralchat'].items():
            if command.startswith('_'):
                continue

            if 'description' not in detail:
                continue
            msg += '    {:<15}        {}\n'.format(command,
                                                   detail['description'])

        print(msg)
        return True


@cli_register(name='neuralchat.version', description='Show version of current neuralchat package.')
class VersionCommand:
    """
    VersionCommand class for displaying the package version.

    This class provides the functionality to display the version of the neuralchat
    package either through the command-line interface or programmatically. It utilizes
    the __version__ attribute to determine the package version.

    Attributes:
        None

    Methods:
        execute(argv): Executes the version display and returns a success status.
    """
    def execute(self, argv: List[str]) -> bool:
        try:
            from ..version import __version__
            version = __version__
        except ImportError:
            version = 'Not an official release'

        msg = 'Package Version:\n'
        msg += '    {}\n\n'.format(version)

        print(msg)
        return True




class TextChatExecutor(BaseCommandExecutor):
    """
    TextChatExecutor class for executing text-based conversations with a chatbot.

    This class extends the BaseCommandExecutor class and provides functionality for
    interacting with a chatbot through the command line or the Python API. It initializes
    the necessary components, including the argument parser and the chatbot instance.

    Attributes:
        parser (argparse.ArgumentParser): An argument parser for command-line input.
        config (PipelineConfig): Configuration instance for the chatbot.

    Methods:
        execute(argv): Execute the chatbot using command-line arguments.
        __call__(prompt): Python API for calling the chatbot executor.

    """
    def __init__(self):
        """
        Initializes the TextChatExecutor class.

        This constructor sets up the necessary components for the chatbot executor.
        It creates a command-line argument parser, initializes the configuration,
        initializes the chatbot instance, and builds the chatbot model.
        """
        super().__init__()
        self.parser = argparse.ArgumentParser(
            prog='neuralchat.textchat', add_help=True)
        self.parser.add_argument(
            '--query', type=str, default=None, help='Prompt text.')
        self.parser.add_argument(
            '--model_name_or_path', type=str, default=None, help='Model name or path.')

    def execute(self, argv: List[str]) -> bool:
        """
        Command line entry point.
        """
        parser_args = self.parser.parse_args(argv)

        prompt = parser_args.query
        model_name = parser_args.model_name_or_path
        if model_name:
            self.config = PipelineConfig(model_name_or_path=model_name)
        else:
            self.config = PipelineConfig()
        self.chatbot = build_chatbot(self.config)
        try:
            res = self(prompt)
            print(res)
            return True
        except Exception as e:
            print("TextChatExecutor Exception: ", e)
            return False

    def __call__(
            self,
            prompt: str):
        """
            Python API to call an executor.
        """
        result = self.chatbot.chat(prompt)
        return result

class VoiceChatExecutor(BaseCommandExecutor):
    def __init__(self):
        super().__init__()
        self.parser = argparse.ArgumentParser(
            prog='neuralchat.voicechat', add_help=True)
        self.parser.add_argument(
            '--audio_input_path', type=str, default=None, help='Input aduio path.')
        self.parser.add_argument(
            '--audio_output_path', type=str, default=None, help='Output aduio path.')
        self.parser.add_argument(
            '--query', type=str, default=None, help='Input text.')
        self.parser.add_argument(
            '--model_name_or_path', type=str, default=None, help='Model name or path.')

    def execute(self, argv: List[str]) -> bool:
        """
            Command line entry.
        """
        parser_args = self.parser.parse_args(argv)

        audio_input_path = parser_args.audio_input_path
        audio_output_path = parser_args.audio_output_path
        query = parser_args.query
        model_name = parser_args.model_name_or_path
        if model_name:
            config = PipelineConfig(audio_input=True if audio_input_path else False,
                                    audio_output=True if audio_output_path else False,
                                    model_name_or_path=model_name)
        else:
            config = PipelineConfig(audio_input=True if audio_input_path else False,
                                    audio_output=True if audio_output_path else False)
        self.chatbot = build_chatbot(config)
        try:
            if audio_input_path:
                res = self(audio_input_path, audio_output_path)
            else:
                res = self(query, audio_output_path)
            print(res)
            return True
        except Exception as e:
            print("VoiceChatExecutor Exception: ", e)
            return False

    def __call__(self,
                 input: str,
                 output: str):
        """
            Python API to call an executor.
        """
        config = GenerationConfig(audio_output_path=output, max_new_tokens=64)
        result = self.chatbot.chat(input, config=config)
        return result

class FinetuingExecutor(BaseCommandExecutor):
    def __init__(self):
        super().__init__()
        self.parser = argparse.ArgumentParser(
            prog='neuralchat.finetune', add_help=True)
        self.parser.add_argument(
            '--base_model', type=str, default=None, help='Base model path or name for finetuning.')
        self.parser.add_argument(
            '--config', type=str, default=None, help='Configuration file path for finetuning.')

    def execute(self, argv: List[str]) -> bool:
        """
            Command line entry.
        """
        parser_args = self.parser.parse_args(argv)
        base_model = parser_args.base_model
        config = parser_args.config

        self.finetuneCfg = FinetuningConfig()
        try:
            res = self()
            print(res)
            return True
        except Exception as e:
            print("FinetuingExecutor Exception: ", e)
            return False

    def __call__(self):
        """
            Python API to call an executor.
        """
        finetuned_model = finetune_model(self.finetuneCfg)
        return finetuned_model

specific_commands = {
    'textchat': ['neuralchat text chat command', 'TextChatExecutor'],
    'voicechat': ['neuralchat voice chat command', 'VoiceChatExecutor'],
    'finetune': ['neuralchat finetuning command', 'FinetuingExecutor'],
}

for com, info in specific_commands.items():
    command_register(
        name='neuralchat.{}'.format(com),
        description=info[0],
        cls='neural_chat.cli.cli_commands.{}'.format(info[1]))
