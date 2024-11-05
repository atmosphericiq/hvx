from setuptools import setup, find_packages

setup(
  name='hvx',
  version='0.0.1',
  author='Tom Hayden',
  author_email='thayden@gmail.com',
  packages=find_packages(exclude=['tests', 'tests.*']),
  long_description="A Library for Simulating High Voltage AC Induction",
  include_package_data=True,
  install_requires=['dateparser', 'numpy'],
  entry_points={
    'console_scripts': [],
  },
  classifiers=[
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
  ],
  python_requires='>=3.6',
)

