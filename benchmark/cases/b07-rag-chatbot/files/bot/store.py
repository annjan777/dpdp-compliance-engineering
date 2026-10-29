users = {}
history = []


class VectorStore:
    def __init__(self):
        self.items = []

    def add(self, text):
        self.items.append(text)

    def search(self, query, k=4):
        return self.items[:k]


vectors = VectorStore()
