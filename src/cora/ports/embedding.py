"""The one numeric step in the pipeline: text to vectors."""

from typing import Protocol


class Embedder(Protocol):
    """Whatever turns text into the vectors an index is searched by.

    One embedder does both sides of a search: a query and the chunks it is matched
    against have to be measured the same way to be comparable at all.
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        """One vector per text, in the order the texts were given.

        Raises:
            EmbeddingError: The model could not be loaded or could not run.
        """
        ...
