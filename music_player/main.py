from tkinter import *
import ttkbootstrap as tb
from googleapiclient.discovery import build
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
from pytube import YouTube
import vlc
from tkinter import messagebox
from tkinter import simpledialog

# Global variable to keep track of player state
is_playing = False

current_media = None

current_index = -1 

# cachne directory which will download and store songs
cache_dir = 'cache'

# list for recent_songs
recent_songs = []

# Window Setup
root = tb.Window(themename='darkly')
root.title('Melodify')
root.iconbitmap("images/music_logo2.ico")
root.geometry("1600x800")

# function to get_api_key from user
def get_api_key():
    api_file = "api.txt"
    try:
        with open(api_file, "r") as f:
            api_key = f.read().strip()
            if api_key:
                return api_key
            else:
                messagebox.showinfo("API Key", "The API key file is empty. Please input your YouTube API key.")
    except FileNotFoundError:
        messagebox.showinfo("API Key", "The API key file doesn't exist. Please input your YouTube API key.")

    # Prompt user for API key using a messagebox
    api_key = simpledialog.askstring("API Key", "Please input your YouTube API key:")
    if api_key:
        with open(api_file, "w") as f:
            f.write(api_key)
        return api_key
    else:
        messagebox.showerror("API Key", "No API key provided. Exiting program.")
        exit()

# Get the API key
api_key = get_api_key() 
youtube = build('youtube', 'v3', developerKey=api_key)

# function to show_info_message
def show_info_message(message):
    messagebox.showinfo("Info", message)

# function to show_warning_message
def show_warning_message(message):
    messagebox.showwarning("Warning", message)

# function to show_error_message
def show_error_message(message):
    messagebox.showerror("Error", message)

# function to search songs from yt
def search(event=None):
    query = search_entry.get()
    if not query:  # If search query is empty, display recent songs
        display_recent_songs()
        return
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=15
        )
        response = request.execute()

        results_listbox.delete(0, END)

        for item in response['items']:
            title = item['snippet']['title']
            # Extract video ID
            video_id = item['id']['videoId']
            # Extract high resolution thumbnail url
            thumbnail_url = item['snippet']['thumbnails']['high']['url']
            results_listbox.insert(END, title)
            # Store video ID and thumbnail URL as additional data in listbox item
            results_listbox.video_ids[results_listbox.size() - 1] = (video_id, thumbnail_url)
            # Insert a blank line for padding
            results_listbox.insert(END, "")
    except Exception as e:
        show_error_message(f"An error occurred during search: {e}")

# function to stop playing songs
def stop_current_song():
    global current_media
    print("stopping..")
    if current_media:
        try:
            current_media.stop()  # Stop the currently playing media
            print("stopped!")
        except Exception as e:
            show_error_message(f"An error occurred while stopping the media: {e}")

