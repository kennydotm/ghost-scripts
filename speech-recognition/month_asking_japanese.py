#!/usr/bin/env python
# coding: utf-8


import speech_recognition as sr
from datetime import datetime
import wave
import pydub
import numpy as np
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder


IP = 'localhost'
PORT = 6140

#月の名前のリストを作る
months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
month = 0
text = ""

mic = sr.Microphone(device_index=0)

# 音声認識のオブジェクトを作成する
r = sr.Recognizer()

while True:
    # マイクから音声を受け取る
    with mic as source:
        print("何月が一番好きですか？")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    print(">>>")
    try:
        # 音声認識でテキストに変換する
        text = r.recognize_google(audio, language="ja-JP")
        print("あなたの答えは「{}」です。".format(text))

        # 音声ファイルとして保存する
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"data/answer_{now}.wav"
        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())


    except sr.UnknownValueError:
        print("Can't recognize the audio data.")
    except sr.RequestError as e:
        print("Error in Google Recognition: {}".format(e))

    #もし認識結果が月の名前だったら録音終了。違ったら続ける
    if text in months:
        month = months.index(text) + 1 #1月のindexが0なので1足す
        #print("あなたの答えは「{}」です。".format(text))
        break
    else:
        print("すみません。もう一度お願いします。")

#書き出した録音データを読み込む
sound = pydub.AudioSegment.from_file(filename, format = "wav")

#無音部分で分割する。基本的には分割した後のファイルが1つになるようにパラメータを調節する（つまり声の前後の無音だけがなくなるようにする)
chunks = pydub.silence.split_on_silence(sound, min_silence_len = 200, silence_thresh = -45, keep_silence = 50) #set good threshold

longest_chunk_duration = 0.
longest_chunk_id = 0

#一応2つ以上に別れた時のために、分けた音声のうち一番長いものを探し、その長さを記録しておく
for i, chunk in enumerate(chunks):
    if chunk.duration_seconds > longest_chunk_duration:
        longest_chunk_duration = chunk.duration_seconds
        longest_chunk_id = i
  
#分割後一番長かったものを記録する
chunks[longest_chunk_id].export(f"data/answer_{now}" + "_splited_" + str(i) + "_month_" + str(month) + ".wav" , format = "wav")


#rmsを求める
data = chunks[longest_chunk_id]
data = np.array(chunks[longest_chunk_id].get_array_of_samples())
x = data[::sound.channels]
rms = np.sqrt(np.mean(np.square(x)))


#oscで月の名前、rms、音声の長さ、タイムスタンプを送信する
client = udp_client.UDPClient(IP, PORT)

msg_m = OscMessageBuilder(address = '/speech/month')
msg_m.add_arg(month)
m_m = msg_m.build()

msg_r = OscMessageBuilder(address = '/speech/rms')
msg_r.add_arg(rms)
m_r = msg_r.build()

msg_d = OscMessageBuilder(address = '/speech/duration')
msg_d.add_arg(longest_chunk_duration)
m_d = msg_d.build()

msg_t = OscMessageBuilder(address = '/speech/time')
msg_t.add_arg(now)
m_t = msg_t.build()

client.send(m_m)
client.send(m_r)
client.send(m_d)
client.send(m_t)


print("month: " + str(month))
print("rms: " + str(rms))
print("duration: " + str(longest_chunk_duration))

