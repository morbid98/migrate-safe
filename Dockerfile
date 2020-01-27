FROM python:3.7.2-stretch

MAINTAINER Andrew Rewoonenco <arewoonenco@infoblox.com>


RUN pip install pg8000

COPY bin/ /bin/

ENTRYPOINT [ "/bin/intel-migrator.sh" ]
