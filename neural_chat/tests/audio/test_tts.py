from neural_chat.pipeline.plugins.audio.tts import TextToSpeech
from neural_chat.pipeline.plugins.audio.asr import AudioSpeechRecognition
import unittest
import shutil
import os
import time
import torch

class TestTTS(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.tts = TextToSpeech(device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        self.asr = AudioSpeechRecognition("openai/whisper-small")
        os.mkdir('./tmp_audio')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./tmp_audio', ignore_errors=True)

    def test_tts(self):
        text = "Welcome to Neural Chat"
        output_audio_path = os.path.join(os.getcwd(), "tmp_audio/1.wav")
        output_audio_path = self.tts.text2speech(text, output_audio_path, voice="default")
        self.assertTrue(os.path.exists(output_audio_path))
        # verify accuracy
        result = self.asr.audio2text(output_audio_path)
        self.assertEqual(text.lower(), result.lower())

    def test_streaming_tts(self):
        def text_generate():
            for i in ["Ann", "Bob", "Tim"]:
                time.sleep(1)
                yield f"Welcome {i} to Neural Chat"
        gen = text_generate()
        output_audio_path = os.path.join(os.getcwd(), "tmp_audio/1.wav")
        for result_path in self.tts.stream_text2speech(gen, output_audio_path, voice="default"):
            self.assertTrue(os.path.exists(result_path))

    def test_create_speaker_embedding(self):
        driven_audio_path = "../../assets/audio/pat.wav"
        spk_embed = self.tts.create_speaker_embedding(driven_audio_path)
        self.assertEqual(spk_embed.shape[0], 1)
        self.assertEqual(spk_embed.shape[1], 512)

if __name__ == "__main__":
    unittest.main()
