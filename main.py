import sys
import os
import time
import json
import mss
import keyboard
import numpy as np
import cv2
import subprocess
import urllib.request
import webbrowser

CURRENT_VERSION = "1.0"

from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMessageBox, 
                             QMainWindow, QLabel, QFileDialog, QToolBar, QWidget, 
                             QVBoxLayout, QHBoxLayout, QScrollArea, QDialog, 
                             QComboBox, QRadioButton, QButtonGroup, QFormLayout, 
                             QPushButton, QLineEdit, QCheckBox)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QImage, QPainter, QPen, QColor, QScreen, QGuiApplication
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QRect, QPoint, QObject, QTimer

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def cv2_to_qimage(cv_img):
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    height, width, channel = img_rgb.shape
    bytes_per_line = channel * width
    q_img = QImage(img_rgb.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
    return q_img 

class HotkeyThread(QThread):
    trigger_capture = pyqtSignal(bool)
    cancel_capture = pyqtSignal()
    open_folder = pyqtSignal()

    def __init__(self, normal, scroll, folder, cancel='esc'):
        super().__init__()
        self.normal = normal
        self.scroll = scroll
        self.folder = folder
        self.cancel = cancel

    def run(self):
        try:
            keyboard.add_hotkey(self.normal, lambda: self.trigger_capture.emit(False))
            keyboard.add_hotkey(self.scroll, lambda: self.trigger_capture.emit(True))
            keyboard.add_hotkey(self.folder, lambda: self.open_folder.emit())
            keyboard.add_hotkey(self.cancel, lambda: self.cancel_capture.emit())
            keyboard.wait() 
        except Exception as e:
            print(f"Hotkey Error: {e}")

    def update_hotkeys(self, normal, scroll, folder, cancel='esc'):
        try:
            keyboard.unhook_all_hotkeys()
            self.normal = normal
            self.scroll = scroll
            self.folder = folder
            self.cancel = cancel
            keyboard.add_hotkey(self.normal, lambda: self.trigger_capture.emit(False))
            keyboard.add_hotkey(self.scroll, lambda: self.trigger_capture.emit(True))
            keyboard.add_hotkey(self.folder, lambda: self.open_folder.emit())
            keyboard.add_hotkey(self.cancel, lambda: self.cancel_capture.emit())
        except Exception as e:
            print(f"Update Hotkey Error: {e}")

class UpdateCheckerThread(QThread):
    update_found = pyqtSignal(str, str, str) # version, url, notes

    def run(self):
        try:
            url = "https://capture.yegomne.com/version.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get("latest_version", CURRENT_VERSION)
                download_url = data.get("download_url", "")
                release_notes = data.get("release_notes", "")
                
                # Check if latest version is numerically/alphabetically greater
                if latest_version != CURRENT_VERSION and latest_version > CURRENT_VERSION:
                    self.update_found.emit(latest_version, download_url, release_notes)
        except Exception:
            # 의도된 침묵: 인터넷 연결 안됨, 404 에러 등은 그냥 무시함
            pass

class PreviewWindow(QMainWindow):
    def __init__(self, capture_app, image_cv, save_dir):
        super().__init__()
        self.capture_app = capture_app
        self.image_cv = image_cv
        self.save_dir = save_dir
        self.setWindowTitle("캡쳐 미리보기")
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        
        self.image_label = QLabel()
        self.q_image = cv2_to_qimage(self.image_cv)
        self.pixmap = QPixmap.fromImage(self.q_image)
        self.image_label.setPixmap(self.pixmap)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        self.layout.addWidget(scroll_area)
        
        self.setCentralWidget(self.central_widget)
        self.create_toolbar()
        
        width = min(self.pixmap.width() + 40, 1000)
        height = min(self.pixmap.height() + 100, 800)
        self.resize(width, height)
        self.show()
        self.raise_()
        self.activateWindow()

    def create_toolbar(self):
        toolbar = QToolBar("메인 툴바")
        self.addToolBar(toolbar)
        
        save_action = QAction("저장", self)
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)
        
        cut_action = QAction("잘라내기", self)
        cut_action.triggered.connect(self.copy_to_clipboard)
        toolbar.addAction(cut_action)
        
        open_folder_action = QAction("저장 폴더 열기", self)
        open_folder_action.triggered.connect(self.open_save_folder)
        toolbar.addAction(open_folder_action)
        
        change_dir_action = QAction("환경 설정", self)
        change_dir_action.triggered.connect(self.change_save_dir)
        toolbar.addAction(change_dir_action)
        
    def open_save_folder(self):
        if os.path.exists(self.save_dir):
            os.startfile(self.save_dir)
        
    def change_save_dir(self):
        self.capture_app.open_settings()
        self.save_dir = self.capture_app.save_dir
        
    def save_image(self):
        filepath = self.capture_app.save_image_data(self.image_cv)
        if filepath:
            QMessageBox.information(self, "저장 완료", f"이미지가 저장되었습니다.\n{filepath}")
        else:
            QMessageBox.warning(self, "저장 실패", "이미지 저장에 실패했습니다.")
        self.close()

    def copy_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(self.pixmap)
        self.close()

    def copy_to_clipboard_silent(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(self.pixmap)

class OverlayWidget(QWidget):
    capture_complete = pyqtSignal(object, QRect, bool)

    def __init__(self, screen_image_cv, geometry, is_scroll=False):
        super().__init__()
        self.screen_image_cv = screen_image_cv
        self.is_scroll = is_scroll
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Removed due to Windows Qt bugs on multi-monitor
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setGeometry(geometry)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        self.q_image = cv2_to_qimage(self.screen_image_cv)
        self.pixmap = QPixmap.fromImage(self.q_image)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawPixmap(self.rect(), self.pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if not self.begin.isNull() and not self.end.isNull():
            rect = QRect(self.begin, self.end).normalized()
            painter.drawPixmap(rect, self.pixmap, rect)
            
            pen_color = QColor("#10B981") if self.is_scroll else QColor("#EC4899")
            pen = QPen(pen_color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            painter.setPen(pen_color)
            painter.drawText(rect.topLeft() + QPoint(5, 18), "스크롤 캡쳐 (진행 예정)" if self.is_scroll else "일반 캡쳐")
            
            if rect.width() > 0 and rect.height() > 0:
                dim_text = f" {rect.width()} x {rect.height()} "
                fm = painter.fontMetrics()
                text_rect = fm.boundingRect(dim_text)
                bg_rect = QRect(self.end.x() + 15, self.end.y() + 15, text_rect.width() + 16, text_rect.height() + 12)
                
                painter.setBrush(QColor(43, 45, 49, 210))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(bg_rect, 6, 6)
                
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, dim_text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.begin = event.position().toPoint()
            self.end = self.begin
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.end = event.position().toPoint()
            self.is_drawing = False
            rect = QRect(self.begin, self.end).normalized()
            
            if rect.width() > 0 and rect.height() > 0:
                x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
                cropped = self.screen_image_cv[y:y+h, x:x+w]
                self.capture_complete.emit(cropped, rect, self.is_scroll)
            self.close()

class ScrollCaptureWorker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, start_img, rect, offset_x=0, offset_y=0):
        super().__init__()
        self.start_img = start_img
        self.rect = rect
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.running = True
        
    def run(self):
        import ctypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        self.last_chunk = self.start_img.copy()
        stitched_img = self.start_img.copy()
        
        h = self.rect.height()
        # 스크롤 양을 안정적으로 줄입니다.
        arrows = max(1, int(h * 0.3 / 100))

        time.sleep(0.5) 
        
        cx = self.rect.x() + self.rect.width() // 2 + self.offset_x
        cy = self.rect.y() + self.rect.height() // 2 + self.offset_y
        ctypes.windll.user32.SetCursorPos(int(cx), int(cy))
        
        for i in range(250):
            if not self.running: break
            
            # 마우스를 움직였으면 강제 종료 (무한 루프 방지)
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            if abs(pt.x - int(cx)) > 20 or abs(pt.y - int(cy)) > 20:
                print("마우스 이동 감지됨. 스크롤 캡쳐를 강제 종료합니다.")
                break
            
            ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120 * arrows, 0)
            
            time.sleep(0.4) 
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                img_np = np.array(sct_img)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                
            x, y, w, h = self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height()
            new_chunk = img_cv[y:y+h, x:x+w]
            
            gray1 = cv2.cvtColor(self.last_chunk, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(new_chunk, cv2.COLOR_BGR2GRAY)
            
            H = gray1.shape[0]
            th = int(H * 0.2)
            if th > 10:
                templ_y_starts = [int(H * 0.6), int(H * 0.4), int(H * 0.2), int(H * 0.7)]
                best_match_found = False
                
                for start_y in templ_y_starts:
                    template = gray1[start_y : start_y + th, :]
                    if np.std(template) < 3.0:
                        continue # 너무 단조로운 영역(단색 배경)은 오작동 원인이므로 건너뜀
                        
                    res = cv2.matchTemplate(gray2, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val > 0.75:
                        match_y = max_loc[1]
                        shift = start_y - match_y
                        if shift > 0:
                            unique_part = new_chunk[H - shift : H, :]
                            stitched_img = np.vstack((stitched_img, unique_part))
                            self.last_chunk = new_chunk
                            best_match_found = True
                            break # Append success
                        elif shift <= 0:
                            # Didn't scroll down
                            pass
                
                if not best_match_found:
                    break
        
        self.finished.emit(stitched_img)


class SettingsDialog(QDialog):
    def __init__(self, current_theme, current_naming, current_format, current_dir, current_autosave, current_hk_normal, current_hk_scroll, current_hk_folder, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경 설정")
        self.resize(400, 360)
        
        self.theme = current_theme
        self.naming = current_naming
        self.format = current_format
        self.save_dir = current_dir
        self.auto_save = current_autosave
        self.hk_normal = current_hk_normal
        self.hk_scroll = current_hk_scroll
        self.hk_folder = current_hk_folder
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 1. 테마 선택
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText(self.theme)
        form_layout.addRow("테마 (Theme):", self.theme_combo)
        
        # 2. 파일 네이밍 방식
        naming_layout = QHBoxLayout()
        self.rb_seq = QRadioButton("순차 번호 (0001)")
        self.rb_time = QRadioButton("타임스탬프 저장")
        self.naming_group = QButtonGroup()
        self.naming_group.addButton(self.rb_seq)
        self.naming_group.addButton(self.rb_time)
        if self.naming == "Timestamp":
            self.rb_time.setChecked(True)
        else:
            self.rb_seq.setChecked(True)
        naming_layout.addWidget(self.rb_seq)
        naming_layout.addWidget(self.rb_time)
        form_layout.addRow("저장 파일명:", naming_layout)
        
        # 3. 확장자
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPG", "PNG"])
        self.format_combo.setCurrentText(self.format.upper())
        form_layout.addRow("저장 포맷:", self.format_combo)
        
        # 4. 저장 위치
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(self.save_dir)
        self.dir_edit.setReadOnly(True)
        self.btn_browse = QPushButton("찾아보기")
        self.btn_browse.clicked.connect(self.browse_dir)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(self.btn_browse)
        form_layout.addRow("저장 폴더:", dir_layout)
        
        # 5. 자동 저장
        self.chk_autosave = QCheckBox("자동 저장 (미리보기 건너뛰기)")
        self.chk_autosave.setChecked(self.auto_save)
        form_layout.addRow("편의 기능:", self.chk_autosave)
        
        # 6. 단축키
        hk_layout = QVBoxLayout()
        hk_cap_layout = QHBoxLayout()
        self.edit_hk_normal = QLineEdit(self.hk_normal)
        self.edit_hk_scroll = QLineEdit(self.hk_scroll)
        self.edit_hk_normal.setPlaceholderText("예: ctrl+space")
        self.edit_hk_scroll.setPlaceholderText("예: ctrl+shift+space")
        hk_cap_layout.addWidget(QLabel("일반:"))
        hk_cap_layout.addWidget(self.edit_hk_normal)
        hk_cap_layout.addWidget(QLabel("스크롤:"))
        hk_cap_layout.addWidget(self.edit_hk_scroll)
        
        hk_sys_layout = QHBoxLayout()
        self.edit_hk_folder = QLineEdit(self.hk_folder)
        self.edit_hk_folder.setPlaceholderText("예: ctrl+alt+shift+x")
        hk_sys_layout.addWidget(QLabel("폴더 열기:"))
        hk_sys_layout.addWidget(self.edit_hk_folder)
        
        hk_layout.addLayout(hk_cap_layout)
        hk_layout.addLayout(hk_sys_layout)
        form_layout.addRow("단축키:", hk_layout)
        
        layout.addLayout(form_layout)
        
        # 버튼 박스
        btn_layout = QHBoxLayout()
        btn_uninstall = QPushButton("앱 삭제 (Uninstall)")
        btn_uninstall.setStyleSheet("color: red; font-weight: bold;")
        btn_uninstall.setToolTip("프로그램 설정과 실행 파일을 모두 완전히 삭제합니다.")
        btn_uninstall.clicked.connect(self.request_uninstall)
        
        btn_save = QPushButton("저장")
        btn_cancel = QPushButton("취소")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_uninstall)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)

    def request_uninstall(self):
        reply = QMessageBox.warning(
            self, "프로그램 완전 삭제",
            "정말로 이 프로그램을 삭제하시겠습니까?\n프로그램 설정과 파일이 모두 삭제되며, 즉시 종료됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.done(2)

    def browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", self.dir_edit.text())
        if dir_path:
            self.dir_edit.setText(dir_path)
            self.save_dir = dir_path

    def get_settings(self):
        return {
            "app_theme": self.theme_combo.currentText(),
            "naming_style": "Timestamp" if self.rb_time.isChecked() else "Sequence",
            "save_format": self.format_combo.currentText().lower(),
            "save_dir": self.dir_edit.text(),
            "auto_save": self.chk_autosave.isChecked(),
            "hotkey_normal": self.edit_hk_normal.text().strip() or "ctrl+space",
            "hotkey_scroll": self.edit_hk_scroll.text().strip() or "ctrl+shift+space",
            "hotkey_folder": self.edit_hk_folder.text().strip() or "ctrl+alt+shift+x"
        }

class CaptureApp(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        self.app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "CaptureApp")
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
            
        self.config_file = os.path.join(self.app_data_dir, "config.json")
        self.save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "CaptureApp")
        self.app_theme = "Light"
        self.naming_style = "Sequence"
        self.save_format = "jpg"
        self.auto_save = False
        self.hotkey_normal = "ctrl+space"
        self.hotkey_scroll = "ctrl+shift+space"
        self.hotkey_folder = "ctrl+alt+shift+x"
        self.load_config()
        
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.apply_theme()
        self.setup_tray()
        self.overlay = None
        self.preview = None
        self.scroll_worker = None
        
        self.pending_scroll = False
        self.capture_timer = QTimer()
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self._execute_capture)
        
        self.hotkey_thread = HotkeyThread(self.hotkey_normal, self.hotkey_scroll, self.hotkey_folder)
        self.hotkey_thread.trigger_capture.connect(self._debounce_capture)
        self.hotkey_thread.cancel_capture.connect(self._cancel_capture)
        self.hotkey_thread.open_folder.connect(self._open_save_folder)
        self.hotkey_thread.start()

        # 업데이트 체크 시작
        self.update_thread = UpdateCheckerThread()
        self.update_thread.update_found.connect(self.show_update_popup)
        self.update_thread.start()

        # 첫 실행 시 유저 온보딩용 웰컴 토스트
        self.tray_icon.showMessage(
            "캡쳐 준비 완료! 📸", 
            f"일반 캡쳐: [{self.hotkey_normal}]\n스크롤 캡쳐: [{self.hotkey_scroll}]\n폴더 열기: [{self.hotkey_folder}]", 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )

    def show_update_popup(self, version, url, notes):
        # PyQt6 환경에서 안전하게 팝업 띄우기
        reply = QMessageBox.information(
            None, 
            "업데이트 알림 🚀",
            f"새로운 버전(v{version})이 배포되었습니다!\n\n[업데이트 내용]\n{notes}\n\n지금 공식 홈페이지로 이동하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes and url:
            webbrowser.open(url)

    def _cancel_capture(self):
        if self.overlay:
            self.overlay.close()
        if self.scroll_worker and self.scroll_worker.running:
            self.scroll_worker.running = False

    def _open_save_folder(self):
        if os.path.exists(self.save_dir):
            os.startfile(self.save_dir)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)
        icon_path = resource_path("icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("blue"))
            self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        
        help_action = QAction("사용법 / 단축키 안내", self.app)
        help_action.triggered.connect(self.show_help)
        tray_menu.addAction(help_action)
        
        tray_menu.addSeparator()

        settings_action = QAction("환경 설정", self.app)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        quit_action = QAction("종료", self.app)
        quit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_help(self):
        msg = QMessageBox()
        msg.setWindowTitle("단축키 안내")
        msg.setText("📸 캡쳐 프로그램 사용법")
        msg.setInformativeText(f"일반 캡쳐 : [{self.hotkey_normal}]\n스크롤 캡쳐 : [{self.hotkey_scroll}]\n폴더 열기 : [{self.hotkey_folder}]\n\n캡쳐 취소 : [ESC]")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.exec()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.save_dir = config.get("save_dir", self.save_dir)
                    self.app_theme = config.get("app_theme", self.app_theme)
                    self.naming_style = config.get("naming_style", self.naming_style)
                    self.save_format = config.get("save_format", self.save_format)
                    self.auto_save = config.get("auto_save", self.auto_save)
                    self.hotkey_normal = config.get("hotkey_normal", self.hotkey_normal)
                    self.hotkey_scroll = config.get("hotkey_scroll", self.hotkey_scroll)
                    self.hotkey_folder = config.get("hotkey_folder", self.hotkey_folder)
            except Exception:
                pass

    def save_config(self):
        try:
            data = {
                "save_dir": self.save_dir,
                "app_theme": self.app_theme,
                "naming_style": self.naming_style,
                "save_format": self.save_format,
                "auto_save": self.auto_save,
                "hotkey_normal": self.hotkey_normal,
                "hotkey_scroll": self.hotkey_scroll,
                "hotkey_folder": self.hotkey_folder
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def open_settings(self):
        dialog = SettingsDialog(self.app_theme, self.naming_style, self.save_format, self.save_dir, self.auto_save, self.hotkey_normal, self.hotkey_scroll, self.hotkey_folder)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        ret = dialog.exec()
        if ret == 1:
            settings = dialog.get_settings()
            self.app_theme = settings["app_theme"]
            self.naming_style = settings["naming_style"]
            self.save_format = settings["save_format"]
            self.save_dir = settings["save_dir"]
            self.auto_save = settings["auto_save"]
            self.hotkey_normal = settings["hotkey_normal"]
            self.hotkey_scroll = settings["hotkey_scroll"]
            self.hotkey_folder = settings["hotkey_folder"]
            self.save_config()
            self.apply_theme()
            self.hotkey_thread.update_hotkeys(self.hotkey_normal, self.hotkey_scroll, self.hotkey_folder)
        elif ret == 2:
            self.uninstall_application()

    def uninstall_application(self):
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except Exception:
                pass
        
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            bat_path = os.path.join(os.environ.get("TEMP", "C:/"), "uninstall_capture.bat")
            try:
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("timeout /t 2 /nobreak > NUL\n")
                    f.write(f'del /f /q "{app_path}"\n')
                    f.write(f'del "%~f0"\n')
                subprocess.Popen([bat_path], shell=True, creationflags=0x08000000)
            except Exception:
                pass
        
        self.tray_icon.hide()
        QApplication.quit()

    def get_next_filename(self):
        ext = f".{self.save_format}"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        if self.naming_style == "Timestamp":
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            return os.path.join(self.save_dir, f"{ts}{ext}")
        else:
            files = os.listdir(self.save_dir)
            max_num = 0
            for f in files:
                if f.endswith('.jpg') or f.endswith('.png'):
                    try:
                        num = int(os.path.splitext(f)[0])
                        if num > max_num: max_num = num
                    except ValueError:
                        pass
            return os.path.join(self.save_dir, f"{max_num + 1:04d}{ext}")

    def save_image_data(self, image_cv):
        filepath = self.get_next_filename()
        ext = f".{self.save_format}"
        is_success, im_buf_arr = cv2.imencode(ext, image_cv)
        if is_success:
            with open(filepath, 'wb') as f:
                f.write(im_buf_arr.tobytes())
            return filepath
        return None

    def apply_theme(self):
        if self.app_theme == "Dark":
            self.app.setStyleSheet("""
                QWidget { background-color: #2b2d31; color: #f2f3f5; font-family: 'Segoe UI', sans-serif; }
                QMenu { background-color: #2b2d31; color: #f2f3f5; border: 1px solid #1e1f22; border-radius: 6px; padding: 4px; }
                QMenu::item { padding: 6px 20px; border-radius: 4px; }
                QMenu::item:selected { background-color: #EC4899; color: white; }
                QMessageBox, QDialog { background-color: #2b2d31; border-radius: 8px; }
                QComboBox, QLineEdit {
                    background-color: #1e1f22; color: #f2f3f5; border: 1px solid #1e1f22; 
                    border-radius: 6px; padding: 6px; selection-background-color: #EC4899;
                }
                QPushButton {
                    background-color: #1e1f22; color: #f2f3f5; border: 1px solid #1e1f22; 
                    border-radius: 6px; padding: 8px 16px; font-weight: bold;
                }
                QPushButton:hover { background-color: #EC4899; color: white; border: 1px solid #EC4899; }
                QPushButton:pressed { background-color: #BE185D; }
                QScrollBar:vertical { background: #2b2d31; width: 10px; margin: 0px 0px 0px 0px; }
                QScrollBar::handle:vertical { background: #1e1f22; border-radius: 5px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #EC4899; }
            """)
        else:
            self.app.setStyleSheet("""
                QWidget { background-color: #ffffff; color: #333333; font-family: 'Segoe UI', sans-serif; }
                QMenu { background-color: #ffffff; color: #333333; border: 1px solid #e0e0e0; border-radius: 6px; padding: 4px; }
                QMenu::item { padding: 6px 20px; border-radius: 4px; }
                QMenu::item:selected { background-color: #EC4899; color: white; }
                QMessageBox, QDialog { background-color: #f7f9fc; border-radius: 8px; }
                QComboBox, QLineEdit {
                    background-color: #ffffff; color: #333333; border: 1px solid #d1d5db; 
                    border-radius: 6px; padding: 6px; selection-background-color: #EC4899;
                }
                QPushButton {
                    background-color: #f3f4f6; color: #374151; border: 1px solid #d1d5db; 
                    border-radius: 6px; padding: 8px 16px; font-weight: bold;
                }
                QPushButton:hover { background-color: #EC4899; color: white; border: 1px solid #EC4899; }
                QPushButton:pressed { background-color: #BE185D; }
                QScrollBar:vertical { background: #f3f4f6; width: 10px; margin: 0px 0px 0px 0px; }
                QScrollBar::handle:vertical { background: #d1d5db; border-radius: 5px; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #EC4899; }
            """)

    def _debounce_capture(self, is_scroll):
        if is_scroll:
            self.pending_scroll = True
        
        # Debounce timer: wait 100ms before evaluating the action.
        # This resolves the conflict when standard and explicit hotkeys fire concurrently.
        self.capture_timer.start(100)

    def _execute_capture(self):
        is_scroll = self.pending_scroll
        self.pending_scroll = False
        self._start_capture(is_scroll)

    def _start_capture(self, is_scroll):
        if hasattr(self, 'overlay') and self.overlay and self.overlay.isVisible():
            return

        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            img_np = np.array(sct_img)
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            
        geometry = QRect(monitor["left"], monitor["top"], monitor["width"], monitor["height"])
        
        self.overlay = OverlayWidget(img_cv, geometry, is_scroll)
        self.overlay.capture_complete.connect(self.process_capture)
        self.overlay.show()

    def process_capture(self, cropped_img_cv, rect, is_scroll):
        if not is_scroll:
            self.show_preview(cropped_img_cv)
        else:
            # 트레이 메시지로 인한 포커스 상실 및 캡쳐 화면 왜곡 방지를 위해 주석 처리
            # self.tray_icon.showMessage("스크롤 캡쳐 진행 중", "키보드 조작을 멈춰주세요...", QSystemTrayIcon.MessageIcon.Information, 2000)
            offset_x = self.overlay.geometry().x()
            offset_y = self.overlay.geometry().y()
            self.scroll_worker = ScrollCaptureWorker(cropped_img_cv, rect, offset_x, offset_y)
            self.scroll_worker.finished.connect(self.show_preview)
            self.scroll_worker.start()

    def show_preview(self, cropped_img_cv):
        if self.auto_save:
            q_img = cv2_to_qimage(cropped_img_cv)
            clipboard = QGuiApplication.clipboard()
            clipboard.setPixmap(QPixmap.fromImage(q_img))
            
            filepath = self.save_image_data(cropped_img_cv)
            if filepath:
                self.tray_icon.showMessage("자동 저장 완료", f"저장 완료: {os.path.basename(filepath)}", QSystemTrayIcon.MessageIcon.Information, 2500)
            return

        self.preview = PreviewWindow(self, cropped_img_cv, self.save_dir)
        # 캡쳐 완료 후 즉시 클립보드에 무음 복사
        self.preview.copy_to_clipboard_silent()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    import ctypes
    try:
        myappid = 'mycompany.myproduct.captureapp.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
        
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    app.setQuitOnLastWindowClosed(False)
    
    capture_app = CaptureApp(app)
    sys.exit(app.exec())
