FROM mwaeckerlin/python-build AS build

COPY requirements.txt .
RUN pip install --user --no-cache-dir --break-system-packages -r requirements.txt
RUN pip install --user --no-cache-dir --break-system-packages --force-reinstall packaging

COPY main.py .
COPY app/ app/
COPY graphs/ graphs/

FROM mwaeckerlin/python

COPY --from=build /home/${BUILD_USER}/.local/lib /home/${RUN_USER}/.local/lib
COPY --from=build /app /app

EXPOSE 8000
