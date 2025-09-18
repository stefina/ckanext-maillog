import click
import smtplib
import logging
from email.mime.text import MIMEText
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


def get_commands():
    return [maillog]


@click.group()
def maillog():
    pass

@maillog.command("send_logs")
@click.option(
    "--cleanup",
    is_flag=True,
    required=False,
    help="Cleanup the written logs after they have been sent",
)
def send_logs(cleanup):
    """Send out any accumulated logs and cleanup afterwards.

    Use with command-option "--cleanup" to clean the log right after the email has been sent.
    """
    smtp_server = toolkit.config.get("smtp.server", "localhost:25")
    from_addr = toolkit.config.get("error_email_from", "ckan@example.org")
    to_addr = toolkit.config.get("ckanext.maillog.digest.to", "admin@example.org")
    subject = "CKAN Debug Log"

    if ":" in smtp_server:
        host, port = smtp_server.rsplit(":", 1)
        mailhost = host, int(port)
    else:
        mailhost = smtp_server

    digest_log_path = toolkit.config.get("ckanext.maillog.digest.log_path", "/srv/app/log/maillog/debug.log")
    with open(digest_log_path, "r") as f:
        body = f.read().strip()
    if not body.strip():
        click.echo("No log messages have been recorded since the last run.")
        body = "No log messages have been recorded since the last run."

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(*mailhost, timeout=10) as smtp:
        if toolkit.config.get("smtp.starttls"):
            smtp.starttls()

        user = toolkit.config.get("smtp.user")
        pwd = toolkit.config.get("smtp.password")
        if user and pwd:
            smtp.login(user, pwd)

        smtp.sendmail(from_addr, [to_addr], msg.as_string())

    click.echo(f"Sent {digest_log_path} to {to_addr} via {smtp_server}")

    if cleanup:
        click.echo(f"Cleaning up {digest_log_path}")
        open(digest_log_path, "w").close()