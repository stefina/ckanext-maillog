import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


from logging.handlers import SMTPHandler
from logging import FileHandler
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class MaillogPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IMiddleware, inherit=True)

    def make_middleware(self, app, config):
        CKAN_MAILLOG_ENABLE_ALERT = toolkit.asbool(config.get("ckanext.maillog.alert", True))
        if CKAN_MAILLOG_ENABLE_ALERT:
            self.make_maillog_alert_middleware(app, config)
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
            subject='Logging',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)

        if CKAN_MAILLOG_ALERT_LOGGERS:
            loggers = ["", "ckan", "ckanext", "maillog.errors"]
            # loggers = CKAN_MAILLOG_ALERT_LOGGERS.split()
        else:
            loggers = ["", "ckan", "ckanext", "maillog.errors"]
        for name in loggers:
            logger = logging.getLogger(name)
            logger.setLevel(CKAN_MAILLOG_ALERT_LOG_LEVEL_NAME)
            logger.addHandler(mail_handler)

        log.debug('Adding Maillog alert middleware...')
        # app.logger.addHandler(mail_handler)

        return app

    def _parse_log_level_name(self, conf, default):
        raw_level = self._parse_log_level_int(conf, default)
        name = str(raw_level).strip().upper()
        return logging.getLevelName(name)

    def _parse_log_level_int(self, conf, default):
        return toolkit.config.get(conf, default)
