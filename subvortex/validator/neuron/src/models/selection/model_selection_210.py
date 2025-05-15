from subvortex.validator.core.database import get_field_value
from subvortex.validator.neuron.src.models.selection import SelectionModel200


class SelectionModel(SelectionModel200):
    """
    Versioned model for storing and retrieving hotkey statistics from Redis.
    This is version 2.1.0 of the model.
    """

    version = "2.1.0"

    def redis_key(self, ss58_address: str) -> str:
        return f"sv:selection:{ss58_address}"
