#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default
WITH_TESTS=false
DATA_ZIP_FILENAME="aisdk-2024-08-07.zip"   # Expected name of the zip file in data/
MANUAL_DOWNLOAD_URL="http://aisdata.ais.dk/?prefix=2024/"
CONFIG_FILE="config.json"
REQUIREMENTS_FILE="requirements.txt"
TRAJECTORIES_FILE="data/trajectories_mf1.json"  
show_help() {
    echo "Usage: ./run.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --with-tests    Run preprocessing and execute tests (requires data zip in data/)"
    echo "  --help          Show this help"
    echo ""
    echo "Without --with-tests, only starts container and runs the server."
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-tests) WITH_TESTS=true; shift ;;
        --help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found. Please install Docker.${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python3 not found.${NC}"; exit 1; }
command -v lsof >/dev/null 2>&1 || { echo -e "${YELLOW}lsof not found. Install it for automatic port killing.${NC}"; }

# Free port if already in use
free_port() {
    local PORT=$1
    if command -v lsof >/dev/null 2>&1; then
        local PID=$(lsof -ti :$PORT 2>/dev/null)
        if [ -n "$PID" ]; then
            echo -e "${YELLOW}Port $PORT is in use by PID $PID. Killing it...${NC}"
            kill -9 $PID 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}Port $PORT freed.${NC}"
        fi
    else
        echo -e "${YELLOW}lsof not installed. Cannot check port $PORT.${NC}"
    fi
}

# config.json if missing
setup_config() {
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${GREEN}Found existing $CONFIG_FILE${NC}"
    else
        echo -e "${YELLOW}Creating $CONFIG_FILE...${NC}"
        read -p "Enter DB_HOST [localhost]: " DB_HOST
        DB_HOST=${DB_HOST:-localhost}
        read -p "Enter DB_PORT [25431]: " DB_PORT
        DB_PORT=${DB_PORT:-25431}
        read -p "Enter DB_USER [postgres]: " DB_USER
        DB_USER=${DB_USER:-postgres}
        read -sp "Enter DB_PASS [mysecretpassword]: " DB_PASS
        echo ""
        DB_PASS=${DB_PASS:-mysecretpassword}
        read -p "Enter DB_NAME [postgres]: " DB_NAME
        DB_NAME=${DB_NAME:-postgres}
        read -p "Enter API_PORT [8080]: " API_PORT
        API_PORT=${API_PORT:-8080}

        cat > "$CONFIG_FILE" <<EOF
{
    "DB_HOST": "$DB_HOST",
    "DB_PORT": $DB_PORT,
    "DB_USER": "$DB_USER",
    "DB_PASS": "$DB_PASS",
    "DB_NAME": "$DB_NAME",
    "API_PORT": $API_PORT
}
EOF
        echo -e "${GREEN}Config saved to $CONFIG_FILE${NC}"
    fi
}

# Get API port from config.json
get_api_port() {
    if [ -f "$CONFIG_FILE" ]; then
        python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('API_PORT', 8080))" 2>/dev/null || echo "8080"
    else
        echo "8080"
    fi
}

# virtual env
setup_venv() {
    if [ ! -d "env" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv env
    fi
    source env/bin/activate
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${YELLOW}Installing requirements...${NC}"
        pip install -r "$REQUIREMENTS_FILE"
    else
        echo -e "${RED}Requirements file not found: $REQUIREMENTS_FILE${NC}"
        exit 1
    fi
}

# Start MobilityDB container
start_container() {
    CONTAINER_NAME="mobilitydb"
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            echo -e "${GREEN}Container already running.${NC}"
        else
            echo -e "${YELLOW}Starting existing container...${NC}"
            docker start "$CONTAINER_NAME"
        fi
    else
        echo -e "${YELLOW}Pulling and starting MobilityDB container...${NC}"
        docker pull --platform=linux/amd64 mobilitydb/mobilitydb
        docker volume create mobilitydb_data
        docker run --name "$CONTAINER_NAME" \
            -e POSTGRES_PASSWORD=mysecretpassword \
            -p 25431:5432 \
            -v mobilitydb_data:/var/lib/postgresql \
            -d mobilitydb/mobilitydb
    fi
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    sleep 5
}

# Check for dataset presence
check_data() {
    DATA_DIR="data"
    mkdir -p "$DATA_DIR"
    if [ ! -f "$DATA_DIR/$DATA_ZIP_FILENAME" ]; then
        echo -e "${RED}Data file not found: $DATA_DIR/$DATA_ZIP_FILENAME${NC}"
        echo -e "${YELLOW}Please download the AIS data zip and place it in the 'data/' folder.${NC}"
        echo -e "You can download it from: ${GREEN}$MANUAL_DOWNLOAD_URL${NC}"
        echo -e "${YELLOW}After downloading, rename the file to '$DATA_ZIP_FILENAME' if necessary.${NC}"
        exit 1
    else
        echo -e "${GREEN}Found data file: $DATA_DIR/$DATA_ZIP_FILENAME${NC}"
    fi
}

# Data preprocessing
run_preprocessing() {
    if [ ! -f "data/ais_to_json.py" ]; then
        echo -e "${RED}Preprocessing script not found: data/ais_to_json.py${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Running data preprocessing...${NC}"
    python data/ais_to_json.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Preprocessing failed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Preprocessing completed.${NC}"
}

# Run tests
run_tests() {
    API_PORT=$(get_api_port)
    free_port $API_PORT
    echo -e "${YELLOW}Starting server in background on port $API_PORT...${NC}"
    python server.py &
    SERVER_PID=$!
    sleep 5
    echo -e "${YELLOW}Running integration tests...${NC}"
    pytest tests/test_mobility_api.py -v -s
    TEST_EXIT=$?
    # kill $SERVER_PID 2>/dev/null || true   # optionally kill server after tests
    exit $TEST_EXIT
}

setup_config
setup_venv
start_container

if [ "$WITH_TESTS" = true ]; then
   
    if [ -f "$TRAJECTORIES_FILE" ] && [ -s "$TRAJECTORIES_FILE" ]; then
        echo -e "${GREEN}Found existing $TRAJECTORIES_FILE (non‑empty). Skipping preprocessing.${NC}"
    else
        echo -e "${YELLOW}Missing or empty $TRAJECTORIES_FILE. Running preprocessing...${NC}"
        check_data
        run_preprocessing
    fi

    run_tests
else
    API_PORT=$(get_api_port)
    free_port $API_PORT
    echo -e "${GREEN}Starting server on port $API_PORT...${NC}"
    python server.py
fi