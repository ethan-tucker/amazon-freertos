import subprocess
import os
import kconfiglib
import re
import sys
from collections import OrderedDict
import boto3
import glob


# getValidUserInput: Validates that the numbered selected the user makes is:
#   1) a number
#   2) within a valid range (based on the number of total options)
# This is used by both getBoardChoice and the getVenderChoice
# retuns: the valid choice that the user made
def getValidUserInput(options, max_acceptable_value, error_message):
    user_input = input("\n%s (by number): " % (error_message))
    # This loop will run until the user has entered a valid selection.
    # At that point the function will return the name of the board chosen.
    while 1:
        # Confirms that the user entered a digit
        if(user_input.isdigit()):
            user_input_int = int(user_input)
            # Given the user entered a digit, make sure that the number is
            # within an acceptable range
            if(user_input_int < 1 or user_input_int > max_acceptable_value):
                user_input = input("\n%s (please enter a valid number): "
                                   % (error_message))
            else:
                return options[user_input_int-1]
        else:
            user_input = input("\n%s (please enter a number): "
                               % (error_message))


# getBoardChoice: Prints all of the possible boards options that the user
# can select from. It then calls getValidUserInput to makes sure that
# they made a valid selection.
# Returns: The board choice (name of the board) that the user chose
def getBoardChoice(boards):
    print("\n-----CHOOSE A BOARD-----\n")

    for idx, board in enumerate(boards, start=1):
        print("%s) %s" % (idx, board))

    return getValidUserInput(boards, len(boards), "Select your board")


# getVendorChoice: This function prints all of the possible vendor options
# that the user can select from. It then calls getValidUserInput to makes
# sure that they made a valid selection.
# Returns: The vendor choice (name of the vendor) that the user chose
def getVendorChoice(boards_dict):
    print("\n-----CHOOSE A VENDOR-----\n")

    # vendors in a list of touples. The first item in each touple is the vendor
    # and the second item is a list of boards corresponding to that vendor
    vendors = list(boards_dict.items())
    for idx, vendor in enumerate(vendors, start=1):
        print("%s) %s" % (idx, vendor[0]))

    return getValidUserInput(vendors, len(vendors), "Select your vendor")


# boardChoiceMenu: calls getVendorChoice followed by getBoardChoice and echos
# the user choice to the terminal.
# Returns: the vendor and board choice that the user made
def boardChoiceMenu(boards_dict):
    vendor = getVendorChoice(boards_dict)
    vendor_name = vendor[0]
    boards = vendor[1]
    board = getBoardChoice(boards)

    command = ["py", "merge_config.py", "KConfig", ".config"]

    config_files = findAllKConfigFiles(vendor_name, board)
    for file in config_files:
        command.append(file)

    # merg_config.py runs merge config with all of the configruation files
    # associated with the chosen board. This created a heirarchy of defaults
    # in which the values assigned int the board configuration files take
    # precedence over those set in the library files (these are included in
    # the file "KConfig"). The output of this process is the .config file.
    # This is the intermediate step. When the genconfig command is run it
    # uses this .config file to generate a new KConfig.h file.
    print("\n-----YOUR BOARD CHOICE-----\n")
    print("Your choice was the %s %s" % (vendor_name, board))
    print("\n-----MERGING CONFIGURATIONS FOR YOUR BOARD-----\n")
    sys.stdout.flush()
    subprocess.run(command)
    print()
    # This is writing the users board choice out to a "database" file. This
    # keeps track of the last board the user has configured in between runs
    # of the program.
    with open("boardChoice.csv", "w") as database_file:
        database_file.write(vendor_name + "," + board)

    return (vendor_name, board)


# findAllKConfigFiles: Globs the boards directory tree for Kconfig files.
# Globbing for files matching a pattern allows for future files to be added
# without the code needing to be changed. It also doesn't break if certain
# boards do not have all of the configuration files (for example some boards
# wont have ota_agent_config.h).
# Returns: A list of all Kconfig files associated with a specific board
def findAllKConfigFiles(vendor, board):
    board_properties = ("../../vendors/" + vendor + "/boards/" + board +
                        "/*Kconfig")
    library_configs = ("../../vendors/" + vendor + "/boards/" + board +
                       "/aws_demos/config_files/*Kconfig")
    KconfigFilenamesList = (glob.glob(board_properties) +
                            glob.glob(library_configs))

    return KconfigFilenamesList


# formatFunctionDeclarations: This function takes in the temp.h temporary
# header file and formats all of the varials with the FUNC tag. The fomatted
# file is outputted to build/kconfig/kconfig.h
def formatFunctionDeclarations(temp_config_filepath, kconfig_build_filepath):
    with open(temp_config_filepath, "r") as config_file,\
         open(kconfig_build_filepath, "w") as outfile:
        for line in config_file.readlines():

            # find all config options that are functions
            if line.split(" ")[1].split("_")[-1] == 'FUNC':
                # remove the quotations around the string value
                line = line.replace("\"", "")
            outfile.write(line)

    # removes the temporary partially formatted header (it was only needed for
    # this intermediary step)
    os.remove(temp_config_filepath)


