files_extensions = {
    "python": ".py",
    "javascript": ".js",
    "c": ".c",
    "php": ".php"
}


def extract_extension(programming_language: str) -> str:
    if programming_language not in files_extensions.keys():
        raise ValueError(
            f"{programming_language} programming language is not supported")

    return files_extensions[programming_language]
