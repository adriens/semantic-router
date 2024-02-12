import numpy as np
from typing import List, Any, Tuple, Optional
from semantic_router.linear import similarity_matrix, top_scores
from semantic_router.index.base import BaseIndex


class LocalIndex(BaseIndex):

    def __init__(self):
        super().__init__() 
        self.type = "local"

    class Config:  # Stop pydantic from complaining about  Optional[np.ndarray] type hints.
        arbitrary_types_allowed = True

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str]):
        embeds = np.array(embeddings)  # type: ignore
        routes_arr = np.array(routes)
        utterances_arr = np.array(utterances)
        if self.index is None:
            self.index = embeds  # type: ignore
            self.routes = routes_arr
            self.utterances = utterances_arr
        else:
            self.index = np.concatenate([self.index, embeds])
            self.routes = np.concatenate([self.routes, routes_arr])
            self.utterances = np.concatenate([self.utterances, utterances_arr])

    def _get_indices_for_route(self, route_name: str):
        """Gets an array of indices for a specific route.
        """
        idx = [
            i for i, route in enumerate(self.routes)
            if route == route_name
        ]
        return idx

    def delete(self, route_name: str):
        """
        Delete all records of a specific route from the index.
        """
        if self.index is not None:
            delete_idx = self._get_indices_for_route(route_name=route_name)
            self.index = np.delete(self.index, delete_idx, axis=0)
            self.routes = np.delete(self.routes, delete_idx, axis=0)
            self.utterances = np.delete(self.utterances, delete_idx, axis=0)

    def describe(self):
        return {
            "type": self.type,
            "dimensions": self.index.shape[1] if self.index is not None else 0,
            "vectors": self.index.shape[0] if self.index is not None else 0
        }

    def query(self, vector: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, List[str]]:
        """
        Search the index for the query and return top_k results.
        """
        if self.index is None:
            raise ValueError("Index is not populated.")
        sim = similarity_matrix(vector, self.index)
        # extract the index values of top scoring vectors
        scores, idx = top_scores(sim, top_k)
        # get routes from index values
        route_names = self.routes[idx].copy()
        return scores, route_names
    
    def delete_index(self):
        """
        Deletes the index, effectively clearing it and setting it to None.
        """
        self.index = None