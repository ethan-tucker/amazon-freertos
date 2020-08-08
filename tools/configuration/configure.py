import subprocess
import os
import kconfiglib
import re
import sys
from collections import OrderedDict
import boto3


def getValidUserInput(options, max_acceptable_value, error_message):
    user_input = input("\n%s (by number): "%(error_message))
    # This loop will run until the user has entered a valid selection. At that point the function will return the name of the board chosen.
    while 1:
        if(user_input.isdigit()):
            user_input_int = int(user_input)
            if(user_input_int < 1 or user_input_int > max_acceptable_value):
                user_input = input("\n%s (please enter a valid number): "%(error_message))
            else:
                return options[user_input_int-1]
        else:
            user_input = input("\n%s (please enter a number): "%(error_message))


def getBoardChoice(boards):
    print("\n-----CHOOSE A BOARD-----\n")
    
    for idx, board in enumerate(boards, start=1):
        print("%s) %s" %(idx, board))
    
    return getValidUserInput(boards, len(boards), "Select your board")


def getVendorChoice(boards_dict):
    print("\n-----CHOOSE A VENDOR-----\n")

    # vendors in a list of touples. The first item in each touple is the vendor and the second item is a list of boards corresponding to that vendor
    vendors = list(boards_dict.items())
    for idx, vendor in enumerate(vendors, start=1):
        print("%s) %s" %(idx, vendor[0]))
    
    return getValidUserInput(vendors, len(vendors), "Select your vendor")


def boardChoiceMenu(boards_dict):
    vendor = getVendorChoice(boards_dict)
    vendor_name = vendor[0]
    boards = vendor[1]
    board = getBoardChoice(boards)
    
    # These are the file paths for the configuration files associated with the vendor and board combo the user chose
    ota_board_config = "../../vendors/" + vendor_name + "/boards/" + board + "/aws_demos/config_files/ota_Kconfig"
    IP_board_config = "../../vendors/" + vendor_name + "/boards/" + board + "/aws_demos/config_files/FreeRTOSIP_Kconfig"
    board_properties = "../../vendors/" + vendor_name + "/boards/" + board + "/Kconfig"

    # merg_config.py runs merge config with all of the configruation files associated with the chosen board. This created a heirarchy of defaults in which
    # the values assigned int the board configuration files take precedence over those set in the library files (these are included in the file "KConfig").
    # The output of this process is the .config file. This is the intermediate step. When the genconfig command is run it uses this .config file to generate 
    # a new KConfig.h file.
    print("\n-----YOUR BOARD CHOICE-----\n")
    print("Your choice was the %s %s"%(vendor_name, board))
    print("\n-----MERGING CONFIGURATIONS FOR YOUR BOARD-----\n")
    sys.stdout.flush()
    subprocess.run(["py","merge_config.py", "KConfig", ".config", ota_board_config, IP_board_config, board_properties])
    print()
    # This is writing the users board choice out to a "database" file. This keeps track of the last board the user has configured in between runs of the program.
    with open("boardChoice.csv", "w") as database_file:
        database_file.write(vendor_name + "," + board)


# This function takes in the temp.h temporary header file and formats all of the varials with the FUNC tag. The fomatted file is outputted to build/kconfig/kconfig.h
def formatFunctionDeclarations(config_filepath):
    with open(config_filepath, "r") as config_file,\
         open("../../build/kconfig/kconfig.h", "w") as outfile:
        for line in config_file.readlines():
            
            # find all config options that are functions
            if line.split(" ")[1].split("_")[-1] == 'FUNC':
                # remove the quotations around the string value
                line = line.replace("\"","")
            outfile.write(line)

    # removes the temporary partially formatted header (it was only needed for this intermediary step)
    os.remove(config_filepath)


def updateKConfigAWSCredentials(iot_endpoint, thing_name):
    with open(".config", "r+") as config_file:
        config_text = config_file.read()
        config_text = config_text.replace("<THING_NAME>", thing_name)
        config_text = config_text.replace("<IOT_ENDPOINT>", iot_endpoint)
        config_file.seek(0)
        config_file.write(config_text)
        config_file.truncate()


