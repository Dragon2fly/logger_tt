from setuptools import setup

with open('README.md', encoding='utf8') as fi:
    long_description = fi.read()

setup(
    name='logger_tt',
    version='1.3.2',
    packages=['logger_tt'],
    url='https://github.com/Dragon2fly/logger_tt',
    package_data={'': ['log_config.json', 'log_config.yaml']},
    include_package_data=True,
    license='MIT',
    platforms=["Any platform -- don't need Windows"],
    author='Nguyen Ba Duc Tin',
    author_email='nguyenbaduc.tin@gmail.com',
    description='Make logging simple, log even exception that you forgot to catch',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires=">=3.6",
)
