import sys
import random
import os
import math
import glob
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QDialog, QGraphicsDropShadowEffect,
    QCalendarWidget, QTextEdit, QMessageBox, QHBoxLayout, QScrollArea,
    QFrame, QGridLayout, QDockWidget, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QFont, QColor, QPalette, QPainter, QIcon, QPixmap, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt, QTimer, QDynamicPropertyChangeEvent, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

def clean_song_name(filename):
    """Process a song filename to extract a clean song title."""
    name = os.path.splitext(filename)[0]
    
    if "Lauv - I Like Me Better" in name:
        return "Lauv - I Like Me Better"
    
    patterns = [
        r"\[.*?\]",  # e.g., [Official Video], [Lyrical]
        r"\(.*?\)",  # e.g., (Official Audio)
        r"\|.*",     # e.g., ｜ Meri Pyaari Bindu ｜ ...
        r" - .*",    # e.g., - Arijit Singh
        r"Song.*",   # e.g., Song Once upon A Time
        r"Lyric.*",  # e.g., Lyrical ｜ The Dirty Picture
    ]
    for pattern in patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    
    separators = ["｜", "|", "-", "–", ":"]
    for sep in separators:
        parts = name.split(sep)
        if len(parts) > 1:
            name = parts[0]
            break
    
    name = name.strip()
    return name if name else filename

# HeartAnimationWidget Class
class HeartAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Ignore mouse events
        self.setStyleSheet("background-color: transparent;")  # Transparent background
        self.hearts = []
        self.heart_timer = QTimer(self)
        self.heart_timer.timeout.connect(self.update_hearts)
        self.heart_timer.start(100)  # Update every 100ms

    def update_hearts(self):
        # Randomly add a new heart at the bottom
        if random.random() < 0.2:  # 20% chance per update
            x = random.randint(50, self.width() - 50)
            self.hearts.append({
                'x': x,
                'y': self.height(),
                'alpha': 255,  # Fully opaque
                'speed': random.uniform(2, 4),  # Vary speed for natural effect
                'color': QColor(255, 99, 71, 255)  # Soft tomato red, fully opaque
            })

        # Update existing hearts
        for heart in self.hearts[:]:
            heart['y'] -= heart['speed']  # Move upward
            if heart['y'] <= 0:  # Remove only when reaching or passing the top
                self.hearts.remove(heart)
            else:
                heart['color'].setAlpha(heart['alpha'])

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw floating hearts
        for heart in self.hearts:
            painter.setPen(Qt.NoPen)
            painter.setBrush(heart['color'])
            x, y = heart['x'], heart['y']
            size = 10
            path = QPainterPath()
            path.moveTo(x, y + size / 2)
            path.arcTo(x - size / 2, y - size / 2, size, size, 0, 180)
            path.arcTo(x, y - size / 2, size, size, 180, 180)
            path.lineTo(x, y + size)
            path.closeSubpath()
            painter.drawPath(path)

        painter.end()

