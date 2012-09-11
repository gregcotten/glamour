# glamour

This will zip up, appcast, generate HTML git commit release notes, maintain a version database, and upload via SFTP your [Sparkle.framework](https://github.com/andymatuschak/Sparkle) enabled Mac apps.

## Installation

You will need to install some wonderful 3rd-party python modules:

	pip install GitPython paramiko PyYAML

## Usage

For the moment just setup glamour_config.yml and run:

	python glamour.py

## Notes on Usage

As of Sparkle.framework 1.5 you must host your files on an HTTPS server. Many hosts offer a shared SSL certificate for free - ask your web hosting company!

## The Future

1. At the moment glamour is more of a command-line tool. The idea is to make this into a full-fledged Python module.
2. Amazon S3 uploading!


## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request