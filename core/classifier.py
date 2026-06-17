import re

class EARSClassifier:
    """
    Classifies EARS requirements into their specific types to aid prompt engineering.
    """
    
    @staticmethod
    def classify(requirement_text: str) -> str:
        text = requirement_text.strip().upper()
        
        # Check for complex patterns first
        if "IF" in text and "THEN" in text:
            if "WHEN" in text or "WHILE" in text or "WHERE" in text:
                return "Complex"
        
        # Check individual patterns
        if text.startswith("WHEN"):
            return "Event-driven"
        elif text.startswith("WHILE"):
            return "State-driven"
        elif text.startswith("WHERE"):
            return "Feature-driven"
        elif "IF" in text and "THEN" in text:
            return "Optional"
        
        return "Ubiquitous"
