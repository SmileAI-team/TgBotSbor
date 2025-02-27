FROM python:3.9-slim
WORKDIR /app
COPY save/requirements.txt ./save/requirements.txt
RUN pip install --no-cache-dir -r save/requirements.txt
COPY save/ ./save/
RUN ls -la /app/save/smile-ai-bot-1dccd401d6ed.json
CMD ["python", "-m", "save.main"]