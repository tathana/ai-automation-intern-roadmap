FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 appuser && mkdir /data && chown appuser /data
COPY course ./course
USER appuser
ENV PYTHONUNBUFFERED=1 CAPSTONE_DB=/data/capstone.sqlite3
EXPOSE 8015
CMD ["python", "-m", "uvicorn", "course.api:app", "--host", "0.0.0.0", "--port", "8015"]
