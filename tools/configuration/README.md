## Overview
The configure.py script allows users to configure the FreeRTOS repository
using kconfiglib. This allows users to configure the repository without
having to change any of the FreeRTOS source code.

## Dependencies
For this tool to run properly you must first install python3 and
kconfiglib.
### Installing python3
Installing python3 can be done here: https://www.python.org/downloads/.
You can verify your download by opening terminal and running 
"python3 --version".
### Installing kconfiglib
The kconfiglib README.md can be found here:
https://github.com/ulfalizer/Kconfiglib. To install kconfiglib run the
command "pip(3) install kconfiglib". The command depends on the current
version of pip that is currently available on your machine

## Script Functionality
When the script runs the user is prompted with a variety of options. I will
describe each of them here.
1. Provision AWS resources: This option will provision AWS resources for the
user. This will only work if the user has properly set up their AWS CLI on
the machine that they are currently working on. To do this you can follow the
"Configure the FreeRTOS demo application" section on these docs:
https://docs.aws.amazon.com/freertos/latest/userguide/getting_started_espressif.html.
Once users have done this, choosing option 1 will allow users to have a thing created for
them.
2. Choose a board: Choosing a board updates the information that will be used when running 
option 3 (configure your board). It set the defaults for all of the configuration
variables to be based on the specific board you have chosen.
3. Configure your demo for your chosen board: This will prompt the user with the
configuration GUI. Here they can make configuration decisions based on their needs.
4. Build and flash the demo for your chosen board: This will build and flash the demo for the
board the user has chosen. This currently only works as a proof of concept for the esp32 board.
5. Cleanup AWS resources: If the user provisioned resources with this tool they will be able to
tear them down with this command.
6. Quit: This quits the configuration tools.