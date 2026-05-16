#!/usr/bin/env python3
"""Standalone backfill wrapper.

Same as `verdict dashboard --no-open` minus the serve step. Useful for
CI, cron, or anyone who just wants to refresh data/ without launching
a browser. Real logic lives in verdict.dashboard_cmd so the Click
subcommand can share it.
"""

from verdict.dashboard_cmd import run_backfill_cli


if __name__ == "__main__":
    run_backfill_cli()
