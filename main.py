import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import logging
import threading
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

def print_reasoning(msg):
    print(f"{Fore.MAGENTA}[REASONING]{Style.RESET_ALL} {msg}")

def print_neuro(msg):
    print(f"{Fore.YELLOW}[NEURO]{Style.RESET_ALL} {msg}")

def print_memory(abs_obj):
    print(f"{Fore.YELLOW}  📎 [{abs_obj.id[:6]}] (Q:{abs_obj.quality_score:.2f}) {abs_obj.content[:80]}...{Style.RESET_ALL}")

def main():
    print(f"{Fore.CYAN}========================================")
    print(f"   🧠 ENGRAM AWAKE CORTEX v5.0")
    print(f"   Neuroscience-Grounded AI Brain")
    print(f"========================================{Style.RESET_ALL}")
    print("Initializing Core Systems...")
    
    try:
        pipeline = EngramPipeline()
        print_system("Memory Core Active.")
        
        if pipeline._reasoning_ready:
            print_system("🔬 Reasoning Engine: Online")
            print_system("🔒 Winner-Take-All Gate: Online (3-translator competition)")
            print_system("⚡ Prediction Engine: Online (Friston Free Energy)")
            print_system("🚧 Impasse Detector: Online (SOAR sub-goals)")
            print_system("🔓 Reconsolidation: Online (memory-on-recall)")
            print_system("🎵 Polyrhythmic Brain: Online")
        else:
            print_system("⚠️  Reasoning Engine: Offline (basic mode)")
        
        print_system(f"Storage: {config.CHROMA_PERSIST_DIRECTORY}")
        
        # Start background engines
        print_system("Starting background engines...")
        pipeline.start_engines()
        
        if pipeline._reasoning_ready:
            print_system("💓 Heartbeat: Running (1 Hz)")
            print_system("⚡ Awake Engine: Running (dynamic Hz)")
            print_system(f"📊 Dashboard: http://localhost:8000/brain_monitor.html")

    except Exception as e:
        print(f"{Fore.RED}CRITICAL ERROR: {e}{Style.RESET_ALL}")
        return

    print()
    print_system("Commands:")
    print_system("  /bye          — Exit")
    print_system("  /ingest <text> — Add memory")
    print_system("  /learn        — Run maintenance")
    print_system("  /status       — Full brain status")
    print_system("  /prove <stmt> — Test reasoning")
    print_system("  /impasses     — Show active impasses")
    print_system("  /predict      — Prediction engine stats")
    print_system("  /helpful      — Rate last answer as helpful")
    print_system("  /wrong        — Rate last answer as wrong")
    print_system("  /world        — Launch 3D embodied world")
    print()

    while True:
        try:
            user_input = input(f"{Fore.WHITE}> {Style.RESET_ALL}").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['/bye', '/exit', '/quit']:
                print_system("Shutting down engines...")
                pipeline.stop_engines()
                print_system("Goodbye.")
                break
                
            if user_input.startswith('/ingest '):
                text = user_input[8:]
                print_system("Ingesting through Translator Gate...")
                pipeline.ingest(text, source="user_cli")
                print_system("Memory stored ✓")
                continue

            if user_input.lower() == '/learn':
                print_system("Running daily maintenance (Clustering & Decay)...")
                from scripts.daily_maintenance import run_daily_maintenance
                run_daily_maintenance()
                print_system("Maintenance complete.")
                continue
            
            if user_input.lower() == '/status':
                _show_status(pipeline)
                continue
            
            if user_input.lower() == '/impasses':
                _show_impasses(pipeline)
                continue
            
            if user_input.lower() == '/predict':
                _show_prediction_stats(pipeline)
                continue
            
            if user_input.startswith('/prove '):
                statement = user_input[7:]
                _prove_statement(pipeline, statement)
                continue
            
            if user_input.lower() == '/helpful':
                result = pipeline.user_feedback_helpful()
                print_neuro(f"👍 {result}")
                continue
            
            if user_input.lower() == '/wrong':
                result = pipeline.user_feedback_wrong()
                print_neuro(f"👎 {result}")
                continue
            
            if user_input.lower() == '/world':
                _launch_world(pipeline)
                continue

            # Standard Chat Query — Full Neuroscience Pipeline
            print_system("Thinking...")
            
            # Show recovered memories
            relevant = pipeline.searcher.search(user_input, top_k=3)
            if relevant:
                print(f"{Fore.YELLOW}Recovered Memories:{Style.RESET_ALL}")
                for r in relevant:
                    print_memory(r)
            else:
                 print(f"{Fore.DIM}No relevant memories found.{Style.RESET_ALL}")

            # Process through full neuroscience pipeline
            response = pipeline.process_query(user_input)
            
            # Show reasoning annotation if present
            if "[Verified via first-principles" in response:
                parts = response.rsplit("\n\n[Verified", 1)
                print_ai(parts[0])
                print_reasoning(f"[Verified{parts[1]}")
            else:
                print_ai(response)
            
            # Show surprise signal if available
            if pipeline._reasoning_ready:
                stats = pipeline.prediction_engine.get_stats()
                if stats["total_predictions"] > 0:
                    recent = list(pipeline.prediction_engine.error_history)
                    if recent:
                        last = recent[-1]
                        if last.surprise > 0.3:
                            print_neuro(f"⚡ Surprise: {last.surprise:.2f} "
                                        f"(prediction error: {last.error_magnitude:.2f})")

        except KeyboardInterrupt:
            print("")
            print_system("Shutting down engines...")
            pipeline.stop_engines()
            print_system("Goodbye.")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


