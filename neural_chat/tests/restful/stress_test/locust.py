from locust import HttpUser, task, between
from neural_chat.tests.restful.config import API_COMPLETION, API_CHAT_COMPLETION, API_ASR, API_TTS, API_FINETUNE, API_TEXT2IMAGE
import time
from neural_chat.server.restful.openai_protocol import CompletionRequest, ChatCompletionRequest
from datasets import Dataset, Audio


# locust will create a FeedbackUser instance for each user
class FeedbackUser(HttpUser):
    # each simulated user will wait 1~2 seconds for the next operation
    wait_time = between(0.5, 2)

    @task
    def test_completions(self):
        time.sleep(0.01)
        request = CompletionRequest(
            model="mpt-7b-chat",
            prompt="This is a test."
        )
        self.client.post(API_COMPLETION, data=request)

    @task
    def test_chat_completions(self):
        time.sleep(0.01)
        request = ChatCompletionRequest(
            model="mpt-7b-chat",
            messages=[
                {"role": "system","content": "You are a helpful assistant."},
                {"role": "user","content": "Hello!"}
            ]
        )
        self.client.post(API_CHAT_COMPLETION, data=request)

    @task
    def test_asr(self):
        audio_path = "../../../assets/audio/pat.wav"
        audio_dataset = Dataset.from_dict({"audio": [audio_path]}).cast_column("audio", Audio(sampling_rate=16000))
        waveform = audio_dataset[0]["audio"]['array']
        self.client.post(API_ASR, data=waveform)

    @task
    def test_tts(self):
        text = "Welcome to Neural Chat"
        self.client.post(API_TTS, data=text)

    @task
    def test_text2image(self):
        text = "A running horse."
        self.client.post(API_TEXT2IMAGE, data=text)

    @task
    def test_finetune(self):
        self.client.post(API_FINETUNE)
        time.sleep(2)