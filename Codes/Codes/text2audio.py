from gtts import gTTS
import os

text = "Hello, how are you? I am speaking in Indian English."

tts = gTTS(text=text, lang='en', tld='co.in')  # 'co.in' gives Indian accent
tts.save("indian_accent.mp3")
os.system("start indian_accent.mp3")
