from core.classifier import EARSClassifier

class PromptBuilder:
    """
    Builds structured prompts for the LLM based on the EARS requirement.
    """
    
    @staticmethod
    def build_prompt(requirement_text: str, context_text: str = None) -> str:
        classification = EARSClassifier.classify(requirement_text)
        
        base_instructions = (
            "You are an expert Requirements Engineer. Your task is to convert the following "
            "EARS (Easy Approach to Requirements Syntax) requirement into standard Gherkin format.\n\n"
            "Constraints:\n"
            "1. Output ONLY the Gherkin format (Feature, Scenario, Given, When, Then).\n"
            "2. Do not include any explanations, markdown code blocks, or extra text.\n"
            "3. Ensure the intent of the requirement is perfectly preserved.\n\n"
        )
        
        classification_hint = f"The input requirement has been classified as: {classification}.\n"
        if classification == "Event-driven":
            classification_hint += "Focus heavily on the triggering event (WHEN) as the 'When' step in Gherkin.\n"
        elif classification == "State-driven":
            classification_hint += "Focus heavily on the system state (WHILE) as the 'Given' step in Gherkin.\n"
        elif classification == "Optional":
            classification_hint += "Focus on the condition (IF/THEN) ensuring it's properly handled in 'Given' or 'When'.\n"
            
        context_section = ""
        if context_text and context_text.strip():
            context_section = f"### System Context / Reference Material:\n{context_text}\n\n"
            
        prompt = (
            f"{base_instructions}"
            f"{classification_hint}\n"
            f"{context_section}"
            f"Input EARS Requirement:\n"
            f"\"{requirement_text}\"\n\n"
            f"Gherkin Output:"
        )
        
        return prompt
