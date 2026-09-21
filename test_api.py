"""Check the API without using the microphone or speech output."""

from main import ActivityAssistant


if __name__ == "__main__":
    assistant = ActivityAssistant(silent=True)
    activity = assistant.get_activity()
    if activity is None:
        raise SystemExit(1)
    print("API works.")
