class RepairCost:
    def __init__(self, name, price_range, unit):
        self.name = name
        self.price_range = price_range  # Tuple or list (min, max)
        self.unit = unit  # e.g., "each", "sq. ft.", "linear ft.", etc.

    def average_cost(self):
        return sum(self.price_range) / len(self.price_range)

    def __str__(self):
        return f"{self.name}: ${self.price_range[0]} - ${self.price_range[1]} per {self.unit}"
