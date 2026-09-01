#!/usr/bin/env python3
"""Compatibility entry point for existing installations started from the repo root."""

import asyncio

from raspberry.main import main


if __name__ == "__main__":
    asyncio.run(main())
