import re

def filter_raw_html_data(raw_html: str) -> str:
    """
    Clean raw HTML into readable text.
    """
    if not raw_html:
        return ""

    # Bước 1: remove unwanted tags (script, style, nav, footer)
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", raw_html, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<nav[\s\S]*?</nav>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<footer[\s\S]*?</footer>", "", cleaned, flags=re.IGNORECASE)

    # Remove all HTML tags → convert to newlines
    cleaned = re.sub(r"<[^>]+>", "\n", cleaned)

    # Remove redundant blank lines
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)

    # Bước 2: split into lines + filter lines shorter than 50 chars
    lines = [line.strip() for line in cleaned.split("\n") if len(line.strip()) > 50]

    # Bước 3: join back into a full text block
    full_text = "\n".join(lines)

    return full_text
