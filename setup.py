from setuptools import find_packages, setup

setup(
    name="django-multitransactiontestcase",
    version="0.0.1",
    author="Kavi Laud",
    author_email="kavinath@gmail.com",
    description="testing",
    packages=find_packages(),
    install_requires=["Django>=1.11", "psycopg2-binary"],
)