def _show_status(pipeline):
    """Display full brain status including neuroscience components"""
    if not pipeline._reasoning_ready:
        print_system("Reasoning not initialized.")
        return
    
    status = pipeline.awake_engine.get_status()
    health = pipeline.heartbeat.get_health()
    pred_stats = pipeline.prediction_engine.get_stats()
    imp_stats = pipeline.impasse_detector.get_stats()
    recon_stats = pipeline.reconsolidation.get_stats()
    
    mode_emoji = {"idle": "💤", "thinking":"🤔", "focused":"🔥", "sleeping":"😴"}
    
    print(f"{Fore.CYAN}{'─'*40}")
    print(f"  🧠 Brain Status (v5.0)")
    print(f"{'─'*40}{Style.RESET_ALL}")
    print(f"  Engine:       {mode_emoji.get(status['mode'],'?')} {status['mode']} @ {status['hz']:.1f} Hz")
    print(f"  Cycles:       {status['cycle_count']}")
    print(f"  Proofs:       {status['proofs_generated']}")
    print(f"  Uptime:       {health['uptime_seconds']:.0f}s")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")
    print(f"  Predictions:  {pred_stats['total_predictions']}")
    print(f"  Surprises:    {pred_stats['total_surprises']}")
    print(f"  Avg Error:    {pred_stats['avg_error']:.3f}")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")
    print(f"  Impasses:     {imp_stats['active_impasses']} active / {imp_stats['total_created']} total")
    print(f"  Resolution:   {imp_stats['resolution_rate']:.0%}")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")
    print(f"  Recon Open:   {recon_stats['active_windows']}")
    print(f"  Strengthened: {recon_stats['total_strengthened']}")
    print(f"  Weakened:     {recon_stats['total_weakened']}")
    print(f"  Updated:      {recon_stats['total_updated']}")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")
    
    snap = pipeline.heartbeat.get_current()
    print(f"  Engrams:      {snap.get('total_engrams', '?')}")
    print(f"  Quality:      {snap.get('avg_quality', 0):.3f}")
    print(f"  Consistency:  {snap.get('avg_consistency', 0):.3f}")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")


