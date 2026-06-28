FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY config.py alerts.py api.py db.py main.py notifier.py ./

CMD ["main.lambda_handler"]
