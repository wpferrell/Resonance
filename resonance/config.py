# Copyright (c) 2026 William Ferrell. All rights reserved.
# Licensed under the Business Source License 1.1 — see LICENSE for details.

# resonance/config.py
# Manages Resonance configuration and the first-run opt-in prompt.
# Config is stored in resonance_data/config.json.
# Users must make a conscious choice about feedback sharing — no default.

import json
import os
from pathlib import Path

CONFIG_DIR = Path("resonance_data")
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "feedback_enabled": None,  # None = not yet chosen
    "first_run_complete": False,
}


def load_config() -> dict:
    """Load config from disk. Return defaults if not found."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULTS, **json.load(f)}
        except Exception:
            return DEFAULTS.copy()
    return DEFAULTS.copy()


def save_config(config: dict):
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def run_first_time_prompt(config: dict) -> dict:
    """
    Show the first-run opt-in prompt.
    User must make a conscious choice — no default, no skip.
    """
    print("\n┌─ Welcome to Resonance ────────────────────────────────┐")
    print("│                                                       │")
    print("│  Before we begin — one question:                     │")
    print("│                                                       │")
    print("│  Help improve Resonance by sharing anonymous          │")
    print("│  correction data?                                     │")
    print("│                                                       │")
    print("│  Corrections only. No message text. No identity.     │")
    print("│  You can change this any time:                       │")
    print("│  resonance config --feedback on/off                  │")
    print("│                                                       │")
    print("│  [1] Yes, I want to help improve Resonance           │")
    print("│  [2] No, keep everything local                       │")
    print("│                                                       │")
    print("└───────────────────────────────────────────────────────┘")

    while True:
        choice = input("\nYour choice (1 or 2): ").strip()
        if choice == "1":
            config["feedback_enabled"] = True
            config["first_run_complete"] = True
            print("\n✓ Thank you. Anonymous corrections will be shared to improve Resonance.")
            print("  Change this any time: resonance config --feedback off\n")
            break
        elif choice == "2":
            config["feedback_enabled"] = False
            config["first_run_complete"] = True
            print("\n✓ Got it. Everything stays local on your machine.")
            print("  Change this any time: resonance config --feedback on\n")
            break
        else:
            print("  Please enter 1 or 2.")

    save_config(config)
    return config


def set_feedback(enabled: bool):
    """Allow user to change feedback setting at any time."""
    config = load_config()
    config["feedback_enabled"] = enabled
    config["first_run_complete"] = True
    save_config(config)
    status = "enabled" if enabled else "disabled"
    print(f"✓ Feedback sharing {status}.")


def ensure_config() -> dict:
    """
    Load config. If first run not complete, show the opt-in prompt.
    Returns the current config.
    """
    config = load_config()
    if not config.get("first_run_complete"):
        config = run_first_time_prompt(config)
    return config
