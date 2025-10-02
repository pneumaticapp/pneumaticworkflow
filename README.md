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
* Docker version 2.27 or above
* Docker compose version 27.0 or above


### Get the files

You can either clone the repository using git like so

```
git clone https://github.com/pneumaticapp/pneumaticworkflow.git
```
or, you can simply download the [project's master folder](https://github.com/pneumaticapp/pneumaticworkflow/archive/refs/heads/master.zip) and unzip it

### Run Pneumatic

To run Pneumatic cd into the project's directory and run the command

```
docker compose up -d
```

Alternatively, you can run the Pneumatic containers from Docker Desktop.

### Open Pneumatic and register a free account

Once the containers are up and running go to http://your-server-address(http://localhost if you're connecting from the same machine) in your browser, register a free account and you're good to go.



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
