# MARSHA
### (Meta AI Robotic Spacecraft Handy Arm)

**[View Aaron Borger's Computer Science Thesis](https://drive.google.com/file/d/1fKjqaqFPO_juqMIO1a90XSz-93eHH_nX/view?usp=sharing)**

MARSHA is part of a research project at Northwest Nazarene University studying the use of Meta-Reinforcement Learning for robotics to account for inaccuracies between simulation and real-world, zero-gravity physics.

## Summary
This work proposes a method to train an agent in simulation with the TD3 algorithm which is a model-free policy optimisation deep reinforcement learning method. A model-agnostic meta learning method for reinforcement learning is utilized that allows the model to be retrained in space with only a few shots despite never being tested in the real world space environment. This work begins to demonstrate these methods by catching a ball in space with a robotic manipulator, but creates an opportunity for further work catching varying shaped objects in space which would be beneficial towards solving multiple challenging problems such as assisting astronauts, space debris removal, and in-orbit assembly and servicing of spacecraft. Catching the object is viewed as a multi-armed bandit problem where the agent receives one observation and performs one action during the course of each episode; where the observation is the position and velocity of the object as determined from a 3D point cloud and the action is a tailored latent space representation of a grasp.

## Branches
This repository contains software to control the robotic arms from two different platforms. The Embedded-Platform branch is designed for an Nvidia Jetson Nano while the Auxiliary-Platform branch is designed for interfacing or simulating the robotic arms.

## Current Progress
This work is a work in progress so installation procedures have not been written yet. Documentation is currently being written and will be linked as soon as it is presentable. The software will be finalized by May 2022 as the payload is scheduled to launch in August 2022.


