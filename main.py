import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import logging
from colorama import init, Fore, Style
from integration.pipeline import EngramPipeline
from utils import config

# Initialize colorama
init()

# Ensure log directory exists
if not config.LOG_DIR.exists():
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging to file only (keep CLI clean)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=str(config.LOG_DIR / "session.log")
)

def print_system(msg):
    print(f"{Fore.CYAN}[ENGRAM]{Style.RESET_ALL} {msg}")

def print_ai(msg):
    print(f"{Fore.GREEN}[AI]{Style.RESET_ALL} {msg}")

def print_memory(abs_obj):
    print(f"{Fore.YELLOW}  📎 [{abs_obj.id[:6]}] (Q:{abs_obj.quality_score:.2f}) {abs_obj.content[:80]}...{Style.RESET_ALL}")

def main():
    print(f"{Fore.CYAN}========================================")
    print(f"   🧠 ENGRAM MEMORY SYSTEM v1.0")
    print(f"========================================{Style.RESET_ALL}")
    print("Initializing Core Systems...")
    
    try:
        pipeline = EngramPipeline()
        print_system("System Online. Memory Core Active.")
        print_system(f"Storage: {config.CHROMA_PERSIST_DIRECTORY}")
    except Exception as e:
        print(f"{Fore.RED}CRITICAL ERROR: {e}{Style.RESET_ALL}")
        return

    print_system("Type '/bye' to exit, '/ingest <text>' to add memory, '/learn' to run maintenance.")
    print("")

    while True:
        try:
            user_input = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['/bye', '/exit', '/quit']:
                print_system("Shutting down...")
                break
                
            if user_input.startswith('/ingest '):
                text = user_input[8:]
                print_system("Ingesting...")
                pipeline.ingest(text, source="user_cli")
                print_system("Memory stored.")
                continue

            if user_input.lower() == '/learn':
                print_system("Running daily maintenance (Clustering & Decay)...")
                from scripts.daily_maintenance import run_daily_maintenance
                run_daily_maintenance()
                print_system("Maintenance complete.")
                continue

            # Standard Chat Query
            print_system("Thinking...")
            
            # Peek at retrieval first for transparency
            relevant = pipeline.searcher.search(user_input, top_k=3)
            if relevant:
                print(f"{Fore.YELLOW}Recovered Memories:{Style.RESET_ALL}")
                for r in relevant:
                    print_memory(r)
            else:
                 print(f"{Fore.DIM}No relevant memories found.{Style.RESET_ALL}")

            # Generate Response
            response = pipeline.process_query(user_input)
            print_ai(response)

        except KeyboardInterrupt:
            print("")
            print_system("Shutting down...")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
