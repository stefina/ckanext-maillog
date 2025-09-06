import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.maillog.cli import get_commands

from logging.handlers import SMTPHandler
from logging import FileHandler
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class MaillogPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IClick)

    def get_commands(self):
        return get_commands()

    def make_middleware(self, app, config):
        CKAN_MAILLOG_ENABLE_ALERT = toolkit.asbool(config.get("ckanext.maillog.alert", False))
        if CKAN_MAILLOG_ENABLE_ALERT:
            self.make_maillog_alert_middleware(app, config)
        return app

    def make_maillog_digest_middleware(self, app, config):
        CKAN_MAILLOG_DIGEST_LOG_LEVEL_NAME = self._parse_log_level_name("ckanext.maillog.digest.log_level", logging.getLevelName(logging.WARNING))
        CKAN_MAILLOG_DIGEST_LOGGERS = config.get("ckanext.maillog.digest.loggers", None)

        CKAN_MAILLOG_DIGEST_LOG_PATH = config.get("ckanext.maillog.digest.log_path", "/srv/app/log/maillog/debug.log")
        Path(CKAN_MAILLOG_DIGEST_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

        file_handler = FileHandler(CKAN_MAILLOG_DIGEST_LOG_PATH)
        file_handler.setLevel(CKAN_MAILLOG_DIGEST_LOG_LEVEL_NAME)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"))

        if CKAN_MAILLOG_DIGEST_LOGGERS:
            loggers = CKAN_MAILLOG_DIGEST_LOGGERS.split()
        else:
            loggers = ["", "ckan", "ckanext", "ckanext.maillog"]
        for name in loggers:
            logger = logging.getLogger(name)
            logger.addHandler(file_handler)

        log.debug("Adding Maillog digest middleware...")

        return app

    def make_maillog_alert_middleware(self, app, config):

        CKAN_MAILLOG_ALERT_LOGGERS = config.get("ckanext.maillog.alert.loggers", None)
        CKAN_MAILLOG_ALERT_TO = config.get("ckanext.maillog.alert.to", config.get('email_to'))
        CKAN_MAILLOG_ALERT_LOG_LEVEL_NAME = self._parse_log_level_name("ckanext.maillog.alert.log_level", logging.getLevelName(logging.ERROR))

        smtp_server = config.get('smtp.server')
        if ":" in smtp_server:
            host, port = smtp_server.rsplit(":", 1)
            mailhost = host, int(port)
        else:
            mailhost = smtp_server
        credentials = None
        if config.get('smtp.user'):
            credentials = (
                config.get('smtp.user'),
                config.get('smtp.password')
            )
        secure = () if config.get('smtp.starttls') else None
        mail_handler = SMTPHandler(
            mailhost=mailhost,
            fromaddr=config.get('error_email_from'),
            toaddrs=[CKAN_MAILLOG_ALERT_TO],
            subject='CKAN Event Report',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(CKAN_MAILLOG_ALERT_LOG_LEVEL_NAME)

        if CKAN_MAILLOG_ALERT_LOGGERS:
            loggers = CKAN_MAILLOG_ALERT_LOGGERS.split()
        else:
            loggers = ["", "ckan", "ckanext"]
        for name in loggers:
            logger = logging.getLogger(name)
            logger.addHandler(mail_handler)

        log.debug("Adding Maillog alert middleware...")

        return app

    def _parse_log_level_name(self, conf, default):
        raw_level = self._parse_log_level_int(conf, default)
        name = str(raw_level).strip().upper()
        return logging.getLevelName(name)

    def _parse_log_level_int(self, conf, default):
        return toolkit.config.get(conf, default)
