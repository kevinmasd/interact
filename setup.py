import setuptools

setuptools.setup(
    name="interact",
    version='11.3.16',
    url="https://github.com/data-8/interact",
    author="Data 8 Team",
    description="Git Grab: Managing Assignments",
    packages=setuptools.find_packages(),
    install_requires=[
        'tornado',
        'pytest',
        'webargs',
        'requests',
        'gitpython',
        'toolz',
        'notebook',
    ],
    package_data={'interact': ['app/static/*']},
)
