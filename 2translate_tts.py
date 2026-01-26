import threading
import tkinter as tk
from datetime import datetime
from googletrans import Translator
import pyttsx3
import speech_recognition as sr
import pyaudio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress comtypes verbose logging
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('comtypes.gen').setLevel(logging.WARNING)


# --- Initialize Translator ---
translator = Translator()

# --- Global variables for controlling the listening state ---
listening = False
listener_thread = None
processing_thread = None
current_mic_index = None  # Track which microphone we're using
stop_event = threading.Event()  # Event to signal thread to stop
microphone = None
recognizer = None
noise_adjusted = False  # Flag to track if noise adjustment has been done
audio_queue = []  # Queue to store captured audio clips

# --- Print detailed microphone information at startup ---
def print_microphone_info():
    try:
        logger.info("🎤 Microphone Information:")
        logger.info("=" * 60)
        
        # Use PyAudio to get actual microphone names
        audio = pyaudio.PyAudio()
        mic_info = []
        
        logger.info("Available microphones with names:")
        logger.info("-" * 60)
        
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            # Check if it's an input device
            if device_info['maxInputChannels'] > 0:
                name = device_info['name']
                logger.info(f"   Index {i}: {name}")
                mic_info.append((i, name))
        
        audio.terminate()
        
        if mic_info:
            logger.info(f"\n🎧 Found {len(mic_info)} input devices")
            logger.info("🔧 To use a specific microphone:")
            logger.info("   1. Look for your Snowball in the list above")
            logger.info("   2. Note its index number")
            logger.info("   3. Click the corresponding button in the GUI")
            logger.info("\n📝 IMPORTANT: Speak directly into the microphone for testing!")
        else:
            logger.warning("   No input devices found!")
            
    except Exception as e:
        logger.error(f"⚠️  Could not retrieve detailed microphone information: {e}")

# Call the function at startup
print_microphone_info()

# --- Speak asynchronously using pyttsx3 (new engine per call) ---
def speak_async(text):
    def _speak():
        engine = pyttsx3.init()  # Fresh engine in each thread
        engine.say(text)
        engine.runAndWait()

    speaker_thread = threading.Thread(target=_speak, daemon=True)
    speaker_thread.start()

# --- Fast Translation via Google Translate ---
def fast_translate(text):
    try:
        start_time = datetime.now()
        result = translator.translate(text, src='auto', dest='en')
        elapsed = datetime.now() - start_time
        logger.info(f"\n[⏱️] Translated in {elapsed.total_seconds():.2f}s")
        return result.text
    except Exception as e:
        logger.error(f"\n[ERROR] Translation failed: {e}")
        status_label.config(text="[!] Translation Failed", fg="red")
        return None

# --- Manual translation function ---
def manual_translate():
    text = manual_input_var.get()
    if text and text.strip():
        logger.info(f"⌨️ Manual input: {text}")
        original_text_var.set(f"You typed: {text}")
        
        # Translate the text
        translation = fast_translate(text)
        if translation:
            logger.info(f"\n✅ Translated: {translation}")
            translated_text_var.set(f"Translation: {translation}")
            speak_async(translation)
        else:
            logger.warning("[!] Failed to get translation.")
            translated_text_var.set("[!] Translation failed")
    else:
        original_text_var.set("Please enter some text to translate")
        translated_text_var.set("")

