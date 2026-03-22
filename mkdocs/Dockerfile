FROM squidfunk/mkdocs-material

RUN pip install --no-cache-dir mkdocs-rss-plugin

COPY mkdocs.yml /docs/mkdocs.yml
COPY docs/ /docs/docs/

WORKDIR /docs

EXPOSE 8000

ENTRYPOINT ["mkdocs"]
CMD ["serve", "--dev-addr=0.0.0.0:8000"]