# function to select from list_box
def on_select(event):
    # Check if there is a selection
    try:
        index = results_listbox.curselection()[0]
    except IndexError:
        return  # If no selection, return without further action
    
    # Check if the selected item has a corresponding video ID
    if index in results_listbox.video_ids:
        # Get video ID and thumbnail URL associated with the selected item
        video_id, thumbnail_url = results_listbox.video_ids[index]
        
        # Get the title of the selected item
        title = results_listbox.get(index)
        
        # Open music player with the selected video
        open_music_player(video_id, title)

        # Download and display the thumbnail image
        response = requests.get(thumbnail_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo  # keep a reference to the image

# function to get recent songs
def get_recent_songs():
    try:
        # Get list of files in the cache directory
        files = os.listdir(cache_dir)
        # Extract titles from the filenames and return as recent songs
        recent_songs = [os.path.splitext(file)[0] for file in files]
        return recent_songs
    except Exception as e:
        show_error_message(f"An error occurred while fetching recent songs: {e}")
        return []


# Function to add a song to the list of recent songs
def add_recent_song(video_id, title):
    # Add the song to the recent songs list
    recent_songs.append((video_id, title))
    # Limit the size of the recent songs list to, for example, 10
    if len(recent_songs) > 50:
        recent_songs.pop(0)  # Remove the oldest song if the list exceeds the limit

# Function to display recent songs in the listbox
def display_recent_songs():
    try:
        # Code to fetch recent songs and populate the listbox
        recent_songs = get_recent_songs()
        if recent_songs:
            results_listbox.delete(0, END)
            for song in recent_songs:
                results_listbox.insert(END, song)
        else:
            show_info_message("No recent songs found.")
    except Exception as e:
        show_error_message(f"An error occurred while displaying recent songs: {e}")

# function to open music_player
def open_music_player(video_id, title):
    try:
        stop_current_song()
        add_recent_song(video_id, title)  
        # Get the index of the currently selected item
        selected_index = results_listbox.curselection()

        # Check if an item is selected
        if selected_index:
            # Get the selected item
            selected_item = results_listbox.get(selected_index)
            # Padding between start and end
            selected_item += '      '
            # Set the text of song_label to the selected item
            song_label.config(text=selected_item)
            scroll_text(song_label)

            # Check if the song is already downloaded (cached)
            filename_mp4 = os.path.join(cache_dir, f"{video_id}.mp4")
            if not os.path.exists(filename_mp4):
                # If not, download the audio from YouTube
                url = f"https://www.youtube.com/watch?v={video_id}"
                youtube = YouTube(url)
                stream = youtube.streams.filter(only_audio=True).first()
                # Make sure the cache directory exists
                os.makedirs(cache_dir, exist_ok=True)
                stream.download(output_path=cache_dir, filename=f"{video_id}.mp4")
                success_label.config(text=f'{video_id}.mp4 sucess', bootstyle = "success")
        else:
            play(video_id)
    except Exception as e:
        show_error_message(f"An error occurred: {e}")

# function to handel scroll text
def scroll_text(label):
    def delayed_action():
        text = label.cget("text")
        text = text[1:] + text[0]
        label.config(text=text)
        label.after(200, scroll_text, label)

    # Delay the start of the scrolling
    label.after(600, delayed_action)

# Function to handle play button pressS
def play_button_pressed():
    global is_playing
    if is_playing:
        try:
            player.play()
            is_playing = False
        except Exception as e:
            show_error_message(f"An error occurred while pausing the audio: {e}")
    else:
        index = results_listbox.curselection()
        if index:
            video_id = results_listbox.video_ids[index[0]][0]
            play(video_id)
            is_playing = True



def stop_button_pressed():
    try:
        player.pause()  # Pause the song
    except Exception as e:
        show_error_message(f"An error occurred while stopping the audio: {e}")

def play(video_id):
    try:
        global player  # Make player a global variable
        instance = vlc.Instance('--input-repeat=-1', '--fullscreen')
        player = instance.media_player_new()
        player.set_media(instance.media_new(f"cache/{video_id}.mp4"))
        player.play()
        root.after(100, lambda: check_player_state(player))  # Check player state periodically
    except Exception as e:
        show_error_message(f"An error occurred while playing the audio: {e}")

def next_button_pressed():
    global current_index
    if current_index < results_listbox.size() - 2:  # Check if there's a next item
        current_index += 2
        # Adjust the index to account for the empty lines in the listbox
        adjusted_index = current_index // 2
        # Check if the adjusted index exists in the video_ids dictionary
        if adjusted_index in results_listbox.video_ids:
            # Access video ID and thumbnail URL from video_ids dictionary
            video_id, _ = results_listbox.video_ids[adjusted_index]
            open_music_player(video_id, '')  # Pass '' as the title argument
        else:
            show_warning_message("Video ID not found for the selected index.")
    else:
        show_info_message("No next item available.")

def previous_button_pressed():
    global current_index
    if current_index > 0:  # Check if there's a previous item
        current_index -= 2
        # Adjust the index to account for the empty lines in the listbox
        adjusted_index = current_index // 2
        # Check if the adjusted index exists in the video_ids dictionary
        if adjusted_index in results_listbox.video_ids:
            # Access video ID and thumbnail URL from video_ids dictionary
            video_id, _ = results_listbox.video_ids[adjusted_index]
            open_music_player(video_id, '')  # Pass '' as the title argument
        else:
            show_warning_message("Video ID not found for the selected index.")
    else:
        show_info_message("No previous item available.")

def play_song_at_index(index):
    # Get the video ID associated with the index
    video_id, _ = results_listbox.video_ids[index]
    open_music_player(video_id)

def check_player_state(player):
    state = player.get_state()
    if state == vlc.State.Ended:
        player.release()
    elif state == vlc.State.Stopped:
        player.release()
    else:
        root.after(100, lambda: check_player_state(player))

# Frame
bar_frame = tb.Frame(root, bootstyle="dark", padding=10)
bar_frame.pack(fill=X)

# Left Label
search_label = tb.Label(bar_frame, text="Search:", font=("Helvetica", 12), width=7)
search_label.pack(side='left')

# Entry Widget
search_entry = tb.Entry(bar_frame, bootstyle='light', font=("Helvetica", 12), foreground='white')
search_entry.pack(side='left', fill=X, expand=True)
root.bind("<Return>", lambda event=None: search())

# Style For Button
search_style = tb.Style()
search_style.configure("dark.TButton", font=("", 16))

# Right Button
search_button = tb.Button(bar_frame, text="\U0001F50D", style='dark.TButton', command=search)
search_button.pack(side='right')

# Listbox to display search result with a horizontal scrollbar
results_listbox = Listbox(root, font=("Helvetica", 12), foreground="white")
scroll = tb.Scrollbar(results_listbox, orient="horizontal", bootstyle = 'light')

# config
scroll.config(command=results_listbox.xview)
results_listbox.config(xscrollcommand=scroll.set)

# pack
results_listbox.pack(fill=BOTH, expand=True, padx=5, side='left')
scroll.pack(side="bottom", fill=X)


# Frame for the player
player_frame = tb.Frame(root, bootstyle = "dark", width=100)
player_frame.pack(side='right', fill='both', expand=True)
player_frame.pack_propagate(False)

# Frame for image
image_frame = tb.Frame(player_frame, bootstyle = 'dark')
image_frame.pack(side="top", fill='x')

# Image label
label = tb.Label(image_frame, text="\U0001F3B5", bootstyle = "dark", font=("Helvetica", 130))
label.pack()

# Song frame
song_frame = tb.Frame(player_frame, bootstyle = "dark")
song_frame.pack(side="top", fill='x')

# Song label
song_label = tb.Label(song_frame, text="None Selected     ", bootstyle = "inverse dark", font=("Helvetica", 12), width=40)
song_label.pack(pady=30)
scroll_text(song_label)

# Song time frame
song_time_frame = tb.Frame(player_frame, bootstyle = "dark")
song_time_frame.pack(side="top", fill='x', pady=15)

# Song time label
song_time_label = tb.Label(song_time_frame, text="0.00", bootstyle = "inverse dark", font=("Helvetica", 12))
song_time_label.pack(side='left')

# Song time progress bar
song_time_bar = tb.Progressbar(song_time_frame, mode="determinate", bootstyle = "light")
song_time_bar.pack(side='right', fill='x', padx=20, expand=True)

# label for sucees
success_label = tb.Label(player_frame, text='', bootstyle = 'inverse dark', font=("helvetica", 12))
success_label.pack(pady=20)

# Button frame
button_frame = tb.Frame(player_frame, bootstyle = "dark")
button_frame.pack(side="bottom", pady=20)

# Buttons
pause_button = tb.Button(button_frame, text="\u23F8", bootstyle = 'dark', command=stop_button_pressed)
pause_button.pack(side="right", padx=5)

play_button = tb.Button(button_frame, text="\u25B6", bootstyle = 'dark', command=play_button_pressed)
play_button.pack(side="right", padx=5)

previous_button = tb.Button(button_frame, text="\u23EE", bootstyle = 'dark', command=previous_button_pressed)
previous_button.pack(side="left", padx=5)

next_button = tb.Button(button_frame, text="\u23ED", bootstyle = 'dark', command=next_button_pressed)
next_button.pack(side="left", padx=5)

# Storing video IDs as additional data
results_listbox.video_ids = {}

# Binding selection event to on_select function
results_listbox.bind("<<ListboxSelect>>", on_select)

root.mainloop()
