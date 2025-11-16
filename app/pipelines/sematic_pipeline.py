from app.pipelines.base import BasePipeline
from app.services.semantic_service import SemanticService


class SemanticAnalysisPipeline(BasePipeline):
    """
    This pipeline runs *only* the expensive AI semantic analysis.
    It assumes the database and metadata tables already exist.
    """

    def __init__(self, service: SemanticService):
        self.service = service  # Note: This takes a SemanticService

    async def run(self, **kwargs):
        print("--- Starting Semantic Analysis Pipeline ---")
        try:
            # Connect is part of the adapter, which the service holds
            await self.service.adapter.connect(recreate=False)

            # Run the main analysis
            await self.service.run_semantic_analysis()

        except Exception as e:
            print(f"[ERROR] Semantic Analysis pipeline failed: {e}")
            raise
        finally:
            await self.service.adapter.close()

        print("--- Semantic Analysis Pipeline Complete ---")
