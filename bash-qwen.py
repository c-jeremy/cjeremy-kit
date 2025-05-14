import os
from http import HTTPStatus
from dashscope import Application
import subprocess
import ast
from colorama import Fore, Style, init

# 初始化彩色输出
init(autoreset=True)

def call_qwen(app_id, prompt, api_key=None):
    """调用百炼Qwen大模型（官方规范）"""
    response = Application.call(
        api_key=api_key or os.getenv("DASHSCOPE_API_KEY"),
        app_id=app_id,
        prompt=prompt
    )
    
    if response.status_code != HTTPStatus.OK:
        print(f'{Fore.RED}[API错误] request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}{Style.RESET_ALL}')
        return None
    return response.output.text

def extract_code(text):
    """改进的代码块提取（支持多代码块）"""
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
    
    return code_blocks if code_blocks else [{'type': 'text', 'content': text}]

def highlight_danger(code_type, code):
    """危险操作高亮提示"""
    dangers = {
        'sh': ['rm ', 'chmod', 'chown', 'sudo', '>', '|', '&', '`'],
        'python': ['os.system', 'subprocess', 'eval', 'exec', 'open(', 'import os']
    }
    
    warnings = []
    for pattern in dangers.get(code_type, []):
        if pattern in code:
            warnings.append(f"{Fore.RED}⚠️ 检测到潜在危险操作: {pattern}{Style.RESET_ALL}")
    
    return warnings

def execute_code(code_type, code):
    """执行代码并返回结果"""
    try:
        if code_type == 'python':
            # Python沙箱执行
            local_vars = {}
            exec(code, {'__builtins__': {}}, local_vars)
            return True, str(local_vars.get('result', '执行成功（无输出）'))
            
        elif code_type == 'sh':
            # Shell执行（带超时）
            result = subprocess.run(
                code,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            output = f"{result.stdout}\n{Fore.YELLOW}{result.stderr}{Style.RESET_ALL}" if result.stderr else result.stdout
            return result.returncode == 0, output
            
    except Exception as e:
        return False, f"{Fore.RED}执行崩溃: {str(e)}{Style.RESET_ALL}"

def diagnose_error(app_id, original_code, error_msg, api_key):
    """调用大模型诊断错误"""
    prompt = f"""我执行这段代码时遇到错误，请分析原因并提供修正方案：
    
原始代码：
```{original_code['type']}
{original_code['content']}
```

错误信息：
{error_msg}

请：
1. 分析错误原因
2. 提供修正后的代码（保持相同代码块格式）
3. 简要说明修改点"""
    
    return call_qwen(app_id, prompt, api_key)

def main():
    # 配置信息
    APP_ID = "YOUR_APP_ID"  # 替换为您的百炼应用ID
    API_KEY = os.getenv("DASHSCOPE_API_KEY") 
    
    print(f"{Fore.CYAN}=== AI代码执行助手 ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}输入'quit'退出 | 危险操作会标红提示{Style.RESET_ALL}\n")
    
    while True:
        try:
            user_input = input("用户请求: ").strip()
            if user_input.lower() in ('quit', 'exit'):
                break
                
            if not user_input:
                continue
                
            # 初始调用
            response_text = call_qwen(APP_ID, user_input, API_KEY)
            if not response_text:
                continue
                
            # 处理所有代码块
            for block in extract_code(response_text):
                if block['type'] == 'text':
                    print(f"\nAI回复:\n{block['content']}")
                    continue
                    
                # 显示代码和警告
                code = '\n'.join(block['content'])
                print(f"\n{Fore.GREEN}生成 {block['type'].upper()} 代码:{Style.RESET_ALL}")
                print(code)
                
                # 危险提示
                warnings = highlight_danger(block['type'], code)
                if warnings:
                    print(f"\n{Fore.RED}安全警告:{Style.RESET_ALL}")
                    print('\n'.join(warnings))
                
                # 执行确认
                confirm = input("\n是否执行？(y/n/r重试/q退出): ").lower()
                if confirm == 'q':
                    return
                elif confirm == 'r':
                    continue
                elif confirm != 'y':
                    break
                    
                # 执行代码
                success, output = execute_code(block['type'], code)
                print(f"\n{Fore.CYAN}=== 执行结果 ==={Style.RESET_ALL}")
                print(output)
                
                # 错误诊断流程
                if not success:
                    retry = input(f"{Fore.RED}执行失败，是否尝试修复？(y/n): {Style.RESET_ALL}").lower()
                    if retry == 'y':
                        print(f"{Fore.BLUE}正在诊断问题...{Style.RESET_ALL}")
                        diagnosis = diagnose_error(
                            APP_ID,
                            {'type': block['type'], 'content': code},
                            output,
                            API_KEY
                        )
                        if diagnosis:
                            print(f"\n{Fore.GREEN}诊断建议:{Style.RESET_ALL}")
                            print(diagnosis)
                            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}已中断当前操作{Style.RESET_ALL}")
            continue
        except Exception as e:
            print(f"{Fore.RED}系统错误: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
