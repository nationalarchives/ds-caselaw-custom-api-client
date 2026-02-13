## AWS Cloudshell:

### Setup

```
sudo yum install -y python3.12
pip install poetry
git clone https://github.com/nationalarchives/ds-caselaw-custom-api-client.git
cd ds-caselaw-custom-api-client/script
poetry install
```

### Run

```
poetry run python clean_s3.py
```
