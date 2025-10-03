import sys
from datetime import datetime
from functools import wraps

import psutil
import platform
import subprocess

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

current_date = datetime.now().strftime("%Y-%m-%d-%H:%M")

console = Console()

def capture_output(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):

        original_stdout = sys.stdout

        try:
            with open(f'{current_date}-scan.txt', 'w', encoding='utf-8') as f:
                class DualOutput:
                    def write(self, text):
                        original_stdout.write(text)  # В терминал
                        f.write(text)  # В файл
                        f.flush()

                    def flush(self):
                        original_stdout.flush()
                        f.flush()

                sys.stdout = DualOutput()
                result = func(*args, **kwargs)
                return result
        finally:
            sys.stdout = original_stdout
            print("\nОтчет обновлен")

    return _wrapper


def get_environment_info():

    info = {
        'platform': {
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'python': platform.python_version()
        }
    }
    print(f"    ОС: {info.get('platform').get('system')}")
    print(f"    Версия ядра: {info.get('platform').get('release')}")
    print(f"    Архитектура: {info.get('platform').get('machine')}")
    print(f"    Версия python: {info.get('platform').get('python')}")

    table = Table(title="\nОтчет о состоянии системы")

    table.add_column("Паратметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="magenta")

    table.add_row("OC", f"{info.get('platform').get('system')}")
    table.add_row("Версия ядра", f"{info.get('platform').get('release')}")
    table.add_row("Архитектура", f"{info.get('platform').get('machine')}")
    table.add_row("Версия python", f"{info.get('platform').get('python')}")

    console.print(table)

def processes_counter():

    ps = subprocess.Popen(
        ['ps', 'aux'],
        stdout=subprocess.PIPE
    )
    count = subprocess.Popen(
        ['wc', '-l'],
        stdin=ps.stdout,
        stdout=subprocess.PIPE,
        text=True
    )
    count.wait()
    print(f"\nЗапущено процессов: {count.communicate()[0]}")


def users_processes_counter():

    processes_by_user = {}
    total_processes = 0
    usernames = []

    for process in psutil.process_iter(['username']):
        try:
            username = process.info['username']
            processes_by_user[username] = processes_by_user.get(username, 0) + 1
            total_processes += 1
            usernames.append(username)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    print(f"\nЗапущено процессов (доп проверка): {total_processes}\n")
    print(f"Пользователи системы: {set(usernames)}")

    table = Table(title="\nПользовательских процессов")

    table.add_column("Пользователь", style="cyan", no_wrap=True)
    table.add_column("Количество процессов", style="magenta")

    print("Пользовательских процессов:")
    for username, count in processes_by_user.items():
        table.add_row(f"{username}", f"{count}")
    console.print(table)


def system_usage():

    for process in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        pass

    top_process_mem = None
    top_process_cpu = None
    max_memory = 0
    max_cpu = 0

    freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()

    mem_panel = Panel(f"\nВсго памяти используется: {memory.total / (1024 ** 3):.1f} GB - {memory.percent}%",
                      title="MEMORY",
                      border_style="blue"
                      )
    console.print(mem_panel)
    cpu_panel = Panel(f"Всего CPU используется: {freq.current:.0f} MHz - {psutil.cpu_percent(interval=1)}%",
                      title="CPU",
                      border_style="blue"
                      )
    console.print(cpu_panel)

    for process in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            memory_usage = process.info['memory_info'].rss
            if memory_usage > max_memory:
                max_memory = memory_usage
                top_process_mem = process.info

            cpu_usage = process.info['cpu_percent']
            if cpu_usage > max_cpu:
                max_cpu = cpu_usage
                top_process_cpu = process.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if top_process_mem:
        memory_mb = max_memory / (1024 * 1024)
        mem_panel = Panel(f"Больше всего памяти использует: {top_process_mem.get('name', 'N/A')[:10]}/PID:{top_process_mem.get('pid', 'N/A')} - {memory_mb:.2f} MB",
                          title="BIGGEST MEMORY",
                          border_style="blue"
                          )
        console.print(mem_panel)
    if top_process_cpu:
        cpu_panel = Panel(f"Больше всего CPU использует: {top_process_cpu.get('name', 'N/A')[:10]}/PID:{top_process_cpu.get('pid', 'N/A')} - {max_cpu}%",
                          title="BIGGEST CPU",
                          border_style="blue"
                          )
        console.print(cpu_panel)


@capture_output
def main():

    get_environment_info()
    processes_counter()
    users_processes_counter()
    system_usage()


if __name__ == "__main__":
    main()