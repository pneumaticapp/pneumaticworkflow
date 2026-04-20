[![Documentation](https://img.shields.io/badge/docs-support.pneumatic.app-blue)](https://support.pneumatic.app/en/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)




<img width="1000" alt="Heading" src="https://github.com/user-attachments/assets/57e9d9df-24bf-42fe-a843-6f9c9b00bfac">


# Pneumatic: All Workflows all the Time



**Pneumatic** is an open-source SaaS workflow management system designed to streamline and organize workflows in businesses of any size. Originally developed as a cloud-based platform, Pneumatic empowers teams by enabling them to set up, run, and optimize workflows collaboratively, tracking each stage as tasks move from team to team.

[:tv: Product Overview (< 5 min)](https://www.youtube.com/watch?v=GC67ocuOFfE)


## Key Features

**Workflow Templates:** Create custom workflow templates and reuse them for repetitive processes. Templates define a series of steps that can be used across multiple workflows.

<img width="1000" alt="Screenshot 2024-11-28 at 2 01 39 PM" src="https://github.com/user-attachments/assets/b7494c37-fd72-4cb0-8202-3e0ccb3ea402">


**Multi-Workflow Management:** Once templates are set, create multiple workflows from each template and run them in parallel, adapting them as needed.

<img width="1000" alt="Screenshot 2024-11-28 at 2 02 11 PM" src="https://github.com/user-attachments/assets/b93e080b-21ab-43e7-b25f-09887afd74f2">


**Task Buckets for Staff:** Pneumatic focuses on individual task management, giving each staff member their own bucket of tasks. Staffers can complete tasks efficiently by emptying their buckets one by one.

<img width="1000" alt="Screenshot 2024-11-28 at 2 03 08 PM" src="https://github.com/user-attachments/assets/eb798843-50d9-4758-932f-de51061053e9">


**Automated Workflow Tracking:** With automated tracking, Pneumatic provides real-time insight into each workflow’s stage and automates handoffs between teams as tasks progress from step to step.


<img width="1000" alt="Screenshot 2024-11-28 at 2 03 31 PM" src="https://github.com/user-attachments/assets/df6f2082-32d4-441a-a243-683ebe9d283b">




## Find out more about how Pneumatic works by watching our video presentations:
[:tv: Getting Started with Workflow Templates (< 5 min)](https://youtu.be/sgDbMDyxWoY)

[:tv: Working with Workflows (< 5 min)](https://youtu.be/4FIqPVQrxtI)

[:tv: Working with Tasks (< 5 min)](https://youtu.be/9ZokwLdoVjY)

[:tv: Information Flow via Data Fields (< 5 min)](https://youtu.be/eITtZEciQnk)

## Integrations

As a cloud native solution Pneumatic easily integrates with other SaaS systems, either directly through its public API or via third party integration solutions like Zapier

<div align="left">
  <img width="1000" src="https://github.com/user-attachments/assets/dce1d41f-aa1f-4afc-9355-6aa306cf715c">
  
</div>


## Documentation
For more in-depth treatment of Pneumatic's features consult the support center: [Pneumatic Support Center](https://support.pneumatic.app/en/)

## Getting Started

You can grab your own copy of Pneumatic by cloning this repository and self-hosting it on your machine/instance. Here's a quick start guide:


### Prerequisites
* Operating System: Linux(Ubuntu/Debian), macOS or Windows(install and run at your own risk)
* Git (optional, if you want to clone the repository)
* Docker version 2.27 or above
* Docker compose version 27.0 or above
* At least 8GB of RAM (recommended 16GB)
* At least 50GB of diskspace(recommended 100GB)
* Ports 80, 443, and 8001 must be open and not in use by any other process(like apache or nginx)


### Get the files

You can either clone the repository using git like so

```
git clone https://github.com/pneumaticapp/pneumaticworkflow.git
```
or, you can simply download the [project's master folder](https://github.com/pneumaticapp/pneumaticworkflow/archive/refs/heads/master.zip) and unzip it

### Automatically create a .env config file and run

Cd into the project's directory, run ```chmod +x start.sh```, and then run the ```./start.sh``` script, passing it the address of your server as the sole argument(```./start.sh your-address```). If no argument is passed the script will use localhost as the default address and create a .env file setting the following parameters:

<pre>
  # Without SSL
  BACKEND_URL=http://your-address:8001
  FRONTEND_URL=http://your-address
  FORMS_URL=http://form.your-address
  FRONTEND_DOMAIN=your-address
  BACKEND_DOMAIN=your-address
  FORM_DOMAIN=form.your-address
  WSS_URL=ws://your-address:8001
</pre>

The script will then proceed to run ```docker compose up -d ```

This will run it in detached mode, if you want to see what's happening omit the -d flag.

Alternatively, you can create a .env file with the required parameters manually and run pneumatic either in terminal by executing the ```docker compose up -d``` command in your project's directory or from docker desktop.

Note, that the way it's currently configured, Pneumatic's frontend takes a while to get up and running.
But you can almost immediately check that your backend is up by going to `http://your-address:8001/admin`

### Open Pneumatic and register a free account

Once the containers are up and running go to http://your-server-address (http://localhost if you're connecting from the same machine) in your browser, register a free account and you're good to go.


### Deploying to Production

Deploying an instance of Pneumatic in production involves such steps as:

- setting up SSL
- setting up SSO
  
These steps are described in detail in [this wiki article](https://github.com/pneumaticapp/pneumaticworkflow/wiki/Configuration)

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

```markdown
Copyright 2024 Pneumatic Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
