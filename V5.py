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
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent;")
        self.hearts = []
        self.heart_timer = QTimer(self)
        self.heart_timer.timeout.connect(self.update_hearts)
        self.heart_timer.start(100)

    def update_hearts(self):
        if random.random() < 0.2:
            x = random.randint(50, self.width() - 50)
            self.hearts.append({
                'x': x,
                'y': self.height(),
                'alpha': 255,
                'speed': random.uniform(2, 4),
                'color': QColor(255, 99, 71, 255)
            })

        for heart in self.hearts[:]:
            heart['y'] -= heart['speed']
            if heart['y'] <= 0:
                self.hearts.remove(heart)
            else:
                heart['color'].setAlpha(heart['alpha'])

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

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
    current_song_changed = Signal(int)

    def __init__(self, player, playlist, parent=None):
        super().__init__(parent)
        self.player = player
        self.original_playlist = playlist
        self.playlist = list(playlist)
        self.current_index = 0
        self.is_playing = True
        self.has_shuffled = False
        self.play_next_queue = []
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
        self.current_song_changed.connect(self.update_ui)

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
        self.current_song_changed.emit(self.current_index)
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
                self.current_index = 0
        self.current_song_changed.emit(self.current_index)
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
            self.current_song_changed.emit(self.current_index)
            self.play_current_song()

    def add_to_play_next(self, song):
        if song not in self.play_next_queue:
            self.play_next_queue.append(song)

    def shuffle_playlist(self):
        if len(self.playlist) > 1:
            lauv = self.playlist[0]
            rest = self.playlist[1:]
            random.shuffle(rest)
            self.playlist = [lauv] + rest
            if self.current_index > 0:
                for idx, song in enumerate(self.playlist):
                    if song == self.original_playlist[self.current_index]:
                        self.current_index = idx
                        break

    def update_ui(self):
        self.song_label.setText(self.get_current_song_name())
        self.scroll_offset = 0
        self.update_scroll()

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
        self.update_song_list()
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
        self.song_list.clear()
        for idx, (song_name, _) in enumerate(self.playlist):
            display_name = song_name
            if (song_name, self.playlist[idx][1]) in self.playlist_widget.play_next_queue:
                queue_pos = self.playlist_widget.play_next_queue.index((song_name, self.playlist[idx][1])) + 1
                display_name = f"{song_name} [Next #{queue_pos}]"
            item = QListWidgetItem(display_name)
            self.song_list.addItem(item)

    def play_selected_song(self, item):
        song_name = item.text().split(" [Next")[0]
        for idx, (name, _) in enumerate(self.playlist):
            if name == song_name:
                self.playlist_widget.set_current_index(idx)
                self.play_pause_button.setText("⏸ Pause")
                self.song_list.setCurrentRow(idx)
                break

    def update_song_list_selection(self, index):
        self.update_song_list()
        self.song_list.setCurrentRow(index)

    def toggle_play_pause(self):
        self.playlist_widget.toggle_play_pause()
        self.play_pause_button.setText("▶ Play" if not self.playlist_widget.is_playing else "⏸ Pause")

    def add_to_play_next(self):
        selected_items = self.song_list.selectedItems()
        if selected_items:
            song_name = selected_items[0].text().split(" [Next")[0]
            for idx, (name, path) in enumerate(self.playlist):
                if name == song_name:
                    self.playlist_widget.add_to_play_next((name, path))
                    self.update_song_list()
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
        image_filenames = ["P1.jpg", "p2.jpg", "P3.jpg"]
        image_dir = os.path.join(self.script_dir, "P")
        
        for idx, filename in enumerate(image_filenames):
            image_path = os.path.join(image_dir, filename)
            image_label = QLabel()
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
        image_filenames = ["p4.jpg", "p5.jpg", "P6.jpg"]
        image_dir = os.path.join(self.script_dir, "P")
        
        for idx, filename in enumerate(image_filenames):
            image_path = os.path.join(image_dir, filename)
            image_label = QLabel()
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
# HomeTab Class
class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Jake Peralta-themed heading
        heading = QLabel("💖 Welcome to Your Nine-Nine LoveBox, My Amy! 💖")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Georgia", 36)
        font.setItalic(True)
        heading.setFont(font)
        heading.setStyleSheet("color: #4fc3f7; border: 2px solid #4682b4; border-radius: 10px; padding: 10px;")
        glow_heading = QGraphicsDropShadowEffect()
        glow_heading.setBlurRadius(40)
        glow_heading.setColor(QColor(255, 255, 255, 180))
        glow_heading.setOffset(0, 0)
        heading.setGraphicsEffect(glow_heading)
        layout.addWidget(heading)

        # Jake-inspired romantic message
        message = QLabel(
            "To my partner in crime, my McClane to my Holly, my sunflower with a badge: \n"
            "You’re the Amy to my Jake, turning every day into a *Die Hard* adventure. \n"
            "Your smile is my ‘Noice!’ and your heart is my precinct. This LoveBox is our heist, \n"
            "packed with love, laughs, and maybe a Nakatomi Plaza-level surprise. I’m all in, my detective! \n \n"
            "EVERY BUTTON IN THIS LOVEBOX IS CLICKABLE! PLEASE CLICK THEM ALL"
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_msg = QFont("Georgia", 18)
        font_msg.setItalic(True)
        message.setFont(font_msg)
        message.setStyleSheet("color: #4fc3f7;")
        message.setWordWrap(True)
        glow_message = QGraphicsDropShadowEffect()
        glow_message.setBlurRadius(30)
        glow_message.setColor(QColor(255, 255, 255, 140))
        glow_message.setOffset(0, 0)
        message.setGraphicsEffect(glow_message)
        layout.addWidget(message)

        # Jake’s love notes section
        love_notes_label = QLabel("Jake’s Love Notes 💌")
        love_notes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        love_notes_label.setStyleSheet("color: #4fc3f7; font-size: 20px; font-weight: bold;")
        love_notes_label.setFont(QFont("Georgia", 20, QFont.Weight.Bold))
        glow_notes = QGraphicsDropShadowEffect()
        glow_notes.setBlurRadius(30)
        glow_notes.setColor(QColor(255, 255, 255, 180))
        glow_notes.setOffset(0, 0)
        love_notes_label.setGraphicsEffect(glow_notes)
        layout.addWidget(love_notes_label)

        love_notes = [
            "You’re my dream heist partner, cooler than a *Die Hard* explosion! 💥",
            "Your laugh is my ‘Cool cool cool cool cool,’ no doubt, no doubt! 😎",
            "I’d climb Nakatomi Plaza to see your smile every day, my Amy. ❤️",
            "You make my heart go ‘Noice!’ every time you’re near. 💖"
        ]
        notes_layout = QGridLayout()
        notes_layout.setSpacing(10)
        for idx, note in enumerate(love_notes):
            note_label = QLabel(note)
            note_label.setStyleSheet("color: #4fc3f7; font-size: 14px; border: 1px solid #4682b4; border-radius: 5px; padding: 5px;")
            note_label.setFont(QFont("Georgia", 14))
            note_label.setWordWrap(True)
            note_label.setAlignment(Qt.AlignCenter)
            notes_layout.addWidget(note_label, idx // 2, idx % 2)
        layout.addLayout(notes_layout)

        # Jake’s catchphrase button
        self.catchphrases = [
            "Noice! 😎",
            "Yippee-ki-yay, my love! 💥",
            "Cool cool cool cool cool. 💖",
            "This is our heist, baby! 😜"
        ]
        self.catchphrase_index = 0
        self.catchphrase_button = QPushButton(self.catchphrases[self.catchphrase_index])
        self.catchphrase_button.setStyleSheet("""
            QPushButton {
                background-color: #0d0d0d;
                color: #4fc3f7;
                border: 2px solid #4682b4;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #4682b4;
                color: #0d0d0d;
            }
        """)
        self.catchphrase_button.setFont(QFont("Georgia", 18, QFont.Weight.Bold))
        self.catchphrase_button.clicked.connect(self.cycle_catchphrase)
        glow_catchphrase = QGraphicsDropShadowEffect()
        glow_catchphrase.setBlurRadius(30)
        glow_catchphrase.setColor(QColor(255, 255, 255, 180))
        glow_catchphrase.setOffset(0, 0)
        self.catchphrase_button.setGraphicsEffect(glow_catchphrase)
        layout.addWidget(self.catchphrase_button, alignment=Qt.AlignCenter)

    def cycle_catchphrase(self):
        self.catchphrase_index = (self.catchphrase_index + 1) % len(self.catchphrases)
        self.catchphrase_button.setText(self.catchphrases[self.catchphrase_index])

# PoemTab Class
class PoemTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
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
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
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
        self.setStyleSheet("background-color: transparent;")
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
        self.setStyleSheet("background-color: transparent; color: #4fc3f7;")
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
        self.setStyleSheet("background-color: transparent;")
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
        self.setStyleSheet("background-color: transparent;")
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

# QualitiesTab Class
class QualitiesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        title_label = QLabel("💖 100 Things I Love About You 💖")
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
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        grid_layout = QGridLayout(scroll_widget)
        grid_layout.setSpacing(10)

        self.qualities = [
    # Jake Peralta-inspired qualities (1-50)
    {"name": "Your Loving Gaze", "desc": "Your eyes hit me like a ‘Noice!’ from across the precinct, my Amy. They’re warmer than a Brooklyn coffee shop in winter, making me feel like John McClane saving the day. It’s not just a look—it’s a full-on heist of my heart, like I’m storming Nakatomi Plaza to win you over. I could stare into those eyes forever, and I’d never want a different case. You make every moment epic, like the best *Die Hard* scene, and I’m so lucky you’re my partner."},
    {"name": "You Make Me Feel Unique", "desc": "You make me feel like the only detective in the Nine-Nine, my Amy. It’s like I’ve cracked the case of your heart, and you see all my goofy *Die Hard* quotes and still choose me. Your love makes me feel like the star of our own heist movie, no cuts needed. You get my chaos, my ‘Cool cool cool,’ and love it anyway. I’m forever grateful you make me feel one-of-a-kind, my sunflower, in this crazy precinct we call life."},
    {"name": "I Can Be Myself", "desc": "With you, I’m full-on Jake Peralta—quoting *Die Hard*, planning fake heists, no filter. You’re my Amy, laughing at my dumb jokes and not judging my nacho obsession. It’s like you’ve built a precinct where I can just be me, no badge required. You love my weird, and that’s why you’re my forever perp, my sunflower. Every moment with you feels like a Halloween Heist win, and I’m so lucky to have you as my partner in this wild, love-filled adventure."},
    {"name": "Family and Friend", "desc": "You fit into my crazy family like you’re part of the Nine-Nine, my Amy. You charm my mom, tolerate my dad’s puns, and banter with my friends like you’re Rosa. It’s like you’re planning heists with the squad at every dinner. Your love for my people makes my heart do a ‘Noice!’ and I’m so grateful you’re in our crew, my sunflower. You make every gathering feel like a precinct party, and I love you for it."},
    {"name": "You Banish My Worries", "desc": "When life’s a stakeout gone wrong, you swoop in like John McClane, my Amy. Your hugs melt my stress faster than a precinct microwave burrito. One smile from you, and it’s ‘Yippee-ki-yay,’ worries gone. You’re my safe house, my sunflower, where I can hide from the world. No case is too tough with you by my side, and I’m so lucky to have you as my partner, making every day feel like a *Die Hard* victory."},
    {"name": "My Heart Smiles", "desc": "Your laugh, your touch—they make my heart dance like I just solved the Pontiac Bandit case, my Amy. It’s a ‘Noice!’ explosion in my chest. You light up my world like the Nine-Nine on a good day, and every moment with you is a victory lap. My heart’s grinning because of you, my sunflower, and I’m never letting that feeling go. You’re my favorite perp, stealing my heart every day in this epic love heist."},
    {"name": "You Know Me Best", "desc": "You get me like you’ve got a detective’s notebook labeled ‘Jake Peralta 101,’ my Amy. You know when I’m hiding nerves with *Die Hard* quotes or need a hug. It’s like you’ve cracked my soul’s code, and you love every goofy bit. You’re my partner in this life heist, my sunflower, and I’m so glad you see me—really see me. No case is too big with you by my side, and I love you for it."},
    {"name": "You Support My Goals", "desc": "You’re my hype squad, like Gina cheering a dance-off, but way hotter, my Amy. Whether I’m chasing a promotion or perfecting my nacho game, you’re there with a ‘Noice!’ You believe in me like I’m John McClane taking down Hans Gruber. You push me to climb my own Nakatomi Plaza, my sunflower, and that makes me want to be better every day. I’m so lucky to have you in my corner for this love-filled heist."},
    {"name": "Your Smooth Skin", "desc": "Your skin’s softer than the precinct lounge blanket I totally didn’t steal, my Amy. Touching you feels like a hug after a long shift chasing perps. It’s like your warmth radiates through every brush of your hand, my sunflower. You’re my *Die Hard* happy ending, and I’d spend every day holding you close, soaking in that softness. No case could ever top the feeling of being near you, and I’m so lucky you’re mine."},
    {"name": "You Make Me Smile", "desc": "Your smile is my ‘Cool cool cool cool cool,’ my Amy. Even when I’m drowning in precinct paperwork, one look at you and I’m grinning like I pulled off the Halloween Heist. You light up my world like a *Die Hard* explosion, my sunflower. I’d do anything to keep that smile shining, because it’s my favorite thing in the universe. You’re my partner in crime, and every grin you spark makes this heist called life so much better."},
    {"name": "You Teach Me Love", "desc": "I thought love was like a *Die Hard* sequel—fun but messy—until you, my Amy. You showed me it’s a perfect heist: planned, heartfelt, worth it. Every text, every late-night talk, you teach me to love deeper. You’re my John McClane, saving my heart, my sunflower. I’m forever grateful for your lessons in love, making every day feel like a Nine-Nine win. I’m all in for this heist with you, babe, no doubt, no doubt."},
    {"name": "I Miss You Always", "desc": "Even when you’re just across the room, I miss you like I’m on a stakeout without my partner, my Amy. You’re my go-to for every adventure, and my heart’s off without you. It’s like I’m John McClane crawling through Nakatomi Plaza vents, searching for you. Your laugh, your presence—I crave it all, my sunflower. You’re my home, and I’m counting seconds until I’m back with you, plotting our next love heist."},
    {"name": "You Heal My Hurts", "desc": "When I’m down, you’re better than precinct coffee, my Amy, picking me up with your hugs and words. You’re my John McClane, taking down my pain with a ‘Yippee-ki-yay’ smile. Every hurt feels smaller with you, my sunflower, turning bad days into wins. I don’t know how you do it, but you’re my hero, healing my heart with every touch. I’m so lucky to have you in this crazy heist called life."},
    {"name": "Always There for Me", "desc": "You’re my rock, my Amy, like Captain Holt backing me on a tough case. No matter what—bad day, crazy heist, or me being a goof—you’re there with a ‘Noice!’ You’re steadier than the Nine-Nine precinct, my sunflower, and I know I can count on you. You make me feel safe, like I’ve got my own John McClane watching over me. I love you for always being my partner in this love-filled adventure."},
    {"name": "Your Umbrella in the Rain", "desc": "When life’s a Brooklyn storm, you’re my umbrella, my Amy, keeping me warm and dry. You organize my chaos like Amy Santiago with a perfect plan. Your care turns rainy days into *Die Hard* victories, my sunflower. I’d run through any storm to be by your side, knowing you’ve got me covered. You’re my hero, making every moment feel like a win, and I’m so lucky to have you in this heist."},
    {"name": "You Encourage Me", "desc": "You push me like Terry hyping me to lift weights, but with more heart, my Amy. You believe I can crack any case, making me want to climb Nakatomi Plaza for you. Your ‘Cool cool cool’ grin fuels me, my sunflower, whether it’s work or a dumb joke. Your encouragement is my superpower, and I’m so lucky to have you as my partner in this heist, cheering me on to be better every day."},
    {"name": "Your Truthfulness", "desc": "Your honesty’s like a detective’s report, my Amy, cutting through my doubts like John McClane taking down bad guys. You tell it straight, but with love, like briefing me on our biggest case—us. Your truth builds my trust, my sunflower, and I’d follow you into any heist knowing you’ve got my back. You’re my partner in crime, and I love how your honesty makes our love stronger every day."},
    {"name": "You Lift Me Up", "desc": "When I’m down, you’re there, my Amy, like Jake Peralta after a failed Halloween Heist. Your hugs and words are my ‘Noice!’ turning bad days around. You make me feel like I can take on Hans Gruber, my sunflower. You lift my spirits higher than Nakatomi Plaza’s rooftop, and I’m so grateful you’re my partner in this love heist, making every moment brighter and better with your love."},
    {"name": "You Give Me Strength", "desc": "You’re my secret weapon, my Amy, giving me strength like John McClane with a machine gun. When I doubt myself, you remind me I can pull off any heist. Your belief is like a precinct pep talk from Holt, but hotter, my sunflower. You make me unstoppable, and I’d take on any challenge for your proud smile. I’m so lucky to have you as my partner in this crazy, love-filled adventure."},
    {"name": "Your Hard Work", "desc": "You work harder than Amy Santiago with her binders, my Amy, inspiring me with your drive. Whether it’s crushing work or planning our dates like a Nine-Nine op, you give it your all. It’s like watching John McClane save the day—total hero vibes, my sunflower. I’m so proud to be with someone who dives in heart-first, and I love you for making every moment feel like a *Die Hard* win."},
    {"name": "You Love My Family", "desc": "You love my crazy family like they’re the Nine-Nine, my Amy, charming my mom and surviving my dad’s puns. You’re like Rosa bantering at a squad dinner, my sunflower. Your love for them makes my heart go ‘Noice!’ and I’m so lucky you’re in our crew. You make every family moment a precinct party, and I love how you fit right in, stealing my heart like it’s a Halloween Heist."},
    {"name": "You Spoil Me When Sick", "desc": "When I’m sick, you go full Amy Santiago, organizing my recovery like a precinct case, my Amy. You bring soup, fluff pillows, and make me feel like the luckiest detective. It’s like you’re my John McClane, fighting my sniffles with love, my sunflower. Your care wraps me up like a cozy blanket, and I’d fake a cold just for more of your attention. You’re my hero in this love heist."},
    {"name": "Our Special Time", "desc": "You carve out time for us like it’s the top case on your desk, my Amy. Binge-watching *Die Hard* or just talking nonsense, it’s our Halloween Heist—perfect and ours. Your effort makes me feel like your star, my sunflower. I’d do anything to keep stealing those moments with you, because they’re my favorite part of every day. You’re my partner in this love-filled heist, and I’m so lucky."},
    {"name": "Your Determination", "desc": "You’ve got fire like John McClane charging into danger, my Amy. Your determination to make us work, chase dreams, tackle challenges—it’s epic. You’re Amy Santiago with binders, planning perfection, my sunflower. I love watching you go all-in, because it shows me how lucky I am to be on this heist with someone so fierce. You make every day a *Die Hard* win, and I’m so proud to be your partner."},
    {"name": "You Reframe Negatives", "desc": "When life’s a mess, you turn it into a win, like Jake Peralta making a stakeout a karaoke party, my Amy. You find the bright side, making bad days feel like *Die Hard* comebacks. Your optimism’s like a precinct coffee run—small but game-changing, my sunflower. You teach me to see the good, and with you, every case has a happy ending. I’m so lucky to have you as my partner in this love heist."},
    {"name": "Your Laugh Sparks Mine", "desc": "Your laugh’s my favorite sound, my Amy, like a ‘Cool cool cool’ that sets my heart ablaze. It’s contagious, like Gina’s sass in the Nine-Nine. When you laugh, I’m right there with you, like we’re in a comedy heist, my sunflower. Your joy lights my life brighter than a *Die Hard* explosion, and I’d do anything to keep hearing that laugh forever. You’re my partner, making every day a blast."},
    {"name": "We Understand Each Other", "desc": "We’re Jake and Amy in the Nine-Nine, my sunflower—different but in sync. You get my *Die Hard* obsession, I get your love for order. It’s like we’re partners on the ultimate case, solving life together, my Amy. Your understanding makes me feel seen, like two pieces of a Nakatomi Plaza puzzle. I love how we fit, and I’m so lucky to have you as my teammate in this wild, love-filled heist."},
    {"name": "Your Arms Are Home", "desc": "Your hugs are home, my Amy, like the precinct after a long shift. They’re warmer than a *Die Hard* victory, wrapping me in love. When I’m in your arms, I’ve cracked the case of a lifetime, my sunflower. You’re my safe house, where I can just be. I’d stay there forever, no heist needed, because you’re my favorite place in the world, and I’m so lucky to call you mine."},
    {"name": "Your Inner Strength", "desc": "Your quiet strength is like Amy Santiago running a precinct, my Amy. You face challenges with fire, like John McClane taking on bad guys, and I’m in awe. Your resilience calms my chaos, my sunflower, making me proud every day. You’re my hero, stronger than any detective, and I love how you carry that strength with heart. I’m so lucky to have you as my partner in this love heist."},
    {"name": "You Keep Promises", "desc": "Your word’s gold, my Amy, like a Nine-Nine logbook entry. You’re there when you say you will, like John McClane coming through in a pinch. Your reliability builds my trust, my sunflower, and I know we’re in this heist forever. You keep every promise, making you my favorite person in the precinct. I’m so lucky to have you as my partner, stealing my heart with every kept vow."},
    {"name": "You Teach Me Tech", "desc": "You’re like Charles teaching me artisanal cheeses, but cooler, my Amy. You explain tech with patience, like I could hack Nakatomi Plaza’s security. Your smarts are sexy, my sunflower, and you make me feel less like a goof. Every lesson’s a fun heist with you, and I love how you guide me through. I’m so lucky to have you as my tech guru and partner in this love-filled adventure."},
    {"name": "Your Comforting Touch", "desc": "Your touch is like precinct coffee on a cold Brooklyn morning, my Amy. A hand-hold or hug chases my stress away, like you’re my *Die Hard* hero. You make me feel safe, my sunflower, and I’d give anything to feel your touch every day. It’s better than any heist win, and I’m so lucky you’re my partner, making every moment warmer and sweeter with your love."},
    {"name": "You Apologize First", "desc": "Your big heart always says sorry first, my Amy, like Amy Santiago owning a case mix-up. Your humility makes me love you more, my sunflower, keeping our peace like a *Die Hard* bomb defused with kindness. You care about us, and that’s everything. I’m so lucky to have you as my partner in this love heist, making every moment smoother with your grace and love."},
    {"name": "You Roll with It", "desc": "When plans go sideways, you’re cooler than Jake Peralta in a Halloween Heist, my Amy. You turn chaos into fun, like a *Die Hard* comeback, my sunflower. Your calm vibe makes every mess manageable, and I love how you handle life’s curveballs. You make me feel like we can tackle anything together, no matter how wild the case. I’m so lucky to have you as my partner in this love-filled adventure."},
    {"name": "You Inspire Me", "desc": "You light a fire in me, my Amy, like Gina hyping the Nine-Nine for a dance-off. Your passion makes me want to chase your heart like it’s the ultimate heist. You inspire me to dream big, my sunflower, with ‘Cool cool cool’ confidence. You’re my John McClane, pushing me to be a hero, and I’m so grateful for your spark in this love heist we’re pulling off together."},
    {"name": "I Can Talk to You", "desc": "Talking to you, my sunflower, is better than Nine-Nine banter. I can spill about *Die Hard* theories or dumb fears, and you listen like it’s the biggest case, my Amy. You’re my best friend, making every chat a heist we’re planning together. I love how easy it is to share my world with you, no matter how goofy. I’m so lucky to have you as my partner in this love-filled adventure."},
    {"name": "Your Love Shines", "desc": "Your love glows brighter than Nine-Nine Christmas lights, my Amy. You shine through my darkest days like a *Die Hard* explosion, my sunflower. Your care is a perfectly planned heist, stealing my heart daily. You make every moment sparkle, and I’m so lucky to bask in your light as your partner in this crazy, love-filled adventure. You’re my favorite perp, and I’m all in for you."},
    {"name": "You Picked Me", "desc": "You chose me, my sunflower, and that’s the greatest heist ever. I’m just a goofy detective quoting *Die Hard*, but you saw something worth loving, my Amy. It’s like I’m Jake Peralta, picked from the Nine-Nine lineup. Your choice makes me feel like I’ve won every Halloween Heist. I’ll spend forever proving I’m worthy of you, my partner in this love-filled heist, no doubt, no doubt."},
    {"name": "Your Smiling Eyes", "desc": "Your eyes sparkle when you smile, my Amy, like the Nine-Nine precinct on a good day. They’re brighter than a *Die Hard* explosion, hitting my heart with a ‘Noice!’ You see all my goofy Jake bits and love them, my sunflower. Those eyes are my favorite view, and I’d stare into them forever, no case too tough. I’m so lucky to have you as my partner in this love heist."},
    {"name": "You Let Me Choose", "desc": "You let me pick the movie, my Amy, even when it’s *Die Hard* again. It’s like you’re saying, ‘Cool cool cool, Jake, you got this.’ Your trust makes me feel like the lead detective, my sunflower. I love how you give me the reins, knowing we’re in this heist together. You make me feel heard, and I’m so lucky to have you as my partner in this love-filled adventure."},
    {"name": "Sweeter Than Dessert", "desc": "You’re sweeter than precinct donuts, my Amy, and that’s big. Your kindness outshines any dessert, like a *Die Hard*-level treat for my heart, my sunflower. Every moment with you is a sugar rush, making me grin like I pulled off the ultimate heist. You’re my favorite flavor, and I’m so lucky to savor you every day. You make this love heist the sweetest adventure, and I’m all in for you, babe."},
    {"name": "You Love Me at My Worst", "desc": "Even when I’m a mess, like Jake after a failed stakeout, you love me, my Amy. You hold me when I’m grumpy or hiding behind *Die Hard* quotes. Your love’s like a Terry hug, warm and unbreakable, my sunflower. You make me feel worthy, even on bad days, and I’m so grateful you’re my partner in this messy, love-filled heist we call life. You’re my hero, always."},
    {"name": "You Treat All Well", "desc": "Your kindness is like Gina’s sass but all heart, my Amy. You treat everyone—strangers, friends, even grumpy cops—with warmth, like Amy Santiago organizing a perfect case. It’s inspiring, my sunflower, how you make the world better. Your goodness shines brighter than a *Die Hard* explosion, and I’m proud to be with you, my partner in this love heist, spreading light everywhere you go."},
    {"name": "We’re Different Yet Same", "desc": "We’re Jake and Amy in the Nine-Nine, my sunflower—different but perfect together. I’m *Die Hard* chaos, you’re organized magic, yet we fit like a heist plan. You love my goofy, I adore your planner heart, my Amy. We’re two sides of the same badge, and I love how we balance each other in this wild, love-filled adventure. I’m so lucky you’re my partner."},
    {"name": "You Strive to Grow", "desc": "You’re always growing, my Amy, like Amy Santiago studying for the sergeant’s exam. Your drive to be better is hotter than a *Die Hard* car chase, my sunflower. You inspire me to keep up, like we’re training for the ultimate heist. Your effort makes me proud, and I’m so lucky to be with someone who reaches for the stars. You’re my hero in this love adventure."},
    {"name": "You Love My People", "desc": "You embrace my friends and family like they’re the Nine-Nine, my Amy. You laugh with Charles, banter with Rosa, charm Holt. It’s like you’re part of the squad, my sunflower, making hangouts a precinct party. Your love for my people makes my heart go ‘Noice!’ I’m so grateful you’re in my crew for this lifelong heist, stealing my heart every day."},
    {"name": "Your Thoughtfulness", "desc": "Your little gestures are like Jake planning a surprise for Amy, my Amy—thoughtful and perfect. A sweet note or remembering my *Die Hard* quotes makes me feel so loved, my sunflower. Your care’s like a precinct coffee run, small but huge. You think of me in ways I don’t expect, and every moment with you is a gift I’ll never stop unwrapping in this love heist."},
    {"name": "Your Protective Nature", "desc": "You’ve got my back like John McClane watching Holly, my Amy. Your protective side makes me feel safe, like I’m in the best precinct, my sunflower. You’d fight any bad day for me, and that fierce love is everything. You’re my *Die Hard* hero, guarding my heart, and I’m so lucky to have you as my partner in this love heist, always in my corner."},
    {"name": "You Gave Me You", "desc": "You gave me your heart, my Amy, the greatest heist I’ve pulled. You’re my prize, like stealing Nakatomi Plaza’s jewels, my sunflower. Your love makes every day a *Die Hard* win. I’m still pinching myself that you chose me, and I’ll spend forever proving I’m worthy of you, my partner in this crazy, love-filled adventure. You’re my everything, no doubt, no doubt."},
    {"name": "You Make Me Better", "desc": "You make me want to be a better Jake, my Amy, like Amy Santiago pushing me to file reports. Your love inspires me to chase dreams and be your hero, my sunflower. You’re my *Die Hard* script, guiding me to my best self. I’m so grateful for you, because with you, I’m aiming for a ‘Noice!’ life. You’re my partner in this love heist, always."},
    {"name": "You Pull Me Close", "desc": "When you hold me at night, my Amy, it’s a heist hug stealing my heart. Your touch is home, safer than the Nine-Nine precinct, my sunflower. It’s better than any *Die Hard* moment, because it’s us. I love how you keep me close, like I’m your favorite perp. I’d stay in your arms forever, plotting our next heist, just you and me, babe."},
    {"name": "You Make Me Special", "desc": "You make me feel like the star of our *Die Hard* movie, my Amy. Your love says, ‘You’re my Jake, one of a kind.’ It’s like winning the Halloween Heist every time you smile, my sunflower. You turn ordinary moments into epic adventures, and I’m so lucky to be your leading man. I’ll keep chasing that ‘Noice!’ feeling with you, my partner in this love heist."},
    {"name": "Your Calming Voice", "desc": "Your voice is my favorite, my sunflower, like a precinct radio saying it’s all okay. It calms my chaos like Amy Santiago organizing a case, my Amy. Whether you’re whispering ‘I love you’ or chatting about nothing, it’s better than any *Die Hard* line. Your voice is my safe place, and I could listen forever, no heist too big. I’m so lucky you’re my partner."},
    {"name": "My Missing Piece", "desc": "Meeting you, my Amy, was like finding my heart’s missing piece, solving the ultimate Nine-Nine case. You complete me, my sunflower, like John McClane and Holly in *Die Hard*’s ending. Without you, I’d be lost in Nakatomi Plaza, but with you, I’m whole. I’ll love you forever for that, my partner in this love heist, making every day a win with you by my side."},

    # Peter Kavinsky-inspired qualities (51-100)
    {"name": "Your Sweet Smile", "desc": "Your smile, Covey, is like the first letter I wrote you—game-changing and heart-stopping. It lights up my world better than a perfect lacrosse goal. When you grin, it’s like we’re back in that diner, sharing fries and laughs. You make every moment feel like a rom-com scene, and I’m the luckiest guy to be your leading man. I’d write a thousand letters just to see that smile, babe, because it’s my favorite thing in the world."},
    {"name": "You’re My Adventure", "desc": "You’re my ultimate adventure, Covey, like a road trip with no map, just us. Every date—whether it’s a movie night or sneaking into a hot tub—feels like a page from our own love story. Your spark makes my heart race faster than a lacrosse game, babe. I love how you dive into life with me, making every moment a thrill. You’re my partner in crime, and I’m so lucky to be on this wild ride with you."},
    {"name": "Your Caring Heart", "desc": "Your heart’s bigger than my lacrosse team’s spirit, Covey. You care for everyone—your sisters, your friends, even me when I’m being a goof. It’s like you’re writing love letters to the world with every kind act. You make me want to be a better guy, babe, just to keep up with you. Your love is my home, and I’m so lucky to have you as my girl, stealing my heart every day."},
    {"name": "You Love My Chaos", "desc": "You roll with my chaos, Covey, like when I blast music too loud or plan a spontaneous date. You’re my Lara Jean, smiling through my dumb ideas and making them better. It’s like we’re in a rom-com, and you’re the one who makes every scene perfect. I love how you love my mess, babe, and I’m so lucky to have you as my partner, turning every day into our own love story."},
    {"name": "Your Thoughtful Notes", "desc": "Your little notes, Covey, are like the letters I fell for, full of heart and surprises. Whether it’s a sticky note or a text, you make me feel like the luckiest guy. It’s like you’re planning a secret date just for us, babe. Your thoughtfulness is my favorite play, better than any lacrosse move. I’m so grateful for you, my girl, making every day sweeter with your words and love."},
    {"name": "You Make Me Brave", "desc": "You make me braver than I am on the lacrosse field, Covey. Your belief in me is like a love letter cheering me on, pushing me to take risks. When I’m with you, I feel like I can face anything, babe, like we’re in our own rom-com, conquering the world. I love how you make me bold, and I’m so lucky to have you as my girl, my partner in every crazy adventure."},
    {"name": "Your Playful Side", "desc": "Your playful side, Covey, is like sneaking into a hot tub with you—fun and full of surprises. You tease me about my bad dance moves, but it makes my heart race like a lacrosse game. You bring out my goofy side, babe, and every laugh we share feels like a perfect date. I love how you keep things light, my girl, and I’m so lucky to be your partner in this love story."},
    {"name": "You Get My Humor", "desc": "You laugh at my dumb jokes, Covey, like they’re the best part of our movie night. It’s like you’re my Lara Jean, getting my goofy side without missing a beat. Your giggles make my heart do a victory lap, babe, better than any lacrosse win. I love how we vibe, sharing laughs like love letters. I’m so lucky to have you as my girl, making every day a rom-com I never want to end."},
    {"name": "Your Gentle Touch", "desc": "Your touch, Covey, is softer than the scarf you wear on our fall walks. A hand-hold or a quick hug feels like a love letter I can feel, babe. It’s like you’re wrapping me in warmth, making every moment a cozy date. I love how your touch says you’re mine, my girl, and I’m so lucky to have you as my partner, stealing my heart with every gentle brush."},
    {"name": "You’re My Home", "desc": "You’re my home, Covey, like the cozy couch we share during movie nights. No matter where I am, your smile brings me back to you, babe. It’s like you’re my Lara Jean, making every moment feel safe and right. I love how you ground me, my girl, turning every day into a rom-com scene I never want to leave. I’m so lucky to have you as my partner in this love story."},
    {"name": "Your Bright Eyes", "desc": "Your eyes sparkle like the lights at our school dance, Covey, stealing my heart every time. They’re full of dreams, like the letters you write, babe. When you look at me, I feel like the luckiest guy, ready to score a lacrosse goal for you. I love how your eyes see me, my girl, and I’m so grateful to have you as my partner, making every glance a moment in our love story."},
    {"name": "You Make Me Feel Loved", "desc": "You make me feel loved, Covey, like I’m the only guy in your love letters. Your sweet words and hugs are better than any lacrosse win, babe. It’s like you’re planning a perfect date just for my heart. I love how you show me I’m yours, my girl, and I’m so lucky to have you as my partner, making every day feel like a rom-com I’ll never get tired of."},
    {"name": "Your Fierce Loyalty", "desc": "You’re loyal like you’re guarding my heart, Covey, fiercer than me on the lacrosse field. You’re always there, like Lara Jean keeping her promises. Your love makes me feel safe, babe, like we’re in this forever. I love how you stick by me, my girl, through every crazy moment. I’m so lucky to have you as my partner, writing our love story with every loyal heartbeat you give me."},
    {"name": "You Inspire My Dreams", "desc": "You make my dreams bigger, Covey, like you’re writing them in one of your letters. Your passion pushes me to aim high, babe, like I’m chasing a lacrosse scholarship just for you. You believe in me, my girl, making every goal feel possible. I love how you inspire me to be better, and I’m so lucky to have you as my partner in this rom-com life we’re living together."},
    {"name": "Your Kind Words", "desc": "Your words, Covey, are like love letters that light up my day. Whether it’s a sweet text or a quiet ‘I love you,’ you make my heart race faster than a lacrosse play, babe. Your kindness is my favorite song, my girl, playing on repeat. I love how you speak love into my life, and I’m so lucky to have you as my partner, writing our story with every word."},
    {"name": "You’re My Best Friend", "desc": "You’re my best friend, Covey, like Lara Jean and me sharing secrets at a diner. We talk about everything—school, dreams, or just dumb stuff—and it’s perfect, babe. Your heart’s my safe place, my girl, making every chat feel like a date. I love how we connect, and I’m so lucky to have you as my partner, living this rom-com life with you by my side forever."},
    {"name": "Your Endless Support", "desc": "You cheer me on like I’m scoring the winning lacrosse goal, Covey. Your support makes me feel unstoppable, babe, like I’m the hero in your letters. Whether it’s school or life, you’re my biggest fan, my girl. I love how you believe in me, pushing me to chase my dreams. I’m so lucky to have you as my partner, making every moment a win in our love story."},
    {"name": "You Light Up My World", "desc": "You light up my life, Covey, like the fairy lights on our movie night setup. Your smile makes every day feel like a perfect date, babe. You’re my Lara Jean, turning ordinary moments into rom-com magic. I love how you make everything brighter, my girl, and I’m so lucky to have you as my partner, stealing my heart with every glow you bring to our love story."},
    {"name": "Your Cute Laugh", "desc": "Your laugh, Covey, is like the best song blasting in my car, making my heart skip. It’s cuter than you reading my letters, babe, and it gets me every time. You laugh at my dumb jokes, my girl, and it feels like we’re in our own rom-com. I love how your giggles light up my day, and I’m so lucky to have you as my partner in this love-filled adventure."},
    {"name": "You’re My Safe Place", "desc": "You’re my safe place, Covey, like curling up with you on a rainy day. Your hugs make me feel like nothing can touch me, babe, better than any lacrosse win. You’re my Lara Jean, grounding me when life’s wild, my girl. I love how you make me feel at home, and I’m so lucky to have you as my partner, building our love story with every cozy moment we share."},
    {"name": "Your Big Dreams", "desc": "Your dreams are huge, Covey, like the stories you write in your letters. You chase them with heart, babe, inspiring me to aim high like I’m on the lacrosse field. You make me believe anything’s possible, my girl, like we’re in a rom-com with no limits. I love how you dream big, and I’m so lucky to have you as my partner, chasing our future together in this love story."},
    {"name": "You Make Time for Us", "desc": "You always make time for us, Covey, like planning a perfect date night. Whether it’s a movie or just talking, you make me feel like your top priority, babe. It’s like you’re writing me into your life’s love letter, my girl. I love how you carve out these moments, and I’m so lucky to have you as my partner, making every second together a scene in our rom-com."},
    {"name": "Your Honest Heart", "desc": "Your honesty, Covey, is like the truth in your love letters—raw and beautiful. You tell me how you feel, babe, and it makes me trust you more every day. You’re my Lara Jean, keeping it real, my girl. I love how you share your heart, making our love stronger. I’m so lucky to have you as my partner, writing our story with every honest word you give me."},
    {"name": "You See the Real Me", "desc": "You see me, Covey, past the lacrosse guy to the real Peter. You get my goofy side, my dreams, even my dumb moments, babe. It’s like you’re reading my own love letter back to me, my girl. I love how you know me inside out, and I’m so lucky to have you as my partner, making every day feel like a rom-com scene where I’m your leading man."},
    {"name": "Your Warm Presence", "desc": "Your presence, Covey, is warmer than our favorite diner booth. Just being near you feels like a perfect date, babe, better than any lacrosse game. You’re my Lara Jean, making every moment cozy and right, my girl. I love how you make me feel at home, and I’m so lucky to have you as my partner, stealing my heart with every second we spend together in this love story."},
    {"name": "You Make Me Happy", "desc": "You make me happier than scoring a lacrosse goal, Covey. Your smile, your texts—they’re like love letters that light up my day, babe. You’re my Lara Jean, turning every moment into a rom-com win, my girl. I love how you bring joy to my life, and I’m so lucky to have you as my partner, making every day a happy chapter in our love story together."},
    {"name": "Your Creative Mind", "desc": "Your mind’s a spark, Covey, like the stories you weave in your letters. You come up with date ideas or cute surprises that make my heart race, babe. You’re my Lara Jean, creating magic like it’s a rom-com script, my girl. I love how you think outside the box, and I’m so lucky to have you as my partner, dreaming up our next adventure in this love story."},
    {"name": "You’re My Teammate", "desc": "You’re my teammate, Covey, like we’re on the lacrosse field together. You’ve got my back, cheering me through life’s plays, babe. You’re my Lara Jean, making every challenge feel like a team win, my girl. I love how we tackle everything together, and I’m so lucky to have you as my partner, running the best plays in our rom-com love story, side by side forever."},
    {"name": "Your Gentle Heart", "desc": "Your heart’s gentle, Covey, like the way you write your letters. You care so deeply, babe, making everyone around you feel special. You’re my Lara Jean, spreading warmth like a cozy movie night, my girl. I love how you love with such softness, and I’m so lucky to have you as my partner, wrapping me in your heart’s glow in this rom-com we’re living together."},
    {"name": "You Make Every Day Better", "desc": "Every day’s better with you, Covey, like a perfect date night every morning. Your smile turns my world into a rom-com, babe, brighter than any lacrosse win. You’re my Lara Jean, making even boring days feel like an adventure, my girl. I love how you light up my life, and I’m so lucky to have you as my partner, writing our love story with every moment we share."},
    {"name": "Your Strong Spirit", "desc": "Your spirit’s stronger than my best lacrosse play, Covey. You face life with grit, like Lara Jean standing up for what matters, babe. You inspire me to be tougher, my girl, pushing through any challenge. I love how you shine with strength, and I’m so lucky to have you as my partner, making our rom-com love story unstoppable with your fierce heart by my side."},
    {"name": "You Keep Me Grounded", "desc": "You keep me steady, Covey, like an anchor on a wild lacrosse day. When I’m all over the place, your calm brings me back, babe. You’re my Lara Jean, grounding our love story with your heart, my girl. I love how you balance me, and I’m so lucky to have you as my partner, keeping our rom-com on track with every steady moment we share together."},
    {"name": "Your Love for Family", "desc": "You love your family like I love my team, Covey, and it’s the sweetest thing. You’re there for your sisters, like Lara Jean planning a perfect day, babe. Your heart makes me proud, my girl, showing me what love looks like. I love how you care so deeply, and I’m so lucky to have you as my partner, building our own family in this rom-com love story."},
    {"name": "You’re My Dream Girl", "desc": "You’re my dream girl, Covey, like I wrote you into my own love letter. Every moment with you feels like a rom-com I never want to end, babe. You’re my Lara Jean, making my heart race faster than a lacrosse game, my girl. I love how you make my dreams real, and I’m so lucky to have you as my partner, living this love story together forever."},
    {"name": "Your Sweet Surprises", "desc": "Your surprises, Covey, are like finding a new love letter in my locker. A cute text or a random date idea makes my day, babe. You’re my Lara Jean, planning little moments that steal my heart, my girl. I love how you keep me guessing, and I’m so lucky to have you as my partner, adding sparkle to our rom-com with every sweet surprise you bring."},
    {"name": "You Make Me Feel Seen", "desc": "You see me, Covey, like you’re reading my heart’s love letter. You get my dreams, my quirks, even my lacrosse obsession, babe. You’re my Lara Jean, making me feel like the only guy in the room, my girl. I love how you know me so well, and I’m so lucky to have you as my partner, writing our rom-com story with every moment you make me feel special."},
    {"name": "Your Endless Patience", "desc": "Your patience, Covey, is like Lara Jean waiting for the perfect moment to share her letters. You put up with my chaos, babe, and still smile. You’re my girl, making me feel okay being me, even when I’m a mess. I love how you give me space to grow, and I’m so lucky to have you as my partner in this rom-com, loving me through every wild moment."},
    {"name": "You’re My Forever", "desc": "You’re my forever, Covey, like the last line in a love letter I’ll never stop writing. Every moment with you feels like a rom-com ending, babe, better than any lacrosse win. You’re my Lara Jean, my girl, making every day a promise of us. I love how you’re my future, and I’m so lucky to have you as my partner, building our love story for a lifetime."},
    {"name": "Your Bright Spirit", "desc": "Your spirit shines, Covey, like the sun on our lake dates. You bring energy to every moment, babe, making life a rom-com adventure. You’re my Lara Jean, lighting up my world, my girl. I love how your spark makes everything better, and I’m so lucky to have you as my partner, chasing every bright moment together in this love story we’re writing day by day."},
    {"name": "You Make Me Whole", "desc": "You make me whole, Covey, like the missing piece in my love letter. Without you, I’d be incomplete, babe, but with you, I’m the luckiest guy. You’re my Lara Jean, filling my heart with every smile, my girl. I love how you complete me, and I’m so grateful to have you as my partner, making our rom-com love story the best adventure I’ll ever have."},
    {"name": "Your Loving Words", "desc": "Your words, Covey, are like love letters I want to read forever. Every ‘I love you’ or sweet text makes my heart skip, babe, better than a lacrosse goal. You’re my Lara Jean, speaking love into my life, my girl. I love how your words wrap me in warmth, and I’m so lucky to have you as my partner, writing our rom-com with every beautiful thing you say."},
    {"name": "You’re My Everything", "desc": "You’re my everything, Covey, like the heart of every letter I’d write for you. You make every day a rom-com win, babe, better than any game or movie. You’re my Lara Jean, my girl, stealing my heart with every moment. I love how you fill my world, and I’m so lucky to have you as my partner, living this love story together, forever and always, no doubt."}
]
        font_btn = QFont("Georgia", 12)
        font_btn.setItalic(True)
        for idx, quality in enumerate(self.qualities):
            button = QPushButton(quality["name"])
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0d0d0d;
                    color: #4fc3f7;
                    border: 2px solid #4682b4;
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #4682b4;
                    color: #0d0d0d;
                }
            """)
            button.setFont(font_btn)
            button.clicked.connect(lambda checked, q=quality: self.show_quality_dialog(q))
            row = idx // 10
            col = idx % 10
            grid_layout.addWidget(button, row, col)

        scroll_widget.setLayout(grid_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

    def show_quality_dialog(self, quality):
        dialog = QDialog(self)
        dialog.setWindowTitle(quality["name"])
        dialog.setStyleSheet("background-color: #0d0d0d;")
        dialog.setFixedSize(300, 200)

        layout = QVBoxLayout(dialog)
        font = QFont("Georgia", 14)
        font.setItalic(True)

        label = QLabel(quality["desc"])
        label.setStyleSheet("color: #4fc3f7; font-size: 14px;")
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(255, 255, 255, 180))
        glow.setOffset(0, 0)
        label.setGraphicsEffect(glow)
        layout.addWidget(label)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("background-color: #4682b4; color: #0d0d0d; font-size: 12px; font-weight: bold;")
        close_button.setFont(font)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)

        dialog.exec()

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

        self.heart_animation = HeartAnimationWidget(self)
        self.heart_animation.setGeometry(0, 0, 800, 580)
        self.heart_animation.lower()

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
        self.tabs.addTab(PlaylistTab(self.player, self.playlist, PlaylistWidget(self.player, self.playlist)), "Playlist")
        self.tabs.addTab(QualitiesTab(), "Qualities")
        main_layout.addWidget(self.tabs)

        self.playlist_dock = QDockWidget()
        self.playlist_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.playlist_dock.setTitleBarWidget(QWidget())
        self.playlist_dock.setWidget(PlaylistWidget(self.player, self.playlist))
        self.addDockWidget(Qt.RightDockWidgetArea, self.playlist_dock)

        self.player.errorOccurred.connect(self.handle_media_error)

    def resizeEvent(self, event):
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
        player.stop()
        sys.exit(0)

