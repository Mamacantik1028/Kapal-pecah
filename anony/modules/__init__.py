def all_modules():
    return [
        file.stem
        for file in __import__("pathlib").Path(__file__).parent.glob("*.py")
        if file.is_file() and file.name != "__init__.py"
    ]
