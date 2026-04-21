import pyttsx3

e = pyttsx3.init()
voces = e.getProperty('voices')

print("Voces disponibles:")
for v in voces:
    print(f"  Nombre: {v.name}")
    print(f"  ID: {v.id}")
    print("---")

print("\nProbando voz...")
e.say("Hola, soy Jarvis, tu asistente personal")
e.runAndWait()
print("Listo.")