def _show_impasses(pipeline):
    """Show active impasses and sub-goals"""
    if not pipeline._reasoning_ready:
        print_system("Reasoning not initialized.")
        return
    
    active = pipeline.impasse_detector.get_active_by_priority()
    
    if not active:
        print_neuro("No active impasses — system is not stuck on anything.")
        return
    
    print(f"{Fore.YELLOW}{'─'*40}")
    print(f"  🚧 Active Impasses ({len(active)})")
    print(f"{'─'*40}{Style.RESET_ALL}")
    
    for imp in active:
        age = imp.to_dict()["age_seconds"]
        print(f"  [{imp.impasse_type.value}] priority={imp.priority:.1f}")
        print(f"    Query: {imp.original_query[:60]}")
        print(f"    Goal:  {imp.sub_goal}")
        print(f"    Age:   {age:.0f}s  Attempts: {imp.attempts}")
        print()


def _show_prediction_stats(pipeline):
    """Show prediction engine statistics"""
    if not pipeline._reasoning_ready:
        print_system("Reasoning not initialized.")
        return
    
    stats = pipeline.prediction_engine.get_stats()
    
    print(f"{Fore.YELLOW}{'─'*40}")
    print(f"  ⚡ Prediction Engine")
    print(f"{'─'*40}{Style.RESET_ALL}")
    print(f"  Total Predictions: {stats['total_predictions']}")
    print(f"  Total Surprises:   {stats['total_surprises']}")
    print(f"  Average Error:     {stats['avg_error']:.4f}")
    print(f"  Cache Size:        {stats['cache_size']}")
    
    domains = stats['surprising_domains']
    if domains:
        print(f"  Surprising Domains:")
        for domain, avg_err in domains:
            print(f"    {domain}: avg error = {avg_err:.3f}")
    
    print(f"{Fore.YELLOW}{'─'*40}{Style.RESET_ALL}")


def _prove_statement(pipeline, statement):
    """Test a proof directly"""
    if not pipeline._reasoning_ready:
        print_system("Reasoning not initialized.")
        return
    
    print_reasoning(f"Attempting proof: {statement}")
    
    proof = pipeline.reasoning_engine.prove(query=statement)
    
    if proof.proven:
        print_reasoning(f"✅ PROVEN (confidence: {proof.confidence:.0%})")
        print_reasoning(f"   Verifier: {proof.verifier}")
        if proof.proof_steps:
            for i, step in enumerate(proof.proof_steps):
                print_reasoning(f"   Step {i+1}: {step}")
    else:
        print_reasoning(f"❌ Not proven (confidence: {proof.confidence:.0%})")
        if proof.error:
            print_reasoning(f"   Reason: {proof.error}")

def _launch_world(pipeline):
    """Launch the 3D embodied world"""
    print_system("Starting Motor Cortex + 3D World...")
    
    try:
        from reasoning.motor_cortex import MotorCortex
        from reasoning.embodiment import EmbodimentBridge
        
        motor = MotorCortex()
        bridge = EmbodimentBridge(motor, pipeline=pipeline)
        bridge.start()
        
        # Store references on pipeline
        pipeline._motor_cortex = motor
        pipeline._embodiment = bridge
        
        print_system("🧠 Motor Cortex: Online")
        print_system("🌍 Embodiment Bridge: ws://localhost:8765")
        print_system("")
        print_system(f"Open this file in your browser:")
        
        import os
        world_path = os.path.join(os.path.dirname(__file__), "world", "world.html")
        print_system(f"  file:///{world_path.replace(os.sep, '/')}")
        print_system("")
        print_system("The AI will start exploring autonomously once the browser connects.")
        
        # Try to open browser automatically
        try:
            import webbrowser
            webbrowser.open(f"file:///{world_path.replace(os.sep, '/')}")
        except Exception:
            pass
        
    except Exception as e:
        print(f"{Fore.RED}World launch failed: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
