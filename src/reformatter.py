from src.standard_reformatter import StandardTestCaseReformatter

class TestCaseReformatter:
    """
    Wrapper for StandardTestCaseReformatter to maintain backward compatibility in app.py
    while providing the new Universal Standard Format output.
    """
    def __init__(self, extractor=None, model_name="qwen2:0.5b"):
        # StandardTestCaseReformatter handles its own extractor initialization
        # We always use AI for reformatting to ensure maximum fidelity as requested
        self.inner = StandardTestCaseReformatter(use_ai=True, model_name=model_name)
        
    def reformat_file(self, input_path, output_path=None):
        """
        Converts messy test case to the system's preferred Universal Standard Format.
        """
        return self.inner.reformat_file(input_path, output_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        reformatter = TestCaseReformatter()
        reformatter.reformat_file(sys.argv[1])
    else:
        print("Usage: python src/reformatter.py <INPUT_EXCEL_FILE>")
