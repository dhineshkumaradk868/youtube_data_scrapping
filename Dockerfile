FROM python:3.7
COPY . /app
WORKDIR /app
ENV PYTHON_APP=youtube.py
ENV PYTHON_RUN_HOST=0.0.0.0
RUN pip install -r requirements.txt
EXPOSE 8501
CMD streamlit run youtube.py