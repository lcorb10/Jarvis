import pyttsx3

engine = pyttsx3.init()
voces = engine.getProperty('voices')

for v in voces:
    print(v.id)
    print(v.name)
    print("------")