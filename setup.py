from setuptools import setup, find_packages

setup(
    name="tutor-gitops",
    version="12.0.0",
    license="AGPLv3",
    author="EOL DevOps",
    author_email="eol-devops@uchile.cl",
    description="GitOps plugin for Tutor Lilac",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "tutor<13.0.0,>=12.0.0",
    ],
    python_requires=">=3.7",
    entry_points={"tutor.plugin.v0": ["gitops = gitops.plugin"]},
)
