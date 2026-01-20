from IPython.core.interactiveshell import InteractiveShell

def get_ipython() -> InteractiveShell | None:
    """Get the global InteractiveShell instance.

    Returns None if no InteractiveShell instance is registered.
    """
    ...
