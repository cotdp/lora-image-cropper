import re
import sys
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QImage, QPixmap, QPen, QColor, QBrush
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsRectItem, QGraphicsItem, QComboBox


class ResizeHandle(QGraphicsRectItem):
    """
    A resize handle for a QGraphicsRectItem.

    This class provides a resize handle that can be used to resize a QGraphicsRectItem. The handle is positioned at the
    bottom-right corner of the parent item, and can be dragged to resize the parent item.

    Attributes:
        None

    Methods:
        mouseMoveEvent: Handles the mouse move event for the resize handle.
        mouseReleaseEvent: Handles the mouse release event for the resize handle.
    """
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setRect(-40, -40, 40, 40)
        self.setPos(parent.rect().right(), parent.rect().bottom())
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)

    def mouseMoveEvent(self, event):
        """
        Handles the mouse move event for the resize handle.

        This method is called when the mouse is moved while the resize handle is selected. It resizes the parent item
        based on the position of the resize handle and the mouse.

        Args:
            event: The mouse move event.

        Returns:
            None
        """
        super().mouseMoveEvent(event)

        # Resize the parent item based on the position of the resize handle and the mouse
        if self.isSelected():
            parent = self.parentItem()
            parent_rect = parent.rect()
            handle_rect = self.rect()

            # Calculate the new width and height of the parent item based on the larger of the horizontal and vertical distances
            dx = event.scenePos().x() - parent_rect.x() - parent_rect.width() + handle_rect.width() / 2
            dy = event.scenePos().y() - parent_rect.y() - parent_rect.height() + handle_rect.height() / 2
            new_size = max(dx, dy)
            new_width = new_size + parent_rect.width()
            new_height = new_size + parent_rect.height()

            # Set the new size of the parent item
            parent_rect.setWidth(new_width)
            parent_rect.setHeight(new_height)
            parent.setRect(parent_rect)

            # Update the position of the resize handle
            self.setPos(parent_rect.right(), parent_rect.bottom())

    def mouseReleaseEvent(self, event):
        """
        Handles the mouse release event for the resize handle.

        This method is called when the mouse button is released while the resize handle is selected. It resets the
        position of the resize handle to the bottom-right corner of the parent item.

        Args:
            event: The mouse release event.

        Returns:
            None
        """
        super().mouseReleaseEvent(event)

        # Reset the position of the resize handle to the bottom-right corner of the parent item
        parent = self.parentItem()
        parent_rect = parent.rect()
        self.setPos(parent_rect.right(), parent_rect.bottom())


