class PressurePrinter:
    """"Helper class for visualizing values graphically on console"""

    # Width to print
    width: int = 80
    # Value for the center character in the printout
    center: float = 0
    # range for the entire printout
    range: float = 100_00

    def calculate_position(self, value: float) -> int:
        offset = float(value - self.center)

        # normalize to unit scale of the range
        relative = offset * (1.0 / self.range)
        # normalize to unit scale from 0-1
        relative += 0.5
        relative = min(relative, 1)
        relative = max(relative, 0)

        charpos = self.width * relative
        return round(charpos)

    def print_value(self, value: float):
        charpos = self.calculate_position(value)
        before = "-" * charpos
        after = "-" * (self.width - charpos)
        print(before + "|" + after, end='')
        print(format(value, '06f'), end='')
        print()
