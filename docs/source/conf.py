# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import django

# Assuming conf.py is located in docs/source/
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, parent_dir)

# Set up Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'procurement_system_backend.settings'
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Smart Procurement System'
copyright = '2024, Sahil Gidwani'
author = 'Sahil Gidwani'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Automatically document Python code
    # 'sphinx.ext.autosummary'   # Generate autodoc summaries
    # 'sphinx.ext.napoleon',     # Google-style or NumPy-style docstrings
    # 'sphinx.ext.todo',         # Todo directive for marking incomplete sections
    # 'sphinx.ext.viewcode',     # View Source link for Python code
    # 'sphinx.ext.githubpages',  # Configuration for hosting on GitHub Pages
    # 'sphinx.ext.intersphinx',  # Link to external documentation
    # 'sphinx.ext.graphviz',     # Add support for Graphviz graphs
    # 'sphinx.ext.imgmath',      # Include math equations using LaTeX
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
