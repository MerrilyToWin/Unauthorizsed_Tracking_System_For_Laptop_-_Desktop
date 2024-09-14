import os
import datetime
import pickle
import cv2
from PIL import Image, ImageTk
import tkinter as tk
import util
from tkinter import ttk
from pynput.keyboard import Listener
import face_recognition
from anti_spoof_test import test
from tkinter import messagebox

'''-----------------------------UI-----------------------------'''
def create_main_window():
    root = tk.Tk()
    root.title("Login Window")

    # Set the dimensions of the window
    window_width = 900
    window_height = 390

    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the position for the window to be centered
    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    # Set the geometry of the window and center it
    root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
    root.resizable(False, False)  # Prevent resizing

    # Set a stylish theme for the window
    style = ttk.Style()
    style.theme_use('clam')  # You can try 'clam', 'default', 'alt', 'classic'

    return root

def login():
    name = name_entry.get()
    email = email_entry.get()
    password = password_entry.get()

    if name and email and password:
        # Store the credentials in a file
        store_credentials(name, email, password)
        # Capture and store the face data
        capture(name)

        # Clear the entry fields
        name_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

        root.quit()
        root.destroy()
    else:
        util.msg_box("Login Error", "Please enter name, email, and password.")

def toggle_password(password_entry, show_var):
    if show_var.get():
        password_entry.config(show="")
    else:
        password_entry.config(show="*")

def setup_ui(root): 
    padding_x = 10
    padding_y = 10

    # Background color
    root.configure(background="#F0F8FF")  # Light blue background

    # Main frame with rounded corners
    main_frame = ttk.Frame(root, padding="20 20 20 20", style="TFrame")
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Define the style
    style = ttk.Style()
    style.configure("TFrame", background="#F0F8FF")
    style.configure("Accent.TButton", foreground="white", background="#008000", font=('Arial', 12, 'bold'), relief="flat")
    style.map("Accent.TButton", background=[("active", "#008000")])

    style.configure("TLabel", background="#F0F8FF", font=('Arial', 14, 'bold'), foreground="#1E90FF")
    style.configure("TEntry", padding="5", relief="flat")

    # Input frame for credentials with a soft shadow
    input_frame = ttk.Frame(main_frame, padding="15 15 15 15", style="TFrame", relief="solid")
    input_frame.grid(row=0, column=0, padx=padding_x, pady=padding_y, sticky="nw")

    # Name entry
    name_label = ttk.Label(input_frame, text="Name:", style="TLabel")
    name_label.grid(row=0, column=0, padx=padding_x, pady=padding_y, sticky="e")
    name_entry = ttk.Entry(input_frame, width=30, font=('Arial', 12))
    name_entry.grid(row=0, column=1, padx=padding_x, pady=padding_y)

    # Email entry
    email_label = ttk.Label(input_frame, text="Email:", style="TLabel")
    email_label.grid(row=1, column=0, padx=padding_x, pady=padding_y, sticky="e")
    email_entry = ttk.Entry(input_frame, width=30, font=('Arial', 12))
    email_entry.grid(row=1, column=1, padx=padding_x, pady=padding_y)

    # Password entry
    password_label = ttk.Label(input_frame, text="Password:", style="TLabel")
    password_label.grid(row=2, column=0, padx=padding_x, pady=padding_y, sticky="e")
    password_entry = ttk.Entry(input_frame, show="*", width=30, font=('Arial', 12))
    password_entry.grid(row=2, column=1, padx=padding_x, pady=padding_y)

    # Show password check button
    show_var = tk.BooleanVar()
    show_password_check = ttk.Checkbutton(input_frame, text="Show Password", variable=show_var, command=lambda: toggle_password(password_entry, show_var), style="TCheckbutton")
    show_password_check.grid(row=3, column=1, padx=padding_x, pady=padding_y, sticky="w")

    # Login button with rounded corners
    login_button = ttk.Button(input_frame, text="Login", command=login, style="Accent.TButton", padding="10")
    login_button.grid(row=4, column=0, columnspan=2, pady=padding_y, padx=padding_x, sticky="ew")

    # Webcam feed area with a modern look
    webcam_frame = ttk.Frame(main_frame, padding="10 10 10 10", relief="solid", borderwidth=2, style="TFrame")
    webcam_frame.grid(row=0, column=1, padx=padding_x, pady=padding_y, sticky="ne")

    webcam_label = tk.Label(webcam_frame, background="black", width=320, height=245)
    webcam_label.grid(row=0, column=0, padx=padding_x, pady=padding_y)

    # Status label for user feedback with a more inviting color
    status_label = ttk.Label(main_frame, text="Please login or register your face.", font=('Arial', 14, 'bold'), foreground="#008000", style="TLabel")
    status_label.grid(row=1, column=0, columnspan=2, pady=padding_y)

    # Return all key components
    return name_entry, email_entry, password_entry, show_var, webcam_label, status_label



'''-----------------------------DIR--------------------------'''

# Initialize directories
db_dir = './db'
unauthorized_access_dir = './Unauthorized access'
if not os.path.exists(db_dir):
    os.mkdir(db_dir)
if not os.path.exists(unauthorized_access_dir):
    os.mkdir(unauthorized_access_dir)

keylog_file = './keylog.txt'

