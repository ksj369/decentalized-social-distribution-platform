#!/home/khevish/Documents/backup/winter 2024/cmput 404/project2/w24-project-l-ocalh-ost-and-found/venv/bin/python3.10

# Copyright: This module has been placed in the public domain.

"""
Adapt a word-processor-generated styles.odt for odtwriter use:

Drop page size specifications from styles.xml in STYLE_FILE.odt.
See https://docutils.sourceforge.io/docs/user/odt.html#page-size

Provisional backwards compatibility stub (to be removed in Docutils >= 0.21).

The actual code moved to the "docutils" library package and can be started
with ``python -m docutils.writers.odf_odt.prepstyles``.
"""

from docutils.writers.odf_odt import prepstyles

if __name__ == '__main__':
    prepstyles.main()
