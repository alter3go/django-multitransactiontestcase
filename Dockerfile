FROM python:3

RUN mkdir -p /opt/test
WORKDIR /opt/test

RUN pip install tox tox-pyenv

RUN curl https://pyenv.run | bash
ENV PATH /root/.pyenv/bin:${PATH}

ADD install-pythons.sh .
RUN ./install-pythons.sh

ADD tox.ini .
RUN eval "$(pyenv init -)"
RUN pyenv local 2.7.16 3.5.7 3.6.9 3.7.5

CMD tox -e py37-django22

ADD setup.py .
ADD multi_transaction_test_case .
ADD tests .