# --- Process audio clip ---
def process_audio_clip(audio):
    try:
        logger.info("🔍 Recognizing speech...")
        text = recognizer.recognize_google(audio, language="*")  # Auto-detect language
        
        # Only process non-empty text
        if text and text.strip():
            logger.info(f"🗣️ You said: {text}")
            original_text_var.set(f"You said: {text}")  # Update GUI with original text
            
            # Translate the recognized text
            translation = fast_translate(text)
            if translation:
                logger.info(f"\n✅ Translated: {translation}")
                translated_text_var.set(f"Translation: {translation}")  # Update GUI with translation
                speak_async(translation)
            else:
                logger.warning("[!] Failed to get translation.")
                translated_text_var.set("[!] Translation failed")
                
    except sr.UnknownValueError:
        logger.warning("[!] Could not understand audio.")
        original_text_var.set("[!] Could not understand audio")
        translated_text_var.set("")
    except sr.RequestError as e:
        logger.error(f"[ERROR] Could not request results; {e}")
        original_text_var.set("[ERROR] Speech recognition service error")
        translated_text_var.set("")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error in processing: {e}")
        original_text_var.set("[ERROR] Unexpected error occurred")
        translated_text_var.set("")

# --- Audio processing thread ---
def process_audio_queue():
    while not stop_event.is_set():
        if audio_queue:
            audio = audio_queue.pop(0)
            process_audio_clip(audio)
        else:
            # Small delay to prevent busy waiting
            threading.Event().wait(0.1)
    logger.info("⏹️ Audio processing stopped.")

# --- Initialize microphone and adjust for noise ---
def initialize_microphone():
    global microphone, recognizer, noise_adjusted
    if recognizer is None:
        recognizer = sr.Recognizer()
    
    # Use specific microphone if set, otherwise use system default
    if current_mic_index is not None:
        microphone = sr.Microphone(device_index=current_mic_index)
        logger.info(f"🎤 Using microphone index: {current_mic_index}")
    else:
        microphone = sr.Microphone()
        logger.info("🎤 Using system default microphone")
    
    # Adjust for ambient noise only once
    if not noise_adjusted:
        logger.info("🎤 Adjusting for ambient noise...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        noise_adjusted = True
        logger.info("✅ Noise adjustment completed")

# --- Listen to microphone input ---
def listen_to_microphone():
    global listening, current_mic_index, processing_thread
    stop_event.clear()  # Clear the stop event
    
    # Initialize microphone if not already done
    if microphone is None or recognizer is None:
        initialize_microphone()
    
    # Start processing thread if not already running
    if processing_thread is None or not processing_thread.is_alive():
        processing_thread = threading.Thread(target=process_audio_queue, daemon=True)
        processing_thread.start()
    
    try:
        # Keep the microphone context open for the entire listening session
        with microphone as source:
            logger.info("🎤 Listening... Please SPEAK into the microphone now.")
            logger.info("💡 Tip: Speak complete sentences and pause between phrases")
            
            while listening and not stop_event.is_set():
                # Check if we should still be listening before each iteration
                if not listening or stop_event.is_set():
                    break
                    
                try:
                    logger.info("🎙️  Ready to receive audio...")
                    # Listen with energy threshold to avoid picking up background noise
                    recognizer.energy_threshold = 300  # Adjust sensitivity
                    recognizer.pause_threshold = 1.0   # Seconds of silence to consider phrase complete
                    
                    # Listen for audio with shorter timeout
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=6)
                    
                    # Add audio to queue for processing
                    audio_queue.append(audio)
                    logger.info("🎵 Audio captured and queued for processing")
                    
                except sr.WaitTimeoutError:
                    # Timeout occurred, check if we should still be listening
                    if not listening or stop_event.is_set():
                        break
                    # Don't log timeout messages too frequently
                    continue
                except Exception as e:
                    if not listening or stop_event.is_set():
                        break
                    logger.error(f"[ERROR] Unexpected error in listening: {e}")
                    break
                    
    except Exception as e:
        logger.error(f"[ERROR] Microphone error: {e}")
        original_text_var.set("[ERROR] Microphone error")
        translated_text_var.set("")
    
    logger.info("⏹️ Microphone listening stopped.")

