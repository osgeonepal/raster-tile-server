from typing import (
    Any,
    Optional,
    Sequence,
)
from abc import ABC, abstractmethod


class RasterStore(ABC):
    """Abstract base class for all raster backends.

    Defines a common interface for all raster backends."""

    @abstractmethod
    # TODO: add accurate signature if mypy ever supports conditional return types
    def get_raster_tile(
        self,
        path: str,
        *,
        tile_bounds: Optional[Sequence[float]] = None,
        tile_size: Sequence[int] = (256, 256),
        preserve_values: bool = False,
        asynchronous: bool = False,
    ) -> Any:
        """Load a raster tile with given path and bounds."""
        pass

    