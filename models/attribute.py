class Attribute:
    def __init__(
        self,
        attr_name: str = "",
        attr_type: int = -1,
        attr_value: str = "",
        size: int = 0,
        decimal: int = 0,
    ) -> None:
        self.attr_name = attr_name
        self.attr_type = (
            attr_type  # 0-Nulo, 1-String, 2-Integer, 3-Double, 4-Logical, 5-FTDate.
        )
        self.attr_value = attr_value
        self.size = size
        self.decimal = decimal