# --- Start listening (called on button press) ---
def start_listening():
    global listening, listener_thread, stop_event
    # Ensure no duplicate threads
    if listener_thread is not None and listener_thread.is_alive():
        logger.warning("Listener already active.")
        return
    
    # Start listening
    listening = True
    stop_event.clear()
    listener_thread = threading.Thread(target=listen_to_microphone, daemon=True)
    listener_thread.start()
    hold_button.config(bg="#e74c3c", text="🔊 Listening... (Release to stop)")
    status_label.config(text="Status: Listening...", fg="green")
    original_text_var.set("")  # Clear previous text
    translated_text_var.set("")  # Clear previous translation
    logger.info("🎤 Started listening...")
    logger.info("📢 PLEASE SPEAK INTO THE MICROPHONE NOW!")
    logger.info("💡 Tip: Speak complete sentences and pause between phrases")

# --- Stop listening (called on button release) ---
def stop_listening():
    global listening, stop_event
    if listening:
        # Stop listening (but let processing finish)
        listening = False
        hold_button.config(bg="#27ae60", text="🎤 Hold to Listen")
        status_label.config(text="Status: Processing...", fg="orange")
        logger.info("⏸️ Stopped listening. Processing remaining audio...")
        
        # Wait a bit for processing to complete, then reset status
        def reset_status():
            threading.Event().wait(3)  # Wait 3 seconds for processing
            if not listening:  # Only reset if we're still not listening
                status_label.config(text="Status: Idle", fg="orange")
        
        reset_thread = threading.Thread(target=reset_status, daemon=True)
        reset_thread.start()

# --- Set specific microphone index ---
def set_microphone_index(index):
    global current_mic_index, noise_adjusted
    current_mic_index = index
    noise_adjusted = False  # Reset noise adjustment flag when mic changes
    logger.info(f"🔧 Microphone index set to: {index}")
    status_label.config(text=f"Status: Mic {index} selected", fg="purple")

# --- Create GUI ---
root = tk.Tk()
root.title("🎤 Real-Time Voice Translator")
root.geometry("600x800")  # Increased height for manual input
root.configure(bg="#f0f0f0")
root.minsize(600, 800)  # Set minimum size

# Header Frame
header_frame = tk.Frame(root, bg="#2c3e50", height=70)
header_frame.pack(fill=tk.X, pady=(0, 10))
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="Real-Time Voice Translator", 
                      font=("Arial", 18, "bold"), fg="white", bg="#2c3e50")
title_label.pack(pady=20)

# Main Content Frame
content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

# Status Panel
status_panel = tk.Frame(content_frame, bg="#ecf0f1", relief=tk.RAISED, bd=2)
status_panel.pack(fill=tk.X, pady=(0, 20))

status_label = tk.Label(status_panel, text="Status: Idle", 
                       font=("Arial", 14, "bold"), fg="orange", bg="#ecf0f1")
status_label.pack(pady=15)

