Genre Detector Documentation
==========================

A Material Design-compliant application for detecting and normalizing music genres in MP3 files.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api/index
   gui/index
   testing
   contributing

Installation
-----------

1. Create and activate a virtual environment:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

2. Install dependencies:

.. code-block:: bash

   python -m pip install -r requirements.txt

Usage
-----

Run the application with:

.. code-block:: bash

   python run_gui.py

Features
--------

- Material Design dark theme with full accessibility support
- Multiple API support for genre detection (MusicBrainz, LastFM)
- Drag-and-drop file handling
- Keyboard navigation and screen reader support
- Automatic file backups
- Genre normalization and filtering
- Batch processing capabilities

Accessibility
------------

The application is fully accessible and compliant with Material Design guidelines:

- Full keyboard navigation using Tab/Shift+Tab
- Screen reader support with ARIA labels
- High contrast color scheme
- Clear focus indicators
- Keyboard shortcuts:
    - Ctrl+O: Add Files
    - Ctrl+Shift+O: Add Folder
    - Ctrl+P: Process Files

Testing
-------

Run the test suite with:

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=src tests/

   # Generate HTML coverage report
   pytest --cov=src --cov-report=html tests/

Contributing
-----------

1. Ensure all tests pass before submitting changes
2. Follow Material Design guidelines for UI changes
3. Maintain accessibility compliance
4. Update documentation as needed

API Reference
------------

.. toctree::
   :maxdepth: 2

   api/core
   api/gui

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
