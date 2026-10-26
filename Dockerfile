FROM python:3.13-slim
WORKDIR /app
COPY app.py .
COPY europe.py .
COPY roma2026.py roma2026.json ./
COPY paris2026.json ./
COPY roma_four_days.json ./
COPY london_two_days.json ./
COPY attractions.py guides.json ./
COPY static ./static
COPY scripts/create_admin.py ./scripts/create_admin.py
COPY scripts/import_members.py ./scripts/import_members.py
ENV HOST=0.0.0.0 PORT=8000 DATA_DIR=/data
RUN mkdir /data && useradd --uid 10001 app && chown app /data
USER app
VOLUME /data
EXPOSE 8000
CMD ["python", "app.py"]
