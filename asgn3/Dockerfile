#FROM python
#COPY dep.sh /asgn3_4.py /VectorClocks.py /
#RUN /dep.sh




FROM sanicframework/sanic:LTS
RUN mkdir /server
COPY . /server
RUN /server/dep.sh
ENTRYPOINT ["python3", "/server/asgn3_5.py"]
