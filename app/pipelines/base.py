from abc import ABC, abstractmethod
from app.services.ingestion_service import IngestionService


class BasePipeline(ABC):
    """
    Abstract Base Class for all pipelines.
    A pipeline orchestrates calls to a service.
    """

    def __init__(self, service: IngestionService):
        self.service = service

    @abstractmethod
    async def run(self, **kwargs):
        """Execute the pipeline's workflow."""
        pass
