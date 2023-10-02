FROM owasp/zap2docker-stable

ARG REPORT_DIR

COPY . /app
WORKDIR /app

USER root


#install python
RUN apt-get install -y python3

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/`curl -sS https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE`/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /tmp
RUN cp /tmp/chromedriver-linux64/chromedriver /usr/local/bin


RUN pip install --upgrade pip


RUN pip install -r requirements.txt
RUN chmod 777 launcher.sh

USER zap

ENTRYPOINT [ "/bin/bash" ]