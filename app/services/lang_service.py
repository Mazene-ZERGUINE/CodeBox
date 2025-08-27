from enum import Enum


class Language(str, Enum):
    python = "python"
    javascript = "javascript"
    c = "c"
    php = "php"


FILES_EXTENSIONS: dict[Language, str] = {
    Language.python: ".py",
    Language.javascript: ".js",
    Language.c: ".c",
    Language.php: ".php",
}


def normalize_language(name: str) -> Language:
    if not isinstance(name, str):
        raise ValueError("Language must be a string.")
    key = name.strip().lower()
    try:
        return Language(key)
    except ValueError:
        raise ValueError(f"{name!r} programming language is not supported")


def extract_extension(programming_language: str) -> str:
    lang = normalize_language(programming_language)
    return FILES_EXTENSIONS[lang]
