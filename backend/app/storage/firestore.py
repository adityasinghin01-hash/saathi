class FirestoreStore:
    """Reserved adapter; backend currently persists locally in SQLite."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Firestore adapter is a later task")
