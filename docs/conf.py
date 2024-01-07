# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import django

sys.path.insert(0, os.path.abspath(".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "procurement_system_backend.settings"
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Smart Procurement System"
copyright = "2024, Sahil Gidwani"
author = "Sahil Gidwani"
release = "1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Automatically document Python code
    "sphinx.ext.napoleon",  # Google-style or NumPy-style docstrings
    "sphinx.ext.viewcode",  # View Source link for Python code
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/*.migrations.rst",
    "**manage.rst",
    "**procurement_system_backend.rst",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
