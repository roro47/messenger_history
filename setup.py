from setuptools import setup, find_packages
setup(
    name="messenger_history",
    version="0.1",
    packages=['src'],
    install_requires = ['requests', 'fbchat', 'sqlalchemy', 'urlextract'],
    entry_points={
        'console_scripts': [
            'msgh = src.main:main'
            ]
        }
    )
print("\n**add environment variable MSGH_DB_PATH as your database's path")
