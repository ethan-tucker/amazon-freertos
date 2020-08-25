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


# When this function is called it redirects stdout to a
# variable that can be accessed by calling
# out.getvalue().strip(). This allows the printed output
# of the function to be checked
@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


# This variable is global because it is needed by a variety
# of tests cases
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


class TestConfigure(unittest.TestCase):
    # mock.patch allows me to mock stdin with my own set of user entered
    # values. Because of how the code was written this allows me to test
    # the code in meangingful ways.
    @mock.patch('configure.input', create=True)
    # Validate that I can enter in incorrect values and then a correct
    # value and the correct value will be returned
    def test_validateUserInput(self, mocked_input):
        mocked_input.side_effect = ['0', '5', 'e', '2']

        res = configure.getValidUserInput(["Option 1", "Option 2",
                                           "Option 3"], 3, "Choose an option")

        self.assertEqual(res, 'Option 2')

    # This is an integration test for the boardChoice menu function. Ensure
    # that incorrect values are filtered out by validateUserInput which has
    # already been validated to function on its own. This ensures the value
    # returned is the expected value and that the messages printed to the
    # screen are correct as well
    @mock.patch('configure.input', create=True)
    def test_boardChoiceMenu(self, mocked_input):
        mocked_input.side_effect = ['0', '15', 'e', '2', '0', '5', 'e', '1']

        actual_output_filepath = "testOutputActual/boardChoiceMenu1"
        expected_output_filepath = "testOutputExpected/boardChoiceMenu1"
        # captured_output() redirects stdout to "out" which allows the
        # full printed output of the function to be checked using
        # filecmp.cmp
        with captured_output() as (out, err),\
             open(actual_output_filepath, 'w') as realOutput:

            res = configure.boardChoiceMenu(boards_dict)
            output = out.getvalue().strip()
            realOutput.write(output)

        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), 'files diffed')

        self.assertEqual(res, ("espressif", "esp32"))

    # Tests the findAllKconfigFiles for the espressif esp32. This board
    # only has three kconfig files currently in the afr-repo. If more are
    # added this test will not pass.
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

    # Tests the findAllKconfigFiles for the nuvoton numaker_iot_m487_wifi.
    # This board only has two kconfig files currently in the afr-repo. It
    # is chosen for this test because it has a different expected result than
    # the esp32 so we can confirm the function works successfully. If more are
    # added this test will not pass.
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

    # Tests the findAllKconfigFiles for the example "vendor" in the afr-repo.
    # This is done because that file structure has no kconfig files so we can
    # ensure the code works under those circumstances as well.
    def test_findAllKConfigFiles3(self):
        # This test will only pass if the afr_KConfig repo has been cloned
        output_dir_name = "afr_Kconfig"

        expected_list = []

        KConfig_list = configure.findAllKConfigFiles("vendor", "board")

        self.assertEqual(expected_list, KConfig_list)

    # Ensures that the format function correctly handles a variety of
    # situations outlined in the test input file.
    def test_formatFunctionDeclarations(self):
        input_filepath = "testOutputExpected/formatFunctionInput"
        # The format function destroys the input file after it is used, so
        # a copy of the input file must be made.
        copyfile(input_filepath, "temp")

        actual_output_filepath = "testOutputActual/formatFunctionActual"
        expected_output_filepath = "testOutputExpected/formatFunctionOutput"
        configure.formatFunctionDeclarations("temp", actual_output_filepath)
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "files diff")

    # confirms that the updateKConfigAWSCredentials behaves correctly under
    # reasonable circumstances. This option is only available after a board
    # is chosen so one must be chosen in the test. This test confirms that
    # the iot_endpoint, iot_thing, thing_cert, and thing_private_key, are
    # properly set in the ".config" file
    @mock.patch('configure.input', create=True)
    def test_updateKConfigAWSCredentials(self, mocked_input):
        iot_endpoint = "testing_endpoint"
        iot_thing = "testing_thing"
        thing_cert = "testing_cert"
        thing_private_key = "testing_key"

        mocked_input.side_effect = ['2', '1']
        # merge config to ensure test is consistent independent of the state of
        # the .config file
        configure.boardChoiceMenu(boards_dict)
        configure.updateKConfigAWSCredentials(iot_endpoint, iot_thing,
                                              thing_cert, thing_private_key)

        expected_output_filepath = ("testOutputExpected/" +
                                    "updateKconfigAWSCredentials")
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "files diff")

    # Tests the resetKconfig under reasonable circumstances. This function
    # would only be called after a board is chosen so a board must be chosen in
    # the test as well. This test confirms that the resetKonfig function
    # correctly returns the ".config" to its original (reset) state
    @mock.patch('configure.input', create=True)
    def test_resetKconfig(self, mocked_input):
        mocked_input.side_effect = ['2', '1']
        # merge config to ensure test is consistent independent of the state of
        # the .config file
        configure.boardChoiceMenu(boards_dict)
        configure.resetKConfig()

        expected_output_filepath = "testOutputExpected/resetKconfigOutput"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "files diff")

    # This test confirms that the boardConfigruation function outputs the
    # expected ".config" and Kconfig files. This test requires some user
    # input. Hit save when prompted and then quit out of the kconfig gui
    @mock.patch('configure.input', create=True)
    def test_boardconfiguration(self, mocked_input):
        thing_created = True
        iot_endpoint = "testing_endpoint"
        thing_name = "testing_thing"
        thing_cert = "testing_cert"
        thing_private_key = "testing_key"
        temp_config_filepath = "temp.h"
        mocked_input.side_effect = ['2', '1']
        # To ensure the test runs consistantly a board must be chosen at the
        # beginning of the test, otherwise the results could be based on the
        # current board choice that has been made by the user.
        configure.boardChoiceMenu(boards_dict)
        configure.boardConfiguration(thing_created, thing_name, iot_endpoint,
                                     thing_cert, thing_private_key,
                                     temp_config_filepath)

        # Test the .config file was created correctly
        expected_output_filepath = "testOutputExpected/resetKconfigOutput"
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "files diff")

        # Test the temp.h file was generated succesfully
        expected_output_filepath = ("testOutputExpected/" +
                                    "boardConfigurationKconfig")
        actual_output_filepath = "temp.h"
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "files diff")
        os.remove("temp.h")

    # This test ensures that the loadCurrentBoard choice function returns
    # the correct values when the boardChoice.csv file exists
    def test_loadCurrentBoardChoice(self):
        # Write expected values to the boardChoice.csv file
        with open("boardChoice.csv", "w") as board_choice_file:
            board_choice_file.write("espressif,esp32")

        res = configure.loadCurrentBoardChoice()
        self.assertEqual("espressif", res[0])
        self.assertEqual("esp32", res[1])

    # This test ensures that the loadCurrentBoard choice function returns
    # the correct values when the boardChoice.csv file does not exists
    def test_loadCurrentBoardChoice2(self):
        if(os.path.isfile("boardChoice.csv")):
            os.remove("boardChoice.csv")

        res = configure.loadCurrentBoardChoice()
        self.assertEqual(None, res)

    # This test ensures that the loadCurrentThingName choice function
    # returns the correct values when the thingName.csv file does
    # exists
    def test_loadCurrentThingName(self):
        with open("thingName.csv", "w") as board_choice_file:
            board_choice_file.write("testing")

        res = configure.loadCurrentThingName()
        self.assertEqual("testing", res)

        os.remove("thingName.csv")

    # This test ensures that the loadCurrentThingName2 choice function
    # returns the correct values when the thingName.csv file does not
    # exists
    def test_loadCurrentThingName2(self):
        if(os.path.isfile("thingName.csv")):
            os.remove("thingName.csv")

        res = configure.loadCurrentThingName()
        self.assertEqual(None, res)

    # This test ensures the configure.json file that the aws setup script
    # takes as input is reset after it is used so that the source code
    # does not change.
    def test_resetConfigJsonFile(self):
        thing_name = "testing"
        configure.resetConfigJsonFile(thing_name)

        actual_output_filepath = "../aws_config_quick_start/configure.json"
        expected_output_filepath = "testOutputExpected/resetConfigJsonExpected"
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "Files diff")

    # This test ensures the configure.json file is updated properly with the
    # thing name.
    def test_updateConfigJsonFile(self):
        thing_name = "testing"
        configure.updateConfigJsonFile(thing_name)

        actual_output_filepath = "../aws_config_quick_start/configure.json"
        expected_output_filepath = ("testOutputExpected/" +
                                    "updateConfigJsonExpected")
        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath), "Files diff")
        configure.resetConfigJsonFile(thing_name)

    # This test ensures the updateFormat function can take in a formatted
    # pem key and takes out the first and last line and all new lines so
    # that the value can be stored in a string.
    def test_updatedFormat(self):
        input_filepath = "testOutputExpected/updateFormatInput"
        expected_output_filepath = "testOutputExpected/updateFormatOutput"
        actual_output_filepath = "testOutputActual/updateFormatActual"
        with open(input_filepath) as in_file:
            res = configure.updateFormat(in_file)

        with open(actual_output_filepath, "w") as actual_output_file:
            actual_output_file.write(res)

        self.assertTrue(filecmp.cmp(actual_output_filepath,
                                    expected_output_filepath))

    # This unit test will only succeed if you have run aws_configure
    # This is an integration test of the entire process that a user
    # may go through when using the script. At the end it checks to
    # ensure the resulting kconfig.h file is what it is expected
    # to be based on.
    @mock.patch('configure.input', create=True)
    def test_integrationTest(self, mocked_input):
        mocked_input.side_effect = ['9', '1', 'testing', '2', '2', '1',
                                    '3', '5', '6']
        configure.main()

        # confirm .config file updated correctly
        expected_output_filepath = ("testOutputExpected/" +
                                    "integrationTestConfigOutput")
        actual_output_filepath = ".config"
        self.assertTrue(filecmp.cmp(expected_output_filepath,
                                    actual_output_filepath), "Files diff")

        # confirm kconfig file generated correctly
        expected_output_filepath = ("testOutputExpected/" +
                                    "integrationTestKConfigOutput")
        actual_output_filepath = "../../build/kconfig/kconfig.h"
        with open(expected_output_filepath) as expected_output,\
             open(actual_output_filepath) as actual_output:
            # The last three lines contain keys that will change every time the
            # code is run. Every other line should be the same
            actual_output_text = actual_output.readlines()[:-3]
            expected_output_text = expected_output.readlines()[:-3]

        self.assertEqual(actual_output_text, expected_output_text)


if __name__ == '__main__':
    unittest.main()
