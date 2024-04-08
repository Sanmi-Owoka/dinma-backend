def remove_percentage(percentage_string: str) -> int:
    string_array = percentage_string.split("%")
    return int(string_array[0])
