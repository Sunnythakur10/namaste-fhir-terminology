# Setup Python Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. To activate the environment, run 'source .venv/bin/activate'"
