from setuptools import setup, find_packages

setup(
    name='pr_review_agent',
    version='0.1',
    package_dir={'': 'backend'},
    packages=find_packages(where='backend'),
    install_requires=[
        'langchain',
        'langgraph',
        'langchain[google-genai]',
        'neo4j',
        'pylint',
        'bandit',
        'flake8',
        'requests',
        'python-dotenv',
        'python-gitlab',
        'bitbucket-api',
        'radon',
        'Flask',
        'Flask-Cors',
        'gunicorn',
    ],
)
