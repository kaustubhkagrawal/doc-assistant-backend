run:
	echo "Running in local mode."
	docker compose create db localstack
	docker compose start db localstack
	poetry run start


migrate:
	echo "Running migrations."
	docker compose create db
	docker compose start db
	poetry run python -m alembic upgrade head
	# workaround for having PGVector create its tables
	poetry run python -m scripts.build_vector_tables

refresh_db:
	# First ask for confirmation.
	@echo -n "Are you sure you want to refresh the local database? This will delete all data in your local db. [Y/n] "; \
	read ans; \
	if [ $${ans:-'N'} = 'Y' ]; then make confirmed_refresh_db; else echo "Aborting."; fi

confirmed_refresh_db:
	echo "Refreshing database."
	docker compose down db
	docker volume rm backend_postgres_data
	make migrate


setup_localstack:
	docker compose create localstack
	docker compose start localstack
	echo "Waiting for localstack to start..."
	# Ping http://localhost:4566 until we get a 200 response
	until $$(curl --output /dev/null --silent --head --fail http://localhost:4566); do \
		printf '.'; \
		sleep 0.5; \
	done
	# Check that S3_ASSET_BUCKET_NAME is set
	if [ -z ${S3_ASSET_BUCKET_NAME} ]; then \
		echo "S3_ASSET_BUCKET_NAME is not set. Please set it and try again."; \
		exit 1; \
	fi
	awslocal s3 mb s3://${S3_ASSET_BUCKET_NAME}
	echo "<html>LocalStack S3 bucket website is alive</html>" > /tmp/index.html
	awslocal s3 cp /tmp/index.html s3://${S3_ASSET_BUCKET_NAME}/index.html
	rm /tmp/index.html
	awslocal s3 website s3://${S3_ASSET_BUCKET_NAME}/ --index-document index.html
	awslocal s3api put-bucket-cors --bucket ${S3_ASSET_BUCKET_NAME} --cors-configuration file://./localstack-cors-config.json
	echo "LocalStack S3 bucket website is ready. Open http://${S3_ASSET_BUCKET_NAME}.s3-website.localhost.localstack.cloud:4566 in your browser to verify."
