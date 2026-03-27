FROM mwaeckerlin/python-build AS build

RUN apk add --no-cache postgresql-dev

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM mwaeckerlin/python

COPY --from=build /root/.local /root/.local
COPY app /app/app
COPY graphs /app/graphs
COPY main.py /app/main.py
