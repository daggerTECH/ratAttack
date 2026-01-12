cat > start_rat.sh << 'EOF'
#!/bin/bash
source rat_env/bin/activate
python rat.py
EOF
chmod +x start_rat.sh
./start_rat.sh
