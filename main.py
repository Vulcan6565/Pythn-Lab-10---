"""Lab 10. Student: Denis Novikov-Ahbabovic. Variant 6: activity assistant."""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("The requests package is missing. Double-click START_LAB.bat first.")
    raise SystemExit(1)

from prepare_model import MODEL_DIR, model_is_ready


BASE_DIR = Path(__file__).resolve().parent
SAVE_FILE = BASE_DIR / "saved_activities.txt"
# A compatible replacement for the old Bored API in the assignment.
API_URL = "https://bored-api.appbrewery.com/random"
COMMANDS = "random, name, participants, type, next, save, help, exit"


class ActivityAssistant:
    def __init__(self, silent=False):
        self.current_activity = None
        self.engine = None

        if not silent:
            try:
                import pyttsx3

                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 165)
            except Exception as error:
                self.engine = None
                print("Speech output is unavailable:", error)
                print("Answers will be printed. See README.txt for setup.")

    def speak(self, text):
        """Print the answer and read it aloud if speech is available."""
        print("Assistant:", text)
        if self.engine is not None:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as error:
                print("Speech output stopped:", error)
                print("Answers will still be printed.")
                self.engine = None

    def get_activity(self):
        """Request an activity and check the fields used by our commands."""
        try:
            response = requests.get(API_URL, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise ValueError("The API did not return an activity object.")
            if not isinstance(data.get("activity"), str) or not data["activity"].strip():
                raise ValueError("The activity name is missing.")
            if type(data.get("participants")) is not int or data["participants"] < 1:
                raise ValueError("The number of participants is invalid.")

        except (requests.RequestException, ValueError) as error:
            print("API error:", error)
            self.speak("Sorry, I could not get an activity. Please try again.")
            return None

        # Keep the previous activity if the request failed.
        self.current_activity = data
        print("\n--- CURRENT ACTIVITY ---")
        print("Activity:", data["activity"])
        print("Type:", data.get("type", "Unknown"))
        print("Participants:", data["participants"])
        print("Price:", data.get("price", "Unknown"))
        print("------------------------\n")
        return data

    def make_sure_activity_exists(self):
        if self.current_activity is None:
            self.speak("There is no current activity. I will get one now.")
            return self.get_activity()
        return self.current_activity

    def command_random(self):
        activity = self.get_activity()
        if activity:
            self.speak("Your random activity is " + activity["activity"])

    def command_name(self):
        activity = self.make_sure_activity_exists()
        if activity:
            self.speak("The activity is " + activity["activity"])

    def command_participants(self):
        activity = self.make_sure_activity_exists()
        if activity:
            number = activity["participants"]
            word = "participant" if number == 1 else "participants"
            self.speak(f"This activity needs {number} {word}.")

    def command_type(self):
        activity = self.make_sure_activity_exists()
        if activity:
            self.speak("The activity type is " + str(activity.get("type", "unknown")))

    def command_next(self):
        activity = self.get_activity()
        if activity:
            self.speak("The next activity is " + activity["activity"])

    def command_save(self):
        activity = self.make_sure_activity_exists()
        if not activity:
            return

        try:
            with SAVE_FILE.open("a", encoding="utf-8") as file:
                file.write(f"Activity: {activity['activity']}\n")
                file.write(f"Type: {activity.get('type', 'Unknown')}\n")
                file.write(f"Participants: {activity['participants']}\n")
                file.write(f"Price: {activity.get('price', 'Unknown')}\n")
                file.write("-" * 40 + "\n")
            self.speak("The activity has been saved.")
            print("Saved to:", SAVE_FILE)
        except OSError as error:
            print("File error:", error)
            self.speak("Sorry, I could not save the activity.")

    def command_help(self):
        self.speak("Available commands are " + COMMANDS + ".")

    def handle_command(self, command):
        """Return False when the user asks to exit."""
        command = command.lower().strip()
        print("You said:", command)

        if command == "random":
            self.command_random()
        elif command == "name":
            self.command_name()
        elif command in ("participants", "participant"):
            self.command_participants()
        elif command == "type":
            self.command_type()
        elif command == "next":
            self.command_next()
        elif command == "save":
            self.command_save()
        elif command == "help":
            self.command_help()
        elif command in ("exit", "stop", "quit"):
            self.speak("Goodbye.")
            return False
        else:
            self.speak("I did not recognize that command. Say help for commands.")
        return True


def run_text_mode(silent=False):
    """Keyboard mode for checking commands without a microphone."""
    assistant = ActivityAssistant(silent)
    print("\nTEXT MODE")
    assistant.command_help()

    while True:
        command = input("Command: ").strip()
        if command and not assistant.handle_command(command):
            break
    return 0


def listen_for_command(stream, recognizer, sample_rate):
    """Wait for a completed command, including when background noise continues."""
    buffered_seconds = 0.0

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if not data:
            raise OSError("The microphone returned no audio data.")

        seconds = len(data) / 2 / sample_rate
        buffered_seconds += seconds

        ended = recognizer.AcceptWaveform(data)
        if ended:
            result = json.loads(recognizer.Result())
        elif buffered_seconds >= 6.0:
            # Background noise can prevent Vosk from detecting a pause.
            # Finalize a short recording instead of waiting indefinitely.
            result = json.loads(recognizer.FinalResult())
        else:
            continue

        command = result.get("text", "").strip()
        recognizer.Reset()
        if command:
            return command

        # Stay listening after silence. Do not silently exit or invent a command.
        if buffered_seconds >= 6.0:
            buffered_seconds = 0.0


def run_voice_mode(silent=False):
    try:
        import pyaudio
        from vosk import Model, KaldiRecognizer, SetLogLevel
    except (ImportError, OSError) as error:
        print("A voice package could not be loaded:", error)
        print("Double-click START_LAB.bat to set up the correct Python environment.")
        return 1

    if not model_is_ready(MODEL_DIR):
        print("The speech model is missing or incomplete:", MODEL_DIR)
        print("Double-click START_LAB.bat to prepare it.")
        return 1

    SetLogLevel(-1)
    print("Loading Vosk model...")
    try:
        model = Model(str(MODEL_DIR))
    except Exception as error:
        print("Could not load the speech model:", error)
        print("Extract the complete ZIP into a fresh folder and run START_LAB.bat.")
        return 1

    grammar = json.dumps([
        "random", "name", "participants", "participant", "type",
        "next", "save", "help", "exit", "stop", "quit", "[unk]"
    ])
    audio = None
    stream = None

    try:
        audio = pyaudio.PyAudio()
        # Use the Windows default microphone automatically.
        device = audio.get_default_input_device_info()
        sample_rate = int(device["defaultSampleRate"])
        recognizer = KaldiRecognizer(model, sample_rate, grammar)
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=int(device["index"]),
            frames_per_buffer=4000,
            start=False
        )

        assistant = ActivityAssistant(silent)
        print("\nVOICE MODE. Say one command in English, then pause for two seconds.")
        print("Commands:", COMMANDS)
        assistant.speak("Voice assistant is ready. Say help for commands.")
        stream.start_stream()
        print("Listening...")

        while True:
            command = listen_for_command(stream, recognizer, sample_rate)
            # Pause recording so the assistant does not hear its own reply.
            stream.stop_stream()
            if not assistant.handle_command(command):
                break
            recognizer.Reset()
            stream.start_stream()
            print("Listening...")

    except (OSError, ValueError) as error:
        print("Microphone error:", error)
        print("Select a working default microphone in Windows Sound settings.")
        print("Allow microphone access for desktop apps in Windows settings.")
        print("You can also run START_LAB.bat --text to check the commands.")
        return 1
    finally:
        if stream is not None:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()
    return 0


def main():
    print("=" * 60)
    print("LAB 10 - VOICE ASSISTANT")
    print("Student: Denis Novikov-Ahbabovic")
    print("Variant 6 - Random Activity")
    print("=" * 60)

    silent = "--silent" in sys.argv
    try:
        if "--text" in sys.argv:
            return run_text_mode(silent)
        return run_voice_mode(silent)
    except KeyboardInterrupt:
        print("\nStopped by a keyboard interrupt (Ctrl+C or the editor Stop command).")
        return 0
    except EOFError:
        print("\nInput was closed. Run the program in a terminal or with START_LAB.bat.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
