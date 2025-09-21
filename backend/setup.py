# backend/setup.py

from setuptools import setup, find_packages

setup(
    name='pr_review_agent',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'langchain',
        'langgraph',
        'langchain-google-genai',
        'neo4j',
        'pylint',
        'bandit',
        'flake8',
        'requests',
        'python-dotenv',
        'python-gitlab',
        'radon',
        'Flask',
        'Flask-Cors',
    ],
)
