#!/usr/bin/env bash

RUN_DIR=$( dirname -- "$( readlink -f -- "$0"; )"; )
source $RUN_DIR/venv/bin/activate

# Run the PDF metadata sync first
$RUN_DIR/pdf_metadata_sync.py

# Then run any other post-consume scripts
$RUN_DIR/post_consume_script.py
