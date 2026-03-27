FROM mwaeckerlin/python-build AS build
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-compile --break-system-packages -r requirements.txt
RUN pip install --user --no-cache-dir --no-compile --break-system-packages --ignore-installed packaging
RUN find /home/${BUILD_USER}/.local/lib -type d -name '__pycache__' -prune -exec rm -rf {} +
RUN find /home/${BUILD_USER}/.local/lib -type f -name '*.pyc' -delete
COPY main.py .
COPY app/ app/
COPY graphs/ graphs/

FROM mwaeckerlin/python
COPY --from=build /home/${BUILD_USER}/.local/lib /home/${RUN_USER}/.local/lib
COPY --from=build /app /app
EXPOSE 8000
