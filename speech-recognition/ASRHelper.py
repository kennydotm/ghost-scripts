#made by frederic seraphine 30/3/2023
#modified generator to function by kenta 30/3/2023

import io
import speech_recognition as sr
import whisper
import torch
import shutil

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform
from langdetect import detect, LangDetectException


def transcribe_asr(model="medium", non_english=False, energy_threshold=1000,
                   record_timeout=2, phrase_timeout=3, default_microphone='pulse'):
    phrase_time = None
    last_sample = bytes()
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = energy_threshold
    recorder.dynamic_energy_threshold = False

    if 'linux' in platform:
        mic_name = default_microphone
        if mic_name == 'list':
            raise ValueError("Please provide a valid microphone name.")
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)

    print("loading Model")
    model = model if non_english else model + ".en"
    audio_model = whisper.load_model(model)
    print("Model Loaded!")

    temp_file = NamedTemporaryFile().name
    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData):
        data = audio.get_raw_data()
        data_queue.put(data)

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    try:
        while True:
            now = datetime.utcnow()
            if not data_queue.empty():
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                if phrase_complete:
                    transcription.append(text)
                    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"data/answer_{now}.wav"
                    shutil.copy(temp_file, filename)
                    try:
                        language = detect(text)
                    except LangDetectException:
                        language = 'unknown'
                    yield text, language, filename, now

                sleep(0.25)
    except KeyboardInterrupt:
        pass

    print("\n\nTranscription:")
    for line in transcription:
        print(line)
