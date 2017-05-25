## Nagios integration

To integrate Nagios with dev_github, we will need to add a nagios event handler which POSTs a HTTP webbhook to dev_github.

## Nagios event handler

The event handler script is available at [etc/dev_githubservice_handler.py].

## Configuring the event handler

The event handler tries to register a trigger type first before sending any
notifications to dev_github. This trigger type is then referenced in dev_github rules. See
[rules/](rules/).

## Installing the event handler

1. Pick the nagios host where you want the event handler to be placed.
2. Copy dev_githubservice_handler.py  and dev_githubservice_handler.yaml to /usr/local/nagios/libexec/

    ```bash
    cp dev_githubservice_handler.* /usr/local/nagios/libexec/
    ```
3. Make sure dev_githubservice_handler.py is executable.

    ```bash
    chmod +x /usr/local/nagios/libexec/dev_githubservice_handler.py
    ```
4. Handlers require a configuration file (See [etc/dev_githubservice_handler.yaml](etc/dev_githubservice_handler.yaml)) containing
   dev_github credentials, dev_github API URL and dev_github auth URL, dev_github API Key, Unauthed and SSL Verify Flag.

5. Test the event handler manually.

    ```bash
    python dev_githubservice_handler.py dev_githubservice_handler.yaml 44534 3 WARNING HARD "/var/log" 4 host-name
    # You'd see something like the following if the test succeeds.
    Sent nagios event to dev_github. HTTP_CODE: 202
    ```

## Handler options

1. The handler supports unauthed dev_github endpoints (server side authentication turned off). Though
   this is not recommended, you can use this for local testing. To turn on the unauthed flag to
   true in dev_githubservice_handler.yaml

   ```
   unauthed: True
   ```
2. The handler also supports turning on/off ssl verification for all API requests to dev_github. By
   default, SSL verification is turned off as evaluation versions of dev_github ship with self-signed
   certs. To turn on ssl verify, change the flag in dev_githubservice_handler.yaml to `True`.

   ```
   ssl_verify: True
   ```
3. If for whatever reason, you've to debug the handler, you can use the --verbose option.

   ```bash
   python dev_githubservice_handler.py dev_githubservice_handler.yaml 44534 3 WARNING HARD "/var/log" 4 host-name --verbose
   ```
# nagios-exchange
# nagios-exchange
