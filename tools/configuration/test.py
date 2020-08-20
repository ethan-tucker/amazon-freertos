import unittest
from unittest import mock
import sys
import filecmp
import configure
from contextlib import contextmanager
from io import StringIO
from collections import OrderedDict
import os
from shutil import copyfile

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestConfigure(unittest.TestCase):
    @mock.patch('configure.input', create=True)
    # validate that I can enter in incorrect values and then a correct
    # value and the correct value will be returned
    def test_validateUserInput(self, mocked_input):
        mocked_input.side_effect = ['0', '5', 'e', '2']

        res = configure.getValidUserInput(["Option 1", "Option 2",
                                            "Option 3"], 3, "Choose an option")

        self.assertEqual(res, 'Option 2')

    @mock.patch('configure.input', create=True)
    def test_boardChoiceMenu(self, mocked_input):
        mocked_input.side_effect = ['0', '15', 'e', '2', '0', '5', 'e', '1']

        boards_dict = OrderedDict(
                [("cypress", ["CY8CKIT_064S0S2_4343W", "CYW943907AEVAL1F",
                              "CYW954907AEVAL1F"]),
                    ("espressif", ["esp32"]),
                    ("infineon", ["xmc4800_iotkit",
                                  "xmc4800_plus_optiga_trust_x"]),
                    ("marvell", ["mw300_rd"]),
                    ("mediatek", ["mt7697hx-dev-kit"]),
                    ("microchip", ["curiosity_pic32mzef",
                                   "ecc608a_plus_winsim"]),
                    ("nordic", ["nrf52840-dk"]),
                    ("nuvoton", ["numaker_iot_m487_wifi"]),
                    ("nxp", ["lpc54018iotmodule"]),
                    ("pc", ["linux", "windows"]),
                    ("renesas", ["rx65n-rsk"]),
                    ("st", ["stm32l475_discovery"]),
                    ("ti", ["cc3220_launchpad"]),
                    ("xilinx", ["microzed"])])

        actual_output_filepath = "testOutputActual/boardChoiceMenu1"
        expected_output_filepath = "testOutputExpected/boardChoiceMenu1"
        with captured_output() as (out, err),\
             open(actual_output_filepath, 'w') as realOutput:

            res = configure.boardChoiceMenu(boards_dict)
            output = out.getvalue().strip()
            realOutput.write(output)

        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), 'files diffed')

        self.assertEqual(res, ("espressif", "esp32"))

    def test_findAllKConfigFiles(self):
        # This test will only pass if the afr_KConfig repo has been cloned
        output_dir_name = "afr_Kconfig"
        expected_list = ["../../vendors/espressif/boards/esp32\\Kconfig",
                         "../../vendors/espressif/boards/esp32/aws_demos" +
                         "/config_files\\FreeRTOSIP_Kconfig",
                         "../../vendors/espressif/boards/esp32/aws_demos" +
                         "/config_files\\mqtt_Kconfig",
                         "../../vendors/espressif/boards/esp32/aws_demos" +
                         "/config_files\\ota_Kconfig"]

        KConfig_list = configure.findAllKConfigFiles("espressif", "esp32")

        self.assertEqual(expected_list, KConfig_list)

    def test_findAllKConfigFiles2(self):
        # This test will only pass if the afr_KConfig repo has been cloned
        output_dir_name = "afr_Kconfig"

        expected_list = ["../../vendors/nuvoton/boards/numaker_iot_m487_wifi" +
                         "\\Kconfig",
                         "../../vendors/nuvoton/boards/numaker_iot_m487_wifi" +
                         "/aws_demos/config_files\\FreeRTOSIP_Kconfig",
                         "../../vendors/nuvoton/boards/numaker_iot_m487_wifi" +
                         "/aws_demos/config_files\\mqtt_Kconfig"]

        KConfig_list = configure.findAllKConfigFiles("nuvoton",
                                                       "numaker_iot_m487_wifi")

        self.assertEqual(expected_list, KConfig_list)

    def test_findAllKConfigFiles3(self):
        # This test will only pass if the afr_KConfig repo has been cloned
        output_dir_name = "afr_Kconfig"

        expected_list = []

        KConfig_list = configure.findAllKConfigFiles("vendor", "board")

        self.assertEqual(expected_list, KConfig_list)

    def test_formatFunctionDeclarations(self):
        input_filepath = "testOutputExpected/formatFunctionInput"
        copyfile(input_filepath, "temp")

        actual_output_filepath= "testOutputActual/formatFunctionActual"
        expected_output_filepath= "testOutputExpected/formatFunctionOutput"
        configure.formatFunctionDeclarations("temp", actual_output_filepath)
        self.assertTrue(filecmp.cmp(actual_output_filepath,expected_output_filepath), "files diff")


    @mock.patch('configure.input', create=True)
    def test_updateKConfigAWSCredentials(self, mocked_input):
        iot_endpoint = "testing_endpoint"
        iot_thing = "testing_thing"
        thing_cert = "testing_cert"
        thing_private_key = "testing_key"

        boards_dict = OrderedDict(
                [("cypress", ["CY8CKIT_064S0S2_4343W", "CYW943907AEVAL1F",
                              "CYW954907AEVAL1F"]),
                    ("espressif", ["esp32"]),
                    ("infineon", ["xmc4800_iotkit",
                                  "xmc4800_plus_optiga_trust_x"]),
                    ("marvell", ["mw300_rd"]),
                    ("mediatek", ["mt7697hx-dev-kit"]),
                    ("microchip", ["curiosity_pic32mzef",
                                   "ecc608a_plus_winsim"]),
                    ("nordic", ["nrf52840-dk"]),
                    ("nuvoton", ["numaker_iot_m487_wifi"]),
                    ("nxp", ["lpc54018iotmodule"]),
                    ("pc", ["linux", "windows"]),
                    ("renesas", ["rx65n-rsk"]),
                    ("st", ["stm32l475_discovery"]),
                    ("ti", ["cc3220_launchpad"]),
                    ("xilinx", ["microzed"])])
        mocked_input.side_effect = ['2','1']
        # merge config to ensure test is consistent independent of the state of the 
        # .config file 
        configure.boardChoiceMenu(boards_dict)
        configure.updateKConfigAWSCredentials(iot_endpoint, iot_thing, thing_cert,
                                              thing_private_key)
        
        expected_output_filepath = "testOutputExpected/updateKconfigAWSCredentials"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,expected_output_filepath), "files diff")

    @mock.patch('configure.input', create=True)
    def test_resetKconfig(self, mocked_input):
        boards_dict = OrderedDict(
                [("cypress", ["CY8CKIT_064S0S2_4343W", "CYW943907AEVAL1F",
                              "CYW954907AEVAL1F"]),
                    ("espressif", ["esp32"]),
                    ("infineon", ["xmc4800_iotkit",
                                  "xmc4800_plus_optiga_trust_x"]),
                    ("marvell", ["mw300_rd"]),
                    ("mediatek", ["mt7697hx-dev-kit"]),
                    ("microchip", ["curiosity_pic32mzef",
                                   "ecc608a_plus_winsim"]),
                    ("nordic", ["nrf52840-dk"]),
                    ("nuvoton", ["numaker_iot_m487_wifi"]),
                    ("nxp", ["lpc54018iotmodule"]),
                    ("pc", ["linux", "windows"]),
                    ("renesas", ["rx65n-rsk"]),
                    ("st", ["stm32l475_discovery"]),
                    ("ti", ["cc3220_launchpad"]),
                    ("xilinx", ["microzed"])])
        mocked_input.side_effect = ['2','1']
        # merge config to ensure test is consistent independent of the state of the 
        # .config file 
        configure.boardChoiceMenu(boards_dict)
        configure.resetKConfig()
        
        expected_output_filepath = "testOutputExpected/resetKconfigOutput"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,expected_output_filepath), "files diff")
    
    # This test requires some user input. Hit save when prompted and then quit
    # out of the kconfig gui
    @mock.patch('configure.input', create=True)
    def test_boardconfiguration(self, mocked_input):
        boards_dict = OrderedDict(
                [("cypress", ["CY8CKIT_064S0S2_4343W", "CYW943907AEVAL1F",
                              "CYW954907AEVAL1F"]),
                    ("espressif", ["esp32"]),
                    ("infineon", ["xmc4800_iotkit",
                                  "xmc4800_plus_optiga_trust_x"]),
                    ("marvell", ["mw300_rd"]),
                    ("mediatek", ["mt7697hx-dev-kit"]),
                    ("microchip", ["curiosity_pic32mzef",
                                   "ecc608a_plus_winsim"]),
                    ("nordic", ["nrf52840-dk"]),
                    ("nuvoton", ["numaker_iot_m487_wifi"]),
                    ("nxp", ["lpc54018iotmodule"]),
                    ("pc", ["linux", "windows"]),
                    ("renesas", ["rx65n-rsk"]),
                    ("st", ["stm32l475_discovery"]),
                    ("ti", ["cc3220_launchpad"]),
                    ("xilinx", ["microzed"])])
        thing_created = True
        iot_endpoint = "testing_endpoint"
        thing_name = "testing_thing"
        thing_cert = "testing_cert"
        thing_private_key = "testing_key"
        temp_config_filepath = "temp.h"
        mocked_input.side_effect = ['2','1']
        # merge config to ensure test is consistent independent of the state of the 
        # .config file 
        configure.boardChoiceMenu(boards_dict)
        configure.boardConfiguration(thing_created, thing_name, iot_endpoint, thing_cert,
                       thing_private_key, temp_config_filepath)
        
        # Test the .config file was created correctly
        expected_output_filepath = "testOutputExpected/resetKconfigOutput"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,expected_output_filepath), "files diff")
        
        # Test the temp.h file was generated succesfully
        expected_output_filepath = "testOutputExpected/boardConfigurationKconfig"
        actual_output_filepath = "temp.h"
        self.assertTrue(filecmp.cmp(actual_output_filepath,expected_output_filepath), "files diff")
        os.remove("temp.h")

    def test_loadCurrentBoardChoice(self):
        with open("boardChoice.csv", "w") as board_choice_file:
            board_choice_file.write("espressif,esp32")

        res = configure.loadCurrentBoardChoice()
        self.assertEqual("espressif", res[0])
        self.assertEqual("esp32", res[1])

    def test_loadCurrentBoardChoice2(self):
        board_choice_file_exists = False
        if(os.path.isfile("boardChoice.csv")):
            copyfile("boardChoice.csv", "temp")
            board_choice_file_exists = True

        os.remove("boardChoice.csv")

        res = configure.loadCurrentBoardChoice()
        self.assertEqual(None, res)
        if(board_choice_file_exists):
            copyfile("temp", "boardChoice.csv")
            os.remove("temp")

    def test_loadCurrentThingName(self):
        with open("thingName.csv", "w") as board_choice_file:
            board_choice_file.write("testing")

        res = configure.loadCurrentThingName()
        self.assertEqual("testing", res)

    def test_loadCurrentThingName2(self):
        board_choice_file_exists = False
        if(os.path.isfile("thingName.csv")):
            copyfile("thingName.csv", "temp")
            board_choice_file_exists = True

        os.remove("thingName.csv")

        res = configure.loadCurrentThingName()
        self.assertEqual(None, res)
        if(board_choice_file_exists):
            copyfile("temp", "thingName.csv")
            os.remove("temp")

    def test_resetConfigJsonFile(self):
        thing_name = "testing"
        configure.resetConfigJsonFile(thing_name)

        actual_output_filepath = "../aws_config_quick_start/configure.json"
        expected_output_filepath = "testOutputExpected/resetConfigJsonExpected"
        self.assertTrue(filecmp.cmp(actual_output_filepath, expected_output_filepath), "Files diff")       

    def test_updateConfigJsonFile(self):
        thing_name = "testing"
        configure.updateConfigJsonFile(thing_name)

        actual_output_filepath = "../aws_config_quick_start/configure.json"
        expected_output_filepath = "testOutputExpected/updateConfigJsonExpected"
        self.assertTrue(filecmp.cmp(actual_output_filepath, expected_output_filepath), "Files diff")
        configure.resetConfigJsonFile(thing_name)

    def test_updatedFormat(self):
        input_filepath = "testOutputExpected/updateFormatInput"
        expected_output_filepath = "testOutputExpected/updateFormatOutput"
        actual_output_filepath = "testOutputActual/updateFormatActual"
        with open(input_filepath) as in_file:
            res = configure.updateFormat(in_file)
        
        with open(actual_output_filepath, "w") as actual_output_file:
            actual_output_file.write(res)

        self.assertTrue(filecmp.cmp(actual_output_filepath, expected_output_filepath))
    
    # This unit test will only succeed if you have run aws_configure
    @mock.patch('configure.input', create=True)
    def test_integrationTest(self, mocked_input):
        mocked_input.side_effect = ['1', 'testing', '2', '2', '1', '3', '5', '6']
        configure.main()

        # confirm .config file updated correctly
        expected_output_filepath = "testOutputExpected/integrationTestConfigOutput"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(expected_output_filepath, actual_output_filepath), "Files diff")
        
        # confirm kconfig file generated correctly
        expected_output_filepath = "testOutputExpected/integrationTestKConfigOutput"
        actual_output_filepath = "../../build/kconfig/kconfig.h"
        with open(expected_output_filepath) as expected_output,\
             open(actual_output_filepath) as actual_output:
                # The last three lines contain keys that will change every time the code is run
                # Every other line should be the same
                actual_output_text = actual_output.readlines()[:-3]
                expected_output_text = expected_output.readlines()[:-3]

        self.assertEqual(actual_output_text, expected_output_text)

if __name__ == '__main__':
    unittest.main()
