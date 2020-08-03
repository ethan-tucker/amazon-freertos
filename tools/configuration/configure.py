import subprocess
import os.path
import kconfiglib
import re

def getBoardChoice(boards, vendor_idx):
    print("\n-----BOARDS-----")
    
    for board_idx in range(len(boards[vendor_idx])):
        print("%s) %s" %(board_idx+1, boards[vendor_idx][board_idx]))
    
    board = input("\nSelect your board (by number): ")
    valid = False
    while not valid:
        if(board.isdigit()):
            board_int = int(board)
            if(board_int < 1 or board_int > len(boards[vendor_idx])):
                board = input("\nSelect your vendor (please enter a valid number): ")
            else:
                valid = True
        else:
            board = input("\nSelect your vendor (please enter a number): ")
    return boards[vendor_idx][board_int-1]


def getVendorChoice(vendors):
    print("\n-----VENDORS-----")
    for vendor_idx in range(len(vendors)):
        print("%s) %s" %(vendor_idx+1, vendors[vendor_idx]))
    
    vendor = input("\nSelect your vendor (by number): ")
    valid = False
    while not valid:
        if(vendor.isdigit()):
            vendor_int = int(vendor)
            if(vendor_int < 1 or vendor_int > len(vendors)):
                vendor = input("\nSelect your vendor (please enter a valid number): ")
            else:
                valid = True
        else:
            vendor = input("\nSelect your vendor (please enter a number): ")

    return (vendor_int-1, vendors[vendor_int-1])


def boardChoiceMenu(vendors, boards):
    ota_library_config = "../../libraries/freertos_plus/aws/ota/KConfig"

    vendor = getVendorChoice(vendors)
    vendorIdx = vendor[0]
    vendor_name = vendor[1]
    board = getBoardChoice(boards, vendorIdx)

    ota_board_config = "../../vendors/" + vendor_name + "/boards/" + board + "/aws_demos/config_files/ota_Kconfig"
    IP_board_config = "../../vendors/" + vendor_name + "/boards/" + board + "/aws_demos/config_files/FreeRTOSIP_Kconfig"
    board_properties = "../../vendors/" + vendor_name + "/boards/" + board + "/Kconfig"

    subprocess.run(["python3","merge_config.py", "KConfig", ".config", ota_board_config, IP_board_config, board_properties])
    f = open("boardChoice.csv", "w")
    f.write(vendor_name + "," + board)


def formatFunctionDeclarations(config_filepath):
    print()
    with open(config_filepath, "r") as config_file,\
         open("../../build/kconfig/kconfig.h", "w") as outfile:
        for line in config_file.readlines():
            
            # find all config options that are functions
            if line.split(" ")[1].split("_")[-1] == 'FUNC':
                # remove the quotations around the string value
                line = line.replace("\"","")
            outfile.write(line)

    # removes the temporary partially formatted header
    os.remove(config_filepath)


def boardConfiguration():
    subprocess.run(["guiconfig"])
    print("-----Finished configuring-----")

    # The header file created by genconfig will be put in the file temp.h. It is almost fully formatted,
    # but still treats macro functions as strings. The fully formatted header will be located in kconfig.h
    subprocess.run(["genconfig", "--header-path=temp.h"])


def loadCurrentBoardChoice():
    if(os.path.isfile("boardChoice.csv")):
        f = open("boardChoice.csv", "r")
        currentChoice = f.read().split(",")
        vendor = currentChoice[0]
        board = currentChoice[1]
        return (vendor, board)
    return None


def main():
    vendors = ["cypress", "espressif", "infineon", "marvell", "mediatek", "microchip", "nordic", "nuvoton", "nxp", "pc", "renesas", "st", "ti", "xilinx"]
    boards = [["CY8CKIT_064S0S2_4343W","CYW943907AEVAL1F","CYW954907AEVAL1F"], ["esp32"], ["xmc4800_iotkit","xmc4800_plus_optiga_trust_x"], ["mw300_rd"], ["mt7697hx-dev-kit"], \
             ["curiosity_pic32mzef","ecc608a_plus_winsim"], ["nrf52840-dk"], ["numaker_iot_m487_wifi"], ["lpc54018iotmodule"], ["linux","windows"], ["rx65n-rsk"], ["stm32l475_discovery"], \
             ["cc3220_launchpad"], ["microzed"]]
    # sets the prefix to the generated config variables, this defualts to 'CONFIG_' which is unecesary
    board_chosen = False
    currentBoardChoice = loadCurrentBoardChoice()
    config_filepath = "temp.h"
    if(currentBoardChoice):
        board_chosen = True
    choice = ""

    while choice != "3":
        print("\n-----FREERTOS Configuration-----")
        print("Options:")
        print("1) Choose a board")
        if(board_chosen):
            print("2) Configure your demo for the %s %s"% (currentBoardChoice[0],currentBoardChoice[1]))
        print("3) Exit")
        choice = input("What do you want to do?: ")
        
        if(choice == "1"):
            boardChoiceMenu(vendors, boards)
            currentBoardChoice = loadCurrentBoardChoice()
            board_chosen = True
        elif(choice == "2" and board_chosen):
            boardConfiguration()
            formatFunctionDeclarations(config_filepath)
        elif(choice == "3"):
            pass
        else:
            print("Please choose a valid option")


if __name__=="__main__": 
    main() 