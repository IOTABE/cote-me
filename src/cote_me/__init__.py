"""
Cote-me - package raiz do projeto Django.
"""
import os


def main() -> None:
    """Ponto de entrada para o manage.py via console_script."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cote_me.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", *os.sys.argv[1:]])
