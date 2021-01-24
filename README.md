# PredictIt

In this repo, `predictit.py` sends an SMS (via email) whenever PredictIt.org launches a new market.

## Setup

1. Clone the repo
2. In the root directory, create a file `passwords.py` that contains the following string objects:
  - EMAIL_FROM: the email address that you'll send notifications from
  - PASSWORD: the password to EMAIL_FROM
  - EMAIL_TO: the email address you'll send notifications to. If your carrier allows, you can send an SMS for faster notifications (see link in next section).
3. Run `predictit.py`. 

Timing is handled within the script, but you could adjust it to be run using a scheduler instead. The default settings check for new markets every minute, which is how often PI updates the API.

## Helpful stuff

- [Free SMS via email](https://20somethingfinance.com/how-to-send-text-messages-sms-via-email-for-free/)
- [App passwords for Gmail](https://myaccount.google.com/apppasswords) for logging in via the `smtplib` package. Recommended that you use a throw-away email.
