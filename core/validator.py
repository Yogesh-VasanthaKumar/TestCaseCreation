class GherkinValidator:
    """
    Validates the structure of generated Gherkin output.
    """
    
    @staticmethod
    def validate(gherkin_text: str) -> tuple[bool, list[str]]:
        """
        Returns a tuple of (is_valid, list_of_errors).
        """
        errors = []
        if not gherkin_text or not gherkin_text.strip():
            return False, ["Output is empty."]
            
        text = gherkin_text.lower()
        
        if "feature:" not in text:
            errors.append("Missing 'Feature:' keyword.")
        if "scenario:" not in text and "scenario outline:" not in text:
            errors.append("Missing 'Scenario:' or 'Scenario Outline:' keyword.")
            
        # These are usually present, but optional depending on strictness. We'll enforce a basic flow.
        if "given " not in text and "\ngiven " not in text:
            errors.append("Missing 'Given' step.")
        if "when " not in text and "\nwhen " not in text:
            errors.append("Missing 'When' step.")
        if "then " not in text and "\nthen " not in text:
            errors.append("Missing 'Then' step.")
            
        return len(errors) == 0, errors