# updateKConfigAWSCredentials: Updates the ".config" file with the thing name
# that the user chose and the users AWS endpoint this prevents them from having
# to enter it in manually.
def updateKConfigAWSCredentials(iot_endpoint, thing_name, thing_cert,
                                thing_private_key):
    with open(".config", "r+") as config_file:
        config_text = config_file.read()
        config_text = config_text.replace("<THING_NAME>", thing_name)
        config_text = config_text.replace("<IOT_ENDPOINT>", iot_endpoint)
        config_text = config_text.replace("<THING_CERT>", thing_cert)
        config_text = config_text.replace("<THING_PRIVATE_KEY>",
                                          thing_private_key)
        config_file.seek(0)
        config_file.write(config_text)
        config_file.truncate()


# resetKConfig: Resets the ".config" file with the format that the
# updateKConfigAWSCredentials expects.
def resetKConfig():
    updated_file = []
    with open(".config", "r") as config_file:
        config_text = config_file.readlines()
        for line in config_text:
            if "CONFIG_IOT_ENDPOINT" in line:
                line = 'CONFIG_IOT_ENDPOINT="<IOT_ENDPOINT>"\n'
            if "CONFIG_THING_NAME" in line:
                line = 'CONFIG_THING_NAME="<THING_NAME>"\n'
            if "CONFIG_THING_CERT" in line:
                line = 'CONFIG_THING_CERT="<THING_CERT>"\n'
            if "CONFIG_THING_PRIVATE_KEY" in line:
                line = 'CONFIG_THING_PRIVATE_KEY="<THING_PRIVATE_KEY>"\n'
            updated_file.append(line)
    with open(".config", "w") as reset_config_file:
        for line in updated_file:
            reset_config_file.write(line)


# boardConfiguration: This function runs the kconfiglib commands guiconfig and
# genconfig. This runs the gui to allow the user to make configuration options
# and then generates the header file that is used by the FreeRTOS source code
def boardConfiguration(thing_created, thing_name, iot_endpoint, thing_cert,
                       thing_private_key, temp_config_filepath):
    # If the user has created a thing using the option in this configure tool
    # then their choices should be prepopulated in the configuration menu.
    # updateKConfigAWSCredentials will take these pieces of information and
    # fill them in for the user.
    if(thing_created):
        updateKConfigAWSCredentials(iot_endpoint, thing_name, thing_cert,
                                    thing_private_key)

    # Running guiconfig uses the base Kconfig and .config file to populate a
    # gui with configuration options for the user to choose. The options are
    # decided by the Kconfigfile and the defaults are set by the values in the
    # .config file
    print("\n-----Running guiconfig-----\n")
    sys.stdout.flush()
    subprocess.run(["guiconfig"])

    # The header file created by genconfig will be put in the file temp.h. It
    # is almost fully formatted, but still treats macro functions as strings.
    # The fully formatted header will be located in kconfig.h and will be
    # generated by formatFunctionDeclarations()
    print("\n-----Running genconfig-----\n")
    sys.stdout.flush()
    subprocess.run(["genconfig", "--header-path=" + temp_config_filepath])

    resetKConfig()

    print("\n-----Finished configuring-----\n")


# loadCurrentBoardChoice: This function checks whether or not the user has
# chosen a board in the past and returns their choice if they have made one
# before.
# Return: If they have chose a board before, it returns the vendor and board
# they previously selected, if not it returns None.
def loadCurrentBoardChoice():
    # os.path.isfile checks if a file exists. This first line is checking if
    # a boardChoice.csv file exists and if it does, read in its information
    if(os.path.isfile("boardChoice.csv")):
        with open("boardChoice.csv", "r") as f:
            vendor_and_board = f.read().split(",")
            return vendor_and_board
    return None


# loadCurrentThingName: Checks whether or not the file "thingName.csv" exists
# and returns their choice if they have made one before.
# Returns: If the user has created a thing in the past this will return the
# name of the thing that they most recently created, if they have not it will
# return None.
def loadCurrentThingName():
    # os.path.isfile checks if a file exists. This first line is checking if
    # a boardChoice.csv file exists and if it does, read in its information
    if(os.path.isfile("thingName.csv")):
        with open("thingName.csv", "r") as f:
            thing_name = f.read()
            return thing_name
    return None


