class Exporter:
    @staticmethod
    def write_file(filepath: str, content: str) -> bool:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
            
    @staticmethod
    def copy_to_clipboard(root, content: str):
        """
        Uses Tkinter's clipboard functionality.
        root is the Tkinter root window.
        """
        root.clipboard_clear()
        root.clipboard_append(content)
        root.update()
