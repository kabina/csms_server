import sys

class TransactionGenerator:
    def __init__(self):
        self.max_value = sys.maxsize
        self.current_value = 1

    def get_next_value(self):
        result = self.current_value
        self.current_value += 1
        if self.current_value > self.max_value:
            self.current_value = 1
        return result