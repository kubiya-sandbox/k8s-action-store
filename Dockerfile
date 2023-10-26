FROM kubiya/base-action-store:stable

WORKDIR /home/app

COPY requirements.txt function/

RUN pip install --no-cache -r function/requirements.txt --user
COPY . function/

# if you want to override the default entrypoint uncomment the following line
# ENV fprocess="python index.py"
# ENV cgi_headers="true"
# ENV mode="http"
# ENV upstream_url="http://127.0.0.1:8000"
# ENV write_debug="false"
# HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

# CMD ["fwatchdog"]%
