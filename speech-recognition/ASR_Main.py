import argparse
import os
from sys import platform
from ASRHelper import transcribe_asr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the English model.")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real-time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    parser.add_argument("--default_microphone", default='pulse' if 'linux' in platform else None,
                        help="Default microphone name for SpeechRecognition. "
                             "Run this with 'list' to view available Microphones.", type=str)

    args = parser.parse_args()

    # Initialize the generator with the specified arguments
    transcriber = transcribe_asr(model=args.model,
                                 non_english=args.non_english,
                                 energy_threshold=args.energy_threshold,
                                 record_timeout=args.record_timeout,
                                 phrase_timeout=args.phrase_timeout,
                                 default_microphone=args.default_microphone)

    # Clear the console to display the transcription.
    os.system('cls' if os.name == 'nt' else 'clear')

    try:
        for line, language in transcriber:
            print(line)
            print(language)
            # Flush stdout.
            print('', end='', flush=True)
    except KeyboardInterrupt:
        pass

    print("\n\nTranscription:")
    for line, _ in transcriber:
        print(line)


if __name__ == "__main__":
    main()