# buildAndFlashBoard: Generates the build file for the board, builds the
# projects, and then flashes the board and runs the demo. These functions
# are currently hard coded for the esp32 board to be built and run on a
# windows machine.
def buildAndFlashBoard():
    # This is currently a proof of concept with hard coded commands
    # First the directory must be changed to the root directory
    os.chdir("../..")

    # Generating the build files
    print("\n-----GENERATING BUILD FILES-----\n")
    sys.stdout.flush()
    subprocess.run(["cmake", "-D", "VENDOR=espressif", "-D",
                    "BOARD=esp32_wrover_kit", "-D", "COMPILER=xtensa-esp32",
                    "-G", "Ninja", "-S", ".", "-B", "build"])

    # Building the project
    print("\n-----BUILDING PROJECT-----\n")
    sys.stdout.flush()
    subprocess.run(["cmake", "--build", "build"])

    # Flashing the board and running the demo
    print("\n-----FLASHING THE BOARD AND RUNNING THE DEMO-----\n")
    sys.stdout.flush()
    subprocess.run(["py", "vendors/espressif/esp-idf/tools/idf.py",
                    "erase_flash", "flash", "monitor", "-p", "COM3",
                    "-B", "build"])
    os.chdir("tools/configuration")


# cleanupResource: runs SetupAWS.py delete_prerqe which cleans up all of the
# files associated with the AWS resources as well as cleans up all of the
# resources that were provisioned to the users AWS account. The SetupAWS
# Readme.md has more information about the inner workings of this program.
def cleanupResources(thing_name):
    print("\n-----Cleaning up your AWS resources-----\n")
    sys.stdout.flush()

    updateConfigJsonFile(thing_name)

    os.chdir("../aws_config_quick_start")
    subprocess.run(["py", "SetupAWS.py", "delete_prereq"])

    resetConfigJsonFile(thing_name)

    os.chdir("../configuration")
    print("\n-----Completed clean up-----\n")
    os.remove("thingName.csv")


# provisionsResources: Runs SetupAWS.py kconfig_setup which is a functionality
# that I added to support setting up the resources and modifying the
# client_credential_keys without modifying the client_credential file.
def provisionResources():
    print("\n----Choose a thing name-----\n")
    thing_name = input("What would you like to your thing name to be: ")

    print("\n-----Provisioning your AWS resources-----\n")
    sys.stdout.flush()

    # Update the configuration file that the SetupAWS.py script relies on
    updateConfigJsonFile(thing_name)

    # Call the SetupAWS.py script with the "kconfig_setup" command line
    # argument. This will create the thing and generate the credential files,
    # but will not attempt to update the client credential source files
    os.chdir("../aws_config_quick_start")
    subprocess.run(["py", "SetupAWS.py", "kconfig_setup"])

    resetConfigJsonFile(thing_name)

    os.chdir("../configuration")
    print("\n-----Completed Provisioning-----\n")

    # write thing choice out to a file so it can persist between runs
    with open("thingName.csv", "w") as database_file:
        database_file.write(thing_name)

    return thing_name


# updateConfigJsonFile: Updates configure.json file (this is where the setup
# script expects the thing_name to be). This file is located in
# "../aws_config_quick_start/configure.json"
def updateConfigJsonFile(thing_name):
    # Open with r+ to read and modify at the same time.
    with open("../aws_config_quick_start/configure.json", "r+") as\
              configure_json:
        configure_text = configure_json.read()

        # The "$thing_name" place holder is replaced with the thing name the
        # user entered
        configure_text = configure_text.replace("$thing_name", thing_name)
        configure_json.seek(0)
        configure_json.write(configure_text)
        configure_json.truncate()


# updateConfigJsonFile: Return the configure.json file to its original state so
# that the file does not remain changed (dont want to change git history). This
# file is located in "../aws_config_quick_start/configure.json"
def resetConfigJsonFile(thing_name):
    # Open with r+ to read and modify at the same time. Here the thing_name
    # place holder is replaced with the thing name the user entered
    with open("../aws_config_quick_start/configure.json", "r+") as\
              configure_json:
        configure_text = configure_json.read()

        # The thing name the user entered is replaced with the "$thing_name"
        # placeholder so that the file is not changed from its original state.
        configure_text = configure_text.replace(thing_name, "$thing_name")
        configure_json.seek(0)
        configure_json.write(configure_text)
        configure_json.truncate()


# getEndpoint: Returns the endpoint of the boto3 client connection the user has
# established. This allows the iot-endpoint to be set in ".config" without the
# user having to manually enter it.
# Returns: The endpoint of the boto3 client connection the user has established
def getEndpoint():
    client = boto3.client('iot')
    endpoint = client.describe_endpoint(endpointType='iot:Data-ATS')
    return endpoint['endpointAddress']


