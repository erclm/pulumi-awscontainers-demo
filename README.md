# pulumi-awscontainers-demo
showcasing how pulumi works with aws. 

This deploys a simple node.js application to AWS ECS(faragate) using Pulumi. The application displays a configurable message that can be changed through Pulumi configuration.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [Python 3.6+](https://www.python.org/downloads/)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [Docker](https://www.docker.com/products/docker-desktop) installed and running

## Project Structure

- `server.js` - The Node.js application that will be deployed
- `package.json` - Node.js package dependencies
- `Dockerfile` - Container definition for the application
- `__main__.py` - Pulumi program written in Python
- `Pulumi.yaml` - Pulumi project configuration

## Getting Started

1. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Initialize a new Pulumi stack:
   ```bash
   pulumi stack init dev
   ```

3. Configure the application message:
   ```bash
   pulumi config set appMessage "Hello from Pulumi!"
   ```

4. Deploy the application:
   ```bash
   pulumi up
   ```

5. After the deployment completes, the URL of your application will be displayed in the output:
   ```
   Outputs:
       url: "http://app-lb-xxxxx.us-west-2.elb.amazonaws.com"
   ```

6. Open the URL in your browser to see your application running with the configured message.

## Changing the Message

To change the message displayed by the application:

1. Update the configuration:
   ```bash
   pulumi config set appMessage "My new message!"
   ```

2. Deploy the changes:
   ```bash
   pulumi up
   ```

3. Once the deployment is complete, refresh the browser to see the updated message.

## Clean Up

To delete all resources created by this project:

```bash
pulumi destroy
```

## Requirements File

You'll need to create a `requirements.txt` file with the following dependencies:

```
pulumi>=3.0.0,<4.0.0
pulumi-aws>=5.0.0,<6.0.0
pulumi-docker>=4.0.0,<5.0.0
```