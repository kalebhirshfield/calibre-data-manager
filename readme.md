# Installation

To install the Calibre Data Manager app, please follow these steps:

1. Install the required dependencies by running the following command in your terminal:

    ```pwsh
    pip install -r .\requirements.txt
    ```

2. If you are using python 3.12 or above, and wish to use the Flet CLI, you will need to install setuptools module by running:

    ```pwsh
    pip install setuptools
    ```

3. Package the app by running the following commands in your terminal:

    ```pwsh
    pip install pyinstaller
    ```

    ```pwsh
    flet pack main.py --name Calibre --icon .\assets\icon.ico
    ```

    This will create a packaged app that you can then run on your system.
