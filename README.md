# glamour

This will zip up, appcast, generate git commit release notes, maintain a version database, and upload via SFTP your [Sparkle.framework](https://github.com/andymatuschak/Sparkle) enabled mac apps.

## Installation

You will need to install the some wonderful 3rd-party python modules:

	pip install GitPython paramiko PyYAML

## Usage

For the moment just setup glamour_config.yml and run:

	python glamour.py

## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request