def resetKConfig(thing_created, iot_endpoint, thing_name):
    updated_file = []
    with open(".config", "r") as config_file:
        config_text = config_file.readlines()
        for line in config_text:
            if "CONFIG_IOT_ENDPOINT" in line:
                line = 'CONFIG_IOT_ENDPOINT="<IOT_ENDPOINT>"\n'
            if "CONFIG_THING_NAME" in line:
                line = 'CONFIG_THING_NAME="<THING_NAME>"\n'
            updated_file.append(line)
    with open(".config", "w") as reset_config_file:
        for line in updated_file:
            reset_config_file.write(line)


# This function runs the kconfiglib commands guiconfig and genconfig. This runs the gui to allow the user to make configuration options and then generates the header file that
# is used by the FreeRTOS source code
def boardConfiguration(thing_created, thing_name, iot_endpoint):
    # Running guiconfig uses the base Kconfig and .config file to populate a gui with configuration opttions for the user to choose. The options are decided by the Kconfig
    # file and the defaults are set by the values in the .config file. 
    if(thing_created):
        updateKConfigAWSCredentials(iot_endpoint, thing_name)

    print("\n-----Running guiconfig-----\n")
    sys.stdout.flush()
    subprocess.run(["guiconfig"])

    # The header file created by genconfig will be put in the file temp.h. It is almost fully formatted,
    # but still treats macro functions as strings. The fully formatted header will be located in kconfig.h
    print("\n-----Running genconfig-----\n")
    sys.stdout.flush()
    subprocess.run(["genconfig", "--header-path=temp.h"])

    resetKConfig(thing_created, iot_endpoint, thing_name)

    print("\n-----Finished configuring-----\n")


# This function checks whether or not the user has chosen a board in the past. If they have it returns the vendor and board they previously selected, if not it returns None.
def loadCurrentBoardChoice():
    # os.path.isfile checks if a file exists. This first line is checking if a boardChoice.csv file exists and if it does, read in its information
    if(os.path.isfile("boardChoice.csv")):
        f = open("boardChoice.csv", "r")
        currentChoice = f.read().split(",")
        vendor = currentChoice[0]
        board = currentChoice[1]
        return (vendor, board)
    return None


def loadCurrentThingName():
    # os.path.isfile checks if a file exists. This first line is checking if a boardChoice.csv file exists and if it does, read in its information
    if(os.path.isfile("thingName.csv")):
        f = open("thingName.csv", "r")
        thing_name = f.read()
        return thing_name
    return None


def buildAndFlashBoard():
    # This is currently a proof of concept with hard coded commands
    os.chdir("../..")
    print("\n-----GENERATING BUILD FILES-----\n")
    sys.stdout.flush()
    subprocess.run(["cmake", "-D","VENDOR=espressif", "-D","BOARD=esp32_wrover_kit", "-D","COMPILER=xtensa-esp32", "-G","Ninja", "-S",".", "-B","build"])
    print("\n-----BUILDING PROJECT-----\n")
    sys.stdout.flush()
    subprocess.run(["cmake", "--build","build"])
    print("\n-----FLASHING THE BOARD AND RUNNING THE DEMO-----\n")
    sys.stdout.flush()
    subprocess.run(["py", "vendors/espressif/esp-idf/tools/idf.py", "erase_flash", "flash", "monitor", "-p", "COM3", "-B", "build"])
    os.chdir("tools/configuration")


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
    return thing_name


def provisionResources():
    print("\n----Choose a thing name-----\n")
    thing_name = input("What would you like to your thing name to be: ")
    
    print("\n-----Provisioning your AWS resources-----\n")
    sys.stdout.flush()

    updateConfigJsonFile(thing_name)

    os.chdir("../aws_config_quick_start")
    subprocess.run(["py", "SetupAWS.py", "kconfig_setup"])

    resetConfigJsonFile(thing_name)

    os.chdir("../configuration")
    print("\n-----Completed Provisioning-----\n")

    # write thing choice out to a file so it can persist between runs
    with open("thingName.csv", "w") as database_file:
        database_file.write(thing_name)

    return thing_name