# PlaylistWidget Class
class PlaylistWidget(QWidget):
    current_song_changed = Signal(int)  # Signal to emit when current_index changes

    def __init__(self, player, playlist, parent=None):
        super().__init__(parent)
        self.player = player
        self.original_playlist = playlist  # Store original playlist
        self.playlist = list(playlist)  # Working copy of playlist
        self.current_index = 0
        self.is_playing = True
        self.has_shuffled = False  # Flag to track if playlist has been shuffled
        self.play_next_queue = []  # Queue for "Play Next" songs
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #0d0d0d; border-left: 2px solid #4682b4;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.song_label = QLabel(self.get_current_song_name())
        self.song_label.setStyleSheet("color: #4fc3f7; font-size: 14px;")
        font = QFont("Georgia", 14)
        font.setItalic(True)
        self.song_label.setFont(font)
        self.song_label.setAlignment(Qt.AlignCenter)
        self.song_label.setWordWrap(False)
        layout.addWidget(self.song_label)

        self.scroll_offset = 0
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.update_scroll)
        self.scroll_timer.start(100)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)

        self.prev_button = QPushButton("⏮")
        self.prev_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 12px;")
        self.prev_button.clicked.connect(self.play_previous)
        control_layout.addWidget(self.prev_button)

        self.play_pause_button = QPushButton("⏸")
        self.play_pause_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 12px;")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        control_layout.addWidget(self.play_pause_button)

        self.next_button = QPushButton("⏭")
        self.next_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 12px;")
        self.next_button.clicked.connect(self.play_next)
        control_layout.addWidget(self.next_button)

        layout.addLayout(control_layout)
        layout.addStretch()

        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.current_song_changed.connect(self.update_ui)  # Connect signal to update UI

    def get_current_song_name(self):
        return self.playlist[self.current_index][0] if self.playlist else "No Song"

    def update_scroll(self):
        if not self.playlist:
            return
        song_name = self.get_current_song_name()
        metrics = self.song_label.fontMetrics()
        text_width = metrics.horizontalAdvance(song_name)
        widget_width = self.song_label.width()

        if text_width > widget_width:
            self.scroll_offset += 1
            if self.scroll_offset > text_width + 50:
                self.scroll_offset = -widget_width
            self.song_label.setText(song_name)
            self.song_label.setStyleSheet(f"color: #4fc3f7; font-size: 14px; padding-left: {-self.scroll_offset}px;")
        else:
            self.scroll_offset = 0
            self.song_label.setStyleSheet("color: #4fc3f7; font-size: 14px;")
            self.song_label.setText(song_name)

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.play_pause_button.setText("▶")
            self.is_playing = False
        else:
            self.player.play()
            self.play_pause_button.setText("⏸")
            self.is_playing = True

    def play_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.playlist) - 1
        self.current_song_changed.emit(self.current_index)  # Emit signal
        self.play_current_song()

    def play_next(self):
        if self.play_next_queue:
            next_song = self.play_next_queue.pop(0)
            for idx, (name, path) in enumerate(self.playlist):
                if name == next_song[0] and path == next_song[1]:
                    self.current_index = idx
                    break
        else:
            if self.current_index < len(self.playlist) - 1:
                self.current_index += 1
            else:
                self.current_index = 0  # Loop back to start
        self.current_song_changed.emit(self.current_index)  # Emit signal
        self.play_current_song()

    def play_current_song(self):
        if not self.playlist or self.current_index >= len(self.playlist):
            print("No songs in playlist or invalid index")
            return
        audio_path = self.playlist[self.current_index][1]
        if os.path.exists(audio_path):
            self.player.setSource(QUrl.fromLocalFile(audio_path))
            self.player.play()
            self.play_pause_button.setText("⏸")
            self.is_playing = True
        else:
            print(f"Song file not found: {audio_path}")

    def set_current_index(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.current_song_changed.emit(self.current_index)  # Emit signal
            self.play_current_song()

    def add_to_play_next(self, song):
        """Add a song to the play next queue."""
        if song not in self.play_next_queue:
            self.play_next_queue.append(song)

    def shuffle_playlist(self):
        """Shuffle the playlist, keeping Lauv first."""
        if len(self.playlist) > 1:
            lauv = self.playlist[0]  # Keep Lauv first
            rest = self.playlist[1:]  # Get the rest of the songs
            random.shuffle(rest)  # Shuffle the rest
            self.playlist = [lauv] + rest  # Reconstruct playlist
            if self.current_index > 0:
                for idx, song in enumerate(self.playlist):
                    if song == self.original_playlist[self.current_index]:
                        self.current_index = idx
                        break

    def update_ui(self):
        self.song_label.setText(self.get_current_song_name())
        self.scroll_offset = 0
        self.update_scroll()  # Force immediate UI update

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.current_index == 0 and not self.has_shuffled and self.playlist[0][0] == "Lauv - I Like Me Better":
                self.shuffle_playlist()
                self.has_shuffled = True
            self.play_next()

# PlaylistTab Class
class PlaylistTab(QWidget):
    def __init__(self, player, playlist, playlist_widget, parent=None):
        super().__init__(parent)
        self.player = player
        self.playlist = playlist
        self.playlist_widget = playlist_widget
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title_label = QLabel("🎵 Your LoveBox Playlist 🎵")
        title_label.setStyleSheet("color: #4fc3f7; font-size: 24px; font-weight: bold;")
        font = QFont("Georgia", 24)
        font.setItalic(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor(255, 255, 255, 180))
        glow.setOffset(0, 0)
        title_label.setGraphicsEffect(glow)
        layout.addWidget(title_label)

        self.song_list = QListWidget()
        self.song_list.setStyleSheet("""
            QListWidget {
                background-color: #0d0d0d;
                color: #4fc3f7;
                border: 2px solid #4682b4;
                font-size: 16px;
            }
            QListWidget::item:selected {
                background-color: #4682b4;
                color: #0d0d0d;
            }
        """)
        self.song_list.setFont(QFont("Georgia", 16))
        self.update_song_list()  # Initialize song list with queue indicators
        self.song_list.itemClicked.connect(self.play_selected_song)
        layout.addWidget(self.song_list)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        prev_button = QPushButton("⏮ Previous")
        prev_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px;")
        prev_button.setFont(QFont("Georgia", 14))
        prev_button.clicked.connect(self.playlist_widget.play_previous)
        control_layout.addWidget(prev_button)

        self.play_pause_button = QPushButton("⏸ Pause")
        self.play_pause_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px;")
        self.play_pause_button.setFont(QFont("Georgia", 14))
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        control_layout.addWidget(self.play_pause_button)

        next_button = QPushButton("Next ⏭")
        next_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px;")
        next_button.setFont(QFont("Georgia", 14))
        next_button.clicked.connect(self.playlist_widget.play_next)
        control_layout.addWidget(next_button)

        play_next_button = QPushButton("Play Next ⏩")
        play_next_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px;")
        play_next_button.setFont(QFont("Georgia", 14))
        play_next_button.clicked.connect(self.add_to_play_next)
        control_layout.addWidget(play_next_button)

        layout.addLayout(control_layout)

        self.playlist_widget.current_song_changed.connect(self.update_song_list_selection)

    def update_song_list(self):
        """Update the song list display with queue indicators."""
        self.song_list.clear()
        for idx, (song_name, _) in enumerate(self.playlist):
            display_name = song_name
            if (song_name, self.playlist[idx][1]) in self.playlist_widget.play_next_queue:
                queue_pos = self.playlist_widget.play_next_queue.index((song_name, self.playlist[idx][1])) + 1
                display_name = f"{song_name} [Next #{queue_pos}]"
            item = QListWidgetItem(display_name)
            self.song_list.addItem(item)

    def play_selected_song(self, item):
        song_name = item.text().split(" [Next")[0]  # Remove queue indicator if present
        for idx, (name, _) in enumerate(self.playlist):
            if name == song_name:
                self.playlist_widget.set_current_index(idx)  # Use setter to update index and emit signal
                self.play_pause_button.setText("⏸ Pause")
                self.song_list.setCurrentRow(idx)  # Highlight selected song
                break

    def update_song_list_selection(self, index):
        self.update_song_list()  # Refresh list to show queue changes
        self.song_list.setCurrentRow(index)  # Update selection

    def toggle_play_pause(self):
        self.playlist_widget.toggle_play_pause()
        self.play_pause_button.setText("▶ Play" if not self.playlist_widget.is_playing else "⏸ Pause")

    def add_to_play_next(self):
        """Add selected song to play next queue."""
        selected_items = self.song_list.selectedItems()
        if selected_items:
            song_name = selected_items[0].text().split(" [Next")[0]  # Remove queue indicator
            for idx, (name, path) in enumerate(self.playlist):
                if name == song_name:
                    self.playlist_widget.add_to_play_next((name, path))
                    self.update_song_list()  # Refresh to show queue indicator
                    break

# PasswordDialog Class
class PasswordDialog(QDialog):
    def __init__(self, player, audio_output, playlist):
        super().__init__()
        self.player = player
        self.audio_output = audio_output
        self.playlist = playlist
        self.setWindowTitle("Unlock LoveBox")
        self.attempts = 0
        self.correct_answers = ["peter", "peter kavinsky"]

        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.setStyleSheet("background-color: #0d0d0d;")

        self.top_image_grid = QGridLayout()
        self.top_image_grid.setSpacing(10)
        self.add_top_images()
        layout.addLayout(self.top_image_grid)

        self.label = QLabel("🔒 Enter Password to Unlock:")
        self.label.setStyleSheet("color: #4fc3f7; font-size: 18px; font-weight: bold;")
        font = QFont("Georgia", 18)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setStyleSheet("background-color: #0d0d0d; color: #4fc3f7; font-size: 16px; border: 1px solid #4682b4;")
        self.input.setFont(font)
        layout.addWidget(self.input)

        self.button = QPushButton("Unlock")
        self.button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 16px; font-weight: bold;")
        self.button.setFont(font)
        self.button.clicked.connect(self.check_password)
        layout.addWidget(self.button)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #4fc3f7; font-size: 16px;")
        self.hint_label.setFont(font)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label)

        self.bottom_image_grid = QGridLayout()
        self.bottom_image_grid.setSpacing(10)
        self.add_bottom_images()
        layout.addLayout(self.bottom_image_grid)

        self.play_first_song()

    def add_top_images(self):
        """Add three images to the top grid layout with dynamic paths."""
        image_filenames = ["P1.jpg", "p2.jpg", "P3.jpg"]
        image_dir = os.path.join(self.script_dir, "P")
        
        for idx, filename in enumerate(image_filenames):
            image_path = os.path.join(image_dir, filename)
            image_label = QLabel()  # Initialize label outside if block
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    image_label.setStyleSheet("border: 2px solid #4682b4; border-radius: 10px;")
                    self.top_image_grid.addWidget(image_label, 0, idx)
                else:
                    print(f"Failed to load image: {image_path}")
            else:
                print(f"Image not found: {image_path}")

    def add_bottom_images(self):
        """Add three images to the bottom grid layout with dynamic paths."""
        image_filenames = ["p4.jpg", "p5.jpg", "P6.jpg"]
        image_dir = os.path.join(self.script_dir, "P")
        
        for idx, filename in enumerate(image_filenames):
            image_path = os.path.join(image_dir, filename)
            image_label = QLabel()  # Initialize label outside if block
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    image_label.setStyleSheet("border: 2px solid #4682b4; border-radius: 10px;")
                    self.bottom_image_grid.addWidget(image_label, 0, idx)
                else:
                    print(f"Failed to load image: {image_path}")
            else:
                print(f"Image not found: {image_path}")

    def play_first_song(self):
        if self.playlist:
            audio_path = self.playlist[0][1]
            if os.path.exists(audio_path):
                print(f"Playing audio: {audio_path}")
                self.player.setSource(QUrl.fromLocalFile(audio_path))
                self.audio_output.setVolume(0.5)
                self.player.play()
            else:
                print(f"Audio file not found: {audio_path}")

    def check_password(self):
        text = self.input.text().strip().lower()
        if text in self.correct_answers:
            self.accept()
        else:
            self.attempts += 1
            if self.attempts == 1:
                self.hint_label.setText("Hint: The answer is your favourite fictional character.")
            elif self.attempts == 2:
                self.hint_label.setText("Answer: Peter")
            else:
                self.hint_label.setText("Try again!")

    def closeEvent(self, event):
        super().closeEvent(event)

