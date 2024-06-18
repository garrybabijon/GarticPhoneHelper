import sys
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QLineEdit, QVBoxLayout, QPushButton, QWidget, QSlider, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QSettings

class TransparentImageWindow(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.original_pixmap = pixmap
        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)
        self.label.resize(pixmap.size())
        self.resize(pixmap.size())

        self.dragging = False
        self.drag_offset = QPoint()
        self.interactive = True

        self.settings = QSettings('ImageOverlayApp', 'positions')

        self.move(self.settings.value('lastPosition', QPoint(200, 200), type=QPoint))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.interactive:
            self.dragging = True
            self.drag_offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.interactive:
            self.move(self.pos() + event.pos() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def wheelEvent(self, event):
        if self.interactive:
            angle = event.angleDelta().y() / 8
            steps = angle / 15
            factor = 1 + steps * 0.1
            self.resize(self.size() * factor)
            self.label.resize(self.label.size() * factor)

    def updateOpacity(self, value):
        opacity = value / 100.0
        image = self.original_pixmap.toImage()
        image = image.convertToFormat(QImage.Format_ARGB32)

        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                color.setAlpha(int(255 * opacity))
                image.setPixelColor(x, y, color)

        self.label.setPixmap(QPixmap.fromImage(image))

    def setNonInteractive(self):
        self.interactive = False
        self.setWindowFlags(self.windowFlags() | Qt.WindowTransparentForInput)
        self.show()

    def setInteractive(self):
        self.interactive = True
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowTransparentForInput)
        self.show()

    def closeEvent(self, event):
        # сохранить текущюю позицию
        self.settings.setValue('lastPosition', self.pos())
        super().closeEvent(event)

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.label = QLabel('Выберите изображение:', self)

        self.button = QPushButton('Выбрать изображение', self)
        self.button.clicked.connect(self.loadImage)

        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(35)
        self.opacity_slider.setEnabled(False)
        self.opacity_slider.valueChanged.connect(self.changeOpacity)

        self.fix_button = QPushButton('Закрепить изображение', self)
        self.fix_button.clicked.connect(self.fixImage)
        self.fix_button.setEnabled(False)

        self.unfix_button = QPushButton('Открепить изображение', self)
        self.unfix_button.clicked.connect(self.unfixImage)
        self.unfix_button.setEnabled(False)

        self.reset_button = QPushButton('Сбросить изображение', self)
        self.reset_button.clicked.connect(self.resetImage)
        self.reset_button.setEnabled(False)

        self.zoom_in_button = QPushButton('Увеличить изображение', self)
        self.zoom_in_button.clicked.connect(self.zoomIn)
        self.zoom_in_button.setEnabled(False)

        self.zoom_out_button = QPushButton('Уменьшить изображение', self)
        self.zoom_out_button.clicked.connect(self.zoomOut)
        self.zoom_out_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.opacity_slider)
        layout.addWidget(self.fix_button)
        layout.addWidget(self.unfix_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.zoom_out_button)
        self.setLayout(layout)

        self.image_window = None

    def loadImage(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.xpm *.jpg *.bmp *.gif)", options=options)
        if filePath:
            pixmap = QPixmap(filePath)
            if self.image_window is None:
                self.image_window = TransparentImageWindow(pixmap)
            else:
                self.image_window.original_pixmap = pixmap
                self.image_window.label.setPixmap(pixmap)
                self.image_window.label.resize(pixmap.size())
                self.image_window.resize(pixmap.size())

            self.image_window.updateOpacity(35)
            self.image_window.show()
            self.opacity_slider.setEnabled(True)
            self.fix_button.setEnabled(True)
            self.unfix_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.zoom_in_button.setEnabled(True)
            self.zoom_out_button.setEnabled(True)
            QMessageBox.information(self, 'Успех', 'Изображение успешно загружено.')

    def changeOpacity(self):
        if self.image_window:
            value = self.opacity_slider.value()
            self.image_window.updateOpacity(value)

    def fixImage(self):
        if self.image_window:
            self.image_window.setNonInteractive()
            self.fix_button.setEnabled(False)
            self.unfix_button.setEnabled(True)

    def unfixImage(self):
        if self.image_window:
            self.image_window.setInteractive()
            self.fix_button.setEnabled(True)
            self.unfix_button.setEnabled(False)

    def resetImage(self):
        if self.image_window:
            self.image_window.label.setPixmap(self.image_window.original_pixmap)
            self.image_window.label.resize(self.image_window.original_pixmap.size())
            self.image_window.resize(self.image_window.original_pixmap.size())
            self.opacity_slider.setValue(35)
            self.image_window.updateOpacity(35)

    def zoomIn(self):
        if self.image_window:
            factor = 1.1
            self.image_window.resize(self.image_window.size() * factor)
            self.image_window.label.resize(self.image_window.label.size() * factor)

    def zoomOut(self):
        if self.image_window:
            factor = 0.9
            self.image_window.resize(self.image_window.size() * factor)
            self.image_window.label.resize(self.image_window.label.size() * factor)

def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("ImageOverlayApp")
    app.setApplicationDisplayName("Image Overlay Application")
    
    app.setWindowIcon(QIcon('ico.jpg'))

    settings_window = SettingsWindow()
    settings_window.show()

    def quitApp():
        if settings_window.image_window:
            settings_window.image_window.close()
        app.quit()
    
    def keyPressEvent(event):
        if event.key() in (Qt.Key_Q, Qt.Key_Escape):
            quitApp()
    
    app.aboutToQuit.connect(quitApp)
    app.keyPressEvent = keyPressEvent

    app.exec_()

if __name__ == '__main__':
    main()
