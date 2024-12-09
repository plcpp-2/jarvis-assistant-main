import asyncio
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import ast
import libcst
import autopep8
import black
import isort
import jedi
from pylint import epylint
import yapf
from prometheus_client import Counter, Histogram
import re
import json
import subprocess
from pathlib import Path

class LanguageExecutor:
    def __init__(self):
        self.logger = logging.getLogger("LanguageExecutor")
        
        # Metrics
        self.parse_counter = Counter(
            'code_parse_total',
            'Total number of code parsing operations',
            ['language', 'status']
        )
        self.transform_duration = Histogram(
            'code_transform_duration_seconds',
            'Code transformation duration in seconds',
            ['language', 'operation']
        )

    async def parse_python(
        self,
        code: str,
        mode: str = 'exec'
    ) -> Dict[str, Any]:
        """Parse Python code and extract information"""
        try:
            # Parse with ast
            tree = ast.parse(code, mode=mode)
            
            # Extract information
            info = {
                'imports': [],
                'functions': [],
                'classes': [],
                'variables': [],
                'calls': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    info['imports'].extend(n.name for n in node.names)
                elif isinstance(node, ast.ImportFrom):
                    info['imports'].append(f"{node.module}.{node.names[0].name}")
                elif isinstance(node, ast.FunctionDef):
                    info['functions'].append({
                        'name': node.name,
                        'args': [a.arg for a in node.args.args],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    })
                elif isinstance(node, ast.ClassDef):
                    info['classes'].append({
                        'name': node.name,
                        'bases': [b.id for b in node.bases if isinstance(b, ast.Name)],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    })
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        info['calls'].append(node.func.id)

            self.parse_counter.labels(
                language='python',
                status='success'
            ).inc()
            
            return info

        except Exception as e:
            self.logger.error(f"Python parsing failed: {str(e)}")
            self.parse_counter.labels(
                language='python',
                status='error'
            ).inc()
            raise

    async def format_python(
        self,
        code: str,
        style: str = 'black'
    ) -> str:
        """Format Python code using various formatters"""
        try:
            start_time = datetime.now()
            
            if style == 'black':
                formatted = black.format_str(
                    code,
                    mode=black.FileMode()
                )
            elif style == 'autopep8':
                formatted = autopep8.fix_code(code)
            elif style == 'yapf':
                formatted = yapf.yapf_api.FormatCode(code)[0]
            else:
                raise ValueError(f"Unsupported style: {style}")

            # Sort imports
            formatted = isort.code(formatted)
            
            duration = (datetime.now() - start_time).total_seconds()
            self.transform_duration.labels(
                language='python',
                operation='format'
            ).observe(duration)
            
            return formatted

        except Exception as e:
            self.logger.error(f"Python formatting failed: {str(e)}")
            raise

    async def analyze_python(
        self,
        code: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze Python code for issues and metrics"""
        try:
            # Write code to temporary file if path not provided
            if not path:
                path = "temp.py"
                with open(path, 'w') as f:
                    f.write(code)

            # Run pylint
            (pylint_stdout, pylint_stderr) = epylint.py_run(
                path,
                return_std=True
            )
            
            issues = []
            for line in pylint_stdout.readlines():
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        issues.append({
                            'line': parts[1],
                            'type': parts[2],
                            'message': ':'.join(parts[3:]).strip()
                        })

            # Get complexity metrics
            tree = ast.parse(code)
            complexity = {
                'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'imports': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
                'lines': len(code.splitlines())
            }

            return {
                'issues': issues,
                'complexity': complexity
            }

        except Exception as e:
            self.logger.error(f"Python analysis failed: {str(e)}")
            raise

    async def get_python_completions(
        self,
        code: str,
        position: tuple,
        path: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get code completions for Python"""
        try:
            script = jedi.Script(code, path=path)
            completions = script.complete(*position)
            
            return [{
                'name': c.name,
                'type': c.type,
                'description': c.description,
                'docstring': c.docstring()
            } for c in completions]

        except Exception as e:
            self.logger.error(f"Python completion failed: {str(e)}")
            raise

    async def parse_javascript(
        self,
        code: str
    ) -> Dict[str, Any]:
        """Parse JavaScript code and extract information"""
        try:
            # Use esprima-python for parsing
            import esprima
            
            tree = esprima.parseScript(code)
            
            info = {
                'imports': [],
                'functions': [],
                'classes': [],
                'variables': [],
                'calls': []
            }
            
            def visit(node):
                if node.type == 'ImportDeclaration':
                    info['imports'].append(node.source.value)
                elif node.type == 'FunctionDeclaration':
                    info['functions'].append({
                        'name': node.id.name,
                        'params': [p.name for p in node.params]
                    })
                elif node.type == 'ClassDeclaration':
                    info['classes'].append({
                        'name': node.id.name,
                        'superClass': node.superClass.name if node.superClass else None
                    })
                elif node.type == 'CallExpression':
                    if hasattr(node.callee, 'name'):
                        info['calls'].append(node.callee.name)

            for node in tree.body:
                visit(node)

            self.parse_counter.labels(
                language='javascript',
                status='success'
            ).inc()
            
            return info

        except Exception as e:
            self.logger.error(f"JavaScript parsing failed: {str(e)}")
            self.parse_counter.labels(
                language='javascript',
                status='error'
            ).inc()
            raise

    async def format_javascript(
        self,
        code: str,
        style: str = 'prettier'
    ) -> str:
        """Format JavaScript code"""
        try:
            start_time = datetime.now()
            
            if style == 'prettier':
                # Use prettier through node
                process = await asyncio.create_subprocess_shell(
                    'npx prettier --stdin-filepath input.js',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate(code.encode())
                
                if process.returncode != 0:
                    raise RuntimeError(f"Prettier failed: {stderr.decode()}")
                
                formatted = stdout.decode()
            else:
                raise ValueError(f"Unsupported style: {style}")

            duration = (datetime.now() - start_time).total_seconds()
            self.transform_duration.labels(
                language='javascript',
                operation='format'
            ).observe(duration)
            
            return formatted

        except Exception as e:
            self.logger.error(f"JavaScript formatting failed: {str(e)}")
            raise

    async def analyze_typescript(
        self,
        code: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze TypeScript code"""
        try:
            if not path:
                path = "temp.ts"
                with open(path, 'w') as f:
                    f.write(code)

            # Run tsc for type checking
            process = await asyncio.create_subprocess_shell(
                f'npx tsc --noEmit {path}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            issues = []
            for line in stderr.decode().splitlines():
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        issues.append({
                            'file': parts[0],
                            'line': parts[1],
                            'column': parts[2],
                            'message': ':'.join(parts[3:]).strip()
                        })

            return {
                'issues': issues
            }

        except Exception as e:
            self.logger.error(f"TypeScript analysis failed: {str(e)}")
            raise

    async def convert_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Convert code between languages using OpenAI's GPT"""
        try:
            # This is a placeholder for code conversion logic
            # In a real implementation, you would use a language model
            # or specific conversion tools
            raise NotImplementedError(
                "Code conversion not implemented. Use a language model API."
            )

        except Exception as e:
            self.logger.error(f"Code conversion failed: {str(e)}")
            raise

    async def detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        try:
            # Check for common language indicators
            indicators = {
                'python': [
                    r'import \w+',
                    r'from \w+ import',
                    r'def \w+\(',
                    r'class \w+:',
                    r'print\('
                ],
                'javascript': [
                    r'const \w+',
                    r'let \w+',
                    r'function \w+\(',
                    r'class \w+ {',
                    r'console\.log\('
                ],
                'typescript': [
                    r'interface \w+',
                    r'type \w+',
                    r': \w+\[\]',
                    r'<\w+>'
                ],
                'java': [
                    r'public class',
                    r'private \w+',
                    r'System\.out\.println',
                    r'@Override'
                ]
            }
            
            scores = {lang: 0 for lang in indicators}
            
            for lang, patterns in indicators.items():
                for pattern in patterns:
                    if re.search(pattern, code):
                        scores[lang] += 1

            # Get language with highest score
            detected = max(scores.items(), key=lambda x: x[1])[0]
            
            if scores[detected] == 0:
                return 'unknown'
                
            return detected

        except Exception as e:
            self.logger.error(f"Language detection failed: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        executor = LanguageExecutor()
        
        # Test Python parsing
        code = """
import math

def calculate_area(radius):
    return math.pi * radius ** 2

class Circle:
    def __init__(self, radius):
        self.radius = radius
        
    def area(self):
        return calculate_area(self.radius)
"""
        
        info = await executor.parse_python(code)
        print("Python code info:", json.dumps(info, indent=2))
        
        # Test formatting
        formatted = await executor.format_python(code)
        print("\nFormatted Python code:")
        print(formatted)
        
        # Test analysis
        analysis = await executor.analyze_python(code)
        print("\nPython code analysis:", json.dumps(analysis, indent=2))

    asyncio.run(main())
