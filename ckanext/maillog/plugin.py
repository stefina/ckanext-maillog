import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.maillog.cli import get_commands

from logging.handlers import SMTPHandler, RotatingFileHandler
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class MaillogPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IClick)

    def get_commands(self):
        return get_commands()

    def make_middleware(self, app, config):
        enable_alert = toolkit.asbool(config.get("ckanext.maillog.alert", False))
        enable_digest = toolkit.asbool(config.get("ckanext.maillog.digest", False))
        if enable_digest:
            self.make_maillog_digest_middleware(app, config)
        if enable_alert:
            self.make_maillog_alert_middleware(app, config)
        return app

    def make_maillog_digest_middleware(self, app, config):
        digest_log_level_name = self._parse_log_level("ckanext.maillog.digest.log_level", "WARNING")
        digest_loggers = config.get("ckanext.maillog.digest.loggers", None)
        digest_max_bytes = int(config.get("ckanext.maillog.digest.max_bytes", 5 * 1024 * 1024))  # 5 MB
        digest_backup_count = int(config.get("ckanext.maillog.digest.backup_count", 1))

        digest_log_path = config.get("ckanext.maillog.digest.log_path", "/srv/app/log/maillog/debug.log")
        Path(digest_log_path).parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            digest_log_path,
            maxBytes=digest_max_bytes,
            backupCount=digest_backup_count,
            encoding="utf-8",
            delay=True
        )
        file_handler.setLevel(digest_log_level_name)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"))

        if digest_loggers:
            loggers = digest_loggers.split()
        else:
            loggers = ["", "ckan", "ckanext", "ckanext.maillog"]
        for name in loggers:
            logger = logging.getLogger(name)
            logger.addHandler(file_handler)

        log.debug("Adding Maillog digest middleware...")

        return app

    def make_maillog_alert_middleware(self, app, config):

        alert_loggers = config.get("ckanext.maillog.alert.loggers", None)
        alert_to = config.get("ckanext.maillog.alert.to", config.get('email_to'))
        alert_log_level_name = self._parse_log_level("ckanext.maillog.alert.log_level", "ERROR")

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
            toaddrs=[alert_to],
            subject='CKAN Event Report',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(alert_log_level_name)

        if alert_loggers:
            loggers = alert_loggers.split()
        else:
            loggers = ["", "ckan", "ckanext"]
        for name in loggers:
            logger = logging.getLogger(name)
            logger.addHandler(mail_handler)

        log.debug("Adding Maillog alert middleware...")

        return app

    def _parse_log_level(self, conf, default):
        raw_level = toolkit.config.get(conf, default)
        if isinstance(raw_level, int):
            return raw_level

        string_level = str(raw_level).strip().upper()
        if string_level.isdigit():
            return int(string_level)

        level = logging.getLevelName(string_level)
        if level is not None:
            return level
        return logging.getLevelName(str(default).upper())
