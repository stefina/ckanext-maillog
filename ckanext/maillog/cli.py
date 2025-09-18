import click
import logging
import mimetypes
import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
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

    digest_log_path = toolkit.config.get("ckanext.maillog.digest.log_path", "/srv/app/log/maillog/")

    files = [os.path.join(digest_log_path, f) for f in os.listdir(digest_log_path)]
    files = [f for f in files if os.path.isfile(f)]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    if files:
        body_text = f"Attached {len(files)} log file(s) from {digest_log_path}."
    else:
        body_text = f"No log files found in {digest_log_path}."
    msg.attach(MIMEText(body_text, _charset="utf-8"))

    for path in files:
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(path, "rb") as fp:
            part = MIMEBase(maintype, subtype)
            part.set_payload(fp.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=os.path.basename(path))
        msg.attach(part)

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
        for path in files:
            open(path, "w").close()