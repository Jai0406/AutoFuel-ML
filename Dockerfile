# Base image
FROM python:3.12-slim

# Working directory set karo
WORKDIR /app

# Requirements copy aur install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki project copy karo
COPY . .

# FastAPI (8000) aur Streamlit (8501) dono ports expose karo
EXPOSE 8000 8501

# Ab hum app.py nahi, balki tumhara master script run.py chalayenge
CMD ["python", "run.py"]