# Text Display Panel
text_panel = tk.LabelFrame(content_frame, text="Translation Results", 
                          font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
text_panel.pack(fill=tk.X, pady=(0, 20))

# Variables to hold text for display
original_text_var = tk.StringVar()
translated_text_var = tk.StringVar()

# Original Text Display
original_label = tk.Label(text_panel, text="Original Speech:", 
                         font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w")
original_label.pack(fill=tk.X, padx=10, pady=(10, 5))

original_text = tk.Label(text_panel, textvariable=original_text_var, 
                        font=("Arial", 10), bg="white", fg="black", 
                        relief=tk.SUNKEN, bd=1, wraplength=500, justify="left",
                        height=3)
original_text.pack(fill=tk.X, padx=10, pady=(0, 10))

# Translated Text Display
translated_label = tk.Label(text_panel, text="Translated Text:", 
                           font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w")
translated_label.pack(fill=tk.X, padx=10, pady=(0, 5))

translated_text = tk.Label(text_panel, textvariable=translated_text_var, 
                          font=("Arial", 10), bg="white", fg="black", 
                          relief=tk.SUNKEN, bd=1, wraplength=500, justify="left",
                          height=3)
translated_text.pack(fill=tk.X, padx=10, pady=(0, 10))

# Manual Input Panel
manual_panel = tk.LabelFrame(content_frame, text="Manual Translation", 
                            font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
manual_panel.pack(fill=tk.X, pady=(0, 20))

manual_input_var = tk.StringVar()
manual_label = tk.Label(manual_panel, text="Type text to translate:", 
                       font=("Arial", 10), bg="#f0f0f0")
manual_label.pack(pady=(10, 5))

manual_entry = tk.Entry(manual_panel, textvariable=manual_input_var, 
                       font=("Arial", 10), width=50)
manual_entry.pack(pady=(0, 10), padx=10, fill=tk.X)

manual_button = tk.Button(manual_panel, text="🔄 Translate Text", command=manual_translate,
                         font=("Arial", 10), bg="#3498db", fg="white",
                         relief=tk.RAISED, bd=2, activebackground="#2980b9")
manual_button.pack(pady=(0, 10))

# Microphone Selection Panel
mic_panel = tk.LabelFrame(content_frame, text="Microphone Settings", 
                         font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
mic_panel.pack(fill=tk.X, pady=(0, 20))

mic_label = tk.Label(mic_panel, text="Select Microphone Index:", 
                    font=("Arial", 10), bg="#f0f0f0")
mic_label.pack(pady=(10, 5))

# Create buttons for common microphone indices
mic_buttons_frame = tk.Frame(mic_panel, bg="#f0f0f0")
mic_buttons_frame.pack(pady=10)

# Buttons for indices 0-9 - FIXED using default argument technique
for i in range(10):
    btn = tk.Button(mic_buttons_frame, text=str(i), width=3, 
                   command=lambda idx=i: set_microphone_index(idx),
                   font=("Arial", 9), bg="#bdc3c7", fg="black",
                   activebackground="#95a5a6", relief=tk.RAISED)
    btn.pack(side=tk.LEFT, padx=3)

# Control Panel
control_panel = tk.Frame(content_frame, bg="#f0f0f0")
control_panel.pack(fill=tk.X, pady=(0, 20))

# Hold button (push-to-talk style)
hold_button = tk.Button(control_panel, text="🎤 Hold to Listen", 
                       font=("Arial", 14, "bold"), bg="#27ae60", fg="white", 
                       height=2, width=20, relief=tk.RAISED, bd=3,
                       activebackground="#2ecc71")
hold_button.pack(pady=10)

# Bind mouse press and release events
hold_button.bind("<ButtonPress-1>", lambda event: start_listening())
hold_button.bind("<ButtonRelease-1>", lambda event: stop_listening())

# Exit button
exit_button = tk.Button(control_panel, text="❌ Exit", command=root.destroy, 
                       font=("Arial", 12), bg="#e74c3c", fg="white", 
                       height=1, width=10, relief=tk.RAISED, bd=2,
                       activebackground="#c0392b")
exit_button.pack()

# Footer with Instructions
footer_frame = tk.Frame(root, bg="#34495e", height=100)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
footer_frame.pack_propagate(False)

instructions = tk.Label(footer_frame, 
                       text="1. Select mic index | 2. HOLD 'Hold to Listen' button | 3. SPEAK into mic", 
                       font=("Arial", 9), fg="white", bg="#34495e")
instructions.pack(pady=(10, 0))

help_text = tk.Label(footer_frame, 
                    text="Look for 'Snowball' in console list. Speak clearly!", 
                    font=("Arial", 8), fg="#aed6f1", bg="#34495e")
help_text.pack()

more_help = tk.Label(footer_frame, 
                    text="💡 Speak complete phrases, pause between sentences", 
                    font=("Arial", 8), fg="#f4d03f", bg="#34495e")
more_help.pack()

# Force window to update and show all content
root.update_idletasks()

# Start the GUI event loop
root.mainloop()
