import modules
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcombe to the Conversational Payment Web App!"

@app.route('/process_voice')
def process_voice():
    # Recognize the voice command using the imported function
    voice_command = recognize_voice_command()
    
    # Parse the recognized voice command
    parsed_command = parse_voice_command(voice_command)
    
    # Return the parsed command as a response
    return f"Voice Command: {voice_command}<br>Parsed Command: {parsed_command}"


def recognize_voice_command():
    # Code to recognize voice command
    return "Voice command recognized"

def parse_voice_command(command):
    # Code to parse the voice command
    return f"Parsed command: {command}"




if __name__ == '__main__':
    app.run(debug=True)
