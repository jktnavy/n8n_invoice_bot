APPROVAL_WORDS = {
    "setuju",
    "iya",
    "ya",
    "oke",
    "ok",
    "gas",
    "lanjut",
    "buat",
    "sudah benar",
    "sip",
    "yes",
}


def is_natural_approval(message: str, conversation_state: str) -> bool:
    if conversation_state != "AWAITING_APPROVAL":
        return False
    normalized = " ".join(message.casefold().strip().split())
    return normalized in APPROVAL_WORDS

