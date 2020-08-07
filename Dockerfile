#FROM python:3.8.1
FROM python:3.6.8-alpine3.8

MAINTAINER Andrew Rewoonenco <arewoonenco@infoblox.com>

##  && apk upgrade \
##  && apk upgrade musl \

RUN apk update \
  && apk add bash bash-completion

RUN pip install pg8000

COPY bin/ /bin/

ENTRYPOINT [ "/bin/intel-migrator.sh" ]
