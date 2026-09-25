# tui_tutor

A terminal-based AI-powered learning application designed to add structure to the process of learning from LLMs.

Rather than chatting with an LLM in an ad-hoc way, you get a structure of lessons, generated from a simple unit outline you can write yourself.

## Features

- AI-generated lessons and topics
- Chat to the AI at the end of each lesson, it has the context.
- Track completed lessons and learning progress
- OpenAI API compatible 
  - cloud API key or
  - local model
- Support to use codex cli with existing non-api chatGPT subscription as the LLM

## Philosophy

Most AI chat interfaces encourage asking questions at random.

TUI Tutor aims to add structure.

Learning is organised into lessons and topics, allowing you to progress through material in a structured way while still having the flexibility to ask questions whenever you need clarification.

The goal is to recreate the feeling of working through an online course.

## How it works

1. Create a small yaml file with information about a unit: goals, topics, etc. and put it in the InputUnits folder.
2. Log in to the app and select "Create Unit" from the main menu and the outline will be generated
3. Lessons for the entire unit can be generated at once with "Generate lessons", or will be generated when you start a lesson.
4. Start a unit or continue from where you left off through the main menu.
5. Learn about your chosen topic and ask questions about it.

## Installation

It's recommended to use docker or podman to host the application.
```
 docker run -d \
 --name tui_tutor \
 --restart unless-stopped \
 -p 2222:22 \
 -p 8082:8082 \
 -v codex-data:/home/dan/.codex \
 -v /run/media/dan/SSD/Docker/tutor/curricula:/opt/app/Curricula \
 -v /run/media/dan/SSD/Docker/tutor/inputunits:/opt/app/InputUnits \
 -v /run/media/dan/SSD/Docker/tutor/config:/opt/app/config \
 -v /run/media/dan/SSD/Docker/tutor/html:/opt/app/html \
 ghcr.io/dwalters0/tui_tutor:latest
```

Once the container is up, you can ssh into it on the mapped port and log in with the credentials root:root. A ForceCommand opens the app automatically.
```
ssh -p 2222 root@localhost
```

The generated websites are hosted continuously alongside the SSH console. From another machine on the same private network, open `http://<docker-host-ip>:8082`. The container binds the service to all network interfaces, but your router and firewall should keep port 8082 private to the LAN.

You can check the web process without loading a lesson at `http://<docker-host-ip>:8082/healthz`. Both SSH and the web process are supervised inside the container, and `--restart unless-stopped` brings the container back after a Docker daemon or host restart.

## Sample InputUnit
Add a .yaml file with the following structure to the InputUnits folder. It can contain any topic you like. ChatGPT is good at generating them too.
```yaml
course: Bachelor of Photography
course_code: BPhoto
name: Introduction to Photography
unit_code: PHOTO101
level: First Year University
total_duration: 24

outcomes:
  - Explain how exposure is controlled using aperture, shutter speed, and ISO, and apply the exposure triangle to produce correctly exposed photographs.
  - Demonstrate an understanding of camera operation, including lenses, focusing systems, metering modes, and file formats.
  - Apply principles of photographic composition to create visually balanced and engaging images across a variety of subjects.
  - Describe the effects of natural and artificial lighting and use appropriate techniques to control light in different shooting conditions.
  - Capture photographs in a range of genres, including landscape, portrait, street, and macro photography, using suitable techniques for each.
  - Demonstrate an effective digital photography workflow, including image import, organisation, basic editing, and exporting for print and digital media.
  - Evaluate photographs using technical and artistic criteria and provide constructive critiques of photographic work.

topic_descriptions:
  - Introduction to Photography
  - Camera Controls and Operation
  - The Exposure Triangle
  - Lenses and Focal Length
  - Composition and Visual Design
  - Light and Lighting Techniques
  - Focus, Depth of Field, and Motion
  - Digital Workflow and Post-Processing
  - Photographic Genres and Image Critique
```
## Configuration
The configuration file is in the mapped config folder when running with docker. You'll need to update it to either use codex or the URL of your LLM.


### Project status
I'm still working on this and might add a gui front to it. It was mostly written manually with a few functions helped along by AI.