class DraggableRectItem(QGraphicsRectItem):
    """
    A rectangular item that can be dragged and resized in a QGraphicsScene.

    This class is a subclass of QGraphicsRectItem that adds support for dragging and resizing the item
    using the mouse. The item can be moved by dragging it with the mouse, and it can be resized by
    dragging the bottom-right corner of the item.

    Attributes:
        resize_handle (ResizeHandle): A handle that can be used to resize the item.

    Methods:
        __init__(self, rect, parent=None): Initializes a new instance of the DraggableRectItem class.
        mousePressEvent(self, event): Handles the mouse press event on the item.
        mouseMoveEvent(self, event): Handles the mouse move event on the item.
        mouseReleaseEvent(self, event): Handles the mouse release event on the item.
    """

    def __init__(self, rect, parent=None):
        """
        Initializes a new instance of the DraggableRectItem class.

        Args:
            rect (QRectF): The rectangle that defines the position and size of the item.
            parent (QGraphicsItem): The parent item of the item (default: None).
        """
        super().__init__(rect, parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Add a resize handle to the bottom-right corner of the box
        self.resize_handle = ResizeHandle(self)

    def mousePressEvent(self, event):
        """
        Handles the mouse press event on the item.

        This method sets the cursor to a closed hand cursor when the mouse button is pressed on the item.

        Args:
            event (QGraphicsSceneMouseEvent): The mouse press event.
        """
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handles the mouse move event on the item.

        This method handles the mouse move event when the item is being dragged or resized.

        Args:
            event (QGraphicsSceneMouseEvent): The mouse move event.
        """
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handles the mouse release event on the item.

        This method sets the cursor to an open hand cursor when the mouse button is released from the item.

        Args:
            event (QGraphicsSceneMouseEvent): The mouse release event.
        """
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class ImageProcessor(QMainWindow):
    """
    A class that provides image processing functionality.

    This class provides methods for loading, saving, and processing images. It can load images from files
    or from memory, and it can save images to files. It also provides methods for cropping and resizing images.

    Attributes:
        image (QImage): The current image being processed.

    Methods:
        __init__(self): Initializes a new instance of the ImageProcessor class.
        load_image(self, filename): Loads an image from a file.
        save_image(self, filename): Saves the current image to a file.
        crop_image(self): Crops the current image to the bounding rectangle of the selected box.
        resize_image(self, size): Resizes the current image to the specified size.
    """

    def __init__(self):
        """
        Initializes a new instance of the ImageProcessor class.
        """
        super().__init__()
        self.title = "Image Processor"
        self.image_width = 1024
        self.image_height = 1024

        # Set up the UI
        self.initUI()
        
        # Set up drag and drop events
        self.setAcceptDrops(True)

        # Set up the image
        self.image = None
        self.image_original = None

        # Setup the crop box
        self.box = None

        # Suggested filename based on the pattern 'image_001.jpg'
        self.suggested_filename = "image_000.jpg"

    def dragEnterEvent(self, event):
        """
        Handles the drag enter event for the main window.

        This method is called when a drag and drop operation enters the main window. It checks if the drag data
        contains URLs and accepts the event if it does.

        Args:
            event (QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Handles the drop event for the main window.

        This method is called when a drag and drop operation is dropped onto the main window. It loads the image
        from the dropped file and displays it in the canvas.

        Args:
            event (QDropEvent): The drop event.
        """
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.load_image(file_path)

    def resizeEvent(self, event):
        """
        Handles the resize event for the main window.

        This method is called when the main window is resized. It resizes the canvas to fit the new size of the
        window and adjusts the view to maintain the aspect ratio of the image.

        Args:
            event (QResizeEvent): The resize event.
        """
        self.canvas.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def initUI(self):
        """
        Initializes the user interface for the main window.

        This method sets up the UI elements for the main window, including buttons for loading, cropping, saving,
        and resetting the image, as well as a message label for displaying status messages. It also sets up the
        canvas for displaying the image and the scene for managing the items in the canvas.

        The layout of the UI elements is set up using QVBoxLayout and QHBoxLayout, and the central widget of the
        main window is set to a QWidget that contains the layout.

        The minimum size of the canvas is set to 1024x1024, and an event filter is installed on the canvas viewport
        to handle mouse events.

        Returns:
            None
        """
        # Set up the UI elements
        self.upload_button = QPushButton("\nLoad Image\n", self)
        self.upload_button.clicked.connect(self.load_image)

        self.size_combo_box = QComboBox(self)
        self.size_combo_box.addItem("512 x 512")
        self.size_combo_box.addItem("1024 x 1024")
        self.size_combo_box.addItem("2048 x 2048")
        self.size_combo_box.setCurrentText("1024 x 1024")
        self.size_combo_box.currentTextChanged.connect(self.set_image_size)

        self.save_button = QPushButton("\nSave Cropped Image\n", self)
        self.save_button.clicked.connect(self.save_image)

        self.message_label = QLabel("", self)

        # Set up the buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.upload_button)
        buttons_layout.addWidget(self.size_combo_box)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.message_label)

        # Set up the canvas
        self.canvas = QGraphicsView(self)
        self.canvas.setMinimumSize(self.image_width, self.image_height)
        self.canvas.viewport().installEventFilter(self)

        # Set up the main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.canvas)

        # Set up the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Set up the scene
        self.scene = QGraphicsScene(self)
        self.canvas.setScene(self.scene)

    def eventFilter(self, obj, event):
        """
        Filters events for the main window.

        This method is called for all events that occur in the main window. It checks if an image is loaded and
        if the event is a mouse button press on the canvas viewport. If an image is not loaded and the event is a
        mouse button press on the canvas viewport, it loads an image. Otherwise, it passes the event to the base
        class event filter.

        Args:
            obj (QObject): The object that the event was generated for.
            event (QEvent): The event that occurred.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        # If no image is loaded, load one when the user clicks on the canvas
        if self.image is None and obj is self.canvas.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            self.load_image()
            return True
        return super().eventFilter(obj, event)
    
    def set_image_size(self, size):
        """
        Sets the size of the image.

        This method sets the size of the image based on the selected size in the combo box. It sets the values of
        self.image_width and self.image_height accordingly.

        Args:
            size (str): The selected size in the combo box.

        Returns:
            None
        """
        if size == "512 x 512":
            self.image_width = 512
            self.image_height = 512
        elif size == "1024 x 1024":
            self.image_width = 1024
            self.image_height = 1024
        elif size == "2048 x 2048":
            self.image_width = 2048
            self.image_height = 2048
        else:
            raise ValueError(f"Invalid size: {size}")
        self.draw_image()

    def load_image(self, file_path=None):
        """
        Loads an image from a file.

        Args:
            filename (str): The name of the file to load the image from.
        """
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            self.image_original = self.image = QImage(file_path)
            self.draw_image()

    def save_image(self):
        """
        Crops the current image to the bounding rectangle of the selected box. Saves the cropped image to a file.

        Args:
            filename (str): The name of the file to save the image to.
        """
        if self.image and self.box:
            # Get the bounding rectangle of the box in item coordinates
            box_rect = self.box.boundingRect()
            box_pos = self.box.pos()
            box_rect.translate(box_pos)

            # Crop the image to the bounding rectangle of the box
            cropped_image = self.image.copy(box_rect.toRect())

            if re.match(r"\w+_\d{3}.jpg", self.suggested_filename):
                self.suggested_filename = "".join([self.suggested_filename.split("_")[0], "_", str(int(self.suggested_filename.split("_")[1].split(".")[0]) + 1).zfill(3), ".jpg"])
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", self.suggested_filename, "JPEG Files (*.jpg)")
            if file_path:
                cropped_image = cropped_image.scaled(self.image_width, self.image_height, Qt.AspectRatioMode.KeepAspectRatio)
                cropped_image.save(file_path, "JPEG")
                self.message_label.setText("Saved!")
                # Extract the filename from the file_path
                self.suggested_filename = file_path.split("/")[-1]

    def draw_image(self, draw_box=True):
        """
        Draws the current image onto the canvas.

        This method draws the current image onto the canvas using a QPixmap. It then adds a box over the center of
        the image using the DraggableRectItem class. The box is drawn with a red pen and a transparent black brush.

        If the draw_box parameter is False, the box is not drawn.

        Args:
            draw_box (bool): Whether to draw the box over the center of the image.

        Returns:
            None
        """
        if not self.image:
            return

        # Clear the scene
        self.scene.clear()
        self.canvas.resetTransform()

        # Draw the image onto the scene
        pixmap = QPixmap.fromImage(self.image)
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(pixmap.rect().topLeft().x(), pixmap.rect().topLeft().y(), pixmap.rect().width(), pixmap.rect().height())

        # Draw a box over the center of the image
        if draw_box:
            image_rect = pixmap.rect()
            box_width = self.image_width
            box_height = self.image_height
            box_rect = QRectF(0, 0, box_width, box_height)
            self.box = box = DraggableRectItem(box_rect)  # Use the DraggableRectItem class instead of QGraphicsRectItem
            box.setPos(image_rect.center().x() - box_width // 2, image_rect.center().y() - box_height // 2)
            box_pen = QPen(Qt.GlobalColor.red)
            box_pen.setWidth(20)  # Set the pen width to 5 pixels
            box.setPen(box_pen)
            box_brush = QBrush(QColor(0, 0, 0, 64))  # Set the brush to transparent black
            box.setBrush(box_brush)
            self.scene.addItem(box)
        else:
            self.box = None

        self.canvas.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_processor = ImageProcessor()
    image_processor.show()
    sys.exit(app.exec())
