# test_injector.py
import asyncio
from resonance.temporal_graph import TemporalGraph
from resonance.reinforcement import ReinforcementLoop
from resonance.injector import LLMContextInjector


async def main():
    graph = TemporalGraph()
    await graph.connect()

    loop = ReinforcementLoop()
    await loop.connect()

    injector = LLMContextInjector(graph, loop)

    print("=== LLM Context Injector Test ===")
    print()
    print("Building full system prompt...")
    print()

    system_prompt = await injector.build_system_prompt(
        base_prompt="You are a helpful AI assistant.",
        include_frameworks=True,
    )

    print(system_prompt)
    print()

    print("--- Current emotion context (one-liner) ---")
    context = await injector.get_current_emotion_context("I don't know what to do anymore.")
    print(context)
    print()
    print("✅ LLM context injector working.")

    await graph.close()
    await loop.close()


asyncio.run(main())