def store_credentials(name, email, password):
    file_path = os.path.join(os.getcwd(), 'credentials.txt')
    with open(file_path, 'a') as file:
        file.write(f"Name: {name}, Email: {email}, Password: {password}\n")


'''-----------------------------KEYLOGGER--------------------------'''

listener = None  # Global listener for keylogger

# Function to start the keylogger
def start_keylogger():
    global listener  # Declare listener as global so we can start and stop it
    def on_press(key):
        with open(keylog_file, 'a') as log_file:
            log_file.write(f'{datetime.datetime.now()} - {key}\n')

    # Start listening to keystrokes
    listener = Listener(on_press=on_press)
    listener.start()  # The keylogger will run in the background



'''----------------------CAMERA OPERATION----------------------'''

check_done = False
warning_shown = False

def is_camera_covered(frame, threshold=50):
    # Convert frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate the mean pixel value of the frame
    mean_pixel_value = gray_frame.mean()
    
    # If the mean pixel value is below the threshold, the frame is mostly black
    if mean_pixel_value < threshold:
        return True
    return False

# Function to capture and store face data upon login
def capture(name):
    ret, frame = cap.read()
    if not ret:
        messagebox.showwarning("Capture Error", "Failed to capture image from webcam.")
        return

    face_locations = face_recognition.face_locations(frame)
    if not face_locations:
        messagebox.showwarning("Face Not Detected", "No face detected. Please try again.")
        return

    face_encodings = face_recognition.face_encodings(frame, face_locations)
    if not face_encodings:
        messagebox.showwarning("Face Not Detected", "No face encodings found. Please try again.")
        return

    # Assuming we use the first detected face
    embeddings = face_encodings[0]

    file_path = os.path.join(db_dir, f'{name}.pickle')
    with open(file_path, 'wb') as file:
        pickle.dump(embeddings, file)  
    root.destroy()



# Function to check for registered users
def check_registered_users(frame):
    global warning_shown, check_done

    # Check if the function has already run
    if check_done:
        return
    

    # Check if there are any .pickle files in the db directory
    if not any(filename.endswith('.pickle') for filename in os.listdir(db_dir)):
        if not warning_shown:
            warning_shown = True
        return
    
    # Perform anti-spoofing test
    label = test(
        image=frame,
        model_dir="C:/Users/merwi/OneDrive/Desktop/IDX/Face-Reg/resources/anti_spoof_models",
        device_id=0
    )

    if label == 1:
        # Anti-spoofing passed, proceed with face recognition
        known_face_encodings = []
        known_face_names = []

        # Load known face encodings and names
        for filename in os.listdir(db_dir):
            if filename.endswith('.pickle'):
                with open(os.path.join(db_dir, filename), 'rb') as file:
                    encoding = pickle.load(file)
                    known_face_encodings.append(encoding)
                    known_face_names.append(os.path.splitext(filename)[0])

        # Find faces in the current frame
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        # Check if any face in the frame matches a known face
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                util.msg_box("Welcome Back", f"Welcome back, {name}!")
                root.quit()
                root.destroy()
                
                # Mark the check as done so the function won't run again
                check_done = True
                return
        
        # No registered face found
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unauthorized_image_path = os.path.join(unauthorized_access_dir, f'unknown_{timestamp}.jpg')
        cv2.imwrite(unauthorized_image_path, frame)
        util.msg_box('Unknown user.', "Unknown user detected")
        start_keylogger()

    else:
        # Anti-spoofing failed
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        spoofed_image_path = os.path.join(unauthorized_access_dir, f'spoofer_{timestamp}.jpg')
        cv2.imwrite(spoofed_image_path, frame)
        util.msg_box('Hey, you are a spoofer!', "Spoofer detected!")
        start_keylogger()

    # Mark the check as done so the function won't run again
    check_done = True

def start_webcam(cap, webcam_label, root):
    def update_webcam():
        ret, frame = cap.read()
        if ret:
            (frame_height, frame_width) = frame.shape[:2]
            box_width, box_height = 140, 152  # Width and height of the rectangle
            start_x = (frame_width - box_width) // 2
            start_y = (frame_height - box_height) // 2
            end_x = start_x + box_width
            end_y = start_y + box_height

            # Draw the rectangle on the frame
            cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2) 

            if is_camera_covered(frame):
                messagebox.showwarning("Camera Error", "Please remove your hand or visor from the camera.")
                start_webcam(cap,webcam_label,root)
                return

            img_ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_ = Image.fromarray(img_)
            imgtk = ImageTk.PhotoImage(image=img_)
            webcam_label.imgtk = imgtk
            webcam_label.config(image=imgtk)

            check_registered_users(frame)
        
        root.after(10, update_webcam)

    update_webcam()



'''--------------------MAIN--------------------'''


def main():
    global root, cap, name_entry, email_entry, password_entry, show_var, webcam_label, status_label

    # Check if the database is empty
    if not os.listdir(db_dir):
        # Database is empty, show login window
        root = create_main_window()
        name_entry, email_entry, password_entry, show_var, webcam_label, status_label = setup_ui(root)

        # Setup webcam feed
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Start updating the webcam feed
        start_webcam(cap, webcam_label, root)

        root.mainloop()
    else:
        # Database is not empty, start face recognition
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            check_registered_users(frame)

# Execute the main function
if __name__ == "__main__":
    main()
