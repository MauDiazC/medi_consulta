def can_manage_users(user: dict) -> bool:
    return user["role"] == "admin"


def can_sign_note(user: dict) -> bool:
    return user["role"] in ["doctor", "admin"]


def can_view_patient(user: dict) -> bool:
    return user["role"] in [
        "doctor",
        "nurse",
        "assistant",
        "admin",
    ]