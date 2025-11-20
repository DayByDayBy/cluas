from typing import Dict, List
from src.characters.corvus import CorvusMCP

class CouncilOrchestrator:
    """
    Manages the council of agents and orchestrates the research process.
    """

    def __init__(self):
        """
        Initializes the orchestrator and the council members.
        For now, only Corvus is instantiated.
        """
        self.corvus = CorvusMCP()
        # In the future, other agents like Magpie, Raven, etc., will be initialized here.

    def process_query(self, query: str) -> List[Dict]:
        """
        Processes a user query by dispatching it to the relevant agents.

        For this initial implementation, it only calls Corvus.
        
        Args:
            query: The user's research query.

        Returns:
            A list of dictionaries containing the search results.
        """
        # In the future, this method will involve more complex logic,
        # such as selecting which agent to call first, facilitating debate,
        # and synthesizing results.
        
        # For now, we just call Corvus directly.
        results = self.corvus.search_papers(query)
        
        return results

# Example usage (for testing):
# if __name__ == "__main__":
#     orchestrator = CouncilOrchestrator()
#     search_results = orchestrator.process_query("corvid cognition")
#     for paper in search_results:
#         print(f"Title: {paper['title']}")
#         print(f"Authors: {paper['authors']}")
#         print("-" * 20)
