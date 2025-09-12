[![Tests](https://github.com/stefina/ckanext-maillog/workflows/Tests/badge.svg?branch=main)](https://github.com/stefina/ckanext-maillog/actions)

# ckanext-maillog

**ckanext-maillog** adds email-based logging to CKAN.
It provides two complementary features that you can use independently or together:

- Email alerts – immediately send selected log messages (based on logger and level) to a configured recipient.

- Log digests – accumulate log messages from specific loggers into a file that can be delivered later (e.g. via a CLI command or cron).

This makes it easier to debug extensions and to set up targeted monitoring for critical events.

## Email alerts

Use this mode to send important log events immediately by email. You can configure one or more loggers and a minimum log level (for example, WARNING or ERROR). Whenever a matching log record is emitted, an email is sent right away to the configured recipient.

This is useful for catching critical issues as they happen — for example, when a new harvester plugin fails to connect to a source, or when a CKAN extension logs warnings that you want to be notified about without delay.

## Log digests

In digest mode, log messages are collected into a designated file instead of being emailed one by one. Later, you can trigger a command (or run it via cron) to send the accumulated messages as a single email.

This is especially handy for debugging when:

- You want to capture lower-level messages such as DEBUG or INFO without getting flooded by individual alert emails.

- You don’t have direct access to log files on the server but still want to review the output of a specific logger.

- You’re developing a new plugin and need to review its behavior over a period of time.

Each digest email contains all log messages from the configured loggers since the last time the digest was sent.

### Log Digest Cli Command

To send all previously accumulated log messages of the configured loggers since the last time the digest was sent.

It is meant to be run regularly by a cronjob. It is recommended to run it with the cleanup option which clears the file after the logs have been sent.

```bash
ckan maillog send_logs --cleanup 
```

## Requirements

Compatibility with core CKAN versions:

| CKAN version | Compatible? |
|--------------|-------------|
| 2.9          | not tested  |
| 2.10         | not tested  |
| 2.11         | yes         |

## Installation

To install ckanext-maillog:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/stefina/ckanext-maillog.git
    cd ckanext-maillog
    pip install -e .
	pip install -r requirements.txt

3. Add `maillog` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Add all required configurations to your configuration as described below.

4. Make sure to [configure an STMP-Email-Server](https://docs.ckan.org/en/latest/maintaining/configuration.html#email-settings).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

Configuration for instant email alerts:

    # Enable or disable instant email alerts 
    # (optional, default: false).
    ckanext.maillog.alert = true
   
    # List of loggers to monitor for alerts (space-separated).
    # (optional, default: "" ckan ckanext).
    ckanext.maillog.alert.loggers = ckanext.mycustomharvester ckanext.harvest ckanext.dcat
   
    # Minimum log level for alerts 
    # (optional, default: ERROR).
    ckanext.maillog.alert.log_level = WARNING
   
    # Recipient address for alert emails.
    # (mandatory)
    ckanext.maillog.alert.to = alert@alert.com

Configuration for log digests per email:   
   
    # Enable or disable digest logging
    # (optional, default: false).
    ckanext.maillog.digest = true
   
    # List of loggers to include in the digest (space-separated).
    # (optional, default: ckan ckanext).
    ckanext.maillog.digest.loggers = ckanext.mycustomharvester ckanext.harvest ckanext.dcat
    # Adding `""` will also include the root-logger.
    ckanext.maillog.digest.loggers = "" ckanext.mycustomharvester ckanext.harvest ckanext.dcat
   
    # Minimum log level for digest logging 
    # (optional, default: WARNING).
    ckanext.maillog.digest.log_level = DEBUG

    # Full path of the digest log 
    # (optional, default: /srv/app/log/maillog/debug.log).
    ckanext.maillog.digest.log_path = /srv/app/log/ckanext-myplugin/debug.log
   
    # Recipient address for digest emails.
    # (mandatory)
    ckanext.maillog.digest.to = digest@digest.com


## Developer installation

To install ckanext-maillog for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/stefina/ckanext-maillog.git
    cd ckanext-maillog
    pip install -e .
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-maillog

If ckanext-maillog should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `pyproject.toml` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python -m build && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
