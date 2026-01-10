#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieStreaming.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 👉 AUTO SETUP DATABASE CHO RENDER (FREE, KHÔNG CẦN SHELL)
    if os.environ.get("RENDER") == "true":
        try:
            from django.core.management import call_command
            print("🔧 Running migrate on Render...")
            call_command("migrate", interactive=False)

            # Chỉ load data nếu DB còn trống (tránh load trùng)
            from django.contrib.contenttypes.models import ContentType
            if ContentType.objects.count() == 0:
                print("📦 Loading initial data myapp.json...")
                call_command("loaddata", "myapp.json")
            else:
                print("✅ Data already exists, skip loaddata")

        except Exception as e:
            print("⚠️ Auto DB init error:", e)

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
