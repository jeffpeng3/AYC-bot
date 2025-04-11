FROM python:3.12-alpine AS base
FROM base AS builder
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app

# update PATH environment variable
ENV PATH=/home/app/.local/bin:$PATH

CMD ["python", "-u", "bot.py"]