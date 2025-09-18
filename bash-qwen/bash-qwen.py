import os
from http import HTTPStatus
from dashscope import Application
import subprocess
import ast
from colorama import Fore, Style, init

# Init colorized output
init(autoreset=True)

class CodeAgent:
    def __init__(self, app_id, api_key=None):
        self.app_id = app_id
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.max_retries = 5  # Maximum diagnosis attempt times
        
    def call_llm(self, prompt):
        """Call the LLM from Bailian (dashscope)"""
        response = Application.call(
            api_key=self.api_key,
            app_id=self.app_id,
            prompt=prompt
        )
        if response.status_code != HTTPStatus.OK:
            print(f'{Fore.RED}[API Error] {response.message}{Style.RESET_ALL}')
            return None
        return response.output.text
    
    def extract_code(self, text):
        """Extract code from the LLM response"""
        code_blocks = []
        current_block = None
        
        for line in text.split('\n'):
            if line.startswith('```python'):
                current_block = {'type': 'python', 'content': []}
            elif line.startswith('```sh'):
                current_block = {'type': 'sh', 'content': []}
            elif line.startswith('```') and current_block:
                code_blocks.append(current_block)
                current_block = None
            elif current_block:
                current_block['content'].append(line)
            elif line.strip() and not code_blocks:
                # retain those lines that aren't code
                code_blocks.append({'type': 'text', 'content': [line]})
        
        return code_blocks
    
    def diagnose_error(self, original_code, error_msg, retry_count=0):
        """Diagnose Issues"""
        prompt = f"""Please fix the following code: 
        
Original Code:
```{original_code['type']}
{original_code['content']}
```

Returns Error: 
{error_msg}

Please: (1) keep the functionalities intact; (2) output the reviewed & fixed code in similar format.
"""
        return self.call_llm(prompt)
    
    def highlight_dangers(self, code_type, code):
        """Highlight and warn the user when Dangerous Code was obtained"""
        danger_rules = {
            'sh': [
                ('rm -rf', Fore.RED + '⚠️ DANGER: Deletion (force)'),
                ('sudo', Fore.YELLOW + '⚠️ WARNING: sudo action'),
                ('>', Fore.YELLOW + '⚠️ WARNING: File Redirection')
            ],
            'python': [
                ('os.system', Fore.RED + '⚠️ DANGER: Calling system command in Python'),
                ('subprocess', Fore.YELLOW + '⚠️ WARNING: LLM attempts to call subprocess')
            ]
        }
        
        warnings = []
        for pattern, message in danger_rules.get(code_type, []):
            if pattern in code:
                warnings.append(message + Style.RESET_ALL)
        
        return warnings
    
    def execute_code(self, code_type, code):
        """Execute and return the result"""
        try:
            if code_type == 'python':
                # Safe sandbox
                safe_globals = {'__builtins__': {'None': None, 'False': False, 'True': True}}
                local_vars = {}
                exec(code, safe_globals, local_vars)
                return True, str(local_vars.get('result', '执行成功（无输出）'))
                
            elif code_type == 'sh':
                # Shell Execution (safe)
                result = subprocess.run(
                    code,
                    shell=True,
                    executable='/bin/bash', # edit here to change to your favorite shell
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                output = []
                if result.stdout: output.append(result.stdout)
                if result.stderr: output.append(Fore.YELLOW + result.stderr)
                return result.returncode == 0, '\n'.join(output)
                
        except subprocess.TimeoutExpired:
            return False, f"{Fore.RED}ERROR: TIMEOUT{Style.RESET_ALL}"
        except Exception as e:
            return False, f"{Fore.RED}EXECUTION FAILURE: {type(e).__name__}: {str(e)}{Style.RESET_ALL}"
    
    def interactive_execution(self, code_blocks, retry_count=0):
        """Interactive Exec with diagnose"""
        for block in code_blocks:
            if block['type'] == 'text':
                print(f"\n{Fore.CYAN}AI: {Style.RESET_ALL} {block['content'][0]}")
                continue
                
            code = '\n'.join(block['content'])
            print(f"\n{Fore.GREEN}Generated {block['type'].upper()} Code:{Style.RESET_ALL}")
            print(code)
            
            # 显示危险警告
            warnings = self.highlight_dangers(block['type'], code)
            if warnings:
                print(f"{Fore.MAGENTA}Security Scanner:{Style.RESET_ALL}")
                print('\n'.join(warnings))
            
            while True:
                choice = input("\n[E]xecute [S]kip [Q]uit: ").lower()
                if choice == 'q':
                    return False
                elif choice == 's':
                    break
                elif choice == 'e':
                    success, output = self.execute_code(block['type'], code)
                    print(f"\n{Fore.BLUE}=== Execution result ==={Style.RESET_ALL}")
                    print(output)
                    
                    if not success and retry_count < self.max_retries:
                        retry = input(f"{Fore.RED}Execution failed. Auto Fix?(y/n): {Style.RESET_ALL}").lower()
                        if retry == 'y':
                            print(f"{Fore.BLUE}Diagnosing...{Style.RESET_ALL}")
                            diagnosis = self.diagnose_error(
                                {'type': block['type'], 'content': code},
                                output,
                                retry_count
                            )
                            if diagnosis:
                                new_blocks = self.extract_code(diagnosis)
                                return self.interactive_execution(new_blocks, retry_count + 1)
                    break
        return True

def main():
    # Configuration
    APP_ID = "b35fb890210d4372b6a323193597de6d"  # Your Dashscope APP_ID
    agent = CodeAgent(APP_ID)
    
    print(f"{Fore.CYAN}=== Bash-Qwen ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}https://github.com/c-jeremy/cjeremy-kit{Style.RESET_ALL}")
    
    while True:
        try:
            user_input = input("\nPrompt(or enter quit):").strip()
            if user_input.lower() in ('quit', 'exit'):
                break
                
            if not user_input:
                continue
                
            # Call the LLM
            response = agent.call_llm(user_input)
            if not response:
                continue
                
            # Execution
            code_blocks = agent.extract_code(response)
            agent.interactive_execution(code_blocks)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Action Paused.{Style.RESET_ALL}")
            continue
        except Exception as e:
            print(f"{Fore.RED}FATAL ERROR: {type(e).__name__}: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