def updateConfigJsonFile(thing_name):
    # update configure.json file (this is where the setup script expects the thing_name to be)
    with open("../aws_config_quick_start/configure.json", "r+") as configure_json:
        configure_text = configure_json.read()
        configure_text = configure_text.replace("$thing_name", thing_name)
        configure_json.seek(0)
        configure_json.write(configure_text)
        configure_json.truncate()


def resetConfigJsonFile(thing_name):
    # return the configure.json file to its original state so that the file does not remain changed 
    # (dont want to change git history)
    with open("../aws_config_quick_start/configure.json", "r+") as configure_json:
        configure_text = configure_json.read()
        configure_text = configure_text.replace(thing_name, "$thing_name")
        configure_json.seek(0)
        configure_json.write(configure_text)
        configure_json.truncate()


def getEndpoint():
    client = boto3.client('iot')
    endpoint = client.describe_endpoint(endpointType='iot:Data-ATS')
    return endpoint['endpointAddress']


def main():
    # I used an ordered dict here so that it was easy to use/index as well as easy to add new vendor board combos.
    boards_dict = OrderedDict(
             [("cypress", ["CY8CKIT_064S0S2_4343W","CYW943907AEVAL1F","CYW954907AEVAL1F"]), 
              ("espressif", ["esp32"]), 
              ("infineon", ["xmc4800_iotkit","xmc4800_plus_optiga_trust_x"]), 
              ("marvell", ["mw300_rd"]), 
              ("mediatek", ["mt7697hx-dev-kit"]), 
              ("microchip", ["curiosity_pic32mzef","ecc608a_plus_winsim"]),
              ("nordic", ["nrf52840-dk"]), 
              ("nuvoton", ["numaker_iot_m487_wifi"]), 
              ("nxp", ["lpc54018iotmodule"]), 
              ("pc", ["linux","windows"]), 
              ("renesas", ["rx65n-rsk"]), 
              ("st", ["stm32l475_discovery"]), 
              ("ti", ["cc3220_launchpad"]), 
              ("xilinx", ["microzed"])])
    config_filepath = "temp.h"
    board_chosen = False
    thing_created = False
    iot_endpoint = getEndpoint()

    # loadCurrentBoardChoice() checks if the user has chosen a board in the past. If they have not chosen a board before the "Configure demo" option 
    # will not be available until they do so
    
    currentBoardChoice = loadCurrentBoardChoice()
    if(currentBoardChoice):
        board_chosen = True

    thing_name = loadCurrentThingName()
    if(thing_name):
        thing_created = True

    choice = ""
    while choice != "6":
        print("-----FREERTOS Configuration-----\n")
        print("Options:")
        print("1) Provision AWS resources")
        print("2) Choose a board")
        if(board_chosen):
            print("3) Configure your demo for the %s %s"% (currentBoardChoice[0],currentBoardChoice[1]))
            print("4) Build and flash the demo for the %s %s"% (currentBoardChoice[0],currentBoardChoice[1]))
        if(thing_created):
            print("5) Cleanup AWS resources for the thing: '%s'"%(thing_name))
        print("6) Exit")
        choice = input("\nWhat do you want to do?: ")
        
        if(choice =="1"):
            thing_name = provisionResources()
            thing_created = True
        elif(choice == "2"):
            boardChoiceMenu(boards_dict)
            currentBoardChoice = loadCurrentBoardChoice()
            board_chosen = True
        elif(choice == "3" and board_chosen):
            boardConfiguration(thing_created, thing_name, iot_endpoint)
            formatFunctionDeclarations(config_filepath)
        elif(choice == "4" and board_chosen):
            buildAndFlashBoard()
        elif(choice == "5" and thing_created):
            cleanupResources(thing_name)
            thing_created = False
        elif(choice == "6"):
            pass
        else:
            print("Please choose a valid option")


if __name__=="__main__": 
    main() 