# HomeTab Class
class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")  # Transparent to show hearts
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        heading = QLabel("💙 Welcome to Your LoveBox 💙")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Georgia", 36)
        font.setItalic(True)
        heading.setFont(font)
        heading.setStyleSheet("color: #4fc3f7;")

        glow_heading = QGraphicsDropShadowEffect()
        glow_heading.setBlurRadius(40)
        glow_heading.setColor(QColor(255, 255, 255, 180))
        glow_heading.setOffset(0, 0)
        heading.setGraphicsEffect(glow_heading)

        message = QLabel("A special place just for you, my dory, my sunflower, my goobe, my love, my everything, my cutie, my model.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_msg = QFont("Georgia", 18)
        font_msg.setItalic(True)
        message.setFont(font_msg)
        message.setStyleSheet("color: #4fc3f7;")

        glow_message = QGraphicsDropShadowEffect()
        glow_message.setBlurRadius(30)
        glow_message.setColor(QColor(255, 255, 255, 140))
        glow_message.setOffset(0, 0)
        message.setGraphicsEffect(glow_message)

        heart = QLabel("❤️")
        heart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heart_font = QFont("Georgia", 48)
        heart.setFont(heart_font)
        heart.setProperty("fontSize", 48)

        glow_heart = QGraphicsDropShadowEffect()
        glow_heart.setBlurRadius(50)
        glow_heart.setColor(QColor(255, 255, 255, 200))
        glow_heart.setOffset(0, 0)
        heart.setGraphicsEffect(glow_heart)

        original_event = heart.event
        def heart_event(self, event):
            if isinstance(event, QDynamicPropertyChangeEvent) and event.propertyName() == b"fontSize":
                font = self.font()
                font.setPointSize(int(self.property("fontSize")))
                self.setFont(font)
            return original_event(event)

        heart.event = heart_event.__get__(heart, QLabel)

        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addWidget(heart)

# PoemTab Class
class PoemTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")  # Transparent to show hearts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        self.init_main_view()

    def init_main_view(self):
        self.clear_layout()

        font = QFont("Georgia", 20)
        font.setItalic(True)

        self.old_button = QPushButton("📜 Old Poems")
        self.old_button.setFont(font)
        self.old_button.setStyleSheet("""
            QPushButton {
                background-color: #0d0d0d;
                color: #4fc3f7;
                border: 2px solid #4682b4;
                border-radius: 20px;
                padding: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #000000;
                color: #4682b4;
            }
        """)
        self.old_button.clicked.connect(self.show_old_poems)

        self.new_button = QPushButton("📝 New Poems")
        self.new_button.setFont(font)
        self.new_button.setStyleSheet("""
            QPushButton {
                background-color: #0d0d0d;
                color: #4fc3f7;
                border: 2px solid #4682b4;
                border-radius: 20px;
                padding: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #000000;
                color: #4682b4;
            }
        """)
        self.new_button.clicked.connect(self.show_new_poems)

        self.layout.addStretch()
        self.layout.addWidget(self.old_button)
        self.layout.addWidget(self.new_button)
        self.layout.addStretch()

    def show_old_poems(self):
        self.clear_layout()
        font = QFont("Georgia", 18)
        font.setItalic(True)

        title_label = QLabel("📜 Old Poems")
        title_label.setStyleSheet("color: #4fc3f7; font-size: 24px; font-weight: bold;")
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glow_title = QGraphicsDropShadowEffect()
        glow_title.setBlurRadius(30)
        glow_title.setColor(QColor(255, 255, 255, 180))
        glow_title.setOffset(0, 0)
        title_label.setGraphicsEffect(glow_title)

        poems = [
            """She is moonlight and moonshine,\nThe gentle ray of white hope,\nThe warm sip of emotion,\nShe's the relief that comes after a drizzle.""",
            """She's prettier than any poem of mine,\nShe's nicer than any concoction of my words,\nHer smile could fix broken glass,\nHer eyes are the crown jewels,\nAnd she's as pure as the Ganges.""",
            """She's snuck into my life,\nIn the dead of night, like an owl,\nMy gods isn't she nice?\nOh she does fix my soul.""",
            """Sunflowers are admired by her,\nUnbeknownst, they envy her,\nFor even they cannot replicate her charm,\nAnd that smile, that makes the world feel warm."""
        ]

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background-color: transparent; border: none;")  # Transparent to show hearts
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        for idx, poem_text in enumerate(poems):
            poem_frame = QFrame()
            poem_frame.setStyleSheet("""
                background-color: #0d0d0d;
                border-left: 4px solid #4682b4;
                border-top: 1px solid #4682b4;
                border-right: 1px solid #4682b4;
                border-bottom: 1px solid #4682b4;
                border-radius: 10px;
                padding: 15px;
            """)

            glow_effect = QGraphicsDropShadowEffect()
            glow_effect.setBlurRadius(20)
            glow_effect.setColor(QColor(255, 255, 255, 180))
            glow_effect.setOffset(0, 0)
            poem_frame.setGraphicsEffect(glow_effect)

            poem_label = QLabel(poem_text)
            poem_label.setStyleSheet("color: #4fc3f7; font-size: 16px; background-color: transparent; padding: 10px;")
            poem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            poem_label.setWordWrap(True)
            poem_label.setFont(font)

            frame_layout = QVBoxLayout(poem_frame)
            frame_layout.setContentsMargins(10, 10, 10, 10)
            frame_layout.addWidget(poem_label)

            poem_frame.setMinimumWidth(250)

            row = idx // 2
            col = idx % 2
            scroll_layout.addWidget(poem_frame, row, col)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        back_button = QPushButton("⬅️ Go Back")
        back_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 16px; font-weight: bold; padding: 10px;")
        back_button.setFont(font)
        back_button.clicked.connect(self.init_main_view)

        self.layout.addWidget(title_label)
        self.layout.addWidget(scroll_area)
        self.layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_new_poems(self):
        self.clear_layout()
        label = QLabel("📝 Welcome to the new poems corner...\n\nThe stars you love,\nI bottled them tight,\nThey whisper your name,\nIn silence and light.")
        label.setStyleSheet("color: #4fc3f7; font-size: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setFont(QFont("Georgia", 18, QFont.Weight.Bold))

        back_button = QPushButton("⬅️ Go Back")
        back_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 16px; font-weight: bold; padding: 10px;")
        back_button.setFont(QFont("Georgia", 14))
        back_button.clicked.connect(self.init_main_view)

        self.layout.addWidget(label)
        self.layout.addWidget(back_button)

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

# TerminalTab Class
class TerminalTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")  # Transparent to show hearts
        layout = QVBoxLayout(self)
        label = QLabel("> This will be your fake terminal soon 💻")
        label.setStyleSheet("color: #4fc3f7; font-family: Consolas; font-size: 14px;")
        font = QFont("Georgia", 14)
        font.setItalic(True)
        label.setFont(font)
        layout.addWidget(label)

# MemoriesTab Class
class MemoriesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent; color: #4fc3f7;")  # Transparent to show hearts
        main_layout = QVBoxLayout(self)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { background-color: #0d0d0d; color: #4fc3f7; }
            QCalendarWidget QAbstractItemView:enabled { color: #4fc3f7; selection-background-color: #4682b4; selection-color: #0d0d0d; }
            QCalendarWidget QToolButton { background-color: #0d0d0d; color: #4fc3f7; }
            QCalendarWidget QMenu { background-color: #0d0d0d; color: #4fc3f7; }
        """)
        font = QFont("Georgia", 14)
        font.setItalic(True)
        self.calendar.setFont(font)

        self.story_display = QTextEdit()
        self.story_display.setReadOnly(True)
        self.story_display.setStyleSheet("background-color: #0d0d0d; color: #4fc3f7; font-size: 14px; border: 1px solid #4682b4;")
        self.story_display.setFont(font)

        self.gift_button = QPushButton("🎁 Gift")
        self.gift_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px; font-weight: bold;")
        self.gift_button.setFont(font)
        self.gift_button.clicked.connect(self.open_gift)

        self.story_game_label = QLabel("🌟 Interactive story coming soon! 🌟")
        self.story_game_label.setStyleSheet("color: #4fc3f7; font-size: 16px; font-style: italic;")
        self.story_game_label.setAlignment(Qt.AlignCenter)
        self.story_game_label.setFont(font)

        self.calendar.selectionChanged.connect(self.load_selected_date)

        main_layout.addWidget(self.calendar)
        main_layout.addWidget(self.story_display)
        main_layout.addWidget(self.gift_button)
        main_layout.addWidget(self.story_game_label)

        self.stories = {
            "2025-06-05": "OUR one month and what a way to celebrate it huh? I felt so happy when you called me, hearing your voice made me go so full very goofy, smiley and happy, as usual I lost all track of time with you! And you telling me that I made you smile just as much also made me feel special! 💖",
            "2025-06-04": "We have had such cute conversations today, I melted off so much when you just said 'how was your day honey' like cho cute and idk it made me melt offf, us having that conversation about the first time we said 'I love you' to each other and us working together on your report was adorable 💕",
            "2025-06-03": "This HAS to include the poem you sent me, you just made me feel so competent and happy, just such a nice thing to send me, its my favourite thing to read in a day, I love you and hehe you know how to just fix my mood 📜",
            "2025-06-02": "Haha my first day of work and you getting up so early for me, everyday you do ofc, it makes my day! You were with me the wholeeeee day even skipping on sleep for my sake, and then you getting all happy happy that I was jealous of the medical guy, my standup routine too, SUCH a nice conversation that was, you saying 'id do more bad stuff' if I was your punishment, lines like these make me melttttt melttt melttttt 😘",
            "2025-06-01": "YES this was the night I had to text you on Snapchat cause WhatsApp was being a bitch, I was in my native and at every scene I was like 'I need to show her this', full photographer I became cause I wanted to share memories w you, its also the day you randomly reassured me because you didnt want to hurt me even in normal conversation, cute af moment 📸",
            "2025-05-31": "YOU BEING ALL INTERESTED IN MY SPAM, NATIVE STORIES AND STORIES, so cute cute to seeeeee, you gave me so much company as usual! 🌟",
            "2025-05-30": "OH TODAY YOU TOLD ME ABOUT YOUR BRO ALSO ADMIRING YOUR SUNFLOWER WALLPAPER, you then gave me your post esa list, so nicely youve written and made for me, YOU SAID, 'everything is best with you' WHAT A NICE LINE TO COMPLIMENT!!! 🌻",
            "2025-05-29": "This be the day I plugged in 10 things I hate about you and you teared up, babied me and just loved me so much, (YOU WRITING I love you 10 times, hehehehe) And calling me the reason for your smile everytime made me cry tears of happiness 🎬",
        }

        self.load_selected_date()

    def load_selected_date(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        story = self.stories.get(date, "No story for this date yet. But every day with you is special 💖")
        self.story_display.setPlainText(story)

    def open_gift(self):
        QMessageBox.information(self, "Virtual Gift Box", "🎁 You opened a virtual gift! More surprises coming soon! 🎉")

# GamesTab Class
class GamesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")  # Transparent to show hearts
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 20, 40)
        layout.setSpacing(20)

        self.instruction_label = QLabel("💖 Navigate the Maze! Use arrow keys to move ❤️ to 💖")
        self.instruction_label.setStyleSheet("color: #4fc3f7; font-size: 16px;")
        font = QFont("Georgia", 16)
        font.setItalic(True)
        self.instruction_label.setFont(font)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instruction_label)

        self.maze = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 3, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]
        self.player_pos = [1, 1]
        self.cell_size = 40

        self.game_area = QWidget()
        self.game_area.setStyleSheet("background-color: #0d0d0d; border: 2px solid #4682b4; border-radius: 10px;")
        self.game_area.setFixedSize(10 * self.cell_size, 10 * self.cell_size)
        layout.addWidget(self.game_area, alignment=Qt.AlignCenter)

        self.labels = []
        for row in range(10):
            row_labels = []
            for col in range(10):
                label = QLabel("", self.game_area)
                label.setFixedSize(self.cell_size, self.cell_size)
                label.setAlignment(Qt.AlignCenter)
                label.move(col * self.cell_size, row * self.cell_size)
                row_labels.append(label)
            self.labels.append(row_labels)

        self.update_maze()

        self.setFocusPolicy(Qt.StrongFocus)
        self.game_area.setFocusPolicy(Qt.StrongFocus)
        self.game_area.setFocus()
        layout.addStretch()

    def showEvent(self, event):
        self.game_area.setFocus()
        super().showEvent(event)

    def update_maze(self):
        font = QFont("Georgia", 18)
        font.setItalic(True)
        for row in range(10):
            for col in range(10):
                label = self.labels[row][col]
                label.setGraphicsEffect(None)
                if self.maze[row][col] == 1:
                    label.setStyleSheet("background-color: #0d0d0d; border: none;")
                    label.setText("")
                elif self.maze[row][col] == 0:
                    label.setStyleSheet("background-color: #0d0d0d; border: 1px solid #4682b4;")
                    label.setText("")
                elif self.maze[row][col] == 2:
                    label.setStyleSheet("background-color: #0d0d0d; color: #4fc3f7; border: 1px solid #4682b4;")
                    label.setText("❤️")
                    label.setFont(font)
                    glow = QGraphicsDropShadowEffect()
                    glow.setBlurRadius(20)
                    glow.setColor(QColor(255, 255, 255, 200))
                    glow.setOffset(0, 0)
                    label.setGraphicsEffect(glow)
                elif self.maze[row][col] == 3:
                    label.setStyleSheet("background-color: #0d0d0d; color: #4fc3f7; border: 1px solid #4682b4;")
                    label.setText("💖")
                    label.setFont(font)
                    glow = QGraphicsDropShadowEffect()
                    glow.setBlurRadius(20)
                    glow.setColor(QColor(255, 255, 255, 180))
                    glow.setOffset(0, 0)
                    label.setGraphicsEffect(glow)

    def keyPressEvent(self, event):
        row, col = self.player_pos
        new_row, new_col = row, col

        if event.key() == Qt.Key_Up:
            new_row -= 1
        elif event.key() == Qt.Key_Down:
            new_row += 1
        elif event.key() == Qt.Key_Left:
            new_col -= 1
        elif event.key() == Qt.Key_Right:
            new_col += 1

        if 0 <= new_row < 10 and 0 <= new_col < 10 and self.maze[new_row][new_col] != 1:
            self.maze[row][col] = 0
            self.maze[new_row][new_col] = 2
            self.player_pos = [new_row, new_col]
            self.update_maze()

            if new_row == 8 and new_col == 8:
                self.show_win_dialog()

    def show_win_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("You Found My Heart! 💖")
        dialog.setStyleSheet("background-color: #0d0d0d;")
        dialog.setFixedSize(400, 400)

        layout = QVBoxLayout(dialog)
        font = QFont("Georgia", 14)
        font.setItalic(True)

        messages = [
            "You found my heart through the maze of life! 💕",
            "Every step you take leads to my heart! ❤️",
            "You navigated to my love, my hero! 😘",
            "You reached my heart, now it’s yours forever! 💖"
        ]
        message_label = QLabel(random.choice(messages))
        message_label.setStyleSheet("color: #4fc3f7; font-size: 14px;")
        message_label.setFont(font)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)

        glow_message = QGraphicsDropShadowEffect()
        glow_message.setBlurRadius(20)
        glow_message.setColor(QColor(255, 255, 255, 180))
        glow_message.setOffset(0, 0)
        message_label.setGraphicsEffect(glow_message)

        sunflower_widget = SunflowerWidget()
        sunflower_widget.setFixedSize(300, 300)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 12px; font-weight: bold;")
        close_button.setFont(font)
        close_button.clicked.connect(dialog.accept)

        layout.addWidget(message_label)
        layout.addWidget(sunflower_widget, alignment=Qt.AlignCenter)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        dialog.exec()

# SunflowerWidget Class
class SunflowerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.draw_stage = 0
        self.setStyleSheet("background-color: #0d0d0d;")

        self.draw_timer = QTimer(self)
        self.draw_timer.timeout.connect(self.update_drawing)
        self.draw_timer.start(50)

    def update_drawing(self):
        if self.draw_stage >= 3:
            self.draw_timer.stop()
            return

        self.progress += 2
        if self.progress >= 100:
            self.draw_stage += 1
            self.progress = 0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x, center_y = self.width() // 2, self.height() // 2
        max_radius = min(self.width(), self.height()) // 3

        if self.draw_stage >= 0:
            pen = QPen(QColor("#FFD700"), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(255, 215, 0, 200)))

            num_petals = 12
            for i in range(num_petals):
                if self.draw_stage == 0 and i * (100 / num_petals) > self.progress:
                    continue
                angle = i * 360 / num_petals
                rad = math.radians(angle)

                start_x = center_x + max_radius * 0.5 * math.cos(rad)
                start_y = center_y + max_radius * 0.5 * math.sin(rad)
                end_x = center_x + max_radius * 1.5 * math.cos(rad)
                end_y = center_y + max_radius * 1.5 * math.sin(rad)

                mid_x1 = center_x + max_radius * math.cos(rad + math.radians(10))
                mid_y1 = center_y + max_radius * math.sin(rad + math.radians(10))
                mid_x2 = center_x + max_radius * math.cos(rad - math.radians(10))
                mid_y2 = center_y + max_radius * math.sin(rad - math.radians(10))

                path = QPainterPath()
                path.moveTo(start_x, start_y)
                path.cubicTo(mid_x1, mid_y1, mid_x2, mid_y2, end_x, end_y)
                path.cubicTo(mid_x2 - 10, mid_y2 + 10, mid_x1 + 10, mid_y1 - 10, start_x, start_y)
                painter.drawPath(path)

        if self.draw_stage >= 1:
            progress = min(self.progress / 100, 1) if self.draw_stage == 1 else 1
            pen = QPen(QColor("#8B4513"), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(139, 69, 19, int(255 * progress))))
            radius = max_radius * 0.5 * progress
            painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))

        if self.draw_stage >= 2:
            pen = QPen(QColor("#654321"), 1, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#654321")))
            num_seeds = 20
            for i in range(num_seeds):
                if i * (100 / num_seeds) > self.progress:
                    continue
                seed_angle = i * 360 / num_seeds + 45
                seed_rad = math.radians(seed_angle)
                seed_dist = max_radius * 0.3 * (i / num_seeds)
                seed_x = center_x + seed_dist * math.cos(seed_rad)
                seed_y = center_y + seed_dist * math.sin(seed_rad)
                painter.drawEllipse(int(seed_x - 2), int(seed_y - 2), 4, 4)

        painter.end()

# CakeWidget Class
class CakeWidget(QWidget):
    def __init__(self, cake_type, parent=None):
        super().__init__(parent)
        self.cake_type = cake_type
        self.setFixedSize(400, 300)

        self.colors = {
            "chocolate": ("#8B4513", "#5C4033", "#3F2A1D"),
            "strawberry": ("#FFB6C1", "#FF9999", "#FF6666"),
            "vanilla": ("#FFF8DC", "#FFF5E1", "#FFF0DB")
        }
        self.layer_colors = self.colors.get(cake_type, ("#FFF8DC", "#FFF5E1", "#FFF0DB"))

        self.draw_stage = 0
        self.progress = 0

        self.draw_timer = QTimer(self)
        self.draw_timer.timeout.connect(self.update_drawing)
        self.draw_timer.start(50)

        self.countdown_active = False
        self.countdown_seconds = 5
        self.show_flames = True

        self.countdown_label = QLabel("", self)
        self.countdown_label.setStyleSheet("color: #4fc3f7; font-size: 20px; font-weight: bold; background-color: transparent;")
        font = QFont("Georgia", 20)
        font.setItalic(True)
        self.countdown_label.setFont(font)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setGeometry(0, 10, 400, 50)
        self.countdown_label.hide()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)

    def update_drawing(self):
        if self.draw_stage >= 5:
            self.draw_timer.stop()
            self.start_countdown()
            return

        self.progress += 5
        if self.progress >= 100:
            self.draw_stage += 1
            self.progress = 0

        self.update()

    def start_countdown(self):
        self.countdown_active = True
        self.countdown_seconds = 5
        self.countdown_label.setText(f"Make a Wish! ({self.countdown_seconds})")
        self.countdown_label.show()
        self.countdown_timer.start(1000)

    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Make a Wish! ({self.countdown_seconds})")
        else:
            self.countdown_timer.stop()
            self.countdown_active = False
            self.show_flames = False
            self.countdown_label.setText("Wish Made! 💖")
            QTimer.singleShot(2000, self.countdown_label.hide)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#4fc3f7"), 2, Qt.SolidLine)
        painter.setPen(pen)

        base_x, base_y = 100, 250
        layer_widths = [200, 180, 160]
        layer_heights = [60, 50, 40]

        if self.draw_stage >= 0:
            width = layer_widths[0] * min(self.progress / 100, 1) if self.draw_stage == 0 else layer_widths[0]
            painter.setBrush(QBrush(QColor(self.layer_colors[0])))
            painter.drawRect(base_x, base_y - layer_heights[0], int(width), layer_heights[0])

        if self.draw_stage >= 1:
            width = layer_widths[1] * min(self.progress / 100, 1) if self.draw_stage == 1 else layer_widths[1]
            painter.setBrush(QBrush(QColor(self.layer_colors[1])))
            painter.drawRect(base_x + 10, base_y - layer_heights[0] - layer_heights[1], int(width), layer_heights[1])

        if self.draw_stage >= 2:
            width = layer_widths[2] * min(self.progress / 100, 1) if self.draw_stage == 2 else layer_widths[2]
            painter.setBrush(QBrush(QColor(self.layer_colors[2])))
            painter.drawRect(base_x + 20, base_y - layer_heights[0] - layer_heights[1] - layer_heights[2], int(width), layer_heights[2])

        if self.draw_stage >= 3:
            candle_positions = [base_x + 50, base_x + 100, base_x + 150]
            for i, x in enumerate(candle_positions):
                height = 30 * min(self.progress / 100, 1) if self.draw_stage == 3 else 30
                if i * 33 < self.progress or self.draw_stage > 3:
                    painter.setBrush(QBrush(QColor("#F5F5F5")))
                    painter.drawRect(x, base_y - layer_heights[0] - layer_heights[1] - layer_heights[2] - int(height), 10, int(height))
                    if (self.draw_stage > 3 or self.progress > 50) and self.show_flames:
                        painter.setBrush(QBrush(QColor("#FFD700")))
                        painter.drawEllipse(x + 2, base_y - layer_heights[0] - layer_heights[1] - layer_heights[2] - int(height) - 10, 6, 10)

        if self.draw_stage >= 4:
            painter.setFont(QFont("Georgia", 12))
            painter.setPen(QColor("#FFD700"))
            sparkle_positions = [(base_x + 40, base_y - 150), (base_x + 100, base_y - 150), (base_x + 160, base_y - 150)]
            for i, (x, y) in enumerate(sparkle_positions):
                if i * 33 < self.progress or self.draw_stage > 4:
                    painter.drawText(x, y, "✨")

        painter.end()

# CakeTab Class
class CakeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")  # Transparent to show hearts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 40, 20, 40)
        main_layout.setSpacing(10)

        self.instruction_label = QLabel("🎂 Choose a Birthday Cake, My Love! 🎂")
        self.instruction_label.setStyleSheet("color: #4fc3f7; font-size: 22px; font-weight: bold;")
        font = QFont("Georgia", 22)
        font.setItalic(True)
        self.instruction_label.setFont(font)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor(255, 255, 255, 180))
        glow.setOffset(0, 0)
        self.instruction_label.setGraphicsEffect(glow)
        main_layout.addWidget(self.instruction_label)

        self.cake_container = QWidget()
        self.cake_container.setFixedSize(400, 300)
        self.cake_container.setStyleSheet("background-color: #0d0d0d; border: 2px solid #4682b4; border-radius: 10px;")
        self.cake_layout = QVBoxLayout(self.cake_container)
        self.cake_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.cake_container, alignment=Qt.AlignCenter)

        self.current_cake_widget = None

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.cake_buttons = []
        cake_options = [
            ("Chocolate Dream 🍫", "chocolate"),
            ("Strawberry Bliss 🍓", "strawberry"),
            ("Vanilla Elegance 🍦", "vanilla"),
        ]

        for cake_name, cake_type in cake_options:
            btn = QPushButton(cake_name)
            btn.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 14px; font-weight: bold; padding: 8px;")
            btn.setFont(QFont("Georgia", 14))
            btn.clicked.connect(lambda checked, ct=cake_type: self.display_cake(ct))
            self.cake_buttons.append(btn)
            control_layout.addWidget(btn)

        main_layout.addLayout(control_layout)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #4fc3f7; font-size: 18px;")
        self.message_label.setFont(QFont("Georgia", 18, QFont.Weight.Bold))
        self.message_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.message_label)

    def display_cake(self, cake_type):
        if self.current_cake_widget:
            self.cake_layout.removeWidget(self.current_cake_widget)
            self.current_cake_widget.deleteLater()

        self.current_cake_widget = CakeWidget(cake_type)
        self.cake_layout.addWidget(self.current_cake_widget)

        self.instruction_label.setText(f"🎂 Watch Your {cake_type.capitalize()} Cake Being Drawn, Love! 🎂")
        self.message_label.setText("Happy Birthday, My Sunflower! 🎉💖")


# LoveBoxApp Class
class LoveBoxApp(QMainWindow):
    def __init__(self, player, audio_output):
        super().__init__()
        self.player = player
        self.audio_output = audio_output
        self.setWindowTitle("LoveBox — For Her 💖")
        self.setGeometry(100, 100, 800, 580)

        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        music_dir = os.path.join(self.script_dir, "M")
        wav_files = glob.glob(os.path.join(music_dir, "*.wav"))
        self.playlist = []
        lauv_file = "Lauv - I Like Me Better [Official Video] 4.wav"
        lauv_path = os.path.join(music_dir, lauv_file)
        if os.path.exists(lauv_path):
            self.playlist.append(("Lauv - I Like Me Better", lauv_path))
        for file_path in sorted(wav_files):
            if os.path.basename(file_path) != lauv_file:
                song_name = clean_song_name(os.path.basename(file_path))
                self.playlist.append((song_name, file_path))

        icon_path = os.path.join(self.script_dir, "sunflower_icon.png")
        if os.path.exists(icon_path):
            print(f"Icon found at: {icon_path}")
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#0d0d0d"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor("#FFD700")))
            painter.drawEllipse(8, 8, 16, 16)
            painter.setBrush(QBrush(QColor("#8B4513")))
            painter.drawEllipse(12, 12, 8, 8)
            painter.setPen(QPen(QColor("#4682b4"), 2))
            painter.drawLine(8, 8, 24, 24)
            painter.end()
            self.setWindowIcon(QIcon(pixmap))
            print("Using fallback placeholder icon")

        # Create the heart animation widget
        self.heart_animation = HeartAnimationWidget(self)
        self.heart_animation.setGeometry(0, 0, 800, 580)  # Match window size
        self.heart_animation.lower()  # Ensure it stays behind other widgets

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.addTab(HomeTab(), "Home")
        self.tabs.addTab(PoemTab(), "Poems")
        self.tabs.addTab(TerminalTab(), "Letter")
        self.tabs.addTab(MemoriesTab(), "Memories")
        self.tabs.addTab(GamesTab(), "Games")
        self.tabs.addTab(CakeTab(), "Birthday Cake")
        playlist_widget = PlaylistWidget(self.player, self.playlist)
        self.tabs.addTab(PlaylistTab(self.player, self.playlist, playlist_widget), "Playlist")
        main_layout.addWidget(self.tabs)

        self.playlist_dock = QDockWidget()
        self.playlist_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.playlist_dock.setTitleBarWidget(QWidget())
        self.playlist_dock.setWidget(playlist_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.playlist_dock)

        self.player.errorOccurred.connect(self.handle_media_error)

    def resizeEvent(self, event):
        # Resize the heart animation widget to match the window size
        self.heart_animation.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def handle_media_error(self, error):
        print(f"Media Player Error: {self.player.errorString()} (Error code: {error})")

    def closeEvent(self, event):
        print("Application closing, stopping audio")
        self.player.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d0d0d"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#4fc3f7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d0d0d"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0d0d0d"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#4fc3f7"))
    app.setPalette(palette)

    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    audio_output.setVolume(0.5)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_dir = os.path.join(script_dir, "M")
    wav_files = glob.glob(os.path.join(music_dir, "*.wav"))
    playlist = []
    lauv_file = "Lauv - I Like Me Better [Official Video] 4.wav"
    lauv_path = os.path.join(music_dir, lauv_file)
    if os.path.exists(lauv_path):
        playlist.append(("Lauv - I Like Me Better", lauv_path))
    for file_path in sorted(wav_files):
        if os.path.basename(file_path) != lauv_file:
            song_name = clean_song_name(os.path.basename(file_path))
            playlist.append((song_name, file_path))

    pwd_dialog = PasswordDialog(player, audio_output, playlist)
    if pwd_dialog.exec() == QDialog.DialogCode.Accepted:
        window = LoveBoxApp(player, audio_output)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)