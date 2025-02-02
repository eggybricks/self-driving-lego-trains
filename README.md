# 🚂 Self-driving LEGO trains!

This code shows how to automate LEGO trains and train track switches using [Pybricks](https://pybricks.com) and LEGO PoweredUp hubs, motors, and color sensors.

This will make more sense after you've watched this video:
[omniscient LEGO trains on eggybricks YouTube](https://youtu.be/T7L7Dx31owQ)

Includes some fun LEGO freight train crashes.

## 🔢 Organization

Each folder in this repo contains code for the corresponding scenario number below. Each scenario builds on the last.

Complete list of scenarios (including links to where it's demoed in the video):

1. Controlling one motorized switch directly (1 switch hub): [3:00](https://youtu.be/T7L7Dx31owQ?t=180)?
2. Controlling multiple motorized switches directly (n switch hubs): [3:50](https://youtu.be/T7L7Dx31owQ?t=230)
3. Remote-controlling multiple switches (1 leader hub + n switch hubs): [5:15](https://youtu.be/T7L7Dx31owQ?t=315)
4. Controlling one LEGO train directly (1 train hub): [7:30](https://youtu.be/T7L7Dx31owQ?t=450)
5. Remote-controlling one LEGO train (1 leader hub + 1 train hub): [8:48](https://youtu.be/T7L7Dx31owQ?t=528)
6. LEGO train routes itself between cities, using breadth-first search (1 leader hub + n switch hubs + 1 train hub): [12:31](https://youtu.be/T7L7Dx31owQ?t=751)
7. LEGO train routes itself between cities, using Dijkstra's algorithm (1 leader hub + n switch hubs + 1 train hub): [16:22](https://youtu.be/T7L7Dx31owQ?t=982)
8. Multiple LEGO trains route themselves between cities, using A* search (1 leader hub + n switch hubs + m train hubs): [21:15](https://youtu.be/T7L7Dx31owQ?t=1275)
9. How to modify code to add trains or cities:
- a. Adding an extra train: [23:02](https://youtu.be/T7L7Dx31owQ?t=1382)
- b. Adding another extra train: [23:39](https://youtu.be/T7L7Dx31owQ?t=1419)
- c. Adding extra cities: [24:02](https://youtu.be/T7L7Dx31owQ?t=1442)

## 👀 To use this with your own trains and layout

First, make sure each of your trains has a motor and a color-and-distance sensor. Here are instructions to add a color-and-distance sensor to any motorized PoweredUp train (it's written for our freight trains, but should work for any other train that has space for a sensor): [instructions - adding color-distance sensor](https://github.com/eggybricks/self-driving-lego-trains/blob/main/instructions%20-%20adding%20color-distance%20sensor.pdf)

Once you have all the parts needed, you should be able to run scenario 08, change the track layout to match your own, and change the switches and trains to match yours — and it *theoretically* should work.

## 🍳 How do I get a train that will run this code?

Any LEGO train with a PoweredUp train hub, PoweredUp train motor, and PoweredUp color-and-distance sensor should work with this code! Instructions for the exact trains we've tested this code on (in the video) are available at [eggybricks.com](https://eggybricks.com)!
