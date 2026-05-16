"""Fixture file for testing suppressed exception detection.

Each function demonstrates a specific exception handling pattern.
Line numbers are stable for testing purposes.
"""


def broad_exception_pass():
    """Should flag: except Exception with pass."""
    try:
        risky_operation()
    except Exception:
        pass


def bare_except_ellipsis():
    """Should flag: bare except with ellipsis."""
    try:
        risky_operation()
    except:
        ...


def narrow_exception_pass():
    """Should flag: narrow exception with pass."""
    try:
        data = {"key": "value"}
        return data["missing_key"]
    except KeyError:
        pass


def logger_only_handler():
    """Should flag: except with only logger call."""
    import logging
    try:
        risky_operation()
    except Exception:
        logging.error("Error occurred")


def continue_in_loop():
    """Should flag: except with continue in loop."""
    items = [1, 2, 3]
    for item in items:
        try:
            process(item)
        except Exception:
            continue


def reraise_handler():
    """Should NOT flag: except with raise."""
    try:
        risky_operation()
    except ValueError:
        raise


def return_handler():
    """Should NOT flag: except with return."""
    try:
        return risky_operation()
    except Exception:
        return None


def multi_statement_handler():
    """Should NOT flag: except with multiple statements."""
    import logging
    try:
        risky_operation()
    except TypeError:
        x = 1
        logging.error("Error with context")


def clean_function():
    """Should NOT flag: no try/except."""
    return 42


def long_try_body():
    """Should flag with boosted confidence: long try body with pass."""
    try:
        # This try body spans more than 10 lines
        line1 = 1
        line2 = 2
        line3 = 3
        line4 = 4
        line5 = 5
        line6 = 6
        line7 = 7
        line8 = 8
        line9 = 9
        line10 = 10
        line11 = 11
        risky_operation()
    except Exception:
        pass


def nested_try_blocks():
    """Should flag both nested handlers if both added."""
    try:
        outer_operation()
        try:
            inner_operation()
        except KeyError:
            pass  # Inner handler - should flag
    except Exception:
        pass  # Outer handler - should flag


def multiple_handlers():
    """Should flag only the suppressed handler, not the one that re-raises."""
    try:
        risky_operation()
    except KeyError:
        pass
    except ValueError:
        raise


def bare_except_long_body():
    """Should flag with confidence capped at 0.95: bare except + long try body."""
    try:
        # This try body spans more than 10 lines
        line1 = 1
        line2 = 2
        line3 = 3
        line4 = 4
        line5 = 5
        line6 = 6
        line7 = 7
        line8 = 8
        line9 = 9
        line10 = 10
        line11 = 11
        risky_operation()
    except:
        pass


# Helper functions referenced above (not actual implementations)
def risky_operation():
    pass


def process(item):
    pass


def outer_operation():
    pass


def inner_operation():
    pass

# Made with Bob
