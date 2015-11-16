#!/usr/bin/env python
import os
import sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, os.pardir))

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
