import sys
import os

# Add the project root to sys.path so core and ui modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
