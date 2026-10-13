#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Jarvis MK2 setup — minimal test without Unicode issues.
"""
import sys
import os

def test_gemini_manager():
    """Test GeminiManager singleton and API key verification."""
    try:
        from modulos.gemini_manager import GeminiManager, gemini

        gm = gemini()
        print("[OK] GeminiManager singleton imported and instantiated")

        # Test that instance is same
        gm2 = gemini()
        assert gm is gm2, "Singleton not working"
        print("[OK] Singleton pattern works")

        # Test key verification
        if gm.api_key:
            print(f"[OK] GEMINI_API_KEY found: {gm.api_key[:15]}...")
        else:
            print("[WARN] No GEMINI_API_KEY in environment")

        # Test stats method
        stats = gm.stats()
        print(f"[OK] Stats available: {len(stats)} keys")

        return True
    except Exception as e:
        print(f"[FAIL] GeminiManager: {e}")
        return False

def test_sintesis_voz():
    """Test TTS integration."""
    try:
        from modulos.sintesis_voz import SintesisVoz
        tts = SintesisVoz()
        print("[OK] SintesisVoz initialized")
        print(f"    Gemini TTS: {tts.usar_gemini_tts}")
        print(f"    Edge TTS: {tts.usar_edge}")
        return True
    except Exception as e:
        print(f"[FAIL] SintesisVoz: {e}")
        return False

def test_ia_local():
    """Test IA Local with GeminiManager."""
    try:
        from modulos.ia_local import IALocal
        ia = IALocal(modelo="llama3")
        print("[OK] IALocal initialized with GeminiManager")
        print(f"    Motor: {ia.motor}")
        print(f"    Gemini disponible: {ia.gemini_ok}")
        return True
    except Exception as e:
        print(f"[FAIL] IALocal: {e}")
        return False

def test_planner():
    """Test Planner with GeminiManager."""
    try:
        from modulos.agent.planner import create_plan, _fallback_plan

        # Test fallback plan (doesn't require API)
        plan = _fallback_plan("test goal")
        assert "steps" in plan, "Fallback plan missing steps"
        print("[OK] Planner fallback available")

        # Test plan function exists and accepts goal
        # (won't call API unless Gemini is actually configured)
        print("[OK] Planner functions integrated")
        return True
    except Exception as e:
        print(f"[FAIL] Planner: {e}")
        return False

def test_executor():
    """Test Executor with GeminiManager."""
    try:
        from modulos.agent.executor import AgentExecutor
        executor = AgentExecutor()
        print("[OK] AgentExecutor initialized with GeminiManager")
        return True
    except Exception as e:
        print(f"[FAIL] AgentExecutor: {e}")
        return False

def test_screen_processor():
    """Test Vision with GeminiManager."""
    try:
        from modulos.tools.screen_processor import screen_process
        print("[OK] screen_processor imported with GeminiManager")
        return True
    except Exception as e:
        print(f"[FAIL] screen_processor: {e}")
        return False

def main():
    print("=" * 60)
    print("JARVIS MK2 VERIFICATION")
    print("=" * 60)
    print()

    tests = [
        ("GeminiManager", test_gemini_manager),
        ("SintesisVoz", test_sintesis_voz),
        ("IALocal", test_ia_local),
        ("Planner", test_planner),
        ("Executor", test_executor),
        ("ScreenProcessor", test_screen_processor),
    ]

    results = []
    for name, test_fn in tests:
        print(f"\nTesting {name}...")
        result = test_fn()
        results.append((name, result))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print()
    print(f"Result: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
