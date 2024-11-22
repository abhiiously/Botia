# parsers/base.py

def fix_encoding(text):
    if text:
        try:
            text = text.encode('latin1').decode('utf-8')
        except UnicodeEncodeError:
            pass
    return text

class ChatParser:
    def parse(self, file_path):
        raise NotImplementedError("This method should be overridden by subclasses.")
