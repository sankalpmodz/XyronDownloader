import re


def sanitize_title(title):
    if not title:
        return "Unknown"
    title = re.sub(r'<[^>]*>', '', title)
    title = title.replace("<", "").replace(">", "")
    title = title.replace("_", "\\_")
    title = title.replace("*", "\\*")
    title = title.replace("`", "\\`")
    title = title.replace("~", "\\~")
    title = title.replace("[", "\\[")
    title = title.replace("]", "\\]")
    return title.strip()


def sanitize_html(text):
    if not text:
        return "Unknown"
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text
