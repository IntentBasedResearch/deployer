# Python SLim Image
FROM python:3.13.0-bullseye

# Work directory
WORKDIR /deployer

# Copying all necessary files
# COPY classes/ app.py .env requirements.txt /deployer/
COPY classes/ /deployer/classes/
COPY app.py /deployer/app.py
COPY .env /deployer/.env
COPY requirements.txt /deployer/requirements.txt
COPY entrypoint.sh /deployer/entrypoint.sh

# Execute permissions on entrypoint script
RUN chmod +x /deployer/entrypoint.sh

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

ENTRYPOINT ["/deployer/entrypoint.sh"]

# Run with host network mode to access mapped onos instance from the virtual machine
# sudo docker run --rm -it --network host --name deployer deployer


