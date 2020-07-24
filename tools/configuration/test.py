import subprocess
import os.path


def getBoardChoice(boards, vendor_idx):
    print("-----BOARDS-----")
    
    for board_idx in range(len(boards[vendor_idx])):
        print("%s) %s" %(board_idx+1, boards[vendor_idx][board_idx]))
    
    board = input("Select your board (by number): ")
    valid = False
    while not valid:
        if(board.isdigit()):
            board_int = int(board)
            if(board_int < 1 or board_int > len(boards[vendor_idx])):
                board = input("Select your vendor (please enter a valid number): ")
            else:
                valid = True
        else:
            board = input("Select your vendor (please enter a number): ")
    return boards[vendor_idx][board_int-1]


def getVendorChoice(vendors):
    print("-----VENDORS-----")
    for vendor_idx in range(len(vendors)):
        print("%s) %s" %(vendor_idx+1, vendors[vendor_idx]))
    
    vendor = input("Select your vendor (by number): ")
    valid = False
    while not valid:
        if(vendor.isdigit()):
            vendor_int = int(vendor)
            if(vendor_int < 1 or vendor_int > len(vendors)):
                vendor = input("Select your vendor (please enter a valid number): ")
            else:
                valid = True
        else:
            vendor = input("Select your vendor (please enter a number): ")

    return (vendor_int-1, vendors[vendor_int-1])


def boardChoiceMenu(vendors, boards):
    ota_library_config = "../../libraries/freertos_plus/aws/ota/KConfig"

    vendor = getVendorChoice(vendors)
    vendorIdx = vendor[0]
    vendor_name = vendor[1]
    board = getBoardChoice(boards, vendorIdx)

    ota_board_config = "../../vendors/" + vendor_name + "/boards/" + board + "/aws_demos/config_files/ota_Kconfig"
    print(ota_board_config)
    subprocess.run(["py","merge_config.py", "Kconfig", ".config", ota_library_config, ota_board_config])
    f = open("boardChoice.csv", "w")
    f.write(vendor_name + "," + board)


def boardConfiguration():
    subprocess.run(["guiconfig"])


def loadCurrentBoardChoice():
    if(os.path.isfile("boardChoice.csv")):
        f = open("boardChoice.csv", "r")
        currentChoice = f.read().split(",")
        vendor = currentChoice[0]
        board = currentChoice[1]
        return (vendor, board)
    return None

def main():
    vendors = ["espressif", "pc"]
    boards = [["esp32"], ["linux", "windows"]]

    currentBoardChoice = loadCurrentBoardChoice()

    choice = ""
    while choice != "3":
        print("-----FREERTOS Configuration-----")
        print("Options:")
        print("1) Choose a board and a demo")
        if(currentBoardChoice != None):
            print("2) Configure your demo for the %s:%s board"% (currentBoardChoice[0],currentBoardChoice[1]))
        print("3) Exit")
        choice = input("What do you want to do?: ")
        
        if(choice == "1"):
            boardChoiceMenu(vendors, boards)
        elif(choice == "2" and currentBoardChoice != None):
            boardConfiguration()
        elif(choice == "3"):
            pass
        else:
            print("Please choose a valid option")


if __name__=="__main__": 
    main() 