import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from jarvis_assistant.agents.language_executor import LanguageExecutor

@pytest.fixture
def temp_code_dir(tmp_path):
    """Create a temporary directory for code files"""
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    return code_dir

@pytest.fixture
async def language_executor(temp_code_dir):
    """Create a language executor instance for testing"""
    config = {
        'formatters': {
            'python': 'black',
            'javascript': 'prettier',
            'typescript': 'prettier'
        },
        'linters': {
            'python': ['pylint', 'mypy'],
            'javascript': ['eslint'],
            'typescript': ['tslint']
        }
    }
    executor = LanguageExecutor(config)
    yield executor

@pytest.mark.asyncio
async def test_language_detection(language_executor, temp_code_dir):
    """Test language detection"""
    # Python file
    py_file = temp_code_dir / "test.py"
    py_file.write_text("def hello(): print('Hello')")
    
    lang = await language_executor.detect_language(str(py_file))
    assert lang == "python"
    
    # JavaScript file
    js_file = temp_code_dir / "test.js"
    js_file.write_text("function hello() { console.log('Hello'); }")
    
    lang = await language_executor.detect_language(str(js_file))
    assert lang == "javascript"

@pytest.mark.asyncio
async def test_code_formatting(language_executor, temp_code_dir):
    """Test code formatting"""
    # Python code
    py_code = "def hello(  ):\n  print(   'Hello'   )"
    formatted_py = await language_executor.format_code(
        py_code,
        "python"
    )
    assert "def hello():" in formatted_py
    
    # JavaScript code
    js_code = "function hello(   ){console.log(  'Hello'   )}"
    formatted_js = await language_executor.format_code(
        js_code,
        "javascript"
    )
    assert "function hello() {" in formatted_js

@pytest.mark.asyncio
async def test_static_analysis(language_executor, temp_code_dir):
    """Test static code analysis"""
    # Python code with type hints
    py_code = """
    def greet(name: str) -> str:
        x = 5
        return 'Hello ' + name + x
    """
    
    analysis = await language_executor.analyze_code(
        py_code,
        "python"
    )
    assert len(analysis['errors']) > 0
    assert any('type' in err.lower() for err in analysis['errors'])

@pytest.mark.asyncio
async def test_code_completion(language_executor):
    """Test code completion"""
    # Python code completion
    py_code = """
    class Person:
        def __init__(self, name):
            self.name = name
            
    person = Person('John')
    person.
    """
    
    completions = await language_executor.get_completions(
        py_code,
        "python",
        position=(7, 11)  # After person.
    )
    
    assert any(c['text'] == 'name' for c in completions)

@pytest.mark.asyncio
async def test_code_conversion(language_executor):
    """Test code conversion between languages"""
    # Python to JavaScript
    py_code = """
    def calculate_sum(numbers):
        return sum(numbers)
    
    result = calculate_sum([1, 2, 3, 4, 5])
    print(result)
    """
    
    js_code = await language_executor.convert_code(
        py_code,
        source_lang="python",
        target_lang="javascript"
    )
    
    assert "function calculateSum" in js_code
    assert "reduce" in js_code
    assert "console.log" in js_code

@pytest.mark.asyncio
async def test_syntax_validation(language_executor):
    """Test syntax validation"""
    # Valid Python code
    valid_py = "def hello(): return 'Hello'"
    result = await language_executor.validate_syntax(
        valid_py,
        "python"
    )
    assert result['valid'] is True
    
    # Invalid Python code
    invalid_py = "def hello() return 'Hello'"
    result = await language_executor.validate_syntax(
        invalid_py,
        "python"
    )
    assert result['valid'] is False
    assert len(result['errors']) > 0

@pytest.mark.asyncio
async def test_dependency_analysis(language_executor, temp_code_dir):
    """Test dependency analysis"""
    # Python file with imports
    py_file = temp_code_dir / "main.py"
    py_file.write_text("""
    import os
    from datetime import datetime
    import custom_module
    from .local_module import helper
    
    def main():
        pass
    """)
    
    deps = await language_executor.analyze_dependencies(str(py_file))
    
    assert "os" in deps['stdlib']
    assert "datetime" in deps['stdlib']
    assert "custom_module" in deps['external']
    assert "local_module" in deps['local']

@pytest.mark.asyncio
async def test_code_metrics(language_executor):
    """Test code metrics calculation"""
    py_code = """
    def complex_function(x):
        result = 0
        for i in range(x):
            if i % 2 == 0:
                if i % 3 == 0:
                    result += i
                else:
                    result -= i
            elif i % 5 == 0:
                result *= 2
        return result
    """
    
    metrics = await language_executor.calculate_metrics(
        py_code,
        "python"
    )
    
    assert metrics['complexity'] > 1
    assert metrics['loc'] > 5
    assert 'maintainability' in metrics

@pytest.mark.asyncio
async def test_error_handling(language_executor):
    """Test error handling"""
    # Invalid language
    with pytest.raises(ValueError):
        await language_executor.format_code(
            "code",
            "invalid_lang"
        )
    
    # Invalid code
    with pytest.raises(SyntaxError):
        await language_executor.analyze_code(
            "def invalid syntax",
            "python"
        )