# updateFormat: The update format function is a helper function used by
# formatCredentials. It takes in the client credential key files and reformats
# them to be a string on a single line so that they can be stored in a simple
# string variable.
# Returns: The contents of the file between the second and second to last line,
# concatenated into one string variable
def updateFormat(file_name):
    lines = file_name.readlines()
    res_text = ""
    for idx, line in enumerate(lines):
        # The first and last lines of the file are headers and do not need to
        # be included
        if (idx != 0 and idx != len(lines) - 1):
            res_text += line.strip()
    return res_text


# formatCredentials: The client credential keys are typically stored in a way
# that is not easily represented in kconfig. This function takes that format
# and converts it so that these values can be stored in a simple string.
# Returns: The two formatted credential keys in a touple
def formatCredentials(thing_name):
    with open("../aws_config_quick_start/" + thing_name + "_cert_pem_file") as\
              cert_pem_file,\
              open("../aws_config_quick_start/" + thing_name +
                   "_private_key_pem_file") as private_key_pem_file:

        return (updateFormat(cert_pem_file),
                updateFormat(private_key_pem_file))


# printMainMenuOptions: Simply prints the options for the main menu. Abstracted
# to make the main code more readable
def printMainMenuOptions(board_chosen, currentBoardChoice, thing_created,
                         thing_name):
    print("\n-----FREERTOS Configuration-----\n")
    print("Options:")
    print("1) Provision AWS resources")
    print("2) Choose a board")
    if(board_chosen):
        print("3) Configure your demo for the %s %s" %
              (currentBoardChoice[0], currentBoardChoice[1]))
        print("4) Build and flash the demo for the %s %s" %
              (currentBoardChoice[0], currentBoardChoice[1]))
    if(thing_created):
        print("5) Cleanup AWS resources for the thing: '%s'" % (thing_name))
    print("6) Exit")


def main():
    # I used an ordered dict here so that it was easy to use/index as well as
    # easy to add new vendor board combos.
    boards_dict = OrderedDict(
             [("cypress", ["CY8CKIT_064S0S2_4343W", "CYW943907AEVAL1F",
                           "CYW954907AEVAL1F"]),
              ("espressif", ["esp32"]),
              ("infineon", ["xmc4800_iotkit", "xmc4800_plus_optiga_trust_x"]),
              ("marvell", ["mw300_rd"]),
              ("mediatek", ["mt7697hx-dev-kit"]),
              ("microchip", ["curiosity_pic32mzef", "ecc608a_plus_winsim"]),
              ("nordic", ["nrf52840-dk"]),
              ("nuvoton", ["numaker_iot_m487_wifi"]),
              ("nxp", ["lpc54018iotmodule"]),
              ("pc", ["linux", "windows"]),
              ("renesas", ["rx65n-rsk"]),
              ("st", ["stm32l475_discovery"]),
              ("ti", ["cc3220_launchpad"]),
              ("xilinx", ["microzed"])])
    temp_config_filepath = "temp.h"
    kconfig_build_filepath = "../../build/kconfig/kconfig.h"
    board_chosen = False
    thing_created = False
    thing_cert = ""
    thing_private_key = ""
    iot_endpoint = getEndpoint()

    # loadCurrentBoardChoice() checks if the user has chosen a board in the
    # past. If they have not chosen a board before the "Configure demo" option
    # will not be available until they do so
    currentBoardChoice = loadCurrentBoardChoice()
    if(currentBoardChoice):
        board_chosen = True

    # loadCurrentThingName() checks if the user has created a thing (using
    # option 1 "provision AWS resources") before. If they have not done this
    # before than the option "Cleanup AWS resources" will not be available
    thing_name = loadCurrentThingName()
    if(thing_name):
        thing_created = True

    choice = ""
    while choice != "6":
        printMainMenuOptions(board_chosen, currentBoardChoice, thing_created,
                             thing_name)
        choice = input("\nWhat do you want to do?: ")

        # Provision AWS resources
        if(choice == "1"):
            thing_name = provisionResources()
            credential_keys = formatCredentials(thing_name)
            thing_cert = credential_keys[0]
            thing_private_key = credential_keys[1]
            thing_created = True

        # Choose a board
        elif(choice == "2"):
            boardChoiceMenu(boards_dict)
            currentBoardChoice = loadCurrentBoardChoice()
            board_chosen = True

        # Choose configuration options
        elif(choice == "3" and board_chosen):
            boardConfiguration(thing_created, thing_name, iot_endpoint,
                               thing_cert, thing_private_key,
                               temp_config_filepath)
            formatFunctionDeclarations(temp_config_filepath,
                                       kconfig_build_filepath)

        # Build and flash the demo
        elif(choice == "4" and board_chosen):
            buildAndFlashBoard()

        # Cleanup the AWS resources
        elif(choice == "5" and thing_created):
            cleanupResources(thing_name)
            thing_created = False

        # Quit the program
        elif(choice == "6"):
            pass
        else:
            print("Please choose a valid option")


if __name__ == "__main__":
    main()
